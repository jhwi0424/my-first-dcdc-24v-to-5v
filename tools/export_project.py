"""Extract reviewable metadata from the versioned EasyEDA Pro project.

No electrical geometry or native project is modified. Run from the repository root.
Uses only the Python standard library.
"""
from pathlib import Path
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'hardware/latest/TPS54202_24V_5V_396VH_real.epro2'
NETLIST = ROOT / 'hardware/netlists/schematic-current.enet'


def parse_project(path):
    with zipfile.ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.endswith('.epru'))
        text = archive.read(name).decode('utf-8')
    docs = []
    for line in text.splitlines():
        header, payload = line.split('||', 1)
        header = json.loads(header)
        payload = payload.removesuffix('|')
        value = json.loads(payload) if payload else None
        if header['type'] == 'DOCHEAD':
            docs.append({'head': value, 'records': {}})
        else:
            key = (header['type'], header.get('id'))
            if value is None:
                docs[-1]['records'].pop(key, None)
            else:
                docs[-1]['records'][key] = (header, value)
    return docs


def natural(value):
    return [int(p) if p.isdigit() else p for p in re.split(r'(\d+)', value)]


def write_json(path, data):
    (ROOT / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def export():
    docs = parse_project(PROJECT)
    pcb = next(d for d in docs if d['head']['docType'] == 'PCB')
    netlist = json.loads(NETLIST.read_text(encoding='utf-8'))
    sch = {c['props']['Designator']: c for c in netlist['components'].values()}
    attrs = {}
    for a, b in pcb['records'].values():
        if a['type'] == 'ATTR':
            attrs.setdefault(b['parentId'], {})[b['key']] = b['value']
    components = {}
    ids = {}
    for a, b in pcb['records'].values():
        if a['type'] != 'COMPONENT':
            continue
        prop = {**b.get('attrs', {}), **attrs.get(a['id'], {})}
        ref = prop['Designator']
        ids[a['id']] = ref
        components[ref] = {'attributes': prop, 'pins': {}}
    for a, b in pcb['records'].values():
        if a['type'] == 'PAD_NET':
            _, cid, pin, _ = json.loads(a['id'])
            if cid in ids:
                components[ids[cid]]['pins'][pin] = b['padNet']

    mismatches = []
    checked = 0
    for ref, component in sorted(components.items(), key=lambda v: natural(v[0])):
        if ref not in sch:
            mismatches.append({'ref': ref, 'reason': 'PCB-only component'})
            continue
        expected = {p['number']: p['net'] for p in sch[ref]['pinInfoMap'].values()}
        actual = component['pins']
        for pin in sorted(set(expected) | set(actual), key=natural):
            checked += 1
            if expected.get(pin) != actual.get(pin):
                mismatches.append({'ref': ref, 'pin': pin, 'schematic': expected.get(pin), 'pcb': actual.get(pin)})
    sch_only = sorted(set(sch) - set(components), key=natural)
    report = {
        'source': PROJECT.relative_to(ROOT).as_posix(),
        'source_sha256': hashlib.sha256(PROJECT.read_bytes()).hexdigest(),
        'schematic_netlist_sha256': hashlib.sha256(NETLIST.read_bytes()).hexdigest(),
        'schematic_component_count': len(sch),
        'pcb_component_count': len(components),
        'common_pins_checked': checked,
        'common_pin_mismatches': mismatches,
        'schematic_only_components': sch_only,
        'pcb_only_components': sorted(set(components) - set(sch), key=natural),
        'scope': 'Logical pad assignments only; does not check copper connectivity, DRC, ERC, thermal or electrical performance.',
    }
    write_json('hardware/netlists/pcb-current.json', {'source': report['source'], 'components': components})
    write_json('hardware/netlists/consistency-report.json', report)
    nets = {}
    for ref, comp in components.items():
        for pin, net in comp['pins'].items():
            nets.setdefault(net or '(unconnected)', []).append(f'{ref}.{pin}')
    lines = ['# 最新版 PCB 网表', '', '从完整工程的 `PAD_NET` 记录重新提取；不代表铜皮连通性或 DRC 检查结果。', '', '| 网络 | 引脚 |', '| --- | --- |']
    for net in sorted(nets):
        lines.append(f'| `{net}` | ' + ', '.join(f'`{x}`' for x in sorted(nets[net], key=natural)) + ' |')
    (ROOT / 'hardware/netlists/README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')

    bom = []
    for ref in sorted(components, key=natural):
        p = sch[ref]['props']
        row = {'ref': ref, 'value': p.get('Value') or p.get('Manufacturer Part') or '',
               'footprint': p.get('FootprintName', ''), 'mpn': p.get('Manufacturer Part', ''),
               'lcsc': p.get('Supplier Part', ''), 'populate': p.get('Value') != 'N/C'}
        bom.append(row)
    write_json('hardware/bom/pcb-bom.json', bom)
    lines = ['# 最新版 PCB BOM', '', '按 PCB 中实际存在的 12 个元件位号整理。C6 为预留位，默认不焊；H1～H4 仅存在于原理图，不计入本表。', '',
             '| 位号 | 数值 / 型号 | 封装 | LCSC 编号 | 装配 |', '| --- | --- | --- | --- | --- |']
    for row in bom:
        lines.append('| ' + ' | '.join([row['ref'], row['value'], row['footprint'], row['lcsc'] or '未指定', '焊接' if row['populate'] else '不焊 / DNP']) + ' |')
    lines += ['', '通用电容、电阻尚未绑定完整采购型号；耐压、容差、介质和直流偏压降容需要在采购前确定。C1 位于输入侧，不能只按“10µF”选料。']
    (ROOT / 'hardware/bom/README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    if mismatches:
        raise SystemExit('Common circuit net mismatch: ' + json.dumps(mismatches))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    export()

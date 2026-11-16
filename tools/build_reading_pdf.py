"""Reflow native PCB PDF pages for reading; never changes the board design.

Requires reportlab and PyMuPDF. The native PDF is a temporary export from
EasyEDA Pro: tmp/pcb-native.pdf. Run after tools/export_project.py.
"""
from pathlib import Path
from io import BytesIO
import json
import pymupdf
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4, landscape

ROOT = Path(__file__).resolve().parents[1]


def build():
    # Use a local CJK font; no font binary is redistributed in the repository.
    font_path = Path('C:/Windows/Fonts/simhei.ttf')
    if not font_path.exists():
        raise SystemExit('Set font_path to an installed CJK TrueType font.')
    pdfmetrics.registerFont(TTFont('CJK', str(font_path)))
    source = pymupdf.open(ROOT / 'tmp/pcb-native.pdf')
    target = pymupdf.open()
    width, height = landscape(A4)
    titles = [(3, 'PCB 顶面装配与铜层'), (4, 'PCB 底面装配与铜层'),
              (0, 'PCB 顶面元件位置'), (5, 'PCB 钻孔位置')]
    for page_no, (source_no, title) in enumerate(titles, 1):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(width, height))
        c.setTitle('TPS54202 24V to 5V - PCB reading copy')
        c.setFont('CJK', 19)
        c.drawString(32, height - 40, title)
        c.setFont('CJK', 10)
        c.drawString(32, height - 60, 'TPS54202 DCDC 24-5 396VH real | 嘉立创EDA 专业版 V4.1.78 | 2026-11-17')
        c.setFont('CJK', 9)
        c.drawString(32, 20, f'{page_no} / 5   放大阅读版，非 1:1 制造图。原始板图内容来自嘉立创 PDF 导出。')
        c.save()
        wrapper = pymupdf.open(stream=buffer.getvalue(), filetype='pdf')
        target.insert_pdf(wrapper)
        target[-1].show_pdf_page(pymupdf.Rect(60, 90, width - 60, height - 43), source, source_no)

    bom = json.loads((ROOT / 'hardware/bom/pcb-bom.json').read_text(encoding='utf-8'))
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width, height))
    c.setFont('CJK', 19)
    c.drawString(32, height - 40, 'PCB BOM / 装配清单')
    c.setFont('CJK', 10)
    c.drawString(32, height - 62, '12 个 PCB 位号；C6 默认不焊。H1～H4 仅存在于原理图，未计入 PCB 清单。')
    columns = [32, 88, 246, 450, 570, width - 32]
    headers = ['位号', '数值 / 型号', '封装', 'LCSC 编号', '装配']
    top = height - 86
    row_h = 29
    c.setFillColorRGB(.91, .94, .97)
    c.rect(columns[0], top - row_h, columns[-1] - columns[0], row_h, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    c.setFont('CJK', 10)
    for x, text in zip(columns, headers):
        c.drawString(x + 6, top - 19, text)
    for index, row in enumerate(bom, 1):
        y = top - index * row_h
        c.setStrokeColorRGB(.8, .82, .85)
        c.line(columns[0], y - row_h, columns[-1], y - row_h)
        footprint = row['footprint']
        # Short, unambiguous package names, with full names in the JSON/Markdown BOM.
        package = 'SOT-23-6' if row['ref'] == 'U1' else 'SMA / DO-214AC' if row['ref'] == 'D1' else 'SOD-123FL' if row['ref'] == 'D2' else '7.0 x 6.6 mm' if row['ref'] == 'L1' else footprint
        values = [row['ref'], row['value'], package, row['lcsc'] or '未指定', '焊接' if row['populate'] else '不焊 / DNP']
        for x, text in zip(columns, values):
            c.drawString(x + 6, y - 19, text)
    c.setFont('CJK', 10)
    c.drawString(32, 95, '通用阻容未绑定完整采购型号；选料前应核对耐压、容差、介质、直流偏压与温度等级。')
    c.drawString(32, 76, '本清单由当前原理图属性与 PCB 实际位号交叉生成。完整封装名称见 hardware/bom/README.md。')
    c.setFont('CJK', 9)
    c.drawString(32, 20, '5 / 5   C6 的 N/C 为不装配标记；并不代表该预留焊盘未连接网络。')
    c.save()
    wrapper = pymupdf.open(stream=buffer.getvalue(), filetype='pdf')
    target.insert_pdf(wrapper)
    target.set_metadata({'title': 'TPS54202 24V to 5V - PCB and assembly', 'author': 'jhwi0424'})
    out = ROOT / 'output/pdf/pcb-current.pdf'
    target.save(out, garbage=4, deflate=True)
    for i, page in enumerate(target):
        page.get_pixmap(matrix=pymupdf.Matrix(1.4, 1.4)).save(ROOT / f'tmp/pcb-reading-{i+1}.png')
    # Repository previews render the native vector geometry, without raster editing.
    for page_no, name in [(3, 'pcb-top.png'), (4, 'pcb-bottom.png')]:
        source[page_no].get_pixmap(matrix=pymupdf.Matrix(15, 15)).save(ROOT / 'docs/images' / name)
    print(out)


if __name__ == '__main__':
    build()

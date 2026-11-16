# 版本与网表整理记录

发布日期：2026-11-17。工程导出软件：嘉立创 EDA 专业版 V4.1.78。

| 资料 | 来源 | 状态 |
| --- | --- | --- |
| `hardware/latest/TPS54202_24V_5V_396VH_real.epro2` | 当前打开的云端 `TPS54202 DCDC 24-5 396VH real` | 最新发布基准，含原理图、PCB、库和空面板 |
| `hardware/history/first-dcdc-schematic.epro2` | 用户最初放入目录的“我画的第一块DCDC.epro2” | 原始字节保留，只有原理图和库 |
| `hardware/netlists/schematic-current.enet` | 从最新版原理图重新原生导出 | 16 个有位号元件 |
| `hardware/netlists/pcb-current.json` | 由脚本读取最新版 PCB 的 `COMPONENT` / `ATTR` / `PAD_NET` | 12 个元件，28 个引脚 |

## 差异

原理图有 H1、H2、H3、H4 四个 2.54mm 排针位号；PCB 中已无这四个元件，使用板边露铜区域连接外部电源和负载。源工程保留此实际状态，本次没有增删原理图元件或改动 PCB 布线。

U1、D1、D2、L1、C1～C6、R3、R4 共 12 个公共元件的 28 个引脚逐项对比没有逻辑网络分配差异。U1.5（EN）的空网络按留空记录；C6 的两端仍有网络，`N/C` 仅为不焊标记。

旧网表没有被当作最新版复用。原生原理图网表和从当前 PCB 重新提取的网表分别保留，并通过 `consistency-report.json` 记录校验范围与输入哈希。不要将“公共元件网络一致”解释为整个工程完全同步。

## PDF 处理

原理图 PDF 保留嘉立创原生矢量输出。原生 PCB PDF 的默认 BOM 有乱码、重叠，且各页物理尺寸不同；发布的 PCB PDF 将有效板图放大至 A4 横向阅读页，并用当前 PCB BOM 重排最后一页。没有改变原始板图几何；不是 1:1 制造文件。

未发布 Gerber 压缩包。当前源工程存在上述接口差异，且本次尚未执行制造前 ERC/DRC 签核；如需制造，应在确认接口实现、完成检查后，从最新版 PCB 重新导出 Gerber 和钻孔文件。

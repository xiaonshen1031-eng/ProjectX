# 项目结果可视化示例

图册收录 24 类图型。每类均提供中英文版本，分别用 MATLAB 导出 EMF、用 Python 导出 PNG，共 96 份原图。

两个后端读取同一份教学数据，数值来自解析函数和固定随机种子。资源分配示例按 1 h 时段给出 kW 功率，逐时积分为 kWh。容量上限采用示例峰值的 1.12 倍。其余示例的单位随指标定义。用于展示画法的数据全部为合成示例。

| 图型 | 图中的关系 |
| --- | --- |
| 资源调度甘特、功率和容量余量 | 淡色窗口包含逐时分配，右列给电量。下方用同一时轴读分组功率、上限和最小余量。 |
| 多阶段分配与流量平衡 | 流带连接三级节点，节点值和共同总量可核对守恒。 |
| 雨云分布与区间比较 | 把密度、观测分布、四分位区间和尾部范围放在同一比较中。 |
| 多指标平行坐标 | 在统一尺度下连接多项指标，呈现不同方案的结构和组内分布。 |
| 空间场与节点网络 | 网格按选区截取，场强和节点连接使用同一坐标系。右侧读同一场上的节点采样。 |
| 可行域与状态投影 | 等比例坐标展示到最近可行点的路径。右侧给欧氏位移，字母 E、L、F 对应投影时等号成立的约束。 |
| 轨迹包络与约束余量 | 比较均值与 P90 对应的余量，在同一时间轴上定位最紧时刻。 |
| 条件分布山峦图 | 沿条件展开分布形状，用中位数和四分位距呈现位置与离散程度。 |
| 弦带与关系矩阵 | 弦带宽度和矩阵来自同一权重。矩阵描边、弦带着色突出所有并列最大值。 |
| 聚类关系矩阵 | 统一聚类树与矩阵的对象顺序，呈现关系分组、方向与强度。 |
| 周期响应与工况间极差 | 环带以小时为中心，由内向外对应 C01–C04。右侧用同一小时的最大值减最小值定位工况分化。 |
| 校准与分辨联合诊断 | 结合校准区间、各区间样本量和类别概率分布，分析预测表现。 |
| 时频结构与频率功率 | 对齐信号、时频结构和各频率的窗口功率合计。 |
| 配对差异与效应量森林 | 每工况使用成对差，显示分布与均值区间。端点和符号区分区间全在零值一侧或跨零。 |
| 容量约束下的负荷持续曲线 | 对照移峰前后的负荷排序，累计超限小时及电量。 |
| 约束饱和日历 | 逐日逐时区分余量充足、接近上限和超限，右侧给出每天的时长汇总。 |
| 调节能量收支 | 用有符号增量核对移峰、储能和节能的影响，再核对基准及调节后的购电量。 |
| 调节后负荷反弹 | 对齐控制开始和回补窗口，按配对工况积分削减量及回补量。 |
| 温控负荷的热滞回 | 在室温与功率图上读出开停机阈值，再在时间轴上核对每次切换。 |
| 成本与未供电量的权衡 | 在同一场景集上核对 56 个配置，用非支配边界标出满足双限值的最低成本方案。 |
| 支路退出后的负荷转供 | 沿线路检查停运、转供和未供节点。余量变化解释为什么转供后仍有负荷未恢复。 |
| 备用要求的边际代价 | 台阶对应已报价的分段备用资源。将台阶与各档已用容量配对，判断多买 1 MW 会调用哪一档。 |
| 多步预测误差与覆盖 | 对相同样本计算两个版本的绝对误差之差。中间 50% 为配对差的四分位距，下方给出各格配对数和缺测状态。 |
| 调节响应时延与超时 | 在给定时限处比较尚未执行的比例。用同一批指令的确认、执行阶段平均时长解释超时变化。 |

在仓库根目录运行：

```powershell
python -m pip install -r skill/senior-projectx/requirements.txt
python gallery/engineering_examples.py --check
python gallery/verify_evidence.py
python gallery/build_bilingual.py
matlab -batch "addpath('gallery'); build_matlab([],'zh'); build_matlab_extra([],'zh'); build_matlab([],'en'); build_matlab_extra([],'en')"
matlab -batch "addpath('gallery'); build_matlab_engineering([],'zh'); build_matlab_engineering([],'en')"
python tools/prepare_bilingual_gallery.py
python tools/audit_bilingual_fonts.py
python tools/verify_site.py
```

`verify_evidence.py`复算流带几何和节点守恒、可行投影、区间、计数及重点标注。`build_bilingual.py`生成 48 张 2400×1440 PNG。MATLAB 使用 Windows 原生 `print -dmeta -vector` 导出 48 张 EMF。`prepare_bilingual_gallery.py`读取实际 PNG 和 EMF，等比例生成浏览器预览并记录原图格式、哈希和矢量检查结果。

Python 原图位于 `docs/downloads/figures/python/`，MATLAB 原图位于 `docs/downloads/figures/matlab/`。网页提供等比例 WebP 预览。完整图型索引位于 `catalog.json`。工程算例由 `engineering_examples.py` 生成 `engineering-data.json`，包含复算数据与两种后端共用的图形坐标。模板依据数据绘制坐标轴、标记、路径及文字。

EMF 导出和预览需要 Windows 上的 MATLAB 以及支持 Windows 元文件的 Pillow。中文使用微软雅黑加粗，英文、数字、单位与符号使用 Times New Roman 常规体。十张工程图把 166 mm 设为阅读宽度，轴标题约 9.4 pt，刻度约 8.2 pt。逐张查看缩放后的轴题、刻度、图例与标注，确认中英文布局。字体核查同时检查 Python 字形与 EMF 原生字体记录。

Copyright © NCEPU-Senior · Author: XiaoN

两套后端共用 `figure-palette.json`。墨黑用于结构和限值，颜色按图中的分组、变化方向或连续数值选用。黄菱形只标选定极值。区间和轨迹同时用端点、形状或线型承载判断。中英文字段及字体设置位于 `figure-language.json`，英语图件保留原路径，中文图件位于对应的 `zh/` 目录。

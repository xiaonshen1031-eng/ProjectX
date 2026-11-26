# 项目结果可视化示例

这里提供14类图型的中英文版本，以及两套实现：**MATLAB绘制EMF**、**Python绘制PNG**，共56份原图。每种图型用于表达一种或几种相互联系的结果关系。

两个后端读取同一份教学数据，数值来自解析函数和固定随机种子。资源分配示例按 1 h 时段给出 kW 功率，逐时积分为 kWh。容量上限采用示例峰值的 1.12 倍。其他指标按定义使用归一化量或 a.u.。

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

在仓库根目录运行：

```powershell
python -m pip install -r skill/senior-projectx/requirements.txt
python gallery/verify_evidence.py
python gallery/build_bilingual.py
matlab -batch "addpath('gallery'); build_matlab([],'zh'); build_matlab_extra([],'zh'); build_matlab([],'en'); build_matlab_extra([],'en')"
python tools/prepare_bilingual_gallery.py
python tools/audit_bilingual_fonts.py
python tools/verify_site.py
```

`verify_evidence.py`复算流带几何和节点守恒、可行投影、区间、计数及重点标注。`build_bilingual.py`生成 28 张 2400×1440 PNG。MATLAB 使用 Windows 原生 `print -dmeta -vector` 导出 28 张 EMF。`prepare_bilingual_gallery.py`读取实际 PNG 和 EMF，等比例生成浏览器预览并记录原图格式、哈希和矢量检查结果。

Python原图位于`docs/downloads/figures/python/`，MATLAB原图位于`docs/downloads/figures/matlab/`。网页使用等比例WebP预览，下载保留各自原生格式。新增8种图型的实现位于`build_python_extra.py`和`build_matlab_extra.m`，完整图型注册表位于`catalog.json`。

EMF导出和预览需要Windows上的MATLAB及支持Windows元文件的Pillow。中文使用微软雅黑加粗，英文、数字、单位与符号使用Times New Roman常规体。Python采用分别指定字体的文字段，MATLAB采用TeX字体段；字体核查同时检查Python实际字形和EMF中的原生字体记录。

Copyright © NCEPU-Senior · Author: XiaoN

两套后端共用 `figure-palette.json`。墨黑用于结构和限值，颜色按图中的分组、变化方向或连续数值选用。黄菱形只标选定极值。区间和轨迹同时用端点、形状或线型承载判断。中英文字段及字体设置位于 `figure-language.json`，英语图件保留原路径，中文图件位于对应的 `zh/` 目录。

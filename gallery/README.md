# 项目结果可视化示例

这里提供14类图型的中英文版本，以及两套实现：**MATLAB绘制EMF**、**Python绘制PNG**，共56份原图。每种图型用于表达一种或几种相互联系的结果关系。

所有数值均由`build_python.py`与`build_python_extra.py`中的解析函数和固定随机种子独立生成。两个后端读取相同的图型数据。

| 图型 | 图中的关系 |
| --- | --- |
| 资源调度甘特与功率分解 | 连接各对象的可用窗口、实际分配和分组功率，解释总体变化的来源。 |
| 多阶段桑基流图 | 用相连的流带展开多阶段分配，保持各阶段的总量对应。 |
| 雨云分布与区间比较 | 把密度、观测分布、四分位区间和尾部范围放在同一比较中。 |
| 多指标平行坐标 | 在统一尺度下连接多项指标，呈现不同方案的结构和组内分布。 |
| 空间场与节点网络 | 把连续空间分布与节点连接放在同一坐标系中，观察局部强度与网络结构。 |
| 可行域与状态投影 | 同时呈现约束边界、状态投影路径与位移，说明状态如何进入可行区域。 |
| 轨迹包络与约束诊断 | 轨迹与分布包络对应上界，再用同一时间轴展开约束余量。 |
| 条件分布山峦图 | 沿条件展开分布形状，用中位数和四分位距呈现位置与离散程度。 |
| 弦带与关系矩阵 | 弦带宽度与矩阵权重对应，连接整体网络结构和具体的成对关系。 |
| 聚类关系矩阵 | 统一聚类树与矩阵的对象顺序，呈现关系分组、方向与强度。 |
| 环形时序分布 | 沿环形时间轴比较周期变化，由内向外对应四种条件。 |
| 校准与分辨联合诊断 | 结合校准区间、各区间样本量和类别概率分布，分析预测表现。 |
| 时频结构与频带能量 | 对齐原始信号、时频结构和频带能量，展开频率随时间的变化。 |
| 配对差异与效应量森林 | 在相同条件下展示配对差异分布、均值和区间，比较条件间的变化。 |

在仓库根目录运行：

```powershell
python -m pip install -r skill/senior-projectx/requirements.txt
python gallery/build_bilingual.py
matlab -batch "addpath('gallery'); build_matlab([],'zh'); build_matlab_extra([],'zh'); build_matlab([],'en'); build_matlab_extra([],'en')"
python tools/prepare_bilingual_gallery.py
python tools/audit_bilingual_fonts.py
python tools/verify_site.py
```

`build_bilingual.py`读取仓库中的两份独立示意数据，生成28张2400×1440 PNG。MATLAB读取相同数据，通过Windows MATLAB原生`print -dmeta -vector`导出28张EMF。`prepare_gallery.py`从实际PNG和EMF生成浏览器预览，并记录原图的格式、哈希和矢量对象检查结果。

Python原图位于`docs/downloads/figures/python/`，MATLAB原图位于`docs/downloads/figures/matlab/`。网页使用等比例WebP预览，下载保留各自原生格式。新增8种图型的实现位于`build_python_extra.py`和`build_matlab_extra.m`，完整图型注册表位于`catalog.json`。

EMF导出和预览需要Windows上的MATLAB及支持Windows元文件的Pillow。中文使用微软雅黑加粗，英文、数字、单位与符号使用Times New Roman常规体。Python采用分别指定字体的文字段，MATLAB采用TeX字体段；字体核查同时检查Python实际字形和EMF中的原生字体记录。

Copyright © NCEPU-Senior · Author: XiaoN

语言与字体定义位于`figure-language.json`。Python中文版本通过`chart_language.py`处理混排，MATLAB中文版本通过`apply_figure_language.m`处理混排。英文图件保留原路径，中文图件存放于各绘图工具目录下的`zh/`；浏览器放大预览与原图下载随语言同步切换。

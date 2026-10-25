# 复杂图表类型演示

这里提供六类图型的两套实现：**MATLAB绘制EMF**、**Python绘制PNG**。

所有数值均由 `build_python.py` 中的解析函数和固定随机种子独立生成，用于说明图型的表达方式。

| 图型 | 图中的关系 |
| --- | --- |
| 轨迹包络与约束诊断 | 参考轨迹、分布包络、约束上界和逐时余量 |
| 条件分布山峦图 | 八种条件的密度、中位数和四分位距 |
| 弦带与关系矩阵 | 八组对象的联系强度及对应的成对权重 |
| 聚类关系矩阵 | 十二个变量的相关系数与同序聚类树 |
| 空间场与节点网络 | 解析空间场、六边形网格、节点和连接 |
| 可行域与状态投影 | 多重约束、等值线、投影路径和位移 |

在仓库根目录运行：

```powershell
python -m pip install -r skill/senior-projectx/requirements.txt
python gallery/build_python.py
matlab -batch "addpath('gallery'); build_matlab"
python tools/prepare_gallery.py
```

第一条绘图命令生成独立的示意数据及六张2400×1440 PNG。MATLAB读取同一份示意数据，通过Windows MATLAB原生 `print -dmeta` 导出六张EMF。最后一条命令从实际图件生成浏览器预览和格式清单。

Python原图位于 `docs/downloads/figures/python/`，MATLAB原图位于 `docs/downloads/figures/matlab/`。网页使用等比例WebP预览；原图下载保留各自格式。

EMF导出和预览需要Windows上的MATLAB及支持Windows元文件的Pillow。图中英文和数字使用Times New Roman。

Copyright © NCEPU-Senior · Author: XiaoN

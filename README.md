# ProjectX

ProjectX 是面向委托研究的开源技能。研究助手读取任务书后，用已有数据建立模型并复算关键约束。报告依据客户模板编排，便于读者从工程判断查到对应图件和计算条件。

[访问网站](https://xiaonshen1031-eng.github.io/ProjectX/) · [下载技能 v1.3.3](https://xiaonshen1031-eng.github.io/ProjectX/downloads/Senior-ProjectX-v1.3.3.zip) · [完整技能](skill/senior-projectx/SKILL.md) · [绘图源码](gallery/README.md)

Copyright © NCEPU-Senior · Author: XiaoN

## 项目工作流

| 阶段 | 主要工作 | 输出 |
| --- | --- | --- |
| 界定范围 | 从任务书提取客户需要据以决策的工况 | 待回答的工程问题 |
| 准备数据 | 核对时段、单位、缺测和对象覆盖 | 与模型对应的数据 |
| 建立模型 | 把运行条件写成变量之间的关系 | 可求解的模型 |
| 复算结果 | 代回原约束，核对工况比较所用条件 | 比较结果及复算脚本 |
| 解释发现 | 找出容量或其他约束何时起作用 | 图表和工程判断 |
| 编排报告 | 让图表和判断在客户模板中互相对应 | 技术报告及支撑材料 |

Word 流程支持 MathType 原生公式、三线表及图题交叉引用。PPT 流程按照客户模板布置工况和结果，可核对原生图表、嵌入工作簿及原比例页面。

v1.3.3 的结果分析直接说明时段负荷、容量余量及运行后果。充电样章用单车移时解释时段容量如何变化，再由全站可供电量上界说明高需求工况的电量缺口。 [选图与模板](skill/senior-projectx/references/project-engineering-figures.md) · [结果分析](skill/senior-projectx/references/project-results-analysis.md) · [版本验证](skill/senior-projectx/references/release-validation.md)

## 结果可视化

工程图册提供 24 类示例，可按用途浏览缩略图或搜索中英文术语。每类均提供中文和英文的 Python PNG、MATLAB EMF，共 96 份原图。中文图中汉字采用加粗微软雅黑，拉丁文和数字采用常规 Times New Roman。

| 用途 | 图型 |
| --- | --- |
| 时序与调度 | 轨迹包络、周期响应、时频图、逐时资源分配、负荷持续曲线、约束饱和日历、调节后负荷反弹 |
| 分布比较 | 条件分布山峦图、雨云分布与区间比较、调节响应时延与超时 |
| 关联与构成 | 成对关系弦图、聚类关系矩阵、桑基流图、平行坐标、调节能量收支、温控负荷热滞回 |
| 空间与约束 | 空间场节点采样、可行域投影、支路退出后的负荷转供 |
| 评估对比 | 校准区间、配对差分布、成本与未供电量权衡、备用要求的边际代价、多步预测误差与覆盖 |

图册采用固定种子和解析模型生成的演示数据。 [数据与绘图命令](gallery/README.md)

## 使用

下载并解压技能包，让本地研究助手读取 `senior-projectx/SKILL.md`。

> 请用 Senior-ProjectX 处理任务书中我负责的部分。用已有数据建模并独立复算，说明哪些工况改变了工程判断。按客户模板整理技术报告，附计算源码。

完整技能说明见[SKILL.md](skill/senior-projectx/SKILL.md)。Python 工具需要 3.10 或更新版本，依赖见 [requirements.txt](skill/senior-projectx/requirements.txt)。MATLAB 的 EMF 导出使用 Windows MATLAB。原生 Office 和 MathType 处理使用已配置的本地环境。

## 网站源码

静态网站位于`docs/`，由GitHub Pages发布。可在本地预览：

```powershell
python -m http.server 8769 --directory docs
```

技能源文件位于`skill/senior-projectx/`。`tools/build_release.py`生成技能下载包，`tools/prepare_gallery.py`生成图件预览与清单，`tools/verify_site.py`检查公开资源、下载完整性、原图格式和发布范围。

## 许可

ProjectX代码与演示图件采用[MIT许可](LICENSE)，Manrope字体采用[SIL Open Font License](docs/assets/fonts/OFL.txt)。

网站中文采用本地加载的Noto Sans SC字形子集，依据[SIL Open Font License](docs/assets/fonts/NotoSansSC-OFL.txt)分发；字体构建脚本见`tools/prepare_webfont.py`。

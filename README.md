# ProjectX

**把项目研究，做到交付。**

ProjectX是面向委托研究与工程技术项目的Skill，配合能够读取文件、运行脚本的研究助手使用。从任务书、已有数据与客户模板开始，衔接建模计算、结果分析、技术报告和模板PPT。

[访问网站](https://xiaonshen1031-eng.github.io/ProjectX/) · [下载技能](https://xiaonshen1031-eng.github.io/ProjectX/downloads/Senior-ProjectX-v1.1.0.zip) · [完整技能](skill/senior-projectx/SKILL.md) · [可视化源码](gallery/README.md)

Copyright © NCEPU-Senior · Author: XiaoN

## 项目工作流

| 阶段 | 主要工作 | 输出 |
| --- | --- | --- |
| 任务与资料 | 阅读任务书、合同内容、已有成果与客户模板 | 研究问题、承担范围与交付清单 |
| 数据与适配 | 数据清理、时间对齐、尺度适配和总量核查 | 模型输入、参数表与处理脚本 |
| 模型与方法 | 定义变量、目标、约束和关键关系，选择计算方法 | 数学模型与可计算的表达 |
| 计算与校核 | 求解、预测或仿真，组织公平比较并独立复核 | 计算结果、比较指标与可复算代码 |
| 结果与分析 | 比较总体与条件差异，分析时空变化和敏感性 | 结果图表、连续分析与工程结论 |
| 成果交付 | 按模板整理报告与汇报，检查公式、图表和页面 | 技术报告、PPT、图件与计算材料 |

报告工作流包括正文、黑色三线表、MathType居中编号公式和参考文献处理；PPT工作流包括学习客户模板的语言与排版、组织模型与算例、检查可编辑对象和页面。技能还包含经验维护与回归检查要求。具体计算与Office交付使用本地已配置的工具。

## 结果可视化

图表用于表达项目结果之间的关系。网站展示14类图型，可切换**中文 / English**，同时支持**MATLAB绘制EMF**、**Python绘制PNG**，共56份原图。中文标注采用微软雅黑加粗，英文、数字与单位采用Times New Roman常规体。

| 用途 | 图型 |
| --- | --- |
| 时序与调度 | 轨迹包络与约束诊断、环形时序分布、时频结构与频带能量、资源调度甘特与功率分解 |
| 分布比较 | 条件分布山峦图、雨云分布与区间比较 |
| 关联与构成 | 弦带与关系矩阵、聚类关系矩阵、多阶段桑基流图、多指标平行坐标 |
| 空间与约束 | 空间场与节点网络、可行域与状态投影 |
| 评估对比 | 校准与分辨联合诊断、配对差异与效应量森林 |

演示采用解析函数与固定随机种子独立生成的数据。图型数据、实现和复现命令见[gallery](gallery/README.md)。

## 使用

下载技能包并解压，保留`senior-projectx`目录结构，让本地研究助手读取`SKILL.md`。可以从这段提示开始：

> 请使用Senior-ProjectX，先阅读我的项目任务书、已有数据和客户模板，梳理我负责部分的研究对象、模型输入与输出，再完成建模计算、对比分析和结果阐释。图表按问题选择，使用MATLAB导出EMF或Python导出PNG，最后按模板整理技术报告、PPT与计算源码。

完整技能说明见[SKILL.md](skill/senior-projectx/SKILL.md)。Python绘图使用科学计算与绘图库；MATLAB的EMF导出使用Windows MATLAB。原生Office与MathType处理使用已配置的本地环境。

## 网站源码

静态网站位于`docs/`，由GitHub Pages发布。可在本地预览：

```powershell
python -m http.server 8769 --directory docs
```

技能源文件位于`skill/senior-projectx/`。`tools/build_release.py`生成技能下载包，`tools/prepare_gallery.py`生成图件预览与清单，`tools/verify_site.py`检查公开资源、下载完整性、原图格式和发布范围。

## 许可

ProjectX代码与演示图件采用[MIT许可](LICENSE)，Manrope字体采用[SIL Open Font License](docs/assets/fonts/OFL.txt)。

网站中文采用本地加载的Noto Sans SC字形子集，依据[SIL Open Font License](docs/assets/fonts/NotoSansSC-OFL.txt)分发；字体构建脚本见`tools/prepare_webfont.py`。

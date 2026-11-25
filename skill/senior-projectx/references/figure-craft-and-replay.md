# 工程图件的证据、构图和复核

新增图、实质改图及复杂插图复核时使用本指南。先打开所给参考图、原生文件及实际导出，识别它如何组织主关系、局部详图、比较条件、注释和空白。复用能说明同类问题的视觉关系，使用本项目的对象、参数和时序。已接受的图以用户确认的源文件及修订为准。

| 用途 | 读图任务 | 适合的图面 |
| --- | --- | --- |
| 背景与机制 | 哪些物理对象处在什么条件，为什么触发调节 | 可辨认的物理结构与对应位置的量、约束或运行状态 |
| 计算流程 | 各步处理哪组量，产物进入哪里 | 一条主路径，关键端口标传输量，局部放大两三个实际运算 |
| 结果比较 | 条件和对象相同的情况下发生了什么 | 真实区间加估计值、对齐的条件图、带约束的完整轨迹 |
| 决策校核 | 分支可达性、风险边界及最后动作怎样相连 | 在共享限值对齐各分支区间和动作。只有两个区间严格分开时才连出支配分支 |

分支在可见端口接入，区分真正汇合和互不相交的交叉。用数据支持的信号片段、区间、状态或局部计算表明操作。原生交付走 [可编辑图示](editable-diagram-playbook.md)。

先在当前坐标补充能改变读图结论的真实信息，如区间端点、约束余量、共同估计引导线或成对变化。局部放大使用原对象、原坐标和明确范围。保留负效应、等值、未观测、不可行及超扫描范围等状态。照片和测量图像保留原像素和比例。裁切明确半开像素边界、样本标识和对应区域。标量场说明色标范围及分界值。

## 颜色、物理尺寸和导出

[颜色库](../templates/research_figure_palette.json)提供墨黑、碧绿、钴蓝、紫、玫红、亮黄和少量浅色底。结构线与说明字通常用墨黑，颜色区分数据层、类别、状态或可解释的区域。浅色点使用深边。配合符号、线型或短标签，使灰度中仍可跟读。连续量选择有序色标，有符号的量围绕零值、基准或阈值设置色标中心。客户指定色序或已经确认的颜色含义随稿保留。

先确定插入宽度，按实际字形布置边距、轴、色条和图例。报告图通常用微软雅黑加粗或已批准的中文替代，英文和数字用 Times New Roman。轴标签 9–11 pt、刻度与图例 8–10 pt 按最终尺寸核对，PPT 按实际观看尺寸另定。保留原始宽高比，优先调整布局再缩小字号。图例放在已确认的空白或共用区域。

PDF/SVG 检查文字对象、目标字体和矢量几何。EMF 以实际 Word 渲染为准。PNG/TIFF 以最终像素和插入尺寸为准。保持冻结输入和作图入口相连，用现有清单记录图号、数据、单位、条件和导出物。矢量容器中的真实位图仍按像素核查。

## 可执行模板

从解压目录可运行这些例子。示例用明确标识的教学数据，真实计算使用自己的记录和所需格式。

~~~powershell
python templates/research_figure_evidence.py --demo --recipe sensitivity --output-dir preview
python templates/research_figure_evidence.py --demo --recipe release --output-dir preview
python templates/research_workflow_replay.py --demo --output-dir preview
python templates/research_figure_composition.py --blank-slots --output-dir preview
python scripts/audit_figure_layout.py preview/project_sensitivity_illustrative.layout.json --pretty
~~~

- **区间端点。** 将 --demo 换成 --config <json>。提供统一 levels、metrics 和各指标的 rows，行字段为 level、estimate、lower、upper。reference 表示等值或阈值。估计确实相等时才写 common_estimate_levels。默认在原坐标标出上端点，需要独立端点视图时设 endpoint_view 为 separate。抽样单位和区间方法在相邻图文交代。
- **限值与行动。** 提供 cases。每例 name 为名称，old、added 为有效区间，released_upper 为行动上界。脚本计算 max 区间，保留越限、未越限及无法判定，记录分支关系。限值不是零时用 reference 声明。
- **运算流程。** 输入三条已归一化的 reports、归一权重 weights、逐步区间 lower、upper 和可选 focus_index（从 0 开始）。这例展示三条输入加权后投影到独立区间。其他方法沿用主路径和局部算子的画法，使用实际运算。
- **源像素、配对效应和待填布局。** [绘图组合](../templates/research_figure_composition.py)支持 --image-plate-config、--effect-config、--blank-slots。配对效应使用保存的估计与匹配样本。空面板仅供版面审查。

真实结果及流程配置用 provenance.kind 和 provenance.source 记录保存记录的类型及位置。结果和流程支持 --language zh|en。结果图配置 canvas 可指定 width_mm、font_pt 或字体，流程模板支持 --width-mm、--height-mm、--font-pt。

布局清单记录 Agg 实测的文字边界、画布、面板和交付文件哈希。检查器核对裁边、重叠和声明的间距、对齐、缩放量。灰度、标记覆盖、可编辑性及工程含义须看实际导出。最后复核实际插图页。格式缺陷走 [显示修复](figure-display-repair.md)。

绘图组合、结果与流程模板及诊断脚本改编自 XiaoN 的 NPS Research Paper v3.2.4，可随本技能独立运行。

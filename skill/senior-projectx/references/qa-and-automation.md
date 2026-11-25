# 质量检查与交付工具

按当前任务选用工具，不为局部文字或版式修改重新计算无关结果。自动检查定位候选问题，不能替代技术判断、原生对象核对或实际页面阅读。

## 数值与图件

`project_research.py` 支持任务定义、字段与单位审查、有限结构的计算、独立约束复算和实际依赖记录。`assess_result_coherence.py` 可辅助检查已有表格数值关系。`validate_experiment_manifest.py` 和 `validate_figure_manifest.py` 读取实际需要的计算、比较或图件清单；使用时将 `manuscript_mode` 声明为 `project`。图型的字段检查不能代替看图，概念图也不需虚构数值输入。

## 文字与引用

```powershell
python scripts/check_writing_quality.py report.docx --manuscript-mode project --language chinese --require-clean --json-out review/writing.json
python scripts/check_reference_format.py report.docx --metadata
```

文字检查后阅读上下文和全文，保留事实、条件、约束与负面结果；详细规则见 [语言与定稿要求](writing-and-release.md)。参考文献工具用于编号、元数据等辅助检查，不能据此声称已满足GB/T 7714的所有著录规则。对照当前适用标准、原始出版或数据记录及首次引用顺序逐项核查。

## Word图件与公式

`replace_docx_figures.py` 用于有确切图题定位的图件替换，执行前打开基线页核对槽位。`audit_docx_submission.py` 检查媒体、对象及声明的公式后端。原生公式本体、保存重开、显示字号和实际页面各有对应的验证。

`project_equation_layout.py` 只调整普通单栏正文中的原生公式与编号布局，不转换公式、不核定其数学含义。具体边界见 [研究与交付指南](project-research-playbook.md)。最终文件保存、关闭、重开后导出PDF，检查全部实际页面，尤其公式位置、图例、字体、三线表、分节和图题。

局部断页、分节、页码和数字引文处理按 [Word 分页与引文](word-pagination-and-citation-release.md) 检查。需要核对已批准的替换内容，按 [定点修订与对象保全](fixed-revision-integrity.md) 比较源稿和拟交付稿。客户明确指定不设参考文献时采用相应引文检查配置。

## 客户模板汇报

按 [汇报制作与复核](project-presentation-playbook.md) 查看实际导出页。全页比例、每个图名及图例、连接线、文本容纳和图表数据要分别核对。`audit_pptx_evidence.py` 读出局部布局修订前后的数据类对象差异，Office 保存重开和编辑持久性另作实际检查。

## 完整研究与局部修订

`audit_project_delivery.py` 面向配套的连续分配算例，检查数据、求解、独立校核、图件、公式、PDF及当前DOCX语言。对于其他模型，按同类检查原则适配，不能为通过算例工具而伪造最优求解状态或无关输入。纯文字或格式修订复用未受影响的数值依据，同时核对最终文件中的改动和原生对象保存。

样例的视觉审阅记录绑定实际导出的 Word 和 PDF。复核完成后记录 `docx_sha256`、`pdf_sha256`、`reviewer`、`reviewed_pages`、`page_images` 和 `status`。页面图片的相对路径以记录所在目录为基准。改动 Word 后，重新导出并检查受影响的页面，再更新对应的哈希和审阅结果。

`build_delivery_package.py` 按明确的输入清单组合代码、图件和数据，仅在用户需要可复用成果包时使用。内部检查、源数据与最终成果分开保存；交付一个当前版本，不加入多个迭代稿、缓存或私人路径。

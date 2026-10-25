# Office 流程回归

本目录说明可在安装 Microsoft Word、PowerPoint 和 MathType 的 Windows 机器上重现的检查。测试只操作指定材料的副本；不会安装技能或修改 Office 启动目录。

1. 用 `project_demo.py prepare`、`sensitivity` 生成合成计算算例，运行求解、独立约束校核和 `project_report.py figures`。该数据只用于验证工具，实际项目使用自己的输入。
2. 从随包 `templates/project_report.docx` 构建源稿。公式包括行间、正文行内、表头、只有公式的单元格，以及区分大小写的变量；建立有序源清单。
3. 运行以下命令，使用新输出目录：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/project_office_smoke.ps1 -SourceDocx source.docx -SourceManifest equation_source.json -OutputDirectory office_check -Python python -Pptx briefing.pptx
```

源清单兼容 `senior_projectx.project.equation_source.v1` 和 `nps.project.equation_source.v1`，按原始大小写、顺序、上下文和哈希核验。未知版本不自动降级。MathType模板按Word位数发现，也可显式提供 `-MathTypeTemplate`，仅载入当前自建的Word会话。无关用户文档存在时不接管该Word会话。

转换在工作副本中临时给纯公式表格段落加上下文，运行一次 Toggle TeX 后移除上下文，避免表格漏转；源稿不变，已经转换的对象不二次切换。保存关闭重开后，核对所有原生对象和显示编号，包含公式居中、行内基线及表格字号。

转换器按清单的角色字号缩放可编辑对象，正文默认12 pt、表格10.5 pt。`project_mathtype_convert.ps1 -MathTypeFullSizePt` 默认12，须与当前MathType“大小→定义”的Full字号一致；使用其他首选项时按实际值传入。对象缩放后的显示和重开尺寸仍需检查。

4. 从同一个源稿独立转换第二份DOCX。逐公式比较有序MTEF并检查预览、实际Word页面和目标含义。版式调整后用 `rebind_formula_receipt.py` 证明对象内容及预览不变，再绑定最终文件。
5. 用 Word 导出实际PDF，将全部页面渲染为图片并阅读。可使用当前环境的文档渲染工具；没有LibreOffice时可使用已验证的Word导出与Poppler路线，无需安装另一个Office套件。
6. 通过 `prepare_review_evidence.py --help` 所列参数准备实际审阅记录，再用 `audit_native_mathtype.py` 和 `mathtype_authenticity.py` 复核。未实际完成的含义、页面或编辑检查保持待审状态。
7. PowerPoint保存重开并逐页导出，检查图例一行、标题与图名位置、原比例、连接线端点和最终字号。测试副本里编辑原生文本、图表数据、表格单元格及MathType对象并保存，关闭重开检查，再恢复测试值。图表工作簿需能打开；对象数量不等于可编辑性。

可用 `project_ppt_edit_check.ps1 -SourcePptx briefing.pptx -OutputPptx edit_check.pptx -EvidenceJson edit_check.json -ChartSlide 2 -TableSlide 4` 检查原生文本、表格和图表数据编辑后的保存重开。按实际材料选择标题对象、工作表和数值单元格；默认B2仅适用于对应的数据布局。该脚本需要实际演示窗口承载ChartData，嵌入工作簿由PowerPoint保存，不额外调用独立Workbook.Save。它只改新副本并恢复测试值，不修改源稿。MathType实际编辑仍需打开编辑器检查，记录编辑前后MTEF变化与重开结果。

编辑持久性核对完成后，脚本关闭测试文件，将整个测试副本恢复为源稿的相同字节，并记录实际编辑后文件的哈希及恢复方式。这样图表缓存、嵌入工作簿和文本格式一起恢复；不能只恢复单元格却留下旧图表缓存。

两个PPT检查入口均先在文件系统复制，再打开副本；源稿即使已在PowerPoint中打开，也不接管、另存或关闭该源稿。公式更新检查沿用有序源清单，也可在测试副本中由新生成的原生MathType对象替换代表公式；保存关闭重开后，应确认目标MTEF实际改变、其他对象内容不变，并检查对应页面。

## 必须保留的复现信息

Python及Office版本、自动回归通过/失败/跳过数、输入和输出哈希、原生公式数量与逐项对比、实际PDF页数和PPT页数、逐页审阅状态、真实编辑测试结果。私有路径、客户资料、测试生成的二进制文件保存在任务工作区，不写入分发包。

## 复现过的问题

- DOCX属性中 `xsi:type` 的前缀必须绑定；ZIP与普通XML解析成功不代表Word能打开。随包自检检查此项。
- 公式清单版本字符串、大小写、段落顺序与纯公式表格单元格必须一起检查。
- 调整公式编号和报告图后，最终文档的审阅记录需要重新绑定；旧哈希不能复用。
- 图的复杂度来自真实条件、窗口、边界与诊断。简单图换名或套进子图不视为升级。

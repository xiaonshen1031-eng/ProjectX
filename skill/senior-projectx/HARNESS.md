# Senior-ProjectX 经验维护

在处理当前任务时读取与它相关的经验；明确要求优先于默认偏好。经验记录服务于后续建模、写作、图表、原生公式和汇报，不增加本次合同任务。

## 反馈到规则

理解用户指出的具体问题和原因，先修正当前成果，再判断其范围：`one_off` 为一次局部调整，`project` 为当前项目，`domain` 为相同技术问题，`preference` 为稳定偏好，`skill` 为通用工作方式。一次性的裁剪距离、面板数量、区域名称、排名和坐标不提升为全局规则。

用户明确要求升级技能时可沉淀相应经验；其他情况应有重复支持。记录实际原因和适用范围，必要时合并、修订或废弃旧规则。偏好不能覆盖数据事实、任务范围或当前客户模板。

## 维护位置

- `harness/state/skill_state.json` 保存版本、偏好、置信程度与最近一次回归状态。
- `harness/feedback/user_feedback.jsonl` 和 `harness/decisions/decision_log.jsonl` 追加实际反馈及采纳决定。
- `harness/writing/` 保存连贯中文分析的正反例。
- `harness/figures/` 保存图件、PPT与最终尺寸方面的经验。
- `harness/experiments/` 保存数据适配、比较、时序划分和独立复算经验。
- `harness/regression/regression_cases.json` 保存有明确预期与禁止行为的情形。
- `harness/evals/` 保存实际测试结果；`tests/` 为可运行回归。

## 记录命令

```powershell
python scripts/update_harness_state.py feedback --classification preference --feedback "用户的实际反馈" --interpretation "需改变的行为" --root-cause "具体原因" --status promoted
python scripts/update_harness_state.py preference --preference-id project_rule_id --statement "规则及适用条件" --scope project --confidence 1
python scripts/update_harness_state.py regression --case-id project_case_id --task-type project_word --input-summary "触发情形" --expected-behavior "可观察结果" --forbidden-behavior "应避免的结果" --relevant-rule "实际资源位置"
python scripts/update_harness_state.py version --version 1.1.0 --summary "本次实际变化"
```

默认写入本技能的 `harness/`；`--harness-root` 可指定独立维护目录。修改应写在可恢复的副本或受维护的技能目录中，不修改用户原始报告和数据。记录不携带机器私有路径或完整客户资料；文件引用只保留实际有使用者的相对位置。

## 运行回归

```powershell
python scripts/run_project_regressions.py --out regression.json
python scripts/selftest_skill.py --out selftest.json
```

完成规则或脚本修改后，运行相关测试。对本次完整版本交付运行全套 Project 回归，并记录成功、失败、错误和跳过数量；缺少依赖导致的跳过应明确列出。代码或输入未变化且检查已通过时不重复运行。自动检查不能证明报告语言自然、原生公式意义正确或PPT清楚，最终文件仍需实际渲染、重开和人工阅读。

需要完整 Office 流程时，使用 `tests/office/` 中的说明和 `scripts/project_office_smoke.ps1`。只操作创建的副本，不关闭其他用户文件。实际完成原生转换与视觉审阅后才登记通过，不能用对象数量代替检查。

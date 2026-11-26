# 充电分配演示

从技能目录运行以下命令。`demo` 是新建的演示目录，输入为合成的时段负荷与车辆充电需求。缺少 Python 依赖时，运行 `python -m pip install -r requirements.txt`。

## 准备并检查数据

```powershell
python scripts/project_demo.py prepare demo
python scripts/project_research.py audit-data demo/data/periods.csv --schema demo/data/periods_schema.json --out demo/review/periods_audit.json
python scripts/project_research.py audit-data demo/data/vehicles.csv --schema demo/data/vehicles_schema.json --out demo/review/vehicles_audit.json
```

打开 `demo/data/periods.csv` 查看各时段的基础负荷、设备容量和时长。`demo/data/vehicles.csv` 给出各车接入时段、需求电量及功率上限。数据检查结果写入 `demo/review/`。

## 计算分配并复算

```powershell
python scripts/project_research.py solve-allocation --periods demo/data/periods.csv --vehicles demo/data/vehicles.csv --config demo/model/allocation.json --allocation-out demo/data/results/allocation.csv --out demo/data/results/result.json
python scripts/project_research.py validate-allocation --periods demo/data/periods.csv --vehicles demo/data/vehicles.csv --config demo/model/allocation.json --allocation demo/data/results/allocation.csv --result demo/data/results/result.json --out demo/review/validation.json
python scripts/project_demo.py sensitivity demo
```

`allocation.csv` 的每一行对应一辆车在一个时段分配到的充电功率。`validate-allocation` 从该表复算各车的电量和各时段的容量余量。`sensitivity.csv` 汇总不同需求倍率下的求解状态和余量。

## 用结果表绘图

```powershell
python scripts/project_report.py figures --periods demo/data/periods.csv --allocation demo/data/results/allocation.csv --vehicles demo/data/vehicles.csv --sensitivity demo/data/results/sensitivity.csv --output-dir demo/figure/final --manifest-out demo/review/figure_manifest.json
```

在 `demo/figure/final/` 打开生成的 PNG，依次查看逐时负荷与余量、接入窗口与实际分配、不同需求下的容量变化。`demo/review/figure_manifest.json` 记录每张图的输入和输出位置。

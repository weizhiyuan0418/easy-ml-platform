# Example Dataset

`sample_regression_classification.csv` 是一个 UTF-8 示例数据集，用于验证字段配置、导入、训练和预测流程。

## 字段建议

在界面“字段”页按下面配置字段：

| 字段名 | 显示名 | 角色 | 类型 | 候选值 |
|---|---|---|---|---|
| `x` | 数值输入 | 输入 | 数值 | |
| `kind` | 类别输入 | 输入 | 类别 | `A,B` |
| `flag` | 布尔输入 | 输入 | 布尔 | |
| `when` | 日期输入 | 输入 | 日期/时间 | |
| `score` | 数值输出 | 输出 | 数值 | |
| `level` | 类别输出 | 输出 | 类别 | `low,high` |

## 使用流程

1. 启动应用。
2. 在“字段”页创建上表字段。
3. 在“导入”页上传 `examples/sample_regression_classification.csv`。
4. 在“模型”页点击“训练全部输出”。
5. 在“预测”页输入 `x`、`kind`、`flag`、`when`，查看 `score` 和 `level` 的预测结果。

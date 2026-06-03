# Contributing

感谢你参与通用机器学习软件的开发。提交代码前请先确认本地验证通过。

## 本地开发

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe tools\verify_project.py
```

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py test
.venv/bin/python tools/verify_project.py
```

## 提交规范

- 保持源码、JSON、CSV 和文档为 UTF-8 编码。
- 不提交 `.env`、`db.sqlite3`、训练模型、缓存、构建产物或安装包。
- 对影响训练、导入、预测或 API 的改动补充测试。
- Pull Request 描述应说明改动内容、原因和验证命令。

## 代码范围

当前版本聚焦表格型机器学习：数值、类别、布尔、日期/时间字段。文本、图片、时序和深度学习模型暂不属于第一版核心范围。

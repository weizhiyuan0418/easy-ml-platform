# 通用机器学习软件

这是一个独立的新工程，支持用户自定义表格型机器学习项目、字段、数据集、训练任务和预测流程。

## 安装依赖

```powershell
py -3 -m pip install -r requirements.txt
```

## 初始化数据库

```powershell
py -3 manage.py migrate
```

## 可选环境变量

```powershell
$env:DJANGO_SECRET_KEY="your-secret-key"
$env:DJANGO_DEBUG="1"
```

## 启动 Web 版

```powershell
py -3 manage.py runserver
```

浏览器访问 `http://127.0.0.1:8000/`。

## 启动桌面 Web 壳

```powershell
py -3 desktop_main.py
```

## 验证

```powershell
py -3 manage.py test
py -3 tools/verify_project.py
```

## 编码规则

所有源码、JSON、CSV 导入导出均使用 UTF-8 或 UTF-8-SIG 编码，避免中文乱码。

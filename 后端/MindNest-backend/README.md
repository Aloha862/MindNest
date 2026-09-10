# MindNest Backend

MindNest 后端是基于 FastAPI 的智能学习平台服务，负责认证、文件上传、图像识别、题库、错题、学习资料、专注监督、学习报告和管理员功能。

## 服务分层

```text
app/routers       REST API 路由和权限依赖
app/schemas       Pydantic 请求/响应模型
app/models        SQLAlchemy 数据模型
app/services      业务服务、OCR、VLM、YOLO、公式和报告
app/utils         文件、分页、响应和时间工具
scripts/          数据库初始化、演示数据和模型辅助脚本
```

## 主要识别流程

```text
上传文件
  → OpenCV 质量评估与预处理
  → YOLO 版面区域检测
  → OCR 文字识别
  → Pix2Text/启发式公式识别
  → VLM 题目结构化理解
  → 结果归一化与审核状态判定
  → 题目、资料、日志和任务状态持久化
```

## 本地启动

在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ..\..\requirements.txt
Copy-Item .\.env.example .\.env
python scripts\init_data.py
python run.py
```

服务地址：

- 健康检查：`http://127.0.0.1:8000/api/health`
- Swagger：`http://127.0.0.1:8000/docs`
- ReDoc：`http://127.0.0.1:8000/redoc`

默认数据库名为 `mindnest`。真实 OCR、VLM、YOLO/YOLOE 和 Pix2Text 均可通过 `.env` 按需启用。

# 一拍即合 SnapMatch Backend

基于 FastAPI + MySQL + SQLAlchemy 的课程设计后端，定位为“面向学习场景的多模态智能题目理解与个性化复习平台”。系统提供作业/试卷/错题图片上传、OpenCV 图像预处理、YOLO 区域检测、OCR/公式识别、视觉语言模型结构化分析、题目卡片管理、知识点统计、错题本和管理员后台接口。

## 技术栈

- Python 3.10+
- FastAPI、Uvicorn
- MySQL 8.x
- SQLAlchemy 2.x
- Pydantic v2
- JWT：python-jose
- 密码加密：passlib[bcrypt]
- 文件上传：python-multipart
- 图像处理：OpenCV
- OCR：优先 PaddleOCR，默认 mock fallback
- YOLO：题目、公式、解析等视觉区域检测，默认 mock，可切换 Ultralytics 权重
- VLM：mock VLM，预留真实模型替换点

## 目录结构

```text
snapmatch-backend
├── app
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── security.py
│   ├── exceptions.py
│   ├── models
│   ├── schemas
│   ├── routers
│   ├── services
│   ├── utils
│   └── uploads
├── scripts
│   └── init_data.py
├── requirements.txt
├── .env.example
└── run.py
```

## 环境要求

1. 安装 Python 3.10 或更高版本。
2. 安装 MySQL 8.x。
3. 创建数据库：

```sql
CREATE DATABASE snapmatch DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 安装依赖

```bash
cd E:\code\SnapMatch\后端\snapmatch-backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 数据库配置

复制 `.env.example` 为 `.env`，修改 MySQL 用户名、密码和数据库地址：

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/snapmatch?charset=utf8mb4
SECRET_KEY=please-change-this
```

## 初始化测试数据

```bash
python scripts/init_data.py
```

如果 Python 初始化脚本因为数据库连接配置失败，可以改用纯 SQL 脚本：

```sql
source E:/code/SnapMatch/后端/snapmatch-backend/scripts/init_mysql.sql
```

默认账号：

- 管理员：`admin / 123456`
- 普通用户：`user / 123456`

密码会用 bcrypt 加密后入库，不会明文存储。

## 启动服务

```bash
python run.py
```

也可以直接运行：

```bash
uvicorn app.main:app --reload
```

访问：

- Swagger 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 健康检查：[http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

## 统一响应格式

成功：

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": "2026-05-20 12:00:00"
}
```

分页：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [],
    "total": 100,
    "page": 1,
    "pageSize": 10
  },
  "timestamp": "2026-05-20 12:00:00"
}
```

## 主要接口示例

登录：

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "user",
  "password": "123456"
}
```

上传图片：

```http
POST /api/files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file=<image>
fileType=exam
subjectHint=数学
remark=高数月考
```

启动识别：

```http
POST /api/recognition/start
Authorization: Bearer <token>

{
  "fileId": 1,
  "enablePreprocess": true,
  "enableYOLO": true,
  "enableOCR": true,
  "enableVLM": true
}
```

批量上传：

```http
POST /api/files/batch-upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

files=<image1>
files=<image2>
fileType=exam
subjectHint=数学
remark=批量导入
```

批量识别：

```http
POST /api/recognition/batch-start
Authorization: Bearer <token>

{
  "fileIds": [1, 2, 3],
  "enablePreprocess": true,
  "enableYOLO": true,
  "enableOCR": true,
  "enableVLM": true
}
```

错题与学习资料：

- `POST /api/questions/{questionId}/wrong`：标记错题。
- `GET /api/wrong-records`：查看错题本。
- `GET /api/materials`：查看学习资料。
- `GET /api/questions/tags`：聚合知识点标签。
- `POST /api/recognition/tasks/{taskId}/retry`：重试失败识别任务。

## OpenCV / YOLO / OCR / VLM 说明

当前识别链路为：`OpenCV 图像预处理 -> YOLO 视觉区域检测 -> OCR 文字识别 -> VLM 结构化分析 -> 题目卡片/学习资料生成`。

`app/services/ocr_service.py` 支持三种 OCR 路径：

- `OCR_PROVIDER=qwen`：优先使用百炼视觉模型识别文字和公式，并要求返回 `formulaBlocks.latex`。
- `OCR_PROVIDER=paddle` 或 `PADDLEOCR_ENABLED=true`：使用 PaddleOCR，适合印刷中文和英文，但复杂数学公式不会天然转成 LaTeX。
- 没有配置真实模型或 PaddleOCR 不可用时：自动 fallback 到 mock，保证流程可演示。

`app/services/yolo_service.py` 提供 `detect_layout(image_path)`，默认 mock 检测题目、公式、解析、答案、手写批注等区域，并把结果写入 `recognition_tasks.yolo_result` 和 `model_logs`。YOLO 不负责识别中文内容，只负责检测视觉区域；中文和公式内容仍由 OCR/VLM 处理。

`app/services/vlm_service.py` 当前使用 mock VLM，返回结构化题目数据，用于前后端联调和课程设计展示。后续接入真实视觉语言模型时，保持 `analyze_question(image_path, ocr_text, layout_context=None) -> dict` 返回格式不变即可。

OCR 返回中预留了 `formulaBlocks`、`sections`、`layoutBlocks`，VLM 返回中预留了 `layoutType`、`materialType`、`questionNo`、`options`、`tags` 等字段，用于报告中公式识别、版面分析、OCR 分段和知识点标签展示。前端识别结果页使用 KaTeX 渲染 `formulaBlocks.latex`。

## 切换真实 PaddleOCR

安装 PaddleOCR：

```bash
pip install paddleocr paddlepaddle
```

安装后重启服务，`run_ocr` 会自动使用 PaddleOCR。若初始化或识别失败，仍会 fallback 到 mock OCR。

如果题目中公式较多，推荐 `OCR_PROVIDER=qwen`，因为 PaddleOCR 更偏通用文字识别，不是公式转 LaTeX 模型。课程设计答辩时可以说明：PaddleOCR 用于文本 OCR，公式 LaTeX 由视觉语言模型或后续专用公式识别模型补强。

## 接入真实 YOLO

课程设计演示阶段默认使用 mock YOLO，不需要训练数据即可看到“视觉区域检测”模块。如果你已经训练好了题目版面检测权重，安装 Ultralytics：

```bash
pip install ultralytics
```

把权重放到 `weights/best.pt`，然后在 `.env` 中配置：

```env
YOLO_ENABLED=true
YOLO_MODE=real
YOLO_MODEL_PATH=weights/best.pt
YOLO_CONFIDENCE=0.35
```

建议自定义训练类别：`question`、`sub_question`、`option`、`formula`、`analysis`、`answer`、`diagram`、`table`、`handwriting`。普通 COCO 预训练模型不能直接识别这些试卷版面类别，因此真实 YOLO 效果依赖自定义数据集。

## 接入真实 VLM API

真实模型通过阿里云百炼 OpenAI-compatible 接口调用，密钥不要写死在代码里，统一放到 `.env`。官方示例里的 `DASHSCOPE_API_KEY` 和项目里的 `VLM_API_KEY` 二选一即可，推荐使用 `DASHSCOPE_API_KEY`：

```env
OCR_PROVIDER=qwen
VLM_PROVIDER=qwen
DASHSCOPE_API_KEY=你的真实APIKey
VLM_API_KEY=
VLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
VLM_MODEL_NAME=qwen3.6-plus
VLM_ENABLE_THINKING=true
VLM_STREAM=true
```

当前后端已内置 `openai.OpenAI(base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")` 调用逻辑，并会传入图片、OCR 文本和 YOLO 区域检测结果。配置好 `.env` 并重启后端后即可生效。后续如果要换其他视觉语言模型，建议仍保持 `analyze_question(image_path, ocr_text, layout_context=None)` 返回字段不变，这样题目卡片、学习资料、模型日志和前端页面都不需要大改。

注意：`qwen3.6-plus` 按你提供的示例已配置为默认模型。如果接口返回“不支持 image_url / multimodal input”，说明该模型在你的百炼账号下不是视觉模型，需要把 `VLM_MODEL_NAME` 改成百炼控制台可用的视觉模型，例如 `qwen3-vl-plus` 或 `qwen-vl-plus`。

注意：后端运行时只读取 `.env`，不会读取 `.env.example`。如果模型参数只写在 `.env.example`，上传识别仍会使用 mock 或提示配置缺失。修改 `.env` 后需要重启后端。

## 新增课程设计支撑能力

- 错题本：`wrong_records` 表和 `/api/wrong-records`、`/api/questions/{questionId}/wrong` 接口。
- 学习资料：`learning_materials` 表和 `/api/materials` 接口；上传 `fileType=note` 后识别会生成资料记录。
- 批量处理：`/api/files/batch-upload` 和 `/api/recognition/batch-start`。
- YOLO 视觉检测：`recognition_tasks.yolo_result` 保存区域检测结果，前端识别结果页展示检测框和 OCR 分段。
- 失败重试：`/api/recognition/tasks/{taskId}/retry`。
- 统计增强：管理员首页返回失败任务数、模型调用数、上传趋势、识别趋势、文件类型分布。
- 初始化脚本：`scripts/init_mysql.sql` 和 `scripts/init_data.py` 均包含错题、学习资料、失败任务示例。

## Vue 前端联调

前端当前 `src/api/*.js` 仍使用 mockApi。切换到后端时，把这些文件改为调用 `src/api/request.js` 中的 axios service，例如：

```js
import request from './request'

export const login = (payload) => request.post('/auth/login', payload)
export const getDashboard = () => request.get('/user/dashboard')
```

Vite 代理保持：

```js
server: {
  proxy: {
    '/api': 'http://127.0.0.1:8000',
    '/uploads': 'http://127.0.0.1:8000'
  }
}
```

## 常见问题

- `pymysql.err.OperationalError`：检查 MySQL 是否启动、数据库是否存在、`.env` 中账号密码是否正确。
- `401 Unauthorized`：检查请求头是否带 `Authorization: Bearer <token>`。
- `403 Forbidden`：普通用户不能访问 `/api/admin/*`。
- 图片无法预览：确认后端已启动，并代理或访问 `/uploads/...` 静态路径。
- PaddleOCR 安装失败：可以先不安装，默认 mock OCR 已能支撑演示。
- YOLO 没有检测框：确认 `.env` 中 `YOLO_ENABLED=true`，课程设计阶段可先用 `YOLO_MODE=mock`；真实权重模式下还要确认 `YOLO_MODEL_PATH` 文件存在。

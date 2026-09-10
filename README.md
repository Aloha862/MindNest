# MindNest

MindNest 是一个面向学习场景的智能题目理解与个性化复习平台。用户可以上传试卷、作业、错题和课堂笔记图片，系统通过图像预处理、版面检测、OCR、公式识别和视觉语言模型分析，将非结构化图片转换为可检索、可复习、可统计的题目与学习资料。

项目由 Vue 3 前端和 FastAPI 后端组成，同时提供题库、错题复习、学科管理、学习报告、专注监督和管理员后台。项目中的目录、包名、数据库名、浏览器存储键和导出文件名均以 `MindNest` 为规范。

## 技术路线总览

```text
浏览器端 Vue 3
  ├─ Vue Router：页面路由和登录/角色守卫
  ├─ Pinia：认证、用户、识别任务和管理员状态
  ├─ Axios：统一请求、JWT 注入、响应解包和错误处理
  ├─ MediaPipe Tasks Vision：摄像头姿态/脸部/离席分析
  └─ KaTeX + ECharts：公式渲染和学习数据可视化
           │  HTTP / JSON / multipart
           ▼
FastAPI 应用层
  ├─ Router：认证、文件、识别、题库、错题、资料、专注、报告、管理
  ├─ Service：业务编排、视觉流水线、模型调用、统计和导出
  ├─ Schema：请求校验、响应结构和领域数据转换
  ├─ SQLAlchemy：数据库访问和模型关系
  └─ Static：原图、处理图、裁剪图和导出文件访问
           │
           ├─ MySQL：用户、任务、题目、错题、日志、专注会话和报告
           ├─ OpenCV：图片质量评估、增强、透视矫正和预处理
           ├─ YOLO/YOLOE：题目版面区域与学习场景物体检测
           ├─ OCR / VLM：文字识别、题目理解和结构化输出
           └─ Pix2Text：公式区域识别和 LaTeX 生成
```

## 技术栈

| 层次 | 技术 |
| --- | --- |
| 前端框架 | Vue 3、Vite、Vue Router、Pinia |
| UI 与交互 | Element Plus、Lucide Vue、Sass |
| 可视化与公式 | ECharts、KaTeX |
| 浏览器视觉 | MediaPipe Tasks Vision |
| 后端框架 | FastAPI、Uvicorn、Pydantic v2 |
| 数据访问 | SQLAlchemy 2、PyMySQL、MySQL 8 |
| 安全认证 | JWT、python-jose、passlib/bcrypt |
| 图像处理 | OpenCV、NumPy、Pillow |
| 智能识别 | PaddleOCR、OpenAI-compatible VLM、Ultralytics YOLO/YOLOE、Pix2Text |
| 文档导出 | python-docx、ReportLab |

## 项目结构

```text
MindNest/
├─ MindNest-frontend/              # Vue 3 前端
│  ├─ src/api/                     # API 请求封装
│  ├─ src/components/              # 上传、识别、题目、图表等复用组件
│  ├─ src/layouts/                 # 用户端、管理员端、认证布局
│  ├─ src/router/                  # 路由与权限守卫
│  ├─ src/stores/                  # Pinia 状态
│  ├─ src/utils/                   # 认证、文件、专注视觉等工具
│  └─ src/views/                   # 页面级视图
├─ 后端/MindNest-backend/          # FastAPI 后端
│  ├─ app/routers/                 # REST API 路由
│  ├─ app/schemas/                 # Pydantic 数据结构
│  ├─ app/models/                  # SQLAlchemy 数据模型
│  ├─ app/services/                # 业务服务和视觉识别服务
│  ├─ app/utils/                   # 文件、分页、响应和时间工具
│  ├─ scripts/                     # 初始化、数据准备和检测脚本
│  ├─ .env.example                 # 环境变量模板
│  ├─ requirements.txt              # 后端基础依赖清单
│  └─ run.py                       # Windows 友好的启动入口
├─ requirements.txt                 # 仓库级 Python 依赖清单
└─ .gitignore                       # 运行环境、构建产物和模型文件忽略规则
```

## 核心功能

### 学习端

- 注册、登录、退出、个人资料和密码修改。
- 图片单文件上传与批量上传，支持试卷、作业、错题和笔记类型。
- 识别任务进度、批次结果、OCR 结果、VLM 结果和版面检测结果查看。
- 题库检索、题目详情、学科筛选、知识点统计和题目编辑。
- 错题本、复习尝试、掌握状态和重新打开复习。
- 学习资料管理、题目导出、学习报告和专注学习记录。

### 管理端

- 用户查询、启用/禁用和删除。
- 上传文件、识别任务和题目管理。
- 模型调用日志、识别诊断和失败任务排查。
- 系统配置、上传策略和平台统计。

### 前端主要路由

```text
/login、/register、/change-password
/user/dashboard、/upload、/history
/recognition/:taskId、/recognition/batches/:batchId
/questions、/questions/:id、/subjects、/wrong-questions
/focus、/reports、/export、/profile
/admin/dashboard、/admin/users、/admin/files
/admin/tasks、/admin/questions、/admin/model-logs、/admin/system-config
```

## 题目识别技术路径

识别主流程由 `后端/MindNest-backend/app/services/recognition_service.py` 统一编排。

### 1. 任务与文件登记

上传接口完成文件类型、大小和用户归属校验，然后创建 `upload_files` 与 `recognition_tasks` 记录。任务记录包含批次标识、执行顺序、当前阶段、进度、`trace_id`、失败信息、重试次数和模型原始结果。

### 2. 图像质量评估与预处理

图像服务使用 OpenCV 评估尺寸、清晰度、亮度、对比度和可读性，并按需要执行：

- 文档轮廓检测和透视矫正。
- 灰度化、CLAHE 对比度增强。
- 自适应阈值和形态学去噪。
- 原图与处理图质量对比记录。

### 3. 版面区域检测

YOLO 服务支持真实模型和 OpenCV fallback。真实模型用于检测题目、图表、公式、答案和解析等区域；没有模型权重时，fallback 根据内容带和图像结构生成可展示的区域结果。每个区域包含类别、置信度、边界框、裁剪文件和质量信息。

### 4. OCR 文字识别

OCR 层支持 `mock`、PaddleOCR 和 Qwen/DashScope 视觉模型。输出统一为文本 block，每个 block 包含文本、位置、置信度和来源。服务会对文本进行行排序、空白归一化、低置信度标记和空结果诊断。

### 5. 公式识别与融合

公式服务优先使用版面检测得到的公式区域，安装 Pix2Text 时生成 LaTeX；未安装时使用 OCR 标记和文本特征进行启发式识别。系统通过 IoU 判断公式区域与 OCR block 的重叠关系，去除重复文本，并将公式以内联 LaTeX 形式合并到题目正文中。

### 6. VLM 题目理解

视觉语言模型接收原图、版面区域、OCR 文本和公式上下文，输出题目级结构化 JSON，字段包括：

- 题干、答案、解析和题目类型。
- 学科、知识点和难度。
- 公式、错误类型和复习建议。
- 识别置信度、审核状态和相似练习建议。

客户端使用 OpenAI-compatible SDK，兼容 DashScope 等服务。解析器会处理 Markdown JSON 围栏、宽松 JSON、LaTeX 反斜杠和文本字段 fallback，再由 `vlm_normalizer.py` 完成字段归一化和业务校验。

### 7. 结果持久化

识别完成后，服务层将题目写入 `questions`，非题目内容写入 `learning_materials`，模型调用和阶段耗时写入 `model_logs`，任务状态最终变为 `completed`、`needs_review` 或 `failed`。前端根据进度接口和诊断接口展示流水线过程。

## 专注监督技术路径

专注监督采用前端低延迟分析与后端物体识别结合的方式。

### 浏览器侧

`FocusMonitor.vue` 通过浏览器摄像头获取视频流，使用 MediaPipe FaceLandmarker 和 PoseLandmarker 分析脸部朝向、人体姿态、离席和坐姿连续性。前端使用采样间隔、稳定窗口、状态平滑和过期响应检查，减少单帧结果造成的状态抖动。

### 后端侧

`/api/focus/analyze-frame` 接收压缩图片帧，`focus_yoloe_service.py` 使用 YOLOE 开放词汇检测学习场景物体，例如手机、电脑、键盘、书本和笔。检测结果经过类别别名归一化、置信度过滤、面积/长宽比约束和 IoU 去重，返回对象列表、建议状态、设备信息和可用性信息。

### 状态融合与报告

姿态主导状态如 `away`、`bad_posture` 和 `fatigue` 保留前端连续判断；手机、电脑和学习用品等物体结果用于补充 `distracted_phone`、`computer_learning`、`writing` 等状态。后端将状态变化写入 `study_state_logs`，结束会话后计算专注时长、离席时间、分心时间、手机时间、平均专注分数和坐姿提醒次数，并生成 `study_reports`。

## 后端分层设计

### Router 层

FastAPI 路由按领域拆分：

```text
/api/auth                 认证和用户身份
/api/user                 用户资料和仪表盘
/api/files                文件上传和文件管理
/api/recognition          识别任务、批次、进度和诊断
/api/questions            题库和题目统计
/api/subjects             学科管理
/api/wrong-records        错题和复习记录
/api/materials            学习资料
/api/focus                专注会话和帧分析
/api/report               学习报告
/api/admin                管理员功能
/api/export               题目导出
```

### Service 层

业务逻辑集中在 `app/services`，通过服务组合实现上传、认证、识别、题库、错题、资料、报告、专注和导出。模型服务与业务服务分离，便于在 `mock`、本地模型和远程 VLM 之间切换。

### 数据层

主要表结构如下：

| 表 | 用途 |
| --- | --- |
| `users` | 用户、角色、状态和登录信息 |
| `upload_files` | 文件元数据、类型、批次和存储路径 |
| `recognition_tasks` | 识别任务、进度、模型结果和重试信息 |
| `questions` | 题干、答案、解析、公式、知识点和置信度 |
| `subjects` | 学科配置 |
| `wrong_records` | 错题状态、复习次数和掌握情况 |
| `wrong_review_attempts` | 每次错题复习尝试 |
| `learning_materials` | 笔记和非题目型学习资料 |
| `model_logs` | 模型调用、阶段耗时、状态和错误 |
| `system_configs` | 系统运行参数 |
| `study_sessions` | 专注学习会话 |
| `study_state_logs` | 专注状态采样 |
| `study_reports` | 学习报告和统计结果 |

### 统一响应

API 默认返回统一结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": "2026-09-10 12:00:00"
}
```

前端请求层会自动解包 `data`，并统一处理 401、403、网络错误和后端业务错误。

## 运行环境

- Windows 10/11 或兼容环境。
- Python 3.10–3.12 推荐。
- Node.js 18 或更高版本。
- MySQL 8.x。

## 安装与启动

### 1. 创建数据库

```sql
CREATE DATABASE mindnest DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

也可以执行：

```text
后端/MindNest-backend/scripts/init_mysql.sql
```

### 2. 安装后端

```powershell
cd <repo-root>\后端\MindNest-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r ..\..\requirements.txt
Copy-Item .\.env.example .\.env
```

编辑 `.env`：

```env
APP_NAME=智学空间(MindNest) Backend
APP_ENV=development
DEBUG=false
DATABASE_URL=mysql+pymysql://root:<password>@127.0.0.1:3306/mindnest?charset=utf8mb4
SECRET_KEY=change-this-secret-key-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
UPLOAD_DIR=app/uploads
BACKEND_BASE_URL=http://127.0.0.1:8000
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
OCR_PROVIDER=mock
VLM_PROVIDER=mock
YOLO_ENABLED=true
YOLO_MODE=mock
FOCUS_YOLOE_ENABLED=false
FORMULA_PROVIDER=heuristic
MAX_CONCURRENT_RECOGNITION=2
```

初始化演示数据并启动：

```powershell
python scripts\init_data.py
python run.py
```

后端地址：

- 健康检查：http://127.0.0.1:8000/api/health
- Swagger：http://127.0.0.1:8000/docs
- ReDoc：http://127.0.0.1:8000/redoc

### 3. 安装前端

```powershell
cd <repo-root>\MindNest-frontend
npm install
npm run dev
```

默认访问：<http://127.0.0.1:5173>。

Vite 将 `/api` 和 `/uploads` 代理到 `http://127.0.0.1:8000`，配置位于 `MindNest-frontend/vite.config.js`。

### 4. 构建前端

```powershell
cd <repo-root>\MindNest-frontend
npm run build
npm run preview
```

## 模型配置

默认使用 mock 模式跑通完整业务链路。需要真实模型时，可以按能力逐项启用：

### Qwen / DashScope VLM

```env
OCR_PROVIDER=qwen
VLM_PROVIDER=qwen
DASHSCOPE_API_KEY=<your-api-key>
VLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
VLM_MODEL_NAME=qwen3-vl-plus
```

### PaddleOCR

```powershell
pip install paddleocr paddlepaddle
```

```env
OCR_PROVIDER=paddle
PADDLEOCR_ENABLED=true
```

### YOLO / YOLOE

```powershell
pip install -U ultralytics
pip install "git+https://github.com/ultralytics/CLIP.git"
```

```env
YOLO_ENABLED=true
YOLO_MODE=real
YOLO_MODEL_PATH=weights/best.pt
FOCUS_YOLOE_ENABLED=true
FOCUS_YOLOE_MODEL=yoloe-26m-seg.pt
FOCUS_YOLOE_DEVICE=0
```

### Pix2Text

```powershell
pip install pix2text
```

```env
FORMULA_PROVIDER=pix2text
```

## 关键配置

| 配置 | 作用 |
| --- | --- |
| `DATABASE_URL` | MySQL 连接串，默认数据库名为 `mindnest` |
| `SECRET_KEY` | JWT 签名密钥 |
| `UPLOAD_DIR` | 原图、处理图和裁剪图存储目录 |
| `CORS_ORIGINS` | 前端允许访问的来源 |
| `OCR_PROVIDER` | `mock`、`paddle`、`qwen` 等 OCR 提供方 |
| `VLM_PROVIDER` | `mock` 或 OpenAI-compatible VLM 提供方 |
| `YOLO_MODE` | `mock` 或 `real` |
| `FOCUS_YOLOE_ENABLED` | 是否启用专注监督对象检测 |
| `FOCUS_YOLOE_DEVICE` | YOLOE 推理设备，如 `0` 或 `cpu` |
| `FORMULA_PROVIDER` | `heuristic` 或 `pix2text` |
| `MAX_CONCURRENT_RECOGNITION` | 同时执行的识别任务数量 |

## 项目命名规范

发布分支内统一使用以下命名：

- 前端目录：`MindNest-frontend`
- 后端目录：`后端/MindNest-backend`
- 前端 npm 包名：`mindnest-frontend`
- 浏览器认证键：`mindnest_token`、`mindnest_user`
- 数据库：`mindnest`
- 导出文件：`mindnest-export.*`
- 后端启动环境变量：`MINDNEST_SKIP_VENV_REEXEC`

## 许可证与模型说明

项目源码、第三方依赖、预训练模型和外部数据集应分别遵循各自许可证。真实模型权重、API Key 和本地上传文件不属于源码提交内容。

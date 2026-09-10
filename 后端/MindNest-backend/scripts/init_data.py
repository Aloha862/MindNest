import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal, init_db  # noqa: E402
from app.models.learning_material import LearningMaterial  # noqa: E402
from app.models.model_log import ModelLog  # noqa: E402
from app.models.question import Question  # noqa: E402
from app.models.recognition_task import RecognitionTask  # noqa: E402
from app.models.subject import Subject  # noqa: E402
from app.models.upload_file import UploadFile  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.wrong_record import WrongRecord  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.utils.file_utils import ensure_upload_dirs, path_to_upload_url  # noqa: E402


DEFAULT_SUBJECTS = [
    ("数学", "高等数学、线性代数、概率论等题目"),
    ("英语", "阅读理解、翻译、写作等题目"),
    ("计算机", "程序设计、操作系统、数据库、算法等题目"),
    ("政治", "政治理论与简答题"),
    ("专业课", "专业课程综合题目"),
    ("其他", "无法自动归类的题目"),
]


def ensure_demo_image(name: str) -> Path:
    ensure_upload_dirs()
    image_path = ROOT / "app" / "uploads" / "original" / name
    if not image_path.exists():
        one_pixel_png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        image_path.write_bytes(base64.b64decode(one_pixel_png))
    return image_path


def upsert_user(db, username: str, password: str, nickname: str, role: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user:
        return user
    user = User(username=username, password_hash=hash_password(password), nickname=nickname, role=role, status="active")
    db.add(user)
    db.flush()
    return user


def main() -> None:
    init_db()
    exam_image = ensure_demo_image("demo_exam.png")
    note_image = ensure_demo_image("demo_note.png")
    db = SessionLocal()
    try:
        upsert_user(db, "admin", "123456", "演示管理员", "admin")
        user = upsert_user(db, "user", "123456", "演示用户", "user")

        for name, description in DEFAULT_SUBJECTS:
            if not db.query(Subject).filter(Subject.name == name).first():
                db.add(Subject(name=name, description=description))
        db.flush()

        if not db.query(UploadFile).filter(UploadFile.file_name == "高数月考试卷.png").first():
            uploaded = UploadFile(
                user_id=user.id,
                file_name="高数月考试卷.png",
                file_type="exam",
                file_url=path_to_upload_url(exam_image),
                original_path=str(exam_image),
                size=exam_image.stat().st_size,
                status="recognized",
                remark="初始化演示试卷",
            )
            db.add(uploaded)
            db.flush()
            task = RecognitionTask(
                file_id=uploaded.id,
                user_id=user.id,
                status="completed",
                current_step="识别完成",
                progress=100,
                ocr_text="1. 已知函数 f(x)=x²+2x，求 f'(x)。\nA. 2x\nB. 2x+2\nC. x+2\nD. 2",
                ocr_blocks=json.dumps([{"text": "1. 已知函数 f(x)=x²+2x，求 f'(x)。", "confidence": 0.96, "box": {"x": 10, "y": 20, "width": 420, "height": 40}}], ensure_ascii=False),
                ocr_formula_blocks=json.dumps([{"latex": "f'(x)=2x+2", "confidence": 0.9}], ensure_ascii=False),
                yolo_result=json.dumps(
                    {
                        "mode": "mock",
                        "layoutType": "single_question",
                        "imageWidth": 1200,
                        "imageHeight": 800,
                        "detections": [
                            {"label": "question", "labelName": "题目区域", "confidence": 0.92, "box": {"x": 72, "y": 64, "width": 1056, "height": 600}},
                            {"label": "formula", "labelName": "公式区域", "confidence": 0.84, "box": {"x": 120, "y": 220, "width": 720, "height": 120}},
                            {"label": "analysis", "labelName": "解析区域", "confidence": 0.82, "box": {"x": 120, "y": 520, "width": 780, "height": 160}},
                        ],
                    },
                    ensure_ascii=False,
                ),
                vlm_summary="本图片包含1道数学选择题，主要考查导数基本公式。",
                vlm_result=json.dumps({"summary": "本图片包含1道数学选择题，主要考查导数基本公式。", "layoutType": "single_question", "materialType": "exam_question"}, ensure_ascii=False),
            )
            db.add(task)
            db.flush()
            question = Question(
                task_id=task.id,
                file_id=uploaded.id,
                user_id=user.id,
                title="函数求导基础题",
                content="已知函数 f(x)=x²+2x，求 f'(x)。",
                subject="数学",
                question_type="选择题",
                knowledge_points=json.dumps(["导数", "函数求导"], ensure_ascii=False),
                difficulty="基础",
                answer="B. 2x+2",
                analysis_summary="x² 的导数为 2x，2x 的导数为 2，因此结果为 2x+2。",
                source_image_url=uploaded.file_url,
            )
            db.add(question)
            db.flush()
            db.add(WrongRecord(question_id=question.id, user_id=user.id, file_id=uploaded.id, task_id=task.id, note="导数公式需要复习", mastery_status="reviewing", review_count=1, source="demo"))
            db.add_all(
                [
                    ModelLog(task_id=task.id, model_type="opencv", model_name="opencv-preprocess-v1", input_summary="高数月考试卷.png", output_summary="灰度化、去噪、二值化", status="success", cost_time=120),
                    ModelLog(task_id=task.id, model_type="yolo", model_name="yolo-layout-mock", input_summary="预处理图片", output_summary="检测题目、公式、解析区域 3 个", status="success", cost_time=35),
                    ModelLog(task_id=task.id, model_type="ocr", model_name="mock-ocr", input_summary="预处理图片", output_summary="识别 1 道数学题，公式块 1 个", status="success", cost_time=80),
                    ModelLog(task_id=task.id, model_type="vlm", model_name="mock-vlm-v1", input_summary="图片 + OCR 文本", output_summary="生成 1 张题目卡片", status="success", cost_time=60),
                ]
            )

        if not db.query(UploadFile).filter(UploadFile.file_name == "课堂笔记截图.png").first():
            note_file = UploadFile(
                user_id=user.id,
                file_name="课堂笔记截图.png",
                file_type="note",
                file_url=path_to_upload_url(note_image),
                original_path=str(note_image),
                size=note_image.stat().st_size,
                status="recognized",
                remark="初始化演示学习资料",
            )
            db.add(note_file)
            db.flush()
            note_task = RecognitionTask(file_id=note_file.id, user_id=user.id, status="completed", current_step="识别完成", progress=100, ocr_text="操作系统课堂笔记：进程调度、时间片轮转、优先级调度。", vlm_summary="本图片是一份计算机课程笔记，主题为操作系统进程调度。")
            db.add(note_task)
            db.flush()
            db.add(
                LearningMaterial(
                    file_id=note_file.id,
                    task_id=note_task.id,
                    user_id=user.id,
                    title="操作系统进程调度笔记",
                    category="note",
                    summary="整理了 FCFS、RR、优先级调度等基础概念。",
                    tags=json.dumps(["操作系统", "进程调度"], ensure_ascii=False),
                    remark="课堂资料",
                    source_image_url=note_file.file_url,
                    ocr_summary=note_task.ocr_text,
                )
            )

        if not db.query(RecognitionTask).filter(RecognitionTask.status == "failed").first():
            failed_file = UploadFile(user_id=user.id, file_name="线代错题失败样例.png", file_type="mistake", file_url=path_to_upload_url(exam_image), original_path=str(exam_image), size=exam_image.stat().st_size, status="failed", remark="失败任务演示")
            db.add(failed_file)
            db.flush()
            failed_task = RecognitionTask(file_id=failed_file.id, user_id=user.id, status="failed", current_step="OCR识别失败", progress=40, error_message="演示失败任务")
            db.add(failed_task)
            db.flush()
            db.add(ModelLog(task_id=failed_task.id, model_type="ocr", model_name="mock-ocr", input_summary="线代错题失败样例.png", output_summary="识别失败", status="failed", cost_time=50, error_message="演示失败日志"))

        db.commit()
        print("初始化完成：admin/123456，user/123456")
    finally:
        db.close()


if __name__ == "__main__":
    main()

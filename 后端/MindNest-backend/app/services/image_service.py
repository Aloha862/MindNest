from __future__ import annotations

from pathlib import Path
from time import perf_counter

from sqlalchemy.orm import Session

from app.services.model_log_service import create_model_log


def _read_image(input_path: str):
    import cv2
    import numpy as np

    source = Path(input_path)
    image_data = np.fromfile(str(source), dtype=np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("图片读取失败")
    return cv2, image


def _find_document_contour(cv2, image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    image_area = image.shape[0] * image.shape[1]
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:8]:
        area = cv2.contourArea(contour)
        if area < image_area * 0.2:
            continue
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        if len(approx) == 4:
            return approx.reshape(4, 2)
    return None


def _order_points(points):
    import numpy as np

    rect = np.zeros((4, 2), dtype="float32")
    s = points.sum(axis=1)
    rect[0] = points[s.argmin()]
    rect[2] = points[s.argmax()]
    diff = np.diff(points, axis=1)
    rect[1] = points[diff.argmin()]
    rect[3] = points[diff.argmax()]
    return rect


def _warp_document(cv2, image, points):
    import numpy as np

    rect = _order_points(points)
    top_left, top_right, bottom_right, bottom_left = rect
    width_a = np.linalg.norm(bottom_right - bottom_left)
    width_b = np.linalg.norm(top_right - top_left)
    height_a = np.linalg.norm(top_right - bottom_right)
    height_b = np.linalg.norm(top_left - bottom_left)
    max_width = int(max(width_a, width_b))
    max_height = int(max(height_a, height_b))
    if max_width < 200 or max_height < 200:
        return image, False
    dst = np.array(
        [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]],
        dtype="float32",
    )
    matrix = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, matrix, (max_width, max_height)), True


def _skew_angle(cv2, gray) -> float:
    import numpy as np

    binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(binary > 0))
    if len(coords) < 50:
        return 0.0
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    return round(float(angle), 2)


def assess_image_quality(input_path: str) -> dict:
    """Return objective quality signals used by both the pipeline and UI."""
    cv2, image = _read_image(input_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    brightness = float(gray.mean())
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    contrast = float(gray.std())
    shadow_score = float(abs(gray.mean() - cv2.medianBlur(gray, 51).mean()))
    skew_angle = _skew_angle(cv2, gray)
    contour = _find_document_contour(cv2, image)
    perspective_score = 0.0 if contour is None else round(float(cv2.contourArea(contour) / (image.shape[0] * image.shape[1])), 4)
    warnings = []
    if blur_score < 80:
        warnings.append("图片可能模糊")
    if brightness < 80:
        warnings.append("图片偏暗")
    if brightness > 220:
        warnings.append("图片过曝")
    if contrast < 35:
        warnings.append("文字对比度偏低")
    if shadow_score > 18:
        warnings.append("可能存在明显阴影或光照不均")
    if abs(skew_angle) > 8:
        warnings.append("图片倾斜较明显")
    if contour is None:
        warnings.append("未检测到稳定纸张边界，跳过强透视裁切")
    return {
        "brightness": round(brightness, 2),
        "blurScore": round(blur_score, 2),
        "contrast": round(contrast, 2),
        "shadowScore": round(shadow_score, 2),
        "skewAngle": skew_angle,
        "perspectiveScore": perspective_score,
        "warnings": warnings,
    }


def preprocess_image(input_path: str, db: Session | None = None, task_id: int | None = None) -> str:
    start = perf_counter()
    try:
        import cv2

        source = Path(input_path)
        output_dir = source.parents[1] / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{source.stem}_processed{source.suffix}"
        cv2, image = _read_image(input_path)

        height, width = image.shape[:2]
        max_side = 2200
        if max(height, width) > max_side:
            scale = max_side / max(height, width)
            image = cv2.resize(image, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)

        contour = _find_document_contour(cv2, image)
        warped, warped_ok = _warp_document(cv2, image, contour) if contour is not None else (image, False)

        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        denoised = cv2.GaussianBlur(gray, (3, 3), 0)
        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(denoised)
        binary = cv2.adaptiveThreshold(
            enhanced,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            10,
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        output = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        success, encoded = cv2.imencode(source.suffix, output)
        if not success:
            raise ValueError("预处理图片编码失败")
        encoded.tofile(str(output_path))
        cost = int((perf_counter() - start) * 1000)
        if db:
            create_model_log(
                db,
                task_id=task_id,
                model_type="opencv",
                model_name="opencv-preprocess-v2",
                stage="preprocessing",
                input_summary=str(source.name),
                output_summary=f"增强图生成完成：{output_path.name}",
                metadata={"warped": warped_ok},
                status="success",
                cost_time=cost,
            )
        return str(output_path)
    except Exception as exc:
        cost = int((perf_counter() - start) * 1000)
        if db:
            create_model_log(
                db,
                task_id=task_id,
                model_type="opencv",
                model_name="opencv-preprocess-v2",
                stage="preprocessing",
                error_code="PREPROCESS_FAILED",
                input_summary=input_path,
                output_summary="预处理失败，回退原图",
                status="failed",
                cost_time=cost,
                error_message=str(exc),
            )
        return input_path

CREATE DATABASE IF NOT EXISTS mindnest DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mindnest;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS model_logs;
DROP TABLE IF EXISTS wrong_review_attempts;
DROP TABLE IF EXISTS wrong_records;
DROP TABLE IF EXISTS learning_materials;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS recognition_tasks;
DROP TABLE IF EXISTS upload_files;
DROP TABLE IF EXISTS system_configs;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS users;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  nickname VARCHAR(64) NOT NULL DEFAULT '',
  phone VARCHAR(32) NOT NULL DEFAULT '',
  avatar VARCHAR(255) NOT NULL DEFAULT '',
  role VARCHAR(16) NOT NULL DEFAULT 'user',
  status VARCHAR(16) NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  last_login_time DATETIME NULL,
  INDEX idx_users_username (username),
  INDEX idx_users_role (role),
  INDEX idx_users_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE subjects (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL UNIQUE,
  description TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE system_configs (
  `key` VARCHAR(64) PRIMARY KEY,
  `value` TEXT NULL,
  description VARCHAR(255) NOT NULL DEFAULT '',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE upload_files (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  file_type VARCHAR(32) NOT NULL,
  batch_id VARCHAR(64) NOT NULL DEFAULT '',
  batch_order INT NOT NULL DEFAULT 0,
  file_url VARCHAR(500) NOT NULL,
  original_path VARCHAR(500) NOT NULL,
  processed_path VARCHAR(500) NOT NULL DEFAULT '',
  size BIGINT NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL DEFAULT 'uploaded',
  remark TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_upload_files_user_id (user_id),
  INDEX idx_upload_files_file_type (file_type),
  INDEX idx_upload_files_batch_id (batch_id),
  INDEX idx_upload_files_status (status),
  CONSTRAINT fk_upload_files_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE recognition_tasks (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  file_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  batch_id VARCHAR(64) NOT NULL DEFAULT '',
  batch_order INT NOT NULL DEFAULT 0,
  trace_id VARCHAR(64) NOT NULL DEFAULT '',
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  current_step VARCHAR(255) NOT NULL DEFAULT '等待识别',
  progress INT NOT NULL DEFAULT 0,
  error_code VARCHAR(64) NOT NULL DEFAULT '',
  error_stage VARCHAR(32) NOT NULL DEFAULT '',
  retry_count INT NOT NULL DEFAULT 0,
  ocr_text TEXT NULL,
  ocr_blocks LONGTEXT NULL,
  ocr_formula_blocks LONGTEXT NULL,
  yolo_result LONGTEXT NULL,
  vlm_summary TEXT NULL,
  vlm_result LONGTEXT NULL,
  pipeline_options_json JSON NULL,
  quality_json JSON NULL,
  normalized_result_json JSON NULL,
  error_message TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  started_at DATETIME NULL,
  heartbeat_at DATETIME NULL,
  finished_at DATETIME NULL,
  INDEX idx_recognition_tasks_file_id (file_id),
  INDEX idx_recognition_tasks_user_id (user_id),
  INDEX idx_recognition_tasks_batch_id (batch_id),
  INDEX idx_recognition_tasks_status (status),
  CONSTRAINT fk_recognition_tasks_file FOREIGN KEY (file_id) REFERENCES upload_files(id) ON DELETE CASCADE,
  CONSTRAINT fk_recognition_tasks_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE questions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_id BIGINT NULL,
  file_id BIGINT NULL,
  user_id BIGINT NOT NULL,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  subject VARCHAR(64) NOT NULL DEFAULT '其他',
  question_type VARCHAR(64) NOT NULL DEFAULT '未知',
  knowledge_points TEXT NULL,
  options_json JSON NULL,
  knowledge_points_json JSON NULL,
  formulas_json JSON NULL,
  raw_vlm_json JSON NULL,
  source_bbox_json JSON NULL,
  confidence DOUBLE NOT NULL DEFAULT 0,
  review_status VARCHAR(32) NOT NULL DEFAULT 'approved',
  difficulty VARCHAR(32) NOT NULL DEFAULT '基础',
  answer TEXT NULL,
  analysis_summary TEXT NULL,
  source_image_url VARCHAR(500) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_questions_task_id (task_id),
  INDEX idx_questions_file_id (file_id),
  INDEX idx_questions_user_id (user_id),
  INDEX idx_questions_subject (subject),
  INDEX idx_questions_question_type (question_type),
  INDEX idx_questions_review_status (review_status),
  INDEX idx_questions_difficulty (difficulty),
  CONSTRAINT fk_questions_task FOREIGN KEY (task_id) REFERENCES recognition_tasks(id) ON DELETE SET NULL,
  CONSTRAINT fk_questions_file FOREIGN KEY (file_id) REFERENCES upload_files(id) ON DELETE SET NULL,
  CONSTRAINT fk_questions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE wrong_records (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  question_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  file_id BIGINT NULL,
  task_id BIGINT NULL,
  note TEXT NULL,
  mastery_status VARCHAR(32) NOT NULL DEFAULT 'unreviewed',
  review_count INT NOT NULL DEFAULT 0,
  last_review_time DATETIME NULL,
  source VARCHAR(32) NOT NULL DEFAULT 'manual',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_wrong_records_question_id (question_id),
  INDEX idx_wrong_records_user_id (user_id),
  INDEX idx_wrong_records_mastery_status (mastery_status),
  CONSTRAINT fk_wrong_records_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
  CONSTRAINT fk_wrong_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE wrong_review_attempts (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  wrong_record_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  question_id BIGINT NOT NULL,
  result VARCHAR(32) NOT NULL,
  self_rating VARCHAR(32) NOT NULL DEFAULT 'normal',
  note TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_wrong_review_attempts_record_id (wrong_record_id),
  INDEX idx_wrong_review_attempts_user_id (user_id),
  INDEX idx_wrong_review_attempts_question_id (question_id),
  INDEX idx_wrong_review_attempts_result (result),
  CONSTRAINT fk_wrong_review_attempts_record FOREIGN KEY (wrong_record_id) REFERENCES wrong_records(id) ON DELETE CASCADE,
  CONSTRAINT fk_wrong_review_attempts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_wrong_review_attempts_question FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE learning_materials (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  file_id BIGINT NULL,
  task_id BIGINT NULL,
  user_id BIGINT NOT NULL,
  title VARCHAR(255) NOT NULL,
  category VARCHAR(64) NOT NULL DEFAULT 'note',
  summary TEXT NULL,
  tags TEXT NULL,
  remark TEXT NULL,
  source_image_url VARCHAR(500) NOT NULL DEFAULT '',
  ocr_summary TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_learning_materials_file_id (file_id),
  INDEX idx_learning_materials_task_id (task_id),
  INDEX idx_learning_materials_user_id (user_id),
  INDEX idx_learning_materials_category (category),
  CONSTRAINT fk_learning_materials_file FOREIGN KEY (file_id) REFERENCES upload_files(id) ON DELETE SET NULL,
  CONSTRAINT fk_learning_materials_task FOREIGN KEY (task_id) REFERENCES recognition_tasks(id) ON DELETE SET NULL,
  CONSTRAINT fk_learning_materials_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE model_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_id BIGINT NULL,
  model_type VARCHAR(32) NOT NULL,
  model_name VARCHAR(128) NOT NULL,
  stage VARCHAR(32) NOT NULL DEFAULT '',
  error_code VARCHAR(64) NOT NULL DEFAULT '',
  input_summary TEXT NULL,
  output_summary TEXT NULL,
  metadata_json JSON NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'success',
  cost_time INT NOT NULL DEFAULT 0,
  error_message TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_model_logs_task_id (task_id),
  INDEX idx_model_logs_model_type (model_type),
  INDEX idx_model_logs_status (status),
  CONSTRAINT fk_model_logs_task FOREIGN KEY (task_id) REFERENCES recognition_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO users (id, username, password_hash, nickname, phone, avatar, role, status)
VALUES
  (1, 'admin', '$2b$12$vtuZ00vvg4f.cedv/oReBuCI3pEaMvrSdtTc8tAxIInlrDZKVl9uG', '演示管理员', '', '', 'admin', 'active'),
  (2, 'user', '$2b$12$VCmXBO/wd1M0BqfhWvBvHeAYi5vMtYbdhPc1k/3f0uB.rhnoUyJdW', '演示用户', '13800000000', '', 'user', 'active');

INSERT INTO subjects (id, name, description)
VALUES
  (1, '数学', '高等数学、线性代数、概率论等题目'),
  (2, '英语', '阅读理解、翻译、写作等题目'),
  (3, '计算机', '程序设计、操作系统、数据库、算法等题目'),
  (4, '政治', '政治理论与简答题'),
  (5, '专业课', '专业课程综合题目'),
  (6, '其他', '无法自动归类的题目');

INSERT INTO upload_files (id, user_id, file_name, file_type, file_url, original_path, size, status, remark)
VALUES
  (1, 2, '高数月考试卷.png', 'exam', '/uploads/original/demo_exam.png', 'app/uploads/original/demo_exam.png', 1024, 'recognized', '初始化演示试卷'),
  (2, 2, '课堂笔记截图.png', 'note', '/uploads/original/demo_note.png', 'app/uploads/original/demo_note.png', 1024, 'recognized', '初始化演示学习资料'),
  (3, 2, '线代错题失败样例.png', 'mistake', '/uploads/original/demo_exam.png', 'app/uploads/original/demo_exam.png', 1024, 'failed', '失败任务演示');

INSERT INTO recognition_tasks (id, file_id, user_id, status, current_step, progress, ocr_text, ocr_blocks, ocr_formula_blocks, yolo_result, vlm_summary, vlm_result, error_message, finished_at)
VALUES
  (1, 1, 2, 'completed', '识别完成', 100, '1. 已知函数 f(x)=x²+2x，求 f''(x)。\nA. 2x\nB. 2x+2\nC. x+2\nD. 2', '[{"text":"1. 已知函数 f(x)=x²+2x，求 f''(x)。","confidence":0.96}]', '[{"latex":"f''(x)=2x+2","confidence":0.9}]', '{"mode":"mock","layoutType":"single_question","imageWidth":1200,"imageHeight":800,"detections":[{"label":"question","labelName":"题目区域","confidence":0.92,"box":{"x":72,"y":64,"width":1056,"height":600}},{"label":"formula","labelName":"公式区域","confidence":0.84,"box":{"x":120,"y":220,"width":720,"height":120}},{"label":"analysis","labelName":"解析区域","confidence":0.82,"box":{"x":120,"y":520,"width":780,"height":160}}]}', '本图片包含1道数学选择题，主要考查导数基本公式。', '{"summary":"本图片包含1道数学选择题，主要考查导数基本公式。","layoutType":"single_question","materialType":"exam_question"}', '', NOW()),
  (2, 2, 2, 'completed', '识别完成', 100, '操作系统课堂笔记：进程调度、时间片轮转、优先级调度。', '[]', '[]', '{"mode":"mock","layoutType":"note","detections":[]}', '本图片是一份计算机课程笔记，主题为操作系统进程调度。', '{"summary":"本图片是一份计算机课程笔记。","materialType":"note"}', '', NOW()),
  (3, 3, 2, 'failed', 'OCR识别失败', 40, '', '[]', '[]', '{}', '', '{}', '演示失败任务', NULL);

INSERT INTO questions (id, task_id, file_id, user_id, title, content, subject, question_type, knowledge_points, difficulty, answer, analysis_summary, source_image_url)
VALUES
  (1, 1, 1, 2, '函数求导基础题', '已知函数 f(x)=x²+2x，求 f''(x)。', '数学', '选择题', '["导数","函数求导"]', '基础', 'B. 2x+2', 'x² 的导数为 2x，2x 的导数为 2，因此结果为 2x+2。', '/uploads/original/demo_exam.png');

INSERT INTO wrong_records (id, question_id, user_id, file_id, task_id, note, mastery_status, review_count, source)
VALUES (1, 1, 2, 1, 1, '导数公式需要复习', 'reviewing', 1, 'demo');

INSERT INTO learning_materials (id, file_id, task_id, user_id, title, category, summary, tags, remark, source_image_url, ocr_summary)
VALUES (1, 2, 2, 2, '操作系统进程调度笔记', 'note', '整理了 FCFS、RR、优先级调度等基础概念。', '["操作系统","进程调度"]', '课堂资料', '/uploads/original/demo_note.png', '操作系统课堂笔记：进程调度、时间片轮转、优先级调度。');

INSERT INTO model_logs (task_id, model_type, model_name, input_summary, output_summary, status, cost_time, error_message)
VALUES
  (1, 'opencv', 'opencv-preprocess-v1', '高数月考试卷.png', '灰度化、去噪、二值化', 'success', 120, ''),
  (1, 'yolo', 'yolo-layout-mock', '预处理图片', '检测题目、公式、解析区域 3 个', 'success', 35, ''),
  (1, 'ocr', 'mock-ocr', '预处理图片', '识别 1 道数学题，公式块 1 个', 'success', 80, ''),
  (1, 'vlm', 'mock-vlm-v1', '图片 + OCR 文本', '生成 1 张题目卡片', 'success', 60, ''),
  (3, 'ocr', 'mock-ocr', '线代错题失败样例.png', '识别失败', 'failed', 50, '演示失败日志');

SELECT 'MindNest database initialized successfully.' AS message;
SELECT username, role, status FROM users ORDER BY id;

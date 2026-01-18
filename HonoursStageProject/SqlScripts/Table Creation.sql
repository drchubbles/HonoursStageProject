Use honoursstageproject;

CREATE TABLE roles (
  role_id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,
  role_name VARCHAR(32) NOT NULL,
  PRIMARY KEY (role_id),
  UNIQUE KEY uq_roles_role_name (role_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE users (
  user_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role_id TINYINT UNSIGNED NOT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_users_username (username),
  KEY idx_users_role_id (role_id),
  CONSTRAINT fk_users_role
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE forms (
  form_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  form_key VARCHAR(64) NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_by BIGINT UNSIGNED NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (form_id),
  UNIQUE KEY uq_forms_form_key (form_key),
  KEY idx_forms_created_by (created_by),
  CONSTRAINT fk_forms_created_by
    FOREIGN KEY (created_by) REFERENCES users(user_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE form_versions (
  form_version_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  form_id BIGINT UNSIGNED NOT NULL,
  version_number INT UNSIGNED NOT NULL,
  created_by BIGINT UNSIGNED NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  notes VARCHAR(255) NULL,
  PRIMARY KEY (form_version_id),
  UNIQUE KEY uq_form_versions (form_id, version_number),
  KEY idx_form_versions_form_id (form_id),
  KEY idx_form_versions_created_by (created_by),
  CONSTRAINT fk_form_versions_form
    FOREIGN KEY (form_id) REFERENCES forms(form_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_form_versions_created_by
    FOREIGN KEY (created_by) REFERENCES users(user_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE questions (
  question_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  question_key VARCHAR(64) NOT NULL,
  created_by BIGINT UNSIGNED NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (question_id),
  UNIQUE KEY uq_questions_question_key (question_key),
  KEY idx_questions_created_by (created_by),
  CONSTRAINT fk_questions_created_by
    FOREIGN KEY (created_by) REFERENCES users(user_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE question_versions (
  question_version_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  question_id BIGINT UNSIGNED NOT NULL,
  version_number INT UNSIGNED NOT NULL,
  prompt_text TEXT NOT NULL,
  response_type VARCHAR(32) NOT NULL,
  is_required TINYINT(1) NOT NULL DEFAULT 0,
  help_text TEXT NULL,
  is_active TINYINT(1) NOT NULL DEFAULT 1,
  created_by BIGINT UNSIGNED NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (question_version_id),
  UNIQUE KEY uq_question_versions (question_id, version_number),
  KEY idx_qv_question_id (question_id),
  KEY idx_qv_active (question_id, is_active),
  CONSTRAINT fk_qv_question
    FOREIGN KEY (question_id) REFERENCES questions(question_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_qv_created_by
    FOREIGN KEY (created_by) REFERENCES users(user_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE question_version_options (
  option_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  question_version_id BIGINT UNSIGNED NOT NULL,
  option_value VARCHAR(128) NOT NULL,
  option_label VARCHAR(255) NOT NULL,
  sort_order INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (option_id),
  UNIQUE KEY uq_qvo (question_version_id, option_value),
  KEY idx_qvo_qv (question_version_id, sort_order),
  CONSTRAINT fk_qvo_qv
    FOREIGN KEY (question_version_id) REFERENCES question_versions(question_version_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE form_version_questions (
  form_version_question_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  form_version_id BIGINT UNSIGNED NOT NULL,
  question_version_id BIGINT UNSIGNED NOT NULL,
  sort_order INT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (form_version_question_id),
  UNIQUE KEY uq_fvq (form_version_id, question_version_id),
  KEY idx_fvq_form_version (form_version_id, sort_order),
  KEY idx_fvq_question_version (question_version_id),
  CONSTRAINT fk_fvq_form_version
    FOREIGN KEY (form_version_id) REFERENCES form_versions(form_version_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_fvq_question_version
    FOREIGN KEY (question_version_id) REFERENCES question_versions(question_version_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE form_question_branching (
  branching_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  form_version_id BIGINT UNSIGNED NOT NULL,
  source_question_version_id BIGINT UNSIGNED NOT NULL,
  target_question_version_id BIGINT UNSIGNED NOT NULL,
  operator ENUM('equals','not_equals','in','not_in','gt','gte','lt','lte','contains','is_empty','is_not_empty')
    NOT NULL DEFAULT 'equals',
  compare_option_value VARCHAR(128) NULL,
  compare_number DECIMAL(18,6) NULL,
  compare_text VARCHAR(255) NULL,
  action ENUM('show','hide','goto') NOT NULL DEFAULT 'show',
  priority INT UNSIGNED NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (branching_id),
  KEY idx_b_form_version (form_version_id),
  KEY idx_b_source (source_question_version_id),
  KEY idx_b_target (target_question_version_id),
  CONSTRAINT fk_b_form_version
    FOREIGN KEY (form_version_id) REFERENCES form_versions(form_version_id)
    ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT fk_b_source_qv
    FOREIGN KEY (source_question_version_id) REFERENCES question_versions(question_version_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_b_target_qv
    FOREIGN KEY (target_question_version_id) REFERENCES question_versions(question_version_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE form_submissions (
  submission_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  form_id BIGINT UNSIGNED NOT NULL,
  form_version_id BIGINT UNSIGNED NOT NULL,
  submitted_by BIGINT UNSIGNED NOT NULL,
  submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (submission_id),
  KEY idx_submissions_form (form_id, submitted_at),
  KEY idx_submissions_user (submitted_by, submitted_at),
  KEY idx_submissions_form_version (form_version_id),
  CONSTRAINT fk_submissions_form
    FOREIGN KEY (form_id) REFERENCES forms(form_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_submissions_form_version
    FOREIGN KEY (form_version_id) REFERENCES form_versions(form_version_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_submissions_user
    FOREIGN KEY (submitted_by) REFERENCES users(user_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE submission_answers (
  submission_answer_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  submission_id BIGINT UNSIGNED NOT NULL,
  question_version_id BIGINT UNSIGNED NOT NULL,
  answer_text TEXT NULL,
  answer_number DECIMAL(18,6) NULL,
  answer_option_value VARCHAR(128) NULL,
  answered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (submission_answer_id),
  UNIQUE KEY uq_submission_question (submission_id, question_version_id),
  KEY idx_answers_submission (submission_id),
  KEY idx_answers_question_version (question_version_id),
  CONSTRAINT fk_answers_submission
    FOREIGN KEY (submission_id) REFERENCES form_submissions(submission_id)
    ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT fk_answers_question_version
    FOREIGN KEY (question_version_id) REFERENCES question_versions(question_version_id)
    ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

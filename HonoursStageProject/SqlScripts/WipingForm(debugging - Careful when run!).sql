USE honoursstageproject;

START TRANSACTION;

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE form_question_branching;
TRUNCATE TABLE form_version_questions;
TRUNCATE TABLE question_version_options;
TRUNCATE TABLE question_versions;
TRUNCATE TABLE questions;
TRUNCATE TABLE form_versions;
TRUNCATE TABLE forms;

SET FOREIGN_KEY_CHECKS = 1;

COMMIT;

USE honoursstageproject;

START TRANSACTION;

SET @created_by :=
  (SELECT u.user_id
   FROM users u
   JOIN roles r ON r.role_id = u.role_id
   WHERE LOWER(r.role_name) = 'admin' AND u.is_active = 1
   ORDER BY u.user_id
   LIMIT 1);

SET @created_by := COALESCE(
  @created_by,
  (SELECT user_id FROM users WHERE is_active = 1 ORDER BY user_id LIMIT 1)
);

INSERT INTO forms (form_key, title, description, created_by)
VALUES (
  'incident_report_v1',
  'Incident / Error Report',
  'Initial form for capturing where an error occurred and how to prevent it.',
  @created_by
);

SET @form_id := LAST_INSERT_ID();

INSERT INTO form_versions (form_id, version_number, created_by, notes)
VALUES (@form_id, 1, @created_by, 'Initial version');

SET @form_version_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by) VALUES ('email', @created_by);
SET @q1_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q1_id, 1, 'Email', 'text', 1, NULL, 1, @created_by);
SET @q1_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by) VALUES ('name', @created_by);
SET @q2_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q2_id, 1, 'Name', 'text', 1, NULL, 1, @created_by);
SET @q2_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by) VALUES ('log_number', @created_by);
SET @q3_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q3_id, 1, 'Log Number', 'text', 1, NULL, 1, @created_by);
SET @q3_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by) VALUES ('opening_code_correct', @created_by);
SET @q4_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q4_id, 1, 'Opening Code Correct?', 'select', 1, NULL, 1, @created_by);
SET @q4_v1_id := LAST_INSERT_ID();
INSERT INTO question_version_options (question_version_id, option_value, option_label, sort_order) VALUES
(@q4_v1_id, 'yes', 'Yes', 1),
(@q4_v1_id, 'no',  'No',  2);

INSERT INTO questions (question_key, created_by) VALUES ('correct_opening_code', @created_by);
SET @q5_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q5_id, 1, 'What was the correct opening code?', 'text', 1, NULL, 1, @created_by);
SET @q5_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by) VALUES ('crimes_missed_or_not_negated', @created_by);
SET @q6_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q6_id, 1, 'Were any crime/s missed or not negated?', 'select', 1, NULL, 1, @created_by);
SET @q6_v1_id := LAST_INSERT_ID();
INSERT INTO question_version_options (question_version_id, option_value, option_label, sort_order) VALUES
(@q6_v1_id, 'yes', 'Yes', 1),
(@q6_v1_id, 'no',  'No',  2);

INSERT INTO questions (question_key, created_by) VALUES ('crime_type_missed_not_negated', @created_by);
SET @q7_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q7_id, 1, 'Crime Type Missed / Not Negated', 'text', 0, NULL, 1, @created_by);
SET @q7_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by) VALUES ('staff_member_requiring_feedback', @created_by);
SET @q8_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q8_id, 1, 'Name of staff member requiring feedback (FIN/Surname)', 'text', 1, NULL, 1, @created_by);
SET @q8_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by) VALUES ('team_selection', @created_by);
SET @q9_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q9_id, 1, 'If the member of staff was CRT/DRT/Dispatch – please select which team (multiple answers can be selected)', 'multi_select', 0, NULL, 1, @created_by);
SET @q9_v1_id := LAST_INSERT_ID();
INSERT INTO question_version_options (question_version_id, option_value, option_label, sort_order) VALUES
(@q9_v1_id, 'example_1', 'example 1', 1),
(@q9_v1_id, 'example_2', 'example 2', 2),
(@q9_v1_id, 'example_3', 'example 3', 3);

INSERT INTO questions (question_key, created_by) VALUES ('supervisor_name', @created_by);
SET @q10_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q10_id, 1, 'Who is their supervisor? (FIN/Surname)', 'text', 1, NULL, 1, @created_by);
SET @q10_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by) VALUES ('ddm_comments', @created_by);
SET @q11_id := LAST_INSERT_ID();
INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q11_id, 1, 'DDM Comments for feedback to be given (please ensure feedback is precise)', 'text', 1, NULL, 1, @created_by);
SET @q11_v1_id := LAST_INSERT_ID();

INSERT INTO form_version_questions (form_version_id, question_version_id, sort_order) VALUES
(@form_version_id, @q1_v1_id,  1),
(@form_version_id, @q2_v1_id,  2),
(@form_version_id, @q3_v1_id,  3),
(@form_version_id, @q4_v1_id,  4),
(@form_version_id, @q5_v1_id,  5),
(@form_version_id, @q6_v1_id,  6),
(@form_version_id, @q7_v1_id,  7),
(@form_version_id, @q8_v1_id,  8),
(@form_version_id, @q9_v1_id,  9),
(@form_version_id, @q10_v1_id, 10),
(@form_version_id, @q11_v1_id, 11);

INSERT INTO form_question_branching
  (form_version_id, source_question_version_id, target_question_version_id, operator, compare_option_value, action, priority)
VALUES
  (@form_version_id, @q6_v1_id, @q7_v1_id, 'equals', 'yes', 'show', 1),
  (@form_version_id, @q6_v1_id, @q7_v1_id, 'not_equals', 'yes', 'hide', 2);

COMMIT;

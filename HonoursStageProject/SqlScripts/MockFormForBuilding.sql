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

INSERT INTO questions (question_key, created_by)
VALUES ('where_was_error', @created_by);
SET @q1_id := LAST_INSERT_ID();

INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q1_id, 1,
   'Where was the error in the system?',
   'select',
   1,
   'Select the area where the error occurred.',
   1,
   @created_by
  );
SET @q1_v1_id := LAST_INSERT_ID();


INSERT INTO question_version_options (question_version_id, option_value, option_label, sort_order) VALUES
(@q1_v1_id, 'frontend',       'Frontend / UI',          1),
(@q1_v1_id, 'backend',        'Backend / API',          2),
(@q1_v1_id, 'database',       'Database',              3),
(@q1_v1_id, 'infrastructure', 'Infrastructure / Host',  4),
(@q1_v1_id, 'network',        'Network',               5),
(@q1_v1_id, 'other',          'Other',                 6);

INSERT INTO questions (question_key, created_by)
VALUES ('reporter_name', @created_by);
SET @q2_id := LAST_INSERT_ID();

INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q2_id, 1, 'Name?', 'text', 1, 'Enter your full name.', 1, @created_by);
SET @q2_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by)
VALUES ('reporter_email', @created_by);
SET @q3_id := LAST_INSERT_ID();

INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q3_id, 1, 'Email?', 'text', 1, 'Enter your email address.', 1, @created_by);
SET @q3_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by)
VALUES ('manager_email', @created_by);
SET @q4_id := LAST_INSERT_ID();

INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q4_id, 1, 'Manager''s email:', 'text', 1, 'Enter your manager''s email address.', 1, @created_by);
SET @q4_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by)
VALUES ('why_was_wrong', @created_by);
SET @q5_id := LAST_INSERT_ID();

INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q5_id, 1, 'Why was this wrong?', 'text', 1, 'Explain what happened and why it was incorrect.', 1, @created_by);
SET @q5_v1_id := LAST_INSERT_ID();

INSERT INTO questions (question_key, created_by)
VALUES ('avoid_in_future', @created_by);
SET @q6_id := LAST_INSERT_ID();

INSERT INTO question_versions
  (question_id, version_number, prompt_text, response_type, is_required, help_text, is_active, created_by)
VALUES
  (@q6_id, 1, 'How can this be avoided in the future?', 'text', 1, 'Describe preventative steps or process changes.', 1, @created_by);
SET @q6_v1_id := LAST_INSERT_ID();

INSERT INTO form_version_questions (form_version_id, question_version_id, sort_order) VALUES
(@form_version_id, @q1_v1_id, 1),
(@form_version_id, @q2_v1_id, 2),
(@form_version_id, @q3_v1_id, 3),
(@form_version_id, @q4_v1_id, 4),
(@form_version_id, @q5_v1_id, 5),
(@form_version_id, @q6_v1_id, 6);

COMMIT;

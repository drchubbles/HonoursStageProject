SELECT
    f.title                     AS form_title,
    fv.version_number           AS form_version,
    fvq.sort_order              AS question_order,
    q.question_key,
    qv.version_number           AS question_version,
    qv.prompt_text,
    qv.response_type,
    qv.is_required,
    qv.is_active
FROM forms f
JOIN form_versions fv
    ON fv.form_id = f.form_id
JOIN form_version_questions fvq
    ON fvq.form_version_id = fv.form_version_id
JOIN question_versions qv
    ON qv.question_version_id = fvq.question_version_id
JOIN questions q
    ON q.question_id = qv.question_id
WHERE f.form_key = 'incident_report_v1'
ORDER BY fv.version_number, fvq.sort_order;

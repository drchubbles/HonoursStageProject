INSERT INTO roles (role_name)
SELECT v.role_name
FROM (
  SELECT 'admin' AS role_name
  UNION ALL SELECT 'Standard User'
  UNION ALL SELECT 'Developer'
) v
WHERE NOT EXISTS (
  SELECT 1
  FROM roles r
  WHERE LOWER(r.role_name) = LOWER(v.role_name)
);

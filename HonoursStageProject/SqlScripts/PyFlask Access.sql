DROP DATABASE IF EXISTS HonoursStageProject;
DROP USER IF EXISTS 'review_user'@'localhost';
DROP USER IF EXISTS 'admin'@'localhost';

CREATE DATABASE HonoursStageProject
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

CREATE USER 'admin'@'localhost'
IDENTIFIED BY 'A-Strong-Password';

GRANT ALL PRIVILEGES
ON HonoursStageProject.*
TO 'admin'@'localhost';

FLUSH PRIVILEGES;
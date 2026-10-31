-- Run once on an existing legacy MySQL/MariaDB installation after taking a backup.
UPDATE usuarios SET senha_plana = NULL;
ALTER TABLE usuarios DROP COLUMN senha_plana;

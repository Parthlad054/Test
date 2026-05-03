BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    CREATE TYPE roleenum_v2 AS ENUM ('admin', 'member');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
DECLARE
    users_id_type TEXT;
BEGIN
    SELECT data_type
    INTO users_id_type
    FROM information_schema.columns
    WHERE table_name = 'users' AND column_name = 'id';

    IF users_id_type IN ('integer', 'bigint', 'smallint') THEN
        ALTER TABLE users ADD COLUMN IF NOT EXISTS id_uuid VARCHAR(36);
        UPDATE users SET id_uuid = gen_random_uuid()::text WHERE id_uuid IS NULL;
        ALTER TABLE users ALTER COLUMN id_uuid SET NOT NULL;

        ALTER TABLE projects ADD COLUMN IF NOT EXISTS owner_id_uuid VARCHAR(36);
        UPDATE projects p
        SET owner_id_uuid = u.id_uuid
        FROM users u
        WHERE p.owner_id::text = u.id::text
          AND p.owner_id_uuid IS NULL;

        ALTER TABLE project_members ADD COLUMN IF NOT EXISTS user_id_uuid VARCHAR(36);
        UPDATE project_members pm
        SET user_id_uuid = u.id_uuid
        FROM users u
        WHERE pm.user_id::text = u.id::text
          AND pm.user_id_uuid IS NULL;

        ALTER TABLE tasks ADD COLUMN IF NOT EXISTS created_by_uuid VARCHAR(36);
        UPDATE tasks t
        SET created_by_uuid = u.id_uuid
        FROM users u
        WHERE t.created_by::text = u.id::text
          AND t.created_by_uuid IS NULL;

        ALTER TABLE tasks ADD COLUMN IF NOT EXISTS assigned_to_uuid VARCHAR(36);
        UPDATE tasks t
        SET assigned_to_uuid = u.id_uuid
        FROM users u
        WHERE t.assigned_to::text = u.id::text
          AND t.assigned_to_uuid IS NULL;

        ALTER TABLE task_status_logs ADD COLUMN IF NOT EXISTS changed_by_uuid VARCHAR(36);
        UPDATE task_status_logs tsl
        SET changed_by_uuid = u.id_uuid
        FROM users u
        WHERE tsl.changed_by::text = u.id::text
          AND tsl.changed_by_uuid IS NULL;

        ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_owner_id_fkey;
        ALTER TABLE project_members DROP CONSTRAINT IF EXISTS project_members_user_id_fkey;
        ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_created_by_fkey;
        ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_assigned_to_fkey;
        ALTER TABLE task_status_logs DROP CONSTRAINT IF EXISTS task_status_logs_changed_by_fkey;
        ALTER TABLE users DROP CONSTRAINT IF EXISTS users_pkey;

        ALTER TABLE users DROP COLUMN id;
        ALTER TABLE users RENAME COLUMN id_uuid TO id;
        ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (id);

        ALTER TABLE projects DROP COLUMN owner_id;
        ALTER TABLE projects RENAME COLUMN owner_id_uuid TO owner_id;

        ALTER TABLE project_members DROP COLUMN user_id;
        ALTER TABLE project_members RENAME COLUMN user_id_uuid TO user_id;
        ALTER TABLE project_members DROP CONSTRAINT IF EXISTS project_members_pkey;
        ALTER TABLE project_members ADD CONSTRAINT project_members_pkey PRIMARY KEY (project_id, user_id);

        ALTER TABLE tasks DROP COLUMN created_by;
        ALTER TABLE tasks DROP COLUMN assigned_to;
        ALTER TABLE tasks RENAME COLUMN created_by_uuid TO created_by;
        ALTER TABLE tasks RENAME COLUMN assigned_to_uuid TO assigned_to;

        ALTER TABLE task_status_logs DROP COLUMN changed_by;
        ALTER TABLE task_status_logs RENAME COLUMN changed_by_uuid TO changed_by;
    END IF;
END
$$;

ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS role roleenum_v2;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'global_role'
    ) THEN
        UPDATE users
        SET role = CASE
            WHEN global_role::text LIKE '%admin%' THEN 'admin'::roleenum_v2
            ELSE 'member'::roleenum_v2
        END
        WHERE role IS NULL;
        ALTER TABLE users DROP COLUMN global_role;
    END IF;
END
$$;

UPDATE users SET role = 'member'::roleenum_v2 WHERE role IS NULL;
UPDATE users SET is_active = TRUE WHERE is_active IS NULL;

ALTER TABLE users
    ALTER COLUMN role SET DEFAULT 'member'::roleenum_v2,
    ALTER COLUMN role SET NOT NULL,
    ALTER COLUMN is_active SET DEFAULT TRUE,
    ALTER COLUMN is_active SET NOT NULL;

ALTER TABLE projects
    ALTER COLUMN owner_id TYPE VARCHAR(36);
ALTER TABLE project_members
    ALTER COLUMN user_id TYPE VARCHAR(36);
ALTER TABLE tasks
    ALTER COLUMN created_by TYPE VARCHAR(36),
    ALTER COLUMN assigned_to TYPE VARCHAR(36);
ALTER TABLE task_status_logs
    ALTER COLUMN changed_by TYPE VARCHAR(36);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'projects_owner_id_fkey') THEN
        ALTER TABLE projects
            ADD CONSTRAINT projects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES users(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'project_members_user_id_fkey') THEN
        ALTER TABLE project_members
            ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tasks_created_by_fkey') THEN
        ALTER TABLE tasks
            ADD CONSTRAINT tasks_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tasks_assigned_to_fkey') THEN
        ALTER TABLE tasks
            ADD CONSTRAINT tasks_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES users(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'task_status_logs_changed_by_fkey') THEN
        ALTER TABLE task_status_logs
            ADD CONSTRAINT task_status_logs_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES users(id);
    END IF;
END
$$;

COMMIT;

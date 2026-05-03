BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    CREATE TYPE roleenum AS ENUM ('admin', 'member');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE projectstatusenum AS ENUM ('active', 'archived');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS global_role roleenum;

UPDATE users
SET global_role = CASE
    WHEN id = (SELECT MIN(id) FROM users) THEN 'admin'::roleenum
    ELSE 'member'::roleenum
END
WHERE global_role IS NULL;

ALTER TABLE users
    ALTER COLUMN global_role SET DEFAULT 'member'::roleenum;

UPDATE users
SET global_role = 'member'::roleenum
WHERE global_role IS NULL;

ALTER TABLE users
    ALTER COLUMN global_role SET NOT NULL;

DO $$
DECLARE
    projects_id_type TEXT;
BEGIN
    SELECT data_type
    INTO projects_id_type
    FROM information_schema.columns
    WHERE table_name = 'projects'
      AND column_name = 'id';

    IF projects_id_type IN ('integer', 'bigint', 'smallint') THEN
        ALTER TABLE projects ADD COLUMN IF NOT EXISTS id_uuid VARCHAR(36);
        UPDATE projects SET id_uuid = gen_random_uuid()::text WHERE id_uuid IS NULL;
        ALTER TABLE projects ALTER COLUMN id_uuid SET NOT NULL;

        ALTER TABLE projects ADD COLUMN IF NOT EXISTS owner_id INTEGER;
        UPDATE projects SET owner_id = created_by_id WHERE owner_id IS NULL;
        ALTER TABLE projects ALTER COLUMN owner_id SET NOT NULL;

        ALTER TABLE projects ADD COLUMN IF NOT EXISTS status projectstatusenum;
        UPDATE projects SET status = 'active'::projectstatusenum WHERE status IS NULL;
        ALTER TABLE projects ALTER COLUMN status SET DEFAULT 'active'::projectstatusenum;
        ALTER TABLE projects ALTER COLUMN status SET NOT NULL;

        ALTER TABLE projects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;
        UPDATE projects SET updated_at = COALESCE(created_at, NOW()) WHERE updated_at IS NULL;
        ALTER TABLE projects ALTER COLUMN updated_at SET DEFAULT NOW();
        ALTER TABLE projects ALTER COLUMN updated_at SET NOT NULL;

        ALTER TABLE project_members ADD COLUMN IF NOT EXISTS project_id_uuid VARCHAR(36);
        UPDATE project_members pm
        SET project_id_uuid = p.id_uuid
        FROM projects p
        WHERE pm.project_id::text = p.id::text
          AND pm.project_id_uuid IS NULL;
        ALTER TABLE project_members ALTER COLUMN project_id_uuid SET NOT NULL;

        ALTER TABLE tasks ADD COLUMN IF NOT EXISTS project_id_uuid VARCHAR(36);
        UPDATE tasks t
        SET project_id_uuid = p.id_uuid
        FROM projects p
        WHERE t.project_id::text = p.id::text
          AND t.project_id_uuid IS NULL;
        ALTER TABLE tasks ALTER COLUMN project_id_uuid SET NOT NULL;

        ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_project_id_fkey;
        ALTER TABLE project_members DROP CONSTRAINT IF EXISTS project_members_project_id_fkey;
        ALTER TABLE project_members DROP CONSTRAINT IF EXISTS project_members_pkey;
        ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_pkey;

        ALTER TABLE projects DROP COLUMN id;
        ALTER TABLE projects RENAME COLUMN id_uuid TO id;
        ALTER TABLE projects ADD CONSTRAINT projects_pkey PRIMARY KEY (id);

        ALTER TABLE project_members DROP COLUMN project_id;
        ALTER TABLE project_members RENAME COLUMN project_id_uuid TO project_id;
        ALTER TABLE project_members ADD CONSTRAINT project_members_pkey PRIMARY KEY (project_id, user_id);

        ALTER TABLE tasks DROP COLUMN project_id;
        ALTER TABLE tasks RENAME COLUMN project_id_uuid TO project_id;

        ALTER TABLE projects DROP COLUMN IF EXISTS created_by_id;
    END IF;
END
$$;

ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS owner_id INTEGER;

ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS status projectstatusenum;

ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

UPDATE projects
SET status = 'active'::projectstatusenum
WHERE status IS NULL;

UPDATE projects
SET updated_at = COALESCE(updated_at, created_at, NOW())
WHERE updated_at IS NULL;

ALTER TABLE projects
    ALTER COLUMN status SET DEFAULT 'active'::projectstatusenum;

ALTER TABLE projects
    ALTER COLUMN status SET NOT NULL;

ALTER TABLE projects
    ALTER COLUMN updated_at SET DEFAULT NOW();

ALTER TABLE projects
    ALTER COLUMN updated_at SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'projects_owner_id_fkey'
    ) THEN
        ALTER TABLE projects
            ADD CONSTRAINT projects_owner_id_fkey
            FOREIGN KEY (owner_id) REFERENCES users(id);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'project_members_project_id_fkey'
    ) THEN
        ALTER TABLE project_members
            ADD CONSTRAINT project_members_project_id_fkey
            FOREIGN KEY (project_id) REFERENCES projects(id);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'tasks_project_id_fkey'
    ) THEN
        ALTER TABLE tasks
            ADD CONSTRAINT tasks_project_id_fkey
            FOREIGN KEY (project_id) REFERENCES projects(id);
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS ix_projects_id ON projects (id);
CREATE INDEX IF NOT EXISTS ix_projects_name ON projects (name);

COMMIT;

BEGIN;

DO $$
BEGIN
    CREATE TYPE taskstatus_v2 AS ENUM ('todo', 'in_progress', 'in_review', 'done');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
BEGIN
    CREATE TYPE taskpriority AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

DO $$
DECLARE
    tasks_id_type TEXT;
BEGIN
    SELECT data_type
    INTO tasks_id_type
    FROM information_schema.columns
    WHERE table_name = 'tasks' AND column_name = 'id';

    IF tasks_id_type IN ('integer', 'bigint', 'smallint') THEN
        ALTER TABLE tasks ADD COLUMN IF NOT EXISTS id_uuid VARCHAR(36);
        UPDATE tasks SET id_uuid = gen_random_uuid()::text WHERE id_uuid IS NULL;
        ALTER TABLE tasks ALTER COLUMN id_uuid SET NOT NULL;
    END IF;
END
$$;

ALTER TABLE tasks
    ADD COLUMN IF NOT EXISTS created_by INTEGER,
    ADD COLUMN IF NOT EXISTS assigned_to INTEGER,
    ADD COLUMN IF NOT EXISTS priority taskpriority,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tasks' AND column_name = 'assigned_to_id'
    ) THEN
        UPDATE tasks
        SET assigned_to = assigned_to_id
        WHERE assigned_to IS NULL;
    END IF;
END
$$;

UPDATE tasks
SET created_by = COALESCE(created_by, assigned_to, (SELECT MIN(id) FROM users))
WHERE created_by IS NULL;

UPDATE tasks
SET priority = 'medium'::taskpriority
WHERE priority IS NULL;

UPDATE tasks
SET updated_at = COALESCE(updated_at, created_at, NOW())
WHERE updated_at IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tasks' AND column_name = 'status'
    ) THEN
        ALTER TABLE tasks
            ALTER COLUMN status TYPE taskstatus_v2
            USING (
                CASE
                    WHEN status::text IN ('Pending', 'pending', 'todo') THEN 'todo'::taskstatus_v2
                    WHEN status::text IN ('In Progress', 'in_progress') THEN 'in_progress'::taskstatus_v2
                    WHEN status::text IN ('In Review', 'in_review') THEN 'in_review'::taskstatus_v2
                    WHEN status::text IN ('Done', 'done') THEN 'done'::taskstatus_v2
                    ELSE 'todo'::taskstatus_v2
                END
            );
    END IF;
END
$$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tasks' AND column_name = 'due_date'
    ) THEN
        ALTER TABLE tasks
            ALTER COLUMN due_date TYPE DATE USING due_date::date;
    END IF;
END
$$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tasks' AND column_name = 'id_uuid'
    ) THEN
        ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_pkey;
        ALTER TABLE tasks DROP COLUMN id;
        ALTER TABLE tasks RENAME COLUMN id_uuid TO id;
        ALTER TABLE tasks ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);
    END IF;
END
$$;

ALTER TABLE tasks
    ALTER COLUMN created_by SET NOT NULL,
    ALTER COLUMN status SET DEFAULT 'todo'::taskstatus_v2,
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN priority SET DEFAULT 'medium'::taskpriority,
    ALTER COLUMN priority SET NOT NULL,
    ALTER COLUMN updated_at SET DEFAULT NOW(),
    ALTER COLUMN updated_at SET NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tasks' AND column_name = 'assigned_to_id'
    ) THEN
        ALTER TABLE tasks DROP COLUMN assigned_to_id;
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'tasks_created_by_fkey'
    ) THEN
        ALTER TABLE tasks
            ADD CONSTRAINT tasks_created_by_fkey FOREIGN KEY (created_by) REFERENCES users(id);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'tasks_assigned_to_fkey'
    ) THEN
        ALTER TABLE tasks
            ADD CONSTRAINT tasks_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES users(id);
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS task_status_logs (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
    old_status taskstatus_v2 NOT NULL,
    new_status taskstatus_v2 NOT NULL,
    changed_by INTEGER NOT NULL REFERENCES users(id),
    changed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

COMMIT;

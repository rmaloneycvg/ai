-- Integration test seed data for langgraph postgres tools
-- Runs on container init via docker-entrypoint-initdb.d

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding FLOAT8[],
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tool_executions (
    id SERIAL PRIMARY KEY,
    tool_name TEXT NOT NULL,
    input_params JSONB,
    output TEXT,
    duration_ms INTEGER,
    executed_at TIMESTAMP DEFAULT NOW()
);

-- Seed data
INSERT INTO documents (title, content) VALUES
    ('README', 'This is the project README with installation instructions.'),
    ('API Guide', 'REST API documentation for the widget service.'),
    ('Architecture', 'System architecture overview with service diagram.'),
    ('Deployment', 'Deployment runbook for production environments.'),
    ('Testing', 'Testing strategy and CI/CD pipeline documentation.')
ON CONFLICT DO NOTHING;

INSERT INTO tool_executions (tool_name, input_params, output, duration_ms) VALUES
    ('postgres_query', '{"sql": "SELECT 1"}', '1', 5),
    ('git_status', '{"cwd": "."}', '{"clean": true}', 120),
    ('read_json', '{"path": "config.json"}', '{"success": true}', 3)
ON CONFLICT DO NOTHING;

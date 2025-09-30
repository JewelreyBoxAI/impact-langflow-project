CREATE TABLE IF NOT EXISTS recruiting_interactions (
    id SERIAL PRIMARY KEY,
    prospect_name TEXT,
    prospect_email TEXT UNIQUE,
    prospect_phone TEXT,
    channel TEXT,
    message_content TEXT,
    response_status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);
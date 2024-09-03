--liquibase formatted sql
--changeset wburklund:dbinit

CREATE EXTENSION vector;

CREATE TABLE user_ (
    id UUID NOT NULL,
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    is_enabled BOOLEAN NOT NULL,
    last_login TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE (username)
);

CREATE TABLE ruleset (
    id UUID NOT NULL,
    owner_id UUID NOT NULL,
    name TEXT NOT NULL,
    last_update TIMESTAMP NOT NULL,
    expression JSONB NOT NULL,
    schema_version TEXT NOT NULL,
    is_active BOOLEAN NOT NULL,  -- Whether to run this ruleset in Databricks

    PRIMARY KEY (id),
    UNIQUE (name),
    FOREIGN KEY (owner_id) REFERENCES user_(id)
);

CREATE TABLE sentence (
    source_id TEXT NOT NULL,
    source TEXT NOT NULL,
    createdatetime TIMESTAMP NOT NULL,
    pidm INT,
    type TEXT NOT NULL,
    sentence_text TEXT NOT NULL,
    sentence_pos INT NOT NULL,
    sentiment TEXT NOT NULL,
    intent_type TEXT NOT NULL,
    agent TEXT[] NOT NULL,
    lemma TEXT[] NOT NULL,
    theme TEXT[] NOT NULL,
    goal TEXT[] NOT NULL,
    beneficiary TEXT[] NOT NULL,
    entities_related_to_lemma TEXT[] NOT NULL,
    embedding vector(384),

    PRIMARY KEY (source_id, source, sentence_pos)
);

-- Default index name is {{table}}_{{"_".join(columns)}}_idx
CREATE INDEX ON sentence(source_id);
CREATE INDEX ON sentence(source);
CREATE INDEX ON sentence(type);
CREATE INDEX ON sentence(sentiment);
CREATE INDEX ON sentence(intent_type);
CREATE INDEX ON sentence USING gin(agent);
CREATE INDEX ON sentence USING gin(lemma);
CREATE INDEX ON sentence USING gin(theme);
CREATE INDEX ON sentence USING gin(goal);
CREATE INDEX ON sentence USING gin(beneficiary);
CREATE INDEX ON sentence USING gin(entities_related_to_lemma);
CREATE INDEX sentence_embedding_cosine_idx ON sentence USING hnsw(embedding vector_cosine_ops);

--rollback DROP INDEX sentence_embedding_cosine_idx;
--rollback DROP INDEX sentence_entities_related_to_lemma_idx;
--rollback DROP INDEX sentence_beneficiary_idx;
--rollback DROP INDEX sentence_goal_idx;
--rollback DROP INDEX sentence_theme_idx;
--rollback DROP INDEX sentence_lemma_idx;
--rollback DROP INDEX sentence_agent_idx;
--rollback DROP INDEX sentence_intent_type_idx;
--rollback DROP INDEX sentence_sentiment_idx;
--rollback DROP INDEX sentence_type_idx;
--rollback DROP INDEX sentence_source_idx;
--rollback DROP INDEX sentence_source_id_idx;
--rollback DROP TABLE sentence;
--rollback DROP TABLE ruleset;
--rollback DROP TABLE user_;
--rollback DROP EXTENSION vector;
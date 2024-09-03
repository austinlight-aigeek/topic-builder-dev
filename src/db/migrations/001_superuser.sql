--liquibase formatted sql
--changeset wburklund:superuser

ALTER TABLE user_ ADD COLUMN is_superuser BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE user_ ALTER COLUMN is_superuser DROP DEFAULT;

--rollback ALTER TABLE user_ DROP COLUMN is_superuser;
# NLP Topic Builder Local Deployment Developer Guide

## 1. Python Environment

- Install `python 3.12.0` and activate virtual environment by running `python -m venv venv` and `source venv/bin/activate`.

- Install python packages by running command: `pip install .`. It will install all dependencies from `pyproject.toml` file.

## 2. Install `liquibase`

- `brew install liquibase` will install `liquibase`, or consult https://docs.liquibase.com/start/install/liquibase-macos.html for more information.

- Verify it's installation using `liquibase --version` command.

## 3. Pull Docker Images and Migrate database

- First comment out `nlpui` service in `docker-compose.yml` file.

- You can only see empty tables inside postgres database.

- `liquibase update` will migrate database changes and you should see tables in postgres database.

## 4. Create a new user

- `create_user -u example.name` will creat a new user and set password.

- In postgres database `user_`table set a new user as super user.

## 5. Databricks configuration

- In Databricks, click `Edit` for compute cluster to be used and set `Assigned` to current user email. and Start running compute cluster

- Go to `Settings/Developer/Access Token/Manage`, click `Generate new token` button if you don't have Databricks access token. Copy token somewhere safe.

- Edit `~/.databrickscfg` file with the following content. Replace `YOUR_CLUSTER_ID` and `DATABRIKCS_TOKEN` with your own

```md
; The profile defined in the DEFAULT section is to be used as a fallback when no profile is explicitly specified.
[DEFAULT]

[wgu-prod]
host = https://wgu-prod.cloud.databricks.com/
cluster_id = [YOUR_CLUSTER_ID]
token = [DATABRIKCS_TOKEN]
```

## 6. Load sentences from Databricks to postgres

- Once Compute Cluster is ready, run `load_sentence_sample` command to load sample sentences to postres.

- Refresh `sentence` table in postgres to confirm sample sentences are loaded.

## 7. Run project
 
- Uncomment `docker-compose` file by reverting Section 3.

- `docker-compose up -d` will run `docker` containers and `localhost:8080` will be accessible.

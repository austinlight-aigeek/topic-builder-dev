# NLP Topic Builder Local Deployment Developer Guide

## 1. Setting Up the Python Environment

- Install `python 3.12.0`.

- Set up a virtual environment:

    ```
    python -m venv venv
    source venv/bin/activate
    ```

- Install the required dependencies by running `pip install .`. This will install all necessary packages specified in the pyproject.toml file.

## 2. Installing `liquibase`

- Install Liquibase using Homebrew: `brew install liquibase`. For more detailed instructions, refer to the official Liquibase [macOS installation guide](https://docs.liquibase.com/start/install/liquibase-macos.html).

- Confirm the installation by running: `liquibase --version`.

## 3. Database Setup and Migration

- Open the `docker-compose.yml` file and temporarily comment out the `nlpui` service.

- Pull the required Docker images by running `docker-compose pull`.

- Verify that the PostgreSQL database contains empty tables.

- Migrate the database changes using Liquibase: `liquibase update`. After running this command, you should see the updated tables in the PostgreSQL database.

## 4. Creating a New User

- To create a new user, execute the following command: `create_user -u user.name`. This command will prompt you to set a password for the user. After the user is created, set the user as a superuser in the `user_` table in the PostgreSQL database.

- `create_user -u example.name` will creat a new user and set password.

- In postgres database `user_`table set a new user as super user.

## 5. Configuring Databricks

- In Databricks, navigate to the compute cluster you wish to use and click `Edit`. Assign the current user’s email to the cluster by setting it to `Assigned`.

- Start the compute cluster.

- If you do not have an access token, navigate to `Settings → Developer → Access Token → Manage` and click `Generate new token`. Save this token securely.

- Go to `Settings/Developer/Access Token/Manage`, click `Generate new token` button if you don't have Databricks access token. Copy token somewhere safe.

- Update your `~/.databrickscfg` configuration file as follows:

    ```
    [DEFAULT]

    [wgu-prod]
    host = https://wgu-prod.cloud.databricks.com/
    cluster_id = [YOUR_CLUSTER_ID]
    token = [DATABRICKS_TOKEN]
    ```

    Replace [YOUR_CLUSTER_ID] and [DATABRICKS_TOKEN] with your actual cluster ID and Databricks token.

## 6. Loading Sentences from Databricks to PostgreSQL

- Once the compute cluster is ready, load the sample sentences into PostgreSQL by running: `load_sentence_sample`.
    Afterward, verify that the sentences are loaded correctly by refreshing the sentence table in the PostgreSQL database.

## 7. Running the Project
 
- Uncomment the `nlpui` service in the `docker-compose.yml` file (revert the changes made in Section 3).

- Start the Docker containers by running `docker-compose up -d`.

- Once the containers are running, you can access the application at [localhost:8080](http://localhost:8080).

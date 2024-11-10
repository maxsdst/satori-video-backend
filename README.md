### Requisites

1. **Docker**  
   Ensure that Docker is installed on your system.

2. **S3-Compatible Storage (for production mode)**  
   An S3-compatible storage service like AWS S3 or DigitalOcean Spaces is required for storing files.

3. **PostgreSQL (for production mode)**  
   Two PostgreSQL databases are required: one for the Django application and one for the Gorse recommendation system. The database user must have all necessary privileges, such as creating, reading, updating, and deleting data.

4. **Redis (for production mode)**  
   Required for both Django and Gorse. A single Redis instance can be used for both.

<br/>

### Installation

1. **Clone the repository**  
   Clone the repository to your local machine:

    ```bash
    git clone https://github.com/maxsdst/satori-video-backend.git
    cd satori-video-backend
    ```

2. **Run in development mode**  
   Start the development server using Docker:

    ```bash
    docker compose -f docker-compose.dev.yml up
    ```

    The server will be available at [`http://localhost:8000`](http://localhost:8000).

3. **Run tests**

    - **Step 1: Install dependencies and activate the virtual environment**  
      Make sure [Pipenv](https://pipenv.pypa.io/en/latest/) is installed. Then, install the dependencies and activate the virtual environment:

        ```bash
        pipenv install --dev
        pipenv shell
        ```

    - **Step 2: Start the test environment using Docker**

        ```bash
        docker compose -f docker-compose.test.yml up -d
        ```

    - **Step 3: Run the tests**

        ```bash
        pytest
        ```

4. **Production setup**

    - **Step 1: Create the `/env` directory**  
      Create an `env` directory in the system root:

        ```bash
        mkdir /env
        ```

    - **Step 2: Create the `backend.env` file**  
      Inside the `/env` directory, create a file named `backend.env` and add the following environment variables:

        ```plaintext
        DOMAIN_NAME=example.com

        # List of allowed hosts separated by commas
        ALLOWED_HOSTS=example.com

        # Gunicorn configuration
        WEB_CONCURRENCY=1

        # S3 Storage configuration
        S3_ACCESS_KEY=example_key
        S3_BUCKET_NAME=bucket_name
        S3_ENDPOINT_URL=https://example.amazonaws.com
        S3_REGION_NAME=region_name
        S3_CUSTOM_DOMAIN=media.example.com
        ```

    - **Step 3: Create the `gorse.env` file**  
      In the `/env` directory, create a file named `gorse.env` and add the following environment variables:

        ```plaintext
        GORSE_SERVER_API_KEY=example_gorse_key
        GORSE_DATA_STORE=postgresql://username:password@example.com/example_gorse_db?sslmode=require
        GORSE_CACHE_STORE=rediss://username:password@example.com
        GORSE_DASHBOARD_USER_NAME=admin
        GORSE_DASHBOARD_PASSWORD=example123
        ```

    - **Step 4: Create the `/secrets` directory**  
      Create a `secrets` directory in the system root:

        ```bash
        mkdir /secrets
        ```

    - **Step 5: Add secret files**  
      Create the following files in the `/secrets` directory to store sensitive data:

        ```bash
        # Database URL
        echo -n "postgresql://username:password@example.com/example_db?sslmode=require" > /secrets/database_url

        # Redis URL
        echo -n "rediss://username:password@example.com" > /secrets/redis_url

        # Django secret key
        echo -n "example_django_key" > /secrets/secret_key

        # Gorse API key (same as defined in /env/gorse.env)
        echo -n "example_gorse_key" > /secrets/gorse_api_key

        # AWS S3 secret key
        echo -n "example_s3_key" > /secrets/s3_secret_key
        ```

5. **Run in production mode**  
   Start the production server using Docker:
    ```bash
    docker compose -f docker-compose.prod.yml up
    ```

# Project Plan: Gemini API Proxy

## 1. Project Goals

The primary goal of this project is to create a proxy server for the Gemini API that provides key management, intelligent error handling, and usage reporting. This will allow applications to interact with the Gemini API more robustly and efficiently.

## 2. Core Features

### 2.1. API Key Management
- **Round-Robin Key Rotation:** The proxy will manage a pool of Gemini API keys defined in a `.env` file. For each incoming request, it will select the next available key in a round-robin fashion.
- **Usage Tracking:** The proxy will track the usage of each key, counting the number of requests per minute and per day.

### 2.2. Intelligent Error Handling
- **"Model Overloaded" Retries:** If a request to the Gemini API fails with a "Model Overloaded" error, the proxy will not immediately return an error to the client. Instead, it will wait for a fixed delay and then retry the request. This process will be repeated until a successful response is received.
- **"Resource Exhausted" Management:** If a request fails with a "Resource Exhausted" error, the proxy will:
    - Identify whether the quota was exceeded for the minute or the day.
    - Temporarily remove the exhausted key from the rotation pool.
    - The key will be returned to the pool after the appropriate time has passed (i.e., at the start of the next minute or the next day).

### 2.3. Client Authentication
- The proxy will authenticate incoming requests using one of the following methods, in order of precedence:
    1.  **`x-goog-api-key` Header:** Check if the header is present and its value matches one of the round-robin keys or a dedicated authentication key.
    2.  **`key` Query Parameter:** If the header is not present or doesn't match, check for a `key` query parameter and validate its value.
- The `key` query parameter will always be stripped from the request before it is forwarded to the Gemini API.

### 2.4. Usage Reporting
- A JSON endpoint will be available at a configurable subpath (e.g., `/status`).
- This endpoint will provide a report of:
    - Total requests made in the last 60 seconds.
    - Total requests made during the current day (Pacific Time).

## 3. Architectural Plan

### 3.1. Technology Stack
- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Dependencies:**
    - `fastapi`: For building the API.
    - `uvicorn`: As the ASGI server.
    - `httpx`: For making asynchronous HTTP requests to the Gemini API.
    - `python-dotenv`: For managing environment variables.
    - `zoneinfo`: (Part of the standard library in Python 3.9+) For handling Pacific Time conversions.

### 3.2. System Components
- **Main Application (`main.py`):**
    - Initializes the FastAPI application.
    - Loads configuration from the `.env` file.
    - Sets up the API key manager and other services.
    - Defines the main proxy endpoint, the reporting endpoint, and a health check endpoint.
- **API Key Manager (`key_manager.py`):**
    - Manages the pool of API keys using an `asyncio.Lock` to ensure thread safety.
    - Handles key rotation, usage tracking, and temporary removal of exhausted keys.
    - Provides a method to get the next available key.
- **Request Forwarder (`forwarder.py`):**
    - Receives the incoming request.
    - Authenticates the client.
    - Gets a key from the `key_manager`.
    - Forwards the request to the Gemini API.
    - Implements the retry logic for "Model Overloaded" errors.
- **Configuration (`config.py`):**
    - Defines and loads all configuration variables from the `.env` file.
    - **Environment Variables:**
        - `GEMINI_API_KEYS`: A comma-separated list of Gemini API keys for round-robin usage.
        - `AUTH_KEY`: An optional, dedicated key for client authentication.
        - `RETRY_DELAY_SECONDS`: The fixed delay (in seconds) for retrying "Model Overloaded" errors.
        - `PORT`: The port for the proxy server.
        - `UPSTREAM_URL`: The base URL for the Gemini API (e.g., `https://generativelanguage.googleapis.com`).
        - `REPORTING_PATH`: The subpath for the JSON reporting endpoint.

### 3.3. Data Models
- **APIKeyUsage:** A data structure (e.g., a Python dictionary or a Pydantic model) to store the usage information for each key:
    - `key`: The API key string.
    - `requests_last_minute`: A list of timestamps for requests made in the last 60 seconds.
    - `requests_today`: A count of requests made on the current day (Pacific Time).
    - `is_exhausted_minute`: A boolean flag indicating if the key has hit the per-minute quota.
    - `is_exhausted_day`: A boolean flag indicating if the key has hit the per-day quota.
    - `exhausted_until`: A timestamp indicating when the key can be used again.

### 3.4. Deployment Strategy
- The application will be packaged as a Docker container.
- A `Dockerfile` will be created to define the container image.
- The `.env` file will be mounted into the container at runtime to provide the configuration.
- The application can be run on any container orchestration platform (e.g., Docker Compose, Kubernetes) or a cloud service like Google Cloud Run.
- A 'docker-compose.yml' will be created to maximally ease deployement of the Dockerfile.

## 4. Next Steps
- Review and approve this plan.
- Proceed with the implementation of the proxy server.
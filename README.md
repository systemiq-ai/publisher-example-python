

# Simple Publisher for Middleware Integration

This script demonstrates how to send structured data and files to a local Middleware system using gRPC. It includes:
- Simulated data publishing
- File publishing via base64 encoding
- A configurable middleware endpoint

## Features

- Publishes dummy telemetry data at 10-second intervals
- Publishes a local file (e.g. `dummy.pdf`) encoded as base64
- Uses a simple batch system via the `Publisher` interface

## Requirements

- Python 3.13+
- Middleware gRPC endpoint running locally or remotely

## Setup

Install dependencies from the root project directory:

```bash
pip install -r requirements.txt
```

## Configuration

Set the middleware endpoint using an environment variable. If not set, it defaults to `localhost:50051`.

```bash
export MIDDLEWARE_ENDPOINT="localhost:50051"
```

Ensure a file named `dummy.pdf` exists in the same folder as the script if you wish to test file publishing.

## Usage

Uncomment the relevant lines in `main()` to activate publishing.

```python
# To set a custom indicator instead of using the default:
# publisher.set_indicator("custom_indicator_name")

# To publish data or files:
# publisher.batch(ELEMENT_ID, [data], "process")

# To store files:
# publisher.batch(ELEMENT_ID, [file_data], "store")
```

Run the script:

```bash
python main.py
```

## Customization

- Adjust `ELEMENT_ID` to change the dataset identifier
- Replace `fetch_data()` with real sensor or telemetry logic
- Replace `dummy.pdf` with any file you wish to transmit

## Docker

The repository includes a `Dockerfile` that sets up Python 3.13-slim, installs the dependencies in `requirements.txt`, and starts `main.py`.

### Build the image

```bash
docker build -t publisher-example .
```

### Run the container in production mode

```bash
docker run --rm \
  --name publisher-example \
  -e MIDDLEWARE_ENDPOINT="localhost:50051" \
  publisher-example
```

### Run the container in development mode with auto-reload

Mount the source code from your host into the container and switch the environment variable so that `watchmedo` restarts the process when you save a change.

```bash
docker run --rm \
  --name publisher-example-dev \
  -e ENVIRONMENT="development" \
  -e MIDDLEWARE_ENDPOINT="localhost:50051" \
  -v "$(pwd)":/app \
  publisher-example
```



### Working with files

The script reads **dummy.pdf** from the project folder. To substitute another file, mount or copy it into `/app` with the same file name, or change the path in `main.py` and rebuild the image.


## Docker Compose

You can run both Middleware and the Publisher script together using Docker Compose without exposing any ports, as long as they operate inside a trusted internal network.

Here is a basic example:

```yaml
services:

  middleware:
    image: ghcr.io/systemiq-ai/middleware:latest
    environment:
      - AUTH_EMAIL=middleware+1234@systemiq.ai # IAM user email
      - AUTH_PASSWORD=supersecret # Password for the IAM user
      - AUTH_CLIENT_ID=2 # Client ID issued by IAM
      - TEST_MODE=true # Optional. default false

  publisher-example:
    build: .
    environment:
      - ENVIRONMENT=development
      - MIDDLEWARE_ENDPOINT=middleware:50051
    depends_on:
      - middleware
    volumes:
      - ./publisher_example:/app # Mount for hot-reloading
```

This setup allows the publisher to connect to the middleware service directly using the internal hostname `middleware`.

To run:

```bash
docker compose up
```

## License

MIT © [systemiq.ai](https://systemiq.ai)
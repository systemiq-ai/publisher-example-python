import logging
import os
import base64
import time
from publisher_service import Publisher

# Unique identifier for the dataset
ELEMENT_ID = 1234

# Connect to Middleware's local gRPC endpoint
MIDDLEWARE_ENDPOINT = os.getenv("MIDDLEWARE_ENDPOINT", "localhost:50051")
publisher = Publisher(middleware_endpoint=MIDDLEWARE_ENDPOINT)

def fetch_data():
    """
    Simulated data collection function.
    Replace with actual logic to gather data.
    """
    return {
        "timestamp": int(time.time()),
        "value": 42.5,  # Example data value
    }

def fetch_file_data(file_path: str):
    """
    Read a local file from the filesystem, encode it as base64, and
    return a dictionary ready for Publisher.batch with the
    "process_files" operation.
    """
    with open(file_path, "rb") as f:
        base64_str = base64.b64encode(f.read()).decode("utf-8")

    return {
        "base64": base64_str,
        "filename": os.path.basename(file_path),
    }

def main():
    logging.basicConfig(level=logging.INFO)
    
    # Optional: Set a custom indicator instead of using the default
    # publisher.set_indicator("custom_indicator_name")

    # Example: Read and publish a local file (filename.pdf) as base64
    # file = os.path.join(os.path.dirname(__file__), "dummy.pdf")
    # file_data = fetch_file_data(file)
    # logging.info(f"Publishing file data to Middleware: {file_data}")

    # Send a batch of file data to Middleware for processing
    # status = publisher.batch(ELEMENT_ID, [file_data], "process")
    # logging.info(f"Status: {status}")

    # Send a batch of file data to Middleware for storing
    # status = publisher.batch(ELEMENT_ID, [file_data], "store")
    # logging.info(f"Status: {status}")

    # Periodically collect and publish simulated data values
    while True:
        try:
            data = fetch_data()
            logging.info(f"Publishing data to Middleware: {data}")

            # Send a batch of data to Middleware for processing
            status = publisher.batch(ELEMENT_ID, [data], "process")
            logging.info(f"Status: {status}") # Status: SUCCESS
        except Exception as e:
            logging.error(f"Error publishing data: {e}")

        time.sleep(10)  # Publish data every 10 seconds

if __name__ == "__main__":
    main()
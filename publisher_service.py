import time
import grpc
import logging
import json
from protos import observer_pb2, observer_pb2_grpc

class Publisher:
    def __init__(self, middleware_endpoint='localhost:50051', max_msg_size_mb=4):
        """
        Initializes the gRPC channel and stub for publishing data.
        """
        self.middleware_endpoint = middleware_endpoint
        max_bytes = max_msg_size_mb * 1024 * 1024
        self.channel = grpc.insecure_channel(
            self.middleware_endpoint,
            options=[
                ('grpc.max_send_message_length', max_bytes),
            ]
        )
        self.stub = observer_pb2_grpc.DataObserverStub(self.channel)
        self.indicator = "default"  # Default Indicator

    def set_indicator(self, indicator):
        """
        Sets the indicator to be used in publishing requests.
        """
        self.indicator = indicator

    def format_data(self, data_dicts, action):
        """
        Validates and formats data for publishing.
        Returns (formatted_data, updated_action, err_code).
        If an error occurs, formatted_data and updated_action are None and err_code contains a string.
        """
        err = None

        # Basic validation
        if not data_dicts:
            return None, None, "NO_DATA_ERROR"

        has_base64 = [("base64" in d) for d in data_dicts]
        has_filename = [("filename" in d) for d in data_dicts]

        # Consistency checks
        if any(has_base64) and not all(has_base64):
            return None, None, "BASE64_INCONSISTENT_ERROR"

        if any(has_base64) and not all(has_filename):
            return None, None, "MISSING_FILENAME_ERROR"

        is_file = any(has_base64)

        # Action adjustments and validation
        if is_file:
            if action in ["process", "skip", "store"]:
                action += "_file"
            else:
                return None, None, "UNSUPPORTED_FILE_ACTION_ERROR"
        else:
            if action not in ["process", "skip"]:
                return None, None, "INVALID_ACTION_ERROR"

        formatted_data = [json.dumps(entry) for entry in data_dicts]
        return formatted_data, action, None

    def batch(self, element_id, data_dicts, action="process", retries=3, reconnect_retries=3, delay=2):
        """
        Publishes a batch of data to the middleware using gRPC with retry logic.
        If all retries fail due to an unavailable connection, attempts to reestablish the connection.
        """
        # Check if indicator is set
        if not self.indicator:
            logging.error("No indicator set. Cannot publish data.")
            return "NO_INDICATOR_ERROR"

        try:
            formatted_data, action, err = self.format_data(data_dicts, action)

            if err:
                logging.error(f"format_data error: {err}")
                return err
        
            observation_request = observer_pb2.ObservationRequest(
                data=formatted_data,
                indicator=self.indicator,
                element_id=element_id,
                action=action
            )

            for attempt in range(retries):
                try:
                    response = self.stub.ObserveData(observation_request)
                    return response.status.upper()  # Return SUCCESS if no error
                except grpc.RpcError as e:
                    if e.code() == grpc.StatusCode.UNAVAILABLE:
                        logging.warning(f"gRPC unavailable. Retry {attempt + 1}/{retries} in {delay} sec...")
                        time.sleep(delay)  # Wait before retrying
                    else:
                        logging.error(f"gRPC error occurred: {e.code()} - {e.details()}")
                        return "INTERNAL_ERROR"

            logging.error(f"gRPC request failed after {retries} attempts. Attempting to reestablish connection...")

            # Attempt to reestablish the connection
            for reconnect_attempt in range(reconnect_retries):
                try:
                    logging.info(f"Reconnecting to gRPC server... Attempt {reconnect_attempt + 1}/{reconnect_retries}")
                    self.channel = grpc.insecure_channel(self.middleware_endpoint)
                    self.stub = observer_pb2_grpc.DataObserverStub(self.channel)
                    time.sleep(delay)  # Allow time for the connection to stabilize

                    # Retry the request after reconnection
                    response = self.stub.ObserveData(observation_request)
                    return response.status.upper()  # Return SUCCESS if no error
                except grpc.RpcError as e:
                    logging.warning(f"Reconnection attempt {reconnect_attempt + 1} failed: {e.code()} - {e.details()}")
                    time.sleep(delay)

            logging.error(f"Failed to reconnect after {reconnect_retries} attempts.")
            return "FAILED"

        except grpc.RpcError as e:
            logging.error(f"gRPC error occurred: {e.code()} - {e.details()}")
            return "INTERNAL_ERROR"
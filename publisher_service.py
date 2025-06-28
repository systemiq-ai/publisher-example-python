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

    def format_data(self, data_dicts):
        """
        Converts a list of dictionaries into a list of JSON-encoded strings.
        """
        return [json.dumps(entry) for entry in data_dicts]

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
            formatted_data = self.format_data(data_dicts)
            observation_request = observer_pb2.ObservationRequest(
                data=formatted_data,
                indicator=self.indicator,
                element_id=element_id,
                action=action
            )

            for attempt in range(retries):
                try:
                    response = self.stub.ObserveData(observation_request)
                    return response.status  # Return success if no error
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
                    return response.status  # Return success if no error
                except grpc.RpcError as e:
                    logging.warning(f"Reconnection attempt {reconnect_attempt + 1} failed: {e.code()} - {e.details()}")
                    time.sleep(delay)

            logging.error(f"Failed to reconnect after {reconnect_retries} attempts.")
            return "FAILED"

        except grpc.RpcError as e:
            logging.error(f"gRPC error occurred: {e.code()} - {e.details()}")
            return "INTERNAL_ERROR"
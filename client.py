import socket
import os
import protocol
import hashlib
import threading
import logging

# Global constants
SERVER_HOST = '127.0.0.1'  # Server address
SERVER_PORT = 12345  # Server port
HASH_LENGTH = 3
ORIGINAL_HASH = "-1"

# Create an Event object to signal when the number is found
stop_work = threading.Event()

# Configure logging
logging.basicConfig(filename='client.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Client:

    def __init__(self, client_socket, cpu_cores_num):
        self.client_socket = client_socket
        self.cpu_cores_num = cpu_cores_num

    def start_client(self):
        """
        Starts the client, sends CPU core information to the server, and handles the hash computation.
        :return: None
        """
        try:
            # Send the start connection message with the CPU cores as the parameter
            start_message = protocol.encode_protocol(protocol.START_CONNECTION, str(self.cpu_cores_num))
            protocol.send_message(self.client_socket, start_message)

            # Get the range and desired hash results
            raw_message = protocol.receive_message(self.client_socket)
            msg_type, msg_params = protocol.decode_protocol(raw_message)

            if msg_type == protocol.SEND_DETAILS:
                # before starting to compute hash, set a thread which will listen for quit message
                threading.Thread(target=self.wait_for_quit).start()

                results = self.handle_threads(*msg_params)

                if results != "-1":  # Found the hash
                    message = protocol.encode_protocol(protocol.FOUND, ORIGINAL_HASH)
                    protocol.send_message(self.client_socket, message)
                    logging.info(f"Found hash! {results}")
                else:  # Didn't find hash
                    message = protocol.encode_protocol(protocol.NOT_FOUND, results)
                    protocol.send_message(self.client_socket, message)
                    logging.info(f"Didn't find hash, searched from {msg_params[1]} to {msg_params[2]}")

        except ValueError as e:
            logging.error(f"Value error: {e}")
        except socket.error as e:
            logging.error(f"Socket error: {e}")
        finally:
            # Close the connection
            self.client_socket.close()

    def wait_for_quit(self):
        """
        check if the server shuts down hash work or if the hash had been found by the client
        :return:
        """
        try:
            while not stop_work.is_set():
                raw_data = protocol.receive_message(self.client_socket)
                msg_type, params = protocol.decode_protocol(raw_data)
                if msg_type == protocol.STOP_WORK:
                    logging.info("Got quit message from server, stopping work")
                    stop_work.set()
                    return
        except socket.error as se:
            # the socket was closed due to program finished, so ignore the error
            return

    def handle_threads(self, desired_hash, range_start, range_end):
        """
        Handles the creation and management of threads for hash computation.

        :param desired_hash: The target hash to be matched.
        :param range_start: The start of the number range to search.
        :param range_end: The end of the number range to search.
        :return: The original hash if found, "-1" otherwise.
        """
        try:
            range_start = int(range_start)
            range_end = int(range_end)
            capacity = range_end - range_start
            capacity_per_thread = capacity // self.cpu_cores_num
            threads = []

            for i in range(self.cpu_cores_num):
                thread_start_range = range_start + i * capacity_per_thread
                thread_end_range = range_start + (i + 1) * capacity_per_thread
                thread = threading.Thread(target=self.compute_hash, args=(desired_hash,
                                                                          thread_start_range,
                                                                          thread_end_range))
                threads.append(thread)

            # Start the threads
            for thread in threads:
                thread.start()

            # Wait for all threads to finish
            for thread in threads:
                thread.join()

            # Return results
            return ORIGINAL_HASH
        except ValueError as e:
            logging.error(f"Value error in range parsing: {e}")
            return "-1"

    def compute_hash(self, desired_hash, range_start, range_end):
        """
        Computes the hash for a range of numbers and compares it with the desired hash.

        :param desired_hash: The target hash to be matched.
        :param range_start: The start of the number range.
        :param range_end: The end of the number range.
        :return: None
        """
        global ORIGINAL_HASH
        try:
            # Iterate over the range from start to end
            for num in range(range_start, range_end + 1):
                # Check if the event has been set by another thread
                if stop_work.is_set():
                    return
                # Pad the number according to the hash length (e.g., 5 -> "00005" if length is 5)
                padded_str = str(num).zfill(HASH_LENGTH)

                # Compute the MD5 hash for the padded string
                hash_obj = hashlib.md5(padded_str.encode())
                hash_guess = hash_obj.hexdigest()

                # Check if the generated hash matches the desired hash
                if hash_guess == desired_hash:
                    stop_work.set()  # Signal that the solution is found
                    ORIGINAL_HASH = str(num)  # Return the number if hash matches
                    logging.info(f"Desired hash found: {padded_str} -> {hash_guess}")

                return
        except Exception as e:
            logging.error(f"Error during hash computation: {e}")


def main():
    """
    Main function to connect the client to the server and start the client process.
    :return: None
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to the server
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        cpu_cores_num = os.cpu_count()
        client = Client(client_socket, cpu_cores_num)
        client.start_client()
    except socket.error as e:
        logging.critical(f"Failed to connect to the server: {e}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()

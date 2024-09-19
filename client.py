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
found_event = threading.Event()

# Configure logging
logging.basicConfig(filename='client.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def start_client(client_socket):
    """
    Starts the client, sends CPU core information to the server, and handles the hash computation.

    :param client_socket: The socket object for the client connection.
    :return: None
    """
    try:
        # Get the number of CPU cores
        cpu_cores_num = os.cpu_count()

        # Send the start connection message with the CPU cores as the parameter
        start_message = protocol.encode_protocol(protocol.START_CONNECTION, str(cpu_cores_num))
        protocol.send_message(client_socket, start_message)

        # Get the range and desired hash results
        raw_message = protocol.receive_message(client_socket)
        msg_type, msg_params = protocol.decode_protocol(raw_message)

        if msg_type == protocol.SEND_DETAILS:
            results = handle_threads(cpu_cores_num, *msg_params)
            if results != "-1":  # Found the hash
                message = protocol.encode_protocol(protocol.FOUND, ORIGINAL_HASH)
                protocol.send_message(client_socket, message)
                logging.info(f"Found hash! {results}")
            else:  # Didn't find hash
                message = protocol.encode_protocol(protocol.NOT_FOUND, results)
                protocol.send_message(client_socket, message)
                logging.info(f"Didn't find hash, searched from {msg_params[1]} to {msg_params[2]}")
    except ValueError as e:
        logging.error(f"Value error: {e}")
    except socket.error as e:
        logging.error(f"Socket error: {e}")
    finally:
        # Close the connection
        client_socket.close()


def handle_threads(num_of_cores, desired_hash, range_start, range_end):
    """
    Handles the creation and management of threads for hash computation.

    :param num_of_cores: Number of CPU cores available for threading.
    :param desired_hash: The target hash to be matched.
    :param range_start: The start of the number range to search.
    :param range_end: The end of the number range to search.
    :return: The original hash if found, "-1" otherwise.
    """
    try:
        range_start = int(range_start)
        range_end = int(range_end)
        capacity = range_end - range_start
        capacity_per_thread = capacity // num_of_cores
        threads = []

        for i in range(num_of_cores):
            thread_start_range = range_start + i * capacity_per_thread
            thread_end_range = range_start + (i + 1) * capacity_per_thread
            thread = threading.Thread(target=compute_hash, args=(desired_hash, thread_start_range, thread_end_range))
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


def compute_hash(desired_hash, range_start, range_end):
    """
    Computes the hash for a range of numbers and compares it with the desired hash.

    :param desired_hash: The target hash to be matched.
    :param range_start: The start of the number range.
    :param range_end: The end of the number range.
    :return: None
    """
    global ORIGINAL_HASH
    try:
        while not found_event.is_set():  # Check if the event has been set by another thread
            # Iterate over the range from start to end
            for num in range(range_start, range_end + 1):
                # Pad the number according to the hash length (e.g., 5 -> "00005" if length is 5)
                padded_str = str(num).zfill(HASH_LENGTH)

                # Compute the MD5 hash for the padded string
                hash_obj = hashlib.md5(padded_str.encode())
                hash_guess = hash_obj.hexdigest()

                # Check if the generated hash matches the desired hash
                if hash_guess == desired_hash:
                    found_event.set()  # Signal that the solution is found
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
        start_client(client_socket)
    except socket.error as e:
        logging.critical(f"Failed to connect to the server: {e}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()

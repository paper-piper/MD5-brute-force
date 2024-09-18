import socket
import os
import protocol
import hashlib
import threading

# Global constants
SERVER_HOST = '127.0.0.1'  # Server address
SERVER_PORT = 12345  # Server port
HASH_LENGTH = 3
ORIGINAL_HASH = "-1"

# Create an Event object to signal when the number is found
found_event = threading.Event()


def start_client():
    # Create a socket object
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    client_socket.connect((SERVER_HOST, SERVER_PORT))

    # Get the number of CPU cores
    cpu_cores_num = os.cpu_count()

    # Send the start connection message with the CPU cores as the parameter
    start_message = protocol.encode_protocol(protocol.START_CONNECTION, str(cpu_cores_num))
    protocol.send_message(client_socket, start_message)

    # get the range and desired hash results
    raw_message = protocol.receive_message(client_socket)
    msg_type, msg_params = protocol.decode_protocol(raw_message)
    if msg_type == protocol.SEND_DETAILS:
        results = handle_threads(cpu_cores_num, *msg_params)
        if results != "-1":
            message = protocol.encode_protocol(protocol.FOUND, ORIGINAL_HASH)
            protocol.send_message(client_socket, message)
            print(f"Found hash! {results}")
        else:  # didn't find hash
            message = protocol.encode_protocol(protocol.NOT_FOUND, results)
            protocol.send_message(client_socket, message)
            print(f"Didn't found hash, search from {msg_params[1]}-{msg_params[2]}")

    # Close the connection
    client_socket.close()


def handle_threads(num_of_cores, desired_hash, range_start, range_end):
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

    # return results
    return ORIGINAL_HASH


def compute_hash(desired_hash, range_start, range_end):
    global ORIGINAL_HASH
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
        return


if __name__ == "__main__":
    start_client()

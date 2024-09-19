import socket
import threading
import protocol
import logging

# Global constants
HOST = '127.0.0.1'  # Localhost
PORT = 12345  # Port to listen on
HASH_RESULTS = "f899139df5e1059396431415e770c6dd"
HASH_LENGTH = 3

# Client list to store connected clients
clients = []
id_count = 1

desired_range = 999
current_range = 0
cpu_power = 5

# Configure logging
logging.basicConfig(filename='server.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Client:
    def __init__(self, client_id, cpu_cores, client_socket):
        """
        Initializes a new client instance.

        :param client_id: ID of the client.
        :param cpu_cores: Number of CPU cores the client has.
        :param client_socket: The socket object associated with the client.
        """
        self.client_id = client_id
        self.cpu_cores = cpu_cores
        self.client_socket = client_socket


def handle_client(client_socket, client_address):
    """
    Handles a new client connection, receives messages, and processes their hash request.

    :param client_socket: The socket object for the client connection.
    :param client_address: The address of the connected client.
    :return: None
    """
    global id_count
    logging.info(f"New connection from {client_address}")

    try:
        # Receive the start connection message
        raw_message = protocol.receive_message(client_socket)
        msg_type, msg_params = protocol.decode_protocol(raw_message)

        if msg_type == protocol.START_CONNECTION:
            # Client wants to connect, extract the number of cores
            cpu_cores = int(msg_params[0])
            client_id = id_count
            id_count += 1
            logging.info(f"Client with id {client_id} has {cpu_cores} cores.")

            # Create a new client object and add to the list of clients
            client = Client(client_id, cpu_cores, client_socket)
            clients.append(client)
            logging.info(f"Client added: {client.client_id}, Total clients: {len(clients)}")
            send_details_message(client)

            # Wait for results
            raw_message = protocol.receive_message(client_socket)
            msg_type, msg_params = protocol.decode_protocol(raw_message)

            if msg_type == protocol.FOUND:
                logging.info(f"Found the hash! ({msg_params[0]})")
            elif msg_type == protocol.NOT_FOUND:
                logging.info(f"Client {client.client_id} didn't find the hash")

    except ValueError as e:
        logging.error(f"Value error in message parsing: {e}")
    except socket.error as e:
        logging.error(f"Socket error with client {client_address}: {e}")
    finally:
        client_socket.close()


def send_details_message(client):
    """
    Sends the hash range details to the client for processing.
    :param client: The client object to send details to.
    :return: None
    """
    range_start, range_end = get_hash_range(client.cpu_cores)
    message = protocol.encode_protocol(protocol.SEND_DETAILS, HASH_RESULTS, str(range_start), str(range_end))
    protocol.send_message(client.client_socket, message)


def get_hash_range(cores_number):
    """
    Calculates the hash range that a client should process based on its CPU cores.

    :param cores_number: The number of CPU cores the client has.
    :return: Tuple containing the start and end of the hash range.
    """
    global current_range
    capacity = cores_number * cpu_power
    start_range = current_range
    end_range = start_range + capacity

    # update ranges
    current_range = end_range
    return start_range, end_range


def start_server():
    """
    Starts the server, listens for incoming connections, and handles clients in separate threads.

    :return: None
    """
    try:
        # Create a socket object
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the address and port
        server_socket.bind((HOST, PORT))

        # Start listening for incoming connections
        server_socket.listen()
        logging.info(f"Server listening on {HOST}:{PORT}")

        while True:
            try:
                # Accept a new client connection
                client_socket, client_address = server_socket.accept()

                # Handle each client in a separate thread
                client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
                client_thread.start()
            except socket.error as e:
                logging.error(f"Error accepting new client: {e}")
    except socket.error as e:
        logging.critical(f"Failed to start the server: {e}")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()

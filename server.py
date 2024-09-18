import socket
import threading
import protocol

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


class Client:
    def __init__(self, client_id, cpu_cores, client_socket):
        self.client_id = client_id
        self.cpu_cores = cpu_cores
        self.client_socket = client_socket


def handle_client(client_socket, client_address):
    global id_count
    print(f"New connection from {client_address}")

    # Receive the start connection message
    raw_message = protocol.receive_message(client_socket)
    msg_type, msg_params = protocol.decode_protocol(raw_message)

    if msg_type == protocol.START_CONNECTION:
        # Client wants to connect, extract the number of cores
        cpu_cores = int(msg_params[0])
        client_id = id_count
        id_count += 1
        print(f"Client with id {client_id} has {cpu_cores} cores.")

        # Create a new client object and add to the list of clients
        client = Client(client_id, cpu_cores, client_socket)
        clients.append(client)
        print(f"Client added: {client.client_id}, Total clients: {len(clients)}")
        send_details_message(client)

        # wait for results
        raw_message = protocol.receive_message(client_socket)
        msg_type, msg_params = protocol.decode_protocol(raw_message)

        if msg_type == protocol.FOUND:
            print(f"Found the hash! ({msg_params[0]})")
        elif msg_type == protocol.NOT_FOUND:
            print(f"the client {client.client_id} didn't found the hash")

    # Close connection
    client_socket.close()


def send_details_message(client):
    range_start, range_end = get_hash_range(client.cpu_cores)
    message = protocol.encode_protocol(protocol.SEND_DETAILS,
                                       HASH_RESULTS, str(range_start), str(range_end))
    protocol.send_message(client.client_socket, message)


def get_hash_range(cores_number):
    global current_range
    capacity = cores_number * cpu_power
    start_range = current_range
    end_range = start_range + capacity

    # update ranges
    current_range = end_range
    return start_range, end_range


def start_server():
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the address and port
    server_socket.bind((HOST, PORT))

    # Start listening for incoming connections
    server_socket.listen()
    print(f"Server listening on {HOST}:{PORT}")

    while True:
        # Accept a new client connection
        client_socket, client_address = server_socket.accept()

        # Handle each client in a separate thread
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()


if __name__ == "__main__":
    start_server()

import socket
import threading
import protocol
import logging

# Global constants
HOST = '127.0.0.1'  # Localhost
PORT = 12345  # Port to listen on

HASH_RESULTS = "b7a782741f667201b54880c925faec4b"
HASH_LENGTH = 5
CPU_POWER = 500
# Configure logging
logging.basicConfig(filename='server.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Client:
    def __init__(self, client_id, cpu_cores, client_socket):
        """
        :param client_id: ID of the client.
        :param cpu_cores: Number of CPU cores the client has.
        :param client_socket: The socket object associated with the client.
        """
        self.client_id = client_id
        self.cpu_cores = cpu_cores
        self.client_socket = client_socket


class Server:

    def __init__(self, server_socket, cpu_power):
        """
        :param server_socket: the main server socket
        :param cpu_power: the amount of range a client will have assigned per cpu
        """
        self.server_socket = server_socket
        # Hash variables
        self.max_hash = (10 ** HASH_LENGTH) - 1
        self.current_hash = 0
        self.cpu_power = cpu_power
        self.lock = threading.Lock()
        # Client list to store connected clients
        self.clients = []
        self.id_count = 1

    def handle_client(self, client_socket, client_address):
        """
        Handles a new client connection, receives messages, and processes their hash request.
        :param client_socket: The socket object for the client connection.
        :param client_address: The address of the connected client.
        :return: None
        """
        logging.info(f"New connection from {client_address}")

        try:
            # Receive the start connection message
            raw_message = protocol.receive_message(client_socket)
            msg_type, msg_params = protocol.decode_protocol(raw_message)

            if msg_type == protocol.START_CONNECTION:
                # Client wants to connect, extract the number of cores
                cpu_cores = int(msg_params[0])
                with self.lock:
                    client_id = self.id_count
                    self.id_count += 1
                    logging.info(f"Client with id {client_id} has {cpu_cores} cores.")

                    # Create a new client object and add to the list of clients
                    client = Client(client_id, cpu_cores, client_socket)
                    self.clients.append(client)
                logging.info(f"Client added: {client.client_id}, Total clients: {len(self.clients)}")
                self.send_details_message(client)

                # Wait for results
                raw_message = protocol.receive_message(client_socket)
                msg_type, msg_params = protocol.decode_protocol(raw_message)

                if msg_type == protocol.FOUND:
                    logging.info(f"client with id {client.client_id} Found the hash! ({msg_params[0]})")
                    # let all other client's know the work is over
                    message = protocol.encode_protocol(protocol.STOP_WORK)
                    for other_client in self.clients:
                        if other_client != client:
                            protocol.send_message(other_client.client_socket, message)

                elif msg_type == protocol.NOT_FOUND:
                    logging.info(f"Client {client.client_id} didn't find the hash")

        except ValueError as e:
            logging.error(f"Value error in message parsing: {e}")
        except socket.error as e:
            logging.error(f"Socket error with client {client_address}: {e}")
        finally:
            client_socket.close()

    def send_details_message(self, client):
        """
        Sends the hash range details to the client for processing.
        :param client: The client object to send details to.
        :return: None
        """
        range_start, range_end = self.get_hash_range(client.cpu_cores)
        message = protocol.encode_protocol(protocol.SEND_DETAILS, HASH_RESULTS, str(range_start), str(range_end))
        protocol.send_message(client.client_socket, message)

    def get_hash_range(self, cores_number):
        """
        Calculates the hash range that a client should process based on its CPU cores.
        :param cores_number: The number of CPU cores the client has.
        :return: Tuple containing the start and end of the hash range.
        """
        with self.lock:
            # if the whole range is covered, check form 0-0
            if self.current_hash > self.max_hash:
                return 0, 0
            capacity = cores_number * CPU_POWER
            start_range = self.current_hash
            end_range = start_range + capacity
            end_range = self.max_hash if end_range > self.max_hash else end_range

            # update ranges
            self.current_hash = end_range
            return start_range, end_range

    def start_server(self):
        """
        Starts the server, listens for incoming connections, and handles clients in separate threads.
        :return: None
        """
        try:

            # Start listening for incoming connections
            self.server_socket.listen()
            logging.info(f"Server listening on {HOST}:{PORT}")

            while True:
                try:
                    # Accept a new client connection
                    client_socket, client_address = self.server_socket.accept()

                    # Handle each client in a separate thread
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                    client_thread.start()
                except socket.error as e:
                    logging.error(f"Error accepting new client: {e}")
        except socket.error as e:
            logging.critical(f"Failed to start the server: {e}")
        finally:
            self.server_socket.close()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server = Server(server_socket, CPU_POWER)
    server.start_server()


if __name__ == "__main__":
    main()

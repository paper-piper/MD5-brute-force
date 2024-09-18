import socket
import os
import protocol
import hashlib


# Global constants
SERVER_HOST = '127.0.0.1'  # Server address
SERVER_PORT = 12345  # Server port
HASH_LENGTH = 3


def start_client():
   # Create a socket object
   client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

   # Connect to the server
   client_socket.connect((SERVER_HOST, SERVER_PORT))

   # Get the number of CPU cores
   cpu_cores = os.cpu_count()

   # Send the start connection message with the CPU cores as the parameter
   start_message = protocol.encode_protocol(protocol.START_CONNECTION, str(cpu_cores))
   protocol.send_message(client_socket, start_message)

   # get the range and desired hash results
   raw_message = protocol.receive_message(client_socket)
   msg_type, msg_params = protocol.decode_protocol(raw_message)
   if msg_type == protocol.SEND_DETAILS:

       # compute_hash()
       pass
   print(msg_type)
   print(msg_params)
   # Close the connection
   client_socket.close()


def compute_hash(desired_hash, range_start, range_end, hash_length):
   # Iterate over the range from start to end
   for num in range(range_start, range_end + 1):
       # Pad the number according to the hash length (e.g., 5 -> "00005" if length is 5)
       padded_str = str(num).zfill(hash_length)

       # Compute the MD5 hash for the padded string
       hash_obj = hashlib.md5(padded_str.encode())
       hash_guess = hash_obj.hexdigest()

       # Check if the generated hash matches the desired hash
       if hash_guess == desired_hash:
           return num  # Return the number if hash matches

   # If no match was found in the range, return -1
   return -1


if __name__ == "__main__":
   start_client()


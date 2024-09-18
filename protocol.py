import socket


# Message protocol
# <message len>:<message type>:<message parameters>

# Server Messages
SEND_DETAILS = "No problem, you need to find the following hash in the following range"  # <hash results>:<range>

# Client Messages
START_CONNECTION = "Hello, I want to work"  # number of cores
FOUND_STRING = "Found it"  # string

# Message special characters
MESSAGE_DIVIDER = ":"


def encode_protocol(msg_type: str, *msg_params:  str) -> str:
   # Join all the parameters with ":" as the separator
   message = f"{msg_type}:{':'.join(msg_params)}"

   # Calculate the length of the message
   message_len = len(message)

   # Return the encoded protocol string
   return f"{message_len}:{message}"


def decode_protocol(raw_message: str) -> (str, list):
   # Split the raw message into components using ":" as the separator
   components = raw_message.split(":")

   # The first part is the message type
   msg_type = components[0]

   # The rest are message parameters
   msg_params = components[1:]  # Get all parameters after the type

   return msg_type, msg_params


def receive_message(sock):
   # Step 1: Read the message length until encountering ":"
   message_len_str = ""
   while True:
       char = sock.recv(1).decode()  # Read one byte, decode it to a string
       if char == ":":
           break
       message_len_str += char  # Add the character to the length string

   message_len = int(message_len_str)  # Convert the length to an integer

   # Step 2: Read the rest of the message with the specified length
   message = ""
   while len(message) < message_len:
       char = sock.recv(1).decode()  # Read one byte at a time
       message += char  # Add the character to the message

   return message


def send_message(sock, message: str):
   # Convert the message to bytes and send it over the socket
   sock.sendall(message.encode())


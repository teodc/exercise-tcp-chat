import random
import socket
import sys
import time

# Name of the bot using this client
try:
    testbot_username = sys.argv[1]
except IndexError:
    sys.exit("Missing bot name")

# Test messages
messages = [
    b"There was an earthquake yesterday",
    b"Maurice loves sweet potato and cheese",
    b"Do you like sushi?",
    b"I drank too much last night",
    b"I need to buy a new pillow",
    b"The movie AKA is really good",
    b"I can't wait for Diablo IV",
]

while True:
    try:
        # Create a TCP connection to our server
        conn = socket.create_connection(("localhost", 9876))
        conn.settimeout(3)
        print(conn.recv(4096).decode())

        # Send our username
        print(f">> Sending name: {testbot_username}")
        conn.sendall(testbot_username.encode() + b"\n")
        time.sleep(1)
        # Catch reply from the server
        print(conn.recv(4096).decode())

        # While connection is opened ...
        while True:
            # ... Send random predefined messages
            message_to_send = random.choice(messages)
            print(f">> Sending message: {message_to_send.decode()}")
            conn.sendall(message_to_send + b"\n")

            # ... Display received messages
            try:
                received_message = conn.recv(4096)
            except socket.timeout:
                received_message = b""
            print(f">> Received message: {received_message.decode()}")

            # Let the client breath for a few seconds
            time.sleep(5)
    except:
        print("/!\\ Disconnected. Trying to reconnect...")
        time.sleep(5)

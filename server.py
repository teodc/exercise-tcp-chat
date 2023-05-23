from dataclasses import dataclass

import trio


@dataclass
class Client:
    username: str
    send_channel: trio.MemorySendChannel


async def connection(stream: trio.abc.Stream, clients: dict[str, Client]) -> None:
    # print(stream)

    try:
        # Create nursery so we can group tasks & share message data between them
        async with trio.open_nursery() as nursery:
            # Open channels to share data between the nursery's tasks
            send_channel, receive_channel = trio.open_memory_channel(0)

            # Ask for username
            await stream.send_all(b"Welcome! What's your name?\n")

            # Intercept response, extract username & reply to the client
            received_data = b""
            while b"\n" not in received_data:
                received_data += await stream.receive_some()
            username, received_data = received_data.split(b"\n", 1)
            await stream.send_all(b"Glad to have you here " + username + b". Enjoy!\n")

            # Create the Client object & add it to the list of clients
            username_str = username.decode()
            clients[username_str] = Client(username=username_str, send_channel=send_channel)

            try:
                # Spawn nursery's child tasks to send and receive messages
                nursery.start_soon(sender, stream, receive_channel)
                nursery.start_soon(receiver, stream, clients, username, nursery)
            except:
                # Remove client from list
                clients.pop(username_str)
                raise
    except Exception as e:
        # Catch exceptions occurring inside the nursery, so it doesn't escalate and crash the server
        print(f"An error occurred: {e}")


async def sender(stream: trio.abc.Stream, channel: trio.MemoryReceiveChannel) -> None:
    while True:
        # Intercept the channel's received messages & send them to the stream
        message = await channel.receive()
        await stream.send_all(message)


async def receiver(stream: trio.abc.Stream, clients: dict[str, Client], username: bytes, nursery: trio.Nursery) -> None:
    while True:
        # Keep intercepting messages from clients
        received_data = b""
        while b"\n" not in received_data:
            received_data += await stream.receive_some()
        message, received_data = received_data.split(b"\n", 1)

        print(f">> Received [{message}] from [{username}]")

        # Send received messages to all clients via their send channels within a nursery task
        for _, client in clients.items():
            nursery.start_soon(
                send_message,
                client.send_channel,
                username + b": " + message + b"\n",
            )


async def send_message(send_channel: trio.MemorySendChannel, message: bytes) -> None:
    with trio.move_on_after(3) as cancel_scope:
        await send_channel.send(message)
    if cancel_scope.cancelled_caught:
        print(f"Failed sending message [{message}]")


async def startup() -> None:
    print("Server started...")

    # List of connected clients
    clients = {}

    async def connection_handler(stream: trio.abc.Stream) -> None:
        await connection(stream, clients)

    # Listen for incoming TCP connections
    await trio.serve_tcp(connection_handler, 9876)


if __name__ == "__main__":
    trio.run(startup)

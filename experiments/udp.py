import socket

def udp_client(server_ip, server_port, message):
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # Send data
        # print(f'Sending message: {message}')
        # sent = sock.sendto(message.encode(), (server_ip, server_port))

        # Receive response
        print('Waiting for response...')
        data, server = sock.recvfrom(7502)
        print(f'Received response: {data.decode()}')

    finally:
        print('Closing socket')
        sock.close()

if __name__ == "__main__":
    server_ip = '127.0.0.1'  # Replace with the server's IP address
    server_port = 12345      # Replace with the server's port
    message = 'Hello, Server!'

    udp_client(server_ip, server_port, message)
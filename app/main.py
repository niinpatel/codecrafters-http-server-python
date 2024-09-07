import socket


def handle_request(client_socket: socket.socket):
    request = client_socket.recv(1024)

    method = request.decode().split(" ")[0]
    path = request.decode().split(" ")[1]

    if method == "GET" and path == "/":
        client_socket.sendall(b"HTTP/1.1 200 OK\r\n\r\n")
    else:
        client_socket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

    client_socket.close()


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        client_socket, _ = server_socket.accept()
        handle_request(client_socket)


if __name__ == "__main__":
    main()

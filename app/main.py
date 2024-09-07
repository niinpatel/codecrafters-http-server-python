import gzip
import os
import socket
import sys
import threading


def parse_headers(request: str) -> dict:
    headers_strings = request.decode().split("\r\n")[1:-2]
    print(headers_strings)
    headers = {}
    for line in headers_strings:
        if line:
            key, value = line.split(": ", 1)
            headers[key] = value
    return headers


def handle_request(client_socket: socket.socket):
    request = client_socket.recv(1024)

    method = request.decode().split(" ")[0]
    path = request.decode().split(" ")[1]
    headers = parse_headers(request)

    if method == "GET" and path == "/":
        client_socket.sendall(b"HTTP/1.1 200 OK\r\n\r\n")

    elif method == "GET" and path.startswith("/echo"):
        accept_encoding = headers.get("Accept-Encoding", "")
        message = path.split("/echo/")[1].encode()
        if "gzip" in accept_encoding:
            compressed_message = gzip.compress(message)
            client_socket.sendall(
                f"HTTP/1.1 200 OK\r\nContent-Length: {len(compressed_message)}\r\nContent-Encoding: gzip\r\nContent-Type: text/plain\r\n\r\n".encode()
                + compressed_message
            )
        else:
            client_socket.sendall(
                f"HTTP/1.1 200 OK\r\nContent-Length: {len(message)}\r\nContent-Type: text/plain\r\n\r\n{message.decode()}".encode()
            )

    elif method == "GET" and path.startswith("/user-agent"):
        user_agent = headers.get("User-Agent", "")
        client_socket.sendall(
            f"HTTP/1.1 200 OK\r\nContent-Length: {len(user_agent)}\r\nContent-Type: text/plain\r\n\r\n{user_agent}".encode()
        )
    elif method == "GET" and path.startswith("/files/"):
        file_name = path.split("/files/")[1]
        directory = sys.argv[2]
        file_path = os.path.join(directory, file_name)

        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                content = file.read()
                client_socket.sendall(
                    f"HTTP/1.1 200 OK\r\nContent-Length: {len(content)}\r\nContent-Type: application/octet-stream\r\n\r\n{content.decode()}".encode()
                )
        else:
            client_socket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
    elif method == "POST" and path.startswith("/files/"):
        file_name = path.split("/files/")[1]
        directory = sys.argv[2]
        file_path = os.path.join(directory, file_name)
        request_body = request.decode().split("\r\n\r\n")[1]
        with open(file_path, "wb") as file:
            file.write(request_body.encode())
        client_socket.sendall(b"HTTP/1.1 201 Created\r\n\r\n")

    else:
        client_socket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

    client_socket.close()


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        client_socket, _ = server_socket.accept()
        client_handler = threading.Thread(target=handle_request, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    main()

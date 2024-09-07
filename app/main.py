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


def construct_response(status_code: int, body: str, headers: dict) -> str:
    status_messages = {
        200: "OK",
        201: "Created",
        404: "Not Found",
    }

    status_line = f"HTTP/1.1 {status_code} {status_messages[status_code]}\r\n"
    headers_str = "".join([f"{key}: {value}\r\n" for key, value in headers.items()])
    headers_str += f"Content-Length: {len(body.encode())}\r\n"

    return f"{status_line}{headers_str}\r\n{body}".encode()


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
            compressed_message = message  # will do later
            client_socket.sendall(
                construct_response(
                    200,
                    compressed_message.decode(),
                    {"Content-Encoding": "gzip", "Content-Type": "text/plain"},
                )
            )
        else:
            client_socket.sendall(
                construct_response(
                    200,
                    message.decode(),
                    {"Content-Type": "text/plain"},
                )
            )

    elif method == "GET" and path.startswith("/user-agent"):
        user_agent = headers.get("User-Agent", "")
        client_socket.sendall(
            construct_response(
                200,
                user_agent,
                {"Content-Type": "text/plain"},
            )
        )
    elif method == "GET" and path.startswith("/files/"):
        file_name = path.split("/files/")[1]
        directory = sys.argv[2]
        file_path = os.path.join(directory, file_name)

        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                content = file.read()
                client_socket.sendall(
                    construct_response(
                        200,
                        content.decode(),
                        {"Content-Type": "application/octet-stream"},
                    )
                )
        else:
            client_socket.sendall(
                construct_response(
                    404,
                    "File not found",
                    {"Content-Type": "text/plain"},
                )
            )
    elif method == "POST" and path.startswith("/files/"):
        file_name = path.split("/files/")[1]
        directory = sys.argv[2]
        file_path = os.path.join(directory, file_name)
        request_body = request.decode().split("\r\n\r\n")[1]
        with open(file_path, "wb") as file:
            file.write(request_body.encode())
        client_socket.sendall(
            construct_response(
                201,
                "File created",
                {"Content-Type": "text/plain"},
            )
        )

    else:
        client_socket.sendall(
            construct_response(
                404,
                "Not Found",
                {"Content-Type": "text/plain"},
            )
        )

    client_socket.close()


def main():
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        client_socket, _ = server_socket.accept()
        client_handler = threading.Thread(target=handle_request, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    main()

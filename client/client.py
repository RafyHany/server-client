import os
import socket
import sys


class HTTPRequest:
    def __init__(self, server_host):
        self.host = server_host

    def create_get_request(self, path):
        return (f"GET /{path} HTTP/1.1\r\n"
                f"Host: {self.host}\r\n"
                f"Connection: keep-alive\r\n"
                f"\r\n").encode()

    def create_post_request(self, path, data):
        content_length = len(data)
        request_header = (
            f"POST /{path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: keep-alive\r\n"
            f"\r\n"
        )
        return request_header.encode() + data


class SimpleHTTPClient:
    def __init__(self, server_host, server_port=80):
        self.host = server_host
        self.port = server_port
        self.request_builder = HTTPRequest(server_host)

    def get(self, input_file_path, client_socket):
        request = self.request_builder.create_get_request(input_file_path)
        client_socket.sendall(request)
        content_length = 0
        response = client_socket.recv(1024)
        headers, body = response.split(b'\r\n\r\n', 1)
        for line in headers.split(b'\r\n'):
            if b'Content-Length' in line:
                content_length = int(line.split(b': ')[1])
                break
        while len(body) < content_length:
            body += client_socket.recv(1024)
        output_path = os.path.join(os.getcwd(), input_file_path.strip('/'))
        with open(output_path, 'wb') as f:
            f.write(body)
        print(f"File '{output_path}' is saved successfully.")

    def post(self, input_file_path, client_socket):
        if not os.path.isfile(input_file_path):
            print(f"File '{input_file_path}' not found.")
            return
        with open(input_file_path, 'rb') as f:
            file_data = f.read()
            request = self.request_builder.create_post_request(input_file_path, file_data)
            client_socket.sendall(request)
            response = b""
            while True:
                part = client_socket.recv(1024)
                response += part
                if b'\r\n\r\n' in response:
                    break
            response_header = response[:response.find(b'\r\n\r\n') + 4]
            response_body = response[response.find(b'\r\n\r\n') + 4:]
            response_header_str = response_header.decode('utf-8', errors='replace')
            print(f"Server response header:\n{response_header_str}")
            if response_body:
                print(f"Server response body:\n{response_body.decode('utf-8', errors='replace')}")


def execute_commands_from_file(file, http_client):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((http_client.host, http_client.port))
            with open(file, 'r') as file:
                for line in file:
                    command = line.strip()
                    if not command:
                        continue
                    if len(command.split()) < 2:
                        print(f"Invalid command: {command}")
                        continue
                    if command.lower() == "exit":
                        print("Exiting Client")
                        break
                    elif command.startswith("GET "):
                        file_path = command.split(" ", 1)[1]
                        http_client.get(file_path, client_socket)
                    elif command.startswith("POST "):
                        file_path = command.split(" ", 1)[1]
                        http_client.post(file_path, client_socket)
                    else:
                        print(f"Invalid command: {command}")
    except FileNotFoundError:
        print(f"Error: File '{file}' not found.")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python client.py <host> <port> <file_path>")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2])
    commands_file = sys.argv[3]
    client = SimpleHTTPClient(host, port)
    execute_commands_from_file(commands_file, client)

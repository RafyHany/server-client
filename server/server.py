import socket
import sys
import threading
import os


class HTTPResponse:
    @staticmethod
    def build_response(status_code, content=b"", keep_alive=False):
        if status_code == 200:
            header = "HTTP/1.1 200 OK\r\n"
        elif status_code == 404:
            header = "HTTP/1.1 404 Not Found\r\n"
        elif status_code == 500:
            header = "HTTP/1.1 500 Internal Server Error\r\n"
        else:
            header = "HTTP/1.1 400 Bad Request\r\n"

        if keep_alive:
            header += "Connection: keep-alive\r\n"
        else:
            header += "Connection: close\r\n"

        return header.encode() + b"\r\n" + content


class SimpleHTTPServer:
    def __init__(self, host='127.0.0.1', port=8080, timeout=10 , max_connections=5):
        self.host = host
        self.port = port
        self.number_threads = 0
        self.timeout = timeout
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(max_connections)
        print(f"Server started on {self.host}:{self.port}")

    def start(self):
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"Connection from {addr}")
                self.number_threads += 1
                client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_handler.start()
        except KeyboardInterrupt:
            print("Shutting down server...")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket):
        keep_alive = True
        with client_socket:
            while keep_alive:
                try:
                    request = client_socket.recv(1024)
                    if not request:
                        self.number_threads -= 1
                        break
                    client_socket.settimeout(self.timeout / self.number_threads)
                    print(f"Received request:\n{request}")
                    request_lines = request.split(b'\r\n')
                    request_line = request_lines[0].decode('utf-8')
                    method, path, _ = request_line.split()

                    if method == "GET":
                        keep_alive = self.handle_get(client_socket, path, request)
                    elif method == "POST":
                        keep_alive = self.handle_post(client_socket, path, request)
                    else:
                        response = HTTPResponse.build_response(500, b"Unsupported method", keep_alive)
                        client_socket.sendall(response)

                except socket.timeout:
                    print("Connection timed out.")
                    self.number_threads -= 1
                    keep_alive = False
                except Exception as e:
                    print(f"Error handling request: {e}")
                    response = HTTPResponse.build_response(500, b"Internal Server Error", keep_alive)
                    client_socket.sendall(response)
                    self.number_threads -= 1
                    keep_alive = False

    def handle_get(self, client_socket, path, request):
        file_path = path.lstrip('/')
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                response = HTTPResponse.build_response(200, data, keep_alive=True)
            except Exception as e:
                print(f"Error reading file {file_path}: {e}")
                response = HTTPResponse.build_response(500, b"Internal Server Error", keep_alive=True)
        else:
            response = HTTPResponse.build_response(404, b"File not found", keep_alive=True)

        client_socket.sendall(response)
        if b'Connection: keep-alive' in request:
            return True
        else:
            return False

    def handle_post(self, client_socket, path, request):
        headers, body = request.split(b'\r\n\r\n', 1)
        content_length = int([line for line in headers.split(b'\r\n') if b'Content-Length' in line][0].split(b': ')[1])
        while len(body) < content_length:
            body += client_socket.recv(1024)
        file_path = path.lstrip('/')
        try:
            with open(file_path, 'wb') as f:  # Open as binary
                f.write(body)
            response = HTTPResponse.build_response(200, b"File uploaded successfully", keep_alive=True)
        except Exception as e:
            print(f"Error saving file: {e}")
            response = HTTPResponse.build_response(500, b"Failed to save file", keep_alive=True)
        client_socket.sendall(response)
        if b'Connection: keep-alive' in request:
            return True
        else:
            return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("It should be python server.py <port>")
        sys.exit(1)
    port = int(sys.argv[1])

    server = SimpleHTTPServer(port=port)
    server.start()

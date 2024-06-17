from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random
import sys
import requests


class ResponseManager:
    def __init__(self, responses=None):
        self.responses = responses if responses is not None else []
        self.index = 0

    def set_responses(self, new_responses):
        self.responses = new_responses
        self.index = 0

    def get_next_response(self):
        if self.index < len(self.responses):
            response = self.responses[self.index]
            self.index += 1
            return response
        else:
            raise IndexError("No more responses available.")


class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/"):
            try:
                response_data = self.server.response_manager.get_next_response()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(
                    response_data.encode("utf-8")
                    if isinstance(response_data, str)
                    else json.dumps(response_data).encode("utf-8")
                )
            except IndexError as e:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Only GET requests are supported")

    def do_POST(self):
        if self.path == "/--internal/exit":
            sys.exit(0)  # To exit the sever without killing the rest of the program
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Only GET requests are supported")

    def log_message(self, format, *args):
        # Override to prevent standard logging to sys.stderr
        pass


def spawn_server(responses, port):
    server_address = ("", port)
    httpd = HTTPServer(server_address, MyHandler)
    httpd.response_manager = responses  # Set the response manager
    httpd.serve_forever()


def exit_server(port):
    try:
        requests.get(f"http://localhost:{port}/--internal/exit")
    except Exception:
        pass


# Use a random port every time, so that we don't have to wait for a few
# seconds after killing the server before starting it again on the same port
# This requires that the port be free on localhost.
# If you are getting errors then you can pass min and max values to use
# different ports, e.g. gen_random_ports(30000, 40000)
def gen_random_port(small=57000, large=58000):
    return random.randrange(small, large)

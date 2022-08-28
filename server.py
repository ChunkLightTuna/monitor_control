#!/usr/bin/env python3

import json
import logging
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


def msg_fun(_):
    pass


class Handler(SimpleHTTPRequestHandler):
    def version_string(self):
        return "16x2"

    def do_GET(self):
        """Serve a GET request."""
        if self.path != "/favicon.ico":
            self.path = "index.html"

        f = self.send_head()
        if f:
            try:
                self.copyfile(f, self.wfile)
            finally:
                f.close()

    def do_POST(self):
        """Serve a POST request."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            line_one, line_two = json.loads(post_data.decode('utf-8'))
            if not line_one and not line_two:
            elif len(line_one) > 16 or len(line_two) > 16:
                self.send_error(HTTPStatus.BAD_REQUEST, "Max 16 char per line")
            else:
                msg_fun(f"{line_one}\n{line_two}")
                self.send_response(HTTPStatus.OK)
                self.end_headers()

        except Exception as e:
            if 'not enough values to unpack' in repr(e):
                self.send_error(HTTPStatus.BAD_REQUEST, "Ya gottta give me something")
            else:
                logging.error(repr(e))
                self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Uhhhh")


def run(msg_f):
    server_address = ('', 1602)

    if callable(msg_f):
        logging.debug(f"msg_f is <{str(msg_f)}>")
        global msg_fun
        msg_fun = msg_f
    else:
        logging.error("msg_f not callable!")

    httpd = ThreadingHTTPServer(server_address, Handler)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    run(lambda s: logging.debug(f"<<{s}>>"))

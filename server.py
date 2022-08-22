#!/usr/bin/env python3

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import logging
import json
import requests

lol_global = lambda s: print(f"DEFAULT LOL GLOBAL: {s}")
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        logging.info(self.path)
        if self.path == "/favicon.ico":
            logging.info("FAVICONNN")
            return super(Handler,self).do_GET()

        if self.path not in ["","/"] :
            self.send_response(404)
            return
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("""
<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="UTF-8">
  <title>16x2</title>
  <style>
    form {
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction:column;
      margin:4ch;
    }
    input {
      width: 16ch;
    }
    #submit {
      width:17ch;
      margin:1ch;
    }
  </style>
</head>
<body>
  <form id="form" autocomplete="off">
    <input type="text" id="line_one" maxlength="16" placeholder="Two Lines">
    <input type="text" id="line_two" maxlength="16" placeholder="16 Chars Each">
    <input type="submit" id="submit" value="Send">
  </form>
  <script>
  document.getElementById('form').onsubmit = function(event) {
        let line_one = document.getElementById('line_one').value
    let line_two = document.getElementById('line_two').value
    fetch("/", {method: "POST", headers: {'Content-Type': 'application/json'}, body: JSON.stringify([line_one, line_two])});
        return false;
  }
  </script>
</body>
</html>""".encode('utf-8'))
        logging.info("recieved get")

    def do_POST(self):
        logging.info("attempting post?")
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself

        try:
            logging.info(f"${post_data.decode('utf-8')} POSTed to ${self.path}")

            line_one, line_two = json.loads(post_data.decode('utf-8'))
            lol_global(f"${line_one}\n${line_two}")
            self.send_response(200)
        except Exception as e:
            logging.error(repr(e))
            self.send_response(400)

def run(msg_fun):
    #server_address = ('https://16x2.oeleri.ch', 1602)
    server_address = ('', 1602)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    #lol_global=msg_fun
    httpd = ThreadingHTTPServer(server_address, Handler)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    run(lambda s: print(f"<<{s}>>"))

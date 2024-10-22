#!/bin/python

import datetime, zoneinfo, http.server, socket

# this runs on a server with python >= 3.9 and complete tzdata
# not on the badge (since micropython doesn't ship with any useful
# timezone implementation, let alone a complete tzdata)

class HTTPServerV6(http.server.HTTPServer):
  address_family = socket.AF_INET6

class HTTPHandler(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
    now = datetime.datetime.now().astimezone(zoneinfo.ZoneInfo('Europe/Amsterdam'))
    timestamp = now.timestamp() + now.utcoffset().seconds - 946684800

    body = f'{timestamp:.0f}\n'.encode()

    self.send_response(200)
    self.send_header('Content-type', 'text/plain')
    self.send_header('Content-length', len(body))
    self.end_headers()

    self.wfile.write(body)

httpd = HTTPServerV6(('::1', 12380), HTTPHandler)
httpd.serve_forever()

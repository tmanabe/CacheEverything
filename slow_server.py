#!/usr/bin/env python
# coding: utf-8

from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from socketserver import ThreadingMixIn
import sys
from time import sleep


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass


class SlowServer(BaseHTTPRequestHandler):

    @classmethod
    def run(cls, addr, port):
        cls.server = ThreadedHTTPServer((addr, port), cls)
        cls.server.serve_forever()

    def do_GET(self):
        sleep(0.1)
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'test')  # Dummy
        return


if __name__ == '__main__':
    SlowServer.run(addr=sys.argv[1], port=int(sys.argv[2]))

#!/usr/bin/env python
# coding: utf-8

import asyncio
import io
import nghttp2
from redis import Redis
import ssl

# See also: https://nghttp2.org/documentation/python-apiref.html


class CacheEverything(nghttp2.BaseRequestHandler):

    class ResponseBody(object):
        def __init__(self, handler):
            self.handler = handler
            self.handler.eof = False
            self.handler.buf = io.BytesIO()

        def generate(self, n):
            buf = self.handler.buf
            data = buf.read1(n)
            if not data and not self.handler.eof:
                return None, nghttp2.DATA_DEFERRED
            if self.handler.eof:
                return data, nghttp2.DATA_EOF
            return data, nghttp2.DATA_OK

    @classmethod
    def under(cls, host):
        cls.upstream = host
        return cls

    @classmethod
    def to(cls, tuple):
        cls.redis = Redis(host=tuple[0], port=tuple[1], db=tuple[2])
        cls.redis.flushall()
        return cls

    @asyncio.coroutine
    def get_contents(self):
        if hasattr(self, 'redis') and self.redis.exists(self.path):
            print('Hit: %s' % self.path)
            self.buf.write(self.redis.get(self.path))
        else:
            if hasattr(self, 'redis'):
                print('Unhit: %s' % self.path)
            connect = asyncio.open_connection(*self.upstream, ssl=False)
            reader, writer = yield from connect
            req = 'GET %s HTTP/1.0\r\n\r\n' % self.path.decode('utf-8')
            writer.write(req.encode('utf-8'))
            # skip response header fields
            while True:
                line = yield from reader.readline()
                line = line.rstrip()
                if not line:
                    break
            # read body
            l = []
            while True:
                b = yield from reader.read(4096)
                if not b:
                    break
                l.append(b)
            b = b''.join(l)
            self.buf.write(b)
            if hasattr(self, 'redis'):
                print('Write: %s' % self.path)
                self.redis.set(self.path, b)
            writer.close()
        self.buf.seek(0)
        self.eof = True
        self.resume()

    def on_headers(self):
        print(self.client_address, self.host, dict(self.headers))
        body = self.ResponseBody(self)
        asyncio.async(self.get_contents())
        self.send_response(status=200, body=body.generate)


if __name__ == '__main__':
    CERT, KEY = './cert.pem', './privkey.pem'
    ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ctx.options = ssl.OP_ALL | ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3
    ctx.load_cert_chain(CERT, KEY)

    THAT_HOST = ('192.168.10.102', 8080)
    THIS_REDIS = ('127.0.0.1', 6379, 0)
    THIS_HOST = ('192.168.10.112', 8443)
    CacheEverything.under(THAT_HOST).to(THIS_REDIS)

    # give None to ssl to make the server non-SSL/TLS
    server = nghttp2.HTTP2Server(THIS_HOST, CacheEverything, ssl=ctx)
    server.serve_forever()

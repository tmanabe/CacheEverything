# CacheEverything
caches everything and serves over HTTP/2.

## Requirements
- redis
```
$ sudo apt-get install redis-server
$ pip install redis
```
- nghttp2
```
$ sudo apt-get install nghttp2
$ python ./setup.py install
```
- A pair of a key and a cert
```
$ openssl genrsa > privkey.pem
$ openssl req -new -x509 -key privkey.pem -out cert.pem -days 365 -nodes
```

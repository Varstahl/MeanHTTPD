# MeanHTTPD
MeanHTTPD is a very lean and mean httpd server, written in Python (and tested on both 2.7 and 3). Its main purpose is to fulfil the specific job of acting as the receiving end of a `curl` file POST, and it is built around it. It features basic resilience against transfer hangs, malicious header forgeries and (very basic) scans.

This code can act as a basis for further development and easily provide additional functions. It can support all commands (including custom ones) with the `do_METHOD` functions as described in the [BaseHTTPRequestHandler documentation](https://docs.python.org/2/library/basehttpserver.html#BaseHTTPServer.BaseHTTPRequestHandler).

Once the server is running you can send files to it through:

> curl -X **METHOD** -F "file=@**FILENAME**;type=**MIMETYPE**" **HOST**:**PORT**

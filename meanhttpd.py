#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function                                   # Python2 print compatibility
from multiprocessing import Process, Queue                              # (Killable) Process (instead of Thread), to avoid I/O locks
from time import clock                                                  # Timeout calculation
from re import split
from socket import error as socket_error                                # Detect port being already in use
try:
    from Queue import Empty                                             # Python2 Empty exception definition
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer       # Python2 HTTP Server
except ImportError:
    from queue import Empty                                             # Python3 Empty exception definition
    from http.server import BaseHTTPRequestHandler, HTTPServer          # Python3 HTTP Server

class RH(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        self.server_version = 'nginx'                                   # Fake server version header
        self.sys_version = ''                                           # Hide used python version
        BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    # Quick error responder
    def _abort(self, bForbidden = True, process = None):
        self.send_response(403 if bForbidden else 408)
        self.end_headers()

    # Set the headers for a valid request response
    def _set_headers(self, mime = 'text/plain'):
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.end_headers()

    # Killable reading queue
    def _enqueue(self, data, queue):
        for line in iter(data.readline, b''):
            queue.put(line)
        data.close()

    # Accepts a file upload in a multipart/form-data, and sends back the parsed data
    def do_POST(self):
        # Convert (valid) headers to string key pairs, discard the rest
        headers = {}
        self.headers = str(self.headers)
        for header in self.headers.split('\r\n' if self.headers.endswith('\r\n') else '\n'):
            if (0 < len(header.strip())):
                try:
                    key, val = split(':[ \t]*', header)
                    headers[key.lower()] = val.lower()
                except:
                    pass

        # Check if content-length and content-type are present and valid, if not return an (arbitrary) forbidden
        if (not 'content-length' in headers) or (not 'content-type' in headers):
            self._abort()
            return
        try:
            # Save boundary as binary data for later content parsing, and content length to avoid input hangs
            self.boundary = str.encode(split('; *boundary=', headers['content-type'])[1])
            self.clen = int(headers['content-length'])
        except (IndexError or ValueError):
            self._abort()
            return

        # Start the reading thread in advance
        q = Queue()
        t = Process(target=self._enqueue, args=(self.rfile, q))
        t.start()

        # Prepare to receive data and to time out if necessary
        start = clock()
        elapsed = 0
        timeout = 3.0
        indata = b''
        while ( (timeout > elapsed) and (self.clen != len(indata)) ):
            elapsed = clock() - start
            try: indata += q.get_nowait()
            except Empty:
                pass

        # Return a 408 if timed out, and stop the hanged reader
        if (timeout <= elapsed):
            print(len(indata))
            self._abort(False)
            t.terminate()
            return

        # Boundary validation and removal, also check if there's any actual content
        if (not (indata.startswith(b'--' + self.boundary + b'\r\n') and indata.endswith(b'\r\n--' + self.boundary + b'--\r\n'))):
            self._abort()
            return
        indata = indata[len(self.boundary)+4 : -len(self.boundary)-8]
        if (0 == len(indata)):
            self._abort()
            return

        # Do actual stuff with the content…

        # All good
        self._set_headers()
        self.wfile.write(indata)

# Bind a local port and start listening
def run(port, server_class=HTTPServer, handler_class=RH):
    from sys import exc_info                                            # General exception handling

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print( 'Starting httpd…' )

    try: httpd.serve_forever()
    except KeyboardInterrupt: print( '\nRequested termination: quitting…' )
    except: print( 'Exception: ', exc_info()[0] )

if __name__ == "__main__":
    from sys import argv

    # Usage: meanhttpd.py [portNumber]
    # Port defaults to 80
    try:
        portNo = int(argv[1])
    except (ValueError, IndexError):
        portNo = 80

    try:
        run(port=portNo)
    except socket_error as e:
        print( 'Unable to bind to port ' + str(portNo) + ': ' + str(e) )
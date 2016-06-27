# Copyright 2013, Google Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following disclaimer
# in the documentation and/or other materials provided with the
# distribution.
#     * Neither the name of Google Inc. nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# pylint: disable=protected-access,missing-docstring,too-few-public-methods,invalid-name,too-many-public-methods
from __future__ import absolute_import

import socket
import threading
import unittest

import httpplus

_RESPONSE = b"""HTTP/1.1 200 OK
Server: wat
Content-Length: 2

hi""".replace(b"\n", b"\r\n")


class SlowCloseServer(object):
    def __init__(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 0))
        s.listen(1)
        unused_addr, self.port = s.getsockname()
        self._socket = s

    def loop(self):
        reqdata = b''
        while b'/quit' not in reqdata:
            con, unused_addr = self._socket.accept()
            reqdata = b''
            while b'\r\n\r\n' not in reqdata:
                reqdata += con.recv(1)
            con.send(_RESPONSE)
            if b'/quit' in reqdata:
                break
            reqdata2 = b''
            while b'\r\n\r\n' not in reqdata2:
                reqdata2 += con.recv(1)
            con.close()


class SlowCloseTest(unittest.TestCase):
    def setUp(self):
        self.server = SlowCloseServer()
        t = threading.Thread(target=self.server.loop)
        t.daemon = True
        t.start()

    def test_request_response_request_close(self):
        # The timeout in this client is 15 seconds. In practice, this
        # test should complete in well under a tenth of a second, so
        # timeouts should indicate a bug in the test code.
        con = httpplus.HTTPConnection(
            'localhost:%d' % self.server.port, timeout=15)
        # Verify we can send a bunch of responses and they all work
        # with the same client.
        con.request('GET', '/')
        resp = con.getresponse()
        self.assertEqual(resp.read(), b"hi")
        con.request('GET', '/ohai')
        resp = con.getresponse()
        self.assertEqual(resp.read(), b"hi")
        con.request('GET', '/wat')
        resp = con.getresponse()
        self.assertEqual(resp.read(), b"hi")
        con.request('GET', '/quit')
        resp = con.getresponse()
        self.assertEqual(resp.read(), b"hi")

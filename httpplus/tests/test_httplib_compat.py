"""Tests to verify API compatibility with httplib."""
from __future__ import absolute_import

import socket
import sys
import threading
import unittest

from wsgiref import simple_server

import httpplus
httplib = httpplus.httplib

def _application(environ, start_response):
    start_response('200 OK', [('OneLine', 'This header has one line.'),
                              # Note: this header looks funny because
                              # SimpleHTTPServer has a bug that
                              # prevents it from correctly writing out
                              # multi-line headers, but the nature of
                              # the bug means we can pre-insert the
                              # \r\n and the leading tab on the second
                              # line and the multi-line header will
                              # work out.
                              ('TwoLines', 'This header\r\n\thas two lines.'),
                              ('TwoLines2', 'Also\r\n  has two lines.'),
                          ])
    return [b'some response bytes']


def _skip_unstable_headers(headers):
    for header, value in headers:
        # At some point between Python 2.7 and 3.5 httplib (aka
        # http.client) stopped lowercasing all headers. Awesome.
        if header.lower() in ('date', 'server'):
            continue
        yield header, value


class TestHttplib(unittest.TestCase):

    mod = httplib

    @classmethod
    def setUpClass(cls):
        cls._server = simple_server.make_server('localhost', 0, _application)
        cls._port = cls._server.socket.getsockname()[1]
        t = threading.Thread(target=cls._server.serve_forever)
        t.daemon = True
        t.start()

    @classmethod
    def tearDownClass(cls):
        cls._server.shutdown()

    def testApiCompatibility(self):
        c = self.mod.HTTPConnection('localhost:%d' % self._port)
        c.request('GET', '/')
        r = c.getresponse()
        self.assertEqual('This header has one line.', r.getheader('OneLine'))
        self.assertEqual(None, r.getheader('This Header Does Not Exist'))
        if sys.version_info < (3, 0):
            expect = [
                ('content-length', '19'),
                ('oneline', 'This header has one line.'),
                ('twolines', 'This header\n has two lines.'),
                ('twolines2', 'Also\n has two lines.'),
            ]
        else:
            # Python 3 dramatically changes httplib's behavior for
            # header handling.
            expect = [
                ('Content-Length', '19'),
                ('OneLine', 'This header has one line.'),
                ('TwoLines', 'This header\r\n\thas two lines.'),
                ('TwoLines2', 'Also\r\n  has two lines.'),
            ]
        self.assertEqual(expect,
                         sorted(_skip_unstable_headers(r.getheaders())))
        self.assertEqual(b'some', r.read(4))
        self.assertEqual(b' response bytes', r.read())


class TestHttpplus(TestHttplib):
    mod = httpplus

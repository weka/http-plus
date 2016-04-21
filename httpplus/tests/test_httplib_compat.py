"""Tests to verify API compatibility with httplib."""

import httplib
import socket
import threading
import unittest
from wsgiref import simple_server

import httpplus


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
    return ['some response bytes']


def _skip_unstable_headers(headers):
    for header, value in headers:
        if header in ('date', 'server'):
            continue
        yield header, value


class TestHttplib(unittest.TestCase):

    mod = httplib

    @classmethod
    def setUpClass(cls):
        cls._server = simple_server.make_server('localhost', 0, _application)
        cls._port = cls._server.socket.getsockname()[1]
        t = threading.Thread(target=cls._server.serve_forever)
        t.start()

    @classmethod
    def tearDownClass(cls):
        cls._server.shutdown()

    def testApiCompatibility(self):
        c = self.mod.HTTPConnection('localhost:%d' % self._port)
        c.request('GET', '/')
        r = c.getresponse()
        self.assertEqual('This header has one line.', r.getheader('OneLine'))
        self.assertIsNone(r.getheader('This Header Does Not Exist'))
        expect = [
            ('content-length', '19'),
            ('oneline', 'This header has one line.'),
            ('twolines', 'This header\n has two lines.'),
            ('twolines2', 'Also\n has two lines.'),
        ]
        self.assertEqual(expect,
                         sorted(_skip_unstable_headers(r.getheaders())))
        self.assertEqual('some', r.read(4))
        self.assertEqual(' response bytes', r.read())


class TestHttpplus(TestHttplib):
    mod = httpplus

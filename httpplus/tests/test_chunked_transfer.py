# Copyright 2010, Google Inc.
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
from __future__ import absolute_import, division

import unittest

import io

import httpplus

# relative import to ease embedding the library
from . import util

def tricklebytes(b):
    return [c.encode('ascii') for c in b.decode('ascii')]

def chunkedblock(x, eol=b'\r\n'):
    r"""Make a chunked transfer-encoding block.

    >>> chunkedblock(b'hi')
    b'2\r\nhi\r\n'
    >>> chunkedblock(b'hi' * 10)
    b'14\r\nhihihihihihihihihihi\r\n'
    >>> chunkedblock(b'hi', eol=b'\n')
    b'2\nhi\n'
    """
    return b''.join((hex(len(x))[2:].encode('ascii'), eol, x, eol))


class ChunkedTransferTest(util.HttpTestBase, unittest.TestCase):
    def testChunkedUpload(self):
        con = httpplus.HTTPConnection('1.2.3.4:80')
        con._connect({})
        sock = con.sock
        sock.read_wait_sentinel = b'0\r\n\r\n'
        sock.data = [b'HTTP/1.1 200 OK\r\n',
                     b'Server: BogusServer 1.0\r\n',
                     b'Content-Length: 6',
                     b'\r\n\r\n',
                     b"Thanks"]

        zz = b'zz\n'
        con.request('POST', '/', body=io.BytesIO(
            (zz * (0x8010 // 3)) + b'end-of-body'))
        expected_req = (b'POST / HTTP/1.1\r\n'
                        b'Host: 1.2.3.4\r\n'
                        b'accept-encoding: identity\r\n'
                        b'transfer-encoding: chunked\r\n'
                        b'\r\n')
        expected_req += chunkedblock(b'zz\n' * (0x8000 // 3) + b'zz')
        expected_req += chunkedblock(
            b'\n' + b'zz\n' * ((0x1b - len('end-of-body')) // 3) + b'end-of-body')
        expected_req += b'0\r\n\r\n'
        self.assertEqual((b'1.2.3.4', 80), sock.sa)
        self.assertStringEqual(expected_req, sock.sent)
        self.assertEqual(b"Thanks", con.getresponse().read())
        self.assertEqual(sock.closed, False)

    def testChunkedDownload(self):
        con = httpplus.HTTPConnection('1.2.3.4:80')
        con._connect({})
        sock = con.sock
        sock.data = [b'HTTP/1.1 200 OK\r\n',
                     b'Server: BogusServer 1.0\r\n',
                     b'transfer-encoding: chunked',
                     b'\r\n\r\n',
                     chunkedblock(b'hi '),
                     ] + tricklebytes(chunkedblock(b'there')) + [
                     chunkedblock(b''),
                     ]
        con.request('GET', '/')
        self.assertStringEqual(b'hi there', con.getresponse().read())

    def testChunkedDownloadOddReadBoundaries(self):
        con = httpplus.HTTPConnection('1.2.3.4:80')
        con._connect({})
        sock = con.sock
        sock.data = [b'HTTP/1.1 200 OK\r\n',
                     b'Server: BogusServer 1.0\r\n',
                     b'transfer-encoding: chunked',
                     b'\r\n\r\n',
                     chunkedblock(b'hi '),
                     ] + tricklebytes(chunkedblock(b'there')) + [
                     chunkedblock(b''),
                     ]
        con.request('GET', '/')
        resp = con.getresponse()
        for amt, expect in [(1, b'h'), (5, b'i the'), (100, b're')]:
            self.assertEqual(expect, resp.read(amt))

    def testChunkedDownloadBadEOL(self):
        con = httpplus.HTTPConnection('1.2.3.4:80')
        con._connect({})
        sock = con.sock
        sock.data = [b'HTTP/1.1 200 OK\n',
                     b'Server: BogusServer 1.0\n',
                     b'transfer-encoding: chunked',
                     b'\n\n',
                     chunkedblock(b'hi ', eol=b'\n'),
                     chunkedblock(b'there', eol=b'\n'),
                     chunkedblock(b'', eol=b'\n'),
                     ]
        con.request('GET', '/')
        self.assertStringEqual(b'hi there', con.getresponse().read())

    def testChunkedDownloadPartialChunkBadEOL(self):
        con = httpplus.HTTPConnection('1.2.3.4:80')
        con._connect({})
        sock = con.sock
        sock.data = [b'HTTP/1.1 200 OK\n',
                     b'Server: BogusServer 1.0\n',
                     b'transfer-encoding: chunked',
                     b'\n\n',
                     chunkedblock(b'hi ', eol=b'\n'),
                     ] + tricklebytes(chunkedblock(
                         b'there\n' * 5, eol=b'\n')) + [
                             chunkedblock(b'', eol=b'\n')]
        con.request('GET', '/')
        self.assertStringEqual(b'hi there\nthere\nthere\nthere\nthere\n',
                               con.getresponse().read())

    def testChunkedDownloadPartialChunk(self):
        con = httpplus.HTTPConnection('1.2.3.4:80')
        con._connect({})
        sock = con.sock
        sock.data = [b'HTTP/1.1 200 OK\r\n',
                     b'Server: BogusServer 1.0\r\n',
                     b'transfer-encoding: chunked',
                     b'\r\n\r\n',
                     chunkedblock(b'hi '),
                     ] + tricklebytes(chunkedblock(b'there\n' * 5)) + [
                         chunkedblock(b'')]
        con.request('GET', '/')
        self.assertStringEqual(b'hi there\nthere\nthere\nthere\nthere\n',
                               con.getresponse().read())

    def testChunkedDownloadEarlyHangup(self):
        con = httpplus.HTTPConnection('1.2.3.4:80')
        con._connect({})
        sock = con.sock
        broken = chunkedblock(b'hi'*20)[:-1]
        sock.data = [b'HTTP/1.1 200 OK\r\n',
                     b'Server: BogusServer 1.0\r\n',
                     b'transfer-encoding: chunked',
                     b'\r\n\r\n',
                     broken,
                     ]
        sock.close_on_empty = True
        con.request('GET', '/')
        resp = con.getresponse()
        self.assertRaises(httpplus.HTTPRemoteClosedError, resp.read)

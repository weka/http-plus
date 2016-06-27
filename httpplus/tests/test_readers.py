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
from __future__ import absolute_import, print_function

import unittest

from httpplus import _readers

try:
    xrange
except NameError:
    # Forward for Python 3
    xrange = range

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

corpus = b'foo\r\nbar\r\nbaz\r\n'


class ChunkedReaderTest(unittest.TestCase):
    def test_many_block_boundaries(self):
        for step in xrange(1, len(corpus)):
            data = b''.join(chunkedblock(corpus[start:start+step]) for
                            start in xrange(0, len(corpus), step))
            for istep in xrange(1, len(data)):
                rdr = _readers.ChunkedReader(b'\r\n')
                print('step', step, 'load', istep)
                for start in xrange(0, len(data), istep):
                    rdr._load(data[start:start+istep])
                rdr._load(chunkedblock(b''))
                self.assertEqual(corpus, rdr.read(len(corpus) + 1))

    def test_small_chunk_blocks_large_wire_blocks(self):
        data = b''.join(
            [chunkedblock(c.encode('ascii')) for c in corpus.decode('ascii')]
            + [chunkedblock(b'')])
        rdr = _readers.ChunkedReader(b'\r\n')
        for start in xrange(0, len(data), 4):
            d = data[start:start + 4]
            if d:
                rdr._load(d)
        self.assertEqual(corpus, rdr.read(len(corpus)+100))

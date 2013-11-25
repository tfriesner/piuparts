# -*- coding: utf-8 -*-

# Copyright 2005 Lars Wirzenius (liw@iki.fi)
# Copyright © 2013 Andreas Beckmann (anbe@debian.org)
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA


import bz2
import zlib
import urllib2


import conf
import dependencyparser
import packagesdb


class DecompressedStream():
    def __init__(self, fileobj, decompressor=None):
        self._input = fileobj
        self._decompressor = decompressor
        self._buffer = ""
        self._line_buffer = []
        self._i = 0
        self._end = 0

    def _refill(self):
        if self._input is None:
            return False
        while True:
            # repeat until decompressor yields some output or input is exhausted
            chunk = self._input.read(4096)
            if not chunk:
                self.close()
                return False
            if self._decompressor:
                chunk = self._decompressor.decompress(chunk)
            self._buffer = self._buffer + chunk
            if chunk:
                return True

    def readline(self):
        while not self._i < self._end:
            self._i = self._end = 0
            self._line_buffer = None
            empty = not self._refill()
            if not self._buffer:
                break
            self._line_buffer = self._buffer.splitlines(True)
            self._end = len(self._line_buffer)
            self._buffer = ""
            if not self._line_buffer[-1].endswith("\n") and not empty:
                self._buffer = self._line_buffer[-1]
                self._end = self._end - 1
        if self._i < self._end:
            self._i = self._i + 1
            return self._line_buffer[self._i - 1]
        return ""

    def close(self):
        if self._input:
            self._input.close()
        self._input = self._decompressor = None


def open_packages_url(url):
    """Open a Packages.bz2 file pointed to by a URL"""
    socket = None
    for ext in ['.bz2', '.gz']:
        try:
            socket = urllib2.urlopen(url + ext)
        except urllib2.HTTPError as httperror:
            pass
        else:
            break
    if socket is None:
        raise httperror
    url = socket.geturl()
    if ext == '.bz2':
        decompressor = bz2.BZ2Decompressor()
        decompressed = DecompressedStream(socket, decompressor)
    elif ext == '.gz':
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        decompressed = DecompressedStream(socket, decompressor)
    else:
        raise ext
    return (url, decompressed)

# vi:set et ts=4 sw=4 :

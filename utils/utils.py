# MIT License

# Copyright (c) [2024] [Gurnoor Singh]

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Module for extra functionality"""
from collections import namedtuple

import sqlite3
import typing

import requests


DummyRow = namedtuple(
    'DummyRow', ('access_token', 'refresh_token', 'client_info'))


def convert_to_human(i: int):
    """Converts given long numbers into human readable"""

    if i >= 1_000_000_000_000_000:
        temp = i / 1_000_000_000_000_000
        return f"{temp:.2f}Q"

    if i >= 1_000_000_000_000:
        temp = i / 1_000_000_000_000
        return f"{temp:.2f}T"

    if i >= 1_000_000_000:
        temp = i / 1_000_000_000
        return f"{temp:.2f}B"

    if i >= 1_000_000:
        temp = i / 1_000_000
        return f"{temp:.2f}M"

    if i >= 1000:
        temp = i / 1000
        return f"{temp:.2f}K"

    return i


class ProxyManager:
    """Class to manage proxies"""

    def __init__(self, fp) -> None:
        self.proxies = []
        self.last = -1

        self.setup(fp)

    def setup(self, fp):
        """Setups the proxy list"""
        proxylist = fp.read().splitlines()

        for x in proxylist:
            t = x.split(':')
            self.proxies.append(f"http://{t[2]}:{t[3]}@{t[0]}:{t[1]}")

    def get(self, with_dict=True):
        """Function to get a proxy"""

        self.last = index = self.last + \
            1 if self.last < (len(self.proxies) - 1) else 0

        proxy = self.proxies[index]

        if with_dict:
            return {"https": proxy, "http": proxy}

        return proxy

    def __len__(self):
        return len(self.proxies)

    def at(self, index: int, with_dict=True):
        """Get proxy at given index"""
        if index >= len(self.proxies) or index < 0:
            raise IndexError('list index out of range')

        proxy = self.proxies[index]

        if with_dict:
            return {"https": proxy, "http": proxy}

        return proxy

    def refetch(self):
        """Refetch all the proxies"""
        r = requests.get(
            "https://proxy.webshare.io/api/v2/proxy/list/download/ohtkcmhmbakegrydtnlrhjgawekqskazxpuvmyoj/-/any/username/direct/-/", timeout=10)

        with open('proxylist.txt', 'w', encoding='utf-8') as fp:
            fp.write(r.text)

        with open('proxylist.txt', 'r', encoding='utf-8') as fp:
            self.setup(fp)


class Row(sqlite3.Row):
    """Overriden row class to make row data printable
    Not performant."""

    def __repr__(self) -> str:
        return str(dict(self))

    def get(self, key) -> typing.Any | None:
        """Mimic get function from builtin Dict class"""
        try:
            return self[key]
        except IndexError:
            return None

    def __getattribute__(self, name: str) -> typing.Any | None:
        try:
            return super().__getattribute__(name)
        except AttributeError:
            try:
                return self[name]
            except IndexError:
                return None
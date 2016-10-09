# coding=utf-8
#
# Copyright © 2016, Itinken Limited
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT.  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function
from __future__ import unicode_literals

import os

from system import clone, libc


def test_no_arg():
    (r, w) = os.pipe()

    def f():
        os.close(r)
        os.write(w, b'ok')
        os.close(w)

    pid = clone(f, libc.CLONE_NEWUSER)
    assert pid > 0

    os.close(w)
    msg = os.read(r, 1024)
    assert msg == b'ok'


def test_with_arg():
    (r, w) = os.pipe()

    def f(arg):
        os.close(r)
        os.write(w, arg)
        os.close(w)

    data = b'hello world'
    clone(f, libc.CLONE_NEWUSER, data)

    os.close(w)
    msg = os.read(r, 1024)
    assert msg == data


def test_return_is_exitstatus():
    def f():
        return 42

    pid = clone(f)
    _, status = os.waitpid(pid, 0)
    assert os.WEXITSTATUS(status) == 42


def test_many_args():
    (r, w) = os.pipe()

    def f(a, b=1, c=None):
        os.close(r)
        os.write(w, '%s %s' % (a, c))
        os.close(w)

    clone(f, libc.CLONE_NEWUSER, 'hello', c='mary')
    os.close(w)
    msg = os.read(r, 1024)

    assert msg == b'hello mary'

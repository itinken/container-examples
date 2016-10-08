# coding=utf-8
#
# Copyright © 2016, Itinken Limited
#
# All rights reserved. Any redistribution or reproduction of part or
# all of the contents in any form is prohibited.
#
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

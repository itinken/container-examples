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

import signal

import six
from cffi import FFI

# For clone and related process orientated system calls.
ffi = FFI()
ffi.cdef('''
#define CLONE_NEWCGROUP         0x02000000      /* New cgroup namespace */
#define CLONE_NEWUTS            0x04000000      /* New utsname namespace */
#define CLONE_NEWIPC            0x08000000      /* New ipc namespace */
#define CLONE_NEWUSER           0x10000000      /* New user namespace */
#define CLONE_NEWPID            0x20000000      /* New pid namespace */
#define CLONE_NEWNET            0x40000000      /* New network namespace */
#define CLONE_NEWNS             0x00020000      /* New mount namespace group */

#define CLONE_VM	0x00000100	/* set if VM shared between processes */

#define SIGCHLD     17

int unshare(int flags);

int clone(int (*fn)(void *), void *child_stack,
                 int flags, void *arg, ...
                 /* pid_t *ptid, struct user_desc *tls, pid_t *ctid */ );
''')

libc = ffi.dlopen(None)

STACK_SIZE = 2 * 1024 * 1024


def clone(func, flags=0, *args, **kwargs):
    """
    Wrap the clone system call with a standard python function.

    :param func: The python function to run in the cloned proceses, must accept a
                 single argument.
    :param flags: Flags that get passed into clone().  This SIGCHLD value will be added.
    :return: The process id of the newly created process.
    """

    # clone requires a chunk of memory to use as a stack.  We need a pointer
    # to the end of the memory, since stacks usually grow down.  If you happen
    # to be on an architecture where this is not true, you will have to modify.
    stack = ffi.new('char[]', STACK_SIZE)
    stack_top = stack + STACK_SIZE

    # Have to wrap as a ffi callback function.
    @ffi.callback('int (void *)')
    def _run(_):
        r = func(*args, **kwargs)
        return int_value(r)

    # Note that we don't pass 'arg' via the system call, although we could there is no
    # need to as it is available in the closure formed by _run().
    return libc.clone(_run, stack_top, flags | signal.SIGCHLD, ffi.NULL)


def int_value(r):
    # type: (Any) -> int
    """
    The return value has to be an integer.

    If the return already is one, then just return it.

    If it is None, this is the normal return when nothing is returned from a python
    function, so return 0 in this case.

    For anything else, return 1 since it is an error.

    :param r: The original return value from the user defined function.
    :return: Our return value which is always an integer.
    """
    if isinstance(r, int):
        return r
    elif r is None:
        return 0
    else:
        return 1

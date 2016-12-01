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

import subprocess

import os
import six

from system import libc, clone

# Change this to match the outside uid in /etc/subuid
OUTSIDE_MIN_UID = 300000
OUTSIDE_MIN_GID = 300000  # Same but for group id


class ContainerBase(object):
    """
    A base class to construct a container.

    By itself it creates a new user namespace and can run a user supplied
    function in that environment.

    Subclasses should set the namespace_flags to include the desired
    namespaces, and override setup() to perform requied setup.
    """

    # The namespace flags.  We will set this to a different set of flags
    # in subclasses later in the series.
    namespace_flags = libc.CLONE_NEWUSER  # type: int

    def __init__(self):
        self.pid = None

    def run(self, func, *args, **kwargs):
        """

        :param func: User suplied function to run in the child namespaced process.
        :param args, kwargs: Any arguments for func
        :return: The process id of the new process.
        """

        (rfd, wfd) = os.pipe()

        # We wrap the supplied function so that we can wait until the
        # parent process has setup our environment before calling the
        # user supplied function.
        def _run(*args, **kwargs):
            os.close(wfd)
            os.read(rfd, 1)

            # Now we should be able to set uid=0, gid=0
            os.setuid(0)
            os.setgid(0)

            # Call function for subclasses
            self.setup()

            # Now the function will be run as root inside the namespace
            return func(*args, **kwargs)

        pid = clone(_run, self.namespace_flags, *args, **kwargs)
        self.pid = pid
        os.close(rfd)

        self.setup_user_maps()
        # Signal to the child that we have finished setting up the namespace
        # by closing the pipe, no need to write anything!
        os.close(wfd)
        return pid

    def setup(self):
        """
        Override in subclasses to setup the environment prior to the
        user supplied function being call.  The user and group ids
        have already been set to 0.
        """

    def wait(self):
        if self.pid:
            return os.waitpid(self.pid, 0)

        raise ValueError('No process to wait for')

    def setup_user_maps(self):
        """
        Set up the user and group mappings.

        We are using the newuidmap programs.
        """

        inside_low = 0
        outside_low = OUTSIDE_MIN_UID
        count = 2000

        for cmd in ('uid', 'gid'):
            if cmd == 'gid':
                outside_low = OUTSIDE_MIN_GID
            cmdlist = ['new%smap' % cmd, six.text_type(self.pid)]
            cmdlist.extend([six.text_type(s) for s in (inside_low, outside_low, count)])

            subprocess.call(cmdlist)

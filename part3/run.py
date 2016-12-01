# coding=utf-8
from __future__ import print_function
from __future__ import unicode_literals

import os

from base import ContainerBase
from system import libc

cb = ContainerBase()
cb.namespace_flags = libc.CLONE_NEWUSER | libc.CLONE_NEWNS
cb.run(os.system, 'bash')
cb.wait()

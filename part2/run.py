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

from base import ContainerBase

cb = ContainerBase()
cb.run(os.system, 'bash')
cb.wait()

#!/usr/bin/python3.5
#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#

# Copyright 2010 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.

import os
import sys

# Set the path so that modules can be found
path_to_parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if path_to_parent not in sys.path:
        sys.path.insert(0, path_to_parent)

import pkg5testenv

def setup_environment(proto):
        pkg5testenv.setup_environment(proto)

# Vim hints
# vim:ts=8:sw=8:et:fdm=marker

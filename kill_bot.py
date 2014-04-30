#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

#===============
# Python Script for killing the IMDb bot process
#  By /u/zd9
#
# Written in Python 2.7.6
#===============

import psutil
import signal

target = "bot.py"

# scan through processes
for proc in psutil.process_iter():
    # pay special attention to Python processes
    if proc.name == "Python":
        broken_path = proc.cmdline[-1].split("/")
        source_f = broken_path[-1]
        # if the source file name matches the target, kill the process
        if source_f == target:
            proc.send_signal(signal.SIGUSR1)
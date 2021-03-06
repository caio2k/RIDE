#  Copyright 2008-2015 Nokia Solutions and Networks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import sys
import os
import re
import datetime
import tempfile
import wx
import atexit

from robotide.widgets import Dialog


class Syslog(object):
    """Global logger to write debug info to a syslog file

    The syslog file is overwritten on each restart.
    """
    def __init__(self):
        self._path = os.path.join(tempfile.gettempdir(), 'ride.log')
        self._outfile = None
        atexit.register(self._close)

    def _close(self):
        self._output.flush()
        self._output.close()

    @property
    def _output(self):
        if self._outfile is None:
            self._outfile = open(self._path, 'w')
        return self._outfile

    def message(self, msg, level='INFO'):
        ts = datetime.datetime.utcnow().isoformat()
        self._output.write('{0} | {1} | {2}\n'.format(ts, level, msg))


class Logger(object):
    empty_suite_init_file_warn = re.compile("Test suite directory initialization "
                                            "file '.*' contains no test data.")

    def __init__(self):
        self._messages = []

    def report_parsing_errors(self):
        errors = [m[0] for m in self._messages]
        if errors:
            # Warnings from robot.variables.Variables.set_from_variable_table
            # are present multiple times, issue 486.
            errors = set(errors)
            dlg = ParsingErrorDialog('\n'.join(self._format_parsing_error_line(line)
                                               for line in errors))
            dlg.ShowModal()
            dlg.Destroy()
        self._messages = []

    def _format_parsing_error_line(self, line):
        if ':' not in line:
            return line
        index = line.index(':') + 1
        return line[:index] + '\n\t' + line[index:]

    def warn(self, msg=''):
        self._write(msg, 'WARN')

    def error(self, msg=''):
        self._write(msg, 'ERROR')

    def message(self, msg):
        message, level = msg.message, msg.level.upper()
        if self._is_logged(level):
            self._messages.append((message, level))

    def _write(self, msg, level):
        level = level.upper()
        if self._is_logged(level) and not self._is_ignored_warning(msg):
            self._show_message(msg, level)

    def _is_logged(self, level):
        return level.upper() in ['ERROR', 'WARN']

    def _is_ignored_warning(self, msg):
        return self.empty_suite_init_file_warn.search(msg)

    def _show_message(self, msg, level):
        try:
            icon = level == 'ERROR' and wx.ICON_ERROR or wx.ICON_WARNING
            wx.MessageBox(msg, level, icon)
        except wx.PyNoAppError:
            sys.stderr.write('%s: %s\n' % (level, msg))


class ParsingErrorDialog(Dialog):

    def __init__(self, message):
        Dialog.__init__(self, title='Parsing errors', size=(700, 400),
                        style=wx.DEFAULT_FRAME_STYLE)
        area = wx.TextCtrl(self, size=(700,400), style=wx.TE_MULTILINE|wx.TE_DONTWRAP|wx.TE_READONLY)
        area.SetValue(message)

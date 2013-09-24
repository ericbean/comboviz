
#This file is part of ComboViz.
#
#ComboViz is a program for recording and visualizing measurements from a
#direct entry fence lock during manipulation.
#
#Copyright (C) 2013  Eric Beanland
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Program wide constants and general utilty classes"""

import contextlib
import os
import sys
import traceback

import gtk
import gobject



def get_resource(resource):
    """convert resource names into paths."""
    basedir = os.path.dirname(__file__)
    if getattr(sys, 'frozen', False):
        # The application is frozen
        basedir = os.path.dirname(sys.executable)

    return os.path.normpath(os.path.join(basedir, 'resources/', resource))


#Constants
APPNAME = 'ComboViz'

APP_XML = get_resource('lock.ui')
ERRDIALOG_XML = get_resource('err_dialog.ui')
MENU_XML = get_resource('menu.ui')



class UiHelper(object):
    """Get objects from builder via attributes. The status method pushes a
    status message to statusbar and pops after delay seconds"""
    def __init__(self, appname, filename):
        self.builder = gtk.Builder()
        self.builder.set_translation_domain(APPNAME)
        self.builder.add_from_file(filename)
        self._fn = filename


    def __getattr__(self, attr_name):
        try:
            return object.__getattribute__(self, attr_name)
        except AttributeError:  #FIXME this error should be fatal
            obj = self.builder.get_object(attr_name)
            if obj:
                setattr(self, attr_name, obj)
                return obj
            errmsg ='No object named \"%s\" in %s.'
            raise AttributeError, errmsg % (attr_name, self._fn)


    @contextlib.contextmanager
    def status(self, message, delay=3000):
        """Display a statusbar msg that will be visable for at least ms delay
        """
        cid = self.statusbar.get_context_id('context')
        mid = self.statusbar.push(cid, message)
        yield
        gobject.timeout_add(delay, self.statusbar.remove_message, cid, mid)



class except_hook(object):
    """Catch exceptions iterpreter wide, show a gtk.dialog if the exception is
    a subclass of Exception"""
    def __init__(self):
        if sys.excepthook == sys.__excepthook__:
            self.builder = gtk.Builder()
            #self.builder.set_translation_domain(appname)
            self.builder.add_from_file(ERRDIALOG_XML)
            self.dialog = self.builder.get_object('dialog')
            self.tb_label = self.builder.get_object('tb_label')
            self.ex_label = self.builder.get_object('ex_label')
            self.ad_label = self.builder.get_object('ad_label')
            self.expander = self.builder.get_object('expander')
            viewport = self.builder.get_object('viewport')
            viewport.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('white'))

            sys.excepthook = self

    def __call__(self, ex_cls, ex, tb):
        if not isinstance(ex, Exception):
            return # bail if ex isn't a subclass of Exception
        elif isinstance(ex, LockException):
            #Hide the extended details
            self.expander.set_visible(False)
        else:
            self.expander.set_visible(True)

        ad_text = '\n'.join(ex.args[1:]) if len(ex.args) > 1 else ''
        tb_text = ''.join(traceback.format_exception(ex_cls, ex, tb, 5))


        #write traceback to stderr
        sys.stderr.write(tb_text)
        sys.stderr.write('\n')

        errmsg = 'An error has occured:  {}'
        ex_text = ex.args[0]

        self.ex_label.set_label(errmsg.format(ex_text))
        self.ad_label.set_label(ad_text)
        self.tb_label.set_text(tb_text)
        self.dialog.run()
        self.dialog.hide()


class LockException(Exception):
    """Exception for recoverable errors caused by user input. Will trigger a
    dialog box with no traceback"""
    pass

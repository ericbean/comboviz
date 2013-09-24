#!/usr/bin/env python

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


"""Main module for ComboViz."""

import json
import os

import gtk
import gobject

from lockview import LockView
from cvfiles import CVLockFile
import misc
from misc import APPNAME, APP_XML, MENU_XML



class ComboVizApp(object):
    """Application controller for ComboViz."""
    def __init__(self):
        self.ui = misc.UiHelper(APPNAME, APP_XML)
        self.window = self.ui.main_window

        #setup models, LockView,and TreeView
        self.treecolumns = []

        vbox = self.ui.LV_vbox
        self.ui.LockView = LockView(self.ui.liststore)
        vbox.pack_start(self.ui.LockView)

        #setup combination col in treeview
        self.ui.comb_cellrenderer.connect('edited', self.on_combination_edited,
            self.ui.liststore)
        self.ui.comb_column.set_cell_data_func(self.ui.comb_cellrenderer,
            self.render_combination, self.ui.wheels_adj)
        #setup measurement col in treeview
        self.ui.meas_cellrenderer.connect('edited', self.on_measure_edited,
            self.ui.liststore)
        self.ui.meas_column.set_cell_data_func(self.ui.meas_cellrenderer,
            self.render_measurement)
        self.ui.meas_column.add_attribute(self.ui.meas_cellrenderer, 'text', 4)

        self.uim = gtk.UIManager()
        self.window.add_accel_group(self.uim.get_accel_group())
        self.uim.insert_action_group(self.ui.file_actiongroup, -1)
        self.uim.insert_action_group(self.ui.edit_actiongroup, -1)
        self.uim.insert_action_group(self.ui.view_actiongroup, -1)
        self.uim.insert_action_group(self.ui.help_actiongroup, -1)

        self.uim.add_ui_from_file(MENU_XML)
        self.ui.popup = self.uim.get_widget('/PopUp')
        self.ui.menubar = self.uim.get_widget('/MenuBar')
        vb1 = self.ui.vbox1
        vb1.pack_start(self.ui.menubar, False)
        vb1.reorder_child(self.ui.menubar, 0)

        self.ui.builder.connect_signals(self)

        self.lockfile = CVLockFile()

        #set file dialogs to open in home
        home = os.path.expanduser('~')
        self.ui.open_dialog.set_current_folder_uri(home)
        self.ui.saveas_dialog.set_current_folder_uri(home)

        self.window.show_all()



    def on_add_button_clicked(self, widget, data=None):
        d = self.ui.dial_size_adj.get_value()
        mw = self.ui.wheels_adj.get_value()

        text = self.ui.combo_entry.get_text()
        x = [float(s) for s in text.split('-') if s]
        row = [0,0,0,0]
        row[0:len(x)] = x

        row.append(float(self.ui.meas_entry.get_text()))
        self.ui.liststore.append(row)
        self.window.set_focus(self.ui.combo_entry)


    def on_entry_activate(self, widget):
        self.window.do_move_focus(self.window, gtk.DIR_TAB_FORWARD)


    def on_draw_grid_toggled(self, action):
        self.ui.LockView.draw_grid = action.get_active()
        self.ui.LockView.queue_draw()


    def render_combination(self, treecolumn, cell, model, treeiter, adj):
        """Callback for displaying entered combinations in TreeView."""
        wheels = int(adj.get_value())
        path = model.get_path(treeiter)
        row = model[path]
        string = []
        for i in xrange(wheels):
            string.append('%g' % row[i])

        cell.set_property('text', '-'.join(string))


    def render_measurement(self, treecolumn, cell, model, treeiter):
        """Callback for displaying entered measurements in TreeView."""
        try:
            m = float(cell.get_property('text'))
            cell.set_property('text', '%g' % m)
        except:
            print cell.get_property('text')

    def on_measure_edited(self, cell, path, text, model):
        model[path][4] = float(text)


    def on_combination_edited(self, cell, path, text, model):
        d = self.ui.dial_size_adj.get_value()
        x = [float(s) for s in text.split('-') if s]
        row = list(model[path])
        row[0:len(x)] = x
        model[path] = row


    def on_delete_event(self, widget, event):
        if not self.lockfile.dumped:
            rsp = self.ask_save()
            if rsp == 1: #save
                self.on_save_activate(None)
                return False
            elif rsp == 0: #cancel
                return True

        return False

    def on_main_window_destroy(self, widget, data=None):
        gtk.main_quit()


    def on_quit_activate(self, action):
        event = gtk.gdk.Event(gtk.gdk.DELETE)
        destroy = not (self.window.emit("delete-event", event))
        if destroy:
            self.window.destroy()
            del self.window


    def ask_save(self):
        """Ask user to continue, cancel, or save and return the response"""
        rsp = self.ui.ask_save_dialog.run()
        self.ui.ask_save_dialog.hide()
        return rsp


    def on_new_activate(self, action):
        if not self.lockfile.dumped:
            rsp = self.ask_save()
            if rsp == 1: #save
                self.on_save_activate(action)
            elif rsp == 0: #cancel
                return

        self.lockfile = CVLockFile()
        self.ui.LockView.set_rows(self.lockfile.rows)
        self.ui.dial_size_adj.set_value(self.lockfile.dial_size)
        self.ui.wheels_adj.set_value(self.lockfile.wheels)
        self.ui.scale_adj.set_value(self.lockfile.scale)
        self.ui.draw_grid.set_active(self.lockfile.draw_grid)


    def on_open_activate(self, action):
        if not self.lockfile.dumped:
            rsp = self.ask_save()
            if rsp == 1: #save
                self.on_save_activate(action)
            elif rsp == 0: #cancel
                return

        rsp = self.ui.open_dialog.run()
        self.ui.open_dialog.hide()
        if rsp == 1: #open
            fpath =  self.ui.open_dialog.get_filename()
            self.lockfile = CVLockFile(fpath)
            self.ui.LockView.set_rows(self.lockfile.rows)
            self.ui.dial_size_adj.set_value(self.lockfile.dial_size)
            self.ui.wheels_adj.set_value(self.lockfile.wheels)
            self.ui.scale_adj.set_value(self.lockfile.scale)
            self.ui.draw_grid.set_active(self.lockfile.draw_grid)


    def on_save_activate(self, action):
        if not self.lockfile.path:
            self.on_saveas_activate(action)

        else:
            self.lockfile.rows = self.ui.LockView.get_rows()
            with self.ui.status('Saving {}...'.format(self.lockfile.path)):
                self.lockfile.dump()
            

    def on_saveas_activate(self, action):
        if not self.lockfile.path:
            self.ui.saveas_dialog.set_current_name('unsaved.cvj')
        rsp = self.ui.saveas_dialog.run()
        self.ui.saveas_dialog.hide()
        if rsp == 1: #save
            self.lockfile.path = self.ui.saveas_dialog.get_filename()
            self.on_save_activate(action)

    def on_about_activate(self, action):
        self.ui.aboutdialog.run()
        self.ui.aboutdialog.hide()

    def on_cut_activate(self, action):
        print 'on_cut_activate'

    def on_copy_activate(self, action):
        print 'on_copy_activate'

    def on_paste_activate(self, action):
        print 'on_paste_activate'


    def on_delete_activate(self, action):
        sel = self.ui.comb_treeview.get_selection()
        model, paths = sel.get_selected_rows()
        for path in paths:
            treeiter = model[path].iter
            model.remove(treeiter)


    def on_comb_treeview_button_press_event(self, treeview, event):
        if event.button == 3:
            treeview.grab_focus()
            x, y = int(event.x), int(event.y)
            pathinfo = treeview.get_path_at_pos(x, y)
            if pathinfo:
                path, tv_col, cx, cy = pathinfo
                treeview.set_cursor(path, tv_col, 0)
                self.ui.popup.popup(None, None, None, event.button, event.time)


    def on_comb_treeview_focus_in_event(self, treeview, event):
        self.ui.edit_actiongroup.set_sensitive(True)


    def on_comb_treeview_focus_out_event(self, treeview, event):
        self.ui.edit_actiongroup.set_sensitive(False)


    def on_dial_size_adj_value_changed(self, adjustment):
        value = int(adjustment.get_value())
        self.lockfile.dial_size = value
        self.ui.LockView.dial_size = value
        self.ui.LockView.queue_draw()


    def on_wheels_adj_value_changed(self, adjustment):
        value = int(adjustment.get_value())
        self.lockfile.wheels = value
        self.ui.LockView.wheel_count = value
        self.ui.LockView.queue_resize()
        self.ui.comb_treeview.columns_autosize()


    def on_scale_adj_value_changed(self, adjustment):
        value = adjustment.get_value()
        self.lockfile.scale = value
        self.ui.LockView.scale = value
        self.ui.LockView.queue_draw()


def run():
    misc.except_hook()
    app = ComboVizApp()
    app.window.show()
    gtk.gdk.threads_init()
    with gtk.gdk.lock:
        gtk.main()

if __name__ == '__main__':
    run()

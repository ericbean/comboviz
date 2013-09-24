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


"""LockView widget and the sectorfy function."""

from __future__ import division
import bisect
import itertools
import math

import gtk


class LockView(gtk.Widget):
    """Gtk+ Widget for displaying information about a combination lock."""

    __gtype_name__ = "LockView" #registers widget with gobject


    def __init__(self, model):
        gtk.Widget.__init__(self)

        self.model = model
        self.scale = 5 #scaling factor for measurements
        self.wheel_count = 3
        self.dial_size = 100
        self.num = 0

        self.wheels = []

        #radius of our wheel
        self.radius = 80

        #set flag for gtk
        self.set_has_window(True)

        self.draw_grid = True

        model.connect("row-changed", self.on_model_changed)
        model.connect("row-deleted", self.on_model_changed)


    def on_model_changed(self, model, path, treeiter=None):
        self.queue_draw()


    def do_expose_event(self, event):
        wheels = []
        for i in xrange(self.wheel_count):
            x = [(r[i], r[4]) for r in self.model]
            wheels.append(sectorfy(x, self.dial_size))

        self.window.clear() #clear the gdk window
        area = (0, 0, self.allocation.width, self.allocation.height)
        self.style.paint_box(self.window, self.state, gtk.SHADOW_IN, area,
            self, 'detail', 0, 0, self.allocation.width,
            self.allocation.height)

        cr = self.window.cairo_create()
    
        # set clip region
        cr.rectangle(event.area.x, event.area.y, 
                event.area.width, event.area.height)
        cr.clip()

        tick = (self.allocation.width - 50) / self.dial_size
        step = max(int(round(self.dial_size / 20)), 1)
        steps = xrange(0, int(self.dial_size), step)

        zipped = zip(wheels, self.layouts)
        for index, (wheel, (xc, yc)) in enumerate(zipped):
            if self.draw_grid:
                self._draw_grid(xc, yc, cr, steps, step, tick)
            self._draw_wheel(wheel, index, xc, yc, cr, steps, step, tick)

        self._draw_separators(cr)


    def _draw_wheel(self, wheel, index, xc, yc, cr, steps, step, tick):
        fg = self.style.fg[self.state]
        cr.set_source_rgb(fg.red_float, fg.green_float, fg.blue_float)

        y = (index * 110) + (110 / 2)
        cr.move_to(25, yc + (wheel[0][2] * self.scale))
        for start, end, v in wheel:
            start, end = start * tick, end * tick
            v = v * self.scale
            cr.line_to(25 + start + (tick / 2), yc + v)
            cr.line_to(25 + end - (tick / 2), yc + v)
        else:
            cr.line_to(25 + end, yc + (wheel[0][2] * self.scale))

        cr.stroke()

        #draw dial tick labels
        for i in xrange(0, int(self.dial_size), step):
            layout = self.create_pango_layout('%g' % i)
            width, height = layout.get_pixel_size()
            x,y = 25 + int((tick * i) - (width / 2) + (tick / 2)), int(yc + 40)
            gc = self.style.text_gc[self.state]
            self.window.draw_layout(gc, x, y, layout)

        #add wheel label
        layout = self.create_pango_layout('Wheel %g' % index)
        width, height = layout.get_pixel_size()
        bg = self.style.bg[self.state]
        cr.set_source_rgb(bg.red_float, bg.green_float, bg.blue_float)
        cr.rectangle(5, int(yc - 50), width, height)
        cr.fill()
        self.window.draw_layout(gc, 5, int(yc - 50), layout)

    def _draw_grid(self, xc, yc, cr, steps, step, tick):
        cr.save()
        bg = self.style.mid[self.state]
        cr.set_source_rgb(bg.red_float, bg.green_float, bg.blue_float)
        cr.set_line_width(1)

        
        x = 25 + (tick / 2) - 0.5
        for i in steps:
            cr.move_to(x+(i*tick), yc-45)
            cr.line_to(x+(i*tick), yc+40)
            cr.stroke()

        cr.restore()


    def _draw_separators(self, cr):
        for i in xrange(self.wheel_count):
            i *=110
            self.style.paint_hline(self.window, self.state, None, self,
                'detail', self.style.xthickness, self.allocation.width, i)


    def do_realize(self):
        self.set_realized(True)
        self.window = gtk.gdk.Window(
                self.get_parent_window(),
                width=self.allocation.width,
                height=self.allocation.height,
                window_type=gtk.gdk.WINDOW_CHILD,
                wclass=gtk.gdk.INPUT_OUTPUT,
                event_mask=self.get_events() | gtk.gdk.EXPOSURE_MASK)

        self.window.set_user_data(self)
        self.style.attach(self.window)
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)


    def do_unrealize(self):
        self.window.destroy()


    def do_size_request(self, requisition):
        sq = 110
        sizes = ((sq*4, sq), (sq*4, sq*2), (sq*4, sq*3), (sq*4, sq*4))
        i = self.wheel_count - 1

        requisition.width, requisition.height = sizes[i]


    def do_size_allocate(self, allocation):
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)

            self.allocation = allocation
            width, height = allocation.width, allocation.height

            layouts = []
            sq = 110
            max_rows = height // sq
            for i in xrange(max_rows):
                w, h = 0, (sq / 2) + (i * sq)
                layouts.append((w, h))

            self.layouts = layouts[:self.wheel_count]


    def set_rows(self, rows):
        """Clear the model and add news rows to the model. The 'row-changed' 
        signal will be emitted for the last row only."""
        self.model.handler_block_by_func(self.on_model_changed)
        self.model.clear()
        for row in rows:
            treeiter = self.model.append(row)

        self.model.handler_unblock_by_func(self.on_model_changed)
        self.queue_draw()


    def get_rows(self):
        """Retrieve a list of rows from the model. Each row will be a list."""
        return [list(row) for row in self.model]



def sectorfy(points, stop=100):
    """Convert a list of (point, radius) tuples to a list of
    (start, end, radius) tuples."""
    """
    >>> a = [(10.0, 1)]
    >>> sectorfy(a, stop=20)
    [(0, 10.0, 0), (10.0, 11.0, 1), (11.0, 20, 0)]

    >>> a = [(0.0, 1)]

    >>> sectorfy(a, stop=10)
    [(0, 1, 1), (1, 10, 0)]

    >>> a = [(5.0, 2), (5.5, 1)]
    >>> sectorfy(a, stop=10)
    [(0, 5.0, 0), (5.0, 6.0, 2), (6.0, 6.5, 1), (6.5, 10, 0)]


    >>> a = [(5.0, 1), (5.5, 2), (15.0, 1)]
    >>> sectorfy(a, stop=10)
    [(0, 5.0, 0), (5.0, 5.5, 1), (5.5, 6.5, 2), (6.5, 10, 0)]

    >>> a = [(5.0, 1), (10.0, -1)]

    >>> sectorfy(a, stop=11)
    [(0, 5.0, 1), (5.0, 6.0, 2), (6.0, 10.0, 1), (10.0, 11, 0)]

    >>> a = []
    >>> sectorfy(a)
    [(0, 100, 0)]
    """

    #filter out unnecessary points
    points = filter(lambda (k,v): v != 0 and k < stop, points)

    d = {0:0, stop:0}
    minv = 0

    for k,v in points:
        d[k] = max(v, d.get(k, min(0, v)))

    x = sorted(d.items())
    for (k,v), (k2,v2) in zip(x, x[1:]):
        if k+1 < k2 and v != 0:
            d[k+1] = 0

        elif k+1 > k2 and v != v2 != 0 and v > v2:
            del d[k2]
            d[k+1] = v2

    #turn points into sectors
    x, v = itertools.izip(*sorted(d.items()))
    minv = min(min(d.values()), 0)

    v = (t - minv for t in v if t is not None)
    y = iter(x)
    next(y, None)

    return zip(x,y,v)



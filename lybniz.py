#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
    Simple Function Graph Plotter
    © Thomas Führinger, Sam Tygier 2005-2018
    https://github.com/thomasfuhringer/lybniz
    Version 3.0.4
    Requires PyGObject 3
    Released under the terms of the revised BSD license
    Modified: 2018-08-16
"""
import sys, os, cairo, gettext, configparser
from math import *
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject, Pango, Gio, GdkPixbuf

app_version = "3.0.4"

gettext.install("lybniz")

# profiling
enable_profiling = False
if enable_profiling:
    from time import time

app_win = None
actions = Gtk.ActionGroup(name="General")
graph = None
connect_points = True
configFile = os.path.expanduser("~/.lybniz.cfg")
config = configparser.ConfigParser()

x_res = 1

x_max = "5.0"
x_min = "-5.0"
x_scale = "1.0"

y_max = "3.0"
y_min = "-3.0"
y_scale = "1.0"

y1 = "sin(x)"
y2 = ""
y3 = ""

# some extra maths functions
def fac(x):
    if type(x) != int or x < 0:
        raise ValueError
    if x==0:
        return 1
    for n in range(2,x):
        x = x*n
    return x

def sinc(x):
    if x == 0:
        return 1
    return sin(x)/x

# create a safe namespace for the eval()s in the graph drawing code
def sub_dict(somedict, somekeys, default=None):
    return dict([ (k, somedict.get(k, default)) for k in somekeys ])
# a list of the functions from math that we want.
safe_list = ['math','acos', 'asin', 'atan', 'atan2', 'ceil', 'cos', 'cosh', 'degrees', 'e', 'exp', 'fabs', 'floor', 'fmod', 'frexp', 'hypot', 'ldexp', 'log', 'log10', 'modf', 'pi', 'pow', 'radians', 'sin', 'sinh', 'sqrt', 'tan', 'tanh','fac','sinc']
safe_dict = sub_dict(locals(), safe_list)

#add any needed builtins back in.
safe_dict['abs'] = abs
safe_dict['min'] = min
safe_dict['max'] = max

def marks(min_val,max_val,minor=1):
    "Yield positions of scale marks between min and max. For making minor marks, set minor to the number of minors you want between majors"
    try:
        min_val = float(min_val)
        max_val = float(max_val)
    except:
        print ("Needs 2 numbers")
        raise ValueError

    if(min_val >= max_val):
        print ("Min bigger or equal to max")
        raise ValueError

    a = 0.2   # tweakable control for when to switch scales
              # big a value results in more marks

    a = a + log10(minor)

    width = max_val - min_val
    log10_range = log10(width)

    interval = 10 ** int(floor(log10_range - a))
    lower_mark = min_val - fmod(min_val,interval)

    if lower_mark < min_val:
        lower_mark += interval

    a_mark = lower_mark
    while a_mark <= max_val:
        if abs(a_mark) < interval / 2:
            a_mark = 0
        yield a_mark
        a_mark += interval

class GraphClass:
    def __init__(self):
        def da_configure_event(widget, event):
            global x_max, x_min, x_scale, y_max, y_min, y_scale, y1, y2, y3

            x_max = app_win.x_max_entry.get_text()
            x_min = app_win.x_min_entry.get_text()
            x_scale = app_win.x_scale_entry.get_text()

            y_max = app_win.y_max_entry.get_text()
            y_min = app_win.y_min_entry.get_text()
            y_scale = app_win.y_scale_entry.get_text()

            y1 = app_win.y1_entry.get_text()
            y2 = app_win.y2_entry.get_text()
            y3 = app_win.y3_entry.get_text()

            gdkWindow = widget.get_window()
            width = widget.get_allocated_width()
            height = widget.get_allocated_height()
            self.surface = gdkWindow.create_similar_surface(cairo.CONTENT_COLOR, width, height)

            self.layout = Pango.Layout(widget.create_pango_context())
            self.canvas_width = width
            self.canvas_height = height
            self.x_max = eval(x_max,{"__builtins__":{}},safe_dict)
            self.x_min = eval(x_min,{"__builtins__":{}},safe_dict)
            self.x_scale = eval(x_scale,{"__builtins__":{}},safe_dict)
            self.y_max = eval(y_max,{"__builtins__":{}},safe_dict)
            self.y_min = eval(y_min,{"__builtins__":{}},safe_dict)
            self.y_scale = eval(y_scale,{"__builtins__":{}},safe_dict)
            self.previousMouseX = 0
            self.previousMouseY = 0
            self.plot()
            return True

        # Redraw the screen from the backing pixmap
        def da_draw_event(widget, cr):
            cr.set_source_surface(self.surface, 0, 0)
            cr.paint()
            return False

        # Start marking selection
        def button_press_event(widget, event):
            global x_sel, y_sel

            if event.button == 1:
                self.selection[0][0], self.selection[0][1] = int(event.x), int(event.y)
                self.selection[1][0], self.selection[1][1] = None, None

                # duplicate surface
                self.clean_surface = self.surface.create_similar(cairo.CONTENT_COLOR, self.canvas_width, self.canvas_height)
                crc = cairo.Context(self.clean_surface)
                crc.set_source_surface(self.surface, 0, 0)
                crc.paint()
                del crc

        # End of selection
        def da_button_release_event(widget, event):
            if event.button == 1 and event.x != self.selection[0][0] and event.y != self.selection[0][1]:
                xmi, ymi = min(self.graph_x(self.selection[0][0]), self.graph_x(event.x)), min(self.graph_y(self.selection[0][1]), self.graph_y(event.y))
                xma, yma = max(self.graph_x(self.selection[0][0]), self.graph_x(event.x)), max(self.graph_y(self.selection[0][1]), self.graph_y(event.y))
                self.x_min, self.y_min, self.x_max, self.y_max = xmi, ymi, xma, yma
                parameter_entries_repopulate()
                self.plot()
                self.selection[1][0] = None
                self.selection[0][0] = None

        # Draw rectangle during mouse movement
        def da_motion_notify_event(widget, event):

            if event.is_hint:
                dummy, x, y, state = event.window.get_device_position(event.device)
            else:
                x = event.x
                y = event.y
                state = event.get_state()

            if state & Gdk.ModifierType.BUTTON1_MASK and self.selection[0][0] is not None:
                cr = cairo.Context(self.surface)
                cr.set_source_surface(self.clean_surface, 0, 0)
                cr.paint()

                x0 = min(self.selection[0][0], int(x))
                y0 = min(self.selection[0][1], int(y))
                w = abs(int(x) - self.selection[0][0])
                h = abs(int(y) - self.selection[0][1])
                self.selection[1][0], self.selection[1][1] = int(x), int(y)

                cr.set_source_rgb(0.3, 0.3, 0.3)
                cr.set_line_width (0.5)
                cr.rectangle(x0, y0, w, h)
                cr.stroke()
                del cr
                widget.queue_draw()
            elif state & Gdk.ModifierType.BUTTON2_MASK:
                dx = event.x - self.previousMouseX
                dy = event.y - self.previousMouseY
                dx = dx / self.canvas_width * (self.x_max - self.x_min)
                dy = dy / self.canvas_height * (self.y_max - self.y_min)
                self.x_min -= dx; self.x_max -= dx
                self.y_min += dy; self.y_max += dy
                parameter_entries_repopulate()
                graph.plot()

            self.previousMouseX = event.x
            self.previousMouseY = event.y

        def da_scroll_event(widget, event):
            if event.direction == Gdk.ScrollDirection.UP:
                zoom_in(None)
            elif event.direction == Gdk.ScrollDirection.DOWN:
                zoom_out(None)

        self.prev_y = [None, None, None]

        # Marked area point[0, 1][x, y]
        self.selection = [[None, None], [None, None]]

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", da_draw_event)
        self.drawing_area.connect("configure_event", da_configure_event)
        self.drawing_area.connect("button_press_event", button_press_event)
        self.drawing_area.connect("button_release_event", da_button_release_event)
        self.drawing_area.connect("motion_notify_event", da_motion_notify_event)
        self.drawing_area.connect("scroll-event", da_scroll_event)
        self.drawing_area.set_events(Gdk.EventMask.EXPOSURE_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK | Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.POINTER_MOTION_HINT_MASK | Gdk.EventMask.SCROLL_MASK)
        self.scale_style = "dec"

    def plot(self):
        cr = cairo.Context(self.surface)
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width (0.2)
        app_win.status_bar.remove_all(0)

        if (self.scale_style == "cust"):

            #draw cross
            cr.rectangle(self.canvas_x(0), 0, 0.2, self.canvas_height)
            cr.rectangle(0, self.canvas_y(0), self.canvas_width, 0.2)
            cr.stroke()

            # old style axis marks
            iv = self.x_scale * self.canvas_width / (self.x_max - self.x_min) # pixel interval between marks
            os = self.canvas_x(0) % iv                                        # pixel offset of first mark
            # loop over each mark.
            for i in range(int(self.canvas_width / iv + 1)):
                # multiples of iv, cause adding of any error in iv, so keep iv as float
                # use round(), to get to closest pixel, int() to prevent warning
                cr.rectangle(os + i * iv,  self.canvas_y(0) - 5, 0.2, 11)
                cr.stroke()

            # and the y-axis
            iv = self.y_scale * self.canvas_height / (self.y_max - self.y_min)
            os = self.canvas_y(0) % iv
            for i in range(int(self.canvas_height / iv + 1)):
                cr.rectangle(self.canvas_x(0) - 5, i * iv + os, 11, 0.2)
                cr.stroke()

        else:
            # new style
            factor = 1
            if (self.scale_style == "rad"): factor = pi
            if (self.scale_style == "tau"): factor = 2 * pi

            # where to put the numbers
            numbers_x_pos = -10
            numbers_y_pos = 10

            # where to center the axis
            center_x_pix = int(round(self.canvas_x(0)))
            center_y_pix = int(round(self.canvas_y(0)))
            if (center_x_pix < 5): center_x_pix = 5
            if (center_x_pix < 20):numbers_x_pos = 10
            if (center_y_pix < 5): center_y_pix = 5
            if (center_x_pix > self.canvas_width - 5): center_x_pix = self.canvas_width - 5
            if (center_y_pix > self.canvas_height -5): center_y_pix = self.canvas_height - 5;
            if (center_y_pix > self.canvas_height -20): numbers_y_pos = - 10

            # draw cross
            cr.rectangle(center_x_pix, 0, 0.1, self.canvas_height)
            cr.rectangle(0, center_y_pix, self.canvas_width, 0.1)
            cr.stroke()

            for i in marks(self.x_min / factor, self.x_max / factor):
                label = '%g' % i
                if (self.scale_style == "rad"): label += " π"
                if (self.scale_style == "tau"): label += " τ"
                i = i * factor

                cr.rectangle(self.canvas_x(i),  center_y_pix - 5, 0.2, 11)
                cr.stroke()

                if (numbers_y_pos < 0):
                    adjust = cr.text_extents(label)[3]
                else:
                    adjust = 0
                cr.move_to(int(round(self.canvas_x(i))), center_y_pix + numbers_y_pos - adjust + 7)
                cr.show_text(label)

            for i in marks(self.y_min,self.y_max):
                label = '%g' % i

                cr.rectangle(center_x_pix - 5, self.canvas_y(i), 11, 0.2)
                cr.stroke()

                if (numbers_x_pos < 0):
                    adjust = cr.text_extents(label)[3]
                else:
                    adjust = 0
                cr.move_to(center_x_pix + numbers_x_pos - adjust, int(round(self.canvas_y(i))) + 7)
                cr.show_text(label)

            # minor marks
            for i in marks(self.x_min / factor, self.x_max / factor, minor=10):
                i = i * factor
                cr.rectangle(self.canvas_x(i),  center_y_pix - 2, 0.2, 5)
                cr.stroke()

            for i in marks(self.y_min, self.y_max, minor=10):
                label = '%g' % i
                cr.rectangle(center_x_pix - 2, self.canvas_y(i), 5, 0.2)
                cr.stroke()

        plots = []
        # precompile the functions
        invalid_input = False
        if y1:
            try:
                compiled_y1 = compile(y1.replace("^","**"), "", 'eval')
                plots.append((compiled_y1, 0, (0, 0, 1), y1))
            except:
                set_statusbar("Function '" + y1 + "' is invalid.")
                invalid_input = True
                compiled_y1 = None
        else:
            compiled_y1 = None

        if y2:
            try:
                compiled_y2 = compile(y2.replace("^","**"),"",'eval')
                plots.append((compiled_y2, 1, (1, 0, 0), y2))
            except:
                set_statusbar("Function '" + y2 + "' is invalid.")
                invalid_input = True
                compiled_y2 = None
        else:
            compiled_y2 = None

        if y3:
            try:
                compiled_y3 = compile(y3.replace("^","**"), "", 'eval')
                plots.append((compiled_y3, 2, (0, 1, 0), y3))
            except:
                set_statusbar("Function '" + y3 + "' is invalid.")
                invalid_input = True
                compiled_y3 = None
        else:
            compiled_y3 = None

        self.prev_y = [None, None, None]

        if enable_profiling:
            start_graph = time()

        cr.set_line_width (0.6)
        if len(plots) != 0:
            for i in range(0, self.canvas_width, x_res):
                x = self.graph_x(i + 1)
                for e in plots:
                    safe_dict['x']=x
                    try:
                        y = eval(e[0],{"__builtins__":{}},safe_dict)
                        y_c = int(round(self.canvas_y(y)))

                        if y_c < 0 or y_c > self.canvas_height:
                            self.prev_y[e[1]] = None
                        else:

                            cr.set_source_rgb(*e[2])
                            if connect_points and self.prev_y[e[1]] is not None:
                                cr.move_to(i, self.prev_y[e[1]])
                                cr.line_to(i + x_res, y_c)
                                cr.stroke()
                            else:
                                cr.rectangle(i + x_res, y_c, 1, 1)
                                cr.fill()

                        self.prev_y[e[1]] = y_c
                    except:
                        #print ("Error at %d: %s" % (x, sys.exc_info()))
                        set_statusbar("Function '" + e[3] + "' is invalid at " + str(int(x)) + ".")
                        invalid_input = True
                        self.prev_y[e[1]] = None

        if enable_profiling:
            print ("Time to draw graph:", (time() - start_graph) * 1000, "ms")

        if not invalid_input:
            set_statusbar("")

        del cr
        self.drawing_area.queue_draw()

    def canvas_x(self, x):
        "Calculate position on canvas to point on graph"
        return (x - self.x_min) * self.canvas_width / (self.x_max - self.x_min)

    def canvas_y(self, y):
        return (self.y_max - y) * self.canvas_height / (self.y_max - self.y_min)

    def canvas_point(self, x, y):
        return (self.canvas_x(x), self.canvas_y(y))

    def graph_x(self, x):
        "Calculate position on graph from point on canvas"
        return x  * (self.x_max - self.x_min) / self.canvas_width + self.x_min

    def graph_y(self, y):
        return self.y_max - (y * (self.y_max - self.y_min) / self.canvas_height)


def menu_toolbar_create():
    app_win.menu_main = Gtk.MenuBar()

    menu_file = Gtk.Menu()
    menu_item_file = Gtk.MenuItem(label=_("_File"))
    menu_item_file.set_submenu(menu_file)
    menu_item_file.set_use_underline(True)

    actions.save = Gtk.Action(name="Save", label=_("_Save"), tooltip=_("Save graph as bitmap"), stock_id=Gtk.STOCK_SAVE)
    actions.save.connect ("activate", save)
    actions.add_action(actions.save)
    menu_item_save = actions.save.create_menu_item()
    menu_item_save.add_accelerator("activate", app_win.accel_group, ord("S"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
    menu_file.append(menu_item_save)

    actions.quit = Gtk.Action(name="Quit", label=_("_Quit"), tooltip=_("Quit Application"), stock_id=Gtk.STOCK_QUIT)
    actions.quit.connect ("activate", quit_dlg)
    actions.add_action(actions.quit)
    menuItem_quit = actions.quit.create_menu_item()
    menuItem_quit.add_accelerator("activate", app_win.accel_group, ord("Q"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
    menu_file.append(menuItem_quit)

    menu_graph = Gtk.Menu()
    menu_item_graph = Gtk.MenuItem(label=_("_Graph"))
    menu_item_graph.set_submenu(menu_graph)
    menu_item_graph.set_use_underline(True)

    actions.plot = Gtk.Action(name="Plot", label=_("P_lot"), tooltip=_("Plot Functions"), stock_id=Gtk.STOCK_REFRESH)
    actions.plot.connect ("activate", plot)
    actions.add_action(actions.plot)
    menu_item_plot = actions.plot.create_menu_item()
    menu_item_plot.add_accelerator("activate", app_win.accel_group, ord("l"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
    menu_graph.append(menu_item_plot)

    actions.evaluate = Gtk.Action(name="Evaluate", label=_("_Evaluate"), tooltip=_("Evaluate Functions"), stock_id=Gtk.STOCK_EXECUTE)
    actions.evaluate.connect ("activate", evaluate)
    actions.add_action(actions.evaluate)
    menu_item_evaluate = actions.evaluate.create_menu_item()
    menu_item_evaluate.add_accelerator("activate", app_win.accel_group, ord("e"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
    menu_graph.append(menu_item_evaluate)

    actions.zoom_in = Gtk.Action(name="zoom_in", label=_("Zoom _In"), tooltip=_("Zoom In"), stock_id=Gtk.STOCK_ZOOM_IN)
    actions.zoom_in.connect ("activate", zoom_in)
    actions.add_action(actions.zoom_in)
    menu_item_zoomin = actions.zoom_in.create_menu_item()
    menu_item_zoomin.add_accelerator("activate", app_win.accel_group, ord("+"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
    menu_graph.append(menu_item_zoomin)

    actions.zoom_out = Gtk.Action(name="zoom_out", label=_("Zoom _Out"), tooltip=_("Zoom Out"), stock_id=Gtk.STOCK_ZOOM_OUT)
    actions.zoom_out.connect ("activate", zoom_out)
    actions.add_action(actions.zoom_out)
    menu_item_zoomout = actions.zoom_out.create_menu_item()
    menu_item_zoomout.add_accelerator("activate", app_win.accel_group, ord("-"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
    menu_graph.append(menu_item_zoomout)

    actions.zoom_reset = Gtk.Action(name="zoom_reset", label=_("Zoom _Reset"), tooltip=_("Zoom Reset"), stock_id=Gtk.STOCK_ZOOM_100)
    actions.zoom_reset.connect ("activate", zoom_reset)
    actions.add_action(actions.zoom_reset)
    menu_item_zoomreset = actions.zoom_reset.create_menu_item()
    menu_item_zoomreset.add_accelerator("activate", app_win.accel_group, ord("r"), Gdk.ModifierType.CONTROL_MASK, Gtk.AccelFlags.VISIBLE)
    menu_graph.append(menu_item_zoomreset)

    menu_item_toggle_connect = Gtk.CheckMenuItem(label=_("_Connect Points"))
    menu_item_toggle_connect.set_active(True)
    menu_item_toggle_connect.set_use_underline(True)
    menu_item_toggle_connect.connect ("toggled", toggle_connect)
    menu_graph.append(menu_item_toggle_connect)

    menu_scale_style = Gtk.Menu()
    menu_item_scale_style = Gtk.MenuItem(label=_("Scale Style"))
    menu_item_scale_style.set_submenu(menu_scale_style)
    menu_graph.append(menu_item_scale_style)

    actions.dec = Gtk.Action(name="Dec", label=_("Decimal"), tooltip=_("Set style to decimal"), stock_id=None)
    actions.dec.connect ("activate", scale_dec)
    actions.add_action(actions.dec)
    menu_item_dec = actions.dec.create_menu_item()
    menu_scale_style.append(menu_item_dec)

    actions.rad = Gtk.Action(name="Rad", label=_("Radians π"), tooltip=_("Set style to radians"), stock_id=None)
    actions.rad.connect ("activate", scale_rad)
    actions.add_action(actions.rad)
    menu_item_rad = actions.rad.create_menu_item()
    menu_scale_style.append(menu_item_rad)

    actions.rad_tau = Gtk.Action(name="Radτ", label=_("Radians τ"), tooltip=_("Set style to radians using Tau (τ)"), stock_id=None)
    actions.rad_tau.connect ("activate", scale_rad_tau)
    actions.add_action(actions.rad_tau)
    menu_item_rad_tau = actions.rad_tau.create_menu_item()
    menu_scale_style.append(menu_item_rad_tau)

    actions.cust = Gtk.Action(name="Cust", label=_("Custom"), tooltip=_("Set style to custom"), stock_id=None)
    actions.cust.connect ("activate", scale_cust)
    actions.add_action(actions.cust)
    menu_item_cust = actions.cust.create_menu_item()
    menu_scale_style.append(menu_item_cust)

    menu_help = Gtk.Menu()
    menu_item_help = Gtk.MenuItem(label="_Help", use_underline=True)
    menu_item_help.set_submenu(menu_help)
    menu_item_help.set_use_underline(True)

    actions.Help = Gtk.Action(name="Help", label=_("_Contents"), tooltip=_("Help Contents"), stock_id=Gtk.STOCK_HELP)
    actions.Help.connect ("activate", show_yelp)
    actions.add_action(actions.Help)
    menu_item_contents = actions.Help.create_menu_item()
    menu_item_contents.add_accelerator("activate", app_win.accel_group, Gdk.keyval_from_name("F1"), 0, Gtk.AccelFlags.VISIBLE)
    menu_help.append(menu_item_contents)

    actions.about = Gtk.Action(name="About", label=_("_About"), tooltip=_("About Box"), stock_id=Gtk.STOCK_ABOUT)
    actions.about.connect ("activate", show_about_dialog)
    actions.add_action(actions.about)
    menu_item_about = actions.about.create_menu_item()
    menu_help.append(menu_item_about)

    app_win.menu_main.append(menu_item_file)
    app_win.menu_main.append(menu_item_graph)
    app_win.menu_main.append(menu_item_help)

    app_win.tool_bar = Gtk.Toolbar()
    app_win.tool_bar.insert(actions.plot.create_tool_item(), -1)
    app_win.tool_bar.insert(actions.evaluate.create_tool_item(), -1)
    app_win.tool_bar.insert(Gtk.SeparatorToolItem(), -1)
    app_win.tool_bar.insert(actions.zoom_in.create_tool_item(), -1)
    app_win.tool_bar.insert(actions.zoom_out.create_tool_item(), -1)
    app_win.tool_bar.insert(actions.zoom_reset.create_tool_item(), -1)


def plot(widget, event=None):
    global x_max, x_min, x_scale, y_max, y_min, y_scale, y1, y2, y3

    x_max = app_win.x_max_entry.get_text()
    x_min = app_win.x_min_entry.get_text()
    x_scale = app_win.x_scale_entry.get_text()

    y_max = app_win.y_max_entry.get_text()
    y_min = app_win.y_min_entry.get_text()
    y_scale = app_win.y_scale_entry.get_text()

    graph.x_max = eval(x_max,{"__builtins__":{}},safe_dict)
    graph.x_min = eval(x_min,{"__builtins__":{}},safe_dict)
    graph.x_scale = eval(x_scale,{"__builtins__":{}},safe_dict)

    graph.y_max = eval(y_max,{"__builtins__":{}},safe_dict)
    graph.y_min = eval(y_min,{"__builtins__":{}},safe_dict)
    graph.y_scale = eval(y_scale,{"__builtins__":{}},safe_dict)

    y1 = app_win.y1_entry.get_text()
    y2 = app_win.y2_entry.get_text()
    y3 = app_win.y3_entry.get_text()

    graph.plot()


def evaluate(widget, event=None):
    "Evaluate a given x for the three functions"

    def entry_changed(self):
        for e in ((y1, dlg_win.y1_entry), (y2, dlg_win.y2_entry), (y3, dlg_win.y3_entry)):
            try:
                x = float(dlg_win.x_entry.get_text())
                safe_dict['x']=x
                e[1].set_text(str(eval(e[0].replace("^","**"),{"__builtins__":{}},safe_dict)))
            except:
                if len(e[0]) > 0:
                    e[1].set_text("Error: " + str(sys.exc_info()[1]))
                else:
                    e[1].set_text("")

    def close(self):
        dlg_win.destroy()

    dlg_win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    dlg_win.set_title(_("Evaluate"))
    dlg_win.connect("destroy", close)

    dlg_win.x_entry = Gtk.Entry()
    dlg_win.x_entry.set_size_request(200, 24)
    dlg_win.x_entry.connect("changed", entry_changed)
    dlg_win.y1_entry = Gtk.Entry()
    dlg_win.y1_entry.set_size_request(200, 24)
    dlg_win.y1_entry.set_sensitive(False)
    dlg_win.y2_entry = Gtk.Entry()
    dlg_win.y2_entry.set_size_request(200, 24)
    dlg_win.y2_entry.set_sensitive(False)
    dlg_win.y3_entry = Gtk.Entry()
    dlg_win.y3_entry.set_size_request(200, 24)
    dlg_win.y3_entry.set_sensitive(False)

    grid = Gtk.Grid()
    grid.set_property("row-spacing", 2)
    grid.set_property("column-spacing", 10)
    grid.set_border_width(24)

    label = Gtk.Label(label="x = ")
    label.set_valign(Gtk.Align.CENTER)
    label.set_halign(Gtk.Align.START)
    grid.add(label)
    grid.attach(dlg_win.x_entry, 1, 0, 1, 1)
    label = Gtk.Label(label="y1 = ")
    label.set_halign(Gtk.Align.START)
    label.set_valign(Gtk.Align.CENTER)
    label.get_style_context().add_class("y1")
    grid.attach(label, 0, 1, 1, 1)
    grid.attach(dlg_win.y1_entry, 1, 1, 1, 1)
    label = Gtk.Label(label="y2 = ")
    label.set_halign(Gtk.Align.START)
    label.set_valign(Gtk.Align.CENTER)
    label.get_style_context().add_class("y2")
    grid.attach(label, 0, 2, 1, 1)
    grid.attach(dlg_win.y2_entry, 1, 2, 1, 1)
    label = Gtk.Label(label="y3 = ")
    label.set_halign(Gtk.Align.START)
    label.set_valign(Gtk.Align.CENTER)
    label.get_style_context().add_class("y3")
    grid.attach(label, 0, 3, 1, 1)
    grid.attach(dlg_win.y3_entry, 1, 3, 1, 1)

    dlg_win.add(grid)
    dlg_win.show_all()


def zoom_in(widget, event=None):
    "Narrow the plotted section by half"
    center_x = (graph.x_min + graph.x_max) / 2
    center_y = (graph.y_min + graph.y_max) / 2
    range_x = (graph.x_max - graph.x_min)
    range_y = (graph.y_max - graph.y_min)

    graph.x_min = center_x - (range_x / 4)
    graph.x_max = center_x + (range_x / 4)
    graph.y_min = center_y - (range_y / 4)
    graph.y_max = center_y +(range_y / 4)

    parameter_entries_repopulate()
    graph.plot()


def zoom_out(widget, event=None):
    "Double the plotted section"
    center_x = (graph.x_min + graph.x_max) / 2
    center_y = (graph.y_min + graph.y_max) / 2
    range_x = (graph.x_max - graph.x_min)
    range_y = (graph.y_max - graph.y_min)

    graph.x_min = center_x - (range_x)
    graph.x_max = center_x + (range_x)
    graph.y_min = center_y - (range_y)
    graph.y_max = center_y +(range_y)

    parameter_entries_repopulate()
    graph.plot()


def zoom_reset(widget, event=None):
    "Set the range back to the user's input"

    graph.x_min = eval(x_min,{"__builtins__":{}},safe_dict)
    graph.y_min = eval(y_min,{"__builtins__":{}},safe_dict)
    graph.x_max = eval(x_max,{"__builtins__":{}},safe_dict)
    graph.y_max = eval(y_max,{"__builtins__":{}},safe_dict)
    parameter_entries_populate()
    graph.plot()


def scale_dec(widget, event=None):
    graph.scale_style = "dec"
    app_win.scale_grid.hide()
    plot(None)


def scale_rad(widget, event=None):
    graph.scale_style = "rad"
    app_win.scale_grid.hide()
    plot(None)


def scale_rad_tau(widget, event=None):
    graph.scale_style = "tau"
    app_win.scale_grid.hide()
    plot(None)


def scale_cust(widget, event=None):
    graph.scale_style = "cust"
    app_win.scale_grid.show()
    plot(None)


def toggle_connect(widget, event=None):
    "Toggle between a graph that connects points with lines and one that does not"

    global connect_points
    connect_points = not connect_points
    graph.plot()


def save(widget, event=None):
    "Save graph as .png"

    file_dialog = Gtk.FileChooserDialog(_("Save as..."), app_win, Gtk.FileChooserAction.SAVE, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
    file_dialog.set_default_response(Gtk.ResponseType.OK)
    filter = Gtk.FileFilter()
    filter.add_mime_type("image/png")
    filter.add_pattern("*.png")
    file_dialog.add_filter(filter)
    file_dialog.set_filename("FunctionGraph.png")

    response = file_dialog.run()
    if response == Gtk.ResponseType.OK:
        width = graph.drawing_area.get_allocated_width()
        height = graph.drawing_area.get_allocated_height()
        pix_buffer = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, False, 8, width, height)
        pix_buffer.get_from_drawable(graph.pix_map, graph.pix_map.get_colormap(), 0, 0, 0, 0, width, height)
        pix_buffer.save(file_dialog.get_filename(), "png")
    file_dialog.destroy()

def set_statusbar(text):
    app_win.status_bar.remove_all(0)
    app_win.status_bar.push(0, text)

def quit_dlg(widget, event=None):
    global config
    width, height = app_win.get_size()
    config["MainWindow"]["width"] = str(width)
    config["MainWindow"]["height"] = str(height)
    x, y = app_win.get_position()
    config["MainWindow"]["x"] = str(x)
    config["MainWindow"]["y"] = str(y)
    with open(configFile, "w") as file:
        config.write(file)
    app_win.destroy()


def show_yelp(widget):
    try:
        import os
        os.system("yelp doc/lybniz.xml")
        #os.system("yelp /usr/share/gnome/help/lybniz/C/lybniz.xml")
        #Gtk.show_uri(None, "lybniz", 0)
    except:
        print ("Can't Show help")


def show_about_dialog(widget):
    about_dialog = Gtk.AboutDialog(transient_for=app_win, modal=True)
    about_dialog.set_program_name("Lybniz")
    about_dialog.set_version(str(app_version))
    about_dialog.set_authors(["Thomas Führinger","Sam Tygier"])
    about_dialog.set_comments(_("Function Graph Plotter"))
    about_dialog.set_license("BSD")
    about_dialog.set_website("https://github.com/thomasfuhringer/lybniz")
    about_dialog.set_logo(lybniz_icon)
    about_dialog.connect ("response", lambda d, r: d.destroy())
    about_dialog.present()


def parameter_entries_create():
    # create text entries for parameters

    app_win.y1_entry = Gtk.Entry()
    app_win.y1_entry.set_size_request(300, 24)
    app_win.y1_entry.set_hexpand(True)
    app_win.y2_entry = Gtk.Entry()
    app_win.y3_entry = Gtk.Entry()
    app_win.y3_entry.set_size_request(300, 24)
    app_win.x_min_entry = Gtk.Entry()
    app_win.x_min_entry.set_width_chars(3)
    app_win.x_min_entry.set_size_request(140, 24)
    app_win.x_min_entry.set_alignment(xalign=1)
    app_win.x_max_entry = Gtk.Entry()
    app_win.x_max_entry.set_width_chars(3)
    app_win.x_max_entry.set_size_request(140, 24)
    app_win.x_max_entry.set_alignment(xalign=1)
    app_win.x_scale_entry = Gtk.Entry()
    app_win.x_scale_entry.set_width_chars(3)
    app_win.x_scale_entry.set_size_request(140, 24)
    app_win.x_scale_entry.set_alignment(xalign=1)
    app_win.y_min_entry = Gtk.Entry()
    app_win.y_min_entry.set_width_chars(3)
    app_win.y_min_entry.set_size_request(140, 24)
    app_win.y_min_entry.set_alignment(xalign=1)
    app_win.y_max_entry = Gtk.Entry()
    app_win.y_max_entry.set_width_chars(3)
    app_win.y_max_entry.set_size_request(140, 24)
    app_win.y_max_entry.set_alignment(xalign=1)
    app_win.y_scale_entry = Gtk.Entry()
    app_win.y_scale_entry.set_width_chars(3)
    app_win.y_scale_entry.set_size_request(140, 24)
    app_win.y_scale_entry.set_alignment(xalign=1)

    parameter_entries_populate()

    app_win.y1_entry.connect("key-press-event", key_press_plot)
    app_win.y2_entry.connect("key-press-event", key_press_plot)
    app_win.y3_entry.connect("key-press-event", key_press_plot)
    app_win.x_min_entry.connect("key-press-event", key_press_plot)
    app_win.y_min_entry.connect("key-press-event", key_press_plot)
    app_win.x_max_entry.connect("key-press-event", key_press_plot)
    app_win.y_max_entry.connect("key-press-event", key_press_plot)
    app_win.x_scale_entry.connect("key-press-event", key_press_plot)
    app_win.y_scale_entry.connect("key-press-event", key_press_plot)

    app_win.scale_grid = Gtk.Grid()
    app_win.scale_grid.set_property("column-spacing", 10)

    grid = Gtk.Grid()
    grid.set_property("row-spacing", 2)
    grid.set_property("column-spacing", 10)
    grid.set_border_width(6)

    label = Gtk.Label(label="y1 = ")
    label.set_valign(Gtk.Align.CENTER)
    label.set_halign(Gtk.Align.START)
    label.get_style_context().add_class("y1")
    grid.add(label)
    grid.attach(app_win.y1_entry, 1, 0, 1, 1)
    label = Gtk.Label(label=_("X min"))
    label.set_valign(Gtk.Align.CENTER)
    label.set_halign(Gtk.Align.START)
    grid.attach(label, 2, 0, 1, 1)
    grid.attach(app_win.x_min_entry, 3, 0, 1, 1)
    label = Gtk.Label(label=_("Y min"))
    label.set_valign(Gtk.Align.CENTER)
    label.set_halign(Gtk.Align.START)
    grid.attach(label, 4, 0, 1, 1)
    grid.attach(app_win.y_min_entry, 5, 0, 1, 1)

    label = Gtk.Label(label="y2 = ")
    label.set_valign(Gtk.Align.CENTER)
    label.get_style_context().add_class("y2")
    grid.attach(label, 0, 1, 1, 1)
    grid.attach(app_win.y2_entry, 1, 1, 1, 1)

    label = Gtk.Label(label=_("X max"))
    label.set_valign(Gtk.Align.CENTER)
    label.set_halign(Gtk.Align.START)
    grid.attach(label, 2, 1, 1, 1)
    grid.attach(app_win.x_max_entry, 3, 1, 1, 1)

    label = Gtk.Label(label=_("Y max"))
    label.set_valign(Gtk.Align.CENTER)
    label.set_halign(Gtk.Align.START)
    grid.attach(label, 4, 1, 1, 1)
    grid.attach(app_win.y_max_entry, 5, 1, 1, 1)

    label = Gtk.Label(label="y3 = ")
    label.set_valign(Gtk.Align.CENTER)
    label.get_style_context().add_class("y3")
    grid.attach(label, 0, 2, 1, 1)
    grid.attach(app_win.y3_entry, 1, 2, 1, 1)

    label = Gtk.Label(label=_("X scale"))
    label.set_valign(Gtk.Align.CENTER)
    app_win.scale_grid.add(label)

    app_win.scale_grid.attach(app_win.x_scale_entry, 1, 0, 1, 1)
    label = Gtk.Label(label=_("Y scale"))
    label.set_valign(Gtk.Align.CENTER)
    app_win.scale_grid.attach(label, 2, 0, 1, 1)
    app_win.scale_grid.attach(app_win.y_scale_entry, 3, 0, 1, 1)
    grid.attach(app_win.scale_grid, 2, 2, 4, 1)
    return grid


def parameter_entries_populate():
    # set text in entries for parameters with user's input

    app_win.y1_entry.set_text(y1)
    app_win.y2_entry.set_text(y2)
    app_win.y3_entry.set_text(y3)
    app_win.x_min_entry.set_text(x_min)
    app_win.x_max_entry.set_text(x_max)
    app_win.x_scale_entry.set_text(x_scale)
    app_win.y_min_entry.set_text(y_min)
    app_win.y_max_entry.set_text(y_max)
    app_win.y_scale_entry.set_text(y_scale)


def parameter_entries_repopulate():
    # set text in entries for parameters

    app_win.y1_entry.set_text(y1)
    app_win.y2_entry.set_text(y2)
    app_win.y3_entry.set_text(y3)
    app_win.x_min_entry.set_text(str(graph.x_min))
    app_win.x_max_entry.set_text(str(graph.x_max))
    app_win.x_scale_entry.set_text(str(graph.x_scale))
    app_win.y_min_entry.set_text(str(graph.y_min))
    app_win.y_max_entry.set_text(str(graph.y_max))
    app_win.y_scale_entry.set_text(str(graph.y_scale))


def key_press_plot(widget, event):
    if event.keyval == 65293:
        plot(None)
        return True
    else:
        return False


class LybnizApp(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, application_id="apps.lybniz", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)

    def on_activate(self, data=None):
        global app_win, graph, config

        style_provider = Gtk.CssProvider ()

        css = """
        button, entry, label {
            padding-top: 0px;
            padding-bottom: 0px;
            min-height: 20px;
            min-width: 12px;
        }
        entry {
            padding-left: 5px;
            padding-right: 5px;
        }
        toolbar, statusbar {
            margin-left: 0px;
            margin-top: 0px;
            margin-bottom: 0px;
            padding-left: 0px;
            padding-top: 0px;
            padding-bottom: 0px;
            min-height: 10px;
        }
        label.y1 {
            color: blue;
        }
        label.y2 {
            color: red;
        }
        label.y3 {
            color: green;
        }
        """

        style_provider.load_from_data(css.encode());
        Gtk.StyleContext.add_provider_for_screen (Gdk.Screen.get_default(), style_provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION);

        app_win = Gtk.ApplicationWindow(application=self, title="Lybniz")
        app_win.connect("delete-event", quit_dlg)
        app_win.set_icon(lybniz_icon)

        if config.read([configFile, ]) == []:
            config.add_section("MainWindow")

        app_win.set_default_size(800, 600)
        if config.has_option("MainWindow", "width"):
            app_win.resize(config.getint("MainWindow", "width"), config.getint("MainWindow", "height"))
        if config.has_option("MainWindow", "x"):
            app_win.move(config.getint("MainWindow", "x"), config.getint("MainWindow", "y"))
        else:
            app_win.set_position(Gtk.WindowPosition.CENTER)

        app_win.accel_group = Gtk.AccelGroup()
        app_win.add_accel_group(app_win.accel_group)

        app_win.v_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        #app_win.v_box.set_border_width(1)

        menu_toolbar_create()
        app_win.v_box.pack_start(app_win.menu_main, False, False, 0)
        app_win.v_box.pack_start(app_win.tool_bar, False, False, 0)

        app_win.v_box.pack_start(parameter_entries_create(), False, False, 4)

        graph = GraphClass()
        app_win.v_box.pack_start(graph.drawing_area, True, True, 0)

        app_win.status_bar = Gtk.Statusbar()
        app_win.status_bar.set_margin_top(0)
        app_win.status_bar.set_margin_bottom(0)
        app_win.v_box.pack_start(app_win.status_bar, False, False, 0)

        app_win.add(app_win.v_box)
        app_win.show_all()
        app_win.scale_grid.hide()
        self.add_window(app_win)

lybniz_icon = GdkPixbuf.Pixbuf.new_from_xpm_data((
"64 64 231 2",
"  	c None",
"! 	c black",
"# 	c #393D39",
"$ 	c #364336",
"% 	c #384336",
"& 	c #364436",
"' 	c #237A21",
"( 	c #1A9218",
") 	c #334D32",
"* 	c #374237",
"+ 	c #383D38",
", 	c #384137",
"- 	c #199417",
". 	c #04CE00",
"0 	c #04CF00",
"1 	c #247623",
"2 	c #364236",
"3 	c #384237",
"4 	c #2E5A2D",
"5 	c #0BBC07",
"6 	c #06CA02",
"7 	c #324E32",
"8 	c #3A3D3A",
"9 	c #394039",
": 	c #384138",
"; 	c #393C39",
"< 	c #384038",
"= 	c #344A34",
"> 	c #3A3A3A",
"? 	c #383F38",
"@ 	c #1D891B",
"A 	c #03C200",
"B 	c #027E00",
"C 	c #0A5509",
"D 	c #027900",
"E 	c #03BD00",
"F 	c #12A80F",
"G 	c #227C20",
"H 	c #0CBA08",
"I 	c #05CB01",
"J 	c #179C14",
"K 	c #2F592F",
"L 	c #383B38",
"M 	c #169E13",
"N 	c #0B4A0A",
"O 	c #3E463E",
"P 	c #8F8F8F",
"Q 	c #484F48",
"R 	c #0C370C",
"S 	c #05CD01",
"T 	c #1F861D",
"U 	c #07C604",
"V 	c #0FAF0C",
"W 	c #374336",
"X 	c #11AA0E",
"Y 	c #03CC00",
"Z 	c #0B220B",
"[ 	c #929292",
"] 	c #EDEDED",
"^ 	c #A6A6A6",
"_ 	c #091509",
"` 	c #03C500",
"a 	c #257324",
"b 	c #383A38",
"c 	c #374337",
"d 	c #315330",
"e 	c #0ABD07",
"f 	c #0CB909",
"g 	c #364735",
"h 	c #393E39",
"i 	c #374137",
"j 	c #13A510",
"k 	c #03A300",
"l 	c #0F3A0F",
"m 	c #070D07",
"n 	c #103510",
"o 	c #039701",
"p 	c #13A610",
"q 	c #384236",
"r 	c #257424",
"s 	c #05CB02",
"t 	c #344B33",
"u 	c #315530",
"v 	c #131313",
"w 	c #189816",
"x 	c #2B6728",
"y 	c #12A90F",
"z 	c #286E26",
"{ 	c #363E36",
"| 	c #14A311",
"} 	c #1C8C1A",
"~ 	c #374236",
" !	c #384633",
"!!	c #247B1F",
"#!	c #364536",
"$!	c #2F572F",
"%!	c #FF0000",
"&!	c #D60C0C",
"'!	c #7D2824",
"(!	c #3D3F34",
")!	c #364435",
"*!	c #237922",
"+!	c #11AC0E",
",!	c #393D38",
"-!	c #169D14",
".!	c #2A6629",
"0!	c #090909",
"1!	c #1C1E1C",
"2!	c #313B31",
"3!	c #1D861B",
"4!	c #2E4E2D",
"5!	c #0E0E0E",
"6!	c #000200",
"7!	c #000300",
"8!	c #000400",
"9!	c #010101",
":!	c #111111",
";!	c #293529",
"<!	c #314931",
"=!	c #0EB40A",
">!	c #247122",
"?!	c #1F221F",
"@!	c #060606",
"A!	c #353D35",
"B!	c #227920",
"C!	c #1C1D1C",
"D!	c #161716",
"E!	c #344234",
"F!	c #0BBD07",
"G!	c #0BBB08",
"H!	c #353C35",
"I!	c #030303",
"J!	c #212721",
"K!	c #1E851C",
"L!	c #15A012",
"M!	c #2A352A",
"N!	c #1A1C1A",
"O!	c #314831",
"P!	c #08C404",
"Q!	c #276326",
"R!	c #191B19",
"S!	c #0D0D0D",
"T!	c #1A1A1A",
"U!	c #202020",
"V!	c #334832",
"W!	c #08C305",
"X!	c #373C37",
"Y!	c #181818",
"Z!	c #191919",
"[!	c #020302",
"]!	c #010601",
"^!	c #000900",
"_!	c #000800",
"`!	c #000600",
"a!	c #010201",
"b!	c #121212",
"c!	c #2A2E2A",
"d!	c #2A5F29",
"e!	c #0FB20B",
"f!	c #343C34",
"g!	c #171717",
"h!	c #303030",
"i!	c #2F2F2F",
"j!	c #2E2E2E",
"k!	c #364136",
"l!	c #0EB50A",
"m!	c #344833",
"n!	c #313131",
"o!	c #2D2D2D",
"p!	c #2C2C2C",
"q!	c #2A6229",
"r!	c #09C105",
"s!	c #354435",
"t!	c #333333",
"u!	c #2B2B2B",
"v!	c #354035",
"w!	c #179915",
"x!	c #30512F",
"y!	c #1E861C",
"z!	c #267025",
"{!	c #30572F",
"|!	c #30552F",
"}!	c #373F37",
"~!	c #325031",
" #	c #374037",
"!#	c #324F32",
"##	c #266F25",
"$#	c #2B632A",
"%#	c #0FB10C",
"&#	c #0ABF06",
"'#	c #1C8E19",
"(#	c #384238",
")#	c #179A15",
"*#	c #1B9118",
"+#	c #2E5C2D",
",#	c #286A27",
"-#	c #3B3B3B",
".#	c #2E5B2D",
"0#	c #2B6529",
"1#	c #374437",
"2#	c #07C603",
"3#	c #314C30",
"4#	c #374537",
"5#	c #1A9317",
"6#	c #2A322A",
"7#	c #325231",
"8#	c #296927",
"9#	c #21821E",
":#	c #11AB0E",
";#	c #169C14",
"<#	c #354535",
"=#	c #393B39",
">#	c #2A6828",
"?#	c #08C504",
"@#	c #0FB00C",
"A#	c #374436",
"B#	c #383E38",
"C#	c #0AC006",
"D#	c #276E26",
"E#	c #1F831D",
"F#	c #06C903",
"G#	c #1F851D",
"H#	c #05CC01",
"I#	c #2B652A",
"J#	c #2F582E",
"K#	c #296728",
"L#	c #393939",
"M#	c #30562F",
"N#	c #07C803",
"O#	c #199616",
"P#	c #354834",
"                                                            ! ! ! !                                                             ",
"                                                            ! ! ! !                                                             ",
"                                                            ! ! ! !                                                             ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                        # $                                 ! ! ! ! !                                                           ",
"                    % & ' ( ) *                             ! ! ! ! !                                                           ",
"                + , - . 0 0 . 1 2                           ! ! ! ! !                                                           ",
"              3 4 5 0 0 0 0 0 6 7 8                         ! ! ! ! !               9 : ; < = * $ >                             ",
"            ? @ . 0 A B C D E 0 F &                         ! ! ! ! !           : , G H I 0 0 I J K ? L                         ",
"          < M 0 0 0 N O P Q R 0 S *                         ! ! ! ! !       + * T U 0 0 0 0 0 0 0 0 V W ;                       ",
"        * X 0 0 0 Y Z [ ] ^ _ ` 0 a b                       ! ! ! ! !     c d e 0 0 0 0 0 0 0 0 0 0 0 f g h                     ",
"      i j 0 0 0 0 0 k l m n o 0 0 p &                       ! ! ! ! !   q r s 0 0 0 0 0 0 0 0 0 0 0 0 0 e t +                   ",
"    > u 0 0 0 0 0 0 0 0 0 0 0 0 0 S :                       ! ! ! ! v < w 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 f ?                   ",
"      , x y . 0 0 0 0 0 0 0 0 0 0 0 z >                     ! ! ! ! { | 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 } *                 ",
"        ; ~  !!!V 0 0 0 0 0 0 0 0 0 | #!                    ! ! ! ! p 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 . $!;               ",
"      %!%!%!&!'!(!)!*!+!. 0 0 0 0 0 6 ,!                    ! ! ! ! 0 0 0 0 0 0 0 0 0 6 -!.!( S 0 0 0 0 0 0 0 f ?               ",
"  ! ! ! ! ! ! ! ! 0!1!2!3!0 0 0 0 0 0 4!5!! ! ! ! ! ! ! ! ! ! ! ! ! 6!7!7!8!8!8!8!8!8!9!9!:!;!<!=!0 0 0 0 0 0 0 >!?!! ! ! ! !   ",
"  ! ! ! ! ! ! ! ! ! ! @!A!e 0 0 0 0 0 B!C!! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! D!E!F!0 0 0 0 0 0 G!H!I!! ! ! !   ",
"  ! ! ! ! ! ! ! ! ! ! ! J!K!0 0 0 0 0 L!M!! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! N!O!P!0 0 0 0 0 0 Q!R!! ! ! !   ",
"  ! S!T!T!T!T!T!T!T!T!T!U!V!0 0 0 0 0 W!X!Y!Z!Z!5!9!9!9![!]!! ! ! ! ^!_!_!_!_!`!a!9!! ! ! b!Y!Y!Y!c!d!0 0 0 0 0 0 e!f!Y!Y!g!g!h!",
"      i!i!i!i!i!i!j!j!j!h!k!l!0 0 0 0 0 m!n!j!j!o!o!p!f!q!S ! ! ! ! 0 0 0 0 r!s!t!p!p!p!p!p!p!u!u!u!v!w!0 0 0 0 0 0 x!h!u!u!u!i!",
"                          : y!0 0 0 0 0 z!>         < {!6 0 ! ! ! ! 0 0 0 s |!<                       i r!0 0 0 0 0 K!}!        ",
"                            ~!0 0 0 0 0 | $        #!#P!0 0 ! ! ! ! 0 0 0 ##k!                        < $#0 0 0 0 0 %#$         ",
"                            ? &#0 0 0 0 S &     i !#W!0 0 0 ! ! ! ! 0 0 '#(#                            i )#0 0 0 0 . i         ",
"                            $ *#0 0 0 0 0 - ? 3 +#W!0 0 0 0 ! ! ! ! 0 F :                                 * r!0 0 0 0 ,#-#      ",
"                              .#0 0 0 0 0 0 F F 0 0 0 0 0 0 ! ! ! ! G!*                                   : 0#0 0 0 0 )#1#      ",
"                              ? 2#0 0 0 0 0 0 0 0 0 0 0 0 0 ! ! ! ! 3#+                                     (#J 0 0 0 W!h       ",
"                              4#5#0 0 0 0 0 0 0 0 0 0 0 0 0 ! ! ! ! 6#                                        * W!0 0 0 7#      ",
"                                !#0 0 0 0 0 0 0 0 0 0 0 0 0 ! ! ! ! 9!                                        : 8#0 0 0 9#h     ",
"                                (#:#0 0 0 0 0 0 0 0 0 0 0 0 ! ! ! ! !                                           , L!0 0 ;#<#    ",
"                                =#>#0 0 0 0 0 0 0 0 0 0 0 0 ! ! ! ! !                                             & ?#0 @#A#    ",
"                                  B#C#0 0 0 0 0 0 0 0 0 0 e ! ! ! ! !                                             (#D#0 W!?     ",
"                                  i E#0 0 0 0 0 0 0 0 0 F#~!! ! ! ! !                                               , G#W!?     ",
"                                    A#H#0 0 0 0 0 0 0 . I#* ! ! ! ! !                                                 i J#i     ",
"                                    * } 0 0 0 0 0 0 6 K#*   ! ! ! ! !                                                   L#      ",
"                                      < X 0 0 0 0 W!M#*     ! ! ! ! !                                                           ",
"                                        A#L!S N#O#P# #      ! ! ! ! !                                                           ",
"                                        L#$ #!? 1#          ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                            ! ! ! ! !                                                           ",
"                                                                  ! !                                                           "))

if __name__ == "__main__":
    app = LybnizApp()
    app.run(sys.argv)

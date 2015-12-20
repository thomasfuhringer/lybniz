#!/usr/bin/env python
# -*- coding: UTF-8 -*-

""" 
	Simple Function graph Plotter
	© Thomas Führinger, Sam Tygier 2005-2015
	http://github.com/thomasfuhringer/lybniz
	
	Version 1.3.3
	Requires PyGtk 2.6	
	Released under the terms of the revised BSD license
	Modified: 2015-12-20
"""

from __future__ import division
import gtk, pango
import sys
import math
from math import *

app_version = "1.3.3"

try:
	import gnome
	props = {gnome.PARAM_APP_DATADIR : '/usr/share'}
	prog = gnome.program_init("lybniz", str(app_version), properties=props)
except:
	print "Gnome not found"


import gettext
gettext.install('lybniz')

# profiling
enable_profiling = False
if enable_profiling:
	from time import time

app_win = None
actions = gtk.ActionGroup("General")
graph = None
connect_points = True

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

icon_file = "/usr/share/pixmaps/lybniz.png"

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

def marks(min_val,max_val,minor=1):
	"yield positions of scale marks between min and max. For making minor marks, set minor to the number of minors you want between majors"
	try:
		min_val = float(min_val)
		max_val = float(max_val)
	except:
		print "needs 2 numbers"
		raise ValueError

	if(min_val >= max_val):
		print "min bigger or equal to max"
		raise ValueError		

	a = 0.2 # tweakable control for when to switch scales
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
		# Create backing pixmap of the appropriate size
		def configure_event(widget, event):
			x, y, w, h = widget.get_allocation()
			self.pix_map = gtk.gdk.Pixmap(widget.window, w, h)
			
			# make colors
			self.gc = dict()
			for name, color in (('black',(0,0,0)),('red',(32000,0,0)),('blue',(0,0,32000)),('green',(0,32000,0))):
				self.gc[name] =self.pix_map.new_gc()
				self.gc[name].set_rgb_fg_color(gtk.gdk.Color(red=color[0],green=color[1],blue=color[2]))
			self.layout = pango.Layout(widget.create_pango_context())
			self.canvas_width = w
			self.canvas_height = h
			self.x_max = eval(x_max,{"__builtins__":{}},safe_dict)
			self.x_min = eval(x_min,{"__builtins__":{}},safe_dict)
			self.x_scale = eval(x_scale,{"__builtins__":{}},safe_dict)
			self.y_max = eval(y_max,{"__builtins__":{}},safe_dict)
			self.y_min = eval(y_min,{"__builtins__":{}},safe_dict)
			self.y_scale = eval(y_scale,{"__builtins__":{}},safe_dict)
			self.plot()
			return True

		# Redraw the screen from the backing pixmap
		def expose_event(widget, event):
			x, y, w, h = event.area
			widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL], self.pix_map, x, y, x, y, w, h)
			return False

		# Start marking selection
		def button_press_event(widget, event):
			global x_sel, y_sel
			
			if event.button == 1:
				self.selection[0][0], self.selection[0][1] = int(event.x), int(event.y)
				self.selection[1][0], self.selection[1][1] = None, None

		# End of selection
		def button_release_event(widget, event):
			
			if event.button == 1 and event.x != self.selection[0][0] and event.y != self.selection[0][1]:
				xmi, ymi = min(self.graph_x(self.selection[0][0]), self.graph_x(event.x)), min(self.graph_y(self.selection[0][1]), self.graph_y(event.y))
				xma, yma = max(self.graph_x(self.selection[0][0]), self.graph_x(event.x)), max(self.graph_y(self.selection[0][1]), self.graph_y(event.y))
				self.x_min, self.y_min, self.x_max, self.y_max = xmi, ymi, xma, yma
				parameter_entries_repopulate()
				graph.plot()
				self.selection[1][0] = None
				self.selection[0][0] = None

		# Draw rectangle during mouse movement
		def motion_notify_event(widget, event):
			
			if event.is_hint:
				x, y, state = event.window.get_pointer()
			else:
				x = event.x
				y = event.y
				state = event.state

			if state & gtk.gdk.BUTTON1_MASK and self.selection[0][0] is not None:
				gc = self.drawing_area.get_style().black_gc
				gc.set_function(gtk.gdk.INVERT)
				if self.selection[1][0] is not None:
					x0 = min(self.selection[1][0], self.selection[0][0])
					y0 = min(self.selection[1][1], self.selection[0][1])
					w = abs(self.selection[1][0] - self.selection[0][0])
					h = abs(self.selection[1][1] - self.selection[0][1])
					self.pix_map.draw_rectangle(gc, False, x0, y0, w, h)
				x0 = min(self.selection[0][0], int(x))
				y0 = min(self.selection[0][1], int(y))
				w = abs(int(x) - self.selection[0][0])
				h = abs(int(y) - self.selection[0][1])
				self.pix_map.draw_rectangle(gc, False, x0, y0, w, h)
				self.selection[1][0], self.selection[1][1] = int(x), int(y)
				self.draw_drawable()
				
		self.prev_y = [None, None, None]
		
		# Marked area point[0, 1][x, y]
		self.selection = [[None, None], [None, None]]
		
		self.drawing_area = gtk.DrawingArea()		
		self.drawing_area.connect("expose_event", expose_event)
		self.drawing_area.connect("configure_event", configure_event)
		self.drawing_area.connect("button_press_event", button_press_event)
		self.drawing_area.connect("button_release_event", button_release_event)
		self.drawing_area.connect("motion_notify_event", motion_notify_event)
		self.drawing_area.set_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.LEAVE_NOTIFY_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK |gtk.gdk.POINTER_MOTION_HINT_MASK)
		self.scale_style = "dec"
		
	def draw_drawable(self):
		x, y, w, h = self.drawing_area.get_allocation()
		self.drawing_area.window.draw_drawable(self.drawing_area.get_style().fg_gc[gtk.STATE_NORMAL], self.pix_map, 0, 0, 0, 0, w, h)
		
	def plot(self):
		self.pix_map.draw_rectangle(self.drawing_area.get_style().white_gc, True, 0, 0, self.canvas_width, self.canvas_height)
				
		if (self.scale_style == "cust"):
			
			#draw cross
			self.pix_map.draw_lines(self.gc['black'], [(int(round(self.canvas_x(0))),0),(int(round(self.canvas_x(0))),self.canvas_height)])
			self.pix_map.draw_lines(self.gc['black'], [(0,int(round(self.canvas_y(0)))),(self.canvas_width,int(round(self.canvas_y(0))))])
			# old style axis marks
			iv = self.x_scale * self.canvas_width / (self.x_max - self.x_min) # pixel interval between marks
			os = self.canvas_x(0) % iv # pixel offset of first mark 
			# loop over each mark.
			for i in xrange(int(self.canvas_width / iv + 1)):
				#multiples of iv, cause adding of any error in iv, so keep iv as float
				# use round(), to get to closest pixel, int() to prevent warning
				self.pix_map.draw_lines(self.gc['black'], [(int(round(os + i * iv)), int(round(self.canvas_y(0) - 5))), (int(round(os + i * iv)), int(round(self.canvas_y(0) + 5)))])
			
			# and the y-axis
			iv = self.y_scale * self.canvas_height / (self.y_max - self.y_min)
			os = self.canvas_y(0) % iv
			for i in xrange(int(self.canvas_height / iv + 1)):
				self.pix_map.draw_lines(self.gc['black'], [(int(round(self.canvas_x(0) - 5)), int(round(i * iv + os))), (int(round(self.canvas_x(0) + 5)), int(round(i * iv + os)))])			
		
		else:
			#new style
			factor = 1
			if (self.scale_style == "rad"): factor = pi

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
			self.pix_map.draw_lines(self.gc['black'], [(center_x_pix,0),(center_x_pix,self.canvas_height)])
			self.pix_map.draw_lines(self.gc['black'], [(0,center_y_pix),(self.canvas_width,center_y_pix)])			
				
			for i in marks(self.x_min / factor, self.x_max / factor):
				label = '%g' % i
				if (self.scale_style == "rad"): label += '\xCF\x80'
				i = i * factor

				self.pix_map.draw_lines(self.gc['black'], [(int(round(self.canvas_x(i))), center_y_pix - 5), (int(round(self.canvas_x(i))), center_y_pix + 5)])
				
				self.layout.set_text(label)
				extents = self.layout.get_pixel_extents()[1]
				if (numbers_y_pos < 0): adjust = extents[3]
				else: adjust = 0
				self.pix_map.draw_layout(self.gc['black'],int(round(self.canvas_x(i))), center_y_pix + numbers_y_pos - adjust,self.layout)

			for i in marks(self.y_min,self.y_max):
				label = '%g' % i

				self.pix_map.draw_lines(self.gc['black'], [(center_x_pix - 5, int(round(self.canvas_y(i)))), (center_x_pix + 5, int(round(self.canvas_y(i))))])
				
				self.layout.set_text(label)
				extents = self.layout.get_pixel_extents()[1]
				if (numbers_x_pos < 0): adjust = extents[2]
				else: adjust = 0
				self.pix_map.draw_layout(self.gc['black'],center_x_pix +numbers_x_pos - adjust,int(round(self.canvas_y(i))),self.layout)

			# minor marks
			for i in marks(self.x_min / factor, self.x_max / factor, minor=10):
				i = i * factor
				self.pix_map.draw_lines(self.gc['black'], [(int(round(self.canvas_x(i))), center_y_pix - 2), (int(round(self.canvas_x(i))), center_y_pix +2)])

			for i in marks(self.y_min, self.y_max, minor=10):
				label = '%g' % i
				self.pix_map.draw_lines(self.gc['black'], [(center_x_pix - 2, int(round(self.canvas_y(i)))), (center_x_pix +2, int(round(self.canvas_y(i))))])
				
		plots = []
		# precompile the functions
		invalid_input = False
		if y1:
			try:
				compiled_y1 = compile(y1.replace("^","**"),"",'eval')
				plots.append((compiled_y1,0,self.gc['blue']))
			except:
				set_statusbar("Invalid function")
				invalid_input = True
				compiled_y1 = None
		else:
			compiled_y1 = None
			
		if y2:
			try:
				compiled_y2 = compile(y2.replace("^","**"),"",'eval')
				plots.append((compiled_y2,1,self.gc['red']))
			except:
				set_statusbar("Invalid function")
				invalid_input = True
				compiled_y2 = None
		else:
			compiled_y2 = None
		
		if y3:	
			try:
				compiled_y3 = compile(y3.replace("^","**"),"",'eval')
				plots.append((compiled_y3,2,self.gc['green']))
			except:
				set_statusbar("Invalid function")
				invalid_input = True
				compiled_y3 = None
		else:
			compiled_y3 = None
		
		self.prev_y = [None, None, None]
		
		if enable_profiling:
			start_graph = time()

		if len(plots) != 0:
			for i in xrange(0,self.canvas_width,x_res):
				x = self.graph_x(i + 1)
				for e in plots:
					safe_dict['x']=x
					try:
						y = eval(e[0],{"__builtins__":{"max": max, "min": min}},safe_dict)
						y_c = int(round(self.canvas_y(y)))
						
						if y_c < 0 or y_c > self.canvas_height:
							break
						
						if connect_points and self.prev_y[e[1]] is not None:
							self.pix_map.draw_lines(e[2], [(i, self.prev_y[e[1]]), (i + x_res, y_c)])
						else:
							self.pix_map.draw_points(e[2], [(i + x_res, y_c)])
						self.prev_y[e[1]] = y_c
					except:
						#print "Error at %d: %s" % (x, sys.exc_value)
						set_statusbar("Invalid function")
						invalid_input = True
						self.prev_y[e[1]] = None
					
		if enable_profiling:
			print "Time to draw graph:", (time() - start_graph) * 1000, "ms"

		if not invalid_input:
			set_statusbar("")
			
		self.draw_drawable()
		
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

	app_win.menu_main = gtk.MenuBar()
	
	menu_file = gtk.Menu()	
	menu_item_file = gtk.MenuItem(_("_File"))
	menu_item_file.set_submenu(menu_file)
	
	actions.save = gtk.Action("Save", _("_Save"), _("Save graph as bitmap"), gtk.STOCK_SAVE)
	actions.save.connect ("activate", save)
	actions.add_action(actions.save)
	menu_item_save = actions.save.create_menu_item()
	menu_item_save.add_accelerator("activate", app_win.accel_group, ord("S"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	menu_file.append(menu_item_save)
	
	actions.quit = gtk.Action("Quit", _("_Quit"), _("Quit Application"), gtk.STOCK_QUIT)
	actions.quit.connect ("activate", quit_dlg)
	actions.add_action(actions.quit)
	menuItem_quit = actions.quit.create_menu_item()
	menuItem_quit.add_accelerator("activate", app_win.accel_group, ord("Q"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	menu_file.append(menuItem_quit)
	
	menu_graph = gtk.Menu()	
	menu_item_graph = gtk.MenuItem(_("_Graph"))
	menu_item_graph.set_submenu(menu_graph)
	
	actions.plot = gtk.Action("Plot", _("P_lot"), _("Plot Functions"), gtk.STOCK_REFRESH)
	actions.plot.connect ("activate", plot)
	actions.add_action(actions.plot)
	menu_item_plot = actions.plot.create_menu_item()
	menu_item_plot.add_accelerator("activate", app_win.accel_group, ord("l"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	menu_graph.append(menu_item_plot)
	
	actions.evaluate = gtk.Action("Evaluate", _("_Evaluate"), _("Evaluate Functions"), gtk.STOCK_EXECUTE)
	actions.evaluate.connect ("activate", evaluate)
	actions.add_action(actions.evaluate)
	menu_item_evaluate = actions.evaluate.create_menu_item()
	menu_item_evaluate.add_accelerator("activate", app_win.accel_group, ord("e"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	menu_graph.append(menu_item_evaluate)
	
	actions.zoom_in = gtk.Action("zoom_in", _("Zoom _In"), _("Zoom In"), gtk.STOCK_ZOOM_IN)
	actions.zoom_in.connect ("activate", zoom_in)
	actions.add_action(actions.zoom_in)
	menu_item_zoomin = actions.zoom_in.create_menu_item()
	menu_item_zoomin.add_accelerator("activate", app_win.accel_group, ord("+"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	menu_graph.append(menu_item_zoomin)
	
	actions.zoom_out = gtk.Action("zoom_out", _("Zoom _Out"), _("Zoom Out"), gtk.STOCK_ZOOM_OUT)
	actions.zoom_out.connect ("activate", zoom_out)
	actions.add_action(actions.zoom_out)
	menu_item_zoomout = actions.zoom_out.create_menu_item()
	menu_item_zoomout.add_accelerator("activate", app_win.accel_group, ord("-"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	menu_graph.append(menu_item_zoomout)
	
	actions.zoom_reset = gtk.Action("zoom_reset", _("Zoom _Reset"), _("Zoom Reset"), gtk.STOCK_ZOOM_100)
	actions.zoom_reset.connect ("activate", zoom_reset)
	actions.add_action(actions.zoom_reset)
	menu_item_zoomreset = actions.zoom_reset.create_menu_item()
	menu_item_zoomreset.add_accelerator("activate", app_win.accel_group, ord("r"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	menu_graph.append(menu_item_zoomreset)
	
	menu_item_toggle_connect = gtk.CheckMenuItem(_("_Connect Points"))
	menu_item_toggle_connect.set_active(True)
	menu_item_toggle_connect.connect ("toggled", toggle_connect)
	menu_graph.append(menu_item_toggle_connect)
	
	menu_scale_style = gtk.Menu()
	menu_item_scale_style = gtk.MenuItem(_("Scale Style"))
	menu_item_scale_style.set_submenu(menu_scale_style)
	menu_graph.append(menu_item_scale_style)
	
	actions.dec = gtk.Action("Dec", _("Decimal"), _("Set style to decimal"),None)
	actions.dec.connect ("activate", scale_dec)
	actions.add_action(actions.dec)
	menu_item_dec = actions.dec.create_menu_item()
	menu_scale_style.append(menu_item_dec)
	
	actions.rad = gtk.Action("Rad", _("Radians"), _("Set style to radians"),None)
	actions.rad.connect ("activate", scale_rad)
	actions.add_action(actions.rad)
	menu_item_rad = actions.rad.create_menu_item()
	menu_scale_style.append(menu_item_rad)	
	
	actions.cust = gtk.Action("Cust", _("Custom"), _("Set style to custom"),None)
	actions.cust.connect ("activate", scale_cust)
	actions.add_action(actions.cust)
	menu_item_cust = actions.cust.create_menu_item()
	menu_scale_style.append(menu_item_cust)
	
	menu_help = gtk.Menu()
	menu_item_help = gtk.MenuItem(_("_Help"))
	menu_item_help.set_submenu(menu_help)

	actions.Help = gtk.Action("Help", _("_Contents"), _("Help Contents"), gtk.STOCK_HELP)
	actions.Help.connect ("activate", show_yelp)
	actions.add_action(actions.Help)
	menu_item_contents = actions.Help.create_menu_item()
	menu_item_contents.add_accelerator("activate", app_win.accel_group, gtk.gdk.keyval_from_name("F1"), 0, gtk.ACCEL_VISIBLE)
	menu_help.append(menu_item_contents)

	actions.about = gtk.Action("About", _("_About"), _("About Box"), gtk.STOCK_ABOUT)
	actions.about.connect ("activate", show_about_dialog)
	actions.add_action(actions.about)
	menu_item_about = actions.about.create_menu_item()
	menu_help.append(menu_item_about)
	
	app_win.menu_main.append(menu_item_file)
	app_win.menu_main.append(menu_item_graph)
	app_win.menu_main.append(menu_item_help)
	
	app_win.tool_bar = gtk.Toolbar()
	app_win.tool_bar.insert(actions.plot.create_tool_item(), -1)
	app_win.tool_bar.insert(actions.evaluate.create_tool_item(), -1)
	app_win.tool_bar.insert(gtk.SeparatorToolItem(), -1)
	app_win.tool_bar.insert(actions.zoom_in.create_tool_item(), -1)
	app_win.tool_bar.insert(actions.zoom_out.create_tool_item(), -1)
	app_win.tool_bar.insert(actions.zoom_reset.create_tool_item(), -1)
	app_win.tool_bar.insert(gtk.SeparatorToolItem(), -1)
	app_win.tool_bar.insert(actions.quit.create_tool_item(), -1)
	

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
					e[1].set_text("Error: %s" % sys.exc_value)
				else:
					e[1].set_text("")
				
	def close(self):
		dlg_win.destroy()
		
	dlg_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
	dlg_win.set_title(_("Evaluate"))
	dlg_win.connect("destroy", close)
	
	dlg_win.x_entry = gtk.Entry()
	dlg_win.x_entry.set_size_request(200, 24)
	dlg_win.x_entry.connect("changed", entry_changed)
	dlg_win.y1_entry = gtk.Entry()
	dlg_win.y1_entry.set_size_request(200, 24)
	dlg_win.y1_entry.set_sensitive(False)
	dlg_win.y2_entry = gtk.Entry()
	dlg_win.y2_entry.set_size_request(200, 24)
	dlg_win.y2_entry.set_sensitive(False)
	dlg_win.y3_entry = gtk.Entry()
	dlg_win.y3_entry.set_size_request(200, 24)
	dlg_win.y3_entry.set_sensitive(False)
	
	table = gtk.Table(2, 5)
	label = gtk.Label("x = ")
	label.set_alignment(0, .5)
	table.attach(label, 0, 1, 0, 1, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	table.attach(dlg_win.x_entry, 1, 2, 0, 1)
	label = gtk.Label("y1 = ")
	label.set_alignment(0, .5)
	label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))
	table.attach(label, 0, 1, 1, 2, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	table.attach(dlg_win.y1_entry, 1, 2, 1, 2)
	label = gtk.Label("y2 = ")
	label.set_alignment(0, .5)
	label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
	table.attach(label, 0, 1, 2, 3, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	table.attach(dlg_win.y2_entry, 1, 2, 2, 3)
	label = gtk.Label("y3 = ")
	label.set_alignment(0, .5)
	label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("DarkGreen"))
	table.attach(label, 0, 1, 3, 4, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	table.attach(dlg_win.y3_entry, 1, 2, 3, 4)
	
	table.set_border_width(24)	
	dlg_win.add(table)	
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
	app_win.scale_box.hide()
	plot(None)


def scale_rad(widget, event=None):
	graph.scale_style = "rad"
	app_win.scale_box.hide()
	plot(None)


def scale_cust(widget, event=None):
	graph.scale_style = "cust"
	app_win.scale_box.show()
	plot(None)


def toggle_connect(widget, event=None):
	"Toggle between a graph that connects points with lines and one that does not"
	
	global connect_points
	connect_points = not connect_points
	graph.plot()
	

def save(widget, event=None):
	"Save graph as .png"

	file_dialog = gtk.FileChooserDialog(_("Save as..."), app_win, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
	file_dialog.set_default_response(gtk.RESPONSE_OK)
	filter = gtk.FileFilter()
	filter.add_mime_type("image/png")
	filter.add_pattern("*.png")
	file_dialog.add_filter(filter)
	file_dialog.set_filename("FunctionGraph.png")
	
	response = file_dialog.run()
	if response == gtk.RESPONSE_OK:
		x, y, w, h = graph.drawing_area.get_allocation()
		pix_buffer = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
		pix_buffer.get_from_drawable(graph.pix_map, graph.pix_map.get_colormap(), 0, 0, 0, 0, w, h)
		pix_buffer.save(file_dialog.get_filename(), "png")
	file_dialog.destroy()


def quit_dlg(widget, event=None):
	gtk.main_quit()


def show_yelp(widget):
	#import os
	#os.system("yelp /usr/share/gnome/help/lybniz/C/lybniz-manual.xml")
	try:
		gnome.help_display("lybniz")
	except:
		print _("Can't Show help")


def show_about_dialog(widget):
	about_dialog = gtk.AboutDialog()
	about_dialog.set_name("Lybniz")
	about_dialog.set_version(str(app_version))
	about_dialog.set_authors([u"Thomas Führinger","Sam Tygier"])
	about_dialog.set_comments(_("Function Graph Plotter"))
	about_dialog.set_license("Revised BSD")
	about_dialog.set_website("github.com/thomasfuhringer/lybniz")
	try:
		lybniz_icon = gtk.gdk.pixbuf_new_from_file(icon_file)
		about_dialog.set_logo(lybniz_icon)
	except:
		print "icon not found at", icon_file
	about_dialog.connect ("response", lambda d, r: d.destroy())
	about_dialog.run()


def parameter_entries_create():
	# create text entries for parameters	
	table = gtk.Table(6, 3)
	
	app_win.y1_entry = gtk.Entry()
	app_win.y1_entry.set_size_request(300, 24)
	app_win.y2_entry = gtk.Entry()
	app_win.y3_entry = gtk.Entry()
	app_win.x_min_entry = gtk.Entry()
	app_win.x_min_entry.set_size_request(90, 24)
	app_win.x_min_entry.set_alignment(1)
	app_win.x_max_entry = gtk.Entry()
	app_win.x_max_entry.set_size_request(90, 24)
	app_win.x_max_entry.set_alignment(1)
	app_win.x_scale_entry = gtk.Entry()
	app_win.x_scale_entry.set_size_request(90, 24)
	app_win.x_scale_entry.set_alignment(1)
	app_win.y_min_entry = gtk.Entry()
	app_win.y_min_entry.set_size_request(90, 24)
	app_win.y_min_entry.set_alignment(1)
	app_win.y_max_entry = gtk.Entry()
	app_win.y_max_entry.set_size_request(90, 24)
	app_win.y_max_entry.set_alignment(1)
	app_win.y_scale_entry = gtk.Entry()
	app_win.y_scale_entry.set_size_request(90, 24)
	app_win.y_scale_entry.set_alignment(1)
	
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
	
	app_win.scale_box = gtk.HBox()
	
	label = gtk.Label("y1 = ")
	label.set_alignment(0, .5)
	label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))
	table.attach(label, 0, 1, 0, 1, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	table.attach(app_win.y1_entry, 1, 2, 0, 1)
	label = gtk.Label(_("X min"))
	label.set_alignment(1, .5)
	table.attach(label, 2, 3, 0, 1, xpadding=5, ypadding=7, xoptions=gtk.FILL)
	table.attach(app_win.x_min_entry, 3, 4, 0, 1, xoptions=gtk.FILL)
	label = gtk.Label(_("Y min"))
	label.set_alignment(1, .5)
	table.attach(label, 4, 5, 0, 1, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	table.attach(app_win.y_min_entry, 5, 6, 0, 1, xpadding=5, xoptions=gtk.FILL)
	label = gtk.Label("y2 = ")
	label.set_alignment(0, .5)
	label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
	table.attach(label, 0, 1, 1, 2, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	table.attach(app_win.y2_entry, 1, 2, 1, 2)
	label = gtk.Label(_("X max"))
	label.set_alignment(1, .5)
	table.attach(label, 2, 3, 1, 2, xpadding=5, ypadding=7, xoptions=gtk.FILL)
	table.attach(app_win.x_max_entry, 3, 4, 1, 2, xoptions=gtk.FILL)
	label = gtk.Label(_("Y max"))
	label.set_alignment(1, .5)
	table.attach(label, 4, 5, 1, 2, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	table.attach(app_win.y_max_entry, 5, 6, 1, 2, xpadding=5, xoptions=gtk.FILL)
	label = gtk.Label("y3 = ")
	label.set_alignment(0, .5)
	label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("DarkGreen"))
	table.attach(label, 0, 1, 2, 3, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	table.attach(app_win.y3_entry, 1, 2, 2, 3)
	
	
	label = gtk.Label(_("X scale"))
	label.set_alignment(0, .5)
	app_win.scale_box.add(label)
	#table.attach(label, 2, 3, 2, 3, xpadding=5, ypadding=7, xoptions=gtk.FILL)
	#table.attach(app_win.x_scale_entry, 3, 4, 2, 3, xoptions=gtk.FILL)
	app_win.scale_box.add(app_win.x_scale_entry)
	label = gtk.Label(_("Y scale"))
	label.set_alignment(0, .5)
	app_win.scale_box.add(label)
	#table.attach(label, 4, 5, 2, 3, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	#table.attach(app_win.y_scale_entry, 5, 6, 2, 3, xpadding=5, xoptions=gtk.FILL)
	app_win.scale_box.add(app_win.y_scale_entry)
	table.attach(app_win.scale_box, 2, 6, 2, 3, xpadding=5, xoptions=gtk.FILL)
	return table
	
	
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
		
def set_statusbar(text):
	app_win.status_bar.remove_all(0)
	app_win.status_bar.push(0, text)


def main():
	global app_win, graph
	
	app_win = gtk.Window(gtk.WINDOW_TOPLEVEL)
	app_win.set_title("Lybniz")
	app_win.set_default_size(800, 600)
	app_win.connect("delete-event", quit_dlg)
	try:
		app_win.set_icon_from_file(icon_file)
	except:
		print "icon not found at", icon_file
	
	app_win.accel_group = gtk.AccelGroup()
	app_win.add_accel_group(app_win.accel_group)

	app_win.v_box = gtk.VBox(False, 1)
	app_win.v_box.set_border_width(1)
	app_win.add(app_win.v_box)
	
	app_win.status_bar = gtk.Statusbar()

	menu_toolbar_create()
	app_win.v_box.pack_start(app_win.menu_main, False, True, 0)
	
	handle_box = gtk.HandleBox()
	handle_box.add(app_win.tool_bar)
	app_win.v_box.pack_start(handle_box, False, True, 0)
	
	app_win.v_box.pack_start(parameter_entries_create(), False, True, 4)
	
	graph = GraphClass()
	app_win.v_box.pack_start(graph.drawing_area, True, True, 0)
	app_win.v_box.pack_start(app_win.status_bar, False, True, 0)	
		
	app_win.show_all()
	app_win.scale_box.hide()

	gtk.main()


# Start it all
if __name__ == '__main__': main()

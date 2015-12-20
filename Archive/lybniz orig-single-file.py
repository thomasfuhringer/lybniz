#!/usr/bin/env python
# -*- coding: UTF-8 -*-

""" 
	Simple Function Graph Plotter
	© Thomas Führinger, 2005-02-12
	www.fuhringer.com/thomas
	
	Code contributions by Sam Tygier - thanks!
	
	Version 1.0
	Requires PyGtk 2.6	
	Released under the terms of the revised BSD license
	Modified: 2005-10-30
"""

import gtk, math, sys

AppWin = None
Actions = gtk.ActionGroup("General")
Graph = None
ConnectPoints = True

xMax = "5.0"
xMin = "-5.0"
xScale = "1.0"

yMax = "3.0"
yMin = "-3.0"
yScale = "1.0"

y1 = ""
y2 = ""
y3 = ""
	
class GraphClass:
	def __init__(self):	

		# Create backing pixmap of the appropriate size
		def ConfigureEvent(Widget, Event):
			x, y, w, h = Widget.get_allocation()
			self.PixMap = gtk.gdk.Pixmap(Widget.window, w, h)
			self.CanvasWidth = w
			self.CanvasHeight = h
			self.xMax = eval(xMax)
			self.xMin = eval(xMin)
			self.xScale = eval(xScale)
			self.yMax = eval(yMax)
			self.yMin = eval(yMin)
			self.yScale = eval(yScale)
			self.Plot()
			return True

		# Redraw the screen from the backing pixmap
		def ExposeEvent(Widget, Event):
			x, y, w, h = Event.area
			Widget.window.draw_drawable(Widget.get_style().fg_gc[gtk.STATE_NORMAL], self.PixMap, x, y, x, y, w, h)
			return False

		# Start marking selection
		def ButtonPressEvent(Widget, Event):
			global xSel, ySel
			
			if Event.button == 1:
				self.Selection[0][0], self.Selection[0][1] = int(Event.x), int(Event.y)
				self.Selection[1][0], self.Selection[1][1] = None, None

		# End of selection
		def ButtonReleaseEvent(Widget, Event):
			
			if Event.button == 1 and Event.x != self.Selection[0][0] and Event.y != self.Selection[0][1]:
				xmi, ymi = min(self.GraphX(self.Selection[0][0]), self.GraphX(Event.x)), min(self.GraphY(self.Selection[0][1]), self.GraphY(Event.y))
				xma, yma = max(self.GraphX(self.Selection[0][0]), self.GraphX(Event.x)), max(self.GraphY(self.Selection[0][1]), self.GraphY(Event.y))
				self.xMin, self.yMin, self.xMax, self.yMax = xmi, ymi, xma, yma
				ParameterEntriesRepopulate()
				Graph.Plot()
				self.Selection[1][0] = None
				self.Selection[0][0] = None

		# Draw rectangle during mouse movement
		def MotionNotifyEvent(Widget, Event):
			
			if Event.is_hint:
				x, y, State = Event.window.get_pointer()
			else:
				x = Event.x
				y = Event.y
				State = Event.state

			if State & gtk.gdk.BUTTON1_MASK and self.Selection[0][0] is not None:
				gc = self.DrawingArea.get_style().black_gc
				gc.set_function(gtk.gdk.INVERT)
				if self.Selection[1][0] is not None:
					x0 = min(self.Selection[1][0], self.Selection[0][0])
					y0 = min(self.Selection[1][1], self.Selection[0][1])
					w = abs(self.Selection[1][0] - self.Selection[0][0])
					h = abs(self.Selection[1][1] - self.Selection[0][1])
					self.PixMap.draw_rectangle(gc, False, x0, y0, w, h)
				x0 = min(self.Selection[0][0], int(x))
				y0 = min(self.Selection[0][1], int(y))
				w = abs(int(x) - self.Selection[0][0])
				h = abs(int(y) - self.Selection[0][1])
				self.PixMap.draw_rectangle(gc, False, x0, y0, w, h)
				self.Selection[1][0], self.Selection[1][1] = int(x), int(y)
				self.DrawDrawable()
				
		self.PrevY = [None, None, None]
		
		# Marked area point[0, 1][x, y]
		self.Selection = [[None, None], [None, None]]
		
		self.DrawingArea = gtk.DrawingArea()		
		self.DrawingArea.connect("expose_event", ExposeEvent)
		self.DrawingArea.connect("configure_event", ConfigureEvent)
		self.DrawingArea.connect("button_press_event", ButtonPressEvent)
		self.DrawingArea.connect("button_release_event", ButtonReleaseEvent)
		self.DrawingArea.connect("motion_notify_event", MotionNotifyEvent)
		self.DrawingArea.set_events(gtk.gdk.EXPOSURE_MASK | gtk.gdk.LEAVE_NOTIFY_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK |gtk.gdk.POINTER_MOTION_HINT_MASK)
			
	def DrawDrawable(self):
		x, y, w, h = self.DrawingArea.get_allocation()
		self.DrawingArea.window.draw_drawable(self.DrawingArea.get_style().fg_gc[gtk.STATE_NORMAL], self.PixMap, 0, 0, 0, 0, w, h)
		
	def Plot(self):	
		self.PixMap.draw_rectangle(self.DrawingArea.get_style().white_gc, True, 0, 0, self.CanvasWidth, self.CanvasHeight)
		
		# draw cross
		self.PixMap.draw_lines(self.DrawingArea.get_style().black_gc, [self.CanvasPoint(0, self.yMin), self.CanvasPoint(0, self.yMax)])
		self.PixMap.draw_lines(self.DrawingArea.get_style().black_gc, [self.CanvasPoint(self.xMin, 0), self.CanvasPoint(self.xMax, 0)])
		
		# draw scaling x
		iv = int(self.xScale * self.CanvasWidth/(self.xMax - self.xMin))
		os = self.CanvasX(0) % iv
		for i in xrange(self.CanvasWidth / iv + 1):
			self.PixMap.draw_lines(self.DrawingArea.get_style().black_gc, [(os + i * iv, self.CanvasY(0) - 5), (os + i * iv, self.CanvasY(0) + 5)])
		# draw scaling y
		iv = int(self.yScale * self.CanvasHeight/(self.yMax - self.yMin))
		os = self.CanvasY(0) % iv
		for i in xrange(self.CanvasHeight / iv + 1):
			self.PixMap.draw_lines(self.DrawingArea.get_style().black_gc, [(self.CanvasX(0) - 5, i * iv + os), (self.CanvasX(0) + 5, i * iv + os)])

		# plot
		# (coloring of lines does not work yet)
		GC1 = self.DrawingArea.get_style().fg_gc[gtk.STATE_NORMAL]
		GC1.foreground = gtk.gdk.color_parse("blue")
		GC2 = self.DrawingArea.get_style().fg_gc[gtk.STATE_NORMAL]
		GC2.foreground = gtk.gdk.color_parse("red")
		GC3 = self.DrawingArea.get_style().fg_gc[gtk.STATE_NORMAL]
		GC3.foreground = gtk.gdk.color_parse("DarkGreen")
		
		self.PrevY = [None, None, None]
		for i in xrange(self.CanvasWidth):
			x = self.GraphX(i + 1)
			for e in ((y1, 0, GC1), (y2, 1, GC2), (y3, 2, GC3)):
				try:
					y = eval(e[0])
					yC = self.CanvasY(y)
					
					if yC < 0 or yC > self.CanvasHeight:
						raise ValueError
					
					if ConnectPoints and self.PrevY[e[1]] is not None:
						self.PixMap.draw_lines(e[2], [(i, self.PrevY[e[1]]), (i + 1, yC)])
					else:
						self.PixMap.draw_points(e[2], [(i + 1, yC)])
					self.PrevY[e[1]] = yC
				except:
					#print "Error at %d: %s" % (x, sys.exc_value)
					self.PrevY[e[1]] = None
		self.DrawDrawable()

		
	def CanvasX(self, x):
		"Calculate position on canvas to point on graph"
		return int((x - self.xMin) * self.CanvasWidth/(self.xMax - self.xMin))

	def CanvasY(self, y):
		return int((self.yMax - y) * self.CanvasHeight/(self.yMax - self.yMin))
		
	def CanvasPoint(self, x, y):
		return (self.CanvasX(x), self.CanvasY(y))
	
	def GraphX(self, x):
		"Calculate position on graph from point on canvas"
		return x  * (self.xMax - self.xMin) / self.CanvasWidth + self.xMin
		
	def GraphY(self, y):
		return self.yMax - (y * (self.yMax - self.yMin) / self.CanvasHeight)
		
		
def MenuToolbarCreate():

	AppWin.MenuMain = gtk.MenuBar()
	
	MenuFile = gtk.Menu()	
	MenuItemFile = gtk.MenuItem("_File")
	MenuItemFile.set_submenu(MenuFile)
	
	Actions.Save = gtk.Action("Save", "_Save", "Save graph as bitmap", gtk.STOCK_SAVE)
	Actions.Save.connect ("activate", Save)
	Actions.add_action(Actions.Save)
	MenuItemSave = Actions.Save.create_menu_item()
	MenuItemSave.add_accelerator("activate", AppWin.AccelGroup, ord("S"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuFile.append(MenuItemSave)
	
	Actions.Quit = gtk.Action("Quit", "_Quit", "Quit Application", gtk.STOCK_QUIT)
	Actions.Quit.connect ("activate", QuitDlg)
	Actions.add_action(Actions.Quit)
	MenuItemQuit = Actions.Quit.create_menu_item()
	MenuItemQuit.add_accelerator("activate", AppWin.AccelGroup, ord("Q"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuFile.append(MenuItemQuit)
	
	MenuGraph = gtk.Menu()	
	MenuItemGraph = gtk.MenuItem("_Graph")
	MenuItemGraph.set_submenu(MenuGraph)
	
	Actions.Plot = gtk.Action("Plot", "P_lot", "Plot Functions", gtk.STOCK_REFRESH)
	Actions.Plot.connect ("activate", Plot)
	Actions.add_action(Actions.Plot)
	MenuItemPlot = Actions.Plot.create_menu_item()
	MenuItemPlot.add_accelerator("activate", AppWin.AccelGroup, ord("l"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuGraph.append(MenuItemPlot)
	
	Actions.Evaluate = gtk.Action("Evaluate", "_Evaluate", "Evaluate Functions", gtk.STOCK_EXECUTE)
	Actions.Evaluate.connect ("activate", Evaluate)
	Actions.add_action(Actions.Evaluate)
	MenuItemEvaluate = Actions.Evaluate.create_menu_item()
	MenuItemEvaluate.add_accelerator("activate", AppWin.AccelGroup, ord("e"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuGraph.append(MenuItemEvaluate)
	
	Actions.ZoomIn = gtk.Action("ZoomIn", "Zoom _In", "Zoom In", gtk.STOCK_ZOOM_IN)
	Actions.ZoomIn.connect ("activate", ZoomIn)
	Actions.add_action(Actions.ZoomIn)
	MenuItemZoomIn = Actions.ZoomIn.create_menu_item()
	MenuItemZoomIn.add_accelerator("activate", AppWin.AccelGroup, ord("+"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuGraph.append(MenuItemZoomIn)
	
	Actions.ZoomOut = gtk.Action("ZoomOut", "Zoom _Out", "Zoom Out", gtk.STOCK_ZOOM_OUT)
	Actions.ZoomOut.connect ("activate", ZoomOut)
	Actions.add_action(Actions.ZoomOut)
	MenuItemZoomOut = Actions.ZoomOut.create_menu_item()
	MenuItemZoomOut.add_accelerator("activate", AppWin.AccelGroup, ord("-"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuGraph.append(MenuItemZoomOut)
	
	Actions.ZoomReset = gtk.Action("ZoomReset", "Zoom _Reset", "Zoom Reset", gtk.STOCK_ZOOM_100)
	Actions.ZoomReset.connect ("activate", ZoomReset)
	Actions.add_action(Actions.ZoomReset)
	MenuItemZoomReset = Actions.ZoomReset.create_menu_item()
	MenuItemZoomReset.add_accelerator("activate", AppWin.AccelGroup, 
ord("r"), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
	MenuGraph.append(MenuItemZoomReset)
	
	MenuItemToggleConnect = gtk.CheckMenuItem("_Connect Points")
	MenuItemToggleConnect.set_active(True)
	MenuItemToggleConnect.connect ("toggled", ToggleConnect)
	MenuGraph.append(MenuItemToggleConnect)
		
	MenuHelp = gtk.Menu()
	MenuItemHelp = gtk.MenuItem("_Help")
	MenuItemHelp.set_submenu(MenuHelp)

	Actions.Help = gtk.Action("Help", "_Contents", "Help Contents", gtk.STOCK_HELP)
	Actions.Help.connect ("activate", ShowYelp)
	Actions.add_action(Actions.Help)
	MenuItemContents = Actions.Help.create_menu_item()
	MenuItemContents.add_accelerator("activate", AppWin.AccelGroup, gtk.gdk.keyval_from_name("F1"), 0, gtk.ACCEL_VISIBLE)
	MenuHelp.append(MenuItemContents)

	Actions.About = gtk.Action("About", "_About", "About Box", gtk.STOCK_ABOUT)
	Actions.About.connect ("activate", ShowAboutDialog)
	Actions.add_action(Actions.About)
	MenuItemAbout = Actions.About.create_menu_item()
	MenuHelp.append(MenuItemAbout)
	
	AppWin.MenuMain.append(MenuItemFile)
	AppWin.MenuMain.append(MenuItemGraph)
	AppWin.MenuMain.append(MenuItemHelp)
	
	AppWin.ToolBar = gtk.Toolbar()
	AppWin.ToolBar.insert(Actions.Plot.create_tool_item(), -1)
	AppWin.ToolBar.insert(Actions.Evaluate.create_tool_item(), -1)
	AppWin.ToolBar.insert(gtk.SeparatorToolItem(), -1)
	AppWin.ToolBar.insert(Actions.ZoomIn.create_tool_item(), -1)
	AppWin.ToolBar.insert(Actions.ZoomOut.create_tool_item(), -1)
	AppWin.ToolBar.insert(Actions.ZoomReset.create_tool_item(), -1)
	AppWin.ToolBar.insert(gtk.SeparatorToolItem(), -1)
	AppWin.ToolBar.insert(Actions.Quit.create_tool_item(), -1)
	

def Plot(Widget, Event=None):
	global xMax, xMin, xScale, yMax, yMin, yScale, y1, y2, y3
	
	xMax = AppWin.xMaxEntry.get_text()
	xMin = AppWin.xMinEntry.get_text()
	xScale = AppWin.xScaleEntry.get_text()

	yMax = AppWin.yMaxEntry.get_text()
	yMin = AppWin.yMinEntry.get_text()
	yScale = AppWin.yScaleEntry.get_text()
	
	Graph.xMax = eval(xMax)
	Graph.xMin = eval(xMin)
	Graph.xScale = eval(xScale)

	Graph.yMax = eval(yMax)
	Graph.yMin = eval(yMin)
	Graph.yScale = eval(yScale)

	y1 = AppWin.Y1Entry.get_text()
	y2 = AppWin.Y2Entry.get_text()
	y3 = AppWin.Y3Entry.get_text()
	
	Graph.Plot()
	

def Evaluate(Widget, Event=None):
	"Evaluate a given x for the three functions"
	
	def EntryChanged(self):
		for e in ((y1, DlgWin.Y1Entry), (y2, DlgWin.Y2Entry), (y3, DlgWin.Y3Entry)):
			try:
				x = float(DlgWin.XEntry.get_text())
				e[1].set_text(str(eval(e[0])))
			except:
				if len(e[0]) > 0:
					e[1].set_text("Error: %s" % sys.exc_value)
				else:
					e[1].set_text("")
				
	def Close(self):
		DlgWin.destroy()
		
	DlgWin = gtk.Window(gtk.WINDOW_TOPLEVEL)
	DlgWin.set_title("Evaluate")
	DlgWin.connect("destroy", Close)
	
	DlgWin.XEntry = gtk.Entry()
	DlgWin.XEntry.set_size_request(200, 24)
	DlgWin.XEntry.connect("changed", EntryChanged)
	DlgWin.Y1Entry = gtk.Entry()
	DlgWin.Y1Entry.set_size_request(200, 24)
	DlgWin.Y1Entry.set_sensitive(False)
	DlgWin.Y2Entry = gtk.Entry()
	DlgWin.Y2Entry.set_size_request(200, 24)
	DlgWin.Y2Entry.set_sensitive(False)
	DlgWin.Y3Entry = gtk.Entry()
	DlgWin.Y3Entry.set_size_request(200, 24)
	DlgWin.Y3Entry.set_sensitive(False)
	
	Table = gtk.Table(2, 5)
	l = gtk.Label("x = ")
	l.set_alignment(0, .5)
	Table.attach(l, 0, 1, 0, 1, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(DlgWin.XEntry, 1, 2, 0, 1)
	l = gtk.Label("y1 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))
	Table.attach(l, 0, 1, 1, 2, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(DlgWin.Y1Entry, 1, 2, 1, 2)
	l = gtk.Label("y2 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
	Table.attach(l, 0, 1, 2, 3, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(DlgWin.Y2Entry, 1, 2, 2, 3)
	l = gtk.Label("y3 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("DarkGreen"))
	Table.attach(l, 0, 1, 3, 4, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(DlgWin.Y3Entry, 1, 2, 3, 4)
	
	Table.set_border_width(24)	
	DlgWin.add(Table)	
	DlgWin.show_all()


def ZoomIn(Widget, Event=None):
	"Narrow the plotted section by half"
	
	Graph.xMin /= 2
	Graph.yMin /= 2
	Graph.xMax /= 2
	Graph.yMax /= 2
	ParameterEntriesRepopulate()
	Graph.Plot()


def ZoomOut(Widget, Event=None):
	"Double the plotted section"
	
	Graph.xMin *= 2
	Graph.yMin *= 2
	Graph.xMax *= 2
	Graph.yMax *= 2
	ParameterEntriesRepopulate()
	Graph.Plot()


def ZoomReset(Widget, Event=None):
	"Set the range back to the user's input"
   
	Graph.xMin = eval(xMin)
	Graph.yMin = eval(yMin)
	Graph.xMax = eval(xMax)
	Graph.yMax = eval(yMax)
	ParameterEntriesPopulate()
	Graph.Plot()


def ToggleConnect(Widget, Event=None):
	"Toggle between a graph that connects points with lines and one that does not"
	
	global ConnectPoints
	ConnectPoints = not ConnectPoints
	Graph.Plot()
	

def Save(Widget, Event=None):
	"Save graph as .png"

	FileDialog = gtk.FileChooserDialog("Save as..", AppWin, gtk.FILE_CHOOSER_ACTION_SAVE, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
	FileDialog.set_default_response(gtk.RESPONSE_OK)
	Filter = gtk.FileFilter()
	Filter.add_mime_type("image/png")
	Filter.add_pattern("*.png")
	FileDialog.add_filter(Filter)
	FileDialog.set_filename("FunctionGraph.png")
	
	Response = FileDialog.run()
	FileDialog.destroy()
	if Response == gtk.RESPONSE_OK:
		x, y, w, h = Graph.DrawingArea.get_allocation()
		PixBuffer = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
		PixBuffer.get_from_drawable(Graph.PixMap, Graph.PixMap.get_colormap(), 0, 0, 0, 0, w, h)
		PixBuffer.save(FileDialog.get_filename(), "png")
	

def QuitDlg(Widget, Event=None):
	gtk.main_quit()
	

def ShowYelp(Widget):
	import os
	os.system("yelp lybniz-manual.xml")
		

def ShowAboutDialog(Widget):
	AboutDialog = gtk.AboutDialog()
	AboutDialog.set_name("Lybniz")
	AboutDialog.set_version("1.0")
	#AboutDialog.set_copyright(u"© 2005 by Thomas Führinger")
	AboutDialog.set_authors([u"Thomas Führinger"])
	AboutDialog.set_comments("Function Graph Plotter")
	AboutDialog.set_license("Revised BSD")
	#AboutDialog.set_website("http://www.fuhringer.com/thomas/lybniz")
	AboutDialog.show()


def ParameterEntriesCreate():
	# create text entries for parameters	
	Table = gtk.Table(6, 3)
	
	AppWin.Y1Entry = gtk.Entry()
	AppWin.Y1Entry.set_size_request(300, 24)
	AppWin.Y2Entry = gtk.Entry()
	AppWin.Y3Entry = gtk.Entry()
	AppWin.xMinEntry = gtk.Entry()
	AppWin.xMinEntry.set_size_request(90, 24)
	AppWin.xMinEntry.set_alignment(1)
	AppWin.xMaxEntry = gtk.Entry()
	AppWin.xMaxEntry.set_size_request(90, 24)
	AppWin.xMaxEntry.set_alignment(1)
	AppWin.xScaleEntry = gtk.Entry()
	AppWin.xScaleEntry.set_size_request(90, 24)
	AppWin.xScaleEntry.set_alignment(1)
	AppWin.yMinEntry = gtk.Entry()
	AppWin.yMinEntry.set_size_request(90, 24)
	AppWin.yMinEntry.set_alignment(1)
	AppWin.yMaxEntry = gtk.Entry()
	AppWin.yMaxEntry.set_size_request(90, 24)
	AppWin.yMaxEntry.set_alignment(1)
	AppWin.yScaleEntry = gtk.Entry()
	AppWin.yScaleEntry.set_size_request(90, 24)
	AppWin.yScaleEntry.set_alignment(1)
	
	ParameterEntriesPopulate()
	
	l = gtk.Label("y1 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))
	Table.attach(l, 0, 1, 0, 1, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.Y1Entry, 1, 2, 0, 1)
	l = gtk.Label("xMin")
	l.set_alignment(1, .5)
	Table.attach(l, 2, 3, 0, 1, xpadding=5, ypadding=7, xoptions=gtk.FILL)
	Table.attach(AppWin.xMinEntry, 3, 4, 0, 1, xoptions=gtk.FILL)
	l = gtk.Label("yMin")
	l.set_alignment(1, .5)
	Table.attach(l, 4, 5, 0, 1, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.yMinEntry, 5, 6, 0, 1, xpadding=5, xoptions=gtk.FILL)
	l = gtk.Label("y2 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("red"))
	Table.attach(l, 0, 1, 1, 2, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.Y2Entry, 1, 2, 1, 2)
	l = gtk.Label("xMax")
	l.set_alignment(1, .5)
	Table.attach(l, 2, 3, 1, 2, xpadding=5, ypadding=7, xoptions=gtk.FILL)
	Table.attach(AppWin.xMaxEntry, 3, 4, 1, 2, xoptions=gtk.FILL)
	l = gtk.Label("yMax")
	l.set_alignment(1, .5)
	Table.attach(l, 4, 5, 1, 2, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.yMaxEntry, 5, 6, 1, 2, xpadding=5, xoptions=gtk.FILL)
	l = gtk.Label("y3 = ")
	l.set_alignment(0, .5)
	l.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("DarkGreen"))
	Table.attach(l, 0, 1, 2, 3, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.Y3Entry, 1, 2, 2, 3)
	l = gtk.Label("xScale")
	l.set_alignment(0, .5)
	Table.attach(l, 2, 3, 2, 3, xpadding=5, ypadding=7, xoptions=gtk.FILL)
	Table.attach(AppWin.xScaleEntry, 3, 4, 2, 3, xoptions=gtk.FILL)
	l = gtk.Label("yScale")
	l.set_alignment(0, .5)
	Table.attach(l, 4, 5, 2, 3, xpadding=5, ypadding=5, xoptions=gtk.FILL)
	Table.attach(AppWin.yScaleEntry, 5, 6, 2, 3, xpadding=5, xoptions=gtk.FILL)
	return Table
	
	
def ParameterEntriesPopulate():
	# set text in entries for parameters with user's input
	
	AppWin.Y1Entry.set_text(y1)
	AppWin.Y2Entry.set_text(y2)
	AppWin.Y3Entry.set_text(y3)
	AppWin.xMinEntry.set_text(xMin)
	AppWin.xMaxEntry.set_text(xMax)
	AppWin.xScaleEntry.set_text(xScale)
	AppWin.yMinEntry.set_text(yMin)
	AppWin.yMaxEntry.set_text(yMax)
	AppWin.yScaleEntry.set_text(yScale)
	
	
def ParameterEntriesRepopulate():
	# set text in entries for parameters
	
	AppWin.Y1Entry.set_text(y1)
	AppWin.Y2Entry.set_text(y2)
	AppWin.Y3Entry.set_text(y3)
	AppWin.xMinEntry.set_text(str(Graph.xMin))
	AppWin.xMaxEntry.set_text(str(Graph.xMax))
	AppWin.xScaleEntry.set_text(str(Graph.xScale))
	AppWin.yMinEntry.set_text(str(Graph.yMin))
	AppWin.yMaxEntry.set_text(str(Graph.yMax))
	AppWin.yScaleEntry.set_text(str(Graph.yScale))
	
	
def Main():
	global AppWin, Graph
	
	AppWin = gtk.Window(gtk.WINDOW_TOPLEVEL)
	AppWin.set_title("Lybniz")
	AppWin.set_default_size(800, 600)
	AppWin.connect("delete-event", QuitDlg)

	AppWin.AccelGroup = gtk.AccelGroup()
	AppWin.add_accel_group(AppWin.AccelGroup)

	AppWin.VBox = gtk.VBox(False, 1)
	AppWin.VBox.set_border_width(1)
	AppWin.add(AppWin.VBox)
	
	AppWin.StatusBar = gtk.Statusbar()
	AppWin.StatusBar.ContextId = AppWin.StatusBar.get_context_id("Dummy")

	MenuToolbarCreate()
	AppWin.VBox.pack_start(AppWin.MenuMain, False, True, 0)
	
	HandleBox = gtk.HandleBox()
	HandleBox.add(AppWin.ToolBar)
	AppWin.VBox.pack_start(HandleBox, False, True, 0)
	
	AppWin.VBox.pack_start(ParameterEntriesCreate(), False, True, 4)
	
	Graph = GraphClass()
	AppWin.VBox.pack_start(Graph.DrawingArea, True, True, 0)
	AppWin.VBox.pack_start(AppWin.StatusBar, False, True, 0)	
		
	AppWin.show_all()

	gtk.main()


# Start it all
if __name__ == '__main__': Main()

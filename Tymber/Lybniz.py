# Tymber version of Lybniz
# © 2020 by Thomas Führinger <thomasfuhringer@live.com>
# Tymber Python library is available here: https://github.com/thomasfuhringer/tymber

import tymber as ty, pickle, sys
from math import *
version = "1.0"

child_position = None # window position of last active MDI child window

def file_new_menu_item__on_click():
    graph = GraphClass()
    mdi.active_child = graph
    if child_position:
        graph.position = (child_position[0] + 14 * GraphClass.graphs, child_position[1] + 14 * GraphClass.graphs, child_position[2], child_position[3])

def file_exit_menu_item__on_click():
    ty.app.window.close()        
        
def about_menu_item__on_click():
    window = ty.Window("About Lybniz", width=320, height=240)
    ty.Label(window, "line1", 50, 50, -10, 22, "Function graph plotter")
    ty.Label(window, "line2", 50, 70, -10, 22, "Version " + version)
    ty.Label(window, "line3", 50, 90, -10, 22, "Tymber Version %d.%d" % ty.version_info[:2])
    ty.Label(window, "line4", 50, 110, -10, 22, "Thomas Führinger, 2020 ")
    window.run()

def load_state():
    pos_bytes = ty.get_setting("Tymber", "Lybniz", "WindowPos")
    if pos_bytes is not None:
        state = pickle.loads(pos_bytes)
        ty.app.window.position = state[0]
        ty.app.window.maximized = state[1]
        ty.app.window.mdi.maximized = state[2]
        global child_position
        child_position = state[3]
        if ty.app.window.mdi.active_child:
            ty.app.window.mdi.active_child.position = child_position

def save_state():
    position = ty.app.window.position
    main_maximized = ty.app.window.maximized
    mdi_maximized = ty.app.window.mdi.maximized
    if ty.app.window.mdi.active_child:
        global child_position
        child_position = ty.app.window.mdi.active_child.position
    ty.set_setting("Tymber", "Lybniz", "WindowPos", pickle.dumps((position, main_maximized, mdi_maximized, child_position)))

def window__before_close(self):
    save_state()
    return True

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
    lower_mark = min_val - fmod(min_val, interval)

    if lower_mark < min_val:
        lower_mark += interval

    a_mark = lower_mark
    while a_mark <= max_val:
        if abs(a_mark) < interval / 2:
            a_mark = 0
        yield a_mark
        a_mark += interval

class GraphClass(ty.MdiWindow):
    graphs = 0
    def __init__(self):
        GraphClass.graphs += 1
        self.connect_points = True
        super(GraphClass, self).__init__(mdi, "graph_" + str(GraphClass.graphs), 10, 10, 640, 420, "Graph " + str(GraphClass.graphs))

        y = 10
        ty.Label(self, "label_y1", 10, y, 30, 20, "y1 = ").text_color = (0, 0, 255)
        ty.Entry(self, "entry_y1", 36, y, -250, 20, "sin(x)").on_key = GraphClass.entry__on_key
        ty.Label(self, "label_x_min", -232, y, 36, 20, "X Min")
        ty.Entry(self, "entry_x_min", -196, y, -130, 20, "-5", data_type=float).on_key = GraphClass.entry__on_key
        ty.Label(self, "label_x_max", -116, y, 36, 20, "X Max")
        ty.Entry(self, "entry_x_max", -80, y, -10, 20, "5", data_type=float).on_key = GraphClass.entry__on_key
        y = 34
        ty.Label(self, "label_y2", 10, y, 30, 20, "y2 = ").text_color = (255, 0, 0)
        ty.Entry(self, "entry_y2", 36, y, -250, 20).on_key = GraphClass.entry__on_key
        ty.Label(self, "label_y_min", -232, y, 36, 20, "Y Min")
        ty.Entry(self, "entry_y_min", -196, y, -130, 20, "-3", data_type=float).on_key = GraphClass.entry__on_key
        ty.Label(self, "label_y_max", -116, y, 36, 20, "Y Max")
        ty.Entry(self, "entry_y_max", -80, y, -10, 20, "3", data_type=float).on_key = GraphClass.entry__on_key
        y = 58
        ty.Label(self, "label_y3", 10, y, 30, 20, "y3 = ").text_color = (0, 170, 0)
        ty.Entry(self, "entry_y3", 36, y, -250, 20).on_key = GraphClass.entry__on_key
        ty.Button(self, "button_repaint", -60, y, -10, 20, "Plot").on_click = GraphClass.button_repaint__on_click

        self.entry_y1.tab_next = self.entry_y2
        self.entry_y2.tab_next = self.entry_y3
        self.entry_y3.tab_next = self.entry_x_min
        self.entry_x_min.tab_next = self.entry_x_max
        self.entry_x_max.tab_next = self.entry_y_min
        self.entry_y_min.tab_next = self.entry_y_max
        canvas = ty.Canvas(self, "canvas", 0, 88, 0, 0)

        GraphClass.button_repaint__on_click(self.button_repaint)

        canvas.on_paint = GraphClass.canvas__on_paint
        #print ("getrefcount", sys.getrefcount(self))

    def entry__on_key(key, entry):
        if key == ty.Key.enter and entry.commit():
            GraphClass.button_repaint__on_click(entry.parent.button_repaint)

    def button_repaint__on_click(button):
        self = button.parent
        self.x_min = self.entry_x_min.data
        self.x_max = self.entry_x_max.data
        self.y_min = self.entry_y_min.data
        self.y_max = self.entry_y_max.data
        self.y1 = self.entry_y1.data
        self.y2 = self.entry_y2.data
        self.y3 = self.entry_y3.data
        self.scale_style = "rad"
        self.canvas.repaint()

    def canvas__on_paint(canvas):
        self = canvas.parent
        self.canvas_width, self.canvas_height = canvas.size

        # new style
        factor = 1
        if (self.scale_style == "rad"): factor = pi
        if (self.scale_style == "tau"): factor = tau

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
        canvas.move_to(center_x_pix, 0)
        canvas.line_to(center_x_pix, self.canvas_height)
        canvas.move_to(0, center_y_pix)
        canvas.line_to(self.canvas_width, center_y_pix)

        for i in marks(self.x_min / factor, self.x_max / factor):
            label = "%g" % i
            if (self.scale_style == "rad"): label += " π"
            if (self.scale_style == "tau"): label += " τ"
            i = i * factor

            canvas.move_to(self.canvas_x(i), center_y_pix - 5)
            canvas.line_to(self.canvas_x(i), center_y_pix + 6)

            if (numbers_y_pos < 0):
                adjust = 4
            else:
                adjust = 0

            canvas.text(int(round(self.canvas_x(i))), center_y_pix + numbers_y_pos - adjust + 7, label)

        for i in marks(self.y_min, self.y_max):
            label = "%g" % i

            canvas.move_to(center_x_pix - 5, self.canvas_y(i))
            canvas.line_to(center_x_pix + 6, self.canvas_y(i))

            if (numbers_x_pos < 0):
                adjust = 4
            else:
                adjust = 0

            canvas.text(center_x_pix + numbers_x_pos - adjust, int(round(self.canvas_y(i))) + 7, label)

        # minor marks
        for i in marks(self.x_min / factor, self.x_max / factor, minor=10):
            i = i * factor
            canvas.move_to(self.canvas_x(i),  center_y_pix - 2)
            canvas.line_to(self.canvas_x(i),  center_y_pix + 3)

        for i in marks(self.y_min, self.y_max, minor=10):
            label = "%g" % i
            canvas.move_to(center_x_pix - 2, self.canvas_y(i))
            canvas.line_to(center_x_pix + 3, self.canvas_y(i))

        plots = []
        # precompile the functions
        invalid_input = False
        if self.y1:
            try:
                compiled_y1 = compile(self.y1.replace("^","**"), "", "eval")
                plots.append((compiled_y1, 0, (0, 0, 255), self.y1))
            except Exception as exception:
                print("Exception: " + exception)
                app.window.status_bar.set_text("Function" + " '" + self.y1 + "' " + "is invalid.")
                invalid_input = True
                compiled_y1 = None
        else:
            compiled_y1 = None

        if self.y2:
            try:
                compiled_y2 = compile(self.y2.replace("^","**"),"", "eval")
                plots.append((compiled_y2, 1, (255, 0, 0), self.y2))
            except Exception as exception:
                print("Exception: " + exception)
                app.window.status_bar.set_text("Function" + " '" + self.y2 + "' " + "is invalid.")
                invalid_input = True
                compiled_y2 = None
        else:
            compiled_y2 = None

        if self.y3:
            try:
                compiled_y3 = compile(self.y3.replace("^","**"), "", "eval")
                plots.append((compiled_y3, 2, (0, 170, 0), self.y3))
            except Exception as exception:
                print("Exception: " + exception)
                app.window.status_bar.set_text("Function" + " '" + self.y3 + "' " + "is invalid.")
                invalid_input = True
                compiled_y3 = None
        else:
            compiled_y3 = None

        self.prev_y = [None, None, None]

        if len(plots) != 0:
            for i in range(-1, self.canvas_width, 1):
                x = self.graph_x(i + 1)
                for e in plots:
                    try:
                        y = eval(e[0])
                        y_c = self.canvas_y(y)
                        if 0 <= y_c and y_c <= self.canvas_height:
                            canvas.pen_color = e[2]
                            if self.connect_points and self.prev_y[e[1]] is not None:
                                canvas.move_to(i, self.prev_y[e[1]])
                                canvas.line_to(i + 1, y_c)
                            else:
                                canvas.point(i + 1, y_c)

                            self.prev_y[e[1]] = y_c
                        else:
                            self.prev_y[e[1]] = None

                    except Exception as exception:
                        #print("Exception: " + exception)
                        #import sys
                        #print ("Error at %d: %s" % (x, sys.exc_info()))
                        app.window.status_bar.set_text("Function" + " '" + e[3] + "' " + "is invalid at" + " " + str(int(x)) + ".")
                        invalid_input = True
                        self.prev_y[e[1]] = None

        if not invalid_input:
            app.window.status_bar.set_text(None)

    def canvas_x(self, x):
        "Calculate position on canvas to point on graph"
        return int(round((x - self.x_min) * self.canvas_width / (self.x_max - self.x_min)))

    def canvas_y(self, y):
        return int(round((self.y_max - y) * self.canvas_height / (self.y_max - self.y_min)))

    def graph_x(self, x):
        "Calculate position on graph from point on canvas"
        return x  * (self.x_max - self.x_min) / self.canvas_width + self.x_min

    def graph_y(self, y):
        return self.y_max - (y * (self.y_max - self.y_min) / self.canvas_height)


app = ty.Application(ty.Window("Lybniz", width=750, height=550))
app.window.before_close = window__before_close
menu = ty.Menu(app, "main", "Main")
file_menu = ty.Menu(menu, "file", "File")
file_new_menu_item = ty.MenuItem(file_menu, "new", "New", file_new_menu_item__on_click, ty.Image(ty.StockIcon.file_new))
file_exit_menu_item = ty.MenuItem(file_menu, "exit", "Exit", file_exit_menu_item__on_click, ty.Image(ty.StockIcon.exit))
window_menu = ty.Menu(menu, "window", "Window")
help_menu = ty.Menu(menu, "help", "Help")
about_menu_item = ty.MenuItem(help_menu, "about", "About...", about_menu_item__on_click, ty.Image(ty.StockIcon.information))

tool_bar = ty.ToolBar(app.window)
tool_bar.append_item(file_new_menu_item)
ty.StatusBar(app.window)

mdi = ty.MdiArea(app.window, "mdi", 0, 0, 0, 0)
mdi.menu = window_menu
file_new_menu_item__on_click()

load_state()
app.run()
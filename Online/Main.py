#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Thomas Führinger 2019
    https://github.com/thomasfuhringer/lybniz
    Released under the terms of the revised BSD license
    Modified: 2020-02-03

    uwsgi --http-socket 127.0.0.1:3031 --plugin python3 --wsgi-file Main.py --callable app  --buffer-size=32768
"""

import os, io, sys, flask, PIL.ImageDraw, PIL.ImageFont, base64
from math import *

app = flask.Flask(__name__)

pages_subdirectory = "static"
app.config.from_envvar("FLASKR_SETTINGS", silent=True)

@app.route("/", methods=["GET"])
def home():
    y1 = flask.request.args.get("y1")
    y2 = flask.request.args.get("y2")
    y3 = flask.request.args.get("y3")
    x_min = flask.request.args.get("xmin")
    x_max = flask.request.args.get("xmax")
    y_min = flask.request.args.get("ymin")
    y_max = flask.request.args.get("ymax")
    units = flask.request.args.get("units")
    return flask.render_template("Home.html", y1=y1 if y1 else "sin(x)", y2=y2 if y2 else "", y3=y3 if y3 else "", x_min=x_min if x_min else "-5", x_max=x_max if x_max else "5", y_min=y_min if y_min else "-3", y_max=y_max if y_max else "3", units=units if units else "deg")

@app.route("/graph", methods=["POST"])
def graph():
    graph = Graph(flask.request.json["y1"],
                  flask.request.json["y2"],
                  flask.request.json["y3"],
                  int(flask.request.json["width"]),
                  int(flask.request.json["height"]),
                  float(flask.request.json["x_min"]),
                  float(flask.request.json["x_max"]),
                  float(flask.request.json["y_min"]),
                  float(flask.request.json["y_max"]),
                  flask.request.json["units"])

    with io.BytesIO() as output:
        graph.image.save(output, format="PNG")
        img_str = base64.b64encode(output.getvalue())
    response = flask.jsonify(img=img_str.decode("utf-8"))
    response.status_code = 200
    return response

class Graph:
    def __init__(self, y1, y2, y3, width, height, x_min, x_max, y_min, y_max, units):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.width = width
        self.height = height

        self.image = PIL.Image.new("RGB", (width, height), color="white")
        draw = PIL.ImageDraw.Draw(self.image)
        grid_color = "grey"
        font = PIL.ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12, encoding="unic")

        factor = 1
        if (units == "pi"): factor = pi
        if (units == "tau"): factor = 2 * pi

        # where to put the numbers
        numbers_x_pos = -8
        numbers_y_pos = 7

        # where to center the axis
        center_x_pix, center_y_pix = self.transform_point(0, 0)
        if (center_x_pix < 5): 
            center_x_pix = 5
            numbers_x_pos = 4
        if (center_x_pix < 20): numbers_x_pos = 10
        if (center_y_pix < 5): center_y_pix = 5
        if (center_x_pix > width - 5): center_x_pix = width - 5
        if (center_y_pix > height -5): center_y_pix = height - 5;
        if (center_y_pix > height -20): numbers_y_pos = -16

        # draw cross
        draw.line((center_x_pix, 0, center_x_pix, height), fill=grid_color, width=1)
        draw.line((0, center_y_pix, width, center_y_pix), fill=grid_color, width=1)

        for i in marks(x_min / factor, x_max / factor):
            if i != 0:
                if (units == "pi"): label = "%g π" % i
                elif (units == "tau"): label = "%g τ" % i
                else: label = "%g" % i

                i = i * factor
                x = self.transform_x(i)
                draw.line((x, center_y_pix, x, center_y_pix + 5), fill=grid_color, width=1)

                adjust = draw.textsize(label, font=font)[0]
                draw.text((x - adjust / 2, center_y_pix + numbers_y_pos), label, font=font, fill=grid_color)

        for i in marks(y_min, y_max):
            if i != 0:
                label = "%g" % i
                y = self.transform_y(i)

                draw.line((center_x_pix - 5, y, center_x_pix , y), fill=grid_color, width=1)

                if (numbers_x_pos < 0):
                    adjust = draw.textsize(label, font=font)[0]
                else:
                    adjust = 0
                draw.text((center_x_pix + numbers_x_pos - adjust, y - 7), label, font=font, fill=grid_color)

        # minor marks
        for i in marks(x_min / factor, x_max / factor, minor=10):
            i = i * factor
            x = self.transform_x(i)
            draw.line((x, center_y_pix , x, center_y_pix + 2), fill=grid_color, width=1)

        for i in marks(y_min, y_max, minor=10):
            label = "%g" % i
            y = self.transform_y(i)
            draw.line((center_x_pix - 2, y, center_x_pix, y), fill=grid_color, width=1)

        plots = []
        # precompile the functions
        invalid_input = False
        if y1:
            try:
                compiled_y1 = compile(y1.replace("^","**"), "", "eval")
                plots.append((compiled_y1, 0, "blue", y1))
            except:
                #print("Function") + " '" + y1 + "' " + _("is invalid.")
                invalid_input = True
                compiled_y1 = None
        else:
            compiled_y1 = None

        if y2:
            try:
                compiled_y2 = compile(y2.replace("^","**"),"","eval")
                plots.append((compiled_y2, 1, "green", y2))
            except:
                #print("Function") + " '" + y2 + "' " + _("is invalid.")
                invalid_input = True
                compiled_y2 = None
        else:
            compiled_y2 = None

        if y3:
            try:
                compiled_y3 = compile(y3.replace("^","**"), "", "eval")
                plots.append((compiled_y3, 2, "red", y3))
            except:
                #print("Function") + " '" + y3 + "' " + _("is invalid.")
                invalid_input = True
                compiled_y3 = None
        else:
            compiled_y3 = None

        self.prev_y = [None, None, None]
        x_res = 1
        connect_points = True

        if len(plots) != 0:
            for i in range(-1, width, x_res):
                x = self.transform_back_x(i + 1)
                for e in plots:
                    safe_dict["x"] = x
                    try:
                        y = eval(e[0], {"__builtins__":{}}, safe_dict)
                        y_c = self.transform_y(y)

                        if connect_points and self.prev_y[e[1]] is not None and not ((self.prev_y[e[1]] < 0 and y_c > height) or (y_c < 0 and self.prev_y[e[1]] > height)):
                            draw.line((i, self.prev_y[e[1]], i + x_res, y_c), fill=e[2], width=1)
                        else:
                            draw.line((i, y_c, i + x_res, y_c), fill=e[2], width=1)

                        self.prev_y[e[1]] = y_c
                    except:
                        #print ("Error at %d: %s" % (x, sys.exc_info()))
                        #print("Function '" + e[3] + "' is invalid at " + str(int(x)) + ".")
                        invalid_input = True
                        self.prev_y[e[1]] = None


    def transform_point(self, x, y):
        return (0, 0) if (self.y_max - self.y_min) == 0 else (int(round((x - self.x_min) * self.width / (self.x_max - self.x_min))), int(round((self.y_max - y) * self.height / (self.y_max - self.y_min))))

    def transform_x(self, x):
        return 0 if (self.y_max - self.y_min) == 0 else int(round((x - self.x_min) * self.width / (self.x_max - self.x_min)))

    def transform_y(self, y):
        return 0 if (self.y_max - self.y_min) == 0 else int(round((self.y_max - y) * self.height / (self.y_max - self.y_min)))

    def transform_back_x(self, x):
        return x  * (self.x_max - self.x_min) / self.width + self.x_min

def marks(min_val, max_val, minor=1):
    "Yield positions of scale marks between min and max. For making minor marks, set minor to the number of minors you want between majors"
    try:
        min_val = float(min_val)
        max_val = float(max_val)
    except:
        #print ("Needs 2 numbers")
        raise ValueError

    if(min_val >= max_val):
        #print ("Min bigger or equal to max")
        raise ValueError

    a = 0.1   # tweakable control for when to switch scales
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

# create a safe namespace for the eval()s in the graph drawing code
def sub_dict(somedict, somekeys, default=None):
    return dict([ (k, somedict.get(k, default)) for k in somekeys ])

# a list of the functions from math that we want.
safe_list = ["math", "acos", "asin", "asinh", "atan", "atanh", "ceil", "cos", "cosh", "degrees", "e", "erf", "erfc", "exp", "expm1", "fabs", "floor", "fmod", "frexp", "hypot", "ldexp", "log", "log2", "log1p", "log10", "modf", "pi", "tau", "pow", "radians", "sin", "sinh", "sqrt", "tan", "tanh"]
safe_dict = sub_dict(locals(), safe_list)

#add any needed builtins back in.
safe_dict["abs"] = abs
safe_dict["min"] = min
safe_dict["max"] = max

@app.route("/about")
def about():
    return flask.render_template("About.html")

@app.errorhandler(404)
def page_not_found_error(error):
    app.logger.error("Page Not Found Error: %s", (error))
    return flask.render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error("Server Error: %s", (error))
    return flask.render_template("500.html"), 500

@app.errorhandler(Exception)
def unhandled_exception(error):
    app.logger.error("Unhandled Exception: %s", (error))
    return flask.render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug = True)

// Thomas Führinger, 2019

function plot() {
    var message, messageJSON, xmlhttp, response_message;
    var img = document.getElementById("Graph");

    var p;
    var newurl = window.location.protocol + "//" + window.location.host + window.location.pathname;
    newurl += "?y1=" + encodeURIComponent(document.getElementById("y1Input").value);

    p = document.getElementById("y2Input").value;
    if (p.length) {
        newurl += "&y2=" + encodeURIComponent(p);
    }
    p = document.getElementById("y3Input").value;
    if (p.length) {
        newurl += "&y3=" + encodeURIComponent(p);
    }

    p = document.getElementById("xMinInput").value;
    if (p !== "-5") {
        newurl += "&xmin=" + encodeURIComponent(p);
    }
    p = document.getElementById("xMaxInput").value;
    if (p !== "5") {
        newurl += "&xmax=" + encodeURIComponent(p);
    }
    p = document.getElementById("yMinInput").value;
    if (p !== "-3") {
        newurl += "&ymin=" + encodeURIComponent(p);
    }
    p = document.getElementById("yMaxInput").value;
    if (p !== "3") {
        newurl += "&ymax=" + encodeURIComponent(p);
    }
    p = document.getElementById("Units").value;
    if (p !== "deg") {
        newurl += "&units=" + encodeURIComponent(p);
    }
    if (p == "Radians π") {
        newurl += "&units=pi";
    }
    if (p == "Radians τ") {
        newurl += "&units=tau";
    }

    window.history.replaceState({
        path: newurl
    }, "", newurl);


    message = {
        "y1": document.getElementById("y1Input").value,
        "y2": document.getElementById("y2Input").value,
        "y3": document.getElementById("y3Input").value,
        "x_min": document.getElementById("xMinInput").value,
        "y_min": document.getElementById("yMinInput").value,
        "x_max": document.getElementById("xMaxInput").value,
        "y_max": document.getElementById("yMaxInput").value,
        "units": document.getElementById("Units").value,
        "width": img.clientWidth,
        "height": img.clientWidth,
        "height": img.clientWidth,
        "height": img.clientHeight
    };
    messageJSON = JSON.stringify(message);
    xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            response_message = JSON.parse(this.responseText);
            document.getElementById("Graph").setAttribute("src", "data:image/png;base64," + response_message.img);
        }
    };
    xmlhttp.open("POST", "/graph", true);
    xmlhttp.setRequestHeader("Content-type", "application/json");
    xmlhttp.send(messageJSON);
}

document.getElementById("y1Input").addEventListener("keyup", keyPressedHandler);
document.getElementById("y2Input").addEventListener("keyup", keyPressedHandler);
document.getElementById("y3Input").addEventListener("keyup", keyPressedHandler);
document.getElementById("xMinInput").addEventListener("keyup", keyPressedHandler);
document.getElementById("xMaxInput").addEventListener("keyup", keyPressedHandler);
document.getElementById("yMinInput").addEventListener("keyup", keyPressedHandler);
document.getElementById("yMaxInput").addEventListener("keyup", keyPressedHandler);

//window.onload = plot();
document.addEventListener("DOMContentLoaded", function() {
    plot();
}, false);

var canvas, ctx, dragging = false,
    startX = 0,
    startY = 0,
    offsetLeft = 0,
    offsetTop = 0;

canvas = document.getElementById("RectCanvas");
if (canvas.getContext) {
    ctx = canvas.getContext("2d");
    ctx.lineWidth = "1";
    ctx.strokeStyle = "grey";
    w = canvas.width;
    h = canvas.height;

    canvas.addEventListener("mousemove", function(e) {
        mouseEvent("move", e)
    }, false);
    canvas.addEventListener("mousedown", function(e) {
        mouseEvent("down", e)
    }, false);
    canvas.addEventListener("mouseup", function(e) {
        mouseEvent("up", e)
    }, false);
    canvas.addEventListener("mouseout", function(e) {
        mouseEvent("out", e)
    }, false);

    // IE9, Chrome, Safari, Opera
    canvas.addEventListener("mousewheel", mouseWheelHandler, false);
    // Firefox
    canvas.addEventListener("DOMMouseScroll", mouseWheelHandler, false);
}

function keyPressedHandler(event) {
    if (event.keyCode === 13) { // "Enter" key
        event.preventDefault();
        document.getElementById("PlotButton").click();
    }
};

function mouseWheelHandler(e) {
    // cross-browser wheel delta
    var e = window.event || e; // old IE support
    var delta = Math.max(-1, Math.min(1, (e.wheelDelta || -e.detail)));
    zoom(delta);

    return false;
}

function mouseEvent(res, e) {
    var rect = canvas.getBoundingClientRect();
    offsetLeft = rect.left;
    offsetTop = rect.top;

    if (res == "down") {
        startX = e.clientX - offsetLeft;
        startY = e.clientY - offsetTop;
        dragging = true;
    }
    if (res == "move") {
        if (dragging) {
            ctx.beginPath();
            ctx.clearRect(0, 0, w, h);
            ctx.rect(startX, startY, e.clientX - offsetLeft - startX, e.clientY - offsetTop - startY);
            ctx.stroke();
            //ctx.closePath();
        }
    }
    if (res == "up") { // || res == "out") {
        dragging = false;
        var xMin = parseFloat(document.getElementById("xMinInput").value);
        var yMin = parseFloat(document.getElementById("yMinInput").value);
        var xMax = parseFloat(document.getElementById("xMaxInput").value);
        var yMax = parseFloat(document.getElementById("yMaxInput").value);

        var xMinNew = Math.min(startX, e.clientX - offsetLeft) * (xMax - xMin) / w + xMin;
        var xMaxNew = Math.max(startX, e.clientX - offsetLeft) * (xMax - xMin) / w + xMin;
        var yMinNew = yMax - (Math.max(startY, e.clientY - offsetTop) * (yMax - yMin) / h);
        var yMaxNew = yMax - (Math.min(startY, e.clientY - offsetTop) * (yMax - yMin) / h);

        document.getElementById("xMinInput").value = xMaxNew - xMinNew > 1 ? Math.round(xMinNew * 100) / 100 : xMinNew;
        document.getElementById("xMaxInput").value = xMaxNew - xMinNew > 1 ? Math.round(xMaxNew * 100) / 100 : xMaxNew;
        document.getElementById("yMinInput").value = yMaxNew - yMinNew > 1 ? Math.round(yMinNew * 100) / 100 : yMinNew;
        document.getElementById("yMaxInput").value = yMaxNew - yMinNew > 1 ? Math.round(yMaxNew * 100) / 100 : yMaxNew;

        ctx.clearRect(0, 0, w, h);
        plot();
    }
}

function zoom(direction) {
    var xMin = parseFloat(document.getElementById("xMinInput").value);
    var yMin = parseFloat(document.getElementById("yMinInput").value);
    var xMax = parseFloat(document.getElementById("xMaxInput").value);
    var yMax = parseFloat(document.getElementById("yMaxInput").value);

    var center_x = (xMin + xMax) / 2;
    var center_y = (yMin + yMax) / 2;
    var range_x = xMax - xMin;
    var range_y = yMax - yMin;

    if (direction > 0) {
        document.getElementById("xMinInput").value = center_x - (range_x / 4);
        document.getElementById("yMinInput").value = center_y - (range_y / 4);
        document.getElementById("xMaxInput").value = center_x + (range_x / 4);
        document.getElementById("yMaxInput").value = center_y + (range_y / 4);
    } else {
        document.getElementById("xMinInput").value = center_x - (range_x);
        document.getElementById("yMinInput").value = center_y - (range_y);
        document.getElementById("xMaxInput").value = center_x + (range_x);
        document.getElementById("yMaxInput").value = center_y + (range_y);
    }

    plot();
}

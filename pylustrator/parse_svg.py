from xml.dom import minidom
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.transforms as transforms
import sys
import numpy as np
import matplotlib.text

def deform(base_trans, x, y, sx=0, sy=0):
    return transforms.Affine2D([[x, sx, 0], [sy, y, 0], [0, 0, 1]]) + base_trans

def parseTransformation(trans, base_trans):
    if trans is None or trans == "":
        return base_trans
    command, main = trans.split("(")
    if command == "translate":
        ox, oy = [float(s) for s in main.strip(")").split(",")]
        return transforms.Affine2D([[1, 0, ox], [0, 1, oy], [0, 0, 1]]) + base_trans
    elif command == "rotate":
        a = np.deg2rad(float(main[:-1]))
        ca, sa = np.cos(a), np.sin(a)
        return transforms.Affine2D([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]]) + base_trans
    elif command == "scale":
        x, y = [float(s) for s in main.strip(")").split(",")]
        return transforms.Affine2D([[x, 0, 0], [0, y, 0], [0, 0, 1]]) + base_trans
    elif command == "matrix":
        x, sx, sy, y, ox, oy = [float(s) for s in main.strip(")").split(",")]
        return transforms.Affine2D([[x, sx, ox], [sy, y, oy], [0, 0, 1]]) + base_trans
    else:
        print("ERROR: unknown transformation", trans)
    return base_trans

def parse_style(style, patch):
    for element in style.split(";"):
        key, value = element.split(":", 1)
        try:
            if key == "opacity":
                patch.set_alpha(float(value))
            elif key == "fill":
                patch.svg_fill = value
                try:
                    patch.set_facecolor(value)
                except AttributeError:
                    patch.set_color(value)
            elif key == "fill-opacity":
                if getattr(patch, "svg_fill", "none") != "none":
                    r, g, b, a = patch.get_facecolor()
                    patch.set_facecolor((r, g, b, float(value)))
            elif key == "stroke":
                patch.svg_stroke = value
                try:
                    patch.set_edgecolor(value)
                except AttributeError:
                    pass
                    #patch.set_color(value)
            elif key == "stroke-opacity":
                if getattr(patch, "svg_stroke", "none")[0] == "#":
                    r, g, b, a = patch.get_edgecolor()
                    patch.set_edgecolor((r, g, b, float(value)))
            elif key == "stroke-dasharray":
                if value != "none":
                    offset = 0
                    if isinstance(patch.get_linestyle(), tuple):
                        offset, dashes = patch.get_linestyle()
                    patch.set_linestyle((offset, [float(s)*4 for s in value.split(",")]))
            elif key == "stroke-dashoffset":
                dashes = [1, 0]
                if isinstance(patch.get_linestyle(), tuple):
                    offset, dashes = patch.get_linestyle()
                patch.set_linestyle((float(value)*4, dashes))
            elif key == "stroke-linecap":
                if value == "square":
                    value = "projecting"
                patch.set_capstyle(value)
            elif key == "stroke-linejoin":
                patch.set_joinstyle(value)
            elif key == "stroke-miterlimit":
                pass  # unfortunately we cannot implement this in matplotlib
            elif key == "stroke-width":
                try:
                    if value.endswith("px"):
                        patch.set_linewidth(float(value[:-2]) * 100)
                    else:
                        patch.set_linewidth(float(value) * 100)
                    pass
                except:
                    pass
            elif key == "stroke-linecap":
                try:
                    patch.set_dash_capstyle(value)
                    patch.set_solid_capstyle(value)
                except AttributeError:
                    pass
            elif key == "font-size":
                if value.endswith("px"):
                    patch.set_fontsize(float(value[:-2]) * 50)
                else:
                    patch.set_fontsize(float(value) * 100)
            elif key == "font-weight":
                patch.set_fontweight(value)
            elif key == "font-style":
                patch.set_fontstyle(value)
            else:
                print("ERROR: unknown style key", key, file=sys.stderr)
        except ValueError:
            print("ERROR: could not set style", element, file=sys.stderr)

def plt_draw_rect(node, trans):
    trans = parseTransformation(node.getAttribute("transform"), trans)

    patch = patches.Rectangle(xy=(float(node.getAttribute("x")), float(node.getAttribute("y"))),
                              width=float(node.getAttribute("width")),
                              height=float(node.getAttribute("height")),
                              transform=trans,
                              )

    parse_style(node.getAttribute("style"), patch)
    plt.gca().add_patch(patch)

def plt_draw_ellipse(node, trans):
    trans = parseTransformation(node.getAttribute("transform"), trans)

    patch = patches.Ellipse(xy=(float(node.getAttribute("cx")), float(node.getAttribute("cy"))),
                              width=float(node.getAttribute("rx"))*2,
                              height=float(node.getAttribute("ry"))*2,
                              transform=trans,
                              )

    parse_style(node.getAttribute("style"), patch)
    plt.gca().add_patch(patch)

def plt_draw_circle(node, trans):
    trans = parseTransformation(node.getAttribute("transform"), trans)

    patch = patches.Circle(xy=(float(node.getAttribute("cx")), float(node.getAttribute("cy"))),
                              radius=float(node.getAttribute("r")),
                              transform=trans,
                              )

    parse_style(node.getAttribute("style"), patch)
    plt.gca().add_patch(patch)


def plt_draw_text(node, trans):
    trans = parseTransformation(node.getAttribute("transform"), trans)
    x = float(node.getAttribute("x"))
    y = float(node.getAttribute("y"))

    text_content = ""
    for child in node.childNodes:
        text_content += child.firstChild.nodeValue
        text = plt.text(float(child.getAttribute("x")), float(child.getAttribute("y")),
                 child.firstChild.nodeValue,
                 transform=trans)

        parse_style(node.getAttribute("style"), text)

def plt_draw_path(node, trans):
    import matplotlib.path as mpath

    trans = parseTransformation(node.getAttribute("transform"), trans)

    last_command = None
    last_command_relative = False
    verts = []
    codes = []
    last_x, last_y = 0, 0
    index = 0
    for part in node.getAttribute("d").split(" "):
        if len(part) == 1:
            index = 0
            last_command_relative = part.islower()
            part = part.lower()
            if part == "m":
                last_command = mpath.Path.MOVETO
            elif part == "v":
                last_command = "v"#mpath.Path.MOVETO
            elif part == "h":
                last_command = "h"
            elif part == "l":
                last_command = mpath.Path.LINETO
            elif part == "c":
                last_command = mpath.Path.CURVE4
            elif part == "z":
                last_command = mpath.Path.CLOSEPOLY
                verts.append(verts[0])
                codes.append(mpath.Path.CLOSEPOLY)
            else:
                raise ValueError("Unknown command", last_command)
            continue
        if last_command == "v":
            x = float(part)
            y = 0
        elif last_command == "h":
            x = 0
            y = float(part)
        else:
            x, y = [float(s) for s in part.split(",")]
        if last_command_relative is True:
            x += last_x
            y += last_y
        verts.append([x, y])
        if last_command == "v" or last_command == "h":
            codes.append(mpath.Path.LINETO)
        else:
            codes.append(last_command)
        if last_command == mpath.Path.MOVETO:
            last_command = mpath.Path.LINETO
        if last_command == mpath.Path.CURVE4:
            index += 1
            if index == 3:
                last_x = x
                last_y = y
        else:
            last_x = x
            last_y = y

    path = mpath.Path(verts, codes)
    patch = patches.PathPatch(path,
                              transform=trans,
                              )

    parse_style(node.getAttribute("style"), patch)
    plt.gca().add_patch(patch)


def svgread(filename):
    # read the SVG file
    doc = minidom.parse(filename)

    svg = doc.getElementsByTagName("svg")[0]
    x1, y1, x2, y2 = [float(s.strip()) for s in svg.getAttribute("viewBox").split()]
    plt.gcf().set_size_inches(x2-x1, y2-y1)
    ax = plt.axes([0, 0, 1, 1], label=filename)
    plt.xticks([])
    plt.yticks([])
    for spine in ["left", "right", "top", "bottom"]:
        ax.spines[spine].set_visible(False)
    plt.xlim(x1, x2)
    plt.ylim(y2, y1)

    def parseGroup(node, trans):
        trans = parseTransformation(node.getAttribute("transform"), trans)
        for node in node.childNodes:
            if node.nodeType == node.TEXT_NODE:
                continue
            if node.tagName == "rect":
                plt_draw_rect(node, trans)
            elif node.tagName == "ellipse":
                plt_draw_ellipse(node, trans)
            elif node.tagName == "circle":
                plt_draw_circle(node, trans)
            elif node.tagName == "path":
                plt_draw_path(node, trans)
            elif node.tagName == "g":
                parseGroup(node, trans)
            elif node.tagName == "text":
                plt_draw_text(node, trans)
            elif node.tagName == "defs":
                pass  # currently ignored might be used for example for gradient definitions
            elif node.tagName == "sodipodi:namedview":
                pass  # used for some inkscape metadata
            elif node.tagName == "metadata":
                pass  # we do not have to draw metadata
            else:
                print("Unknown tag", node.tagName, file=sys.stderr)

    parseGroup(doc.getElementsByTagName("svg")[0], plt.gca().transData)

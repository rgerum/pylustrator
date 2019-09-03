from xml.dom import minidom
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.transforms as transforms
import sys
import numpy as np
import re
import io
import base64
import matplotlib.text
from .arc2bez import arcToBezier

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

def get_style(node, base_style=None):
    style = {}
    if base_style is not None:
        style.update(base_style)
    attribute_names = ["alignment-baseline", "baseline-shift", "clip-path", "clip-rule", "color", "color-interpolation", "color-interpolation-filters", "color-rendering", "cursor", "direction", "display", "dominant-baseline", "fill", "fill-opacity", "fill-rule", "filter", "flood-color", "flood-opacity", "font-family", "font-size", "font-size-adjust", "font-stretch", "font-style", "font-variant", "font-weight", "glyph-orientation-horizontal", "glyph-orientation-vertical", "image-rendering", "letter-spacing", "lighting-color", "marker-end", "marker-mid", "marker-start", "mask", "opacity", "overflow", "paint-order", "pointer-events", "shape-rendering", "stop-color", "stop-opacity", "stroke", "stroke-dasharray", "stroke-dashoffset", "stroke-linecap", "stroke-linejoin", "stroke-miterlimit", "stroke-opacity", "stroke-width", "text-anchor", "text-decoration", "text-overflow", "text-rendering", "unicode-bidi", "vector-effect", "visibility", "white-space", "word-spacing", "writing-mode"]
    for name in attribute_names:
        value = node.getAttribute(name)
        if value != "":
            style[name] = value

    for element in node.getAttribute("style").split(";"):
        if element == "":
            continue
        key, value = element.split(":", 1)
        style[key] = value
    return style

def apply_style(style, patch):
    print(patch, style)
    for key, value in style.items():
        print(key, value)
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
                    try:
                        r, g, b, a = patch.get_facecolor()
                        patch.set_facecolor((r, g, b, float(value)))
                    except AttributeError:
                        r, g, b, a = patch.get_color()
                        patch.set_color((r, g, b, float(value)))
            elif key == "stroke":
                patch.svg_stroke = value
                try:
                    patch.set_edgecolor(value)
                    print("stroke", value)
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
                    patch.set_linewidth(svgUnitToMpl(value))
                except:
                    pass
            elif key == "stroke-linecap":
                try:
                    patch.set_dash_capstyle(value)
                    patch.set_solid_capstyle(value)
                except AttributeError:
                    pass
            elif key == "font-size":
                patch.set_fontsize(svgUnitToMpl(value))
            elif key == "font-weight":
                patch.set_fontweight(value)
            elif key == "font-style":
                patch.set_fontstyle(value)
            else:
                print("ERROR: unknown style key", key, file=sys.stderr)
        except ValueError:
            print("ERROR: could not set style", key, value, file=sys.stderr)

def plt_patch(node, trans, style, constructor):
    trans = parseTransformation(node.getAttribute("transform"), trans)

    patch = constructor(node, trans)

    apply_style(get_style(node, style), patch)
    plt.gca().add_patch(patch)

def patch_rect(node, trans):
    return patches.Rectangle(xy=(float(node.getAttribute("x")), float(node.getAttribute("y"))),
                             width=float(node.getAttribute("width")),
                             height=float(node.getAttribute("height")),
                             transform=trans)

def patch_ellipse(node, trans):
    return patches.Ellipse(xy=(float(node.getAttribute("cx")), float(node.getAttribute("cy"))),
                           width=float(node.getAttribute("rx"))*2,
                           height=float(node.getAttribute("ry"))*2,
                           transform=trans)

def patch_circle(node, trans):
    return patches.Circle(xy=(float(node.getAttribute("cx")), float(node.getAttribute("cy"))),
                          radius=float(node.getAttribute("r")),
                          transform=trans)

def plt_draw_text(node, trans, style):
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties

    trans = parseTransformation(node.getAttribute("transform"), trans)
    x = float(node.getAttribute("x"))
    y = float(node.getAttribute("y"))

    text_content = ""
    for child in node.childNodes:
        text_content += child.firstChild.nodeValue
        text = plt.text(float(child.getAttribute("x")), float(child.getAttribute("y")),
                 child.firstChild.nodeValue,
                 transform=trans)
        apply_style(style, text)

def patch_path(node, trans):
    import matplotlib.path as mpath

    start_pos = None
    command = None
    verts = []
    codes = []

    current_pos = np.array([0, 0])

    elements = [a[0] for a in re.findall(r'((-?\d+\.?\d*)|(-?\d*\.?\d+)|\w)', node.getAttribute("d"))]
    elements.reverse()

    def popPos():
        pos = np.array([float(elements.pop()), float(elements.pop())])
        if not absolute:
            pos += current_pos
        return pos

    def popValue(count=None):
        if count is None:
            return float(elements.pop())
        else:
            return [float(elements.pop()) for i in range(count)]

    def addPathElement(type, *positions):
        for pos in positions:
            verts.append(pos)
            codes.append(type)
        return positions[-1]

    while elements:
        if 'A' <= elements[-1] <= 'z':
            last_command = command
            command = elements.pop()
            absolute = command.isupper()
            command = command.lower()

        # moveto
        if command == "m":
            current_pos = addPathElement(mpath.Path.MOVETO, popPos())
            start_pos = current_pos

            command = "l"
        # close
        elif command == "z":
            # Close path
            if not np.all(current_pos == start_pos):
                verts.append(start_pos)
                codes.append(mpath.Path.CLOSEPOLY)

            current_pos = start_pos
            start_pos = None
            command = None  # You can't have implicit commands after closing.
        # lineto
        elif command == 'l':
            current_pos = addPathElement(mpath.Path.LINETO, popPos())
        # horizontal lineto
        elif command == 'h':
            current_pos = addPathElement(mpath.Path.LINETO,
                                         np.array([popValue()+current_pos[0]*(1-absolute), current_pos[1]]))
        # vertical lineto
        elif command == 'v':
            current_pos = addPathElement(mpath.Path.LINETO,
                                         np.array([current_pos[0], popValue() + current_pos[1] * (1 - absolute)]))
        # cubic bezier curveto
        elif command == 'c':
            current_pos = addPathElement(mpath.Path.CURVE4, popPos(), popPos(), popPos())
        # smooth cubic bezier curveto
        elif command == 's':
            # Smooth curve. First control point is the "reflection" of
            # the second control point in the previous path.

            if last_command not in 'cs':
                # If there is no previous command or if the previous command
                # was not an C, c, S or s, assume the first control point is
                # coincident with the current point.
                control1 = current_pos
            else:
                # The first control point is assumed to be the reflection of
                # the second control point on the previous command relative
                # to the current point.
                control1 = current_pos + (current_pos - verts[-2])

            current_pos = addPathElement(mpath.Path.CURVE4, control1, popPos(), popPos())
        # quadratic bezier curveto
        elif command == 'q':
            current_pos = addPathElement(mpath.Path.CURVE3, popPos(), popPos())
        # smooth quadratic bezier curveto
        elif command == 't':
            # Smooth curve. Control point is the "reflection" of
            # the second control point in the previous path.

            if last_command not in 'qt':
                # If there is no previous command or if the previous command
                # was not an Q, q, T or t, assume the first control point is
                # coincident with the current point.
                control1 = current_pos
            else:
                # The control point is assumed to be the reflection of
                # the control point on the previous command relative
                # to the current point.
                control1 = current_pos + (current_pos - verts[-2])
            current_pos = addPathElement(mpath.Path.CURVE3, control1, popPos())
        # elliptical arc
        elif command == 'a':
            radius1, radius2, rotation, arc, sweep = popValue(5)
            end = popPos()

            for e in arcToBezier(current_pos, end, radius1, radius2, rotation, arc, sweep):
                current_pos = addPathElement(mpath.Path.CURVE4, e[:2], e[2:4], e[4:6])

    path = mpath.Path(verts, codes)
    return patches.PathPatch(path, transform=trans)

def svgUnitToMpl(unit, default=None):
    import re
    if unit == "":
        return default
    match = re.match(r"^([-.\d]*)(\w*)$", unit)
    if match:
        value, unit = match.groups()
        value = float(value)
        if unit == "pt":
            value *= plt.gcf().dpi / 72
        elif unit == "pc":
            value *= plt.gcf().dpi / 6
        elif unit == "in":
            value *= plt.gcf().dpi
        elif unit == "px":
            pass
        elif unit == "cm":
            value *= plt.gcf().dpi / 2.5
        elif unit == "mm":
            value *= plt.gcf().dpi / 25
        return value


def openImageFromLink(link):
    if link.startswith("file:///"):
        return plt.imread(link[len("file:///"):])
    else:
        type, data = re.match(r"data:image/(\w*);base64,(.*)", link).groups()

        data = base64.decodebytes(bytes(data, "utf-8"))

        buf = io.BytesIO()
        buf.write(data)
        buf.seek(0)
        im = plt.imread(buf, format=type)
        buf.close()
        return im

def svgread(filename):
    # read the SVG file
    doc = minidom.parse(filename)

    svg = doc.getElementsByTagName("svg")[0]
    try:
        x1, y1, x2, y2 = [float(s.strip()) for s in svg.getAttribute("viewBox").split()]
        plt.gcf().set_size_inches(x2 - x1, y2 - y1)
    except ValueError:
        width = svgUnitToMpl(svg.getAttribute("width"), default=100)
        height = svgUnitToMpl(svg.getAttribute("height"), default=100)
        x1, y1, x2, y2 = 0, 0, width, height
        plt.gcf().set_size_inches(width/plt.gcf().dpi, height/plt.gcf().dpi)
    ax = plt.axes([0, 0, 1, 1], label=filename, frameon=False)
    plt.xticks([])
    plt.yticks([])
    for spine in ["left", "right", "top", "bottom"]:
        ax.spines[spine].set_visible(False)
    plt.xlim(x1, x2)
    plt.ylim(y2, y1)

    def parseGroup(node, trans, style):
        trans = parseTransformation(node.getAttribute("transform"), trans)
        style = get_style(node, style)
        for node in node.childNodes:
            if node.nodeType == node.TEXT_NODE:
                continue
            if node.tagName == "rect":
                plt_patch(node, trans, style, patch_rect)
            elif node.tagName == "ellipse":
                plt_patch(node, trans, style, patch_ellipse)
            elif node.tagName == "circle":
                plt_patch(node, trans, style, patch_circle)
            elif node.tagName == "path":
                plt_patch(node, trans, style, patch_path)
            elif node.tagName == "polygon":
                # matplotlib has a designated polygon patch, but it is easier to just convert it to a path
                node.setAttribute("d", "M "+node.getAttribute("points")+" Z")
                plt_patch(node, trans, style, patch_path)
            elif node.tagName == "polyline":
                node.setAttribute("d", "M " + node.getAttribute("points"))
                plt_patch(node, trans, style, patch_path)
            elif node.tagName == "line":
                node.setAttribute("d", "M " + node.getAttribute("x1") + "," + node.getAttribute("y1") + " " + node.getAttribute("x2") + "," + node.getAttribute("y2"))
                plt_patch(node, trans, style, patch_path)
            elif node.tagName == "g":
                parseGroup(node, trans, style)
            elif node.tagName == "text":
                plt_draw_text(node, trans, style)
            elif node.tagName == "defs":
                pass  # currently ignored might be used for example for gradient definitions
            elif node.tagName == "sodipodi:namedview":
                pass  # used for some inkscape metadata
            elif node.tagName == "image":
                link = node.getAttribute("xlink:href")
                im = openImageFromLink(link)
                plt.imshow(im, extent=[svgUnitToMpl(node.getAttribute("x")), svgUnitToMpl(node.getAttribute("x")) + svgUnitToMpl(node.getAttribute("width")),
                                       svgUnitToMpl(node.getAttribute("y")), svgUnitToMpl(node.getAttribute("y")) + svgUnitToMpl(node.getAttribute("height")),
                                       ], zorder=1)
            elif node.tagName == "metadata":
                pass  # we do not have to draw metadata
            else:
                print("Unknown tag", node.tagName, file=sys.stderr)

    parseGroup(doc.getElementsByTagName("svg")[0], plt.gca().transData, {})

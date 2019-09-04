from xml.dom import minidom
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms
import sys
import numpy as np
import re
import io
import base64
import matplotlib.text
from .arc2bez import arcToBezier

def deform(base_trans, x, y, sx=0, sy=0):
    return mtransforms.Affine2D([[x, sx, 0], [sy, y, 0], [0, 0, 1]]) + base_trans

def parseTransformation(transform_text, base_trans):
    if transform_text is None or transform_text == "":
        return base_trans
    transformations_list = re.findall(r"\w*\([-.,\d\s]*\)", transform_text)
    for transform_text in transformations_list:
        data = [float(s) for s in re.findall(r"[-.\d]+", transform_text)]
        command = re.findall(r"^\w+", transform_text)[0]
        if command == "translate":
            ox, oy = data
            base_trans = mtransforms.Affine2D([[1, 0, ox], [0, 1, oy], [0, 0, 1]]) + base_trans
        elif command == "rotate":
            a = np.deg2rad(data[0])
            ca, sa = np.cos(a), np.sin(a)
            base_trans = mtransforms.Affine2D([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]]) + base_trans
        elif command == "scale":
            if len(data) >= 2:
                x, y = data
            else:
                x, y = data[0], data[0]
            base_trans = mtransforms.Affine2D([[x, 0, 0], [0, y, 0], [0, 0, 1]]) + base_trans
        elif command == "skewX":
            x, = data
            x = np.tan(x*np.pi/180)
            base_trans = mtransforms.Affine2D([[1, x, 0], [0, 1, 0], [0, 0, 1]]) + base_trans
        elif command == "skewY":
            y, = data
            y = np.tan(y*np.pi/180)
            base_trans = mtransforms.Affine2D([[1, 0, 0], [y, 1, 0], [0, 0, 1]]) + base_trans
        elif command == "matrix":
            x, sx, sy, y, ox, oy = data
            base_trans = mtransforms.Affine2D([[x, sx, ox], [sy, y, oy], [0, 0, 1]]) + base_trans
        else:
            print("ERROR: unknown transformation", transform_text)
    return base_trans

def get_inline_style(node, base_style=None):
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

def get_css_style(node, css_list, base_style):
    style = {}
    if base_style is not None:
        style.update(base_style)
    classes = node.getAttribute("class").split()
    for css in css_list:
        css_condition, css_style = css
        if css_condition[0] == "." and css_condition[1:] in classes:
            style.update(css_style)
        elif css_condition[0] == "#" and css_condition[1:] == node.getAttribute("id"):
            style.update(css_style)
        elif css_condition == node.tagName:
            style.update(css_style)
    return style

def apply_style(style, patch):
    fill_opacity = float(style.get("opacity", 1)) * float(style.get("fill-opacity", 1))
    stroke_opacity = float(style.get("opacity", 1)) * float(style.get("stroke-opacity", 1))

    # matplotlib defaults differ
    if "fill" not in style:
        style["fill"] = "none"
    if "stroke" not in style:
        style["stroke"] = "none"

    for key, value in style.items():
        try:
            if key == "opacity":
                pass
                #patch.set_alpha(float(value))
            elif key == "fill":
                if value == "none" or value == "transparent":
                    patch.set_facecolor("none")
                else:
                    try:
                        r, g, b = mcolors.to_rgb(value)
                        patch.set_facecolor((r, g, b, fill_opacity))
                    except Exception as err:
                        patch.set_facecolor("none")
                        raise
            elif key == "fill-opacity":
                pass
            elif key == "stroke":
                if value == "none" or value == "transparent":
                    patch.set_edgecolor("none")
                else:
                    try:
                        r, g, b = mcolors.to_rgb(value)
                        patch.set_edgecolor((r, g, b, stroke_opacity))
                    except Exception as err:
                        patch.set_edgecolor("none")
                        raise
            elif key == "stroke-opacity":
                pass
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
                pass
            elif key == "font-weight":
                pass
            elif key == "font-style":
                pass
            elif key == "font-family":
                pass
            elif key == "font-variant":
                pass
            elif key == "font-stretch":
                pass
            elif key == "display":
                pass
            else:
                print("ERROR: unknown style key", key, file=sys.stderr)
        except ValueError:
            print("ERROR: could not set style", key, value, file=sys.stderr)
    return style

def font_properties_from_style(style):
    from matplotlib.font_manager import FontProperties
    fp = FontProperties()
    for key, value in style.items():
        if key == "font-family":
            fp.set_family(value)
        if key == "font-size":
            fp.set_size(svgUnitToMpl(value))
        if key == "font-weight":
            fp.set_weight(value)
        if key == "font-style":
            fp.set_style(value)
        if key == "font-variant":
            fp.set_variant(value)
        if key == "font-stretch":
            fp.set_stretch(value)
    return fp

def styleNoDisplay(style):
    return style.get("display", "inline") == "none" or \
            style.get("visibility", "visible") == "hidden" or \
            style.get("visibility", "visible") == "collapse"

def plt_patch(node, trans, style, constructor, ids, no_draw=False):
    trans = parseTransformation(node.getAttribute("transform"), trans)

    patch = constructor(node, trans)

    style = apply_style(get_inline_style(node, get_css_style(node, ids["css"], style)), patch)
    if not no_draw and not styleNoDisplay(style):
        plt.gca().add_patch(patch)
    if node.getAttribute("id") != "":
        ids[node.getAttribute("id")] = patch
    return patch

def patch_rect(node, trans):
    return mpatches.Rectangle(xy=(float(node.getAttribute("x")), float(node.getAttribute("y"))),
                              width=float(node.getAttribute("width")),
                              height=float(node.getAttribute("height")),
                              transform=trans)

def patch_ellipse(node, trans):
    return mpatches.Ellipse(xy=(float(node.getAttribute("cx")), float(node.getAttribute("cy"))),
                            width=float(node.getAttribute("rx"))*2,
                            height=float(node.getAttribute("ry"))*2,
                            transform=trans)

def patch_circle(node, trans):
    return mpatches.Circle(xy=(float(node.getAttribute("cx")), float(node.getAttribute("cy"))),
                           radius=float(node.getAttribute("r")),
                           transform=trans)

def plt_draw_text(node, trans, style, ids, no_draw=False):
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties

    trans = mtransforms.Affine2D([[1, 0, 0], [0, -1, 0], [0, 0, 1]]) + trans
    trans = parseTransformation(node.getAttribute("transform"), trans)
    pos = np.array([svgUnitToMpl(node.getAttribute("x")), -svgUnitToMpl(node.getAttribute("y"))])

    style = get_inline_style(node, get_css_style(node, ids["css"], style))

    text_content = ""
    patch_list = []
    for child in node.childNodes:
        text_content += child.firstChild.nodeValue
        if 1:
            style_child = get_inline_style(child, get_css_style(child, ids["css"], style))
            pos_child = pos.copy()
            if child.getAttribute("x") != "":
                pos_child = np.array([svgUnitToMpl(child.getAttribute("x")), -svgUnitToMpl(child.getAttribute("y"))])
            if child.getAttribute("dx") != "":
                pos_child[0] += svgUnitToMpl(child.getAttribute("dx"))
            if child.getAttribute("dy") != "":
                pos_child[1] -= svgUnitToMpl(child.getAttribute("dy"))
            #fp = FontProperties()#family="Helvetica", style="italic")
            path1 = TextPath(pos_child,
                             child.firstChild.nodeValue,
                             prop=font_properties_from_style(style_child))
            patch = mpatches.PathPatch(path1, transform=trans)

            apply_style(style_child, patch)
            if not no_draw and not styleNoDisplay(style_child):
                plt.gca().add_patch(patch)
            if child.getAttribute("id") != "":
                ids[child.getAttribute("id")] = patch
            patch_list.append(patch)
        else:
            text = plt.text(float(child.getAttribute("x")), float(child.getAttribute("y")),
                     child.firstChild.nodeValue,
                     transform=trans)
            apply_style(style, text)

    if node.getAttribute("id") != "":
        ids[node.getAttribute("id")] = patch_list

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
    return mpatches.PathPatch(path, transform=trans)

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

def parseStyleSheet(text):
    # remove line comments
    text = re.sub("//.*?\n", "", text)
    # remove multiline comments
    text = text.replace("\n", " ")
    text = re.sub("/\*.*?\*/", "", text)
    text = re.sub("/\*.*?\*/", "", text)

    style_definitions = []
    styles = re.findall("[^}]*{[^}]*}", text)
    for style in styles:
        condition, main = style.split("{", 1)
        parts = [part.strip().split(":", 1) for part in main[:-1].split(";") if part.strip() != ""]
        style_dict = {k: v.strip() for k, v in parts}
        for cond in condition.split(","):
            style_definitions.append([cond.strip(), style_dict])
    return style_definitions

def parseGroup(node, trans, style, ids, no_draw=False):
    trans = parseTransformation(node.getAttribute("transform"), trans)
    style = get_inline_style(node, style)

    patch_list = []
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE or child.nodeType == child.COMMENT_NODE:
            continue
        if child.tagName == "style":
            for childchild in child.childNodes:
                if childchild.nodeType == childchild.CDATA_SECTION_NODE:
                    ids["css"].extend(parseStyleSheet(childchild.wholeText))
        elif child.tagName == "rect":
            patch_list.append(plt_patch(child, trans, style, patch_rect, ids, no_draw=no_draw))
        elif child.tagName == "ellipse":
            patch_list.append(plt_patch(child, trans, style, patch_ellipse, ids, no_draw=no_draw))
        elif child.tagName == "circle":
            patch_list.append(plt_patch(child, trans, style, patch_circle, ids, no_draw=no_draw))
        elif child.tagName == "path":
            patch_list.append(plt_patch(child, trans, style, patch_path, ids, no_draw=no_draw))
        elif child.tagName == "polygon":
            # matplotlib has a designated polygon patch, but it is easier to just convert it to a path
            child.setAttribute("d", "M " + child.getAttribute("points") + " Z")
            patch_list.append(plt_patch(child, trans, style, patch_path, ids, no_draw=no_draw))
        elif child.tagName == "polyline":
            child.setAttribute("d", "M " + child.getAttribute("points"))
            patch_list.append(plt_patch(child, trans, style, patch_path, ids, no_draw=no_draw))
        elif child.tagName == "line":
            child.setAttribute("d", "M " + child.getAttribute("x1") + "," + child.getAttribute("y1") + " " + child.getAttribute("x2") + "," + child.getAttribute("y2"))
            patch_list.append(plt_patch(child, trans, style, patch_path, ids, no_draw=no_draw))
        elif child.tagName == "g":
            patch_list.append(parseGroup(child, trans, style, ids, no_draw=(no_draw or styleNoDisplay(style))))
        elif child.tagName == "text":
            patch_list.append(plt_draw_text(child, trans, style, ids, no_draw=no_draw))
        elif child.tagName == "defs":
            patch_list.append(parseGroup(child, trans, style, ids, no_draw=True))
        elif child.tagName == "clipPath":
            patch_list.append(parseGroup(child, trans, style, ids, no_draw=True))
        elif child.tagName == "symbol":
            patch_list.append(parseGroup(child, trans, style, ids, no_draw=True))
        elif child.tagName == "marker":
            patch_list.append(parseGroup(child, trans, style, ids, no_draw=True))
        elif child.tagName == "sodipodi:namedview":
            pass  # used for some inkscape metadata
        elif child.tagName == "image":
            link = child.getAttribute("xlink:href")
            im = openImageFromLink(link)
            if no_draw is False:
                im_patch = plt.imshow(im[::-1], extent=[svgUnitToMpl(child.getAttribute("x")), svgUnitToMpl(child.getAttribute("x")) + svgUnitToMpl(child.getAttribute("width")),
                                                        svgUnitToMpl(child.getAttribute("y")), svgUnitToMpl(child.getAttribute("y")) + svgUnitToMpl(child.getAttribute("height")),
                                                        ], zorder=1)
                patch_list.append(im_patch)
        elif child.tagName == "metadata":
            pass  # we do not have to draw metadata
        else:
            print("Unknown tag", child.tagName, file=sys.stderr)

    if node.getAttribute("id") != "":
        ids[node.getAttribute("id")] = patch_list
    return patch_list

def svgread(filename):
    # read the SVG file
    doc = minidom.parse(filename)

    svg = doc.getElementsByTagName("svg")[0]
    try:
        x1, y1, x2, y2 = [svgUnitToMpl(s.strip()) for s in svg.getAttribute("viewBox").split()]
        plt.gcf().set_size_inches((x2 - x1)/plt.gcf().dpi, (y2 - y1)/plt.gcf().dpi)
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

    parseGroup(doc.getElementsByTagName("svg")[0], plt.gca().transData, {}, {"css": []})

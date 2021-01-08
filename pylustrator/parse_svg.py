#!/usr/bin/env python
# -*- coding: utf-8 -*-
# parse_svg.py

# Copyright (c) 2016-2020, Richard Gerum
#
# This file is part of Pylustrator.
#
# Pylustrator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pylustrator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pylustrator. If not, see <http://www.gnu.org/licenses/>

from xml.dom import minidom
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.transforms as mtransforms
import matplotlib.path as mpath
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
import sys
import numpy as np
import re
import io
import base64
import matplotlib.text
from .arc2bez import arcToBezier


def deform(base_trans: mtransforms.Transform, x: float, y: float, sx: float = 0, sy: float = 0):
    """ apply an affine transformation to the given transformation """
    return mtransforms.Affine2D([[x, sx, 0], [sy, y, 0], [0, 0, 1]]) + base_trans


def parseTransformation(transform_text: str) -> mtransforms.Transform:
    """ convert a transform string in the svg file to a matplotlib transformation """
    base_trans = mtransforms.IdentityTransform()
    if transform_text is None or transform_text == "":
        return base_trans
    transformations_list = re.findall(r"\w*\([-.,\d\s]*\)", transform_text)
    for transform_text in transformations_list:
        data = [float(s) for s in re.findall(r"[-.\d]+", transform_text)]
        command = re.findall(r"^\w+", transform_text)[0]
        if command == "translate":
            try:
                ox, oy = data
            except ValueError:
                ox, oy = data[0], data[0]
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
            x, sy, sx, y, ox, oy = data
            base_trans = mtransforms.Affine2D([[x, sx, ox], [sy, y, oy], [0, 0, 1]]) + base_trans
        else:
            print("ERROR: unknown transformation", transform_text)
    return base_trans


def get_inline_style(node: minidom.Element, base_style: dict = None) -> dict:
    """ update the basestyle with the style defined by the style property of the node """
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


def get_css_style(node: minidom.Element, css_list: list, base_style: dict) -> dict:
    """ update the base_style with the style definitions from the stylesheet that are applicable to the node
        defined by the classes or id of the node
    """
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


def apply_style(style: dict, patch: mpatches.Patch) -> dict:
    """ apply the properties defined in style to the given patch """
    fill_opacity = float(style.get("opacity", 1)) * float(style.get("fill-opacity", 1))
    stroke_opacity = float(style.get("opacity", 1)) * float(style.get("stroke-opacity", 1))

    def readColor(value):
        try:
            return mcolors.to_rgb(value)
        except:
            # matplotlib cannot handle html colors in the form #000
            if len(value) == 4 and value[0] == "#":
                return readColor("#"+value[1]*2+value[2]*2+value[3]*2)
            raise

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
                        r, g, b = readColor(value)
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
                        r, g, b = readColor(value)
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
            elif key == "text-anchor":
                pass
            else:
                print("ERROR: unknown style key", key, file=sys.stderr)
        except ValueError:
            print("ERROR: could not set style", key, value, file=sys.stderr)
    return style


def font_properties_from_style(style: dict) -> FontProperties:
    """ convert a style to a FontProperties object """
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


def styleNoDisplay(style: dict) -> bool:
    """ check whether the style defines not to display the element """
    return style.get("display", "inline") == "none" or \
            style.get("visibility", "visible") == "hidden" or \
            style.get("visibility", "visible") == "collapse"


def plt_patch(node: minidom.Element, trans_parent_trans: mtransforms.Transform, style: dict, constructor: callable, ids: dict, no_draw: bool = False) -> mpatches.Patch:
    """ add a node to the figure by calling the provided constructor """
    trans_node = parseTransformation(node.getAttribute("transform"))
    style = get_inline_style(node, get_css_style(node, ids["css"], style))

    patch = constructor(node, trans_node + trans_parent_trans + plt.gca().transData, style, ids)
    if not isinstance(patch, list):
        patch = [patch]

    for p in patch:
        if not getattr(p, "is_marker", False):
            style = apply_style(style, p)
            p.style = style
            #p.set_transform(p.get_transform() + plt.gca().transData)
        p.trans_parent = trans_parent_trans
        p.trans_node = parseTransformation(node.getAttribute("transform"))

        if not no_draw and not styleNoDisplay(style):
                plt.gca().add_patch(p)
    if node.getAttribute("id") != "":
        ids[node.getAttribute("id")] = patch
    return patch


def clone_patch(patch: mpatches.Patch) -> mpatches.Patch:
    """ clone a patch element with the same properties as the given patch """
    if isinstance(patch, mpatches.Rectangle):
        return mpatches.Rectangle(xy=patch.get_xy(),
                                  width=patch.get_width(),
                                  height=patch.get_height())
    if isinstance(patch, mpatches.Circle):
        return mpatches.Circle(xy=patch.get_xy(),
                               radius=patch.get_radius())
    if isinstance(patch, mpatches.Ellipse):
        return mpatches.Ellipse(xy=patch.get_xy(),
                                width=patch.get_width(),
                                height=patch.get_height())
    if isinstance(patch, mpatches.PathPatch):
        return mpatches.PathPatch(patch.get_path())


def patch_rect(node: minidom.Element, trans: mtransforms.Transform, style: dict, ids: dict) -> mpatches.Rectangle:
    """ draw a svg rectangle node as a rectangle patch element into the figure (with the given transformation and style) """
    if node.getAttribute("d") != "":
        return patch_path(node, trans, style, ids)
    if node.getAttribute("ry") != "" and node.getAttribute("ry") != 0:
        return mpatches.FancyBboxPatch(xy=(float(node.getAttribute("x")), float(node.getAttribute("y"))),
                                       width=float(node.getAttribute("width")),
                                       height=float(node.getAttribute("height")),
                                       boxstyle=mpatches.BoxStyle.Round(0, float(node.getAttribute("ry"))),
                                       transform=trans)
    return mpatches.Rectangle(xy=(float(node.getAttribute("x")), float(node.getAttribute("y"))),
                              width=float(node.getAttribute("width")),
                              height=float(node.getAttribute("height")),
                              transform=trans)


def patch_ellipse(node: minidom.Element, trans: mtransforms.Transform, style: dict, ids: dict) -> mpatches.Ellipse:
    """ draw a svg ellipse node as a ellipse patch element into the figure (with the given transformation and style) """
    if node.getAttribute("d") != "":
        return patch_path(node, trans, style, ids)
    return mpatches.Ellipse(xy=(float(node.getAttribute("cx")), float(node.getAttribute("cy"))),
                            width=float(node.getAttribute("rx"))*2,
                            height=float(node.getAttribute("ry"))*2,
                            transform=trans)


def patch_circle(node: minidom.Element, trans: mtransforms.Transform, style: dict, ids: dict) -> mpatches.Circle:
    """ draw a svg circle node as a circle patch element into the figure (with the given transformation and style) """
    if node.getAttribute("d") != "":
        return patch_path(node, trans, style, ids)
    return mpatches.Circle(xy=(float(node.getAttribute("cx")), float(node.getAttribute("cy"))),
                           radius=float(node.getAttribute("r")),
                           transform=trans)


def plt_draw_text(node: minidom.Element, trans: mtransforms.Transform, style: dict, ids: dict, no_draw: bool = False):
    """ draw a svg text node as a text patch element into the figure (with the given transformation and style) """
    trans = parseTransformation(node.getAttribute("transform")) + trans + plt.gca().transData
    trans = mtransforms.Affine2D([[1, 0, 0], [0, -1, 0], [0, 0, 1]]) + trans
    if node.getAttribute("x") != "":
        pos = np.array([svgUnitToMpl(node.getAttribute("x")), -svgUnitToMpl(node.getAttribute("y"))])
    else:
        pos = np.array([0, 0])

    style = get_inline_style(node, get_css_style(node, ids["css"], style))

    dx = node.getAttribute("dx") or "0"
    dy = node.getAttribute("dy") or "0"

    text_content = ""
    patch_list = []
    for child in node.childNodes:
        if not isinstance(child, minidom.Element):
            partial_content = child.data
            pos_child = pos.copy()

            pos_child[0] += svgUnitToMpl(dx)
            pos_child[1] -= svgUnitToMpl(dy)
            style_child = style
            part_id = ""
        else:
            part_id = node.getAttribute("id")
            if child.firstChild is None:
                continue
            partial_content = child.firstChild.nodeValue
            style_child = get_inline_style(child, get_css_style(child, ids["css"], style))
            pos_child = pos.copy()
            if child.getAttribute("x") != "":
                pos_child = np.array([svgUnitToMpl(child.getAttribute("x")), -svgUnitToMpl(child.getAttribute("y"))])
            if child.getAttribute("dx") != "":
                pos_child[0] += svgUnitToMpl(child.getAttribute("dx"))
            if child.getAttribute("dy") != "":
                pos_child[1] -= svgUnitToMpl(child.getAttribute("dy"))

            text_content += partial_content
            path1 = TextPath(pos_child,
                             partial_content,
                             prop=font_properties_from_style(style_child))
            patch = mpatches.PathPatch(path1, transform=trans)

            apply_style(style_child, patch)
            if not no_draw and not styleNoDisplay(style_child):
                plt.gca().add_patch(patch)
            if part_id != "":
                ids[part_id] = patch
            patch_list.append(patch)

    if node.getAttribute("id") != "":
        ids[node.getAttribute("id")] = patch_list


def patch_path(node: minidom.Element, trans: mtransforms.Transform, style: dict, ids: dict) -> list:
    """ draw a path svg node by using a matplotlib path patch (with the given transform and style) """


    start_pos = None
    command = None
    verts = []
    codes = []
    angles = []

    current_pos = np.array([0, 0])

    elements = [a[0] for a in re.findall(r'(([-+]?\d*\.?\d+(?:e[-+]?\d*\.?\d+)?)|\w)', node.getAttribute("d"))]
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

    def addPathElement(type, *positions, no_angle=False):
        for pos in positions:
            verts.append(pos)
            codes.append(type)

        def vec2angle(vec):
            return np.arctan2(vec[1], vec[0])

        if not no_angle:
            n = len(positions)
            angles[-1].append(vec2angle(verts[-n] - verts[-n-1]))
            for i in range(n-1):
                angles.append([])
            angles.append([vec2angle(verts[-1] - verts[-2])])
        else:
            angles.append([])
        return positions[-1]

    i = len(elements)
    while elements:
        # if things go wrong for some reason prevent endless loops
        i -= 1
        if i <= 0:
            break
        if 'A' <= elements[-1] <= 'z':
            last_command = command
            command = elements.pop()
            absolute = command.isupper()
            command = command.lower()

        # moveto
        if command == "m":
            current_pos = addPathElement(mpath.Path.MOVETO, popPos(), no_angle=True)
            start_pos = current_pos

            command = "l"
        # close
        elif command == "z":
            # Close path
            current_pos = addPathElement(mpath.Path.CLOSEPOLY, start_pos, no_angle=True)

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

            current_pos = addPathElement(mpath.Path.CURVE4, *arcToBezier(current_pos, end, radius1, radius2, rotation, arc, sweep))

    # average angles when a point has more than one line
    for i in range(len(angles)):
        if len(angles[i]) == 1:
            angles[i] = angles[i][0]
        else:
            angles[i] = np.arctan2(np.mean(np.sin(angles[i])), np.mean(np.cos(angles[i])))

    def addMarker(i, name):
        marker_style, patches = ids[name]
        def add_list_elements(element):
            if isinstance(element, list):
                for e in element:
                    add_list_elements(e)
            else:
                parent_patch = element
                patch = clone_patch(parent_patch)
                apply_style(parent_patch.style, patch)

                a = angles[i]
                ca, sa = np.cos(a), np.sin(a)
                ox, oy = verts[i]
                trans2 = parent_patch.trans_node + mtransforms.Affine2D([[ca, -sa, ox], [sa, ca, oy], [0, 0, 1]]) + parent_patch.trans_parent + trans#+ plt.gca().transAxes
                if marker_style.get("markerUnits", "strokeWidth") == "strokeWidth":
                    s = svgUnitToMpl(style["stroke-width"])
                    trans2 = mtransforms.Affine2D([[s, 0, 0], [0, s, 0], [0, 0, 1]]) + trans2
                patch.set_transform(trans2)
                patch.is_marker = True
                patch_list.append(patch)
        add_list_elements(patches)

    patch_list = []

    if len(verts) == 0:
        return patch_list
    path = mpath.Path(verts, codes)
    patch_list.append(mpatches.PathPatch(path, transform=trans))

    if style.get("marker-start"):
        if style.get("marker-start").startswith("url(#"):
            name = style.get("marker-start")[len("url(#"):-1]
            if name in ids:
                addMarker(0, name)
    if style.get("marker-mid"):
        if style.get("marker-mid").startswith("url(#"):
            name = style.get("marker-mid")[len("url(#"):-1]
            if name in ids:
                for i in range(1, len(angles)-1):
                    addMarker(i, name)
    if style.get("marker-end"):
        if style.get("marker-end").startswith("url(#"):
            name = style.get("marker-end")[len("url(#"):-1]
            if name in ids:
                addMarker(len(angles)-1, name)

    return patch_list


def svgUnitToMpl(unit: str, default=None) -> float:
    """ convert a unit text to svg pixels """
    import re
    if unit == "":
        return default
    match = re.match(r"^([-.\d]*)(\w*).*$", unit)
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


def openImageFromLink(link: str) -> np.ndarray:
    """ load an embedded image file or an externally liked image file"""
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


def parseStyleSheet(text: str) -> list:
    """ parse a style sheet text """
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


def parseGroup(node: minidom.Element, trans: mtransforms.Transform, style: dict, ids: dict, no_draw: bool = False) -> list:
    """ parse the children of a group node with the inherited transformation and style """
    trans = parseTransformation(node.getAttribute("transform")) + trans
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
                if child.getAttribute("x") != "":
                    im_patch = plt.imshow(im[::-1], extent=[svgUnitToMpl(child.getAttribute("x")), svgUnitToMpl(child.getAttribute("x")) + svgUnitToMpl(child.getAttribute("width")),
                                                            svgUnitToMpl(child.getAttribute("y")), svgUnitToMpl(child.getAttribute("y")) + svgUnitToMpl(child.getAttribute("height")),
                                                            ], zorder=1)
                else:
                    pass#im_patch = plt.imshow(im[::-1], zorder=1)
                #patch_list.append(im_patch)
        elif child.tagName == "metadata":
            pass  # we do not have to draw metadata
        else:
            print("Unknown tag", child.tagName, file=sys.stderr)

    if node.getAttribute("id") != "":
        ids[node.getAttribute("id")] = [style, patch_list]

    return patch_list


def svgread(filename: str):
    """ read an SVG file """
    doc = minidom.parse(filename)

    svg = doc.getElementsByTagName("svg")[0]
    try:
        x1, y1, x2, y2 = [svgUnitToMpl(s.strip()) for s in svg.getAttribute("viewBox").split()]
        width, height = (x2 - x1)/plt.gcf().dpi, (y2 - y1)/plt.gcf().dpi
        if max([width, height]) > 8:
            f = 8/max([width, height])
            plt.gcf().set_size_inches(width*f, height*f)
        else:
            plt.gcf().set_size_inches(width, height)
    except ValueError:
        width = svgUnitToMpl(svg.getAttribute("width"), default=100)
        height = svgUnitToMpl(svg.getAttribute("height"), default=100)
        x1, y1, x2, y2 = 0, 0, width, height
        width /= plt.gcf().dpi
        height /= plt.gcf().dpi
        if max([width, height]) > 8:
            f = 8/max([width, height])
            plt.gcf().set_size_inches(width*f, height*f)
        else:
            plt.gcf().set_size_inches(width, height)
    ax = plt.axes([0, 0, 1, 1], label=filename, frameon=False)
    plt.xticks([])
    plt.yticks([])
    for spine in ["left", "right", "top", "bottom"]:
        ax.spines[spine].set_visible(False)
    plt.xlim(x1, x2)
    plt.ylim(y2, y1)

    parseGroup(doc.getElementsByTagName("svg")[0], mtransforms.IdentityTransform(), {}, {"css": []})

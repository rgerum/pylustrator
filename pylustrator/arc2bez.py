#!/usr/bin/env python
# -*- coding: utf-8 -*-
# arc2bez.py

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

import numpy as np

def mapToEllipse(pos, rx, ry, cosphi, sinphi, centerx, centery):
    x, y = pos
    x *= rx
    y *= ry

    xp = cosphi * x - sinphi * y
    yp = sinphi * x + cosphi * y

    return xp + centerx, yp + centery


def approxUnitArc(ang1, ang2):
    a = 4 / 3 * np.tan(ang2 / 4)

    x1 = np.cos(ang1)
    y1 = np.sin(ang1)
    x2 = np.cos(ang1 + ang2)
    y2 = np.sin(ang1 + ang2)

    return [
            [x1 - y1 * a, y1 + x1 * a],
            [x2 + y2 * a, y2 - x2 * a],
            [x2, y2]
          ]


def vectorAngle(ux, uy, vx, vy):
    sign = -1 if (ux * vy - uy * vx < 0) else 1

    dot = ux * vx + uy * vy

    if dot > 1:
        dot = 1
    
    if dot < -1:
        dot = -1

    return sign * np.arccos(dot)


def getArcCenter (px, py, cx, cy, rx, ry,
    largeArcFlag, sweepFlag, sinphi, cosphi, pxp, pyp):
    rxsq = np.power(rx, 2)
    rysq = np.power(ry, 2)
    pxpsq = np.power(pxp, 2)
    pypsq = np.power(pyp, 2)

    radicant = (rxsq * rysq) - (rxsq * pypsq) - (rysq * pxpsq)

    if radicant < 0:
        radicant = 0

    radicant /= (rxsq * pypsq) + (rysq * pxpsq)
    radicant = np.sqrt(radicant) * (-1 if largeArcFlag == sweepFlag else 1)

    centerxp = radicant * rx / ry * pyp
    centeryp = radicant * -ry / rx * pxp

    centerx = cosphi * centerxp - sinphi * centeryp + (px + cx) / 2
    centery = sinphi * centerxp + cosphi * centeryp + (py + cy) / 2

    vx1 = (pxp - centerxp) / rx
    vy1 = (pyp - centeryp) / ry
    vx2 = (-pxp - centerxp) / rx
    vy2 = (-pyp - centeryp) / ry

    ang1 = vectorAngle(1, 0, vx1, vy1)
    ang2 = vectorAngle(vx1, vy1, vx2, vy2)

    if sweepFlag == 0 and ang2 > 0:
        ang2 -= np.pi*2

    if sweepFlag == 1 and ang2 < 0:
        ang2 += np.pi*2

    return centerx, centery, ang1, ang2


def arcToBezier(pos1, pos2, rx, ry, xAxisRotation = 0, largeArcFlag = 0, sweepFlag = 0):
    px, py = pos1
    cx, cy = pos2
    curves = []

    if rx == 0 or ry == 0:
        return []

    sinphi = np.sin(xAxisRotation * np.pi * 2 / 360)
    cosphi = np.cos(xAxisRotation * np.pi * 2 / 360)

    pxp = cosphi * (px - cx) / 2 + sinphi * (py - cy) / 2
    pyp = -sinphi * (px - cx) / 2 + cosphi * (py - cy) / 2

    if pxp == 0 and pyp == 0:
        return []

    rx = np.abs(rx)
    ry = np.abs(ry)

    lambda_ = np.power(pxp, 2) / np.power(rx, 2) + np.power(pyp, 2) / np.power(ry, 2)

    if lambda_ > 1:
        rx *= np.sqrt(lambda_)
        ry *= np.sqrt(lambda_)

    centerx, centery, ang1, ang2 = getArcCenter(px, py, cx, cy, rx, ry,
                                    largeArcFlag, sweepFlag, sinphi, cosphi, pxp, pyp)

    # If 'ang2' == 90.0000000001, then `ratio` will evaluate to
    # 1.0000000001. This causes `segments` to be greater than one, which is an
    # unecessary split, and adds extra points to the bezier curve. To alleviate
    # this issue, we round to 1.0 when the ratio is close to 1.0.
    ratio = np.abs(ang2) / (np.pi * 2 / 4)
    if np.abs(1.0 - ratio) < 0.0000001:
        ratio = 1.0

    segments = np.max([np.ceil(ratio), 1])

    ang2 /= segments

    for i in range(int(segments)):
        curves.append(approxUnitArc(ang1, ang2))
        ang1 += ang2

    def curve(curve):
        x1, y1 = mapToEllipse(curve[0], rx, ry, cosphi, sinphi, centerx, centery)
        x2, y2 = mapToEllipse(curve[1], rx, ry, cosphi, sinphi, centerx, centery)
        x, y = mapToEllipse(curve[2], rx, ry, cosphi, sinphi, centerx, centery)

        return np.array([x1, y1]), np.array([x2, y2]), np.array([x, y])

    return [p for c in curves for p in curve(c)]

"""Bezier, a module for creating Bezier curves.
"""

import numpy as np


def two_points(pos, first_point, second_point):
    """
    :param pos: float/int; a parameterization.
    :param first_point: numpy array; a point.
    :param second_point: numpy array; a point.
    :return: numpy array; a point.
    """
    if not isinstance(first_point, np.ndarray) or not isinstance(
        second_point, np.ndarray
    ):
        raise TypeError("Points must be an instance of the numpy.ndarray!")
    if not isinstance(pos, (int, float)):
        raise TypeError("Parameter t must be an int or float!")
    return (1 - pos) * first_point + pos * second_point


def points(pos, pts):
    """
    Returns a list of points interpolated by the Bezier process
    :param pos: float/int; a parameterization.
    :param pts: list of numpy arrays; points.
    :return: list of numpy arrays; points.
    """
    new_points = []
    for i in range(0, len(pts) - 1):
        new_points += [two_points(pos, pts[i], pts[i + 1])]
    return new_points


def point(pos, pts):
    """
    Returns a point interpolated by the Bezier process
    :param pos: float/int; a parameterization.
    :param pts: list of numpy arrays; points.
    :return: numpy array; a point.
    """
    new_points = pts
    while len(new_points) > 1:
        new_points = points(pos, new_points)
    return new_points[0]


def curve(t_values, pts):
    """
    :param t_values: list of floats/ints; a parameterization.
    :param pts: list of numpy arrays; points.
    :return: list of numpy arrays; points. curve
    """
    if not hasattr(t_values, "__iter__"):
        raise TypeError(
            "`t_values` Must be an iterable of integers or floats, of length greater than 0 ."
        )
    if len(t_values) < 1:
        raise TypeError(
            "`t_values` Must be an iterable of integers or floats, of length greater than 0 ."
        )
    if not isinstance(t_values[0], (int, float)):
        raise TypeError(
            "`t_values` Must be an iterable of integers or floats, of length greater than 0 ."
        )
    curs = np.array([[0.0] * len(pts[0])])
    for i in t_values:
        curs = np.append(curs, [point(i, pts)], axis=0)
    curs = np.delete(curs, 0, 0)
    return curs

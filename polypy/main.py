# -*- coding: utf-8 -*-
#
import numpy

from .helpers import shoelace


class Polygon(object):
    def __init__(self, points):
        self.points = numpy.array(points)
        assert self.points.shape[1] == 2

        self.edges = numpy.roll(points, -1, axis=0) - points
        self.e_dot_e = numpy.einsum("ij,ij->i", self.edges, self.edges)

        self.area = 0.5 * shoelace(self.points)
        self.positive_orientation = self.area > 0
        if self.area < 0:
            self.area = -self.area

        self._is_convex_node = None
        return

    def _all_distances(self, x):
        x = numpy.array(x).T
        assert x.shape[0] == 2

        # Find closest point for each side segment
        # <https://stackoverflow.com/q/51397389/353337>
        diff = x.T[:, None, :] - self.points[None, :, :]
        diff_dot_edge = numpy.einsum("ijk,jk->ij", diff, self.edges)
        t = diff_dot_edge / self.e_dot_e

        # The squared distance from the point x to the line defined by the points x0, x1
        # is
        #
        # (<x1-x0, x1-x0> <x-x0, x-x0> - <x-x0, x1-x0>**2) / <x1-x0, x1-x0>
        #
        dist2_points = numpy.einsum("ijk,ijk->ij", diff, diff)
        dist2_sides = (self.e_dot_e * dist2_points - diff_dot_edge ** 2) / self.e_dot_e

        # Get the squared distance to the polygon. By default equals the distance to the
        # line, unless t < 0 (then the squared distance to x0), unless t > 1 (then the
        # squared distance to x1).
        t0 = t < 0.0
        t1 = t > 1.0
        t[t0] = 0.0
        t[t1] = 1.0
        dist2_sides[t0] = dist2_points[t0]
        dist2_sides[t1] = numpy.roll(dist2_points, -1, axis=1)[t1]

        idx = numpy.argmin(dist2_sides, axis=1)

        return t, dist2_sides, idx

    def squared_distance(self, x):
        """Get the squared distance of all points x to the polygon `poly`.
        """
        x = numpy.array(x)
        assert x.shape[1] == 2
        _, dist2_polygon, idx = self._all_distances(x)
        return dist2_polygon[numpy.arange(idx.shape[0]), idx]

    def _is_inside(self, x, idx):
        pts0 = self.points
        pts1 = numpy.roll(self.points, -1, axis=0)
        tri = numpy.array([x, pts0[idx], pts1[idx]])
        eps = 1.0e-15
        return (shoelace(tri) > -eps) == self.positive_orientation

    def is_inside(self, x):
        x = numpy.array(x)
        assert x.shape[1] == 2
        _, _, idx = self._all_distances(x)
        return self._is_inside(x, idx)

    def signed_distance(self, x):
        """Negative inside the polgon.
        """
        x = numpy.array(x)
        assert x.shape[1] == 2
        _, dist2_polygon, idx = self._all_distances(x)
        dist = numpy.sqrt(dist2_polygon[numpy.arange(idx.shape[0]), idx])

        # compute sign
        pts0 = self.points
        pts1 = numpy.roll(self.points, -1, axis=0)
        tri = numpy.array([x, pts0[idx], pts1[idx]])
        eps = 1.0e-15
        is_inside = (shoelace(tri) > -eps) == self.positive_orientation

        dist[is_inside] *= -1
        return dist

    def closest_points(self, x):
        """Get the closest points on the polygon.
        """
        x = numpy.array(x)
        assert x.shape[1] == 2
        t, dist2_polygon, idx = self._all_distances(x)

        pts0 = self.points[idx]
        pts1 = numpy.roll(self.points, -1, axis=0)[idx]
        r = numpy.arange(t.shape[0])
        t0 = t[r, idx]
        closest_points = (pts0.T * (1 - t0)).T + (pts1.T * t0).T
        return closest_points

    @property
    def is_convex_node(self):
        if self._is_convex_node is None:
            tri = numpy.array(
                [
                    numpy.roll(self.points, +1, axis=0),
                    self.points,
                    numpy.roll(self.points, -1, axis=0),
                ]
            )
            self._is_convex_node = numpy.equal(
                shoelace(tri) > 0, self.positive_orientation
            )
        return self._is_convex_node

    def plot(self):
        import matplotlib.pyplot as plt

        x = numpy.concatenate([self.points[:, 0], [self.points[0, 0]]])
        y = numpy.concatenate([self.points[:, 1], [self.points[0, 1]]])
        plt.plot(x, y, "-")
        return

    def show(self, *args, **kwargs):
        import matplotlib.pyplot as plt

        self.plot(*args, **kwargs)
        plt.show()
        return


def plot(points):
    Polygon(points).plot()
    return


def show(points):
    Polygon(points).show()
    return

# Licensed under GPL version 3 - see LICENSE.rst
import numpy as np
import pytest

from ..utils import (plane_with_hole, combine_disjoint_triangulations,
                     get_color, color_tuple_to_hex,
                     MARXSVisualizationWarning,
                     DisplayDict)
from ..mayavi import plot_object

def test_hole_round():
    '''Ensure that plane around the inner hole closes properly at the last point.'''
    outer = np.array([[-1, -1, 1, 1], [-1, 1, 1, -1], [0,0,0,0]]).T

    # Try out a rectangle and a circle - the two cases we are most likely to need.
    for n in [3, 4, 90, 360]:
        inner  = np.zeros((n, 3))
        phi = np.linspace(0, 2 * np.pi, n, endpoint=False)
        inner[:, 0] = np.sin(phi)
        inner[:, 1] = np.cos(phi)
        xyz, triangles = plane_with_hole(outer, inner)
        assert triangles[0][1] == triangles[-1][2]
        tri = np.array(triangles)
        # Technically, the order of the points in each triangle
        # is irrelevant, but the current implementation does it this way
        # and that's an easy way to check.
        # Check first point is always on outer rim
        assert set(tri[:, 0]) == set([0,1,2,3])
        # Check all points turn up in the middle
        assert set(tri[:, 1]) == set(np.arange(4 + n))
        # Check last point is always on inner rim
        assert set(tri[:, 2]) == set(np.arange(4, 4 + n))

def test_stack_triangulations():
    xyz = np.array([[-1. , -1. ,  0. ],
                    [-1. ,  1. ,  0. ],
                    [ 1. ,  1. ,  0. ],
                    [ 1. , -1. ,  0. ]])
    triangles = np.array([[0, 1, 2], [0, 2, 3]])
    xyz_out, tri_out = combine_disjoint_triangulations([xyz, xyz + 5.3],
                                                       [triangles, triangles])
    assert np.all(xyz_out[:4, :] == xyz)
    assert np.allclose(xyz_out[4:, :], xyz + 5.3)
    assert np.all(tri_out[:2, :] == triangles)
    assert np.all(tri_out[2:, :] == triangles + 4)

def test_color_roundtrip():
    '''Test that the different color convertes are consistent.'''
    colortup = get_color({'color': 'white'})
    assert colortup == (1.0, 1.0, 1.0)
    hexstr = color_tuple_to_hex(colortup)
    assert hexstr == '0xffffff'
    assert get_color({'color': '#ffffff'}) == (1.0, 1.0, 1.0)
    # repeat with a second color that has different values for rgb
    colortup = get_color({'color': '#ff013a'})
    # Note that matplotlib expects hex strings with '#' while python uses '0x'
    assert color_tuple_to_hex(colortup) == '0xff013a'

    # Int input
    assert color_tuple_to_hex((255, 255, 255)) == '0xffffff'

def test_color_hex_pad():
    '''Regression test: We want to color hexstring with leading zeroths'''
    assert color_tuple_to_hex((0., 1., .5)) == '0x00ff7f'

def test_color_to_hex_bad_input():
    with pytest.raises(ValueError) as e:
        out = color_tuple_to_hex('white')
    assert 'Input tuple must be all' in str(e.value)

    with pytest.raises(ValueError) as e:
        out = color_tuple_to_hex((-1, 0, 234))
    assert 'Int values in color tuple' in str(e.value)

    with pytest.raises(ValueError) as e:
        out = color_tuple_to_hex((1., 3., 0.3))
    assert 'Float values in color tuple' in str(e.value)

def test_no_display_warnings():
    '''Check that warnings are emitted without for classes, functions, and others'''
    class NoDisplay(object):
        pass

    with pytest.warns(MARXSVisualizationWarning) as record:
        plot_object(NoDisplay())

    # check that only one warning was raised
    assert len(record) == 1
    # check that the message matches
    assert 'No display dictionary found.' in record[0].message.args[0]

    def f():
        pass

    with pytest.warns(MARXSVisualizationWarning) as record:
        plot_object(f)

    # check that only one warning was raised
    assert len(record) == 1
    # check that the message matches
    assert 'No display dictionary found.' in record[0].message.args[0]


    with pytest.warns(MARXSVisualizationWarning) as record:
        plot_object(range)

    assert len(record) == 1
    assert 'No display dictionary found' in record[0].message.args[0]

def test_warning_unknownshape():
    '''Test warning (and no crash) for plotting stuff of unknown shape.'''
    class Display():
        display = {'shape': 'cilinder'}

    with pytest.warns(MARXSVisualizationWarning) as record:
        plot_object(Display())

    # check that only one warning was raised
    assert len(record) == 1
    # check that the message matches
    assert 'No function to plot cilinder.' in record[0].message.args[0]

def test_warning_noshapeset():
    '''Test warning (and no crash) for plotting stuff of unknown shape.'''
    class Display():
        display = {'form': 'cilinder'}

    with pytest.warns(MARXSVisualizationWarning) as record:
        plot_object(Display())

    # check that only one warning was raised
    assert len(record) == 1
    # check that the message matches
    assert '"shape" not set in display dict.' in record[0].message.args[0]

def test_DiplayDict():
    '''Simple mock-up using a DisplayDict variable.'''
    class A(object):
        pass

    a = A()
    b = A()
    b.geometry = A()
    b.geometry.value = 5

    a.display = DisplayDict(a, r=7)
    b.display = DisplayDict(b, value_1='w')

    assert a.display['r'] == 7
    assert b.display['value_1'] == 'w'
    assert b.display['value'] == 5
    # value is set in display and in geometry
    b.display['value'] = 6
    assert b.display['value'] == 6
    assert b.geometry.value == 5
    # values added to geometry later
    b.geometry.value2 = 'q'
    assert b.display['value2'] == 'q'
    # Make sure there is the right error only when used on an object without geomtry
    with pytest.raises(KeyError) as e:
        temp = a.display['q']
    # Make sure there is the right error if something is not found
    with pytest.raises(KeyError) as e:
        temp = b.display['1']

    # get works, too
    assert b.display.get('value') == 6
    assert a.display.get('qwer') is None
    assert a.display.get('asdf', 5) == 5

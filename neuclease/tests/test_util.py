import tempfile
import textwrap
import pytest

import numpy as np
from neuclease.util import uuids_match, read_csv_header, read_csv_col, connected_components, graph_tool_available

def test_uuids_match():
    assert uuids_match('abcd', 'abcdef') == True
    assert uuids_match('abc9', 'abcdef') == False


def test_read_csv_header():
    tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', prefix='test_read_csv_header')
    tmpfile.write(textwrap.dedent("""\
        a,b,c
        0,1,2
        3,4,5
    """))
    tmpfile.flush()
    assert read_csv_header(tmpfile.name) == ['a', 'b', 'c']


def test_read_csv_header_singlecol():
    tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', prefix='test_read_csv_header_singlecol')
    tmpfile.write(textwrap.dedent("""\
        a
        0
        3
    """))
    tmpfile.flush()
    assert read_csv_header(tmpfile.name) == ['a']


def test_read_csv_header_noheader():
    tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', prefix='test_read_csv_header_noheader')
    tmpfile.write(textwrap.dedent("""\
        0,1,2
        3,4,5
    """))
    tmpfile.flush()
    assert read_csv_header(tmpfile.name) is None


def test_read_csv_header_noheader_singlecol():
    tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', prefix='test_read_csv_header_noheader_singlecol')
    tmpfile.write(textwrap.dedent("""\
        0
        3
    """))
    tmpfile.flush()
    assert read_csv_header(tmpfile.name) is None


def test_read_csv_col():
    tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', prefix='test_read_csv_col')
    tmpfile.write(textwrap.dedent("""\
        a,b,c
        0,1,2
        3,4,5
    """))
    tmpfile.flush()
    
    col0 = read_csv_col(tmpfile.name)
    assert (col0  == [0,3]).all()
    assert col0.name == 'a'

    col1 = read_csv_col(tmpfile.name, 1)
    assert (col1  == [1,4]).all()
    assert col1.name == 'b'

    col2 = read_csv_col(tmpfile.name, 2)
    assert (col2  == [2,5]).all()
    assert col2.name == 'c'


def test_read_csv_col_noheader():
    tmpfile = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', prefix='test_read_csv_col')
    tmpfile.write(textwrap.dedent("""\
        0,1,2
        3,4,5
    """))
    tmpfile.flush()
    
    col0 = read_csv_col(tmpfile.name)
    assert (col0  == [0,3]).all()
    assert col0.name is None

    col1 = read_csv_col(tmpfile.name, 1)
    assert (col1  == [1,4]).all()
    assert col1.name is None

    col2 = read_csv_col(tmpfile.name, 2)
    assert (col2  == [2,5]).all()
    assert col2.name is None


@pytest.mark.skipif(not graph_tool_available(), reason="requires graph-tool")
def test_connected_components_gt():
    edges = [[1,2],
             [2,3],
             [4,5],
             [5,6]]

    cc_labels = connected_components(edges, 8, _lib='gt')
    assert cc_labels.shape == (8,)
    assert np.unique(cc_labels).shape == (4,)
    assert (cc_labels[0] != cc_labels[1])
    assert (cc_labels[1:4] == cc_labels[1]).all()
    assert (cc_labels[4:7] == cc_labels[4]).all()
    assert cc_labels[7] != cc_labels[6]


def test_connected_components_nx():
    edges = [[1,2],
             [2,3],
             [4,5],
             [5,6]]

    cc_labels = connected_components(edges, 8, _lib='nx')
    assert cc_labels.shape == (8,)
    assert np.unique(cc_labels).shape == (4,)
    assert (cc_labels[0] != cc_labels[1])
    assert (cc_labels[1:4] == cc_labels[1]).all()
    assert (cc_labels[4:7] == cc_labels[4]).all()
    assert cc_labels[7] != cc_labels[6]


if __name__ == "__main__":
    pytest.main(['-s', '--tb=native', '--pyargs', 'neuclease.tests.test_util'])
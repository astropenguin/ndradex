# dependencies
import ndradex


# test functions
def test_version():
    """Make sure the version is valid."""
    assert ndradex.__version__ == "0.3.1"


def test_author():
    """Make sure the author is valid."""
    assert ndradex.__author__ == "Akio Taniguchi"

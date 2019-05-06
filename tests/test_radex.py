# dependent packages
import ndradex


# test functions
def test_binary_existences():
    assert (ndradex.RADEX_BINPATH/'radex-uni').exists()
    assert (ndradex.RADEX_BINPATH/'radex-lvg').exists()
    assert (ndradex.RADEX_BINPATH/'radex-slab').exists()

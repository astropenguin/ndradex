# dependent packages
import numpy as np
import ndradex


# test functions
def test_binary_existences():
    assert (ndradex.RADEX_BINPATH/'radex-uni').exists()
    assert (ndradex.RADEX_BINPATH/'radex-lvg').exists()
    assert (ndradex.RADEX_BINPATH/'radex-slab').exists()


def test_radex_run():
    ds = ndradex.run('co', '1-0')
    assert np.isclose(ds['I'], 1.36)
    assert np.isclose(ds['F'], 2.684e-8)

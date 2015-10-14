import PAFClient
import numpy as np

client = PAFClient.PAFClient("ena-kazr", 3000)
count_array = np.array([0, 1, 100, 253000000000, .000253])
result_array = np.array([-79.29843367, -79.29843367, -39.29843367, 148.76397676, -151.23602324])


def test_convert_mW_to_dBm_0():
    assert np.isinf(client._convert_mW_to_dBm(0))


def test_convert_mW_to_dBm_100():
    assert client._convert_mW_to_dBm(100) == 20.


def test_convert_mW_to_dBm_one_hundredth():
    assert client._convert_mW_to_dBm(.01) == -20.


def test_convert_mW_to_dBm_large():
    np.testing.assert_almost_equal(client._convert_mW_to_dBm(253000), 54.031205212)


def test_convert_mW_to_dBm_small():
    np.testing.assert_almost_equal(client._convert_mW_to_dBm(.000000253), -65.968794788)


def test_convert_count_array_to_dBm():
    np.testing.assert_almost_equal(client._convert_count_to_dBm(count_array), result_array)


def test_convert_count_to_dBm():
    np.testing.assert_almost_equal(client._convert_count_to_dBm(1), -79.29843367)


def test_safe_convert_value_valid():
    assert client._safe_convert_value("122.1534") == 122.1534
    assert not client._safe_convert_value("122.1534") == "122.1534"


def test_safe_convert_value_invalid():
    assert client._safe_convert_value("122.15d34") == "122.15d34"

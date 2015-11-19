from pyarmret.io.PAFClient import PAFClient

def test_pafclient_import():
    assert PAFClient("localhost", 3000)

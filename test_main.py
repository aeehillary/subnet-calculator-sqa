import pytest
from fastapi.testclient import TestClient
from main import app, hitung_subnet

client = TestClient(app)

@pytest.mark.parametrize("ip,prefix,network,broadcast,hosts", [
    ("172.16.5.130", 25, "172.16.5.128", "172.16.5.255", 126),
    ("10.0.0.0", 30, "10.0.0.0", "10.0.0.3", 2),
    ("192.168.1.0", 31, "192.168.1.0", None, 2),
    ("192.168.1.5", 32, "192.168.1.5", None, 1),
])
def test_hitung_subnet(ip, prefix, network, broadcast, hosts):
    result = hitung_subnet(ip, prefix)
    assert result["network"] == network
    assert result["broadcast"] == broadcast
    assert result["usable_hosts"] == hosts

@pytest.mark.parametrize("ip,prefix", [
    ("256.1.1.1", 24), ("192.168.01.1", 24), ("192.168.1", 24),
    ("abc", 24), ("", 24), ("192.168.1.1", 33), ("192.168.1.1", -1),
])
def test_input_invalid(ip, prefix):
    with pytest.raises(ValueError):
        hitung_subnet(ip, prefix)

def test_api_subnet_success():
    response = client.get("/api/subnet?ip=172.16.5.130&prefix=25")
    assert response.status_code == 200
    assert response.json()["network"] == "172.16.5.128"

def test_api_invalid_returns_400():
    response = client.get("/api/subnet?ip=256.1.1.1&prefix=24")
    assert response.status_code == 400

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "<html" in response.text.lower()

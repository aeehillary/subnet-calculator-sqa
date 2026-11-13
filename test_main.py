import pytest
from fastapi.testclient import TestClient
from main import app, hitung_subnet, alokasi_vlsm

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


# ── VLSM Tests ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("network,kebutuhan,harapan", [
    (
        "192.168.1.0/24",
        [100, 50, 20, 2],
        [
            {"network_cidr": "192.168.1.0/25",   "usable_hosts": 126},
            {"network_cidr": "192.168.1.128/26",  "usable_hosts": 62},
            {"network_cidr": "192.168.1.192/27",  "usable_hosts": 30},
            {"network_cidr": "192.168.1.224/30",  "usable_hosts": 2},
        ],
    ),
    (
        "10.0.0.0/24",
        [50, 20],
        [
            {"network_cidr": "10.0.0.0/26",   "usable_hosts": 62},
            {"network_cidr": "10.0.0.64/27",  "usable_hosts": 30},
        ],
    ),
])
def test_alokasi_vlsm(network, kebutuhan, harapan):
    result = alokasi_vlsm(network, kebutuhan)
    assert len(result) == len(harapan)
    for blok, exp in zip(result, harapan):
        assert blok["network_cidr"] == exp["network_cidr"]
        assert blok["usable_hosts"] == exp["usable_hosts"]


@pytest.mark.parametrize("network,kebutuhan", [
    ("192.168.1.0/30", [50, 20]),    # kebutuhan melebihi kapasitas network
    ("not-valid", [10]),             # format network tidak valid
    ("192.168.1.0/24", []),          # kebutuhan kosong
    ("192.168.1.0/24", [0]),         # kebutuhan host 0 tidak valid
])
def test_vlsm_invalid(network, kebutuhan):
    with pytest.raises(ValueError):
        alokasi_vlsm(network, kebutuhan)


def test_api_vlsm_success():
    payload = {"network": "192.168.1.0/24", "kebutuhan_host": [100, 50, 20, 2]}
    response = client.post("/api/vlsm", json=payload)
    assert response.status_code == 200
    hasil = [b["network_cidr"] for b in response.json()]
    assert hasil == ["192.168.1.0/25", "192.168.1.128/26", "192.168.1.192/27", "192.168.1.224/30"]


def test_api_vlsm_invalid_returns_400():
    payload = {"network": "192.168.1.0/30", "kebutuhan_host": [50, 20]}
    response = client.post("/api/vlsm", json=payload)
    assert response.status_code == 400

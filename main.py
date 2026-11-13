from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel

app = FastAPI(title="Kalkulator Subnet & VLSM")
ROOT = Path(__file__).resolve().parent


def _parse_ipv4(ip: str):
    import re
    if not isinstance(ip, str) or not re.fullmatch(
        r"(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})\.(0|[1-9][0-9]{0,2})",
        ip,
    ):
        raise ValueError("Format IP harus tepat empat oktet tanpa spasi atau nol di depan.")
    octets = [int(part) for part in ip.split(".")]
    if any(part > 255 for part in octets):
        raise ValueError("Setiap oktet IP harus berada pada rentang 0 sampai 255.")
    return octets


def hitung_subnet(ip: str, prefix: int) -> dict:
    octets = _parse_ipv4(ip)
    if isinstance(prefix, bool) or not isinstance(prefix, int) or not 0 <= prefix <= 32:
        raise ValueError("Prefix harus berupa bilangan bulat dari 0 sampai 32.")

    ip_int = sum(value << (24 - 8 * i) for i, value in enumerate(octets))
    mask_int = ((0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF) if prefix else 0
    network_int = ip_int & mask_int
    wildcard_int = 0xFFFFFFFF ^ mask_int
    broadcast_int = network_int | wildcard_int

    def to_ip(value):
        return ".".join(str((value >> shift) & 255) for shift in (24, 16, 8, 0))

    if prefix <= 30:
        first_host = to_ip(network_int + 1)
        last_host = to_ip(broadcast_int - 1)
        usable_hosts = (2 ** (32 - prefix)) - 2
        broadcast = to_ip(broadcast_int)
    elif prefix == 31:
        first_host = to_ip(network_int)
        last_host = to_ip(broadcast_int)
        usable_hosts = 2
        broadcast = None
    else:
        first_host = last_host = to_ip(ip_int)
        usable_hosts = 1
        broadcast = None

    mask = to_ip(mask_int)
    return {
        "mask": mask,
        "network": to_ip(network_int),
        "broadcast": broadcast,
        "first_host": first_host,
        "last_host": last_host,
        "usable_hosts": usable_hosts,
    }


def alokasi_vlsm(network: str, kebutuhan_host: list[int]) -> list[dict]:
    """Kerangka fungsi alokasi VLSM yang belum diimplementasikan."""
    raise NotImplementedError("Fitur VLSM belum diimplementasikan")


class VLSMRequest(BaseModel):
    network: str
    kebutuhan_host: list[int]


@app.get("/")
def home():
    return FileResponse(ROOT / "index.html")


@app.get("/api/subnet")
def api_subnet(ip: str, prefix: int):
    try:
        return hitung_subnet(ip, prefix)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/vlsm")
def api_vlsm(payload: VLSMRequest):
    try:
        return alokasi_vlsm(payload.network, payload.kebutuhan_host)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))

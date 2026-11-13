from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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


@app.get("/")
def home():
    return FileResponse(ROOT / "index.html")


@app.get("/api/subnet")
def api_subnet(ip: str, prefix: int):
    try:
        return hitung_subnet(ip, prefix)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _parse_cidr(network: str):
    """Parse string CIDR seperti '192.168.1.0/24' → (network_int, prefix)."""
    import re
    if not isinstance(network, str) or "/" not in network:
        raise ValueError("Format network harus CIDR, contoh: 192.168.1.0/24")
    ip_part, prefix_part = network.split("/", 1)
    octets = _parse_ipv4(ip_part)
    try:
        prefix = int(prefix_part)
    except ValueError:
        raise ValueError("Prefix CIDR harus berupa bilangan bulat.")
    if not 0 <= prefix <= 32:
        raise ValueError("Prefix CIDR harus antara 0 dan 32.")
    mask_int = ((0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF) if prefix else 0
    ip_int = sum(v << (24 - 8 * i) for i, v in enumerate(octets))
    network_int = ip_int & mask_int
    return network_int, prefix


def _prefix_untuk_host(n: int) -> int:
    """Prefix terkecil yang menampung n usable host (≥1)."""
    import math
    if n < 1:
        raise ValueError("Jumlah host harus minimal 1.")
    # usable = 2^(32-p) - 2 >= n  →  p <= 32 - ceil(log2(n+2))
    bits = max(2, math.ceil(math.log2(n + 2)))
    return 32 - bits


def alokasi_vlsm(network: str, kebutuhan_host: list[int]) -> list[dict]:
    """Alokasikan subnet VLSM dari network CIDR untuk tiap kebutuhan host.

    Subnet dialokasikan dari yang terbesar ke terkecil (best-fit VLSM).
    Setiap elemen hasil berisi: network_cidr, mask, broadcast,
    first_host, last_host, usable_hosts.
    """
    if not kebutuhan_host:
        raise ValueError("Daftar kebutuhan host tidak boleh kosong.")
    if any(h < 1 for h in kebutuhan_host):
        raise ValueError("Setiap kebutuhan host harus minimal 1.")

    net_int, net_prefix = _parse_cidr(network)
    total_ip = 2 ** (32 - net_prefix)
    batas_atas = net_int + total_ip  # alamat tepat setelah network ini

    def to_ip(val: int) -> str:
        return ".".join(str((val >> s) & 255) for s in (24, 16, 8, 0))

    # Urutkan kebutuhan dari terbesar ke terkecil
    urutan = sorted(range(len(kebutuhan_host)), key=lambda i: -kebutuhan_host[i])
    kebutuhan_terurut = [kebutuhan_host[i] for i in urutan]

    hasil_terurut = []
    pointer = net_int  # alamat awal blok berikutnya

    for n in kebutuhan_terurut:
        prefix = _prefix_untuk_host(n)
        blok_size = 2 ** (32 - prefix)

        # Alignment: pointer harus kelipatan blok_size
        if pointer % blok_size != 0:
            pointer = ((pointer // blok_size) + 1) * blok_size

        blok_akhir = pointer + blok_size
        if blok_akhir > batas_atas:
            raise ValueError(
                f"Network {network} tidak cukup untuk menampung semua kebutuhan host."
            )

        mask_int = ((0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF)
        wildcard = 0xFFFFFFFF ^ mask_int
        broadcast_int = pointer | wildcard
        usable = blok_size - 2

        hasil_terurut.append({
            "network_cidr": f"{to_ip(pointer)}/{prefix}",
            "mask": to_ip(mask_int),
            "broadcast": to_ip(broadcast_int),
            "first_host": to_ip(pointer + 1),
            "last_host": to_ip(broadcast_int - 1),
            "usable_hosts": usable,
        })
        pointer = blok_akhir

    # Kembalikan dalam urutan sesuai input asli
    hasil = [None] * len(kebutuhan_host)
    for posisi, idx_asli in enumerate(urutan):
        hasil[idx_asli] = hasil_terurut[posisi]

    return hasil


class VLSMRequest(BaseModel):
    network: str
    kebutuhan_host: list[int]


@app.post("/api/vlsm")
def api_vlsm(payload: VLSMRequest):
    try:
        return alokasi_vlsm(payload.network, payload.kebutuhan_host)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))

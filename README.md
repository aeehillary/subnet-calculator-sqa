# Kalkulator Subnet IPv4

Aplikasi web sederhana untuk menghitung subnet IPv4 menggunakan FastAPI.

## Menjalankan aplikasi

Pastikan Python 3.12 dan `uv` sudah terpasang.

```bash
uv sync --dev
uv run fastapi dev main.py
```

Buka http://127.0.0.1:8000

## Menjalankan pengujian

```bash
uv run pytest -v
```

## Endpoint API

- `GET /api/subnet?ip=172.16.5.130&prefix=25`
- `GET /` untuk halaman web.

Fitur VLSM belum termasuk pada versi awal ini.

# Kalkulator Subnet IPv4

Aplikasi web sederhana untuk menghitung subnet IPv4 dan alokasi VLSM menggunakan FastAPI.

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
- `POST /api/vlsm` dengan body `{"network": "192.168.1.0/24", "kebutuhan_host": [100, 50, 20, 2]}`
- `GET /` untuk antarmuka web.

## Docker

### Build Image
```bash
docker build -t subnet-calculator .
```

### Menjalankan Container
```bash
docker run -d --name subnet-app -p 8000:8000 subnet-calculator
```

### Smoke Test Container Lokal
```bash
uv run python scripts/smoke_test.py http://127.0.0.1:8000
```

Hentikan dan hapus container setelah selesai:
```bash
docker rm -f subnet-app
```

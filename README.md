# Subnetting App

FLSM/VLSM subnet calculator for IPv4 and IPv6. Table-form solutions with network address, prefix, mask, usable range, broadcast, plus nth-usable-IP lookup. Ships as a local Windows `.exe`.

## Features

- IPv4 FLSM (equal-size split by new prefix or subnet count)
- IPv4 VLSM (variable-size allocation by hosts needed, largest-first)
- IPv6 equal-size splits
- Solution table: network address, subnet prefix, subnet mask, first usable, last usable, broadcast address, usable count
- Nth usable IP query, e.g. "What is the 100th IP in this range?"
- Edge cases: `/31` (RFC 3021, both usable), `/32` (single host)

## Tech Stack

- Frontend: Electron (`frontend/`)
- Backend: Python stdlib only, no runtime deps (`backend/src/subnet_calc/`)
- Bridge: line-delimited JSON over stdin/stdout (`cli.py` <-> `python-bridge.js`)
- Packaging: PyInstaller (backend) + electron-builder (`.exe`)

## UI Theme

- Background: `#1D2128`
- Accent: `#08CB00`
- Text: `#F6F6F6`

## Project Structure

```text
backend/
  src/subnet_calc/
    common.py       # parse, describe, nth usable
    ipv4_flsm.py    # equal-size IPv4 splits
    vlsm.py         # variable-size allocation
    ipv6_subnet.py  # IPv6 splits
    cli.py          # JSON stdin/stdout bridge
  tests/test_subnet_calc.py
frontend/
  main.js           # Electron entry, spawns backend
  preload.js        # contextBridge subnetApi
  python-bridge.js  # JSON-lines child_process wrapper
  src/index.html | styles.css | renderer.js
```

## Setup

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pyinstaller   # packaging only; runtime is stdlib (ipaddress, json)
python tests/test_subnet_calc.py -v
```

Electron dev (`npm start`) auto-uses `backend/.venv\Scripts\python.exe` when present, else falls back to system `python` with a console warning.

### Frontend

```powershell
cd frontend
npm install
npm start
```

## Usage

FLSM: enter `192.168.1.0/24` + new prefix `26` -> 4 x `/26` subnets.

VLSM: enter base `10.0.0.0/24` + requirements one per line:

```text
A:50
B:20
C:10
```

IPv6: enter `2001:db8::/48` + new prefix `56` -> 256 subnets.

Nth IP: enter subnet `192.168.1.0/26` + `100` -> `192.168.1.100` style answer (1-indexed within usable range).

## Backend CLI Protocol

One JSON object per stdin line, one JSON response per stdout line.

Requests:

```json
{"action": "flsm", "network": "192.168.1.0/24", "new_prefix": 26}
{"action": "vlsm", "network": "10.0.0.0/24", "requirements": [{"name": "A", "hosts_needed": 50}]}
{"action": "ipv6", "network": "2001:db8::/48", "new_prefix": 56}
{"action": "nth", "network": "192.168.1.0/26", "n": 100}
{"action": "describe", "network": "192.168.1.0/24"}
```

Responses:

```json
{"ok": true, "subnets": [...]}
{"ok": true, "ip": "192.168.1.100"}
{"ok": false, "error": "..."}
```

## Packaging (.exe)

```powershell
cd backend
pyinstaller build-cli.spec
# -> backend/dist/subnet-cli/subnet-cli.exe

cd ../frontend
npm run dist
# -> frontend/dist/*.exe (NSIS + portable, per electron-builder.yml)
```

In packaged mode Electron runs `resources/subnet-cli/subnet-cli.exe`. In dev it runs `python -m subnet_calc.cli`.

## Testing

```powershell
python backend/tests/test_subnet_calc.py -v
```

17 tests: FLSM splits, VLSM allocation order, exhaustion errors, `/31`/`/32`, nth-IP, IPv6 splits, invalid input.

## Code Standards

See [CODE_STANDARDS.md](context/CODE_STANDARDS.md). Priority: correctness > security > readability > performance.

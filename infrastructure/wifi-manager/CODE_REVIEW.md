# Code Review: wifi-manager

## Critical Bugs

### 1. `wifi_manager.py:127` — `and` should be `or` (logic inversion)
```python
if not profile.wireless_security and not profile.wireless_security.psk:
```
- If `wireless_security` is `None`: `not None` is `True`, then Python evaluates the second operand `not None.psk` → **`AttributeError` crash**
- If `wireless_security` is set but `psk` is `None`: first operand is `False`, short-circuits, condition is `False` → **the check is silently skipped**

Should be `or`:
```python
if not profile.wireless_security or not profile.wireless_security.psk:
```

---

### 2. `wifi_manager.py:332` vs `test_api.py:33` — Password mask length mismatch
```python
# wifi_manager.py
profile.wireless_security.psk = "*" * PASSWORD_MIN_LENGTH  # 8 asterisks

# test_api.py
assert body[key] == "*" * 10  # expects 10 asterisks
```
`PASSWORD_MIN_LENGTH = 8`, so the mask produces `"********"` but the test asserts `"**********"`. This test will always fail.

---

### 3. `test_api.py:89`, `test_connection.py:82` — `WifiAccessPoint` has no `security` field
```python
assert body["security"] == "wpa-psk"       # test_api.py
assert hotspot_ap.security == "wpa-psk"    # test_connection.py
```
`WifiAccessPoint` only defines `ssid` and `signal_strength`. There is no `security` field. Both assertions will always fail.

---

## Logic / Behavior Issues

### 4. `main.py:63-65` — `delete_connection_by_id` silently ignores "not found"
```python
def delete_connection_by_id(uuid: UUID, _=Depends(open_system_bus)):
    wm.delete_connection(uuid)  # returns bool, return value discarded
```
If the UUID doesn't exist, `wm.delete_connection` returns `False` but the endpoint still returns HTTP 200. Should raise a 404.

---

### 5. `wifi_manager.py:451` — Likely wrong exception caught in `delete_connection`
```python
except NmSettingsInvalidConnectionError:
    return False
```
`NmSettingsInvalidConnectionError` is for invalid connection data (bad settings). The appropriate exception for "connection not found" is `NetworkManagerUnknownConnectionError` (which is imported but unused here). If deleting a nonexistent UUID raises `NetworkManagerUnknownConnectionError`, this function will propagate an unhandled exception instead of returning `False`.

---

### 6. `wifi_manager.py:309` — `get_wifi_connections` will crash on open networks
`get_wifi_connections` calls `WifiConnectionSettings.from_profile(profile)` for every wifi profile. Due to bug #1, a profile with `wireless_security = None` (open/unsecured network) will crash with `AttributeError`.

---

### 7. `wifi_manager.py:259-260` — Scan result race condition
```python
_scan_for_access_points(device)
ap_paths = _get_access_point_paths(device)  # fetched immediately, before scan completes
```
Scanning is asynchronous at the hardware level. The AP list fetched right after `request_scan({})` will likely be from the previous scan cycle, not the newly triggered one.

---

### 8. `main.py` — Unhandled custom exceptions propagate as HTTP 500
`WifiDeviceNotFound`, `InvalidConnection`, `InvalidPassword` are never caught at the route level. Operations on a bad interface name or a profile with missing settings will return 500 instead of a proper 4xx response.

---

## Code Smells

### 9. `wifi_manager.py:303` — Shadows built-in `all`
```python
all = [resolve_connection_settings(path) for path in paths]
```
`all` is a Python built-in. Use a different name (e.g., `profiles`).

---

### 10. `wifi_manager.py:361-367` — Docstring return type wrong + typo
```python
def get_saved_connection_path(uuid: str) -> Optional[str]:
    """...
    Returns:
        bool: True if profile with given uuid exists, False otherwise.
    """
```
Returns `Optional[str]`, docstring says `bool`. Also "givee" should be "given".

---

### 11. `wifi_manager.py:145` — Redundant `None` check on a non-optional field
```python
password = self.password.get_secret_value() if self.password else None
```
`password` is typed `SecretStr` (not `Optional[SecretStr]`). The guard is dead code.

---

## Dockerfile Issues

### 12. `Dockerfile` — "builder" stage label with no second stage
```dockerfile
FROM python:3.13 AS builder
```
The `AS builder` label is never referenced with `COPY --from=builder`. The label is meaningless and the image includes all build dependencies in the final layer.

---

### 13. `Dockerfile` — `uv.lock` not copied; builds are not reproducible
```dockerfile
COPY pyproject.toml .
RUN uv pip install --system --no-cache-dir .
```
The `uv.lock` file exists but is not copied in. Dependencies will float to latest compatible versions on each build. Should be:
```dockerfile
COPY pyproject.toml uv.lock .
RUN uv sync --frozen --no-dev
```

---

## Test Issues

### 14. `test_api.py:65, 91` — Unnecessary f-strings
```python
client.delete(f"/wifi/connection/clear")   # no interpolation needed
```

---

### 15. `test_api.py:122` — Missing leading slash
```python
response = client.get("wifi/connection/saved")  # should be "/wifi/connection/saved"
```

---

### 16. `test_connection.py:5` — Misleading import alias
```python
import wifi_manager as nm
```
`nm` reads as "network manager" (the system daemon), but the module is the app's own `wifi_manager`. This is confusing since the code also wraps the actual NetworkManager library.

---

### 17. `conftest.py:34` — `sleep(1)` in autouse fixture taxes every test
The `delete_all_connections` fixture is `autouse=True` with `scope="function"`, adding a 1-second delay before every single test.

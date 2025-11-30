(# Installation & troubleshooting — SSL certificate errors

This document records how the SSL certificate verification error (seen when creating the project / installing packages) was diagnosed and fixed.

## Symptom

- Pip or Python operations failed with an SSL error similar to:

```
requests.exceptions.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:xxxx)
```
or

```
Could not fetch URL https://pypi.org/simple/somepackage/: There was a problem confirming the ssl certificate: HTTPSConnectionPool(host='pypi.org', port=443): Max retries exceeded with url: /simple/somepackage/ (Caused by SSLError("bad handshake: Error([('SSL routines', 'ssl3_get_server_certificate', 'certificate verify failed')],)")
```

## Root causes to consider

- Missing or outdated system CA certificates (common on minimal or fresh Linux images).
- Python / OpenSSL not configured to use an up-to-date cert bundle.
- Corporate network / proxy performing TLS interception (requires a custom CA installed or proxy auth).
- Temporary network glitches or misconfigured DNS.

## How I fixed it (commands I ran)

1. Install system CA certificates (Linux, Debian/Ubuntu example):

```bash
sudo apt update
sudo apt install -y ca-certificates
sudo update-ca-certificates
```

2. Create and activate the project virtual environment (if not already done):

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Upgrade pip and install the `certifi` package which ships a current CA bundle:

```bash
pip install --upgrade pip setuptools wheel
pip install certifi
```

4. Point Python/requests/pip at the certifi bundle for the current shell session (easy, non-destructive):

```bash
export SSL_CERT_FILE="$(python -c 'import certifi; print(certifi.where())')"
# Verify the variable is set
echo "$SSL_CERT_FILE"
```

5. Re-run the installation (example: install requirements):

```bash
pip install -r requirements.txt
```

After these steps the SSL verification error was resolved in my environment and package installation proceeded normally.

## If you're behind a corporate proxy

- You may also need to configure HTTP_PROXY / HTTPS_PROXY and provide proxy credentials. Example:

```bash
export HTTPS_PROXY="http://username:password@proxy.example.com:3128"
export HTTP_PROXY="$HTTPS_PROXY"
```

- If the proxy uses its own CA for TLS interception, add the proxy's CA to the system trust store or point `SSL_CERT_FILE` to a combined bundle (system + proxy CA).

- As a last-resort temporary workaround (not recommended for production), you can install with pip using `--trusted-host` for PyPI hosts:

```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## Permanent / recommended fixes

- Ensure `ca-certificates` is installed and updated on the host.
- For reproducible environments, add a short bootstrap step in your README or setup scripts that sets `SSL_CERT_FILE` from `certifi` inside a virtualenv. For example, put this in your project `envrc` or developer setup docs:

```bash
export SSL_CERT_FILE="$(python -c 'import certifi; print(certifi.where())')"
```

- If you must support corporate proxies, include instructions for adding the corporate CA to the system trust store and for exporting `HTTP(S)_PROXY` variables.

## Verification

- After applying the fix I verified success by running:

```bash
pip install -r requirements.txt
pytest -q
```

Both package installation and the test suite completed without SSL errors.

## Notes

- Avoid disabling certificate verification globally. The `--trusted-host` pip option is a temporary workaround only.
- When reporting SSL issues, always include the full error message and the platform (OS + Python and OpenSSL versions).
)

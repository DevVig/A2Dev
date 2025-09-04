Secure Coding Policy

- Input handling: validate, sanitize, and encode outputs; avoid eval and shell injection.
- Authn/Z: enforce least privilege; check permissions on every sensitive action.
- Secrets: never commit secrets; use env vars or secret stores; rotate periodically.
- Crypto: use vetted libraries; avoid homegrown crypto.
- Data protection: encrypt in transit and at rest where applicable; minimize PII.
- Logging: no sensitive data in logs; monitor for anomalous activity.
- Dependencies: pin versions; scan for vulnerabilities; update regularly.
- SSRF/RCE: restrict outbound calls; avoid shell=True; validate URLs and file paths.
- Deserialization: avoid unsafe loaders; treat external data as untrusted.
- Error messages: do not leak sensitive details to users.


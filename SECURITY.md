# Security Policy

## 🔒 Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.0.x   | :x:                |

---

## 🛡️ Security Architecture & Safety Guardrails

Bujji Agent executes actions on the host operating system with strict built-in safety controls:

1. **Destructive Command Blocking**: Commands matching dangerous patterns (e.g. `rm -rf`, `format`, `del /s /q`, `mkfs`, fork bombs) are intercepted by [`tools/shell.py`](file:///Users/n.harshavardhan/Desktop/Bujji%20Agent/tools/shell.py) and blocked unless explicit confirmation (`confirm=True`) is provided.
2. **System State Safeguards**: Operations like shutdown, reboot, and file deletion require explicit confirmation.
3. **No Credential Leakage**: Secrets and keys must strictly reside in `.env`, which is ignored by version control.
4. **Sandboxed Command Execution**: Shell commands execute with strict timeout enforcement (default 30 seconds).

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability in this project:

1. Please do **NOT** open a public issue on GitHub.
2. Report the vulnerability privately to the project maintainers via GitHub Security Advisories or by emailing security concerns to the maintainers.
3. Include detailed steps to reproduce the issue and any relevant logs.
4. You will receive an acknowledgment within 48 hours.

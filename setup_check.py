"""
setup_check.py — Cross-Platform Setup & Health Diagnostic Validator
Validates dependencies, API credentials, platform drivers, microphone, and browser automation.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

print("\n" + "═" * 60)
print("  Bujji Agent — Cross-Platform Setup Validator")
print("═" * 60 + "\n")

errors = []
warnings = []
ok = []


def check(name, test_fn):
    try:
        result = test_fn()
        status = result if isinstance(result, str) else "OK"
        ok.append(f"  ✅ {name}: {status}")
    except Exception as e:
        errors.append(f"  ❌ {name}: {e}")


def warn(name, test_fn):
    try:
        result = test_fn()
        status = result if isinstance(result, str) else "OK"
        ok.append(f"  ✅ {name}: {status}")
    except Exception as e:
        warnings.append(f"  ⚠️  {name}: {e}")


# ── 1. Python Environment ─────────────────────────────────────────
v = sys.version_info
if v.major == 3 and v.minor >= 10:
    ok.append(f"  ✅ Python: {sys.version.split()[0]} (supported)")
else:
    warnings.append(f"  ⚠️  Python: {sys.version.split()[0]} (3.10+ recommended)")


# ── 2. Platform Abstraction Layer Check ───────────────────────────
try:
    from platform_layer import get_platform
    plat = get_platform()
    ok.append(f"  ✅ Platform Detection: {plat.os_name} ({sys.platform})")
except Exception as e:
    errors.append(f"  ❌ Platform Layer: {e}")


# ── 3. Dependencies ───────────────────────────────────────────────
REQUIRED_PACKAGES = {
    "groq": "groq",
    "sounddevice": "sounddevice",
    "numpy": "numpy",
    "pyautogui": "pyautogui",
    "PIL": "Pillow",
    "playwright": "playwright",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "dotenv": "python-dotenv",
    "websockets": "websockets",
    "httpx": "httpx"
}

for module_name, pkg_name in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
        ok.append(f"  ✅ Package: {pkg_name}")
    except ImportError:
        errors.append(f"  ❌ Package missing: {pkg_name} — run: pip install {pkg_name}")


# ── 4. API Configuration ──────────────────────────────────────────
api_key = os.getenv("GROQ_API_KEY", "")
if api_key and api_key.startswith("gsk_"):
    ok.append(f"  ✅ GROQ_API_KEY: Configured ({api_key[:8]}...)")
else:
    errors.append("  ❌ GROQ_API_KEY: Missing or invalid in .env")


# ── 5. Groq Connectivity Test ─────────────────────────────────────
if api_key:
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Respond with 'OK'."}],
            max_tokens=10
        )
        raw_ans = resp.choices[0].message.content
        ans = raw_ans.strip() if raw_ans else "OK"
        ok.append(f"  ✅ Groq LLM API: Connected ({model} → '{ans}')")
    except Exception as e:
        errors.append(f"  ❌ Groq API Error: {e}")


# ── 6. Audio Devices ──────────────────────────────────────────────
try:
    import sounddevice as sd
    devices = sd.query_devices()
    input_devs = [d for d in devices if d.get("max_input_channels", 0) > 0]
    if input_devs:
        ok.append(f"  ✅ Audio Input: {len(input_devs)} input device(s) found")
    else:
        warnings.append("  ⚠️  Audio Input: No microphone devices detected")
except Exception as e:
    warnings.append(f"  ⚠️  Sounddevice check: {e}")


# ── 7. Playwright Browser ─────────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(headless=True)
            b.close()
            ok.append("  ✅ Playwright: Chromium browser available")
        except Exception:
            warnings.append("  ⚠️  Playwright: Run 'python -m playwright install chromium'")
except Exception as e:
    warnings.append(f"  ⚠️  Playwright diagnostic: {e}")


# ── Print Report ──────────────────────────────────────────────────
print("\n" + "─" * 40 + " RESULTS " + "─" * 40)
for msg in ok:
    print(msg)
for msg in warnings:
    print(msg)
for msg in errors:
    print(msg)
print("─" * 89)

if errors:
    print(f"\n❌ Setup check failed with {len(errors)} error(s). Please resolve them before running Bujji.\n")
    sys.exit(1)
else:
    print(f"\n✨ Setup check passed! Bujji is ready to run.\n")
    sys.exit(0)

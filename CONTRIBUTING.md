# Contributing to Bujji Voice Task Agent

Thank you for your interest in contributing to **Bujji Agent**! We welcome contributions, bug reports, feature suggestions, and documentation improvements.

---

## 🛠️ Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/imharsha33/Voice-Text--Task-Agent.git
   cd Voice-Text--Task-Agent
   ```

2. **Set Up Virtual Environment**
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and supply your GROQ_API_KEY
   ```

5. **Run Preflight Diagnostics & Tests**
   ```bash
   python setup_check.py
   python -m unittest discover -s tests -p "test_*.py"
   ```

---

## 📐 Architecture Guidelines

- **Zero OS Leakage**: Never place platform-specific APIs (`osascript`, PowerShell, Win32) inside `core/` or `tools/`. All OS-specific code belongs in `platform_layer/macos/` or `platform_layer/windows/`.
- **Path Safety**: Always use `pathlib.Path` and `Path.home()`. Never hardcode absolute system paths or user names.
- **Security Confirmation**: Destructive tools (file deletion, system shutdown, mass process termination) must implement `confirm: bool = False` safety gating.
- **Provider Interfaces**: Voice STT, TTS, and LLM backends must inherit from `SpeechToTextProvider`, `TextToSpeechProvider`, and `BaseLLMProvider`.

---

## 🧪 Testing Guidelines

Before opening a Pull Request:
1. Ensure all unit tests pass with zero failures:
   ```bash
   python -m unittest discover -s tests -p "test_*.py"
   ```
2. Run the diagnostic setup validator:
   ```bash
   python setup_check.py
   ```
3. Add new tests under `tests/` for any new tools or platform capabilities.

---

## 📋 Pull Request Process

1. Create a feature branch (`git checkout -b feature/amazing-feature`).
2. Commit your changes (`git commit -m "feat: add amazing feature"`).
3. Push to your branch (`git push origin feature/amazing-feature`).
4. Open a Pull Request on GitHub.

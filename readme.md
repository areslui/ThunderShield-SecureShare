# 🛡️ ThunderShield SecureShare

> Encrypted peer-to-peer LAN file sharing for Windows & macOS — no cloud, no accounts, no data leaving your network.

Built by **[ThunderShield (雷盾資安)](https://www.tssecurity.com.tw)** · Based on open-source Python file sharing

---

## ✅ Features

- 🔐 **AES-256-GCM encryption in transit** — mandatory, on by default, no configuration required
- ✅ **SHA-256 file integrity verification** — every transfer is verified, shown as ✅ Verified or ❌ Integrity Failed
- 🔑 **Ephemeral Diffie-Hellman key exchange** — no pre-shared keys, fresh session key per transfer
- 📤 **Sender Tab** — file browser or drag & drop, auto host discovery, custom filename, configurable port
- 📥 **Receiver Tab** — choose save location, one-click start/stop listening
- 🔍 **Auto Host Discovery** — scan and list available hosts on the LAN automatically
- 📊 **Real-time Transfer Progress** — live status and logs per transfer
- 📁 **Multi-file Support** — send multiple files in one go (auto-zipped)
- 🌐 **Zero internet dependency** — LAN/Wi-Fi only, air-gap friendly
- 🖥️ **Cross-platform** — Windows & macOS (Linux supported)

---

## 📸 Screenshots

> ![Sender Tab](assets/sender_tab.png)
> ![Receiver Tab](assets/receiver_tab.png)

---

## 🚀 Getting Started

### Requirements
- Python 3.7+
- Windows, macOS, or Linux
- No internet connection required (runs on local network)

### Installation

1. Clone the repo:
```bash
git clone https://github.com/areslui/ThunderShield-SecureShare.git
cd ThunderShield-SecureShare
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app:
```bash
python main.py
```

### 📦 Packaging (Optional)

Build a standalone executable (no Python install needed for end users):

```bash
# Windows
pyinstaller --onefile --windowed main.py

# macOS
pyinstaller --onefile --windowed main.py
```

---

## 🔒 Security Design

| Feature | Implementation |
|---|---|
| Encryption | AES-256-GCM (authenticated encryption) |
| Key Exchange | X25519 ephemeral Diffie-Hellman |
| Key Derivation | HKDF-SHA256 (32-byte session key) |
| Integrity | SHA-256 checksum verified on receiver |
| Fallback | None — plaintext transfers are disabled |

All transfers are encrypted and verified by default. There is no opt-out — this is by design.

---

## 🙌 Contributing

Contributions, bug reports, and feature requests are welcome!

1. Fork the repo
2. Create a new branch: `git checkout -b feature-xyz`
3. Commit your changes: `git commit -m 'Add new feature'`
4. Push and open a Pull Request

---

## 📢 License

MIT License – free to use, modify, and distribute.

---

## 🙏 Acknowledgements

Based on the open-source [Python File Share](https://github.com/asim-builds/File-Share) project by [@asim-builds](https://github.com/asim-builds).
Security layer (AES-256-GCM, X25519, SHA-256) added by ThunderShield (雷盾資安).

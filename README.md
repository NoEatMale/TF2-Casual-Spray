# 🌍 TF2 Casual Spray Sync
> **"Bringing the vibrant spray culture back to Team Fortress 2 Casual matches."**

[![Release](https://img.shields.io/github/v/release/NoEatMale/TF2-Casual-Spray?color=orange)](https://github.com/NoEatMale/TF2-Casual-Spray/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TF2](https://img.shields.io/badge/Game-TF2-red)](https://www.teamfortress.com/)

---

## 📖 Introduction
I truly missed the days when we could see everyone's unique and funny custom sprays in Casual matchmaking. Since official servers disabled automatic spray downloads, the game felt a bit less lively. 

**TF2 Casual Spray Sync** is a lightweight, background tool that allows players to share and see each other's custom sprays again in official Valve servers.

---

## ✨ Key Features
* **Background Syncing:** Automatically uploads and downloads `.vtf` spray files every 5 minutes.
* **Smart Vault System:** Keeps a local backup to prevent TF2 from wiping your collected sprays.
* **Zip Optimization:** Uses compressed downloads for mass synchronization to save your bandwidth.
* **VAC-Safe:** Operates strictly on the filesystem level. No memory injection, no process modification.
* **Auto-Startup:** Optional Windows startup registration for a "set it and forget it" experience.

---

## 🛠️ How to Use
1. **Download** the latest `.exe` from the [Releases](https://github.com/NoEatMale/TF2-Casual-Spray/releases) page.
2. **Run** the program. On the first run, it will ask for permission to add itself to the Windows Startup (Y/N).
3. **Play TF2.** The console will hide itself and work quietly in the background. 
4. **Enjoy!** You will start seeing sprays from other users of this tool in your Casual matches.

---

## 🛡️ Safety & VAC Safety
* **100% VAC Safe:** This program does **not** inject code or modify game memory. It strictly handles file transfers in the `tf/materials/temp` directory.
* **Open Source:** Every line of code is public. Feel free to review the logic in `TF2_Spray_Sync.py`.
* **No Bloat:** Small footprint, zero FPS drop during gameplay.

---

## 🤝 Credits & Support
* **Lead Developer:** [NoEatMale](https://github.com/NoEatMale)
* **AI Assistance:** Developed with the support of Google Gemini.
* **Community Links:** * [Download Latest Version](https://github.com/NoEatMale/TF2-Casual-Spray/releases)
    * [Report Issues](https://github.com/NoEatMale/TF2-Casual-Spray/issues)

---
© 2026 NoEatMale. All rights reserved.

# ⚙️ PiDebugger v5.1 Modular

## ✨ VSCode Style + Système Modulaire Complet

**Interface professionnelle avec modules contextuels dynamiques !**

### 🏗️ Architecture

```
pidebugger_v5.1/
├── pidebugger_v5.1.py       # Application principale (1200 lignes)
├── core/                     # Système de détection
│   ├── context_detector.py  # Détection 10+ contextes
│   ├── module_manager.py    # Gestion modules
│   └── __init__.py
├── modules/                  # Modules spécialisés
│   ├── base_module.py       # Module de base
│   ├── uboot_module.py      # Commandes U-Boot
│   ├── linux_module.py      # Commandes Linux
│   ├── atf_module.py        # ARM Trusted Firmware
│   └── __init__.py
└── README_V5.1.md
```

### 🎨 Interface

```
┌──────────────────────────────────────────────┐
│ ⚙️ PiDebugger v5.1 Modular                  │
├──┬─────────────────┬───────────────────────┤
│🏠│ 💻 Terminal     │ 📦 Modules            │
│📊│ U-Boot 2024.01  │ ✅ uboot_module       │
│💾│ Marvell>>       │                       │
│💡│ > [cmd] [Send]  │ 💡 Suggestions        │
│⚙️│                 │ • help                │
│  │                 │ • printenv            │
│  │                 │ • bdinfo              │
├──┴─────────────────┴───────────────────────┤
│ Context: U-Boot │ Port: USB0 │ Uptime     │
└──────────────────────────────────────────────┘
```

### 🚀 Installation

```bash
tar -xzf pidebugger_v5.1.tar.gz
cd pidebugger_v5.1

pip3 install PyQt6 pyserial

python3 pidebugger_v5.1.py
```

### 🧩 Système Modulaire

**Détection automatique → Modules activés:**
- BootROM → bootrom_module
- U-Boot → uboot_module
- Linux → linux_module
- ATF → atf_module

**Suggestions contextuelles:**
- U-Boot: help, printenv, bdinfo, boot
- Linux: uname, lscpu, ifconfig, ps

**Hardware extraction:**
- Version U-Boot/Linux
- SoC, Board, Architecture
- Détection automatique

### ✨ Fonctionnalités

✅ Interface VSCode professionnelle  
✅ 10+ contextes détectés  
✅ Modules chargés dynamiquement  
✅ Suggestions contextuelles  
✅ Timeline complète  
✅ Hardware auto-détecté  
✅ Sidebar icônes  
✅ Status bar complète  
✅ Bouton Enter  
✅ Thème Dark+ cohérent  

**Version:** 5.1 Modular  
**Status:** Production Ready

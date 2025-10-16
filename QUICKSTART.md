# ⚡ Quick Start - 2 Minutes

Parti in 2 minuti. Zero configurazione complicata.

## 🚀 Installazione Rapida

```bash
# 1. Setup automatico
python setup.py

# 2. Health check (verifica sistema)
python health_checker.py

# 3. Avvia GUI
python famousify_load_tester_v2.py

# FATTO! 🎉
```

## 🎯 Primo Test (GUI)

1. **Apri GUI** - Doppio click su `famousify_load_tester_v2.py`

2. **Tab "Configuration"**
   - Base URL: `https://web-production-abb48.up.railway.app`
   - Admin Token: `famousify-admin-2025`
   - Click "Save Config"

3. **Tab "Run Test"**
   - Pipeline: **USER** (standard)
   - Total Requests: `3`
   - Concurrent: `1`
   - Click "▶ Start Test"

4. **Aspetta ~2-3 minuti** - Guarda il log live

5. **Tab "Results"** - Vedi il report

## ⌨️ Primo Test (CLI)

```bash
python famousify_load_tester_v2.py --cli

# Quando chiede:
Pipeline [1]: 1         # 1=USER, 2=TEEINBLUE
Total requests [10]: 3
Concurrent [10]: 1
Start test? yes
```

## 🔄 Test con Scenari Predefiniti

```bash
# Lista scenari disponibili
python test_scenarios.py list

# Smoke test USER
python test_scenarios.py user_smoke

# Smoke test TEEINBLUE  
python test_scenarios.py teeinblue_smoke

# Confronto pipeline
python test_scenarios.py quick_compare
```

## 💰 Calcolo Costi

```bash
# Tabella costi rapida
python cost_calculator.py table

# Calcolatore interattivo
python cost_calculator.py calc

# Budget mensile
python cost_calculator.py budget 50
```

**Costi base:**
- Ogni generazione: €0.08
- Margine sicurezza: +10%
- USER pipeline: ~50s/gen
- TEEINBLUE pipeline: ~120s/gen

**Esempi:**
- 3 req: €0.26 (~3min)
- 10 req: €0.88 (~5min USER, ~10min TEEINBLUE)
- 50 req: €4.40 (~15min USER, ~30min TEEINBLUE)

**Test con 5 richieste:**
- ⏱️ Tempo: ~2-3 minuti
- 💰 Costo: ~€0.40 (5 × €0.08)
- ✅ Success rate atteso: >90%
- 📈 Avg time: 45-60 secondi

## 🔧 Configurazione Alternativa (.env)

```bash
# Copia template
cp .env.example .env

# Modifica .env con il tuo editor
nano .env
```

## 📦 Build EXE (Opzionale)

```bash
# Installa PyInstaller
pip install pyinstaller

# Build
python build_exe.py

# Output: dist/FamousifyLoadTester.exe
```

## 🆘 Problemi Comuni

### ❌ "GUI not available"
```bash
# Usa CLI mode
python famousify_load_tester_v2.py --cli
```

### ❌ "Module not found"
```bash
# Reinstalla dependencies
pip install -r requirements.txt
```

### ❌ "Connection timeout"
```bash
# Verifica che Railway sia attivo
curl https://web-production-abb48.up.railway.app/health
```

### ❌ "HTTP 401 Unauthorized"
```bash
# Verifica admin token in .env
cat .env | grep ADMIN_TOKEN
```

## 🎓 Test Scenarios

### Smoke Test (veloce)
```
Requests: 3
Concurrent: 1
Time: ~2 min
Cost: €0.24
```

### Load Test (normale)
```
Requests: 50
Concurrent: 10
Time: ~15 min
Cost: €4.00
```

### Stress Test (intenso)
```
Requests: 200
Concurrent: 20
Time: ~45 min
Cost: €16.00
```

## 📁 Struttura File

```
famousify-load-tester-v2/
├── famousify_load_tester_v2.py  # Main app
├── setup.py                      # Auto installer
├── build_exe.py                  # EXE builder
├── requirements.txt              # Dependencies
├── .env                          # Your config (create this)
├── .env.example                  # Config template
├── README.md                     # Full docs
├── QUICKSTART.md                 # This file
└── results/                      # Auto-created
    ├── reports/                  # JSON reports
    └── images/                   # Downloaded images
```

## 🔥 Pro Tips

1. **Primo avvio**: Fai sempre un test piccolo (3-5 requests)
2. **Monitoraggio**: Guarda il log real-time per catch errors
3. **Reports**: Sono in `results/reports/` - doppio click per aprire
4. **Costs**: Ogni request = €0.08, pianifica budget
5. **Timing**: Test in orari non-peak per risultati migliori

## 🚀 Ready!

Ora sei pronto. Domande? Vedi `README.md` per la docs completa.

**Happy Testing! 🧪**
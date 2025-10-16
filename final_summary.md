# 🚀 Famousify Load Tester V2 - Complete Setup Guide

## 📁 File Structure

```
famousify-load-tester-v2/
│
├── 🎯 Core Application
│   ├── famousify_load_tester_v2.py    # Main app (GUI + CLI, multi-pipeline)
│   ├── test_scenarios.py               # Predefined test scenarios
│   ├── health_checker.py               # Pre-test system validation
│   ├── utils.py                        # Analysis & utilities
│   └── automation_examples.py          # CI/CD examples
│
├── 🔧 Setup & Build
│   ├── setup.py                        # Auto installer
│   ├── build_exe.py                    # EXE builder
│   ├── requirements.txt                # Dependencies
│   ├── .env.example                    # Config template
│   └── .gitignore                      # Git rules
│
├── 📚 Documentation
│   ├── README.md                       # Full documentation
│   ├── QUICKSTART.md                   # 2-minute guide
│   ├── PROJECT_STRUCTURE.md            # File organization
│   └── COMPLETE_SETUP.md               # This file
│
└── 📊 Results (auto-created)
    ├── reports/                        # JSON reports
    └── images/                         # Downloaded images
```

## ⚡ Quick Setup (3 Steps)

### Step 1: Install

```bash
# Download all files to famousify-load-tester-v2/
cd famousify-load-tester-v2

# Run auto installer
python setup.py
```

**What it does:**
- ✅ Checks Python version
- ✅ Installs dependencies
- ✅ Creates config (.env)
- ✅ Sets up directories
- ✅ Tests installation

### Step 2: Validate

```bash
# Run health check
python health_checker.py
```

**What it checks:**
- 🌐 Base URL connectivity
- 🖼️ Test image accessibility
- 🔌 USER endpoint
- 🔌 TEEINBLUE endpoint
- ⚙️ Configuration validity
- 🎨 Styles availability

### Step 3: Test

```bash
# GUI mode (recommended for first time)
python famousify_load_tester_v2.py

# OR CLI mode
python famousify_load_tester_v2.py --cli

# OR use predefined scenarios
python test_scenarios.py user_smoke
```

## 🎯 Pipeline Types Explained

### USER Pipeline (Standard)

**What it does:**
```
Upload → Preprocessing (768x1024) → AI Generation → Done
```

**Characteristics:**
- Format: 3:4 portrait
- Time: 45-60 seconds avg
- Cost: €0.08 per generation
- Use case: Standard AI art generation

**Best for:**
- Quick tests
- High volume generation
- Standard AI art needs

### TEEINBLUE Pipeline (E-commerce)

**What it does:**
```
Upload → Preprocessing (1024x1024) → AI Generation → 
Background Removal → Upscaling → Done
```

**Characteristics:**
- Format: 1:1 square
- Time: 90-180 seconds avg
- Cost: €0.08 + processing
- Use case: E-commerce ready images

**Best for:**
- Shopify/Teeinblue integration
- Product mockups
- Print-on-demand
- Clean backgrounds needed

## 📊 Test Scenarios Reference

### Quick Tests (2-5 min)

| Scenario | Pipeline | Requests | Time | Cost |
|----------|----------|----------|------|------|
| `user_smoke` | USER | 3 sequential | ~3 min | €0.24 |
| `teeinblue_smoke` | TEEINBLUE | 3 sequential | ~5 min | €0.24 |

**Usage:**
```bash
python test_scenarios.py user_smoke
```

### Normal Load Tests (15-45 min)

| Scenario | Pipeline | Requests | Concurrent | Time | Cost |
|----------|----------|----------|------------|------|------|
| `user_normal` | USER | 50 | 10 | ~15 min | €4.00 |
| `teeinblue_normal` | TEEINBLUE | 25 | 5 | ~30 min | €2.00 |

**Usage:**
```bash
python test_scenarios.py user_normal
```

### Stress Tests (1-3 hours)

| Scenario | Pipeline | Requests | Concurrent | Time | Cost |
|----------|----------|----------|------------|------|------|
| `user_stress` | USER | 200 | 20 | ~45 min | €16.00 |
| `teeinblue_stress` | TEEINBLUE | 100 | 10 | ~2 hours | €8.00 |

**Usage:**
```bash
python test_scenarios.py user_stress
```

### Comparison Tests

| Scenario | What it does | Time | Cost |
|----------|--------------|------|------|
| `quick_compare` | Tests both pipelines with 10 req each | ~15 min | €1.60 |

**Usage:**
```bash
python test_scenarios.py quick_compare
```

## 🔧 Configuration Guide

### Environment Variables (.env)

```bash
# Core settings
FAMOUSIFY_BASE_URL=https://web-production-abb48.up.railway.app
FAMOUSIFY_ADMIN_TOKEN=famousify-admin-2025
FAMOUSIFY_TEST_IMAGE_URL=https://images.unsplash.com/photo-...

# Timeouts (increase if tests timeout)
FAMOUSIFY_TIMEOUT_USER=180         # 3 minutes
FAMOUSIFY_TIMEOUT_TEEINBLUE=300    # 5 minutes

# Polling (how often to check status)
FAMOUSIFY_POLL_INTERVAL=5          # 5 seconds

# Retry logic
FAMOUSIFY_MAX_RETRIES=3            # Retry 3 times on failure
FAMOUSIFY_RETRY_DELAY=10           # 10 seconds between retries
```

### GUI Configuration

1. Open GUI: `python famousify_load_tester_v2.py`
2. Go to "Configuration" tab
3. Edit values
4. Click "Save Config"

**Saved to:** `.env` file

## 🧪 Usage Examples

### Example 1: Quick Validation

```bash
# Check system health
python health_checker.py

# Run smoke test
python test_scenarios.py user_smoke

# View results
python utils.py analyze
```

### Example 2: Normal Testing

```bash
# GUI mode with progress tracking
python famousify_load_tester_v2.py

# Select USER pipeline
# Set 50 requests, 10 concurrent
# Click Start

# Results appear in results/reports/
```

### Example 3: Automated CI/CD

```bash
# Add to GitHub Actions / cron
python automation_examples.py smoke

# Exit code 0 = passed
# Exit code 1 = failed
```

### Example 4: Compare Pipelines

```bash
# Run comparison scenario
python test_scenarios.py quick_compare

# Generates 2 reports:
# - load_test_user_TIMESTAMP.json
# - load_test_teeinblue_TIMESTAMP.json

# Analyze results
python utils.py analyze
```

### Example 5: Download Images

```bash
# After running tests, download generated images
python utils.py download 3

# Downloads images from last 3 test reports
# Saved to: results/images/
```

## 📊 Understanding Reports

### JSON Report Structure

```json
{
  "test_info": {
    "timestamp": "2025-10-16T10:30:00",
    "pipeline": "user",
    "total_requests": 50,
    "concurrent": 10,
    "total_time": 320.5
  },
  "summary": {
    "successful": 47,
    "failed": 3,
    "success_rate": 94.0,
    "total_retries": 5
  },
  "timing": {
    "avg_time": 45.2,
    "min_time": 32.1,
    "max_time": 78.5,
    "median_time": 44.0,
    "p95_time": 65.3
  },
  "health": "EXCELLENT",
  "results": [...]
}
```

### Health Status Interpretation

#### USER Pipeline
- **EXCELLENT**: ≥95% success, <45s avg
- **GOOD**: ≥90% success, <60s avg
- **FAIR**: ≥80% success
- **POOR**: <80% success

#### TEEINBLUE Pipeline
- **EXCELLENT**: ≥95% success, <120s avg
- **GOOD**: ≥90% success, <180s avg
- **FAIR**: ≥80% success
- **POOR**: <80% success

## 🚨 Troubleshooting

### Problem: Connection timeout

```bash
# Check URL
curl https://web-production-abb48.up.railway.app/health

# Verify in .env
cat .env | grep BASE_URL
```

**Solution:** Verify Railway service is running

### Problem: Image download fails

```bash
# Test image URL
curl -I https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800
```

**Solution:** Use a different public image URL

### Problem: HTTP 401 Unauthorized

```bash
# Check admin token
cat .env | grep ADMIN_TOKEN
```

**Solution:** Verify token matches backend configuration

### Problem: Tests timeout

**For USER:**
```bash
# Increase timeout in .env
FAMOUSIFY_TIMEOUT_USER=300  # 5 minutes
```

**For TEEINBLUE:**
```bash
# Increase timeout in .env
FAMOUSIFY_TIMEOUT_TEEINBLUE=600  # 10 minutes
```

### Problem: All tests fail

```bash
# Run health check first
python health_checker.py

# Run single test to debug
python test_scenarios.py user_smoke
```

### Problem: GUI not loading

```bash
# Use CLI mode instead
python famousify_load_tester_v2.py --cli

# Or install tkinter
# Ubuntu: sudo apt-get install python3-tk
# Mac: brew install python-tk
```

## 📦 Build Standalone EXE

### Windows

```bash
# Install PyInstaller
pip install pyinstaller

# Build
python build_exe.py

# Output: dist/FamousifyLoadTester.exe
```

### macOS / Linux

```bash
# Install PyInstaller
pip install pyinstaller

# Build
python build_exe.py

# Output: dist/FamousifyLoadTester
```

### Distribution Package

After building:

```
dist/FamousifyLoadTester_Package/
├── FamousifyLoadTester.exe    # Executable
├── .env.example                # Config template
├── README.txt                  # Quick guide
└── results/                    # Auto-created
```

**Distribute this folder** to other machines.

## 🔄 Update Workflow

### Check for Issues

```bash
# 1. Health check
python health_checker.py

# 2. Quick test
python test_scenarios.py user_smoke

# 3. View recent results
python utils.py analyze
```

### After Backend Updates

```bash
# Re-validate endpoints
python health_checker.py

# Run comparison to detect regressions
python test_scenarios.py quick_compare
```

### Before Production Deployment

```bash
# Full validation suite
python health_checker.py
python test_scenarios.py user_normal
python test_scenarios.py teeinblue_normal
python utils.py analyze
```

## 💡 Pro Tips

1. **Start Small**: Always run `user_smoke` before bigger tests
2. **Monitor Costs**: Each request = €0.08, plan accordingly
3. **Use Scenarios**: Predefined scenarios save time
4. **Check Health First**: Run `health_checker.py` before expensive tests
5. **Save Reports**: Reports in `results/reports/` for historical comparison
6. **Download Images**: Use `utils.py download` to inspect generated images
7. **Compare Pipelines**: Use `quick_compare` to validate both work
8. **Increase Timeouts**: If tests timeout, increase in .env
9. **Watch Retries**: High retry count indicates instability
10. **Read Logs**: GUI log shows real-time progress and errors

## 🎓 Next Steps

After setup is complete:

1. ✅ Run health check
2. ✅ Test USER pipeline (smoke test)
3. ✅ Test TEEINBLUE pipeline (smoke test)
4. ✅ Run normal load test
5. ✅ Analyze results
6. ✅ Set up monitoring/CI if needed

## 📞 Support

- **Health issues**: Run `python health_checker.py`
- **Config issues**: Check `.env` file
- **Test failures**: Check `results/reports/*.json`
- **Backend issues**: Check Railway logs

---

**Ready to test!** 🚀

Start with: `python health_checker.py`

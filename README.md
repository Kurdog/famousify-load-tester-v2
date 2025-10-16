# 🚀 Famousify Load Tester V2

Modern, professional load testing suite for Famousify AI generation pipeline with GUI and CLI modes.

## ✨ Features

- **🖥️ GUI Mode** - Full-featured graphical interface (Tkinter)
- **⌨️ CLI Mode** - Command-line interface for automation
- **🔄 Multi-Pipeline** - Test both USER and TEEINBLUE pipelines
- **📦 Portable** - Can be packaged as standalone EXE
- **⚡ Async Engine** - High-performance concurrent testing
- **🔁 Retry Logic** - Automatic retry on failures
- **📊 Rich Reports** - JSON reports with detailed metrics
- **🔧 Configurable** - Environment variables or GUI config
- **🎯 Real-time Monitoring** - Live progress tracking
- **💾 Results Archive** - Automatic report saving
- **⏱️ Adaptive Timeouts** - Different timeouts per pipeline
- **🏥 Health Checks** - Comprehensive system validation

## 🎯 Quick Start

### Installation

```bash
# Clone or download
cd famousify-load-tester-v2

# Install dependencies
pip install -r requirements.txt

# Run GUI mode
python famousify_load_tester_v2.py

# Or CLI mode
python famousify_load_tester_v2.py --cli
```

### First Run

1. **Calculate Costs** - Use cost calculator to estimate expenses
   ```bash
   python cost_calculator.py
   ```

2. **Configure** - Set your Famousify URL and credentials in the Configuration tab

3. **Select Pipeline** - Choose USER (standard) or TEEINBLUE (with bg removal + upscale)

4. **Check Estimate** - GUI shows real-time cost estimate as you adjust parameters

5. **Run Test** - Set parameters and start testing

6. **View Results** - Check the Results tab for historical data with cost breakdown

## 🔄 Pipeline Types

### USER Pipeline (Standard)
- **Format**: 3:4 portrait (768x1024)
- **Process**: Upload → Preprocessing → AI Generation
- **Time**: 45-60 seconds average
- **Use case**: Standard image generation
- **Cost**: €0.08 per generation

### TEEINBLUE Pipeline (E-commerce)
- **Format**: 1:1 square (1024x1024)
- **Process**: Upload → Preprocessing → AI Generation → BG Removal → Upscaling
- **Time**: 90-180 seconds average
- **Use case**: E-commerce products (Shopify/Teeinblue)
- **Cost**: €0.08 + processing overhead

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set system variables:

```bash
FAMOUSIFY_BASE_URL=https://web-production-abb48.up.railway.app
FAMOUSIFY_ADMIN_TOKEN=famousify-admin-2025
FAMOUSIFY_TEST_IMAGE_URL=https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800
FAMOUSIFY_TIMEOUT=180
FAMOUSIFY_POLL_INTERVAL=5
```

### GUI Configuration

All settings can be configured directly in the GUI:
- **Configuration tab** - Set URLs, tokens, timeouts
- **Save Config** - Persists to `.env` file
- **Load Config** - Reloads from `.env` file

## 📖 Usage

### GUI Mode (Default)

```bash
python famousify_load_tester_v2.py
```

**Interface:**
- **Configuration Tab**: Set up connection parameters
- **Run Test Tab**: Execute load tests with live progress
- **Results Tab**: View and analyze historical test results

**Test Parameters:**
- **Total Requests**: Number of generation requests (1-200)
- **Concurrent**: How many requests to run simultaneously (1-50)

### CLI Mode

```bash
python famousify_load_tester_v2.py --cli
```

**Interactive prompts:**
```
Total requests [10]: 25
Concurrent requests [10]: 10
Start test? (yes/no): yes
```

### Automated/Scripted Testing

```python
import asyncio
from famousify_load_tester_v2 import Config, LoadTester

config = Config()
config.base_url = "https://your-instance.railway.app"
config.admin_token = "your-token"

tester = LoadTester(config)
report = asyncio.run(tester.run_test(num_requests=50, concurrent=10))

print(f"Success Rate: {report['summary']['success_rate']}%")
print(f"Health: {report['health']}")
```

## 📊 Reports

### Report Structure

```json
{
  "test_info": {
    "timestamp": "2025-01-20T10:30:00",
    "base_url": "https://...",
    "total_requests": 50,
    "concurrent": 10,
    "total_time": 320.5
  },
  "summary": {
    "successful": 47,
    "failed": 3,
    "success_rate": 94.0
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

### Health Status

- **EXCELLENT**: ≥95% success, <45s avg time
- **GOOD**: ≥90% success, <60s avg time
- **FAIR**: ≥80% success
- **POOR**: <80% success

### Report Files

Reports are saved in `results/reports/` with timestamp:
```
results/
├── reports/
│   ├── load_test_20250120_103000.json
│   ├── load_test_20250120_143522.json
│   └── ...
└── images/
    └── (downloaded generation images)
```

## 📦 Build Standalone EXE

### Using PyInstaller

```bash
# Install PyInstaller
pip install pyinstaller

# Build EXE (Windows)
pyinstaller --onefile --windowed --name "FamousifyLoadTester" famousify_load_tester_v2.py

# Build EXE (macOS/Linux - CLI mode)
pyinstaller --onefile --name "FamousifyLoadTester" famousify_load_tester_v2.py

# Output: dist/FamousifyLoadTester.exe
```

### Distribution Package

For distributing to other machines:

```
FamousifyLoadTester/
├── FamousifyLoadTester.exe    # Standalone executable
├── .env.example                # Template configuration
├── README.txt                  # Quick guide
└── results/                    # Will be created automatically
```

## 🧪 Test Scenarios

### Quick Smoke Test (3 requests)

```bash
Total requests: 3
Concurrent: 1
```
**Purpose**: Verify basic functionality, ~€0.24 cost

### Normal Load (50 requests, 10 concurrent)

```bash
Total requests: 50
Concurrent: 10
```
**Purpose**: Simulate typical production load, ~€4 cost

### Stress Test (200 requests, 20 concurrent)

```bash
Total requests: 200
Concurrent: 20
```
**Purpose**: Find capacity limits, ~€16 cost

## 🔍 Troubleshooting

### Connection Issues

```
❌ Error: Image download failed
```
**Solution**: Check `TEST_IMAGE_URL` is publicly accessible

```
❌ HTTP 401: Unauthorized
```
**Solution**: Verify `ADMIN_TOKEN` is correct

### Timeout Issues

```
❌ Polling timeout
```
**Solution**: Increase `FAMOUSIFY_TIMEOUT` (default 180s)

### GUI Not Loading

```
⚠️ GUI not available, running in CLI mode
```
**Solution**: Install tkinter or use CLI mode with `--cli` flag

## 🛠️ Advanced Usage

### Custom Test Scenarios

```python
# Create custom test scenario
config = Config()
tester = LoadTester(config)

# Progressive load test
for concurrent in [5, 10, 20, 50]:
    print(f"Testing {concurrent} concurrent...")
    report = await tester.run_test(
        num_requests=concurrent * 5,
        concurrent=concurrent
    )
    
    if report['summary']['success_rate'] < 80:
        print(f"Degraded at {concurrent} concurrent")
        break
```

### Integration with CI/CD

```yaml
# .github/workflows/load-test.yml
name: Weekly Load Test

on:
  schedule:
    - cron: '0 2 * * 1'  # Every Monday 2am

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Load Test
        run: |
          pip install -r requirements.txt
          python famousify_load_tester_v2.py --cli << EOF
          50
          10
          yes
          EOF
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: results/reports/
```

## 📈 Performance Targets

Based on Famousify pipeline analysis:

| Metric | Target | Notes |
|--------|--------|-------|
| Success Rate | ≥90% | Stable production |
| Avg Generation Time | <60s | User satisfaction |
| P95 Time | <90s | Worst-case acceptable |
| Concurrent Capacity | 10-20 | Safe operating range |
| Daily Capacity | 100-200 gen | With current infra |

## 🤝 Contributing

This tool is designed to be extended. Key extension points:

- **Custom Styles**: Modify `config.styles` list
- **Additional Metrics**: Extend `TestResult` class
- **Report Formats**: Add HTML/PDF generators
- **Webhooks**: Add Slack/Discord notifications

## 📝 License

Internal tool for Famousify testing.

## 🆘 Support

For issues or questions:
1. Check troubleshooting section
2. Review test logs in `results/reports/`
3. Contact development team

---

**Version**: 2.0.0  
**Last Updated**: January 2025  
**Requires**: Python 3.8+

#!/usr/bin/env python3
"""
Utility functions for Famousify Load Tester V2
- Result analysis
- Image downloading
- Report comparison
- HTML report generation
"""

import json
import requests
from pathlib import Path
from datetime import datetime
import statistics
from typing import List, Dict, Optional

# ==================== RESULT ANALYSIS ====================

def analyze_reports(reports_dir: str = "results/reports") -> Dict:
    """Analyze all test reports and generate summary"""
    
    reports_path = Path(reports_dir)
    report_files = sorted(reports_path.glob("*.json"))
    
    if not report_files:
        return {"error": "No reports found"}
    
    all_reports = []
    for filepath in report_files:
        with open(filepath, 'r') as f:
            data = json.load(f)
            data['_filepath'] = str(filepath)
            all_reports.append(data)
    
    # Calculate aggregate statistics
    total_tests = len(all_reports)
    total_requests = sum(r['test_info']['total_requests'] for r in all_reports)
    
    success_rates = [r['summary']['success_rate'] for r in all_reports]
    avg_times = [r['timing'].get('avg_time', 0) for r in all_reports if r['timing']]
    
    health_counts = {}
    for r in all_reports:
        health = r.get('health', 'UNKNOWN')
        health_counts[health] = health_counts.get(health, 0) + 1
    
    # Find best and worst
    best_test = max(all_reports, key=lambda x: x['summary']['success_rate'])
    worst_test = min(all_reports, key=lambda x: x['summary']['success_rate'])
    
    return {
        "summary": {
            "total_tests": total_tests,
            "total_requests": total_requests,
            "date_range": {
                "first": all_reports[0]['test_info']['timestamp'],
                "last": all_reports[-1]['test_info']['timestamp']
            }
        },
        "aggregates": {
            "avg_success_rate": round(statistics.mean(success_rates), 2),
            "avg_time": round(statistics.mean(avg_times), 2) if avg_times else 0,
            "min_success_rate": round(min(success_rates), 2),
            "max_success_rate": round(max(success_rates), 2)
        },
        "health_distribution": health_counts,
        "best_test": {
            "date": best_test['test_info']['timestamp'],
            "success_rate": best_test['summary']['success_rate'],
            "file": Path(best_test['_filepath']).name
        },
        "worst_test": {
            "date": worst_test['test_info']['timestamp'],
            "success_rate": worst_test['summary']['success_rate'],
            "file": Path(worst_test['_filepath']).name
        },
        "recent_tests": [
            {
                "date": r['test_info']['timestamp'][:19],
                "requests": r['test_info']['total_requests'],
                "success_rate": r['summary']['success_rate'],
                "health": r.get('health', 'N/A')
            }
            for r in all_reports[-10:]  # Last 10
        ]
    }

def compare_reports(report1_path: str, report2_path: str) -> Dict:
    """Compare two test reports"""
    
    with open(report1_path, 'r') as f:
        r1 = json.load(f)
    
    with open(report2_path, 'r') as f:
        r2 = json.load(f)
    
    comparison = {
        "test1": {
            "date": r1['test_info']['timestamp'],
            "success_rate": r1['summary']['success_rate'],
            "avg_time": r1['timing'].get('avg_time', 0),
            "health": r1.get('health', 'N/A')
        },
        "test2": {
            "date": r2['test_info']['timestamp'],
            "success_rate": r2['summary']['success_rate'],
            "avg_time": r2['timing'].get('avg_time', 0),
            "health": r2.get('health', 'N/A')
        },
        "deltas": {
            "success_rate": r2['summary']['success_rate'] - r1['summary']['success_rate'],
            "avg_time": r2['timing'].get('avg_time', 0) - r1['timing'].get('avg_time', 0)
        }
    }
    
    # Determine if improvement
    if comparison['deltas']['success_rate'] > 0 and comparison['deltas']['avg_time'] < 0:
        comparison['verdict'] = "IMPROVED"
    elif comparison['deltas']['success_rate'] < 0 or comparison['deltas']['avg_time'] > 10:
        comparison['verdict'] = "DEGRADED"
    else:
        comparison['verdict'] = "SIMILAR"
    
    return comparison

# ==================== IMAGE DOWNLOADING ====================

def download_images_from_report(report_path: str, output_dir: Optional[str] = None) -> int:
    """Download all generated images from a test report"""
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    if output_dir is None:
        # Create folder based on report name
        report_name = Path(report_path).stem
        output_dir = f"results/images/{report_name}"
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    downloaded = 0
    results = report.get('results', [])
    
    for result in results:
        if not result.get('success'):
            continue
        
        image_url = result.get('image_url')
        if not image_url:
            continue
        
        job_id = result.get('job_id', f"unknown_{result['test_id']}")
        filename = f"{job_id}.png"
        filepath = Path(output_dir) / filename
        
        try:
            print(f"Downloading {job_id}...")
            response = requests.get(image_url, timeout=30)
            
            if response.status_code == 200:
                filepath.write_bytes(response.content)
                downloaded += 1
                print(f"  ✅ Saved: {filepath}")
            else:
                print(f"  ❌ HTTP {response.status_code}")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print(f"\n✅ Downloaded {downloaded}/{len(results)} images to {output_dir}")
    return downloaded

def download_latest_images(count: int = 1) -> int:
    """Download images from the N most recent reports"""
    
    reports_dir = Path("results/reports")
    report_files = sorted(reports_dir.glob("*.json"), reverse=True)[:count]
    
    if not report_files:
        print("❌ No reports found")
        return 0
    
    total_downloaded = 0
    
    for report_file in report_files:
        print(f"\n📂 Processing: {report_file.name}")
        downloaded = download_images_from_report(str(report_file))
        total_downloaded += downloaded
    
    return total_downloaded

# ==================== HTML REPORT GENERATION ====================

def generate_html_report(report_path: str, output_path: Optional[str] = None) -> str:
    """Generate HTML report from JSON"""
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    if output_path is None:
        output_path = report_path.replace('.json', '.html')
    
    # Build HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Load Test Report - {report['test_info']['timestamp'][:19]}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }}
        .metric-card.success {{ border-left-color: #28a745; }}
        .metric-card.warning {{ border-left-color: #ffc107; }}
        .metric-card.danger {{ border-left-color: #dc3545; }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .health-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }}
        .health-EXCELLENT {{ background: #d4edda; color: #155724; }}
        .health-GOOD {{ background: #cce5ff; color: #004085; }}
        .health-FAIR {{ background: #fff3cd; color: #856404; }}
        .health-POOR {{ background: #f8d7da; color: #721c24; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .success-row {{ color: #28a745; }}
        .fail-row {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Load Test Report</h1>
        <div class="subtitle">
            {report['test_info']['timestamp'][:19]} • 
            {report['test_info']['base_url']}
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Total Requests</div>
                <div class="metric-value">{report['test_info']['total_requests']}</div>
            </div>
            
            <div class="metric-card success">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value">{report['summary']['success_rate']}%</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Average Time</div>
                <div class="metric-value">{report['timing'].get('avg_time', 0):.1f}s</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-label">Total Duration</div>
                <div class="metric-value">{report['test_info']['total_time']:.1f}s</div>
            </div>
        </div>
        
        <h2>Health Status</h2>
        <p>
            <span class="health-badge health-{report.get('health', 'UNKNOWN')}">
                {report.get('health', 'UNKNOWN')}
            </span>
        </p>
        
        <h2>Timing Breakdown</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Average Time</td>
                <td>{report['timing'].get('avg_time', 0):.2f}s</td>
            </tr>
            <tr>
                <td>Minimum Time</td>
                <td>{report['timing'].get('min_time', 0):.2f}s</td>
            </tr>
            <tr>
                <td>Maximum Time</td>
                <td>{report['timing'].get('max_time', 0):.2f}s</td>
            </tr>
            <tr>
                <td>Median Time</td>
                <td>{report['timing'].get('median_time', 0):.2f}s</td>
            </tr>
            {f'<tr><td>P95 Time</td><td>{report["timing"]["p95_time"]:.2f}s</td></tr>' if report['timing'].get('p95_time') else ''}
        </table>
        
        <h2>Test Results</h2>
        <table>
            <tr>
                <th>Test ID</th>
                <th>Style</th>
                <th>Job ID</th>
                <th>Status</th>
                <th>Time</th>
            </tr>
"""
    
    for result in report['results']:
        status_class = "success-row" if result['success'] else "fail-row"
        status_icon = "✅" if result['success'] else "❌"
        time_str = f"{result['total_time']:.1f}s" if result['total_time'] else "N/A"
        
        html += f"""
            <tr class="{status_class}">
                <td>{result['test_id']}</td>
                <td>{result['style']}</td>
                <td>{result['job_id'] or 'N/A'}</td>
                <td>{status_icon}</td>
                <td>{time_str}</td>
            </tr>
"""
    
    html += """
        </table>
    </div>
</body>
</html>
"""
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"✅ HTML report generated: {output_path}")
    return output_path

# ==================== CLI UTILITIES ====================

def print_analysis():
    """Print analysis of all reports"""
    print("\n" + "="*70)
    print("📊 ANALYZING ALL TEST REPORTS")
    print("="*70 + "\n")
    
    analysis = analyze_reports()
    
    if 'error' in analysis:
        print(f"❌ {analysis['error']}")
        return
    
    summary = analysis['summary']
    agg = analysis['aggregates']
    
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Total Requests: {summary['total_requests']}")
    print(f"Date Range: {summary['date_range']['first'][:10]} to {summary['date_range']['last'][:10]}")
    print()
    
    print("Aggregate Statistics:")
    print(f"  Average Success Rate: {agg['avg_success_rate']}%")
    print(f"  Average Time: {agg['avg_time']}s")
    print(f"  Success Rate Range: {agg['min_success_rate']}% - {agg['max_success_rate']}%")
    print()
    
    print("Health Distribution:")
    for health, count in analysis['health_distribution'].items():
        print(f"  {health}: {count}")
    print()
    
    print("Best Test:")
    print(f"  Date: {analysis['best_test']['date'][:19]}")
    print(f"  Success: {analysis['best_test']['success_rate']}%")
    print(f"  File: {analysis['best_test']['file']}")
    print()
    
    print("Recent Tests (last 10):")
    for test in analysis['recent_tests'][-5:]:  # Show last 5
        print(f"  {test['date']} - {test['requests']} req - {test['success_rate']}% - {test['health']}")
    
    print("\n" + "="*70 + "\n")

# ==================== MAIN CLI ====================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python utils.py analyze              # Analyze all reports")
        print("  python utils.py download [N]         # Download images from N latest reports")
        print("  python utils.py html <report.json>   # Generate HTML report")
        print("  python utils.py compare <r1> <r2>    # Compare two reports")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze":
        print_analysis()
    
    elif command == "download":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        download_latest_images(count)
    
    elif command == "html":
        if len(sys.argv) < 3:
            print("❌ Usage: python utils.py html <report.json>")
            sys.exit(1)
        generate_html_report(sys.argv[2])
    
    elif command == "compare":
        if len(sys.argv) < 4:
            print("❌ Usage: python utils.py compare <report1> <report2>")
            sys.exit(1)
        
        comparison = compare_reports(sys.argv[2], sys.argv[3])
        print(json.dumps(comparison, indent=2))
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

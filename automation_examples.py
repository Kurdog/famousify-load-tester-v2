#!/usr/bin/env python3
"""
Automation Examples for Famousify Load Tester V2

Examples of how to integrate load testing into:
- CI/CD pipelines
- Scheduled monitoring
- Pre-deployment validation
- Performance regression detection
"""

import asyncio
import sys
import json
from pathlib import Path
from famousify_load_tester_v2 import Config, LoadTester

# ==================== EXAMPLE 1: SIMPLE SMOKE TEST ====================

async def smoke_test():
    """
    Quick smoke test for CI/CD
    Runs 3 requests to verify system is working
    """
    print("🔥 Running smoke test...")
    
    config = Config()
    tester = LoadTester(config)
    
    # Run minimal test
    report = await tester.run_test(num_requests=3, concurrent=1)
    
    # Check if passed
    success_rate = report['summary']['success_rate']
    
    if success_rate >= 90:
        print(f"✅ Smoke test PASSED - {success_rate}% success")
        return 0
    else:
        print(f"❌ Smoke test FAILED - {success_rate}% success")
        return 1

# ==================== EXAMPLE 2: PROGRESSIVE LOAD TEST ====================

async def progressive_load_test():
    """
    Progressive load test to find capacity limits
    Increases load until degradation detected
    """
    print("📈 Running progressive load test...")
    
    config = Config()
    tester = LoadTester(config)
    
    load_levels = [5, 10, 20, 30, 50]
    results = []
    
    for concurrent in load_levels:
        print(f"\n🔄 Testing {concurrent} concurrent requests...")
        
        report = await tester.run_test(
            num_requests=concurrent * 2,  # 2x concurrent
            concurrent=concurrent
        )
        
        success_rate = report['summary']['success_rate']
        avg_time = report['timing'].get('avg_time', 999)
        
        results.append({
            'concurrent': concurrent,
            'success_rate': success_rate,
            'avg_time': avg_time
        })
        
        # Stop if degraded
        if success_rate < 80 or avg_time > 90:
            print(f"⚠️  System degraded at {concurrent} concurrent")
            break
        
        # Pause between tests
        print("⏸️  Pausing 30s before next level...")
        await asyncio.sleep(30)
    
    # Summary
    print("\n" + "="*70)
    print("PROGRESSIVE TEST RESULTS")
    print("="*70)
    for r in results:
        print(f"Concurrent: {r['concurrent']:3d} | Success: {r['success_rate']:5.1f}% | Avg: {r['avg_time']:5.1f}s")
    
    # Find max safe capacity
    good_results = [r for r in results if r['success_rate'] >= 90 and r['avg_time'] < 60]
    if good_results:
        max_capacity = max(r['concurrent'] for r in good_results)
        print(f"\n✅ Max safe capacity: {max_capacity} concurrent")
    else:
        print("\n❌ No safe capacity level found")
    
    return 0

# ==================== EXAMPLE 3: REGRESSION DETECTION ====================

async def regression_test(baseline_path: str):
    """
    Compare current performance against baseline
    Fails if regression detected
    """
    print("🔍 Running regression test...")
    
    # Load baseline
    with open(baseline_path, 'r') as f:
        baseline = json.load(f)
    
    baseline_success = baseline['summary']['success_rate']
    baseline_time = baseline['timing'].get('avg_time', 0)
    
    print(f"📊 Baseline: {baseline_success}% success, {baseline_time:.1f}s avg")
    
    # Run new test with same parameters
    config = Config()
    tester = LoadTester(config)
    
    num_requests = baseline['test_info']['total_requests']
    concurrent = baseline['test_info']['concurrent']
    
    print(f"🧪 Running test: {num_requests} requests, {concurrent} concurrent...")
    
    report = await tester.run_test(num_requests, concurrent)
    
    current_success = report['summary']['success_rate']
    current_time = report['timing'].get('avg_time', 0)
    
    print(f"📊 Current: {current_success}% success, {current_time:.1f}s avg")
    
    # Calculate deltas
    success_delta = current_success - baseline_success
    time_delta = current_time - baseline_time
    
    print(f"\n📈 Delta: {success_delta:+.1f}% success, {time_delta:+.1f}s time")
    
    # Determine if regression
    regression = False
    
    if success_delta < -5:  # 5% drop in success
        print("❌ REGRESSION: Success rate dropped significantly")
        regression = True
    
    if time_delta > 15:  # 15s increase in avg time
        print("❌ REGRESSION: Average time increased significantly")
        regression = True
    
    if not regression:
        print("✅ No regression detected")
        return 0
    else:
        return 1

# ==================== EXAMPLE 4: SCHEDULED MONITORING ====================

async def scheduled_monitoring():
    """
    Run regular monitoring test
    Suitable for cron jobs or scheduled tasks
    """
    print("⏰ Running scheduled monitoring...")
    
    config = Config()
    tester = LoadTester(config)
    
    # Standard monitoring test
    report = await tester.run_test(num_requests=10, concurrent=5)
    
    success_rate = report['summary']['success_rate']
    health = report['health']
    
    # Alert if unhealthy
    if health in ['POOR', 'FAIR']:
        print(f"⚠️  ALERT: System health is {health}")
        
        # Here you could send alerts via:
        # - Email
        # - Slack webhook
        # - PagerDuty
        # - etc.
        
        send_alert(report)
    else:
        print(f"✅ System healthy: {health}")
    
    return 0

def send_alert(report: dict):
    """Send alert notification (example)"""
    # Example: Send to Slack
    # webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    # if webhook_url:
    #     requests.post(webhook_url, json={
    #         "text": f"⚠️ Famousify Load Test Alert\n"
    #                 f"Health: {report['health']}\n"
    #                 f"Success: {report['summary']['success_rate']}%"
    #     })
    
    print("📧 Alert sent (stub)")

# ==================== EXAMPLE 5: PRE-DEPLOYMENT VALIDATION ====================

async def pre_deployment_validation():
    """
    Validate system before deployment
    Comprehensive test suite
    """
    print("🚀 Running pre-deployment validation...")
    
    config = Config()
    tester = LoadTester(config)
    
    tests = [
        ("Quick Check", 5, 5),
        ("Normal Load", 20, 10),
        ("Burst Test", 30, 15),
    ]
    
    all_passed = True
    
    for test_name, num_req, concurrent in tests:
        print(f"\n🧪 Test: {test_name} ({num_req} req, {concurrent} concurrent)")
        
        report = await tester.run_test(num_req, concurrent)
        
        success = report['summary']['success_rate']
        health = report['health']
        
        if success >= 90 and health in ['EXCELLENT', 'GOOD']:
            print(f"  ✅ {test_name} PASSED")
        else:
            print(f"  ❌ {test_name} FAILED")
            all_passed = False
        
        # Pause between tests
        if test_name != tests[-1][0]:
            await asyncio.sleep(30)
    
    if all_passed:
        print("\n✅ All validation tests PASSED - Ready for deployment")
        return 0
    else:
        print("\n❌ Some tests FAILED - DO NOT DEPLOY")
        return 1

# ==================== EXAMPLE 6: BATCH TESTING ====================

async def batch_style_testing():
    """
    Test all available styles individually
    Find problematic styles
    """
    print("🎨 Running batch style testing...")
    
    config = Config()
    styles = config.styles
    
    style_results = {}
    
    for style in styles:
        print(f"\n🧪 Testing style: {style}")
        
        tester = LoadTester(config)
        report = await tester.run_test(
            num_requests=5,
            concurrent=1,
            styles=[style]  # Test single style
        )
        
        style_results[style] = {
            'success_rate': report['summary']['success_rate'],
            'avg_time': report['timing'].get('avg_time', 0),
            'health': report['health']
        }
        
        await asyncio.sleep(10)  # Pause between styles
    
    # Summary
    print("\n" + "="*70)
    print("STYLE TEST RESULTS")
    print("="*70)
    
    for style, results in style_results.items():
        print(f"{style:20s} | {results['success_rate']:5.1f}% | {results['avg_time']:5.1f}s | {results['health']}")
    
    # Find problematic styles
    problematic = [s for s, r in style_results.items() if r['success_rate'] < 90]
    if problematic:
        print(f"\n⚠️  Problematic styles: {', '.join(problematic)}")
    else:
        print("\n✅ All styles working well")
    
    return 0

# ==================== MAIN CLI ====================

def main():
    """Main entry point for automation examples"""
    
    if len(sys.argv) < 2:
        print("Automation Examples:")
        print("  smoke            - Quick smoke test (3 requests)")
        print("  progressive      - Progressive load test")
        print("  regression <baseline.json>  - Regression test")
        print("  monitor          - Scheduled monitoring")
        print("  validate         - Pre-deployment validation")
        print("  batch-styles     - Test all styles individually")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "smoke":
        exit_code = asyncio.run(smoke_test())
    
    elif command == "progressive":
        exit_code = asyncio.run(progressive_load_test())
    
    elif command == "regression":
        if len(sys.argv) < 3:
            print("❌ Usage: automation_examples.py regression <baseline.json>")
            sys.exit(1)
        exit_code = asyncio.run(regression_test(sys.argv[2]))
    
    elif command == "monitor":
        exit_code = asyncio.run(scheduled_monitoring())
    
    elif command == "validate":
        exit_code = asyncio.run(pre_deployment_validation())
    
    elif command == "batch-styles":
        exit_code = asyncio.run(batch_style_testing())
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

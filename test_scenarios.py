#!/usr/bin/env python3
"""
Predefined Test Scenarios for Famousify Load Tester V2
Quick access to common testing patterns for both pipelines
"""

import asyncio
import sys
from famousify_load_tester_v2 import Config, LoadTester

# ==================== SCENARIOS ====================

SCENARIOS = {
    # USER Pipeline Scenarios
    "user_smoke": {
        "name": "USER Smoke Test",
        "pipeline": "user",
        "requests": 3,
        "concurrent": 1,
        "description": "Quick validation (3 sequential requests)",
        "time_estimate": "2-3 minutes",
        "cost_estimate": "€0.24"
    },
    "user_normal": {
        "name": "USER Normal Load",
        "pipeline": "user",
        "requests": 50,
        "concurrent": 10,
        "description": "Standard production load test",
        "time_estimate": "15-20 minutes",
        "cost_estimate": "€4.00"
    },
    "user_stress": {
        "name": "USER Stress Test",
        "pipeline": "user",
        "requests": 200,
        "concurrent": 20,
        "description": "High load stress test",
        "time_estimate": "45-60 minutes",
        "cost_estimate": "€16.00"
    },
    
    # TEEINBLUE Pipeline Scenarios
    "teeinblue_smoke": {
        "name": "TEEINBLUE Smoke Test",
        "pipeline": "teeinblue",
        "requests": 3,
        "concurrent": 1,
        "description": "Quick validation with full pipeline (bg + upscale)",
        "time_estimate": "5-10 minutes",
        "cost_estimate": "€0.24"
    },
    "teeinblue_normal": {
        "name": "TEEINBLUE Normal Load",
        "pipeline": "teeinblue",
        "requests": 25,
        "concurrent": 5,
        "description": "E-commerce load test",
        "time_estimate": "30-45 minutes",
        "cost_estimate": "€2.00"
    },
    "teeinblue_stress": {
        "name": "TEEINBLUE Stress Test",
        "pipeline": "teeinblue",
        "requests": 100,
        "concurrent": 10,
        "description": "High load with full pipeline",
        "time_estimate": "2-3 hours",
        "cost_estimate": "€8.00"
    },
    
    # Mixed/Comparison Scenarios
    "quick_compare": {
        "name": "Quick Pipeline Comparison",
        "pipeline": "both",
        "requests": 10,
        "concurrent": 5,
        "description": "Compare USER vs TEEINBLUE performance",
        "time_estimate": "10-15 minutes",
        "cost_estimate": "€1.60"
    },
}

# ==================== SCENARIO RUNNER ====================

async def run_scenario(scenario_key: str):
    """Run a predefined scenario"""
    
    if scenario_key not in SCENARIOS:
        print(f"❌ Unknown scenario: {scenario_key}")
        print(f"Available: {', '.join(SCENARIOS.keys())}")
        return 1
    
    scenario = SCENARIOS[scenario_key]
    
    config = Config()
    config.load_from_file()
    
    # Calculate actual costs based on config
    base_cost = scenario['requests'] * config.cost_per_generation
    cost_with_margin = base_cost * config.cost_margin
    
    if scenario['pipeline'] == 'both':
        base_cost *= 2
        cost_with_margin *= 2
    
    print("="*70)
    print(f"🎯 {scenario['name']}")
    print("="*70)
    print(f"Description: {scenario['description']}")
    print(f"Pipeline: {scenario['pipeline'].upper()}")
    print(f"Requests: {scenario['requests']} (concurrent: {scenario['concurrent']})")
    print(f"\n💰 Cost Estimate:")
    print(f"   Base: €{base_cost:.2f}")
    print(f"   With {int((config.cost_margin-1)*100)}% margin: €{cost_with_margin:.2f}")
    print(f"\n⏱️  Estimated Time: {scenario['time_estimate']}")
    print()
    
    confirm = input("Start this scenario? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("Aborted")
        return 0
    
    if scenario['pipeline'] == "both":
        # Run both pipelines sequentially
        print("\n" + "="*70)
        print("📊 PART 1: USER Pipeline")
        print("="*70)
        
        tester = LoadTester(config)
        user_report = await tester.run_test(
            num_requests=scenario['requests'],
            concurrent=scenario['concurrent'],
            pipeline="user"
        )
        
        print("\n⏸️  Pausing 30 seconds before TEEINBLUE test...")
        await asyncio.sleep(30)
        
        print("\n" + "="*70)
        print("📊 PART 2: TEEINBLUE Pipeline")
        print("="*70)
        
        tester = LoadTester(config)
        teeinblue_report = await tester.run_test(
            num_requests=scenario['requests'],
            concurrent=scenario['concurrent'],
            pipeline="teeinblue"
        )
        
        # Comparison
        print("\n" + "="*70)
        print("📈 COMPARISON RESULTS")
        print("="*70)
        print(f"\nUSER Pipeline:")
        print(f"  Success Rate: {user_report['summary']['success_rate']}%")
        print(f"  Avg Time: {user_report['timing'].get('avg_time', 0):.1f}s")
        print(f"  Health: {user_report['health']}")
        
        print(f"\nTEEINBLUE Pipeline:")
        print(f"  Success Rate: {teeinblue_report['summary']['success_rate']}%")
        print(f"  Avg Time: {teeinblue_report['timing'].get('avg_time', 0):.1f}s")
        print(f"  Health: {teeinblue_report['health']}")
        
        print(f"\nTime Difference: {teeinblue_report['timing'].get('avg_time', 0) - user_report['timing'].get('avg_time', 0):.1f}s (Teeinblue slower)")
        print("="*70)
        
    else:
        # Single pipeline
        tester = LoadTester(config)
        report = await tester.run_test(
            num_requests=scenario['requests'],
            concurrent=scenario['concurrent'],
            pipeline=scenario['pipeline']
        )
        
        # Print summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        print(f"Scenario: {scenario['name']}")
        print(f"Pipeline: {scenario['pipeline'].upper()}")
        print(f"Success Rate: {report['summary']['success_rate']}%")
        print(f"Average Time: {report['timing'].get('avg_time', 0):.1f}s")
        print(f"Health: {report['health']}")
        
        if report['summary']['total_retries'] > 0:
            print(f"Total Retries: {report['summary']['total_retries']}")
        
        print("="*70)
    
    return 0

# ==================== CLI ====================

def list_scenarios():
    """List all available scenarios"""
    print("\n" + "="*70)
    print("📋 AVAILABLE TEST SCENARIOS")
    print("="*70 + "\n")
    
    # Group by pipeline
    user_scenarios = {k: v for k, v in SCENARIOS.items() if v['pipeline'] == 'user'}
    teeinblue_scenarios = {k: v for k, v in SCENARIOS.items() if v['pipeline'] == 'teeinblue'}
    other_scenarios = {k: v for k, v in SCENARIOS.items() if v['pipeline'] not in ['user', 'teeinblue']}
    
    if user_scenarios:
        print("👤 USER Pipeline:")
        for key, scenario in user_scenarios.items():
            print(f"  {key:20s} - {scenario['name']}")
            print(f"  {'':20s}   {scenario['description']}")
            print(f"  {'':20s}   {scenario['requests']} req, {scenario['concurrent']} concurrent")
            print(f"  {'':20s}   ⏱️  {scenario['time_estimate']}, 💰 {scenario['cost_estimate']}")
            print()
    
    if teeinblue_scenarios:
        print("🛒 TEEINBLUE Pipeline:")
        for key, scenario in teeinblue_scenarios.items():
            print(f"  {key:20s} - {scenario['name']}")
            print(f"  {'':20s}   {scenario['description']}")
            print(f"  {'':20s}   {scenario['requests']} req, {scenario['concurrent']} concurrent")
            print(f"  {'':20s}   ⏱️  {scenario['time_estimate']}, 💰 {scenario['cost_estimate']}")
            print()
    
    if other_scenarios:
        print("🔀 Mixed/Comparison:")
        for key, scenario in other_scenarios.items():
            print(f"  {key:20s} - {scenario['name']}")
            print(f"  {'':20s}   {scenario['description']}")
            print(f"  {'':20s}   {scenario['requests']} req per pipeline, {scenario['concurrent']} concurrent")
            print(f"  {'':20s}   ⏱️  {scenario['time_estimate']}, 💰 {scenario['cost_estimate']}")
            print()
    
    print("="*70)
    print("\nUsage: python test_scenarios.py <scenario_key>")
    print("Example: python test_scenarios.py user_smoke\n")

def main():
    """Main CLI entry point"""
    
    if len(sys.argv) < 2:
        list_scenarios()
        return 0
    
    scenario_key = sys.argv[1]
    
    if scenario_key in ['-l', '--list', 'list']:
        list_scenarios()
        return 0
    
    try:
        exit_code = asyncio.run(run_scenario(scenario_key))
        return exit_code
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

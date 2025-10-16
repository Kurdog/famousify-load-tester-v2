#!/usr/bin/env python3
"""
Cost Calculator for Famousify Load Tests
Quick utility to estimate costs before running tests
"""

import sys

# Cost configuration
COST_PER_GENERATION = 0.08  # EUR
SAFETY_MARGIN = 1.10  # 10% extra

# Time estimates (seconds per generation)
TIME_USER = 50
TIME_TEEINBLUE = 120

def calculate_cost(num_requests: int, pipeline: str = "user", concurrent: int = 10):
    """Calculate cost and time estimates"""
    
    # Base cost
    base_cost = num_requests * COST_PER_GENERATION
    cost_with_margin = base_cost * SAFETY_MARGIN
    
    # Time estimate
    if pipeline == "teeinblue":
        avg_time_per_req = TIME_TEEINBLUE
    else:
        avg_time_per_req = TIME_USER
    
    # Total time accounting for concurrency
    total_seconds = (num_requests * avg_time_per_req) / concurrent
    total_minutes = total_seconds / 60
    total_hours = total_minutes / 60
    
    return {
        "requests": num_requests,
        "pipeline": pipeline,
        "concurrent": concurrent,
        "base_cost": base_cost,
        "cost_with_margin": cost_with_margin,
        "margin_percentage": (SAFETY_MARGIN - 1) * 100,
        "total_seconds": total_seconds,
        "total_minutes": total_minutes,
        "total_hours": total_hours,
        "avg_time_per_req": avg_time_per_req
    }

def print_cost_table():
    """Print cost table for common scenarios"""
    
    print("\n" + "="*80)
    print("💰 FAMOUSIFY LOAD TEST - COST CALCULATOR")
    print("="*80)
    print(f"\nBase cost per generation: €{COST_PER_GENERATION}")
    print(f"Safety margin: +{int((SAFETY_MARGIN-1)*100)}%")
    print()
    
    # Quick reference table
    print("📊 QUICK REFERENCE TABLE")
    print("-"*80)
    print(f"{'Requests':<12} {'Pipeline':<12} {'Concurrent':<12} {'Base Cost':<12} {'With Margin':<12} {'Time':<12}")
    print("-"*80)
    
    scenarios = [
        (3, "user", 1),
        (10, "user", 5),
        (50, "user", 10),
        (100, "user", 20),
        (200, "user", 20),
        (3, "teeinblue", 1),
        (10, "teeinblue", 5),
        (25, "teeinblue", 5),
        (50, "teeinblue", 10),
        (100, "teeinblue", 10),
    ]
    
    for requests, pipeline, concurrent in scenarios:
        result = calculate_cost(requests, pipeline, concurrent)
        
        if result['total_hours'] >= 1:
            time_str = f"{result['total_hours']:.1f}h"
        else:
            time_str = f"{int(result['total_minutes'])}min"
        
        print(f"{requests:<12} {pipeline:<12} {concurrent:<12} "
              f"€{result['base_cost']:<11.2f} €{result['cost_with_margin']:<11.2f} {time_str:<12}")
    
    print("-"*80)
    print()

def calculate_custom():
    """Interactive cost calculator"""
    
    print("\n" + "="*80)
    print("🧮 CUSTOM COST CALCULATOR")
    print("="*80)
    print()
    
    try:
        # Get inputs
        num_requests = int(input("Number of requests: "))
        
        print("\nPipeline:")
        print("1. USER (standard, ~50s per request)")
        print("2. TEEINBLUE (with bg removal + upscale, ~120s per request)")
        pipeline_choice = input("Select [1]: ").strip() or "1"
        pipeline = "teeinblue" if pipeline_choice == "2" else "user"
        
        concurrent = int(input(f"Concurrent requests [{min(num_requests, 10)}]: ") or str(min(num_requests, 10)))
        
        # Calculate
        result = calculate_cost(num_requests, pipeline, concurrent)
        
        # Display results
        print("\n" + "="*80)
        print("📊 COST ESTIMATE")
        print("="*80)
        print(f"\nTest Configuration:")
        print(f"  Requests: {result['requests']}")
        print(f"  Pipeline: {result['pipeline'].upper()}")
        print(f"  Concurrent: {result['concurrent']}")
        print(f"  Avg time per request: {result['avg_time_per_req']}s")
        
        print(f"\n💰 Cost Breakdown:")
        print(f"  Base cost: €{result['base_cost']:.2f}")
        print(f"  Safety margin (+{int(result['margin_percentage'])}%): €{result['cost_with_margin'] - result['base_cost']:.2f}")
        print(f"  Total estimate: €{result['cost_with_margin']:.2f}")
        
        print(f"\n⏱️  Time Estimate:")
        
        if result['total_hours'] >= 1:
            print(f"  Total time: {result['total_hours']:.1f} hours ({int(result['total_minutes'])} minutes)")
        else:
            print(f"  Total time: {int(result['total_minutes'])} minutes ({int(result['total_seconds'])} seconds)")
        
        # Cost per minute/hour
        cost_per_minute = result['cost_with_margin'] / result['total_minutes']
        print(f"  Cost per minute: €{cost_per_minute:.3f}")
        
        # Warnings
        if result['cost_with_margin'] > 10:
            print(f"\n⚠️  WARNING: High cost test (>€10)")
            print(f"   Consider starting with a smaller test first")
        
        if result['total_hours'] > 2:
            print(f"\n⚠️  WARNING: Long duration test (>{int(result['total_hours'])}h)")
            print(f"   Ensure system stability before running")
        
        print("\n" + "="*80)
        print()
        
        # Ask if should run
        run = input("Do you want to run this test? (yes/no): ")
        if run.lower() in ['yes', 'y']:
            print("\n✅ Run test with:")
            print(f"   python famousify_load_tester_v2.py --cli")
            print(f"   Or: python test_scenarios.py (for predefined scenarios)")
        
    except ValueError:
        print("❌ Invalid input")
        return
    except KeyboardInterrupt:
        print("\n\n⏹️  Cancelled")
        return

def calculate_budget(monthly_budget: float):
    """Calculate how many tests fit in a budget"""
    
    print("\n" + "="*80)
    print("📅 MONTHLY BUDGET CALCULATOR")
    print("="*80)
    print()
    
    print(f"Monthly budget: €{monthly_budget:.2f}")
    print()
    
    # Calculate for different scenarios
    scenarios = {
        "Smoke tests (3 req)": 3,
        "Quick tests (10 req)": 10,
        "Normal load (50 req)": 50,
        "Heavy load (100 req)": 100,
        "Stress test (200 req)": 200
    }
    
    print("📊 Tests you can run:")
    print("-"*80)
    print(f"{'Test Type':<30} {'Cost Each':<15} {'Tests/Month':<15} {'Total Requests'}")
    print("-"*80)
    
    for name, requests in scenarios.items():
        cost_each = requests * COST_PER_GENERATION * SAFETY_MARGIN
        tests_per_month = int(monthly_budget / cost_each)
        total_requests = tests_per_month * requests
        
        print(f"{name:<30} €{cost_each:<14.2f} {tests_per_month:<15} {total_requests}")
    
    print("-"*80)
    print()
    
    # Recommendations
    print("💡 Recommendations:")
    
    if monthly_budget < 5:
        print("  • Focus on smoke tests (3-10 requests)")
        print("  • Run tests only for critical changes")
    elif monthly_budget < 20:
        print("  • Mix of smoke tests and normal loads")
        print("  • Run 1-2 normal load tests per week")
    elif monthly_budget < 50:
        print("  • Regular normal and heavy load testing")
        print("  • Weekly stress tests possible")
    else:
        print("  • Full testing suite available")
        print("  • Daily load tests feasible")
        print("  • Consider automated CI/CD integration")
    
    print()

def main():
    """Main CLI entry point"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "table":
            print_cost_table()
        elif command == "budget":
            try:
                if len(sys.argv) > 2:
                    budget = float(sys.argv[2])
                else:
                    budget = float(input("Monthly budget (EUR): "))
                calculate_budget(budget)
            except ValueError:
                print("❌ Invalid budget amount")
        elif command == "calc":
            calculate_custom()
        else:
            print(f"❌ Unknown command: {command}")
            print("\nUsage:")
            print("  python cost_calculator.py table          # Show cost table")
            print("  python cost_calculator.py calc           # Custom calculator")
            print("  python cost_calculator.py budget [amount] # Budget calculator")
    else:
        # Interactive menu
        print("\n" + "="*80)
        print("💰 FAMOUSIFY COST CALCULATOR")
        print("="*80)
        print("\nWhat would you like to do?")
        print("1. View cost table")
        print("2. Calculate custom test cost")
        print("3. Calculate monthly budget")
        print("4. Exit")
        print()
        
        choice = input("Select [1]: ").strip() or "1"
        
        if choice == "1":
            print_cost_table()
        elif choice == "2":
            calculate_custom()
        elif choice == "3":
            try:
                budget = float(input("\nMonthly budget (EUR): "))
                calculate_budget(budget)
            except ValueError:
                print("❌ Invalid budget amount")
        elif choice == "4":
            print("Goodbye!")
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()

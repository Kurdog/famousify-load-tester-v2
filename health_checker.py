#!/usr/bin/env python3
"""
Health Checker for Famousify Load Tester V2
Validates system before running expensive load tests
"""

import asyncio
import aiohttp
import sys
from famousify_load_tester_v2 import Config

class HealthChecker:
    """Comprehensive system health validation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
    
    def print_header(self, text: str):
        print("\n" + "="*70)
        print(f"  {text}")
        print("="*70)
    
    def check_result(self, name: str, passed: bool, message: str = "", warning: bool = False):
        """Print check result"""
        if passed:
            print(f"✅ {name}: {message if message else 'OK'}")
            self.checks_passed += 1
        elif warning:
            print(f"⚠️  {name}: {message}")
            self.warnings.append(f"{name}: {message}")
            self.checks_passed += 1  # Warning doesn't fail the check
        else:
            print(f"❌ {name}: {message}")
            self.checks_failed += 1
    
    async def check_base_connectivity(self) -> bool:
        """Check if base URL is reachable"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config.base_url}/health", timeout=10) as resp:
                    if resp.status == 200:
                        self.check_result("Base URL Connectivity", True, f"Connected to {self.config.base_url}")
                        return True
                    else:
                        self.check_result("Base URL Connectivity", False, f"HTTP {resp.status}")
                        return False
        except aiohttp.ClientConnectorError:
            self.check_result("Base URL Connectivity", False, "Cannot connect - check URL or network")
            return False
        except asyncio.TimeoutError:
            self.check_result("Base URL Connectivity", False, "Connection timeout")
            return False
        except Exception as e:
            self.check_result("Base URL Connectivity", False, str(e))
            return False
    
    async def check_test_image(self) -> bool:
        """Check if test image URL is valid and accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.config.test_image_url, timeout=10) as resp:
                    if resp.status == 200:
                        content_type = resp.headers.get('Content-Type', '')
                        if 'image' in content_type:
                            image_data = await resp.read()
                            size_kb = len(image_data) / 1024
                            self.check_result("Test Image", True, f"Valid image ({size_kb:.1f}KB)")
                            return True
                        else:
                            self.check_result("Test Image", False, f"Not an image: {content_type}")
                            return False
                    else:
                        self.check_result("Test Image", False, f"HTTP {resp.status}")
                        return False
        except Exception as e:
            self.check_result("Test Image", False, str(e))
            return False
    
    async def check_user_endpoint(self) -> bool:
        """Check USER pipeline endpoint availability"""
        try:
            async with aiohttp.ClientSession() as session:
                # Try OPTIONS to check if endpoint exists
                async with session.options(f"{self.config.base_url}/api/user/generate", timeout=10) as resp:
                    if resp.status in [200, 204, 405]:  # 405 = Method Not Allowed but endpoint exists
                        self.check_result("USER Endpoint", True, "/api/user/generate available")
                        return True
                    else:
                        self.check_result("USER Endpoint", False, f"HTTP {resp.status}")
                        return False
        except Exception as e:
            self.check_result("USER Endpoint", False, str(e))
            return False
    
    async def check_teeinblue_endpoint(self) -> bool:
        """Check TEEINBLUE pipeline endpoint availability"""
        try:
            async with aiohttp.ClientSession() as session:
                # Check status endpoint first
                async with session.get(f"{self.config.base_url}/api/teeinblue/status", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        enabled = data.get('enabled', False)
                        if enabled:
                            self.check_result("TEEINBLUE Endpoint", True, "Enabled and available")
                            return True
                        else:
                            self.check_result("TEEINBLUE Endpoint", False, "Disabled on server", warning=True)
                            return False
                    else:
                        # Try main endpoint as fallback
                        async with session.options(f"{self.config.base_url}/api/teeinblue/effect", timeout=10) as resp2:
                            if resp2.status in [200, 204, 405]:
                                self.check_result("TEEINBLUE Endpoint", True, "/api/teeinblue/effect available", warning=True)
                                return True
                            else:
                                self.check_result("TEEINBLUE Endpoint", False, "Not available")
                                return False
        except Exception as e:
            self.check_result("TEEINBLUE Endpoint", False, str(e))
            return False
    
    async def check_styles_availability(self) -> bool:
        """Check if configured styles exist"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config.base_url}/api/admin/styles", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        available_styles = list(data.get('styles', {}).keys())
                        
                        missing_styles = [s for s in self.config.styles if s not in available_styles]
                        
                        if not missing_styles:
                            self.check_result("Styles Availability", True, f"All {len(self.config.styles)} styles available")
                            return True
                        else:
                            self.check_result("Styles Availability", False, 
                                            f"Missing styles: {', '.join(missing_styles)}", warning=True)
                            return True  # Warning, not failure
                    else:
                        self.check_result("Styles Availability", True, "Cannot verify (endpoint protected)", warning=True)
                        return True  # Can't verify, but don't fail
        except Exception as e:
            self.check_result("Styles Availability", True, f"Cannot verify: {e}", warning=True)
            return True  # Can't verify, but don't fail
    
    def check_timeouts(self) -> bool:
        """Validate timeout configuration"""
        if self.config.timeout_user < 60:
            self.check_result("USER Timeout", False, "Too short (min 60s recommended)")
            return False
        elif self.config.timeout_user > 600:
            self.check_result("USER Timeout", True, f"{self.config.timeout_user}s (very long)", warning=True)
        else:
            self.check_result("USER Timeout", True, f"{self.config.timeout_user}s")
        
        if self.config.timeout_teeinblue < 120:
            self.check_result("TEEINBLUE Timeout", False, "Too short (min 120s recommended)")
            return False
        elif self.config.timeout_teeinblue > 600:
            self.check_result("TEEINBLUE Timeout", True, f"{self.config.timeout_teeinblue}s (very long)", warning=True)
        else:
            self.check_result("TEEINBLUE Timeout", True, f"{self.config.timeout_teeinblue}s")
        
        return True
    
    def check_retry_config(self) -> bool:
        """Validate retry configuration"""
        if self.config.max_retries < 1:
            self.check_result("Retry Config", False, "No retries configured")
            return False
        elif self.config.max_retries > 5:
            self.check_result("Retry Config", True, f"{self.config.max_retries} retries (may be excessive)", warning=True)
        else:
            self.check_result("Retry Config", True, f"{self.config.max_retries} retries, {self.config.retry_delay}s delay")
        
        return True
    
    async def run_quick_test(self, pipeline: str = "user") -> bool:
        """Run a quick single request test"""
        print(f"\n🧪 Running quick {pipeline.upper()} test...")
        
        try:
            from famousify_load_tester_v2 import LoadTester
            
            tester = LoadTester(self.config)
            
            # Run single test
            report = await tester.run_test(num_requests=1, concurrent=1, pipeline=pipeline)
            
            if report['summary']['success_rate'] == 100:
                self.check_result(f"Quick {pipeline.upper()} Test", True, 
                                f"Completed in {report['timing']['avg_time']:.1f}s")
                return True
            else:
                error = report['results'][0].get('error', 'Unknown error')
                self.check_result(f"Quick {pipeline.upper()} Test", False, error)
                return False
        
        except Exception as e:
            self.check_result(f"Quick {pipeline.upper()} Test", False, str(e))
            return False
    
    async def run_all_checks(self, include_quick_test: bool = False):
        """Run all health checks"""
        
        self.print_header("🏥 FAMOUSIFY LOAD TESTER - HEALTH CHECK")
        
        print("\n📋 Configuration:")
        print(f"  Base URL: {self.config.base_url}")
        print(f"  Test Image: {self.config.test_image_url}")
        print(f"  Styles: {', '.join(self.config.styles)}")
        
        # Basic connectivity
        self.print_header("🌐 Connectivity Checks")
        await self.check_base_connectivity()
        await self.check_test_image()
        
        # Endpoints
        self.print_header("🔌 Endpoint Checks")
        await self.check_user_endpoint()
        await self.check_teeinblue_endpoint()
        await self.check_styles_availability()
        
        # Configuration
        self.print_header("⚙️  Configuration Checks")
        self.check_timeouts()
        self.check_retry_config()
        
        # Optional quick test
        if include_quick_test:
            self.print_header("🧪 Quick Test")
            print("⚠️  This will consume credits (€0.08)")
            confirm = input("Run quick test? (yes/no): ")
            if confirm.lower() in ['yes', 'y']:
                await self.run_quick_test("user")
        
        # Summary
        self.print_header("📊 HEALTH CHECK SUMMARY")
        print(f"\n✅ Passed: {self.checks_passed}")
        print(f"❌ Failed: {self.checks_failed}")
        
        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        print()
        
        if self.checks_failed == 0:
            print("🎉 All checks passed! System ready for load testing.")
            return 0
        else:
            print("⛔ Some checks failed. Fix issues before running load tests.")
            return 1

# ==================== CLI ====================

async def main():
    """Main CLI entry point"""
    
    config = Config()
    config.load_from_file()
    
    checker = HealthChecker(config)
    
    # Check if quick test requested
    include_quick_test = "--quick-test" in sys.argv or "-q" in sys.argv
    
    exit_code = await checker.run_all_checks(include_quick_test)
    
    if exit_code == 0:
        print("\n💡 Next steps:")
        print("  python famousify_load_tester_v2.py        # GUI mode")
        print("  python famousify_load_tester_v2.py --cli  # CLI mode")
        print("  python test_scenarios.py list             # View scenarios")
        print()
    
    return exit_code

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

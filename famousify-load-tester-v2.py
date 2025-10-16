class Config:
    """Centralized configuration"""
    
    def __init__(self):
        self.base_url = os.getenv("FAMOUSIFY_BASE_URL", "https://web-production-abb48.up.railway.app")
        self.admin_token = os.getenv("FAMOUSIFY_ADMIN_TOKEN", "famousify-admin-2025")
        self.test_image_url = os.getenv("FAMOUSIFY_TEST_IMAGE_URL", 
                                       "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800")
        
        # Timeouts (increased for Teeinblue)
        self.timeout_user = int(os.getenv("FAMOUSIFY_TIMEOUT_USER", "180"))  # 3 min for USER
        self.timeout_teeinblue = int(os.getenv("FAMOUSIFY_TIMEOUT_TEEINBLUE", "300"))  # 5 min for Teeinblue
        self.poll_interval = int(os.getenv("FAMOUSIFY_POLL_INTERVAL", "5"))
        
        # Retry configuration
        self.max_retries = int(os.getenv("FAMOUSIFY_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("FAMOUSIFY_RETRY_DELAY", "10"))
        
        # Cost per generation (Flux MAX)
        self.cost_per_generation = float(os.getenv("FAMOUSIFY_COST_PER_GEN", "0.08"))
        
        # Cost estimation margin (10% extra for safety)
        self.cost_margin = float(os.getenv("FAMOUSIFY_COST_MARGIN", "1.10"))#!/usr/bin/env python3
"""
Famousify Load Tester V2 - Complete & Robust
Tests both USER and TEEINBLUE pipelines with advanced error handling
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import statistics
from collections import defaultdict

# GUI imports (graceful fallback)
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, filedialog, messagebox
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("⚠️  GUI not available, running in CLI mode")

# ==================== CONFIGURATION ====================

class Config:
    """Centralized configuration"""
    
    def __init__(self):
        self.base_url = os.getenv("FAMOUSIFY_BASE_URL", "https://web-production-abb48.up.railway.app")
        self.admin_token = os.getenv("FAMOUSIFY_ADMIN_TOKEN", "famousify-admin-2025")
        self.test_image_url = os.getenv("FAMOUSIFY_TEST_IMAGE_URL", 
                                       "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800")
        
        # Timeouts (increased for Teeinblue)
        self.timeout_user = int(os.getenv("FAMOUSIFY_TIMEOUT_USER", "180"))  # 3 min for USER
        self.timeout_teeinblue = int(os.getenv("FAMOUSIFY_TIMEOUT_TEEINBLUE", "300"))  # 5 min for Teeinblue
        self.poll_interval = int(os.getenv("FAMOUSIFY_POLL_INTERVAL", "5"))
        
        # Retry configuration
        self.max_retries = int(os.getenv("FAMOUSIFY_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("FAMOUSIFY_RETRY_DELAY", "10"))
        
        # Styles
        self.styles = ["kimono_vogue", "pop_art", "urban_graffiti"]
        
        # Directories
        self.results_dir = Path("results")
        self.images_dir = self.results_dir / "images"
        self.reports_dir = self.results_dir / "reports"
        
        self.results_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    def save_to_file(self, filepath: str = ".env"):
        with open(filepath, 'w') as f:
            f.write(f"FAMOUSIFY_BASE_URL={self.base_url}\n")
            f.write(f"FAMOUSIFY_ADMIN_TOKEN={self.admin_token}\n")
            f.write(f"FAMOUSIFY_TEST_IMAGE_URL={self.test_image_url}\n")
            f.write(f"FAMOUSIFY_TIMEOUT_USER={self.timeout_user}\n")
            f.write(f"FAMOUSIFY_TIMEOUT_TEEINBLUE={self.timeout_teeinblue}\n")
            f.write(f"FAMOUSIFY_POLL_INTERVAL={self.poll_interval}\n")
            f.write(f"FAMOUSIFY_MAX_RETRIES={self.max_retries}\n")
    
    def load_from_file(self, filepath: str = ".env"):
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key, value = key.strip(), value.strip()
                    
                    if key == "FAMOUSIFY_BASE_URL":
                        self.base_url = value
                    elif key == "FAMOUSIFY_ADMIN_TOKEN":
                        self.admin_token = value
                    elif key == "FAMOUSIFY_TEST_IMAGE_URL":
                        self.test_image_url = value
                    elif key == "FAMOUSIFY_TIMEOUT_USER":
                        self.timeout_user = int(value)
                    elif key == "FAMOUSIFY_TIMEOUT_TEEINBLUE":
                        self.timeout_teeinblue = int(value)
                    elif key == "FAMOUSIFY_POLL_INTERVAL":
                        self.poll_interval = int(value)
                    elif key == "FAMOUSIFY_MAX_RETRIES":
                        self.max_retries = int(value)

# ==================== TEST RESULT ====================

class TestResult:
    """Individual test result with pipeline type"""
    def __init__(self, test_id: int, style: str, pipeline: str = "user"):
        self.test_id = test_id
        self.style = style
        self.pipeline = pipeline  # "user" or "teeinblue"
        self.start_time = time.time()
        self.end_time = None
        self.total_time = None
        self.job_id = None
        self.success = False
        self.error = None
        self.image_url = None
        self.status_code = None
        self.retries = 0
        self.phases = {}  # Track pipeline phases
    
    def complete(self, success: bool, error: str = None, image_url: str = None):
        self.end_time = time.time()
        self.total_time = self.end_time - self.start_time
        self.success = success
        self.error = error
        self.image_url = image_url
    
    def to_dict(self):
        return {
            "test_id": self.test_id,
            "style": self.style,
            "pipeline": self.pipeline,
            "job_id": self.job_id,
            "success": self.success,
            "total_time": round(self.total_time, 2) if self.total_time else None,
            "error": self.error,
            "image_url": self.image_url,
            "status_code": self.status_code,
            "retries": self.retries,
            "phases": self.phases
        }

# ==================== LOAD TESTER ====================

class LoadTester:
    """Core load testing engine with multi-pipeline support"""
    
    def __init__(self, config: Config, progress_callback=None):
        self.config = config
        self.progress_callback = progress_callback
        self.results: List[TestResult] = []
        self.active_tests = 0
        self.max_concurrent = 0
        self.test_start_time = None
        self.stopped = False
    
    def log(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        print(formatted)
        
        if self.progress_callback:
            self.progress_callback(formatted, level)
    
    async def download_test_image(self, session: aiohttp.ClientSession) -> bytes:
        """Download test image with retry"""
        for attempt in range(self.config.max_retries):
            try:
                async with session.get(self.config.test_image_url, timeout=30) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    else:
                        raise Exception(f"HTTP {resp.status}")
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    self.log(f"Image download attempt {attempt+1} failed, retrying...", "warning")
                    await asyncio.sleep(2)
                else:
                    raise Exception(f"Failed to download image after {self.config.max_retries} attempts: {e}")
    
    async def submit_user_generation(self, session: aiohttp.ClientSession, 
                                     result: TestResult, image_data: bytes) -> bool:
        """Submit USER pipeline generation"""
        try:
            data = aiohttp.FormData()
            data.add_field('style', result.style)
            data.add_field('user_id', 'load_test_user')
            data.add_field('image', image_data, filename='test.jpg', content_type='image/jpeg')
            
            self.log(f"[{result.test_id}] Submitting USER generation (style: {result.style})...")
            
            async with session.post(
                f"{self.config.base_url}/api/user/generate",
                data=data,
                timeout=30
            ) as resp:
                result.status_code = resp.status
                
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {error_text[:200]}")
                
                response_data = await resp.json()
                
                if not response_data.get('success'):
                    raise Exception(f"API Error: {response_data.get('error', 'Unknown')}")
                
                result.job_id = response_data.get('job_id')
                
                if not result.job_id:
                    raise Exception("No job_id in response")
                
                self.log(f"[{result.test_id}] ✓ Submitted - Job: {result.job_id}")
                return True
                
        except Exception as e:
            self.log(f"[{result.test_id}] ✗ Submit failed: {e}", "error")
            return False
    
    async def submit_teeinblue_generation(self, session: aiohttp.ClientSession,
                                         result: TestResult, image_data: bytes) -> bool:
        """Submit TEEINBLUE pipeline generation (with bg removal + upscale)"""
        try:
            data = aiohttp.FormData()
            data.add_field('file', image_data, filename='test.jpg', content_type='image/jpeg')
            data.add_field('effect', result.style)
            data.add_field('shop', 'load-test')
            
            self.log(f"[{result.test_id}] Submitting TEEINBLUE generation (style: {result.style})...")
            
            # Note: Teeinblue uses /api/teeinblue/effect endpoint
            async with session.post(
                f"{self.config.base_url}/api/teeinblue/effect",
                data=data,
                timeout=30,
                headers={'X-Shop-Domain': 'load-test.com'}
            ) as resp:
                result.status_code = resp.status
                
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {error_text[:200]}")
                
                # Teeinblue returns image directly, but we need job_id for tracking
                # Check if it's JSON (async mode) or image (sync mode)
                content_type = resp.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    response_data = await resp.json()
                    result.job_id = response_data.get('job_id')
                    self.log(f"[{result.test_id}] ✓ Submitted - Job: {result.job_id}")
                    return True
                else:
                    # Sync mode - save image directly
                    image_bytes = await resp.read()
                    if len(image_bytes) > 1000:  # Valid image
                        result.job_id = f"teeinblue_sync_{result.test_id}"
                        # Save image
                        image_path = self.config.images_dir / f"{result.job_id}.png"
                        image_path.write_bytes(image_bytes)
                        result.image_url = str(image_path)
                        result.complete(True, None, str(image_path))
                        self.log(f"[{result.test_id}] ✓ Completed (sync) - Saved: {image_path}")
                        return True
                    else:
                        raise Exception("Invalid image response")
                        
        except Exception as e:
            self.log(f"[{result.test_id}] ✗ Submit failed: {e}", "error")
            return False
    
    async def poll_user_status(self, session: aiohttp.ClientSession, result: TestResult):
        """Poll USER pipeline status"""
        start_poll = time.time()
        timeout = self.config.timeout_user
        
        while time.time() - start_poll < timeout:
            if self.stopped:
                result.complete(False, "Test stopped")
                return
            
            try:
                # Try standard status endpoint
                async with session.get(
                    f"{self.config.base_url}/status/{result.job_id}",
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        content_type = resp.headers.get('Content-Type', '')
                        
                        # Check if response is JSON
                        if 'application/json' in content_type:
                            data = await resp.json()
                            status = data.get('status')
                            
                            # Track phases
                            if 'phases' in data:
                                result.phases = data['phases']
                            
                            if status == 'completed':
                                # Extract image URL
                                image_url = None
                                phases = data.get('phases', {})
                                gen_phase = phases.get('style_generation', {})
                                styles = gen_phase.get('styles', {})
                                
                                for style_data in styles.values():
                                    if style_data.get('output_url'):
                                        image_url = style_data['output_url']
                                        break
                                
                                result.complete(True, None, image_url)
                                self.log(f"[{result.test_id}] ✅ Completed in {result.total_time:.1f}s")
                                return
                            
                            elif status == 'failed':
                                error = data.get('error', 'Unknown error')
                                result.complete(False, error)
                                self.log(f"[{result.test_id}] ❌ Failed: {error}", "error")
                                return
                        else:
                            # HTML response - endpoint not found or error
                            await asyncio.sleep(self.config.poll_interval)
                            continue
                    else:
                        await asyncio.sleep(self.config.poll_interval)
                        continue
            
            except asyncio.TimeoutError:
                self.log(f"[{result.test_id}] Poll timeout, retrying...", "warning")
            except Exception as e:
                self.log(f"[{result.test_id}] Poll error: {e}", "warning")
            
            await asyncio.sleep(self.config.poll_interval)
        
        # Timeout
        result.complete(False, "Polling timeout")
        self.log(f"[{result.test_id}] ❌ Polling timeout after {timeout}s", "error")
    
    async def poll_teeinblue_status(self, session: aiohttp.ClientSession, result: TestResult):
        """Poll TEEINBLUE pipeline status (longer timeout, track phases)"""
        start_poll = time.time()
        timeout = self.config.timeout_teeinblue
        
        while time.time() - start_poll < timeout:
            if self.stopped:
                result.complete(False, "Test stopped")
                return
            
            try:
                # Teeinblue uses different status endpoint
                async with session.get(
                    f"{self.config.base_url}/api/teeinblue/test-status/{result.job_id}",
                    timeout=10
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        status = data.get('status')
                        phase = data.get('phase')
                        
                        # Track phase
                        if phase:
                            result.phases[phase] = time.time() - start_poll
                        
                        if status == 'completed' or phase == 'completed':
                            # Get final image
                            image_url = data.get('output_url')
                            if not image_url:
                                image_url = f"{self.config.base_url}/api/teeinblue/result/{result.job_id}"
                            
                            result.complete(True, None, image_url)
                            self.log(f"[{result.test_id}] ✅ Teeinblue completed in {result.total_time:.1f}s")
                            return
                        
                        elif status == 'failed':
                            error = data.get('error', 'Unknown error')
                            result.complete(False, error)
                            self.log(f"[{result.test_id}] ❌ Failed: {error}", "error")
                            return
            
            except Exception as e:
                self.log(f"[{result.test_id}] Poll error: {e}", "warning")
            
            await asyncio.sleep(self.config.poll_interval)
        
        # Timeout
        result.complete(False, "Teeinblue polling timeout")
        self.log(f"[{result.test_id}] ❌ Teeinblue timeout after {timeout}s", "error")
    
    async def run_single_test(self, session: aiohttp.ClientSession,
                              test_id: int, style: str, pipeline: str) -> TestResult:
        """Run single test with retry logic"""
        result = TestResult(test_id, style, pipeline)
        
        if self.stopped:
            result.complete(False, "Test stopped by user")
            return result
        
        self.active_tests += 1
        self.max_concurrent = max(self.max_concurrent, self.active_tests)
        
        try:
            # Download image (with retry)
            self.log(f"[{test_id}] Downloading test image...")
            image_data = await self.download_test_image(session)
            
            # Submit with retry
            submit_success = False
            for attempt in range(self.config.max_retries):
                if pipeline == "teeinblue":
                    submit_success = await self.submit_teeinblue_generation(session, result, image_data)
                else:
                    submit_success = await self.submit_user_generation(session, result, image_data)
                
                if submit_success:
                    break
                
                result.retries += 1
                if attempt < self.config.max_retries - 1:
                    self.log(f"[{test_id}] Retry {attempt+1}/{self.config.max_retries} after {self.config.retry_delay}s...", "warning")
                    await asyncio.sleep(self.config.retry_delay)
            
            if not submit_success:
                result.complete(False, f"Failed to submit after {self.config.max_retries} attempts")
                return result
            
            # Poll for completion
            if pipeline == "teeinblue":
                # Check if it was sync mode
                if not result.success:  # Not already completed in sync mode
                    await self.poll_teeinblue_status(session, result)
            else:
                await self.poll_user_status(session, result)
        
        except Exception as e:
            result.complete(False, str(e))
            self.log(f"[{test_id}] ❌ Unexpected error: {e}", "error")
        finally:
            self.active_tests -= 1
        
        return result
    
    async def run_test(self, num_requests: int, concurrent: int = 10,
                       styles: Optional[List[str]] = None,
                       pipeline: str = "user") -> Dict:
        """Run load test"""
        if styles is None:
            styles = self.config.styles
        
        self.test_start_time = time.time()
        self.results = []
        self.stopped = False
        
        # Calculate cost estimate
        estimated_cost = num_requests * self.config.cost_per_generation
        estimated_cost_with_margin = estimated_cost * self.config.cost_margin
        
        pipeline_name = "TEEINBLUE (bg+upscale)" if pipeline == "teeinblue" else "USER (standard)"
        self.log(f"🚀 Starting {pipeline_name} load test:")
        self.log(f"   Requests: {num_requests}, Concurrent: {concurrent}")
        self.log(f"   Target: {self.config.base_url}")
        self.log(f"   Styles: {', '.join(styles)}")
        self.log(f"   💰 Estimated Cost: €{estimated_cost:.2f} (with {int((self.config.cost_margin-1)*100)}% margin: €{estimated_cost_with_margin:.2f})")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(num_requests):
                if self.stopped:
                    break
                
                style = styles[i % len(styles)]
                task = self.run_single_test(session, i+1, style, pipeline)
                tasks.append(task)
                
                # Control concurrency
                if len(tasks) >= concurrent:
                    completed = await asyncio.gather(*tasks[:concurrent])
                    self.results.extend(completed)
                    tasks = tasks[concurrent:]
                    
                    if not self.stopped and tasks:
                        await asyncio.sleep(0.5)
            
            # Complete remaining
            if tasks and not self.stopped:
                completed = await asyncio.gather(*tasks)
                self.results.extend(completed)
        
        total_time = time.time() - self.test_start_time
        report = self.generate_report(total_time, pipeline)
        self.save_report(report)
        
        return report
    
    def generate_report(self, total_time: float, pipeline: str) -> Dict:
        """Generate comprehensive test report"""
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        # Calculate actual cost
        actual_cost = len(successful) * self.config.cost_per_generation
        estimated_cost = len(self.results) * self.config.cost_per_generation
        cost_saved = estimated_cost - actual_cost
        
        report = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "base_url": self.config.base_url,
                "pipeline": pipeline,
                "total_requests": len(self.results),
                "concurrent": self.max_concurrent,
                "total_time": round(total_time, 2)
            },
            "summary": {
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": round(len(successful) / len(self.results) * 100, 2) if self.results else 0,
                "total_retries": sum(r.retries for r in self.results)
            },
            "cost": {
                "actual": round(actual_cost, 2),
                "estimated": round(estimated_cost, 2),
                "saved": round(cost_saved, 2),
                "cost_per_generation": self.config.cost_per_generation,
                "currency": "EUR"
            },
            "timing": {},
            "results": [r.to_dict() for r in self.results]
        }
        
        if successful:
            times = [r.total_time for r in successful]
            report["timing"] = {
                "avg_time": round(statistics.mean(times), 2),
                "min_time": round(min(times), 2),
                "max_time": round(max(times), 2),
                "median_time": round(statistics.median(times), 2),
                "p95_time": round(statistics.quantiles(times, n=20)[18], 2) if len(times) >= 20 else None
            }
        
        # Error analysis
        if failed:
            error_counts = defaultdict(int)
            for r in failed:
                error_key = (r.error[:50] if r.error else "Unknown")
                error_counts[error_key] += 1
            report["errors"] = dict(error_counts)
        
        # Health status
        success_rate = report["summary"]["success_rate"]
        avg_time = report["timing"].get("avg_time", 999)
        
        # Different thresholds for Teeinblue (longer acceptable times)
        if pipeline == "teeinblue":
            if success_rate >= 95 and avg_time < 120:
                report["health"] = "EXCELLENT"
            elif success_rate >= 90 and avg_time < 180:
                report["health"] = "GOOD"
            elif success_rate >= 80:
                report["health"] = "FAIR"
            else:
                report["health"] = "POOR"
        else:  # USER pipeline
            if success_rate >= 95 and avg_time < 45:
                report["health"] = "EXCELLENT"
            elif success_rate >= 90 and avg_time < 60:
                report["health"] = "GOOD"
            elif success_rate >= 80:
                report["health"] = "FAIR"
            else:
                report["health"] = "POOR"
        
        return report
    
    def save_report(self, report: Dict):
        """Save report to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pipeline = report["test_info"]["pipeline"]
        filename = self.config.reports_dir / f"load_test_{pipeline}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log(f"💾 Report saved: {filename}")
    
    def stop(self):
        """Stop ongoing test"""
        self.stopped = True
        self.log("⏹️  Stopping test...", "warning")

# ==================== GUI APPLICATION ====================

if GUI_AVAILABLE:
    class LoadTesterGUI:
        """Enhanced GUI with pipeline selection"""
        
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("Famousify Load Tester V2 - Multi-Pipeline")
            self.root.geometry("950x750")
            
            self.config = Config()
            self.config.load_from_file()
            
            self.tester = None
            self.test_task = None
            
            self.create_widgets()
            self.update_status("Ready")
        
        def create_widgets(self):
            notebook = ttk.Notebook(self.root)
            notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Tabs
            config_frame = ttk.Frame(notebook)
            notebook.add(config_frame, text="Configuration")
            self.create_config_tab(config_frame)
            
            test_frame = ttk.Frame(notebook)
            notebook.add(test_frame, text="Run Test")
            self.create_test_tab(test_frame)
            
            results_frame = ttk.Frame(notebook)
            notebook.add(results_frame, text="Results")
            self.create_results_tab(results_frame)
            
            # Status bar
            self.status_var = tk.StringVar()
            status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        def create_config_tab(self, parent):
            """Config tab"""
            ttk.Label(parent, text="Base URL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            self.base_url_var = tk.StringVar(value=self.config.base_url)
            ttk.Entry(parent, textvariable=self.base_url_var, width=60).grid(row=0, column=1, padx=5, pady=5)
            
            ttk.Label(parent, text="Admin Token:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            self.admin_token_var = tk.StringVar(value=self.config.admin_token)
            ttk.Entry(parent, textvariable=self.admin_token_var, width=60, show="*").grid(row=1, column=1, padx=5, pady=5)
            
            ttk.Label(parent, text="Test Image URL:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            self.test_image_var = tk.StringVar(value=self.config.test_image_url)
            ttk.Entry(parent, textvariable=self.test_image_var, width=60).grid(row=2, column=1, padx=5, pady=5)
            
            ttk.Label(parent, text="Timeout USER (s):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
            self.timeout_user_var = tk.IntVar(value=self.config.timeout_user)
            ttk.Spinbox(parent, from_=60, to=600, textvariable=self.timeout_user_var, width=10).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
            
            ttk.Label(parent, text="Timeout TEEINBLUE (s):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
            self.timeout_teeinblue_var = tk.IntVar(value=self.config.timeout_teeinblue)
            ttk.Spinbox(parent, from_=60, to=600, textvariable=self.timeout_teeinblue_var, width=10).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
            
            btn_frame = ttk.Frame(parent)
            btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
            
            ttk.Button(btn_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Load Config", command=self.load_config).pack(side=tk.LEFT, padx=5)
        
        def create_test_tab(self, parent):
            """Test tab with pipeline selection"""
            params_frame = ttk.LabelFrame(parent, text="Test Parameters", padding=10)
            params_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(params_frame, text="Total Requests:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
            self.num_requests_var = tk.IntVar(value=10)
            req_spinbox = ttk.Spinbox(params_frame, from_=1, to=200, textvariable=self.num_requests_var, width=10)
            req_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
            req_spinbox.bind('<KeyRelease>', self.update_cost_estimate)
            req_spinbox.bind('<<Increment>>', self.update_cost_estimate)
            req_spinbox.bind('<<Decrement>>', self.update_cost_estimate)
            
            ttk.Label(params_frame, text="Concurrent:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
            self.concurrent_var = tk.IntVar(value=10)
            ttk.Spinbox(params_frame, from_=1, to=50, textvariable=self.concurrent_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
            
            ttk.Label(params_frame, text="Pipeline:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
            self.pipeline_var = tk.StringVar(value="user")
            pipeline_combo = ttk.Combobox(params_frame, textvariable=self.pipeline_var, 
                                         values=["user", "teeinblue"], state="readonly", width=15)
            pipeline_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
            pipeline_combo.bind('<<ComboboxSelected>>', self.update_cost_estimate)
            
            # Info label
            info_label = ttk.Label(params_frame, text="USER: Standard 3:4 portrait (45-60s)\nTEEINBLUE: 1:1 square + bg removal + upscale (90-180s)", 
                                  foreground="gray")
            info_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
            
            # Cost estimate (NEW)
            cost_frame = ttk.LabelFrame(params_frame, text="💰 Cost Estimate", padding=5)
            cost_frame.grid(row=4, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=10)
            
            self.cost_label = ttk.Label(cost_frame, text="Calculating...", font=('Arial', 10, 'bold'), foreground='#0066cc')
            self.cost_label.pack()
            
            self.update_cost_estimate()  # Initial calculation
            
            btn_frame = ttk.Frame(parent)
            btn_frame.pack(fill=tk.X, padx=5, pady=10)
            
            self.start_btn = ttk.Button(btn_frame, text="▶ Start Test", command=self.start_test)
            self.start_btn.pack(side=tk.LEFT, padx=5)
            
            self.stop_btn = ttk.Button(btn_frame, text="⏹ Stop Test", command=self.stop_test, state=tk.DISABLED)
            self.stop_btn.pack(side=tk.LEFT, padx=5)
            
            progress_frame = ttk.LabelFrame(parent, text="Progress", padding=10)
            progress_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
            self.progress_bar.pack(fill=tk.X, pady=5)
            
            self.log_text = scrolledtext.ScrolledText(progress_frame, height=20, wrap=tk.WORD)
            self.log_text.pack(fill=tk.BOTH, expand=True)
        
        def create_results_tab(self, parent):
            """Results tab"""
            btn_frame = ttk.Frame(parent)
            btn_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Button(btn_frame, text="🔄 Refresh", command=self.load_results).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="📂 Open Results Folder", command=self.open_results_folder).pack(side=tk.LEFT, padx=5)
            
            list_frame = ttk.Frame(parent)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            self.results_tree = ttk.Treeview(list_frame, 
                                            columns=("Date", "Pipeline", "Requests", "Success", "Avg Time", "Health"), 
                                            show="headings")
            self.results_tree.heading("Date", text="Date")
            self.results_tree.heading("Pipeline", text="Pipeline")
            self.results_tree.heading("Requests", text="Requests")
            self.results_tree.heading("Success", text="Success %")
            self.results_tree.heading("Avg Time", text="Avg Time")
            self.results_tree.heading("Health", text="Health")
            
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
            self.results_tree.configure(yscrollcommand=scrollbar.set)
            
            self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.results_tree.bind('<Double-1>', self.view_result)
            
            self.load_results()
        
        def update_cost_estimate(self, event=None):
            """Update cost estimate in real-time"""
            try:
                num_requests = self.num_requests_var.get()
                base_cost = num_requests * self.config.cost_per_generation
                cost_with_margin = base_cost * self.config.cost_margin
                
                # Calculate time estimate based on pipeline
                pipeline = self.pipeline_var.get()
                if pipeline == "teeinblue":
                    avg_time = 120  # 2 minutes per request
                else:
                    avg_time = 50   # 50 seconds per request
                
                concurrent = self.concurrent_var.get()
                estimated_minutes = (num_requests * avg_time) / (concurrent * 60)
                
                cost_text = (f"Base: €{base_cost:.2f} | "
                           f"With margin (+{int((self.config.cost_margin-1)*100)}%): €{cost_with_margin:.2f}\n"
                           f"Est. Time: ~{int(estimated_minutes)} minutes")
                
                self.cost_label.config(text=cost_text)
            except:
                self.cost_label.config(text="Enter valid numbers")
        
        
        def get_quickstart_text(self):
            """Get quick start guide text"""
            return """
QUICK START GUIDE
═════════════════════════════════════════════════════════════════════

🚀 GETTING STARTED (3 STEPS)

1. CONFIGURE
   • Go to "Configuration" tab
   • Set your Base URL and Admin Token
   • Click "Save Configuration"

2. ESTIMATE COSTS
   • Go to "Run Test" tab
   • Adjust Total Requests and Pipeline
   • Watch real-time cost estimate update

3. RUN TEST
   • Click "▶ Start Test"
   • Watch progress in real-time
   • View results in "Results" tab

💰 COST EXAMPLES

3 requests:    €0.26  (~3 minutes)
10 requests:   €0.88  (~5-10 minutes)
50 requests:   €4.40  (~15-30 minutes)
200 requests:  €17.60 (~45min-2hours)

⚠️  IMPORTANT TIPS

• Always start with 3-10 requests to validate
• Check cost estimate before running
• USER pipeline is faster (45-60s per request)
• TEEINBLUE includes bg removal + upscale (90-180s)
• Use "Health Check" button to verify system

📚 For more details, check other help tabs →
"""
        
        def get_pipelines_text(self):
            """Get pipelines explanation"""
            return """
PIPELINE TYPES
═════════════════════════════════════════════════════════════════════

👤 USER PIPELINE (Standard)
────────────────────────────────────────────────────────────────────
Process: Upload → Preprocessing → AI Generation → Done
Format:  3:4 portrait (768x1024)
Time:    45-60 seconds average
Cost:    €0.08 per generation

Best for:
• Quick tests
• High volume generation
• Standard AI art needs
• Rapid iteration

🛒 TEEINBLUE PIPELINE (E-commerce)
────────────────────────────────────────────────────────────────────
Process: Upload → Preprocessing → AI Generation → 
         Background Removal → Upscaling → Done
Format:  1:1 square (1024x1024)
Time:    90-180 seconds average
Cost:    €0.08 + processing overhead

Best for:
• Shopify/Teeinblue integration
• Product mockups
• Print-on-demand
• Clean backgrounds needed
• E-commerce ready images

🎯 WHICH TO USE?

Use USER when:
✓ Testing functionality
✓ Need fast results
✓ Standard AI art generation
✓ Don't need background removal

Use TEEINBLUE when:
✓ Creating product mockups
✓ Need clean backgrounds
✓ E-commerce integration
✓ Professional quality needed
✓ Willing to wait longer
"""
        
        def get_cost_guide_text(self):
            """Get cost guide"""
            return """
COST GUIDE
═════════════════════════════════════════════════════════════════════

💰 PRICING

Base cost per generation: €0.08
Safety margin (default):  +10%
Estimated cost shown includes margin for safety

📊 COST BREAKDOWN BY SCENARIO

SMOKE TESTS (Quick Validation)
• 3 requests:   €0.26  (~3 min)
• 5 requests:   €0.44  (~5 min)

NORMAL LOAD TESTS
• 10 requests:  €0.88  (~5-10 min)
• 25 requests:  €2.20  (~12-25 min)
• 50 requests:  €4.40  (~15-45 min)

STRESS TESTS
• 100 requests: €8.80  (~30min-2h)
• 200 requests: €17.60 (~1-3 hours)

⏱️ TIME FACTORS

Pipeline speed:
• USER: ~50 seconds per request
• TEEINBLUE: ~120 seconds per request

Concurrency affects total time:
• 10 concurrent: Runs 10 requests simultaneously
• Higher concurrency = Faster completion
• But more concurrent = More system load

💡 COST OPTIMIZATION TIPS

1. Start Small
   Always test with 3-10 requests first

2. Use USER Pipeline for Testing
   Faster and cheaper for validation

3. Batch Similar Tests
   Run multiple tests at once to save time

4. Monitor Success Rate
   Failed requests still consume time but not cost

5. Use Cost Calculator
   Run: python cost_calculator.py

🔍 READING COST REPORTS

After test completion, check:
• Actual Cost: What you actually spent
• Estimated Cost: What was budgeted
• Saved: Money saved from failures
  (failures don't consume generation costs)

📅 MONTHLY BUDGETING

€5/month:   ~60 smoke tests or ~5 normal tests
€20/month:  ~220 smoke tests or ~20 normal tests
€50/month:  ~570 smoke tests or ~50 normal tests
€100/month: ~1140 smoke tests or ~110 normal tests

Use: python cost_calculator.py budget 50
"""
        
        def get_troubleshooting_text(self):
            """Get troubleshooting guide"""
            return """
TROUBLESHOOTING
═════════════════════════════════════════════════════════════════════

🔧 COMMON ISSUES

❌ CONNECTION TIMEOUT
────────────────────────────────────────────────────────────────────
Problem: Cannot connect to server
Solutions:
• Check BASE_URL is correct
• Verify Railway service is running
• Test with: curl [BASE_URL]/health
• Check your internet connection

❌ HTTP 401 UNAUTHORIZED
────────────────────────────────────────────────────────────────────
Problem: Authentication failed
Solutions:
• Verify ADMIN_TOKEN in configuration
• Token must match backend configuration
• Check for typos or extra spaces

❌ TESTS TIMING OUT
────────────────────────────────────────────────────────────────────
Problem: Tests fail with "Polling timeout"
Solutions:
• Increase timeout in Configuration tab
  - USER: Try 300s instead of 180s
  - TEEINBLUE: Try 600s instead of 300s
• Reduce concurrent requests
• Check if backend is overloaded

❌ HIGH FAILURE RATE
────────────────────────────────────────────────────────────────────
Problem: Success rate <80%
Solutions:
• Run Health Check first
• Reduce concurrent requests
• Increase timeouts
• Check backend logs
• Verify test image URL is accessible

❌ COST ESTIMATE SHOWS "ENTER VALID NUMBERS"
────────────────────────────────────────────────────────────────────
Problem: Cost calculation fails
Solutions:
• Ensure Total Requests is a valid number
• Ensure Concurrent is a valid number
• Try resetting values to defaults
• Restart the application

❌ GUI NOT LOADING
────────────────────────────────────────────────────────────────────
Problem: Interface doesn't appear
Solutions:
• Use CLI mode instead:
  python famousify_load_tester_v2.py --cli
• Install tkinter if missing:
  - Ubuntu: sudo apt-get install python3-tk
  - Mac: brew install python-tk
  - Windows: Reinstall Python with tk/tcl

🏥 HEALTH CHECK

Before running expensive tests:
1. Click "Health Check" button in Configuration
2. Verify all endpoints are available
3. Check test image is accessible
4. Validate timeout settings

📊 READING ERROR REPORTS

Check results JSON for error patterns:
• "Test stopped": User manually stopped
• "Timeout": Request took too long
• "HTTP xxx": Server error (check code)
• "Polling timeout": Status check failed

🆘 STILL STUCK?

1. Run health check: python health_checker.py
2. Check logs in results/reports/
3. Verify .env configuration
4. Try with minimal test (3 requests, 1 concurrent)
5. Contact: kurdog@gmail.com
"""
        
        def run_health_check(self):
            """Run health check"""
            messagebox.showinfo("Health Check", 
                              "Run health check from command line:\n\n"
                              "python health_checker.py\n\n"
                              "This will validate:\n"
                              "• Connection\n"
                              "• Endpoints\n"
                              "• Configuration\n"
                              "• Timeouts")
        
        def open_email(self):
            """Open email client"""
            import webbrowser
            webbrowser.open("mailto:kurdog@gmail.com")
        
        def update_status(self, message: str):
            self.status_var.set(message)
        
        def log_message(self, message: str, level: str = "info"):
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
        
        def save_config(self):
            self.config.base_url = self.base_url_var.get()
            self.config.admin_token = self.admin_token_var.get()
            self.config.test_image_url = self.test_image_var.get()
            self.config.timeout_user = self.timeout_user_var.get()
            self.config.timeout_teeinblue = self.timeout_teeinblue_var.get()
            
            self.config.save_to_file()
            self.update_status("Configuration saved")
            messagebox.showinfo("Success", "Configuration saved successfully!")
        
        def load_config(self):
            self.config.load_from_file()
            
            self.base_url_var.set(self.config.base_url)
            self.admin_token_var.set(self.config.admin_token)
            self.test_image_var.set(self.config.test_image_url)
            self.timeout_user_var.set(self.config.timeout_user)
            self.timeout_teeinblue_var.set(self.config.timeout_teeinblue)
            
            self.update_status("Configuration loaded")
            messagebox.showinfo("Success", "Configuration loaded successfully!")
        
        def start_test(self):
            self.config.base_url = self.base_url_var.get()
            self.config.admin_token = self.admin_token_var.get()
            self.config.test_image_url = self.test_image_var.get()
            self.config.timeout_user = self.timeout_user_var.get()
            self.config.timeout_teeinblue = self.timeout_teeinblue_var.get()
            
            self.log_text.delete(1.0, tk.END)
            
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.progress_var.set(0)
            
            self.tester = LoadTester(self.config, self.log_message)
            
            num_requests = self.num_requests_var.get()
            concurrent = self.concurrent_var.get()
            pipeline = self.pipeline_var.get()
            
            async def run_async():
                try:
                    report = await self.tester.run_test(num_requests, concurrent, pipeline=pipeline)
                    self.root.after(0, self.test_completed, report)
                except Exception as e:
                    self.root.after(0, self.test_failed, str(e))
            
            import threading
            def run_thread():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(run_async())
                loop.close()
            
            thread = threading.Thread(target=run_thread, daemon=True)
            thread.start()
            
            self.update_status(f"Test running ({pipeline})...")
        
        def stop_test(self):
            if self.tester:
                self.tester.stop()
        
        def test_completed(self, report: Dict):
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.progress_var.set(100)
            
            success_rate = report["summary"]["success_rate"]
            health = report["health"]
            pipeline = report["test_info"]["pipeline"]
            actual_cost = report["cost"]["actual"]
            
            self.update_status(f"Test completed ({pipeline}): {success_rate}% success, €{actual_cost}, {health}")
            
            messagebox.showinfo("Test Complete", 
                              f"Test finished ({pipeline})!\n\n"
                              f"Success Rate: {success_rate}%\n"
                              f"Actual Cost: €{actual_cost}\n"
                              f"Health: {health}")
            
            self.load_results()
        
        def test_failed(self, error: str):
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            
            self.update_status(f"Test failed: {error}")
            messagebox.showerror("Test Failed", f"Test failed with error:\n{error}")
        
        def load_results(self):
            self.results_tree.delete(*self.results_tree.get_children())
            
            result_files = sorted(self.config.reports_dir.glob("*.json"), reverse=True)
            
            for filepath in result_files[:20]:
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    date = data["test_info"]["timestamp"][:19]
                    pipeline = data["test_info"].get("pipeline", "user")
                    requests = data["test_info"]["total_requests"]
                    success = f"{data['summary']['success_rate']:.1f}%"
                    avg_time = f"{data['timing'].get('avg_time', 0):.1f}s"
                    health = data.get("health", "N/A")
                    
                    self.results_tree.insert("", tk.END, values=(date, pipeline, requests, success, avg_time, health),
                                            tags=(str(filepath),))
                
                except Exception as e:
                    print(f"Error loading result {filepath}: {e}")
        
        def view_result(self, event):
            selection = self.results_tree.selection()
            if not selection:
                return
            
            item = selection[0]
            filepath = self.results_tree.item(item, "tags")[0]
            
            import subprocess
            import platform
            
            if platform.system() == 'Darwin':
                subprocess.call(('open', filepath))
            elif platform.system() == 'Windows':
                os.startfile(filepath)
            else:
                subprocess.call(('xdg-open', filepath))
        
        def open_results_folder(self):
            import subprocess
            import platform
            
            folder = str(self.config.results_dir)
            
            if platform.system() == 'Darwin':
                subprocess.call(('open', folder))
            elif platform.system() == 'Windows':
                os.startfile(folder)
            else:
                subprocess.call(('xdg-open', folder))
        
        def run(self):
            self.root.mainloop()

# ==================== CLI APPLICATION ====================

def cli_main():
    """Enhanced CLI with pipeline selection"""
    print("="*70)
    print("🚀 FAMOUSIFY LOAD TESTER V2 - CLI Mode")
    print("="*70)
    print()
    
    config = Config()
    config.load_from_file()
    
    print(f"Target: {config.base_url}")
    print(f"Test Image: {config.test_image_url}")
    print(f"Cost per generation: €{config.cost_per_generation}")
    print()
    
    # Pipeline selection
    print("Select Pipeline:")
    print("1. USER (standard 3:4 portrait, 45-60s avg)")
    print("2. TEEINBLUE (1:1 square + bg removal + upscale, 90-180s avg)")
    print()
    
    pipeline_choice = input("Pipeline [1]: ").strip() or "1"
    pipeline = "teeinblue" if pipeline_choice == "2" else "user"
    
    # Test parameters
    try:
        num_requests = int(input("Total requests [10]: ") or "10")
        concurrent = int(input("Concurrent requests [10]: ") or "10")
    except ValueError:
        print("❌ Invalid input")
        return
    
    # Calculate costs
    base_cost = num_requests * config.cost_per_generation
    cost_with_margin = base_cost * config.cost_margin
    
    # Estimate time
    avg_time = 120 if pipeline == "teeinblue" else 50
    estimated_minutes = (num_requests * avg_time) / (concurrent * 60)
    
    print()
    print("="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Pipeline: {pipeline.upper()}")
    print(f"Requests: {num_requests} (concurrent: {concurrent})")
    print(f"Timeout: {config.timeout_teeinblue if pipeline == 'teeinblue' else config.timeout_user}s")
    print()
    print(f"💰 Cost Estimate:")
    print(f"   Base: €{base_cost:.2f}")
    print(f"   With {int((config.cost_margin-1)*100)}% margin: €{cost_with_margin:.2f}")
    print()
    print(f"⏱️  Time Estimate: ~{int(estimated_minutes)} minutes")
    print("="*70)
    print()
    
    confirm = input(f"Start test? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("Aborted")
        return
    
    # Run test
    tester = LoadTester(config)
    
    try:
        report = asyncio.run(tester.run_test(num_requests, concurrent, pipeline=pipeline))
        
        # Print summary with costs
        print()
        print("="*70)
        print("📊 TEST RESULTS")
        print("="*70)
        print(f"Pipeline: {pipeline.upper()}")
        print(f"Total Requests: {report['test_info']['total_requests']}")
        print(f"Successful: {report['summary']['successful']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']}%")
        print(f"Total Retries: {report['summary']['total_retries']}")
        print()
        
        # Cost breakdown
        print(f"💰 Cost Breakdown:")
        print(f"   Actual Cost: €{report['cost']['actual']}")
        print(f"   Estimated Cost: €{report['cost']['estimated']}")
        if report['cost']['saved'] > 0:
            print(f"   Saved (from failures): €{report['cost']['saved']}")
        print()
        
        if report['timing']:
            print(f"⏱️  Timing:")
            print(f"   Average Time: {report['timing']['avg_time']}s")
            print(f"   Min Time: {report['timing']['min_time']}s")
            print(f"   Max Time: {report['timing']['max_time']}s")
            print(f"   Median Time: {report['timing']['median_time']}s")
        print()
        print(f"🏥 Health Status: {report['health']}")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test stopped by user")
        tester.stop()

# ==================== ENTRY POINT ====================

if __name__ == "__main__":
    if "--cli" in sys.argv or not GUI_AVAILABLE:
        cli_main()
    else:
        app = LoadTesterGUI()
        app.run()

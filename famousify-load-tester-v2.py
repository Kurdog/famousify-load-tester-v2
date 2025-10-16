#!/usr/bin/env python3
"""
Famousify Load Tester v2 - COSTI REALI AGGIORNATI
Calcola costi dinamici in base ai modelli Replicate effettivi
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
import aiohttp
import asyncio
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional
import time
import io
from PIL import Image
import base64

# ============================================
# COSTI REALI REPLICATE (Ottobre 2025)
# ============================================
REPLICATE_COSTS = {
    'bg_removal': 0.00033,      # lucataco/remove-bg
    'flux_kontext_max': 0.08,   # black-forest-labs/flux-kontext-max
    'real_esrgan': 0.0020,      # nightmareai/real-esrgan
}

# Costi per pipeline
PIPELINE_COSTS = {
    'user': {
        'base': REPLICATE_COSTS['flux_kontext_max'],
        'components': ['AI Generation'],
        'description': '3:4 portrait, AI only'
    },
    'teeinblue': {
        'base': (
            REPLICATE_COSTS['flux_kontext_max'] + 
            REPLICATE_COSTS['bg_removal'] + 
            REPLICATE_COSTS['real_esrgan']
        ),
        'components': ['AI Generation', 'BG Removal', 'Upscaling'],
        'description': '1:1 square, full pipeline'
    }
}

SAFETY_MARGIN = 1.10  # 10% extra

@dataclass
class TestConfig:
    base_url: str
    admin_token: str
    total_requests: int
    concurrent: int
    pipeline: str  # 'user' or 'teeinblue'
    timeout_user: int = 300
    timeout_teeinblue: int = 600
    results_dir: Path = Path("load_test_results")
    images_dir: Path = Path("load_test_images")
    
    def __post_init__(self):
        self.results_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)

@dataclass
class TestResult:
    test_id: int
    pipeline: str
    style: str
    job_id: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None
    image_url: Optional[str] = None
    duration: float = 0.0
    status_code: int = 0
    submit_time: float = 0.0
    complete_time: float = 0.0
    
    def complete(self, success: bool, error: Optional[str] = None, image_url: Optional[str] = None):
        self.status = "completed" if success else "failed"
        self.error = error
        self.image_url = image_url
        self.complete_time = time.time()
        if self.submit_time > 0:
            self.duration = self.complete_time - self.submit_time


class LoadTester:
    def __init__(self, config: TestConfig, log_callback=None):
        self.config = config
        self.results: List[TestResult] = []
        self.log_callback = log_callback
        self.stopped = False
        
        # Generate 1024x1024 test image (keep as bytes)
        self.test_image_bytes = self.generate_test_image()
    
    def generate_test_image(self) -> bytes:
        """Generate a 1024x1024 test image as PNG bytes"""
        # Create 1024x1024 gradient image
        img = Image.new('RGB', (1024, 1024), color='white')
        
        # Add simple gradient for variety
        pixels = img.load()
        for i in range(1024):
            for j in range(1024):
                # Simple gradient from light gray to white
                gray_value = 200 + int(55 * (i / 1024))
                pixels[i, j] = (gray_value, gray_value, gray_value)
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def log(self, message: str, level: str = "info"):
        if self.log_callback:
            self.log_callback(message, level)
    
    def stop(self):
        self.stopped = True
        self.log("🛑 Stop signal received", "warning")
    
    async def submit_user_generation(self, session: aiohttp.ClientSession, result: TestResult):
        """Submit USER pipeline generation"""
        try:
            data = aiohttp.FormData()
            # Send as file with proper content type
            data.add_field('image', 
                          self.test_image_bytes,
                          filename='test.png',
                          content_type='image/png')
            data.add_field('style', result.style)
            
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
                result.job_id = response_data.get('job_id')
                self.log(f"[{result.test_id}] ✓ Submitted - Job: {result.job_id}")
                return True
                
        except Exception as e:
            self.log(f"[{result.test_id}] ✗ Submit failed: {e}", "error")
            return False
    
    async def submit_teeinblue_generation(self, session: aiohttp.ClientSession, result: TestResult):
        """Submit TEEINBLUE pipeline generation"""
        try:
            data = aiohttp.FormData()
            # Send as file with proper content type
            data.add_field('file',
                          self.test_image_bytes,
                          filename='test.png',
                          content_type='image/png')
            data.add_field('effect', result.style)
            
            self.log(f"[{result.test_id}] Submitting TEEINBLUE generation (style: {result.style})...")
            
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
                
                content_type = resp.headers.get('Content-Type', '')
                
                if 'application/json' in content_type:
                    response_data = await resp.json()
                    result.job_id = response_data.get('job_id')
                    self.log(f"[{result.test_id}] ✓ Submitted - Job: {result.job_id}")
                    return True
                else:
                    # Sync mode
                    image_bytes = await resp.read()
                    if len(image_bytes) > 1000:
                        result.job_id = f"teeinblue_sync_{result.test_id}"
                        image_path = self.config.images_dir / f"{result.job_id}.png"
                        image_path.write_bytes(image_bytes)
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
                async with session.get(
                    f"{self.config.base_url}/status/{result.job_id}",
                    timeout=10
                ) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(3)
                        continue
                    
                    data = await resp.json()
                    status = data.get('status', 'unknown')
                    
                    if status == 'completed':
                        result.complete(True, None, data.get('final_url'))
                        self.log(f"[{result.test_id}] ✓ Completed in {result.duration:.1f}s")
                        return
                    
                    elif status == 'failed':
                        result.complete(False, data.get('error', 'Unknown error'))
                        self.log(f"[{result.test_id}] ✗ Failed: {result.error}", "error")
                        return
                    
            except Exception as e:
                self.log(f"[{result.test_id}] Poll error: {e}", "warning")
            
            await asyncio.sleep(3)
        
        result.complete(False, f"Timeout after {timeout}s")
        self.log(f"[{result.test_id}] ✗ Timeout", "error")
    
    async def poll_teeinblue_status(self, session: aiohttp.ClientSession, result: TestResult):
        """Poll TEEINBLUE pipeline status"""
        start_poll = time.time()
        timeout = self.config.timeout_teeinblue
        
        while time.time() - start_poll < timeout:
            if self.stopped:
                result.complete(False, "Test stopped")
                return
            
            try:
                async with session.get(
                    f"{self.config.base_url}/api/teeinblue/status/{result.job_id}",
                    timeout=10
                ) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(5)
                        continue
                    
                    data = await resp.json()
                    status = data.get('status', 'unknown')
                    
                    if status == 'completed':
                        result.complete(True, None, data.get('final_url'))
                        self.log(f"[{result.test_id}] ✓ Completed in {result.duration:.1f}s")
                        return
                    
                    elif status == 'failed':
                        result.complete(False, data.get('error', 'Unknown error'))
                        self.log(f"[{result.test_id}] ✗ Failed: {result.error}", "error")
                        return
                    
            except Exception as e:
                self.log(f"[{result.test_id}] Poll error: {e}", "warning")
            
            await asyncio.sleep(5)
        
        result.complete(False, f"Timeout after {timeout}s")
        self.log(f"[{result.test_id}] ✗ Timeout", "error")
    
    async def run_single_test(self, session: aiohttp.ClientSession, test_id: int, style: str):
        """Run single generation test"""
        result = TestResult(
            test_id=test_id,
            pipeline=self.config.pipeline,
            style=style,
            submit_time=time.time()
        )
        self.results.append(result)
        
        # Submit based on pipeline
        if self.config.pipeline == 'user':
            success = await self.submit_user_generation(session, result)
            if success and result.job_id:
                await self.poll_user_status(session, result)
        else:  # teeinblue
            success = await self.submit_teeinblue_generation(session, result)
            if success and result.job_id and result.status == "pending":
                await self.poll_teeinblue_status(session, result)
        
        if not success:
            result.complete(False, "Submission failed")
    
    async def run_test(self):
        """Run complete load test"""
        self.log("="*80)
        self.log(f"🚀 STARTING LOAD TEST")
        self.log("="*80)
        self.log(f"Pipeline: {self.config.pipeline.upper()}")
        self.log(f"Total requests: {self.config.total_requests}")
        self.log(f"Concurrent: {self.config.concurrent}")
        self.log(f"Target: {self.config.base_url}")
        self.log(f"Test image: 1024x1024 PNG ({len(self.test_image_bytes)} bytes)")
        
        # Calculate cost
        cost_per_gen = PIPELINE_COSTS[self.config.pipeline]['base']
        total_cost = cost_per_gen * self.config.total_requests
        cost_with_margin = total_cost * SAFETY_MARGIN
        
        self.log(f"\n💰 COST ESTIMATE:")
        self.log(f"  Base cost: ${cost_per_gen:.5f} per generation")
        self.log(f"  Components: {', '.join(PIPELINE_COSTS[self.config.pipeline]['components'])}")
        self.log(f"  Total base: ${total_cost:.2f}")
        self.log(f"  With {int((SAFETY_MARGIN-1)*100)}% margin: ${cost_with_margin:.2f}")
        self.log("="*80)
        
        start_time = time.time()
        styles = ['kimono_vogue', 'green_vogue']
        
        async with aiohttp.ClientSession() as session:
            # Run in batches
            for batch_start in range(0, self.config.total_requests, self.config.concurrent):
                if self.stopped:
                    self.log("🛑 Test stopped by user", "warning")
                    break
                
                batch_end = min(batch_start + self.config.concurrent, self.config.total_requests)
                
                self.log(f"\n📦 Batch {batch_start//self.config.concurrent + 1}: Requests {batch_start+1}-{batch_end}")
                
                tasks = []
                for i in range(batch_start, batch_end):
                    style = styles[i % len(styles)]
                    tasks.append(self.run_single_test(session, i+1, style))
                
                await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        self.generate_report(total_time, cost_with_margin)
    
    def generate_report(self, total_time: float, estimated_cost: float):
        """Generate test report"""
        completed = [r for r in self.results if r.status == "completed"]
        failed = [r for r in self.results if r.status == "failed"]
        
        success_rate = (len(completed) / len(self.results) * 100) if self.results else 0
        avg_duration = sum(r.duration for r in completed) / len(completed) if completed else 0
        
        self.log("\n" + "="*80)
        self.log("📊 TEST RESULTS")
        self.log("="*80)
        self.log(f"Total requests: {len(self.results)}")
        self.log(f"Completed: {len(completed)} ({success_rate:.1f}%)")
        self.log(f"Failed: {len(failed)}")
        self.log(f"Avg duration: {avg_duration:.1f}s")
        self.log(f"Total time: {total_time:.1f}s")
        self.log(f"Estimated cost: ${estimated_cost:.2f}")
        self.log("="*80)
        
        # Save JSON report
        report_file = self.config.results_dir / f"load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            'config': asdict(self.config),
            'summary': {
                'total_requests': len(self.results),
                'completed': len(completed),
                'failed': len(failed),
                'success_rate': success_rate,
                'avg_duration': avg_duration,
                'total_time': total_time,
                'estimated_cost': estimated_cost
            },
            'results': [asdict(r) for r in self.results]
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.log(f"\n✅ Report saved: {report_file}")


class LoadTesterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Famousify Load Tester v2 - COSTI REALI")
        self.root.geometry("900x700")
        
        # Famousify PWA theme
        self.bg_color = "#1a1a2e"
        self.fg_color = "#ffffff"
        self.accent_color = "#00ff88"
        self.accent_secondary = "#00ccff"
        self.entry_bg = "#16213e"
        
        self.root.configure(bg=self.bg_color)
        
        self.tester = None
        self.running = False
        
        self.setup_ui()
        self.load_config()
    
    def setup_ui(self):
        # Notebook
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.entry_bg, foreground=self.fg_color, padding=[20, 10])
        style.map('TNotebook.Tab', background=[('selected', self.accent_color)], foreground=[('selected', self.bg_color)])
        
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tabs
        self.setup_config_tab(notebook)
        self.setup_run_tab(notebook)
        self.setup_results_tab(notebook)
        self.setup_help_tab(notebook)
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready | Made with ❤️ by KRD",
            bg=self.entry_bg,
            fg=self.fg_color,
            anchor='w',
            padx=10
        )
        self.status_bar.pack(side='bottom', fill='x')
    
    def setup_config_tab(self, notebook):
        frame = tk.Frame(notebook, bg=self.bg_color)
        notebook.add(frame, text="⚙️ Configuration")
        
        form = tk.Frame(frame, bg=self.bg_color)
        form.pack(pady=20, padx=20, fill='both', expand=True)
        
        row = 0
        
        # Base URL
        tk.Label(form, text="Base URL:", bg=self.bg_color, fg=self.fg_color).grid(row=row, column=0, sticky='w', pady=5)
        self.url_entry = tk.Entry(form, width=50, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color)
        self.url_entry.grid(row=row, column=1, pady=5, padx=10)
        self.url_entry.insert(0, "https://web-production-abb48.up.railway.app")
        
        row += 1
        
        # Admin Token
        tk.Label(form, text="Admin Token:", bg=self.bg_color, fg=self.fg_color).grid(row=row, column=0, sticky='w', pady=5)
        self.token_entry = tk.Entry(form, width=50, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color, show='*')
        self.token_entry.grid(row=row, column=1, pady=5, padx=10)
        
        row += 1
        
        # Buttons
        btn_frame = tk.Frame(form, bg=self.bg_color)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        tk.Button(
            btn_frame,
            text="💾 Save Configuration",
            command=self.save_config,
            bg=self.accent_color,
            fg=self.bg_color,
            padx=20,
            pady=10,
            relief='flat',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="🏥 Health Check",
            command=self.run_health_check,
            bg=self.accent_secondary,
            fg=self.bg_color,
            padx=20,
            pady=10,
            relief='flat',
            font=('Arial', 10, 'bold')
        ).pack(side='left', padx=5)
    
    def setup_run_tab(self, notebook):
        frame = tk.Frame(notebook, bg=self.bg_color)
        notebook.add(frame, text="▶️ Run Test")
        
        controls = tk.Frame(frame, bg=self.bg_color)
        controls.pack(pady=20, padx=20, fill='x')
        
        row = 0
        
        # Total Requests
        tk.Label(controls, text="Total Requests:", bg=self.bg_color, fg=self.fg_color).grid(row=row, column=0, sticky='w', pady=5)
        self.requests_entry = tk.Entry(controls, width=20, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color)
        self.requests_entry.grid(row=row, column=1, pady=5, padx=10, sticky='w')
        self.requests_entry.insert(0, "10")
        self.requests_entry.bind('<KeyRelease>', lambda e: self.update_cost_estimate())
        
        row += 1
        
        # Concurrent
        tk.Label(controls, text="Concurrent:", bg=self.bg_color, fg=self.fg_color).grid(row=row, column=0, sticky='w', pady=5)
        self.concurrent_entry = tk.Entry(controls, width=20, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color)
        self.concurrent_entry.grid(row=row, column=1, pady=5, padx=10, sticky='w')
        self.concurrent_entry.insert(0, "5")
        self.concurrent_entry.bind('<KeyRelease>', lambda e: self.update_cost_estimate())
        
        row += 1
        
        # Pipeline
        tk.Label(controls, text="Pipeline:", bg=self.bg_color, fg=self.fg_color).grid(row=row, column=0, sticky='w', pady=5)
        self.pipeline_var = tk.StringVar(value='user')
        
        pipeline_frame = tk.Frame(controls, bg=self.bg_color)
        pipeline_frame.grid(row=row, column=1, pady=5, padx=10, sticky='w')
        
        pipeline_combo = ttk.Combobox(
            pipeline_frame,
            textvariable=self.pipeline_var,
            values=['user', 'teeinblue'],
            state='readonly',
            width=18
        )
        pipeline_combo.pack(side='left')
        pipeline_combo.bind('<<ComboboxSelected>>', lambda e: self.update_cost_estimate())
        
        row += 1
        
        # Cost Estimate
        self.cost_label = tk.Label(
            controls,
            text="Cost estimate: calculating...",
            bg=self.bg_color,
            fg=self.accent_color,
            font=('Arial', 11, 'bold')
        )
        self.cost_label.grid(row=row, column=0, columnspan=2, pady=15, sticky='w')
        
        row += 1
        
        # Buttons
        btn_frame = tk.Frame(controls, bg=self.bg_color)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        self.start_btn = tk.Button(
            btn_frame,
            text="▶ Start Test",
            command=self.start_test,
            bg=self.accent_color,
            fg=self.bg_color,
            padx=30,
            pady=15,
            relief='flat',
            font=('Arial', 12, 'bold')
        )
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹ Stop Test",
            command=self.stop_test,
            bg='#dc3545',
            fg=self.fg_color,
            padx=30,
            pady=15,
            relief='flat',
            font=('Arial', 12, 'bold'),
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=5)
        
        # Log
        tk.Label(frame, text="📋 Test Log:", bg=self.bg_color, fg=self.fg_color, font=('Arial', 11, 'bold')).pack(anchor='w', padx=20, pady=(10,5))
        
        self.log_text = scrolledtext.ScrolledText(
            frame,
            height=20,
            bg=self.entry_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill='both', expand=True, padx=20, pady=(0,20))
        
        self.update_cost_estimate()
    
    def setup_results_tab(self, notebook):
        frame = tk.Frame(notebook, bg=self.bg_color)
        notebook.add(frame, text="📊 Results")
        
        tk.Label(
            frame,
            text="Test results will appear here after completion",
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(pady=50)
    
    def setup_help_tab(self, notebook):
        frame = tk.Frame(notebook, bg=self.bg_color)
        notebook.add(frame, text="❓ Help")
        
        help_text = scrolledtext.ScrolledText(
            frame,
            bg=self.entry_bg,
            fg=self.fg_color,
            font=('Arial', 10),
            wrap='word'
        )
        help_text.pack(fill='both', expand=True, padx=20, pady=20)
        
        help_content = """
🚀 FAMOUSIFY LOAD TESTER v2 - COSTI REALI

💰 CALCOLO COSTI DINAMICO

I costi sono calcolati in base ai modelli Replicate EFFETTIVI:

USER Pipeline ($0.08000/gen):
  • AI Generation (FLUX Kontext Max): $0.08000
  
TEEINBLUE Pipeline ($0.08233/gen):
  • AI Generation (FLUX Kontext Max): $0.08000
  • Background Removal (lucataco/remove-bg): $0.00033
  • Upscaling (Real-ESRGAN): $0.00200

🖼️ TEST IMAGE
Genera automaticamente un'immagine 1024x1024 PNG per ogni test.

⚙️ CONFIGURAZIONE

1. Imposta Base URL (default: Railway production)
2. Imposta Admin Token (opzionale)
3. Salva configurazione

▶️ ESECUZIONE TEST

1. Scegli Total Requests (quante generazioni)
2. Scegli Concurrent (quante in parallelo)
3. Scegli Pipeline (user o teeinblue)
4. Verifica costo stimato in tempo reale
5. Clicca "Start Test"

🎯 BEST PRACTICES

✓ Inizia con 3-5 requests per test
✓ USER pipeline è più veloce (45-60s)
✓ TEEINBLUE è più lenta (90-180s)
✓ Usa concurrent=5 per bilanciamento

Made with ❤️ by KRD
"""
        
        help_text.insert('1.0', help_content)
        help_text.config(state='disabled')
    
    def update_cost_estimate(self):
        """Update cost estimate in real-time"""
        try:
            requests = int(self.requests_entry.get())
            concurrent = int(self.concurrent_entry.get())
            pipeline = self.pipeline_var.get()
            
            cost_per_gen = PIPELINE_COSTS[pipeline]['base']
            total_cost = cost_per_gen * requests
            cost_with_margin = total_cost * SAFETY_MARGIN
            
            avg_time = 50 if pipeline == 'user' else 120
            estimated_seconds = (requests * avg_time) / concurrent
            estimated_minutes = estimated_seconds / 60
            
            cost_text = f"💰 Cost: ${cost_per_gen:.5f}/gen | Total: ${total_cost:.2f} → ${cost_with_margin:.2f} (with margin)\n"
            cost_text += f"⏱️ Time: ~{int(estimated_minutes)} minutes"
            
            self.cost_label.config(text=cost_text)
        except:
            self.cost_label.config(text="Enter valid numbers")
    
    def log_callback(self, message: str, level: str = "info"):
        """Log callback for tester"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
        self.root.update()
    
    def save_config(self):
        config = {
            'base_url': self.url_entry.get(),
            'admin_token': self.token_entry.get()
        }
        
        with open('load_tester_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        messagebox.showinfo("Success", "Configuration saved!")
        self.status_bar.config(text="✓ Configuration saved")
    
    def load_config(self):
        try:
            with open('load_tester_config.json', 'r') as f:
                config = json.load(f)
                self.url_entry.delete(0, 'end')
                self.url_entry.insert(0, config.get('base_url', ''))
                self.token_entry.delete(0, 'end')
                self.token_entry.insert(0, config.get('admin_token', ''))
        except FileNotFoundError:
            pass
    
    def run_health_check(self):
        """Run health check"""
        self.log_callback("Running health check...")
        messagebox.showinfo("Health Check", "Health check not implemented yet")
    
    def start_test(self):
        """Start load test"""
        if self.running:
            return
        
        try:
            requests = int(self.requests_entry.get())
            concurrent = int(self.concurrent_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid numbers")
            return
        
        config = TestConfig(
            base_url=self.url_entry.get(),
            admin_token=self.token_entry.get(),
            total_requests=requests,
            concurrent=concurrent,
            pipeline=self.pipeline_var.get()
        )
        
        self.tester = LoadTester(config, self.log_callback)
        self.running = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_bar.config(text="🚀 Test running...")
        
        self.log_text.delete('1.0', 'end')
        
        # Run async test
        asyncio.run(self.tester.run_test())
        
        self.running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_bar.config(text="✓ Test completed")
    
    def stop_test(self):
        """Stop test"""
        if self.tester:
            self.tester.stop()
            self.stop_btn.config(state='disabled')


if __name__ == "__main__":
    root = tk.Tk()
    app = LoadTesterGUI(root)
    root.mainloop()

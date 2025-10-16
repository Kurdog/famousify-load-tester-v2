#!/usr/bin/env python3
"""Famousify Load Tester v2 - Complete with GUI"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional
import time

# Costi reali Replicate
REPLICATE_COSTS = {'bg_removal': 0.00033, 'flux_kontext_max': 0.08, 'real_esrgan': 0.0020}
PIPELINE_COSTS = {'user': {'base': 0.08, 'components': ['AI Generation']}, 'teeinblue': {'base': 0.08233, 'components': ['AI Gen', 'BG Removal', 'Upscale']}}
SAFETY_MARGIN = 1.10
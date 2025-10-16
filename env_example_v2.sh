# ================================
# Famousify Load Tester V2 Config
# ================================
#
# Copy this file to .env and fill in your values
# All settings can also be configured via GUI

# Base URL of your Famousify instance
FAMOUSIFY_BASE_URL=https://web-production-abb48.up.railway.app

# Admin authentication token
FAMOUSIFY_ADMIN_TOKEN=famousify-admin-2025

# Test image URL (must be publicly accessible)
# Default: sample dog image from Unsplash
FAMOUSIFY_TEST_IMAGE_URL=https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=800

# Maximum time to wait for generation completion (seconds)
FAMOUSIFY_TIMEOUT=180

# How often to poll job status (seconds)
FAMOUSIFY_POLL_INTERVAL=5

# ================================
# Advanced Options (Optional)
# ================================

# Custom styles to test (comma-separated)
# FAMOUSIFY_STYLES=kimono_vogue,pop_art,urban_graffiti

# Results directory
# FAMOUSIFY_RESULTS_DIR=results

# Enable debug logging
# FAMOUSIFY_DEBUG=false

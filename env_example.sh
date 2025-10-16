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

# Maximum time to wait for USER pipeline completion (seconds)
# Recommended: 180s (3 minutes)
FAMOUSIFY_TIMEOUT_USER=180

# Maximum time to wait for TEEINBLUE pipeline completion (seconds)
# Recommended: 300s (5 minutes) - includes bg removal + upscale
FAMOUSIFY_TIMEOUT_TEEINBLUE=300

# How often to poll job status (seconds)
FAMOUSIFY_POLL_INTERVAL=5

# Maximum retry attempts on failure
FAMOUSIFY_MAX_RETRIES=3

# Delay between retry attempts (seconds)
FAMOUSIFY_RETRY_DELAY=10

# ================================
# Advanced Options (Optional)
# ================================

# Custom styles to test (comma-separated)
# FAMOUSIFY_STYLES=kimono_vogue,pop_art,urban_graffiti

# Results directory
# FAMOUSIFY_RESULTS_DIR=results

# Enable debug logging
# FAMOUSIFY_DEBUG=false

# Gunicorn configuration file
import os
import multiprocessing

# Server socket
bind = "0.0.0.0:{}".format(os.environ.get("PORT", 5001))
backlog = 2048

# Worker processes
workers = 1  # Use only 1 worker to save memory
worker_class = "sync"
worker_connections = 1000
timeout = 300  # 5 minutes timeout
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "ai-jobfit-analyzer"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (not needed for Render)
keyfile = None
certfile = None

keyfile = None
certfile = None

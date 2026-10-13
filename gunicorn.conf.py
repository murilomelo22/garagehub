"""Servidor WSGI para hospedagens que fornecem PORT e um proxy HTTPS."""

import os

bind = f"0.0.0.0:{int(os.getenv('PORT', '10000'))}"
# Um único processo para a versão com SQLite e disco persistente.
workers = 1
worker_class = "gthread"
threads = 4
timeout = 120
accesslog = "-"
errorlog = "-"
forwarded_allow_ips = "*" if os.getenv("GARAGEHUB_TRUST_PROXY") == "1" else "127.0.0.1,::1"

#!/bin/sh
set -eu

cat > /usr/share/nginx/html/config.js <<EOF
window.AGENT_API_BASE_URL="${AGENT_API_BASE_URL:-}";
EOF

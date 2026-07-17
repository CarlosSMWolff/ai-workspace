#!/usr/bin/env bash
set -euo pipefail

# This script sets up a "default-deny" firewall INSIDE the container:
# nothing can go out unless it is explicitly allowed below.
# It needs root privileges (run with sudo) and the container needs
# the NET_ADMIN / NET_RAW capabilities added in devcontainer.json.

# --- 1. Reset any existing rules, start from a clean state ---
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# --- 2. Default policy: drop everything, unless explicitly allowed ---
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# --- 3. Always allow local loopback traffic (127.0.0.1) ---
# The container itself, and tools running inside it, talk to each other this way.
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# --- 4. Allow DNS lookups (needed to resolve any domain name at all) ---
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
iptables -A INPUT -p udp --sport 53 -j ACCEPT
iptables -A INPUT -p tcp --sport 53 -j ACCEPT

# --- 5. Allow replies to connections we already started ---
# (e.g. the response to a request we sent out is allowed back in)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# --- 6. The actual allowlist: only these domains get network access ---
# Add or remove lines here as your workflow changes.
ALLOWED_DOMAINS=(
  # Python packages
  "pypi.org"
  "files.pythonhosted.org"
  # GitHub (cloning repos, releases, raw files)
  "github.com"
  "api.github.com"
  "raw.githubusercontent.com"
  "codeload.github.com"
  "objects.githubusercontent.com"
  # arXiv (papers)
  "arxiv.org"
  "export.arxiv.org"
  # Claude / Anthropic itself (needed for Claude Code to work at all)
  "api.anthropic.com"
  "console.anthropic.com"
  "claude.ai"
)

# ipset is a tool that lets iptables match against a whole GROUP of IP
# addresses efficiently, instead of writing one rule per address.
ipset create allowed-domains hash:ip 2>/dev/null || ipset flush allowed-domains

for domain in "${ALLOWED_DOMAINS[@]}"; do
  # Look up every IP address this domain currently resolves to,
  # and add each one to the allowlist group.
  ips=$(dig +short "$domain" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' || true)
  for ip in $ips; do
    ipset add allowed-domains "$ip" 2>/dev/null || true
  done
done

# --- 7. Allow outbound HTTPS (443) and HTTP (80) only to the allowlist ---
iptables -A OUTPUT -p tcp -m set --match-set allowed-domains dst --dport 443 -j ACCEPT
iptables -A OUTPUT -p tcp -m set --match-set allowed-domains dst --dport 80 -j ACCEPT

echo "Firewall applied. Allowed domains:"
printf '  - %s\n' "${ALLOWED_DOMAINS[@]}"
echo "Everything else is blocked by default."

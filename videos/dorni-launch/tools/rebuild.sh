#!/usr/bin/env bash
# Regenerate frames, assemble index, inject transitions, vendor GSAP locally.
set -euo pipefail
cd "$(dirname "$0")/.."
P=/root/.claude/plugins/cache/hyperframes/hyperframes/0.8.86/skills
L=$P/hyperframes/scripts/plugin-cli.mjs; K=$P/product-launch-video/scripts
python3 tools/build-frames.py >/dev/null
node $L --script $K/assemble-index.mjs --storyboard ./STORYBOARD.md --hyperframes . | grep -E "total|anomal" || true
node $L --script $K/transitions.mjs inject --storyboard ./STORYBOARD.md --hyperframes . >/dev/null
node $L --script $K/transitions.mjs verify --storyboard ./STORYBOARD.md --index ./index.html | tail -1
sed -i 's#<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"[^>]*></script>#<script src="assets/gsap.min.js"></script>#' index.html

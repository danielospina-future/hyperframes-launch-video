#!/usr/bin/env bash
# Regenerate frames, cut the music bed, assemble index, inject transitions, place + carve audio,
# vendor GSAP locally. Needs ffmpeg and `npm i` (for @hyperframes/core, used by the carve).
set -euo pipefail
cd "$(dirname "$0")/.."
# Newest installed plugin version (the marketplace moves; 0.8.86 built the silent cut).
P=$(ls -d /root/.claude/plugins/cache/hyperframes/hyperframes/*/skills | sort -V | tail -1)
L=$P/hyperframes/scripts/plugin-cli.mjs; K=$P/product-launch-video/scripts
python3 tools/build-frames.py >/dev/null
node tools/mix.mjs prep
node $L --script $K/assemble-index.mjs --storyboard ./STORYBOARD.md --hyperframes . | grep -E "total|anomal|bgm" || true
node $L --script $K/transitions.mjs inject --storyboard ./STORYBOARD.md --hyperframes . >/dev/null
node tools/mix.mjs patch
# Voiceover carve on the bed (hyperframes-audio): dynamic, default strength 0.8.
node $P/hyperframes-audio/scripts/carve.mjs --comp index.html --bed el-bgm | grep -E "^(bed|carve|level)" | sed 's/^/  /'
node tools/mix.mjs release
node $L --script $K/transitions.mjs verify --storyboard ./STORYBOARD.md --index ./index.html | tail -1
sed -i 's#<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"[^>]*></script>#<script src="assets/gsap.min.js"></script>#' index.html

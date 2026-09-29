# Handoff: add HeyGen voiceover + music

State: 40s silent film rendered (renders/video.mp4), all frames animated. Next session has
HEYGEN_API_KEY + *.heygen.com / *.heygen.ai network access.

## Container setup (ephemeral, redo each session)
- `apt-get install -y ffmpeg libnss3-tools`
- Trust proxy CA for Chromium: `mkdir -p ~/.pki/nssdb && certutil -d sql:$HOME/.pki/nssdb -N --empty-password && certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n ccr -i /root/.ccr/agent-proxy-ca.crt`
- Reinstall plugin: `claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes`
- Rebuild: `tools/rebuild.sh` (frames -> assemble -> transitions -> local gsap). jsdelivr is blocked, gsap is vendored.

## Draft narration (pending user approval), one line per frame
01 "There's a jellyfish that can live forever."
02 "When it grows old, it simply turns young again... and starts over."
03 "Its name is dohrnii. Ours is Dorni."
04 "AI has eaten software. But the world of atoms is still waiting."
05 "Now we have the tools to make brands last forever."
06 "More functional. Healthier. Longer human lives."
07 "D2C health brands, enhanced by Dorni OS."
08 (no VO: music + sting)
09 "Acquiring the brands that will help billions live longer, healthier lives."

## Open decisions
- Voice gender/tone (shortlist 2-3 HeyGen Starfish voices).
- Music mood (proposed: deep ambient, underwater synths building to a hopeful swell).

## Steps
Write SCRIPT.md, set STORYBOARD `music:` + per-frame `voiceover`, then product-launch-video Step 3.1:
audio.mjs (HeyGen provider) -> sync-durations -> tools/rebuild.sh (frame durations may change;
frame JS timings are absolute seconds, rescale if a frame grows a lot) -> check -> render.

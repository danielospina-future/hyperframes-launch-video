# Handoff: generate HeyGen voiceover + music, then re-render

State (2026-09-29): 40s silent film rendered (renders/video.mp4). Narration **approved as drafted**
and locked in SCRIPT.md. Storyboard switched from silent to VO + music. Only the HeyGen calls are
left, and they were blocked last session.

## Blocker from last session
The environment's network policy allows `*.heygen.ai` but not `api.heygen.com`, and the HeyGen
engine hardcodes `https://api.heygen.com/v3` (media-use/audio/scripts/lib/heygen.mjs).
`api.heygen.ai` only 301s to heygen.com. Add `api.heygen.com` (or `*.heygen.com`) to the
environment's allowed domains, then verify: `npx hyperframes auth status` must show the API check
passing. If audio downloads then fail, check `curl -sS "$HTTPS_PROXY/__agentproxy/status"` for the
host the audio/music files are served from and allow it too.

## User decisions (locked)
- Narration: SCRIPT.md, exactly as drafted. Frame 8 has no VO.
- Voice: warm male, documentary style (HeyGen Starfish).
- Music: "deep ambient, underwater synths building to a hopeful swell" (STORYBOARD `music:`).

## Container setup (ephemeral, redo each session)
- `apt-get install -y ffmpeg libnss3-tools`
- Trust proxy CA for Chromium: `mkdir -p ~/.pki/nssdb && certutil -d sql:$HOME/.pki/nssdb -N --empty-password && certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n ccr -i /root/.ccr/agent-proxy-ca.crt`
- Reinstall plugin: `claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes`
- `tools/rebuild.sh` now picks the newest installed plugin version (was pinned to 0.8.86; 0.8.92
  reproduces the silent cut byte-for-byte).

## Steps
```bash
cd videos/dorni-launch
P=$(ls -d /root/.claude/plugins/cache/hyperframes/hyperframes/*/skills | sort -V | tail -1)

# 1. Voice: list Starfish voices, shortlist 2-3 warm male documentary voices, audition Lines 2+3
node $P/media-use/audio/scripts/heygen-tts.mjs --list
node $P/media-use/audio/scripts/heygen-tts.mjs "Its name is dohrnii. Ours is Dorni." -o /tmp/a.wav --voice <id>

# 2. Narration + music (HeyGen TTS with word timings; BGM retrieved from HeyGen's library)
node $P/product-launch-video/scripts/audio.mjs --script ./SCRIPT.md --storyboard ./STORYBOARD.md \
  --hyperframes . --out ./audio_meta.json --provider heygen --voice <id>

# 3. Fit durations. Do NOT run the skill's sync-durations: it sets duration = raw voice length,
#    which shrinks frames and cuts the absolute-timed animation (frame 9's swim-away).
node tools/fit-durations.mjs        # duration = max(visual_duration, voice + 0.5s)

# 4. Rebuild (build-frames.py now reads durations from STORYBOARD.md; assemble picks up audio_meta.json)
bash tools/rebuild.sh
```
Then: `npx hyperframes lint`, `npx hyperframes check`, snapshot at cuts, review, render
(`npx hyperframes render --skill=product-launch-video --quality high --output renders/video.mp4`).

## Things to listen/check for
- Pronunciation: "dohrnii" (DOR-nee-eye), "Dorni" (DOR-nee; the pun needs them to sound related),
  "D2C" (D-to-C). If HeyGen mangles one, respell only the spoken text in SCRIPT.md (e.g.
  "Dor-nee-eye", "Dornee", "D-to-C") and regenerate that line.
- Frame growth: fit-durations warns at >15%. Frame 2 (12 words + a pause in 4.5s) is the likely
  one; re-time its reveals in build-frames.py to the word timestamps in audio_meta.json so the
  on-screen line lands with the spoken word.
- Frame 4 on-screen reads "is yet to be disrupted." while the approved VO says "is still waiting."
  Left as is; ask the user whether to match the on-screen line to the VO.
- Music: assemble sets the bed to 0.12 under VO. The swell should peak on the frame 8 lockup
  (no VO, ~28-32s). Per SKILL Step 5, compare the track's opening with later sections and trim with
  ffmpeg so the build lands there; short fade-in, longer fade-out, no silence at the tail. Consider
  lifting the bed for frame 8 and the last ~2s of frame 9.
- Captions: skip. On-screen type already carries every line.

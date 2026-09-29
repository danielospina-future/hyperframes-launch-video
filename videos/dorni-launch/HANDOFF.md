# Handoff: Dorni launch film (narrated)

State (2026-09-29): 43.5s film with HeyGen voiceover + music, rendered to renders/video.mp4.
Previous silent cut was 40s; frames grew to fit the voice (tools/fit-durations.mjs).

## Locked decisions
- Narration: SCRIPT.md, approved as drafted. Frame 8 (lockup) has no VO.
- Voice: HeyGen "Resonant Docu-Pro" `aiXCV9D0yx4ptgZ3piiy` (warm male, documentary). Picked from a
  12-voice audition on Lines 2+3 by measured pitch/pace/pronunciation length, not by ear.
  Alternates: Samuel-Narration `6e51a203c3e74398ae8046f3c320abf6`, Harry-Narration `6648fd92bcba41df809a01712faf9a4a`.
- Music: HeyGen library track 3164530a ("deep atmospheric bass drone, rising triumphant cinematic
  swell"), assets/bgm/library-3164530a.flac. The pipeline's default top hit had disco undertones.
- Frame 4 on-screen line matches the VO: "is still waiting."

## How the audio is built
- `audio.mjs` (skill) → assets/voice/NN.wav + audio_meta.json (word timings).
- HeyGen ignores "..."; pauses are `<break time="0.7s"/>` in SCRIPT.md. "D2C" is spelled "D-to-C"
  for TTS (HeyGen stumbled on it). On-screen text is unaffected.
- `tools/fit-durations.mjs`: duration = max(visual_duration, voice_offset + voice + 0.5s). Use it
  instead of the skill's sync-durations, which would shrink frames to raw voice length.
- `voice_offset:` (storyboard, frame 9 = 3s) delays a frame's voice; frame 9's VO is read while
  the jellyfish writes the same line.
- `tools/mix.mjs prep` cuts assets/bgm/bed.mp3 from the library track: from 7s (swell lands on the
  frame 8 lockup at ~31s), -8 dB, 1.5s fade in, 3s fade out, fitted to the film length.
  Offset and level are baked into the file because the carve reads the file from sample 0 and
  ignores data-volume / data-media-start.
- `tools/mix.mjs patch` groups the narration as `voiceover`, applies voice offsets, checks length.
- Voiceover carve (hyperframes-audio carve.mjs, strength 0.8, dynamic) on el-bgm against the group.
- `tools/mix.mjs release` then opens the carve's level duck for frames with no VO: it ramps to
  0 dB over 30.45-31.0s (the crossfade into the lockup) and stays open until frame 9's voice. The
  carve's slow release otherwise held the bed ~10 dB down through the lockup (measured -24 LUFS).
- Measured on the render: -14.3 LUFS integrated, -1.6 dBFS peak; narration ~-15 to -17 LUFS;
  lockup swell -19 → -16 LUFS.
- Frame reveals in build-frames.py are timed to the word timestamps (frames 2, 3, 4, 5, 6, 7).

## Rebuild / render
```bash
cd videos/dorni-launch
apt-get install -y ffmpeg libnss3-tools          # per container
mkdir -p ~/.pki/nssdb && certutil -d sql:$HOME/.pki/nssdb -N --empty-password && \
  certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n ccr -i /root/.ccr/agent-proxy-ca.crt   # Chromium trusts proxy
claude plugin marketplace add heygen-com/hyperframes && claude plugin install hyperframes@hyperframes
npm i                                            # @hyperframes/core for the carve
bash tools/rebuild.sh                            # frames, bed, assemble, transitions, mix, carve
npx hyperframes lint && npx hyperframes check
npx hyperframes render --skill=product-launch-video --quality high --output renders/video.mp4
```
To change the voice: edit the voice id in SCRIPT.md's header, rerun `audio.mjs ... --voice <id>`
(see product-launch-video SKILL Step 3.1), then `node tools/fit-durations.mjs` and the rebuild.
To move the swell: change `offset` / `gainDb` in tools/mix.mjs and rebuild.

## Known
- `check` flags 5 contrast warnings on frame 7's small "a dorni brand" tags (blue on navy), sampled
  mid-crossfade. Unchanged from the approved silent cut's design.
- Captions skipped: on-screen type already carries every line.

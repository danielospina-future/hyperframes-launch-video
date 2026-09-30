# Handoff: Dorni launch film (narrated)

State (2026-09-30): 43.5s film with HeyGen voiceover + upbeat startup-tech music, rendered to renders/video.mp4.
Previous silent cut was 40s; frames grew to fit the voice (tools/fit-durations.mjs).

## Locked decisions
- Narration: SCRIPT.md, approved as drafted. Frame 8 (lockup) has no VO.
- Voice: HeyGen "Resonant Docu-Pro" `aiXCV9D0yx4ptgZ3piiy` (warm male, documentary). Picked from a
  12-voice audition on Lines 2+3 by measured pitch/pace/pronunciation length, not by ear.
  Alternates: Samuel-Narration `6e51a203c3e74398ae8046f3c320abf6`, Harry-Narration `6648fd92bcba41df809a01712faf9a4a`.
- Music: HeyGen library track 5530e1c0 ("modern optimistic tech, clean synths, rhythmic and
  confident"), assets/bgm/library-5530e1c0.flac, ~120 BPM, major key. Replaced the first bed (deep
  ambient drone 3164530a), which the user found spooky. Picked from 10 "upbeat startup tech" library
  hits by measured tempo, key (two "upbeat" hits were minor), brightness and section structure.
- Frame 4 on-screen line matches the VO: "is still waiting."

## How the audio is built
- `audio.mjs` (skill) → assets/voice/NN.wav + audio_meta.json (word timings).
- HeyGen ignores "..."; pauses are `<break time="0.7s"/>` in SCRIPT.md. "D2C" is spelled "D-to-C"
  for TTS (HeyGen stumbled on it). On-screen text is unaffected.
- `tools/fit-durations.mjs`: duration = max(visual_duration, voice_offset + voice + 0.5s). Use it
  instead of the skill's sync-durations, which would shrink frames to raw voice length.
- `voice_offset:` (storyboard, frame 9 = 3s) delays a frame's voice; frame 9's VO is read while
  the jellyfish writes the same line.
- `tools/mix.mjs prep` cuts assets/bgm/bed.mp3 from the library track: from 1s, -4 dB, 1s fade in,
  3s fade out, fitted to the film length. The 1s offset lands the track's beat drop (16.0s) on the
  end of "AI has eaten software." (film 15.0s) and its post-break re-entry (32.0s) on the lockup (31.0s).
  Offset and level are baked into the file because the carve reads the file from sample 0 and
  ignores data-volume / data-media-start.
- `tools/mix.mjs patch` groups the narration as `voiceover`, applies voice offsets, checks length.
- Voiceover carve (hyperframes-audio carve.mjs, strength 0.5, dynamic) on el-bgm against the group.
  The default 0.8 held the bed ~20 dB under the voice (-35 LUFS), which hid the groove.
- `tools/mix.mjs release` then opens the carve's level duck for frames with no VO: it ramps to
  0 dB over 30.45-31.0s (the crossfade into the lockup) and stays open until frame 9's voice. The
  carve's slow release otherwise held the bed ~10 dB down through the lockup (measured -24 LUFS).
- Measured (bed-only render with voices muted): bed under narration -32 LUFS before the drop, -28
  after it (13-17 dB under the ~-15 LUFS voice); lockup -16 LUFS.
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
To change the music: swap `source` / `offset` / `gainDb` in tools/mix.mjs and rebuild. Measure the bed
under narration by rendering once with the voice `data-volume` set to 0.

## Known
- `check` flags 5 contrast warnings on frame 7's small "a dorni brand" tags (blue on navy), sampled
  mid-crossfade. Unchanged from the approved silent cut's design.
- Captions skipped: on-screen type already carries every line.

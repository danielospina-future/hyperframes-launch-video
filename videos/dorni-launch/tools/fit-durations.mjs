#!/usr/bin/env node
// Fit STORYBOARD.md frame durations to the HeyGen voice clips, without shrinking the visuals.
//
// The skill's `audio.mjs sync-durations` sets duration = raw voice length. This film was cut
// silent first with absolute-second animation timings, so that would shrink frames and cut
// animation (frame 9's 8s swim-away would drop to ~5s). Instead:
//   duration = max(visual_duration, voice_offset + voice + TAIL)
// `visual_duration` is written once (the original silent-cut length), so re-runs are idempotent.
// `voice_offset` (optional, per frame) delays that frame's voice; tools/mix.mjs applies it.
//
//   node tools/fit-durations.mjs [--audio-meta ./audio_meta.json] [--tail 0.5]
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const arg = (name, def) => {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : def;
};
const TAIL = Number(arg("tail", "0.5"));
const meta = JSON.parse(readFileSync(arg("audio-meta", join(ROOT, "audio_meta.json")), "utf8"));
const voice = new Map((meta.voices ?? []).map((v) => [v.frame, v.duration_s]));

const sbPath = join(ROOT, "STORYBOARD.md");
const lines = readFileSync(sbPath, "utf8").split("\n");

// Pass 1: per frame, where its duration line is and what it already declares.
const frames = new Map();
let cur = null;
lines.forEach((line, i) => {
  const h = line.match(/^## Frame (\d+)/);
  if (h) frames.set((cur = Number(h[1])), { durLine: -1, visual: null, offset: 0 });
  if (cur == null) return;
  const f = frames.get(cur);
  let m;
  if ((m = line.match(/^- duration:\s*([0-9.]+)s?/))) Object.assign(f, { durLine: i, cur: Number(m[1]) });
  if ((m = line.match(/^- visual_duration:\s*([0-9.]+)s?/))) f.visual = Number(m[1]);
  if ((m = line.match(/^- voice_offset:\s*([0-9.]+)s?/))) f.offset = Number(m[1]);
});

// Pass 2: rewrite bottom-up so inserted visual_duration lines don't shift later indexes.
let total = 0;
const report = [];
for (const [n, f] of [...frames].sort((a, b) => b[1].durLine - a[1].durLine)) {
  if (f.durLine < 0) continue;
  const base = f.visual ?? f.cur;
  const v = voice.get(n);
  const fit = v ? Math.max(base, Math.ceil((f.offset + v + TAIL) * 10) / 10) : base;
  lines[f.durLine] = `- duration: ${fit}s`;
  if (f.visual == null) lines.splice(f.durLine + 1, 0, `- visual_duration: ${base}s`);
  total += fit;
  const grow = fit / base - 1;
  report.unshift(
    `frame ${n}: visual ${base}s · voice ${v ?? "-"}s${f.offset ? ` @+${f.offset}s` : ""} → ${fit}s` +
      (grow > 0.15 ? `  ⚠ +${Math.round(grow * 100)}%: re-time the frame's reveals to the words` : ""),
  );
}
writeFileSync(sbPath, lines.join("\n"));
console.log(report.join("\n"));
console.log(`total: ${Math.round(total * 10) / 10}s`);

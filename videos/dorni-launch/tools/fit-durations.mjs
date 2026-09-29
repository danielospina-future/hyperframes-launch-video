#!/usr/bin/env node
// Fit STORYBOARD.md frame durations to the HeyGen voice clips, without shrinking the visuals.
//
// The skill's `audio.mjs sync-durations` sets duration = raw voice length. This film was cut
// silent first with absolute-second animation timings, so that would shrink frames and cut
// animation (frame 9's 8s swim-away would drop to ~5s). Instead:
//   duration = max(visual_duration, voice + TAIL)
// `visual_duration` is written once (the original silent-cut length), so re-runs are idempotent.
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
let frame = null;
let visual = null;
let total = 0;
for (let i = 0; i < lines.length; i++) {
  const h = lines[i].match(/^## Frame (\d+)/);
  if (h) {
    frame = Number(h[1]);
    visual = null;
    continue;
  }
  const vd = lines[i].match(/^- visual_duration:\s*([0-9.]+)s?/);
  if (vd) visual = Number(vd[1]);
  const d = lines[i].match(/^- duration:\s*([0-9.]+)s?/);
  if (!d || frame == null) continue;
  const cur = Number(d[1]);
  // visual_duration sits right after duration once written; peek so re-runs use it.
  const next = lines[i + 1]?.match(/^- visual_duration:\s*([0-9.]+)s?/);
  const base = visual ?? (next ? Number(next[1]) : cur);
  const v = voice.get(frame);
  const fit = v ? Math.max(base, Math.ceil((v + TAIL) * 10) / 10) : base;
  lines[i] = `- duration: ${fit}s`;
  if (!next) lines.splice(i + 1, 0, `- visual_duration: ${base}s`);
  total += fit;
  const grow = fit / base - 1;
  console.log(
    `frame ${frame}: visual ${base}s · voice ${v ?? "-"}s → ${fit}s` +
      (grow > 0.15 ? `  ⚠ +${Math.round(grow * 100)}%: consider rescaling frame JS timings` : ""),
  );
}
writeFileSync(sbPath, lines.join("\n"));
console.log(`sum of frame durations: ${total.toFixed(1)}s (before transition overlaps)`);

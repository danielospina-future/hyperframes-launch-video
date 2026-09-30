#!/usr/bin/env node
// Music bed + voice placement for the Dorni film. Passes around assemble-index + the carve:
//
//   node tools/mix.mjs prep    before assembly: cut the bed from the library track so its
//                              post-break re-entry lands on the frame 8 lockup, fitted to the film's length,
//                              and point audio_meta.json at it (volume 1: level is in the file).
//   node tools/mix.mjs patch   after assembly: group the narration (so the carve can name the
//                              group), apply per-frame `voice_offset`, verify the timeline.
//   node tools/mix.mjs release after the carve: open the carve's level duck fully for frames
//                              with no voiceover (frame 8 lockup). The carve releases slowly by
//                              design, which is right between sentences but held the bed ~10 dB
//                              down through the lockup, where the music should come forward.
//
// The bed's offset and level are baked into the file on purpose: the voiceover carve
// (hyperframes-audio carve.mjs) decodes the bed from sample 0 and ignores data-volume and
// data-media-start, so anything done in attributes would be invisible to its analysis.
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

// HeyGen music library 5530e1c0: "modern optimistic tech, clean synths, rhythmic and
// confident" (53s, ~120 BPM, major). Light groove to 16.0s, full beat 16.0-29.75s, a two-bar
// break 29.75-31.75s, full beat again from 32.0s. Starting 1s in lands the beat drop on the end
// of "AI has eaten software." (film 15.0s) and the post-break re-entry on the lockup (31.0s).
const BED = {
  source: "assets/bgm/library-5530e1c0.flac",
  out: "assets/bgm/bed.mp3",
  offset: 1,
  gainDb: -4, // full groove -11.8 LUFS → ≈ -16 at the lockup, against ≈ -15 LUFS narration
  fadeIn: 1,
  fadeOut: 3,
};
const VOICE_GROUP = "voiceover";
const BED_GROUP = "music";

const r3 = (n) => Math.round(n * 1000) / 1000;
const die = (m) => {
  console.error(`✗ mix: ${m}`);
  process.exit(1);
};

// STORYBOARD frames: number, src stem (= assembled comp id), duration, voice_offset, silent.
function storyboard() {
  const frames = [];
  let f = null;
  for (const line of readFileSync(join(ROOT, "STORYBOARD.md"), "utf8").split("\n")) {
    const h = line.match(/^## Frame (\d+)/);
    if (h) frames.push((f = { n: Number(h[1]), offset: 0 }));
    if (!f) continue;
    let m;
    if ((m = line.match(/^- duration:\s*([0-9.]+)s?/))) f.duration = Number(m[1]);
    if ((m = line.match(/^- voice_offset:\s*([0-9.]+)s?/))) f.offset = Number(m[1]);
    if (/^- voiceover:\s*""\s*$/.test(line)) f.silent = true;
    if ((m = line.match(/^- src:\s*compositions\/frames\/(\S+)\.html/))) f.id = m[1];
  }
  return frames;
}
const filmLength = () => r3(storyboard().reduce((a, f) => a + (f.duration ?? 0), 0));

function prep() {
  const total = filmLength();
  const fadeOutAt = r3(total - BED.fadeOut);
  execFileSync("ffmpeg", [
    "-v", "error", "-y",
    "-ss", String(BED.offset), "-t", String(total), "-i", join(ROOT, BED.source),
    "-af", `volume=${BED.gainDb}dB,afade=t=in:st=0:d=${BED.fadeIn},afade=t=out:st=${fadeOutAt}:d=${BED.fadeOut}`,
    "-ar", "44100", "-b:a", "192k", join(ROOT, BED.out),
  ]);
  const metaPath = join(ROOT, "audio_meta.json");
  const meta = JSON.parse(readFileSync(metaPath, "utf8"));
  meta.bgm = {
    path: BED.out,
    volume: 1,
    query: `library 5530e1c0 from ${BED.offset}s, ${BED.gainDb} dB, fades ${BED.fadeIn}/${BED.fadeOut}s`,
    duration_s: total,
  };
  writeFileSync(metaPath, JSON.stringify(meta, null, 2));
  console.log(`✓ mix prep: ${BED.out} ${total}s (from ${BED.offset}s, ${BED.gainDb} dB)`);
}

// Set (or replace) one attribute on the opening tag that carries id="<id>".
function setAttr(html, id, name, value) {
  const re = new RegExp(`(<(audio|video)\\b[^>]*\\bid="${id}"[^>]*?)(\\s*>)`);
  const m = html.match(re);
  if (!m) die(`no <audio>/<video> with id="${id}" in index.html`);
  let tag = m[1];
  const attr = new RegExp(`\\s${name}="[^"]*"`);
  tag = attr.test(tag) ? tag.replace(attr, ` ${name}="${value}"`) : `${tag}\n        ${name}="${value}"`;
  return html.replace(m[0], tag + m[3]);
}
const getAttr = (html, id, name) =>
  html.match(new RegExp(`<(?:audio|video)\\b[^>]*\\bid="${id}"[^>]*\\b${name}="([^"]*)"`))?.[1];

function patch() {
  const path = join(ROOT, "index.html");
  let html = readFileSync(path, "utf8");
  const total = Number(html.match(/id="root"[^>]*?data-duration="([0-9.]+)"/s)?.[1]);
  if (total !== filmLength()) die(`index.html is ${total}s but STORYBOARD sums to ${filmLength()}s`);

  const report = [];
  for (const f of storyboard()) {
    const id = `el-${f.id}-voice`;
    if (!html.includes(`id="${id}"`)) continue;
    html = setAttr(html, id, "data-audio-group", VOICE_GROUP);
    if (f.offset) {
      const start = Number(getAttr(html, id, "data-start"));
      const dur = Number(getAttr(html, id, "data-duration"));
      html = setAttr(html, id, "data-start", r3(start + f.offset));
      html = setAttr(html, id, "data-duration", r3(dur - f.offset));
      report.push(`${id} +${f.offset}s`);
    }
  }
  if (!html.includes('id="el-bgm"')) die("no el-bgm in index.html (run `mix.mjs prep` before assembly)");
  if (getAttr(html, "el-bgm", "src") !== BED.out) die(`el-bgm src is not ${BED.out}`);
  html = setAttr(html, "el-bgm", "data-audio-group", BED_GROUP);
  writeFileSync(path, html);
  console.log(`✓ mix patch: voices grouped as "${VOICE_GROUP}"${report.length ? `, offsets: ${report.join(", ")}` : ""}`);
}

// Attribute JSON the way carve.mjs writes it: double-quoted, `&` and `"` escaped.
const unesc = (v) => v.replace(/&quot;/g, '"').replace(/&amp;/g, "&");
const esc = (v) => v.replace(/&/g, "&amp;").replace(/"/g, "&quot;");

function release() {
  const path = join(ROOT, "index.html");
  let html = readFileSync(path, "utf8");
  const chain = JSON.parse(unesc(getAttr(html, "el-bgm", "data-fx-chain") ?? die("el-bgm has no carve chain")));
  const duck = chain.nodes.find((n) => n.fromCarve && n.type === "gain") ?? die("no carve gain stage on el-bgm");
  const auto = JSON.parse(unesc(getAttr(html, "el-bgm", "data-automation")));
  const lane = auto.lanes.find((l) => l.target === `fx.${duck.id}.gain`) ?? die("no carve gain lane");
  if (Number(getAttr(html, "el-bgm", "data-start")) !== 0) die("el-bgm must start at 0 (lane time = film time)");

  // Voice windows on the film clock: [clip start, last word end].
  const meta = JSON.parse(readFileSync(join(ROOT, "audio_meta.json"), "utf8"));
  const frames = storyboard();
  const voices = meta.voices.map((v) => {
    const id = `el-${frames.find((f) => f.n === v.frame).id}-voice`;
    const start = Number(getAttr(html, id, "data-start"));
    return { start, end: r3(start + v.words.at(-1).end) };
  });
  const valueAt = (t) => {
    const pts = lane.points;
    const i = pts.findIndex((p) => p.t > t);
    if (i === 0) return pts[0].v;
    if (i < 0) return pts.at(-1).v;
    const a = pts[i - 1], b = pts[i];
    return a.v + ((b.v - a.v) * (t - a.t)) / (b.t - a.t);
  };

  const opened = [];
  for (const f of frames.filter((f) => f.silent)) {
    const start = Number(getAttr(html, `el-${f.id}`, "data-start") ?? html.match(new RegExp(`id="el-${f.id}"[^>]*?data-start="([0-9.]+)"`, "s"))?.[1]);
    const prevEnd = Math.max(...voices.filter((v) => v.end <= start).map((v) => v.end));
    const nextStart = Math.min(...voices.filter((v) => v.start >= start).map((v) => v.start), Infinity);
    const from = r3(prevEnd + 0.2); // let the last word's tail clear before the bed rises
    const keep = lane.points.filter((p) => p.t < from || p.t >= nextStart);
    const ramp = [{ t: from, v: r3(valueAt(from)) }, { t: start, v: 0 }];
    if (Number.isFinite(nextStart)) ramp.push({ t: r3(nextStart), v: 0 });
    lane.points = [...keep, ...ramp].sort((a, b) => a.t - b.t);
    opened.push(`frame ${f.n} @${start}s (ramp ${from}→${start}s)`);
  }
  html = setAttr(html, "el-bgm", "data-automation", esc(JSON.stringify(auto)));
  writeFileSync(path, html);
  console.log(`✓ mix release: duck open for ${opened.join(", ") || "no silent frames"}`);
}

const mode = process.argv[2];
if (mode === "prep") prep();
else if (mode === "patch") patch();
else if (mode === "release") release();
else die("usage: node tools/mix.mjs prep|patch|release");

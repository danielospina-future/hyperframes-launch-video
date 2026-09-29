#!/usr/bin/env python3
"""Generate compositions/frames/*.html for the Dorni launch film.

Every frame shares one jellyfish rig (traced from assets/dorni-jellyfish-sting.mp4)
driven by a single clock tween, so its swim, pulse and tentacle wiggle are a pure
function of time (seek-safe, deterministic).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "compositions" / "frames"
OUT.mkdir(parents=True, exist_ok=True)

NAVY, SURF, BLUE, CREAM, MIST, HAIR = "#05070F", "#0B1A5C", "#1A4DFF", "#EEF1FF", "#8FA6FF", "#16225E"

FONTS = """
@font-face{font-family:'Inter';font-weight:400;font-style:normal;font-display:block;src:url("assets/fonts/inter-latin-400-normal.woff2") format('woff2');}
@font-face{font-family:'Inter';font-weight:500;font-style:normal;font-display:block;src:url("assets/fonts/inter-latin-500-normal.woff2") format('woff2');}
@font-face{font-family:'IBM Plex Mono';font-weight:400;font-style:normal;font-display:block;src:url("assets/fonts/ibm-plex-mono-latin-400-normal.woff2") format('woff2');}
@font-face{font-family:'IBM Plex Mono';font-weight:500;font-style:normal;font-display:block;src:url("assets/fonts/ibm-plex-mono-latin-500-normal.woff2") format('woff2');}
"""


def jelly(jid, color=BLUE):
    return f"""<div class="jf" id="{jid}"><svg viewBox="0 0 260 310" width="260" height="310">
  <path class="jf-dome" fill="{color}" d="M0 155 L0 130 A130 130 0 0 1 260 130 L260 155 Z"/>
  <rect class="jf-t" x="75" y="175" width="16" height="100" rx="8" fill="{color}"/>
  <rect class="jf-t" x="122" y="175" width="16" height="135" rx="8" fill="{color}"/>
  <rect class="jf-t" x="169" y="175" width="16" height="100" rx="8" fill="{color}"/>
</svg></div>"""


# rig(jid) returns pose(x, y, rot, scale, t, tent=1, alpha=1): (x, y) = dome-base centre.
JELLY_JS = """
function rig(jid){
  const el=document.getElementById(jid), dome=el.querySelector('.jf-dome'), ts=el.querySelectorAll('.jf-t');
  gsap.set(dome,{transformOrigin:'50% 100%'}); ts.forEach(t=>gsap.set(t,{transformOrigin:'50% 0%'}));
  return function(x,y,rot,s,t,tent,alpha){
    tent=(tent===undefined)?1:tent; alpha=(alpha===undefined)?1:alpha;
    const p=Math.sin(t*Math.PI*2/0.9);
    gsap.set(el,{x:x-130,y:y-155,rotation:rot,scale:s,opacity:alpha});
    gsap.set(dome,{scaleX:1+0.06*p,scaleY:1-0.07*p});
    ts.forEach((r,i)=>gsap.set(r,{scaleY:Math.max(0,tent*(1+0.12*Math.sin(t*Math.PI*2/0.9-0.8-i*0.35))),skewX:7*Math.sin(t*Math.PI*2/1.1+i)}));
  };
}
function clamp(v,a,b){return Math.max(a,Math.min(b,v));}
function seg(t,a,b){return clamp((t-a)/(b-a),0,1);}
function easeOut(u){return 1-Math.pow(1-u,3);}
function easeInOut(u){return u<0.5?4*u*u*u:1-Math.pow(-2*u+2,3)/2;}
function lerp(a,b,u){return a+(b-a)*u;}
function heading(dx,dy){return Math.atan2(dy,dx)*180/Math.PI+90;}
// Pure-math path sampler (M/L/C only): no DOM measurement, so it is seek-order independent.
function mkPath(d){
  const tk=d.match(/[MLC]|-?[0-9.]+/g); const pts=[]; let i=0,cx=0,cy=0,cmd='M';
  while(i<tk.length){ if(/[MLC]/.test(tk[i])){cmd=tk[i++];}
    if(cmd==='M'||cmd==='L'){cx=+tk[i++];cy=+tk[i++];pts.push([cx,cy]);}
    else { const x1=+tk[i++],y1=+tk[i++],x2=+tk[i++],y2=+tk[i++],x3=+tk[i++],y3=+tk[i++];
      for(let k=1;k<=60;k++){const t=k/60,m=1-t;pts.push([m*m*m*cx+3*m*m*t*x1+3*m*t*t*x2+t*t*t*x3,m*m*m*cy+3*m*m*t*y1+3*m*t*t*y2+t*t*t*y3]);}
      cx=x3;cy=y3; } }
  const cum=[0]; for(let k=1;k<pts.length;k++){cum.push(cum[k-1]+Math.hypot(pts[k][0]-pts[k-1][0],pts[k][1]-pts[k-1][1]));}
  return {pts,cum,L:cum[cum.length-1]};
}
function at(P,s){s=clamp(s,0,P.L);let k=1;while(k<P.cum.length-1&&P.cum[k]<s)k++;const a=P.pts[k-1],b=P.pts[k],seg=(P.cum[k]-P.cum[k-1])||1,f=(s-P.cum[k-1])/seg;return [a[0]+(b[0]-a[0])*f,a[1]+(b[1]-a[1])*f];}
function onPath(P,u){const s=clamp(u,0,1)*P.L,a=at(P,s),b=at(P,Math.min(P.L,s+6)),c=(b[0]===a[0]&&b[1]===a[1])?at(P,Math.max(0,s-6)):null;
  const dx=c?a[0]-c[0]:b[0]-a[0],dy=c?a[1]-c[1]:b[1]-a[1];return {x:a[0],y:a[1],rot:heading(dx,dy)};}
"""


def frame(fid, dur, body, css, js, rootx=""):
    return f"""<template>
<style>
{FONTS}
#root{{position:relative;width:1920px;height:1080px;overflow:hidden;font-family:'Inter',sans-serif;color:{CREAM};}}
#f{fid}-bg{{position:absolute;inset:0;background:{NAVY};}}
#root .jf{{position:absolute;left:0;top:0;width:260px;height:310px;transform-origin:130px 155px;}}
#root .jf svg{{display:block;overflow:visible;}}
#root .mono{{font-family:'IBM Plex Mono',monospace;font-weight:500;text-transform:uppercase;letter-spacing:0.14em;}}
{css}
</style>
<div id="root" data-composition-id="{fid}" data-width="1920" data-height="1080">
{rootx}
  <div id="f{fid}-bg" class="clip" data-start="0" data-duration="{dur}" data-track-index="0"></div>
  <div id="f{fid}-stage" class="clip" data-start="0" data-duration="{dur}" data-track-index="1" style="position:absolute;inset:0;">
{body}
  </div>
</div>
<script>
(function(){{
{JELLY_JS}
const D={dur};
const tl=gsap.timeline({{paused:true}});
{js}
tl.to({{}},{{duration:D}},0);
window.__timelines["{fid}"]=tl;
}})();
</script>
</template>
"""


def clock(render="render"):
    return f"const clock={{t:0}};tl.to(clock,{{t:D,duration:D,ease:'none',onUpdate:function(){{{render}(clock.t);}}}},0);{render}(0);"


frames = {}

# ---------- 01 · The immortal jellyfish (4s) ----------
snow = "\n".join(
    f'<div class="f01-snow" id="f01-s{i}" style="left:{(i*397)%1880+20}px;top:{(i*241)%1000+40}px;width:{2+(i%3)}px;height:{2+(i%3)}px;opacity:{0.15+0.1*(i%4)};"></div>'
    for i in range(46))
frames["01-immortal"] = (4, f"""
{snow}
<div id="f01-copy">
  <div class="mono" id="f01-kicker">Turritopsis dohrnii</div>
  <div class="f01-line"><span id="f01-l1">there's a jellyfish</span></div>
  <div class="f01-line"><span id="f01-l2">that can live <em>forever.</em></span></div>
</div>
{jelly("f01-jf")}
""", f"""
#root .f01-snow{{position:absolute;border-radius:50%;background:{MIST};}}
#f01-copy{{position:absolute;left:150px;top:300px;width:1150px;}}
#f01-kicker{{color:{BLUE};font-size:26px;margin-bottom:34px;}}
#root .f01-line{{overflow:hidden;padding-bottom:10px;}}
#root .f01-line span{{display:inline-block;font-size:108px;font-weight:500;letter-spacing:-0.035em;line-height:1.02;}}
#root .f01-line em{{font-style:normal;color:{BLUE};}}
""", f"""
tl.fromTo('#f01-kicker',{{autoAlpha:0,y:16}},{{autoAlpha:1,y:0,duration:0.5,ease:'power3.out'}},0.3);
tl.fromTo('#f01-l1',{{yPercent:110}},{{yPercent:0,duration:0.8,ease:'expo.out'}},0.7);
tl.fromTo('#f01-l2',{{yPercent:110}},{{yPercent:0,duration:0.8,ease:'expo.out'}},1.4);
for(let i=0;i<46;i++){{tl.fromTo('#f01-s'+i,{{y:0}},{{y:-(40+(i%5)*25),duration:D,ease:'none'}},0);}}
const pose=rig('f01-jf');
function render(t){{const u=easeOut(seg(t,0,2.4));pose(1500,lerp(1250,470,u)+Math.sin(t*2.2)*14,Math.sin(t*1.3)*5,1.25,t);}}
{clock()}
""")

# ---------- 02 · It turns young again (4.5s) ----------
frames["02-rewind"] = (4.5, f"""
<div id="f02-copy">
  <div class="f02-line"><span id="f02-l1">when it grows old,</span></div>
  <div class="f02-line"><span id="f02-l2">it turns <em>young again.</em></span></div>
  <div class="f02-line f02-small"><span id="f02-l3">and starts over.</span></div>
  <div id="f02-meter">
    <div class="mono f02-lab"><span>young</span><span id="f02-rw">&#9664;&#9664; rewind</span><span>old</span></div>
    <div id="f02-track"><div id="f02-fill"></div></div>
  </div>
</div>
{jelly("f02-jf")}
""", f"""
#f02-copy{{position:absolute;left:150px;top:230px;width:1050px;}}
#root .f02-line{{overflow:hidden;padding-bottom:8px;}}
#root .f02-line span{{display:inline-block;font-size:96px;font-weight:500;letter-spacing:-0.035em;line-height:1.05;}}
#root .f02-line em{{font-style:normal;color:{BLUE};}}
#root .f02-small span{{font-size:64px;color:{MIST};}}
#f02-meter{{margin-top:70px;width:760px;}}
#root .f02-lab{{display:flex;justify-content:space-between;font-size:20px;color:{MIST};margin-bottom:14px;}}
#f02-rw{{color:{BLUE};}}
#f02-track{{height:6px;background:{HAIR};}}
#f02-fill{{height:6px;width:760px;background:{BLUE};transform-origin:left center;}}
""", f"""
tl.fromTo('#f02-l1',{{yPercent:110}},{{yPercent:0,duration:0.7,ease:'expo.out'}},0.2);
tl.fromTo('#f02-meter',{{autoAlpha:0}},{{autoAlpha:1,duration:0.4}},0.3);
tl.fromTo('#f02-fill',{{scaleX:0.02}},{{scaleX:1,duration:1.3,ease:'power1.in'}},0.4);
tl.fromTo('#f02-rw',{{autoAlpha:0}},{{autoAlpha:1,duration:0.15}},1.8);
tl.to('#f02-fill',{{scaleX:0.02,duration:0.9,ease:'power3.inOut'}},1.85);
tl.fromTo('#f02-l2',{{yPercent:110}},{{yPercent:0,duration:0.7,ease:'expo.out'}},1.9);
tl.fromTo('#f02-l3',{{yPercent:110}},{{yPercent:0,duration:0.7,ease:'expo.out'}},3.1);
const pose=rig('f02-jf'), jd=document.querySelector('#f02-jf .jf-dome'), jts=document.querySelectorAll('#f02-jf .jf-t');
function render(t){{
  // age up (0.4-1.7): grows, droops, fades toward mist; rewind (1.85-2.75): shrinks to a speck; rebirth (2.8-3.5)
  let s, tent=1, drift=Math.sin(t*2)*10, rot=Math.sin(t*1.4)*4, col;
  const age=seg(t,0.4,1.7), back=easeInOut(seg(t,1.85,2.75)), born=easeOut(seg(t,2.8,3.5));
  if(t<1.85){{s=lerp(0.9,1.45,age);tent=lerp(1,1.5,age);rot+=age*14;col=age;}}
  else if(t<2.8){{s=lerp(1.45,0.12,back);tent=lerp(1.5,0.2,back);col=1-back;}}
  else{{s=lerp(0.12,1.0,born);tent=lerp(0.2,1,born);col=0;}}
  const c=gsap.utils.interpolate('{BLUE}','{MIST}',col*0.8);
  gsap.set(jd,{{fill:c}});jts.forEach(r=>gsap.set(r,{{fill:c}}));
  pose(1480,500+drift,rot,s,t,tent);
}}
{clock()}
""")

# ---------- 03 · dohrnii -> dorni (3s) ----------
letters = "dohrnii"
# Inter 500 advances (units/2048) at 410px with -0.045em tracking; laid out absolutely so the
# surviving letters can close ranks onto the real wordmark's footprint (x 510-1382, baseline 690).
ADV = {"d": 1266, "o": 1237, "h": 1232, "r": 792, "n": 1232, "i": 516}
adv = [ADV[c] / 2048 * 410 - 0.045 * 410 for c in letters]
x0 = 960 - sum(adv) / 2
start = [x0 + sum(adv[:i]) for i in range(len(letters))]
keep = [0, 1, 3, 4, 5]
fx0 = 946 - sum(adv[i] for i in keep) / 2
final = {k: fx0 + sum(adv[j] for j in keep[:n]) for n, k in enumerate(keep)}
spans = "".join(f'<span class="f03-ch" id="f03-c{i}" style="left:{start[i]:.1f}px;">{ch}</span>' for i, ch in enumerate(letters))
close_js = "\n".join(f"tl.fromTo('#f03-c{k}',{{x:0}},{{x:{final[k]-start[k]:.1f},duration:0.5,ease:'power3.inOut'}},0.95);" for k in keep)
frames["03-name"] = (3, f"""
<div id="f03-kick" class="mono">the name</div>
<div id="f03-word" data-layout-allow-overlap="true">{spans}</div>
<img id="f03-mark" src="assets/dorni-wordmark.png" alt="dorni">
<div id="f03-dot"></div>
{jelly("f03-jf")}
""", f"""
#f03-kick{{position:absolute;left:0;right:0;top:230px;text-align:center;font-size:24px;color:{MIST};}}
#f03-word{{position:absolute;left:0;top:336px;width:1920px;height:420px;font-size:410px;font-weight:500;letter-spacing:-0.045em;line-height:1;white-space:nowrap;}}
#root .f03-ch{{position:absolute;top:0;display:block;}}
#f03-mark{{position:absolute;left:500px;top:376px;width:892px;height:326px;}}
#f03-dot{{position:absolute;left:1309px;top:364px;width:92px;height:92px;border-radius:50%;background:{BLUE};}}
""", f"""
tl.fromTo('#f03-kick',{{autoAlpha:0}},{{autoAlpha:1,duration:0.4}},0.1);
tl.fromTo('#f03-word',{{autoAlpha:0,scale:0.96}},{{autoAlpha:1,scale:1,duration:0.5,ease:'power3.out'}},0.05);
tl.fromTo('#f03-c2',{{y:0,autoAlpha:1,rotation:0}},{{y:420,autoAlpha:0,rotation:-18,duration:0.6,ease:'power2.in'}},0.75);
tl.fromTo('#f03-c6',{{y:0,autoAlpha:1,rotation:0}},{{y:420,autoAlpha:0,rotation:16,duration:0.6,ease:'power2.in'}},0.85);
{close_js}
tl.to('#f03-word',{{autoAlpha:0,filter:'blur(10px)',duration:0.4,ease:'power2.in'}},1.45);
tl.fromTo('#f03-mark',{{autoAlpha:0,filter:'blur(10px)'}},{{autoAlpha:1,filter:'blur(0px)',duration:0.4,ease:'power2.out'}},1.5);
tl.fromTo('#f03-dot',{{scale:0}},{{scale:1,duration:0.35,ease:'back.out(2)'}},2.3);
const pose=rig('f03-jf');
function render(t){{
  // jelly swims in from top-right and dives into the dot of the i (1355,410)
  const u=easeInOut(seg(t,1.3,2.35));
  const x=lerp(1900,1355,u), y=lerp(80,410,u)-Math.sin(u*Math.PI)*60;
  const s=lerp(0.7,0.35,u);
  pose(x,y,lerp(220,180,u),s,t,1,t<2.3?1:0);
}}
{clock()}
""")

# ---------- 04 · AI ate software (4.5s) ----------
sw = "software"
swspans = "".join(f'<span class="f04-ch" data-layout-allow-overlap="true" id="f04-c{i}">{ch}</span>' for i, ch in enumerate(sw))
eat_js = "\n".join(
    f"tl.fromTo('#f04-c{i}',{{x:0,y:0,scale:1,autoAlpha:1}},{{x:{-120-40*(7-i)},y:{(-1)**i*70},scale:0.1,autoAlpha:0,duration:0.45,ease:'power3.in'}},{1.25+(7-i)*0.12:.2f});"
    for i in range(len(sw)))
frames["04-atoms"] = (4.5, f"""
<div id="f04-pre"><span id="f04-p1">ai has eaten</span></div>
<div id="f04-sw" data-layout-allow-overlap="true">{swspans}</div>
<div id="f04-post" data-layout-allow-overlap="true">
  <div class="f04-line"><span id="f04-a1">the world of <em>atoms</em></span></div>
  <div class="mono" id="f04-a2">is yet to be disrupted.</div>
</div>
{jelly("f04-jf")}
""", f"""
#f04-pre{{position:absolute;left:150px;top:250px;overflow:hidden;}}
#f04-pre span{{display:inline-block;font-size:72px;font-weight:500;color:{MIST};letter-spacing:-0.03em;}}
#f04-sw{{position:absolute;left:140px;top:350px;font-size:250px;font-weight:500;letter-spacing:-0.05em;line-height:1;white-space:nowrap;}}
#root .f04-ch{{display:inline-block;}}
#f04-post{{position:absolute;left:150px;top:420px;}}
#root .f04-line{{overflow:hidden;padding-bottom:12px;}}
#root .f04-line span{{display:inline-block;font-size:150px;font-weight:500;letter-spacing:-0.045em;line-height:1.02;}}
#root .f04-line em{{font-style:normal;color:{BLUE};}}
#f04-a2{{font-size:34px;color:{CREAM};margin-top:36px;}}
""", f"""
tl.fromTo('#f04-p1',{{yPercent:110}},{{yPercent:0,duration:0.6,ease:'expo.out'}},0.1);
tl.fromTo('#f04-sw',{{autoAlpha:0,y:30}},{{autoAlpha:1,y:0,duration:0.6,ease:'power3.out'}},0.35);
{eat_js}
tl.to('#f04-pre',{{autoAlpha:0,duration:0.3}},2.2);
tl.fromTo('#f04-a1',{{yPercent:110,autoAlpha:0}},{{yPercent:0,autoAlpha:1,duration:0.8,ease:'expo.out'}},2.45);
tl.fromTo('#f04-a2',{{autoAlpha:0,y:14}},{{autoAlpha:1,y:0,duration:0.5,ease:'power3.out'}},3.2);
const pose=rig('f04-jf');
function render(t){{
  // swims right->left through the word, mouth-first, gobbling letters
  const u=seg(t,1.0,2.6);
  const x=lerp(2150,-250,u), y=470+Math.sin(u*Math.PI*3)*40;
  pose(x,y,-90+Math.sin(u*Math.PI*3)*12,0.8,t,1,1);
}}
{clock()}
""")

# ---------- 05 · Brands that last forever (3.5s, blue register) ----------
frames["05-forever"] = (3.5, f"""
<svg id="f05-inf" width="1920" height="1080" viewBox="0 0 1920 1080">
  <path id="f05-path" d="M960 320 C1080 180 1320 180 1320 320 C1320 460 1080 460 960 320 C840 180 600 180 600 320 C600 460 840 460 960 320"
        fill="none" stroke="{CREAM}" stroke-opacity="0.35" stroke-width="4" stroke-linecap="round"/>
</svg>
<div id="f05-copy">
  <div class="f05-line f05-small"><span id="f05-l1">now we have the tools</span></div>
  <div class="f05-line"><span id="f05-l2">to make brands last forever.</span></div>
</div>
{jelly("f05-jf", CREAM)}
""", f"""
#f05-forever-bg{{background:{BLUE} !important;}}
#f05-inf{{position:absolute;left:0;top:0;}}
#f05-copy{{position:absolute;left:0;right:0;top:560px;text-align:center;}}
#root .f05-line{{overflow:hidden;padding-bottom:10px;}}
#root .f05-line span{{display:inline-block;font-size:112px;font-weight:500;letter-spacing:-0.04em;line-height:1.05;}}
#root .f05-small span{{font-size:56px;color:rgba(238,241,255,0.75);}}
""", f"""
tl.fromTo('#f05-l1',{{yPercent:110}},{{yPercent:0,duration:0.7,ease:'expo.out'}},0.35);
tl.fromTo('#f05-l2',{{yPercent:110}},{{yPercent:0,duration:0.8,ease:'expo.out'}},1.0);
const path=document.getElementById('f05-path'), P=mkPath(path.getAttribute('d')), L=P.L;
gsap.set(path,{{strokeDasharray:L}});
const pose=rig('f05-jf');
function render(t){{
  const u=seg(t,0,3.3); const p=onPath(P,u);
  gsap.set(path,{{strokeDashoffset:L*(1-u)}});
  pose(p.x,p.y,p.rot,0.42,t,1,1);
}}
{clock()}
""")

# ---------- 06 · Longer human lives (3.5s) ----------
ecg = "M150 860 L760 860 L800 860 L830 800 L860 920 L890 760 L920 880 L950 860 L1770 860"
frames["06-lives"] = (3.5, f"""
<div id="f06-copy">
  <div class="f06-line"><span id="f06-l1">more functional.</span></div>
  <div class="f06-line"><span id="f06-l2">healthier.</span></div>
  <div class="f06-line"><span id="f06-l3"><em>longer human lives.</em></span></div>
</div>
<svg id="f06-ecg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <path id="f06-path" d="{ecg}" fill="none" stroke="{BLUE}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>
</svg>
{jelly("f06-jf")}
""", f"""
#f06-copy{{position:absolute;left:150px;top:170px;}}
#root .f06-line{{overflow:hidden;padding-bottom:6px;}}
#root .f06-line span{{display:inline-block;font-size:150px;font-weight:500;letter-spacing:-0.045em;line-height:1.0;}}
#root .f06-line em{{font-style:normal;color:{BLUE};}}
#f06-ecg{{position:absolute;left:0;top:0;}}
""", f"""
tl.fromTo('#f06-l1',{{yPercent:110}},{{yPercent:0,duration:0.7,ease:'expo.out'}},0.2);
tl.fromTo('#f06-l2',{{yPercent:110}},{{yPercent:0,duration:0.7,ease:'expo.out'}},0.9);
tl.fromTo('#f06-l3',{{yPercent:110}},{{yPercent:0,duration:0.7,ease:'expo.out'}},1.6);
tl.to('#f06-l1',{{opacity:0.45,duration:0.5}},1.6);
tl.to('#f06-l2',{{opacity:0.7,duration:0.5}},1.6);
const path=document.getElementById('f06-path'), P=mkPath(path.getAttribute('d')), L=P.L;
gsap.set(path,{{strokeDasharray:L}});
const pose=rig('f06-jf');
function render(t){{
  const u=seg(t,0.2,3.3); const p=onPath(P,u);
  gsap.set(path,{{strokeDashoffset:L*(1-u)}});
  pose(p.x,p.y-8,p.rot,0.32,t,1,u>0.995?0:1);
}}
{clock()}
""")

# ---------- 07 · Enhanced by Dorni OS (4.5s) ----------
cats = ["metabolic health", "functional nutrition", "sleep &amp; recovery", "movement &amp; mobility"]
cards = "\n".join(
    f'<div class="f07-card" id="f07-k{i}" style="left:{150+i*410}px;"><div class="mono f07-n">0{i+1}</div>'
    f'<div class="f07-name">{c}</div><div class="mono f07-tag" id="f07-tag{i}">a dorni brand</div>'
    f'<div class="f07-on" id="f07-on{i}"></div></div>' for i, c in enumerate(cats))
conns = "\n".join(
    f'<path id="f07-w{i}" d="M960 470 C960 560 {345+i*410} 540 {345+i*410} 620" fill="none" stroke="{BLUE}" stroke-width="4" stroke-linecap="round"/>'
    for i in range(4))
frames["07-os"] = (4.5, f"""
<div id="f07-head"><span id="f07-h1">d2c health brands,</span> <span id="f07-h2">enhanced by <em>dorni os.</em></span></div>
<div class="mono" id="f07-label">dorni os</div>
<svg id="f07-wires" width="1920" height="1080" viewBox="0 0 1920 1080">{conns}</svg>
{cards}
{jelly("f07-jf")}
""", f"""
#f07-head{{position:absolute;left:150px;right:150px;top:95px;font-size:72px;font-weight:500;letter-spacing:-0.035em;white-space:nowrap;}}
#f07-head span{{display:inline-block;}}
#f07-head em{{font-style:normal;color:{BLUE};}}
#f07-label{{position:absolute;left:1060px;top:318px;font-size:24px;color:{BLUE};}}
#f07-wires{{position:absolute;left:0;top:0;}}
#root .f07-card{{position:absolute;top:620px;width:390px;height:260px;border:1px solid {HAIR};background:{NAVY};padding:28px 30px;box-sizing:border-box;overflow:hidden;}}
#root .f07-on{{position:absolute;inset:0;background:{SURF};border-top:3px solid {BLUE};}}
#root .f07-n{{position:relative;z-index:1;font-size:20px;color:{MIST};}}
#root .f07-name{{position:relative;z-index:1;font-size:42px;font-weight:500;letter-spacing:-0.025em;margin-top:70px;line-height:1.05;}}
#root .f07-tag{{position:relative;z-index:1;font-size:16px;color:{MIST};margin-top:18px;}}
""", f"""
tl.fromTo('#f07-h1',{{autoAlpha:0,y:24}},{{autoAlpha:1,y:0,duration:0.6,ease:'power3.out'}},0.2);
for(let i=0;i<4;i++){{
  tl.fromTo('#f07-k'+i,{{autoAlpha:0,y:40}},{{autoAlpha:1,y:0,duration:0.5,ease:'power3.out'}},0.55+i*0.12);
  tl.fromTo('#f07-on'+i,{{autoAlpha:0}},{{autoAlpha:1,duration:0.3}},1.95+i*0.28);
  tl.fromTo('#f07-tag'+i,{{color:'{MIST}'}},{{color:'{BLUE}',duration:0.3}},1.95+i*0.28);
}}
tl.fromTo('#f07-label',{{autoAlpha:0,x:-10}},{{autoAlpha:1,x:0,duration:0.4}},1.1);
tl.fromTo('#f07-h2',{{autoAlpha:0,y:24}},{{autoAlpha:1,y:0,duration:0.6,ease:'power3.out'}},2.7);
const wires=[0,1,2,3].map(i=>document.getElementById('f07-w'+i)), WL=wires.map(w=>mkPath(w.getAttribute('d')).L);
wires.forEach((w,i)=>gsap.set(w,{{strokeDasharray:WL[i],strokeDashoffset:WL[i]}}));
const pose=rig('f07-jf');
function render(t){{
  const u=easeOut(seg(t,0,1.0));
  pose(960,lerp(-200,330,u)+Math.sin(t*2)*6,Math.sin(t*1.5)*3,0.55,t,1,1);
  wires.forEach((w,i)=>{{const v=easeInOut(seg(t,1.3+i*0.28,1.95+i*0.28));gsap.set(w,{{strokeDashoffset:WL[i]*(1-v)}});}});
}}
{clock()}
""")

# ---------- 08 · Lockup: user's sting from 6.0s (4.5s) ----------
STING = """
<video id="f08-sting" src="assets/dorni-jellyfish-sting.mp4" data-frame-video="approved"
  data-start="0" data-duration="4.5" data-track-index="2" data-media-start="6"
  data-frame-video-x="0" data-frame-video-y="0" data-frame-video-width="1920" data-frame-video-height="1080"
  data-frame-video-fit="cover" muted playsinline></video>
"""
frames["08-lockup"] = (4.5, "", "", "", STING)

# ---------- 09 · Swim away, writing the line (8s, final frame) ----------
PHRASE = "acquiring the brands that will help billions live longer, healthier lives."
swim = "M1355 410 C1330 300 1250 220 1100 205 C850 180 500 170 330 300 C230 420 225 620 255 790"
wave = "M255 790 C515 760 765 820 1025 790 C1285 760 1535 820 1795 790"
frames["09-swim-away"] = (8, f"""
<div id="f09-circle"></div>
<img id="f09-mark" src="assets/dorni-wordmark.png" alt="dorni">
<div id="f09-cap"></div>
<div id="f09-dot"></div>
<div id="f09-dot2"></div>
<svg id="f09-trail" width="1920" height="1080" viewBox="0 0 1920 1080">
  <defs><clipPath id="f09-clip"><rect id="f09-reveal" x="0" y="0" width="0" height="1080"/></clipPath></defs>
  <path id="f09-swim" d="{swim}" fill="none" stroke="none"/>
  <path id="f09-wave" d="{wave}" fill="none" stroke="none"/>
  <text id="f09-text" clip-path="url(#f09-clip)"><textPath href="#f09-wave" startOffset="0">{PHRASE}</textPath></text>
</svg>
{jelly("f09-jf")}
""", f"""
#f09-circle{{position:absolute;left:445px;top:25px;width:1030px;height:1030px;border-radius:50%;background:{BLUE};}}
#f09-mark{{position:absolute;left:500px;top:376px;width:892px;height:326px;}}
#f09-cap{{position:absolute;left:1300px;top:405px;width:110px;height:60px;border-radius:60px 60px 10px 10px;background:{NAVY};}}
#f09-dot,#f09-dot2{{position:absolute;left:1309px;top:364px;width:92px;height:92px;border-radius:50%;background:{BLUE};}}
#f09-trail{{position:absolute;left:0;top:0;overflow:visible;}}
#f09-text{{font-family:'Inter',sans-serif;font-weight:500;font-size:44px;letter-spacing:-0.01em;fill:{CREAM};}}
""", f"""
// circle collapses back into the dot of the i
tl.fromTo('#f09-cap',{{autoAlpha:1}},{{autoAlpha:0,duration:0.3}},0.35);
tl.fromTo('#f09-circle',{{x:0,y:0,scale:1}},{{x:395,y:-130,scale:92/1030,duration:1.0,ease:'expo.inOut'}},0.4);
tl.set('#f09-circle',{{autoAlpha:0}},1.4);
tl.fromTo('#f09-dot',{{autoAlpha:0}},{{autoAlpha:1,duration:0.01}},1.4);
// the dot becomes the jellyfish
tl.to('#f09-dot',{{scale:0,duration:0.35,ease:'power2.in'}},1.6);
// a new dot is born on the i: it starts over
tl.fromTo('#f09-dot2',{{scale:0}},{{scale:1,duration:0.5,ease:'back.out(2.2)'}},7.0);
const swimP=mkPath(document.getElementById('f09-swim').getAttribute('d')), waveP=mkPath(document.getElementById('f09-wave').getAttribute('d')), reveal=document.getElementById('f09-reveal');
const pose=rig('f09-jf');
function render(t){{
  let x=1355,y=410,rot=0,s=0,tent=0,a=0;
  if(t>=1.6&&t<2.2){{const u=easeOut(seg(t,1.6,2.2));s=0.42*u;tent=u;a=1;y=410-10*u;}}
  else if(t>=2.2&&t<3.7){{const p=onPath(swimP,easeInOut(seg(t,2.2,3.7)));x=p.x;y=p.y;rot=p.rot;s=0.42;tent=1;a=1;}}
  else if(t>=3.7&&t<6.6){{const p=onPath(waveP,seg(t,3.7,6.6));x=p.x;y=p.y-70;rot=p.rot;s=0.42;tent=1;a=1;}}
  else if(t>=6.6){{const u=seg(t,6.6,7.1);x=lerp(1795,2120,u);y=lerp(720,640,u);rot=70;s=0.42;tent=1;a=1;}}
  pose(x,y,rot,s,t,tent,a);
  const w = t<3.7?0:(t<6.6?(x-20):1920);
  reveal.setAttribute('width',Math.max(0,w));
}}
{clock()}
""")

def storyboard_durations():
    """src -> seconds from STORYBOARD.md, so VO-synced durations flow into the frames."""
    import re
    out, dur = {}, None
    for line in (ROOT / "STORYBOARD.md").read_text().splitlines():
        if line.startswith("## Frame"):
            dur = None
        m = re.match(r"^- duration:\s*([0-9.]+)s?\s*$", line)
        if m:
            dur = float(m.group(1))
        m = re.match(r"^- src:\s*compositions/frames/(\S+)\.html", line)
        if m and dur is not None:
            out[m.group(1)] = dur
    return out


durs = storyboard_durations()
for fid, spec in frames.items():
    d = durs.get(fid, spec[0])
    spec = (int(d) if d == int(d) else d,) + tuple(spec[1:])
    (OUT / f"{fid}.html").write_text(frame(fid, *spec))
    print("wrote", fid, f"{spec[0]:g}s")

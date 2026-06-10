
import base64, importlib, json, sys
from collections import defaultdict
from pathlib import Path
import cv2, plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
from india_mapper import COMPARISON_TABLE, TIER_CONFIG

st.set_page_config(page_title="ADAS India", page_icon="🛡️",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@700;800&display=swap');

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

html,body,.stApp,[data-testid="stAppViewContainer"]{
  background:#111 !important;
  font-family:'DM Sans',sans-serif;
  color:#e8e0d4;
}
[data-testid="stHeader"],[data-testid="stSidebar"]{display:none !important}
section[data-testid="stMain"]>div{padding-top:0 !important}
.block-container{padding:0 0 40px !important;max-width:100% !important}

/* ── NAV ── */
nav.topbar{
  position:sticky;top:0;z-index:200;
  display:flex;align-items:center;justify-content:center;
  padding:0 48px;height:64px;
  background:rgba(17,17,17,0.92);
  backdrop-filter:blur(20px);
  border-bottom:1px solid rgba(245,158,11,0.1);
}
nav.topbar .nav-inner{
  display:flex;align-items:center;
  width:100%;max-width:1200px;
}
nav.topbar .brand{
  font-family:'Playfair Display',serif;
  font-weight:800;font-size:1.15rem;
  color:#fff;letter-spacing:-0.01em;
  margin-right:auto;
}
nav.topbar .brand span{color:#f59e0b}
nav.topbar .links{display:flex;gap:4px}

/* nav buttons */
[data-testid="stHorizontalBlock"] .stButton>button{
  background:none !important;color:#888 !important;
  border:none !important;border-radius:8px !important;
  font-family:'DM Sans',sans-serif !important;font-weight:500 !important;
  font-size:0.9rem !important;padding:8px 18px !important;
  letter-spacing:0.01em !important;transition:all .2s !important;
  min-height:auto !important;line-height:1.4 !important;
}
[data-testid="stHorizontalBlock"] .stButton>button:hover{
  background:rgba(245,158,11,0.08) !important;color:#f59e0b !important;
  opacity:1 !important;
}

/* ── HERO ── */
.hero{
  position:relative;overflow:hidden;
  background:#111;
  min-height:88vh;
  display:flex;flex-direction:column;
  align-items:center;justify-content:center;
  padding:80px 48px 100px;
  text-align:center;
}
.hero::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 70% 50% at 50% 100%,rgba(245,158,11,0.18) 0%,transparent 70%);
  pointer-events:none;
}
.hero::after{
  content:'';position:absolute;
  left:50%;bottom:0;transform:translateX(-50%);
  width:1px;height:100%;
  background:repeating-linear-gradient(to top,
    rgba(245,158,11,0.3) 0px,rgba(245,158,11,0.3) 20px,
    transparent 20px,transparent 44px);
  animation:road 0.8s linear infinite;
}
@keyframes road{from{background-position:0 0}to{background-position:0 -44px}}
.hero-eye{
  font-family:'DM Sans',sans-serif;
  font-size:0.78rem;letter-spacing:0.2em;text-transform:uppercase;
  color:rgba(245,158,11,0.5);margin-bottom:28px;font-weight:500;
}
.hero-h1{
  font-family:'Playfair Display',serif;
  font-size:clamp(3rem,6.5vw,6rem);
  font-weight:800;line-height:1.05;
  color:#fff;letter-spacing:-0.03em;
  max-width:880px;
}
.hero-h1 em{color:#f59e0b;font-style:normal}
.hero-p{
  font-size:1rem;
  color:rgba(255,255,255,0.4);
  max-width:520px;line-height:1.8;
  margin-top:28px;
}

/* ── PAGE WRAPPER ── */
.pg{padding:72px 48px;max-width:1200px;margin:0 auto}

/* ── SECTION HEADING ── */
.sh{
  font-family:'Playfair Display',serif;
  font-size:clamp(1.8rem,3vw,2.5rem);
  font-weight:800;letter-spacing:-0.02em;
  color:#fff;margin-bottom:12px;
}
.sh em{color:#f59e0b;font-style:normal}
.sp{
  font-size:0.95rem;color:#777;
  max-width:520px;line-height:1.7;margin-bottom:48px;
}

/* ── PROBLEM CARDS ── */
.pcards{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
.pcard{
  background:#1a1a1a;border-radius:12px;padding:32px;
  border:1px solid rgba(245,158,11,0.08);
  transition:transform .2s,border-color .3s;
}
.pcard:hover{transform:translateY(-3px);border-color:rgba(245,158,11,0.25)}
.pcard-num{
  font-family:'DM Sans',sans-serif;font-size:0.75rem;font-weight:600;
  color:#f59e0b;letter-spacing:0.08em;text-transform:uppercase;
  margin-bottom:16px;display:flex;align-items:center;gap:8px;
}
.pcard-num::after{
  content:'';flex:1;height:1px;background:rgba(245,158,11,0.15);
}
.pcard-t{font-family:'DM Sans',sans-serif;font-weight:700;font-size:1.05rem;
  color:#fff;margin-bottom:10px}
.pcard-b{font-size:0.9rem;color:#888;line-height:1.7}

/* ── VIDEO COMPARISON ── */
.vgrid{display:grid;grid-template-columns:1fr 1fr;gap:2px;background:#000}
.vpanel{position:relative;overflow:hidden;background:#000}
.vpanel video{width:100%;display:block}
.vpanel-label{
  position:absolute;top:16px;left:16px;z-index:10;
  font-family:'DM Sans',sans-serif;font-size:0.72rem;
  font-weight:600;letter-spacing:0.06em;text-transform:uppercase;
  padding:5px 12px;border-radius:6px;
}
.lbl-base{background:rgba(255,255,255,0.1);color:#aaa;backdrop-filter:blur(8px)}
.lbl-india{background:rgba(245,158,11,0.9);color:#111}
.vplaceholder{
  aspect-ratio:16/9;background:#0a0a0a;
  display:flex;align-items:center;justify-content:center;
}
.vplaceholder p{font-size:0.85rem;color:#555;font-family:'DM Sans',sans-serif}

/* ── METRIC ROW ── */
.mrow{
  display:grid;grid-template-columns:repeat(5,1fr);
  gap:1px;background:#222;
}
.mcell{
  background:#161616;padding:28px 20px;
  border-top:3px solid transparent;
}
.mcell.cr{border-top-color:#ef4444}
.mcell.hi{border-top-color:#f59e0b}
.mcell.me{border-top-color:#eab308}
.mcell.rk{border-top-color:#f59e0b}
.mcell.fr{border-top-color:#333}
.mc-v{font-family:'DM Sans',sans-serif;font-size:2rem;font-weight:700;
  letter-spacing:-0.03em;line-height:1;margin-bottom:6px}
.mc-l{font-size:0.78rem;color:#666;line-height:1.4}
.col-cr{color:#ef4444}.col-hi{color:#f59e0b}
.col-me{color:#eab308}.col-rk{color:#f59e0b}.col-fr{color:#aaa}

/* ── CHARTS ── */
.cpanel{background:#1a1a1a;border-radius:12px;padding:28px;
  border:1px solid rgba(245,158,11,0.08)}
.ct{font-family:'DM Sans',sans-serif;font-size:0.78rem;font-weight:600;
  letter-spacing:0.06em;text-transform:uppercase;color:#f59e0b;margin-bottom:20px}

/* ── GAP TABLE ── */
.grow{
  display:grid;grid-template-columns:110px 1fr 16px 1fr;
  align-items:center;gap:12px;
  padding:12px 16px;background:#1a1a1a;border-radius:8px;
  border-left:3px solid transparent;
  border:1px solid rgba(255,255,255,0.04);
  transition:background .15s;
}
.grow:hover{background:#222}
.gbadge{
  font-size:0.65rem;font-family:'DM Sans',sans-serif;font-weight:600;
  padding:4px 10px;border-radius:4px;text-align:center;white-space:nowrap;
}
.gfrom{font-size:0.85rem;color:#777}
.garr{color:#555;text-align:center}
.gto{font-size:0.88rem;color:#fff;font-weight:600}

/* ── UPLOAD PAGE ── */
.up-hero{
  background:#161616;padding:72px 48px 48px;
  display:flex;flex-direction:column;
  align-items:center;text-align:center;
  border-bottom:1px solid rgba(245,158,11,0.1);
}
.up-hero .sh{color:#fff}
.up-hero .sh em{color:#f59e0b}
.up-hero .sp{color:#777;margin-bottom:0}
.upload-wrap{max-width:600px;margin:0 auto;padding:40px 0}

/* ── PROGRESS ── */
.pbar-wrap{background:#222;border-radius:4px;overflow:hidden;height:4px;margin:8px 0}
.pbar-fill{height:4px;border-radius:4px;
  background:linear-gradient(90deg,#f59e0b,#fbbf24);transition:width .3s}
.pstat{font-size:0.8rem;color:#777;font-family:'DM Sans',sans-serif}

/* ── FOOTER ── */
footer.ft{
  background:#0a0a0a;padding:32px 48px;
  display:flex;justify-content:center;align-items:center;gap:32px;
  border-top:1px solid rgba(245,158,11,0.08);
}
footer.ft p{
  font-size:0.78rem;color:#555;
  font-family:'DM Sans',sans-serif;letter-spacing:0.02em;
}

/* ── STREAMLIT WIDGET OVERRIDES ── */
.pg .stButton>button, .up-hero~div .stButton>button, .hero~div .stButton>button{
  background:#f59e0b !important;color:#111 !important;
  border:none !important;border-radius:8px !important;
  font-family:'DM Sans',sans-serif !important;font-weight:700 !important;
  font-size:0.92rem !important;padding:14px 32px !important;
  letter-spacing:0.01em !important;transition:all .2s !important;
}
.pg .stButton>button:hover, .hero~div .stButton>button:hover,
.up-hero~div .stButton>button:hover{
  background:#fbbf24 !important;opacity:1 !important;
  transform:translateY(-1px);box-shadow:0 4px 20px rgba(245,158,11,0.3) !important;
}
[data-testid="stFileUploader"]{background:transparent !important}
[data-testid="stFileUploader"] section{
  background:#1a1a1a !important;
  border:2px dashed rgba(245,158,11,0.2) !important;
  border-radius:12px !important;
}
[data-testid="stFileUploader"] label{color:#888 !important;font-size:0.9rem !important}
[data-testid="stFileUploader"] p{color:#666 !important}
[data-testid="stFileUploader"] span{color:#888 !important}
div[data-testid="stAlert"]{
  background:rgba(245,158,11,0.08) !important;
  border:1px solid rgba(245,158,11,0.2) !important;
  border-radius:8px !important;color:#f59e0b !important;
}
[data-testid="stProgress"]>div>div{
  background:linear-gradient(90deg,#f59e0b,#fbbf24) !important;
}
[data-testid="stProgress"]{background:#222 !important}

::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:#111}
::-webkit-scrollbar-thumb{background:#333;border-radius:2px}

@keyframes fadeUp{
  from{opacity:0;transform:translateY(16px)}
  to{opacity:1;transform:translateY(0)}
}
.a1{animation:fadeUp .5s ease both}
.a2{animation:fadeUp .5s .12s ease both}
.a3{animation:fadeUp .5s .24s ease both}
.a4{animation:fadeUp .5s .36s ease both}
</style>
""", unsafe_allow_html=True)

# ── helpers ──────────────────────────────────────────────────────────────
@st.cache_data
def load_logs():
    bp = Path("outputs/baseline_log.json")
    ip = Path("outputs/india_log.json")
    return (json.loads(bp.read_text()) if bp.exists() else {},
            json.loads(ip.read_text()) if ip.exists() else {})

def b64vid(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode()

def vid_src(names):
    return next((Path(f"outputs/{n}") for n in names
                 if Path(f"outputs/{n}").exists()), None)

def encode_video(raw: Path) -> Path:
    web = raw.with_stem(raw.stem + "_web")
    try:
        import imageio
        r = imageio.get_reader(str(raw))
        fps = r.get_meta_data().get("fps", 25)
        w = imageio.get_writer(str(web), fps=fps, codec="libx264",
                               pixelformat="yuv420p", macro_block_size=1, quality=7)
        for f in r: w.append_data(f)
        w.close(); r.close()
        return web
    except Exception:
        return raw

def pb(ex=None, ey=None):
    x = dict(gridcolor="#222", zeroline=False, showline=False,
             tickfont=dict(size=11, color="#888"), automargin=True)
    y = dict(gridcolor="#222", zeroline=False, showline=False,
             tickfont=dict(size=11, color="#888"), automargin=True)
    if ex: x.update(ex)
    if ey: y.update(ey)
    return dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color="#888", size=11),
        margin=dict(l=40,r=20,t=20,b=60), xaxis=x, yaxis=y
    )

baseline, india = load_logs()
tc  = india.get("tier_counts", {})
tf  = india.get("total_frames", 0)
ta  = india.get("total_alerts", 0)
pct = round((tc.get("critical",0)+tc.get("high",0))/tf*100,1) if tf else 0

# ── session state ─────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Home"

# ── NAV ──────────────────────────────────────────────────────────────────
st.markdown("""
<nav class="topbar">
  <div class="nav-inner">
    <div class="brand">ADAS <span>India</span></div>
    <div class="links">
""", unsafe_allow_html=True)

pages = ["Home","Demo","Analytics","Upload"]
cols  = st.columns([2,1,1,1.3,1,2])
for i,p in enumerate(pages):
    with cols[i+1]:
        if st.button(p, key=f"nb_{p}"):
            st.session_state.page = p; st.rerun()

st.markdown("</div></div></nav>", unsafe_allow_html=True)

page = st.session_state.page

# ═══════════════════════════════════════════════════════════════════════
# HOME
# ═══════════════════════════════════════════════════════════════════════
if page == "Home":
    b_total = sum(baseline.get("detection_counts",{}).values())

    st.markdown("""
    <div class="hero">
      <div class="hero-eye a1">ET AutoTech Hackathon 2026 &middot; Theme 3</div>
      <h1 class="hero-h1 a2">Indian roads demand<br><em>Indian intelligence</em></h1>
      <p class="hero-p a3">Standard ADAS sees a road. This prototype sees India.
        Cattle on highways, auto-rickshaws, jaywalkers, two-wheeler swarms.
        Same model, fundamentally different understanding.</p>
    </div>
    """, unsafe_allow_html=True)

    _, cc, _ = st.columns([1,2,1])
    with cc:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("See it in action", use_container_width=True):
                st.session_state.page = "Demo"; st.rerun()
        with c2:
            if st.button("Upload your clip", use_container_width=True):
                st.session_state.page = "Upload"; st.rerun()

    st.markdown("""
    <div class="pg">
      <div style="margin-top:16px">
        <h2 class="sh">The problem with <em>generic</em> ADAS</h2>
        <p class="sp">
          ADAS systems trained on Western datasets fail to recognise what makes
          Indian roads uniquely dangerous. This prototype maps every gap and builds
          an India-specific context layer on top of YOLOv8.
        </p>
        <div class="pcards">
          <div class="pcard">
            <div class="pcard-num">01 &middot; Blind spot</div>
            <div class="pcard-t">Entire object classes are missing</div>
            <div class="pcard-b">Cattle, buffalo, auto-rickshaws, tempo travellers
              do not exist in COCO. A generic model returns zero detections where
              India's most critical hazards actually appear.</div>
          </div>
          <div class="pcard">
            <div class="pcard-num">02 &middot; Density</div>
            <div class="pcard-t">No swarm or density awareness</div>
            <div class="pcard-b">One motorcycle is routine. Eight motorcycles weaving
              through an intersection is an emergency. Generic ADAS treats them
              identically, with no concept of density as a risk multiplier.</div>
          </div>
          <div class="pcard">
            <div class="pcard-num">03 &middot; Context</div>
            <div class="pcard-t">Risk is assigned without context</div>
            <div class="pcard-b">A person on a sidewalk in Germany and a pedestrian
              jaywalking on a Mumbai expressway are both labelled "person 0.9".
              Context should determine the risk, not just the class label.</div>
          </div>
          <div class="pcard">
            <div class="pcard-num">04 &middot; Output</div>
            <div class="pcard-t">Detection without prioritisation</div>
            <div class="pcard-b">Raw detection output is noise. This engine classifies
              every frame into critical, high, medium, or low risk tiers,
              enabling real-time alert prioritisation for drivers.</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════════
elif page == "Demo":
    bv = vid_src(["baseline_web.mp4","baseline_detected.mp4"])
    iv = vid_src(["india_web.mp4","india_detected.mp4"])

    if bv and iv:
        st.markdown(f"""
        <div class="vgrid">
          <div class="vpanel">
            <span class="vpanel-label lbl-base">Generic ADAS</span>
            <video autoplay muted loop controls style="width:100%;display:block">
              <source src="data:video/mp4;base64,{b64vid(bv)}" type="video/mp4">
            </video>
          </div>
          <div class="vpanel">
            <span class="vpanel-label lbl-india">India ADAS</span>
            <video autoplay muted loop controls style="width:100%;display:block">
              <source src="data:video/mp4;base64,{b64vid(iv)}" type="video/mp4">
            </video>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="vgrid">
          <div class="vpanel"><div class="vplaceholder"><p>Run detect.py first</p></div></div>
          <div class="vpanel"><div class="vplaceholder"><p>Run detect_india.py first</p></div></div>
        </div>""", unsafe_allow_html=True)

    # metric strip
    st.markdown(f"""
    <div class="mrow">
      <div class="mcell fr">
        <div class="mc-v col-fr">{tf:,}</div>
        <div class="mc-l">Frames analysed</div>
      </div>
      <div class="mcell cr">
        <div class="mc-v col-cr">{tc.get('critical',0):,}</div>
        <div class="mc-l">Critical risk frames</div>
      </div>
      <div class="mcell hi">
        <div class="mc-v col-hi">{tc.get('high',0):,}</div>
        <div class="mc-l">High risk frames</div>
      </div>
      <div class="mcell me">
        <div class="mc-v col-me">{tc.get('medium',0):,}</div>
        <div class="mc-l">Medium risk frames</div>
      </div>
      <div class="mcell rk">
        <div class="mc-v col-rk">{pct}%</div>
        <div class="mc-l">High + Critical rate</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # gap table
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    st.markdown('<h2 class="sh">What gets <em>missed</em></h2>', unsafe_allow_html=True)
    st.markdown('<p class="sp">Every row is a detection failure in a generic system: wrong label, missing class, or invisible hazard.</p>', unsafe_allow_html=True)

    gs = {
        "Wrong class":       ("#ef4444","rgba(239,68,68,0.1)"),
        "Missing context":   ("#f59e0b","rgba(245,158,11,0.1)"),
        "Missing class":     ("#eab308","rgba(234,179,8,0.1)"),
        "Missing behaviour": ("#a855f7","rgba(168,85,247,0.1)"),
        "Underdetected":     ("#3b82f6","rgba(59,130,246,0.1)"),
    }
    g1, g2 = st.columns(2)
    for i,(coco,il,gap) in enumerate(COMPARISON_TABLE):
        c,bg = gs.get(gap,("#888","#fafafa"))
        with (g1 if i%2==0 else g2):
            st.markdown(f"""
            <div class="grow" style="border-left:3px solid {c}">
              <span class="gbadge" style="background:{bg};color:{c}">{gap}</span>
              <span class="gfrom">{coco}</span>
              <span class="garr">→</span>
              <span class="gto">{il}</span>
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# ANALYTICS
# ═══════════════════════════════════════════════════════════════════════
elif page == "Analytics":
    st.markdown('<div class="pg">', unsafe_allow_html=True)
    st.markdown('<h2 class="sh">Detection <em>breakdown</em></h2>', unsafe_allow_html=True)
    st.markdown('<p class="sp">Every frame classified. Every hazard counted.</p>', unsafe_allow_html=True)

    tiers  = ["critical","high","medium","low"]
    colors = ["#ef4444","#f59e0b","#eab308","#22c55e"]
    vals   = [tc.get(t,0) for t in tiers]

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown('<div class="cpanel"><div class="ct">Generic ADAS: what it sees</div>', unsafe_allow_html=True)
        bc = baseline.get("detection_counts",{})
        if bc:
            top = dict(list(bc.items())[:10])
            fig = go.Figure(go.Bar(
                x=list(top.values()), y=list(top.keys()), orientation="h",
                marker=dict(color=list(range(len(top))),
                            colorscale=[[0,"#333"],[1,"#f59e0b"]],showscale=False),
                text=list(top.values()), textposition="outside",
                textfont=dict(size=10,color="#888"),
            ))
            fig.update_layout(height=320,
                **pb(ex=dict(title_text="Detection Count"),
                     ey=dict(tickfont=dict(size=10), title_text="Object Class")))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="cpanel"><div class="ct">India ADAS: risk tier breakdown</div>', unsafe_allow_html=True)
        if any(vals):
            fig2 = go.Figure(go.Bar(
                x=[t.capitalize() for t in tiers], y=vals,
                marker_color=colors, width=0.5,
                text=vals, textposition="outside",
                textfont=dict(size=11,color="#888"),
            ))
            fig2.update_layout(height=320,
                **pb(ex=dict(title_text="Risk Tier"),
                     ey=dict(title_text="Frame Count")))
            st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    ic = india.get("india_label_counts",{})
    if ic:
        st.markdown('<div class="cpanel" style="margin-top:16px"><div class="ct">India-specific class detections</div>', unsafe_allow_html=True)
        sc = dict(sorted(ic.items(),key=lambda x:-x[1]))
        cmap = {
            "Pedestrian / Jaywalker":"#ef4444","Cattle / Buffalo":"#ef4444",
            "Stray Animal":"#ef4444","Dense Two-Wheeler Traffic":"#f59e0b",
            "Two-Wheeler (Overload risk)":"#f59e0b","Car / Auto-Rickshaw":"#eab308",
            "Truck / Goods Vehicle":"#eab308","Bus / Tempo Traveller":"#eab308",
            "Traffic Signal":"#22c55e",
        }
        fig3 = go.Figure(go.Bar(
            x=list(sc.keys()), y=list(sc.values()),
            marker_color=[cmap.get(k,"#555") for k in sc],
            text=list(sc.values()), textposition="outside",
            textfont=dict(size=10,color="#888"), width=0.6,
        ))
        fig3.update_layout(height=340,
                           **pb(ex=dict(tickangle=-30, tickfont=dict(size=10),
                                        title_text="India-Specific Class"),
                                ey=dict(title_text="Detection Count")))
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if any(vals):
        dc1, dc2 = st.columns([1,2])
        with dc1:
            st.markdown('<div class="cpanel" style="margin-top:16px"><div class="ct">Risk distribution</div>', unsafe_allow_html=True)
            fig4 = go.Figure(go.Pie(
                labels=[t.capitalize() for t in tiers], values=vals, hole=0.6,
                marker=dict(colors=colors,line=dict(color="#1a1a1a",width=3)),
                textinfo="label+percent",
                textfont=dict(size=10,family="DM Sans",color="#ccc"),
            ))
            fig4.update_layout(
                height=260,
                paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="DM Sans",color="#888",size=10),
                margin=dict(l=8,r=8,t=8,b=8),showlegend=False,
                annotations=[dict(text=f"<b>{pct}%</b>",x=0.5,y=0.5,
                    showarrow=False,font=dict(size=20,color="#f59e0b",family="DM Sans"))]
            )
            st.plotly_chart(fig4, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with dc2:
            st.markdown('<div class="cpanel" style="margin-top:16px"><div class="ct">Frame counts per tier</div>', unsafe_allow_html=True)
            fig5 = go.Figure()
            for t,c,v in zip(tiers,colors,vals):
                fig5.add_trace(go.Bar(name=t.capitalize(),x=[t.capitalize()],y=[v],
                    marker_color=c,width=0.4,
                    text=[v],textposition="outside",
                    textfont=dict(size=12,color=c)))
            fig5.update_layout(height=280,showlegend=False,barmode="group",
                **pb(ex=dict(title_text="Risk Tier"),
                     ey=dict(title_text="Frame Count")))
            st.plotly_chart(fig5, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# UPLOAD
# ═══════════════════════════════════════════════════════════════════════
elif page == "Upload":
    st.markdown("""
    <div class="up-hero">
      <h2 class="sh">Test it on <em>your</em> footage</h2>
      <p class="sp">Upload any Indian dashcam clip and both pipelines
        will run automatically. Results appear side by side.</p>
    </div>
    """, unsafe_allow_html=True)

    _, uc, _ = st.columns([1,2,1])
    with uc:
        st.markdown('<div class="upload-wrap">', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Drag and drop your video (MP4, AVI, MOV)",
            type=["mp4","avi","mov"],
            label_visibility="visible",
        )

        if uploaded:
            data_dir = Path("data"); data_dir.mkdir(exist_ok=True)
            upload_path = data_dir / "uploaded_video.mp4"
            upload_path.write_bytes(uploaded.read())
            st.markdown(
                f'<p style="font-size:0.88rem;color:#aaa;margin:12px 0 4px">'
                f'{uploaded.name} &middot; {uploaded.size//1024:,} KB</p>',
                unsafe_allow_html=True
            )
            run_btn = st.button("Run analysis", use_container_width=True)
        else:
            run_btn = False
        st.markdown('</div>', unsafe_allow_html=True)

    if uploaded and run_btn:
        from india_mapper import (map_coco_to_india, DENSE_TW_LABEL,
                                  DENSE_TW_THRESHOLD, DENSE_TW_TIER)
        import detect as _det, detect_india as _ind
        importlib.reload(_det); importlib.reload(_ind)
        TW = {"motorcycle","bicycle"}

        cap_tmp = cv2.VideoCapture(str(upload_path))
        n_frames = int(cap_tmp.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        cap_tmp.release()

        def open_cap():
            c = cv2.VideoCapture(str(upload_path))
            W = int(c.get(cv2.CAP_PROP_FRAME_WIDTH))
            H = int(c.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = c.get(cv2.CAP_PROP_FPS) or 25
            return c, W, H, fps

        # ── run baseline ──────────────────────────────────────────────
        pb1 = st.progress(0, text="Generic ADAS: processing...")
        cap, W, H, fps = open_cap()
        out_b = Path("outputs/baseline_detected.mp4")
        wr = cv2.VideoWriter(str(out_b), cv2.VideoWriter_fourcc(*"mp4v"), fps,(W,H))
        cnt: dict = defaultdict(int); fi = 0
        mdl_b = _det.YOLO(str(_det.MODEL_PATH))
        while True:
            ret, frame = cap.read()
            if not ret: break
            fi += 1
            for box in mdl_b(frame, conf=0.30, verbose=False)[0].boxes:
                cid=int(box.cls[0]); lbl=mdl_b.names[cid]; cf=float(box.conf[0])
                x1,y1,x2,y2=map(int,box.xyxy[0])
                cnt[lbl]+=1; _det.draw_box(frame,x1,y1,x2,y2,lbl,cf)
            _det.draw_hud(frame,fi,fps,sum(cnt.values()))
            wr.write(frame)
            if fi%15==0 or fi==n_frames:
                pb1.progress(fi/n_frames, text=f"Generic ADAS: {fi}/{n_frames}")
        cap.release(); wr.release()
        Path("outputs/baseline_log.json").write_text(json.dumps({
            "source_video":str(upload_path),"total_frames":fi,
            "total_detections":sum(cnt.values()),
            "detection_counts":dict(sorted(cnt.items(),key=lambda x:-x[1])),
            "conf_threshold":0.30,"device":"cpu"
        },indent=2))
        pb1.progress(1.0, text="Generic ADAS: encoding...")
        web_b = encode_video(out_b)

        # ── run india ─────────────────────────────────────────────────
        pb2 = st.progress(0, text="India ADAS: processing...")
        cap, W, H, fps = open_cap()
        out_i = Path("outputs/india_detected.mp4")
        wr = cv2.VideoWriter(str(out_i), cv2.VideoWriter_fourcc(*"mp4v"), fps,(W,H))
        tc2:dict=defaultdict(int); lc:dict=defaultdict(int)
        htc:dict=defaultdict(int); alerts=0; fi=0
        mdl_i = _ind.YOLO(str(_ind.MODEL_PATH))
        while True:
            ret, frame = cap.read()
            if not ret: break
            fi += 1
            dets=[]; tw=0
            for box in mdl_i(frame, conf=0.30, verbose=False)[0].boxes:
                cid=int(box.cls[0]); coco=mdl_i.names[cid].lower()
                cf=float(box.conf[0]); x1,y1,x2,y2=map(int,box.xyxy[0])
                il,tier=map_coco_to_india(coco)
                if coco in TW: tw+=1
                dets.append((il,tier)); lc[il]+=1
                _ind.draw_india_box(frame,x1,y1,x2,y2,il,tier,cf)
            if tw>=DENSE_TW_THRESHOLD:
                dets.append((DENSE_TW_LABEL,DENSE_TW_TIER))
                lc[DENSE_TW_LABEL]+=1; _ind.draw_dense_tw_banner(frame,tw)
            ft=_ind.classify_frame_tier(dets)
            tc2[ft]+=1; htc[ft]+=1
            if ft in ("critical","high"): alerts+=1
            _ind.draw_alert_strip(frame,[(l,t) for l,t in dets if t in ("critical","high")])
            _ind.draw_hud(frame,fi,fps,htc,alerts)
            wr.write(frame)
            if fi%15==0 or fi==n_frames:
                pb2.progress(fi/n_frames, text=f"India ADAS: {fi}/{n_frames}, alerts: {alerts}")
        cap.release(); wr.release()
        Path("outputs/india_log.json").write_text(json.dumps({
            "source_video":str(upload_path),"total_frames":fi,
            "total_alerts":alerts,"tier_counts":dict(tc2),
            "india_label_counts":dict(sorted(lc.items(),key=lambda x:-x[1])),
            "conf_threshold":0.30,"device":"cpu"
        },indent=2))
        pb2.progress(1.0, text="India ADAS: encoding...")
        web_i = encode_video(out_i)

        pb1.empty(); pb2.empty()

        # ── side-by-side result ───────────────────────────────────────
        st.markdown(f"""
        <div class="vgrid" style="margin-top:32px;border-radius:12px;overflow:hidden">
          <div class="vpanel">
            <span class="vpanel-label lbl-base">Generic ADAS</span>
            <video autoplay muted loop controls style="width:100%;display:block">
              <source src="data:video/mp4;base64,{b64vid(web_b)}" type="video/mp4">
            </video>
          </div>
          <div class="vpanel">
            <span class="vpanel-label lbl-india">India ADAS</span>
            <video autoplay muted loop controls style="width:100%;display:block">
              <source src="data:video/mp4;base64,{b64vid(web_i)}" type="video/mp4">
            </video>
          </div>
        </div>
        """, unsafe_allow_html=True)
        st.success("Analysis complete. Check the Analytics page for the full breakdown.")

# ── footer ────────────────────────────────────────────────────────────
st.markdown("""
<footer class="ft">
  <p>&copy; 2026 ADAS India Prototype &middot; ET AutoTech Hackathon &middot; Theme 3</p>
  <p>YOLOv8n &middot; India Context Engine</p>
</footer>
""", unsafe_allow_html=True)
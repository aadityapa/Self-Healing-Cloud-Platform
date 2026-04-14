import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

API_BASE = os.getenv(
    "ORCHESTRATOR_URL", "https://nexovo-helling-orchestrator.onrender.com"
)

st.set_page_config(page_title="Nexovo Helling Cloud", layout="wide", page_icon="☁️")

if "nexovo_view" not in st.session_state:
    st.session_state["nexovo_view"] = "home"
if "selected_plan" not in st.session_state:
    st.session_state["selected_plan"] = None

# Interactive Three.js globe (iframe). CDN loads Three.js in the component sandbox.
THREE_GLOBE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; overflow: hidden; background: transparent; }
    #globe-root { width: 100%; height: 300px; display: block; }
    canvas { display: block; width: 100% !important; height: 100% !important; outline: none; }
  </style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
  <div id="globe-root"></div>
  <script>
  (function () {
    var container = document.getElementById("globe-root");
    var h = 300;
    var w = Math.max(container.clientWidth || 800, 320);
    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(42, w / h, 0.08, 120);
    camera.position.set(0, 0, 3.45);
    var renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: "high-performance" });
    renderer.setSize(w, h);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    var group = new THREE.Group();
    var geo = new THREE.IcosahedronGeometry(1, 3);
    var mat = new THREE.MeshPhongMaterial({
      color: 0x0ea5e9,
      emissive: 0x172554,
      shininess: 95,
      specular: 0xaaddff
    });
    var mesh = new THREE.Mesh(geo, mat);
    var wireMat = new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.22 });
    var wire = new THREE.LineSegments(new THREE.WireframeGeometry(geo), wireMat);
    group.add(mesh);
    group.add(wire);

    var nodeGeo = new THREE.SphereGeometry(0.042, 10, 10);
    var nodeMat = new THREE.MeshBasicMaterial({ color: 0x22d3ee });
    for (var i = 0; i < 36; i++) {
      var nm = new THREE.Mesh(nodeGeo, nodeMat.clone());
      var ang = (i / 36) * Math.PI * 2;
      var phi = Math.PI * 0.35 + Math.sin(i * 1.3) * 0.35;
      var rr = 1.14;
      nm.position.set(
        rr * Math.sin(phi) * Math.cos(ang),
        rr * Math.cos(phi),
        rr * Math.sin(phi) * Math.sin(ang)
      );
      group.add(nm);
    }
    scene.add(group);

    var pCount = 720;
    var positions = new Float32Array(pCount * 3);
    for (var j = 0; j < pCount; j++) {
      var rr = 1.28 + Math.random() * 0.55;
      var t = Math.random() * Math.PI * 2;
      var p = Math.acos(2 * Math.random() - 1);
      positions[j * 3] = rr * Math.sin(p) * Math.cos(t);
      positions[j * 3 + 1] = rr * Math.sin(p) * Math.sin(t);
      positions[j * 3 + 2] = rr * Math.cos(p);
    }
    var pGeom = new THREE.BufferGeometry();
    pGeom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    var pMat = new THREE.PointsMaterial({
      color: 0x38bdf8,
      size: 0.038,
      transparent: true,
      opacity: 0.88,
      sizeAttenuation: true
    });
    var points = new THREE.Points(pGeom, pMat);
    scene.add(points);

    scene.add(new THREE.AmbientLight(0x6688cc, 0.52));
    var d1 = new THREE.DirectionalLight(0xffffff, 1.05);
    d1.position.set(4, 6, 7);
    scene.add(d1);
    var d2 = new THREE.DirectionalLight(0x38bdf8, 0.42);
    d2.position.set(-4, -3, -5);
    scene.add(d2);

    var mx = 0, my = 0, tmx = 0, tmy = 0;
    var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    renderer.domElement.addEventListener("mousemove", function (e) {
      var rect = renderer.domElement.getBoundingClientRect();
      tmx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      tmy = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    });
    renderer.domElement.addEventListener("mouseleave", function () { tmx = 0; tmy = 0; });
    renderer.domElement.style.cursor = "grab";

    var baseY = 0;
    function animate() {
      requestAnimationFrame(animate);
      mx += (tmx - mx) * 0.07;
      my += (tmy - my) * 0.07;
      if (!reducedMotion) baseY += 0.0042;
      group.rotation.y = baseY + mx * 0.55;
      group.rotation.x = my * 0.38;
      points.rotation.y = baseY * 0.65 + 0.15;
      points.rotation.x = my * 0.12;
      camera.position.x = mx * 0.22;
      camera.position.y = my * 0.18;
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
    }
    animate();

    window.addEventListener("resize", function () {
      var nw = Math.max(container.clientWidth || 800, 320);
      camera.aspect = nw / h;
      camera.updateProjectionMatrix();
      renderer.setSize(nw, h);
    });
  })();
  </script>
</body>
</html>
"""


def inject_theme(theme: str) -> None:
    is_light = theme == "light"
    bg = (
        "radial-gradient(circle at 15% 20%, rgba(56, 189, 248, 0.20), transparent 35%),"
        "radial-gradient(circle at 85% 10%, rgba(129, 140, 248, 0.24), transparent 40%),"
        "radial-gradient(circle at 50% 80%, rgba(14, 165, 233, 0.12), transparent 45%),"
        "linear-gradient(165deg, #050816 0%, #0b1220 45%, #0b1024 100%)"
    )
    text_color = "#e2e8f0"
    card_bg = "linear-gradient(145deg, rgba(15,23,42,0.97), rgba(30,41,59,0.78))"
    border = "rgba(148, 163, 184, 0.20)"
    hero_sub = "#fcd34d"
    if is_light:
        bg = (
            "radial-gradient(circle at 10% 20%, rgba(56, 189, 248, 0.14), transparent 35%),"
            "radial-gradient(circle at 88% 12%, rgba(99, 102, 241, 0.12), transparent 40%),"
            "linear-gradient(165deg, #eff6ff 0%, #f8fafc 45%, #eef2ff 100%)"
        )
        text_color = "#0f172a"
        card_bg = "linear-gradient(145deg, rgba(255,255,255,0.92), rgba(241,245,249,0.85))"
        border = "rgba(100, 116, 139, 0.25)"
        hero_sub = "#1d4ed8"

    console_shell_bg = (
        "linear-gradient(180deg, rgba(15,23,42,0.4) 0%, transparent 140px)"
        if not is_light
        else "linear-gradient(180deg, rgba(241,245,249,0.95) 0%, rgba(255,255,255,0.4) 100%)"
    )

    st.markdown(
        f"""
<style>
    .scene-3d {{
        perspective: 1200px;
        perspective-origin: 50% 20%;
        margin: 8px 0 18px 0;
    }}
    .topnav {{
        position: sticky;
        top: 0;
        z-index: 99;
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 14px;
        box-shadow: 0 12px 40px rgba(2, 6, 23, 0.22), inset 0 1px 0 rgba(255,255,255,0.08);
        backdrop-filter: blur(12px);
        animation: navGlow 8s ease-in-out infinite;
    }}
    .nav-brand {{font-weight: 800; letter-spacing: 0.4px; font-size: 1.05rem;}}
    .nav-links {{font-size: 0.88rem; opacity: 0.9;}}
    .main {{color: {text_color};}}
    .stApp {{
        background: {bg};
        position: relative;
    }}
    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background:
            radial-gradient(ellipse 120% 70% at 12% 15%, rgba(56, 189, 248, 0.14), transparent 55%),
            radial-gradient(ellipse 90% 60% at 90% 85%, rgba(129, 140, 248, 0.12), transparent 50%),
            radial-gradient(ellipse 55% 45% at 50% 45%, rgba(14, 165, 233, 0.07), transparent 62%);
        transform-origin: center center;
        animation: ambientShift 22s ease-in-out infinite alternate;
    }}
    [data-testid="stAppViewContainer"] {{
        position: relative;
        z-index: 1;
    }}
    .hero {{
        background: linear-gradient(135deg, rgba(245,158,11,0.22) 0%, rgba(251,191,36,0.18) 45%, rgba(56,189,248,0.12) 100%);
        border: 1px solid {border};
        border-radius: 20px;
        padding: 22px 26px;
        box-shadow: 0 28px 56px rgba(2, 6, 23, 0.28), inset 0 1px 0 rgba(255,255,255,0.1);
        backdrop-filter: blur(12px);
        margin-bottom: 14px;
        transform-style: preserve-3d;
        transform: rotateX(2deg) translateZ(8px);
        animation: heroFloat 8s ease-in-out infinite;
    }}
    .hero-title {{
        font-size: 1.8rem;
        font-weight: 750;
        margin: 0;
        letter-spacing: 0.3px;
    }}
    .hero-sub {{
        margin-top: 6px;
        color: {hero_sub};
        font-size: 0.95rem;
    }}
    .feature-grid {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0,1fr));
        gap: 10px;
        margin: 12px 0 16px 0;
    }}
    .feature {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 18px 36px rgba(2, 6, 23, 0.2), inset 0 -2px 0 rgba(0,0,0,0.06);
        transition: transform 0.35s ease, box-shadow 0.35s ease;
        transform-style: preserve-3d;
        transform: translateZ(0) rotateX(0deg);
        animation: cardFloat 5s ease-in-out infinite;
    }}
    .feature:nth-child(1) {{ animation-delay: 0s; }}
    .feature:nth-child(2) {{ animation-delay: 0.4s; }}
    .feature:nth-child(3) {{ animation-delay: 0.8s; }}
    .feature:nth-child(4) {{ animation-delay: 1.2s; }}
    .feature:hover {{
        transform: translateY(-8px) translateZ(16px) rotateX(2deg);
        box-shadow: 0 28px 48px rgba(2, 6, 23, 0.32);
    }}
    div[data-testid="stMetric"] {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 12px;
        box-shadow: 0 16px 30px rgba(2, 6, 23, 0.20), inset 0 1px 0 rgba(255,255,255,0.04);
        transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.4s ease;
    }}
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 22px 44px rgba(14, 165, 233, 0.18), inset 0 1px 0 rgba(255,255,255,0.08);
    }}
    .card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 14px;
        margin-bottom: 12px;
        box-shadow: 0 14px 28px rgba(2, 6, 23, 0.18), inset 0 1px 0 rgba(255,255,255,0.04);
        backdrop-filter: blur(8px);
        transition: transform 0.35s ease, box-shadow 0.35s ease, border-color 0.35s ease;
    }}
    .card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(2, 6, 23, 0.24), inset 0 1px 0 rgba(255,255,255,0.07);
        border-color: rgba(56, 189, 248, 0.35);
    }}
    .sev-critical {{color: #ef4444; font-weight: 700;}}
    .sev-high {{color: #f97316; font-weight: 700;}}
    .sev-medium {{color: #eab308; font-weight: 700;}}
    .sev-low {{color: #22c55e; font-weight: 700;}}
    .tiny {{color: #60a5fa; font-size: 0.84rem; margin-top: 4px;}}
    .orb-stage {{
        position: relative;
        height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 8px auto 12px auto;
        perspective: 900px;
        animation: stageBob 8s ease-in-out infinite;
    }}
    .orb-halo {{
        position: absolute;
        width: 240px;
        height: 240px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.45) 0%, rgba(56, 189, 248, 0.12) 42%, transparent 70%);
        filter: blur(14px);
        animation: haloPulse 5s ease-in-out infinite;
        pointer-events: none;
    }}
    .orb-ring {{
        position: absolute;
        width: 188px;
        height: 188px;
        border-radius: 50%;
        border: 1px solid rgba(56, 189, 248, 0.35);
        box-shadow: 0 0 50px rgba(14, 165, 233, 0.25), inset 0 0 30px rgba(56, 189, 248, 0.08);
        animation: ringSpin 28s linear infinite;
        pointer-events: none;
    }}
    .orb-ring::after {{
        content: "";
        position: absolute;
        inset: -4px;
        border-radius: 50%;
        border: 1px dashed rgba(129, 140, 248, 0.25);
        animation: ringSpin 40s linear infinite reverse;
    }}
    .node-wrap {{
        height: 150px;
        margin-bottom: 10px;
        position: relative;
        filter: drop-shadow(0 4px 12px rgba(14, 165, 233, 0.15));
    }}
    .node-svg .n-line {{
        stroke-dasharray: 10 14;
        animation: dashFlow 4s linear infinite;
    }}
    .node-svg .n-line:nth-child(2) {{ animation-duration: 5.2s; animation-delay: -0.5s; }}
    .node-svg .n-line:nth-child(3) {{ animation-duration: 3.8s; animation-delay: -1s; }}
    .node-svg .n-line:nth-child(4) {{ animation-duration: 4.5s; animation-delay: -0.2s; }}
    .node-svg .n-node {{
        animation: nodePulse 2.8s ease-in-out infinite;
        transform-origin: center;
        transform-box: fill-box;
    }}
    .node-svg .n-node.n-d1 {{ animation-delay: 0s; }}
    .node-svg .n-node.n-d2 {{ animation-delay: 0.35s; }}
    .node-svg .n-node.n-d3 {{ animation-delay: 0.7s; }}
    .node-svg .n-node.n-d4 {{ animation-delay: 1.05s; }}
    .node-svg .n-node.n-d5 {{ animation-delay: 1.4s; }}
    .cloud-3d {{
        position: relative;
        width: 150px;
        height: 150px;
        margin: 0 auto;
        border-radius: 50%;
        background:
          radial-gradient(circle at 28% 22%, rgba(255,255,255,0.92) 0%, rgba(186, 230, 253, 0.45) 8%, transparent 42%),
          radial-gradient(circle at 72% 78%, rgba(15, 23, 42, 0.9) 0%, transparent 55%),
          radial-gradient(circle at 30% 35%, #bae6fd, #0ea5e9 45%, #1e40af 78%, #0f172a 100%);
        box-shadow:
          inset -16px -22px 36px rgba(2,6,23,0.55),
          inset 16px 20px 32px rgba(255,255,255,0.35),
          0 36px 72px rgba(14,165,233,0.35),
          0 0 100px rgba(56,189,248,0.3);
        animation: spinCloud 20s linear infinite;
        transform-style: preserve-3d;
    }}
    .orb-shine {{
        position: absolute;
        inset: 0;
        border-radius: 50%;
        background: radial-gradient(circle at 32% 28%, rgba(255,255,255,0.75), transparent 38%);
        mix-blend-mode: soft-light;
        pointer-events: none;
        animation: shineDrift 6s ease-in-out infinite; 
    }}
    .orb-cavity {{
        position: absolute;
        inset: 18%;
        border-radius: 50%;
        background: radial-gradient(circle at 40% 40%, rgba(0,0,0,0.06), transparent 60%);
        pointer-events: none;
    }}
    .steps {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }}
    .steps b {{color: #fbbf24;}}
    .selling-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0,1fr));
        gap: 12px;
        margin: 12px 0 18px 0;
    }}
    .plan-card-wrap {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 18px;
        padding: 18px;
        min-height: 200px;
        box-shadow: 0 20px 40px rgba(2, 6, 23, 0.2);
        transform-style: preserve-3d;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    .plan-card-wrap:hover {{
        transform: translateY(-10px) rotateX(4deg) translateZ(12px);
        box-shadow: 0 32px 56px rgba(245, 158, 11, 0.2);
        border-color: #f59e0b;
    }}
    .plan-price {{font-size: 1.35rem; font-weight: 800; margin-top: 6px;}}
    .chip {{
        display: inline-block;
        border: 1px solid #f59e0b;
        color: #f59e0b;
        border-radius: 999px;
        padding: 2px 8px;
        font-size: 0.72rem;
        margin-left: 6px;
        vertical-align: middle;
    }}
    .cta {{
        background: linear-gradient(90deg, #f59e0b, #f97316, #0ea5e9);
        background-size: 240% 240%;
        color: white;
        border-radius: 12px;
        padding: 10px 14px;
        font-weight: 700;
        text-align: center;
        margin: 10px 0 0 0;
        animation: shift 6s ease infinite;
        box-shadow: 0 14px 25px rgba(37, 99, 235, 0.4);
    }}
    @keyframes ambientShift {{
        0% {{ opacity: 0.88; transform: scale(1); }}
        50% {{ opacity: 1; transform: scale(1.02); }}
        100% {{ opacity: 0.92; transform: scale(1.035); }}
    }}
    @keyframes navGlow {{
        0%, 100% {{ box-shadow: 0 12px 40px rgba(2, 6, 23, 0.22), inset 0 1px 0 rgba(255,255,255,0.08), 0 0 0 0 rgba(56,189,248,0); }}
        50% {{ box-shadow: 0 14px 44px rgba(2, 6, 23, 0.26), inset 0 1px 0 rgba(255,255,255,0.1), 0 0 28px rgba(56,189,248,0.12); }}
    }}
    @keyframes haloPulse {{
        0%, 100% {{ transform: scale(1); opacity: 0.75; }}
        50% {{ transform: scale(1.08); opacity: 1; }}
    }}
    @keyframes ringSpin {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}
    @keyframes dashFlow {{
        from {{ stroke-dashoffset: 0; }}
        to {{ stroke-dashoffset: -48; }}
    }}
    @keyframes nodePulse {{
        0%, 100% {{ transform: scale(1); filter: drop-shadow(0 0 4px rgba(56,189,248,0.5)); }}
        50% {{ transform: scale(1.12); filter: drop-shadow(0 0 12px rgba(129,140,248,0.85)); }}
    }}
    @keyframes shineDrift {{
        0%, 100% {{ opacity: 0.85; transform: translate(0, 0) scale(1); }}
        50% {{ opacity: 1; transform: translate(4%, -3%) scale(1.03); }}
    }}
    @keyframes pulse {{0%,100% {{transform: scale(1); opacity: 0.8;}} 50% {{transform: scale(1.08); opacity: 1;}}}}
    @keyframes spinCloud {{from {{transform: rotateY(0deg) rotateX(10deg);}} to {{transform: rotateY(360deg) rotateX(10deg);}}}}
    @keyframes stageBob {{0%,100% {{transform: translateY(0);}} 50% {{transform: translateY(-12px);}}}}
    @keyframes shellBreath {{
        0%, 100% {{ box-shadow: inset 0 1px 0 rgba(255,255,255,0.06), 0 24px 48px rgba(2,6,23,0.18); }}
        50% {{ box-shadow: inset 0 1px 0 rgba(255,255,255,0.09), 0 28px 52px rgba(14,165,233,0.14); }}
    }}
    @keyframes cloudBob {{0%,100% {{transform: translateY(0) translateZ(0);}} 50% {{transform: translateY(-10px) translateZ(20px);}}}}
    @keyframes heroFloat {{0%,100% {{transform: rotateX(2deg) translateZ(8px);}} 50% {{transform: rotateX(4deg) translateZ(14px);}}}}
    @keyframes cardFloat {{0%,100% {{transform: translateZ(0);}} 50% {{transform: translateZ(6px);}}}}
    @keyframes shift {{0% {{background-position: 0% 50%;}} 50% {{background-position: 100% 50%;}} 100% {{background-position: 0% 50%;}}}}
    .landing-hero {{
        background: linear-gradient(145deg, rgba(255,255,255,0.06) 0%, rgba(56,189,248,0.08) 50%, rgba(99,102,241,0.06) 100%);
        border: 1px solid {border};
        border-radius: 22px;
        padding: 28px 32px 32px 32px;
        margin-bottom: 18px;
        box-shadow: 0 32px 64px rgba(2, 6, 23, 0.35), inset 0 1px 0 rgba(255,255,255,0.12);
        backdrop-filter: blur(16px);
        transform-style: preserve-3d;
        transform: rotateX(1.5deg) translateZ(10px);
    }}
    .kicker {{
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #38bdf8;
        font-weight: 700;
        margin-bottom: 10px;
    }}
    .headline-xl {{
        font-size: clamp(1.45rem, 2.4vw, 2.05rem);
        font-weight: 800;
        line-height: 1.2;
        margin: 0 0 12px 0;
        letter-spacing: -0.02em;
    }}
    .lede {{
        font-size: 1.02rem;
        line-height: 1.55;
        opacity: 0.88;
        max-width: 52rem;
        margin: 0 0 18px 0;
    }}
    .trust-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 18px 0 22px 0;
    }}
    .trust-pill {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 999px;
        padding: 8px 14px;
        font-size: 0.82rem;
        font-weight: 600;
        box-shadow: 0 8px 20px rgba(2,6,23,0.15);
    }}
    .pillar-grid {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin: 16px 0 20px 0;
    }}
    .pillar {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 16px 18px;
        box-shadow: 0 16px 32px rgba(2,6,23,0.2);
        transform: translateZ(0);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }}
    .pillar:hover {{
        transform: translateY(-4px) translateZ(8px);
        box-shadow: 0 22px 44px rgba(2,6,23,0.28);
    }}
    .pillar h4 {{ margin: 0 0 8px 0; font-size: 0.95rem; }}
    .pillar p {{ margin: 0; font-size: 0.86rem; opacity: 0.88; line-height: 1.45; }}
    .mini-hero {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 16px;
        box-shadow: 0 20px 40px rgba(2,6,23,0.22);
    }}
    .mini-hero h2 {{ margin: 0 0 6px 0; font-size: 1.35rem; }}
    .mini-hero p {{ margin: 0; opacity: 0.85; }}
    .roi-panel {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 16px;
        box-shadow: 0 24px 48px rgba(2,6,23,0.25);
    }}
    .roi-panel h3 {{ margin: 0 0 6px 0; }}
    .roi-panel .sub {{ opacity: 0.85; font-size: 0.9rem; margin-bottom: 16px; }}
    .roi-big {{
        font-size: 1.75rem;
        font-weight: 800;
        color: #38bdf8;
        margin: 8px 0;
    }}
    .sales-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
        margin-top: 8px;
    }}
    .sales-card {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 20px 22px;
        min-height: 140px;
        box-shadow: 0 18px 36px rgba(2,6,23,0.2);
    }}
    .sales-card h4 {{ margin: 0 0 10px 0; font-size: 1.05rem; }}
    .sales-card p {{ margin: 0; font-size: 0.88rem; opacity: 0.88; line-height: 1.45; }}
    .console-shell {{
        border: 1px solid {border};
        border-radius: 18px;
        padding: 16px 18px 20px 18px;
        margin-top: 8px;
        background: {console_shell_bg};
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.06), 0 24px 48px rgba(2,6,23,0.18);
        animation: shellBreath 14s ease-in-out infinite;
    }}
    .section-label {{
        font-size: 0.75rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        opacity: 0.65;
        margin-bottom: 6px;
    }}
    div[data-testid="stTabs"] {{
        background: {card_bg};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 8px 10px 14px 10px;
        box-shadow: 0 16px 32px rgba(2,6,23,0.16);
    }}
    iframe[title="streamlit.components.v1.html"] {{
        border: none !important;
        border-radius: 18px;
        box-shadow: 0 24px 56px rgba(2, 6, 23, 0.35), 0 0 60px rgba(14, 165, 233, 0.12);
    }}
    @media (prefers-reduced-motion: reduce) {{
        .stApp::before,
        .topnav,
        .orb-stage,
        .orb-halo,
        .orb-ring,
        .cloud-3d,
        .orb-shine,
        .node-svg .n-line,
        .node-svg .n-node,
        .console-shell,
        .hero,
        .feature {{
            animation: none !important;
        }}
    }}
</style>
""",
        unsafe_allow_html=True,
    )


def gauge(label: str, value: float, max_value: float = 100.0) -> None:
    pct = 0.0 if max_value == 0 else max(0.0, min(100.0, (value / max_value) * 100.0))
    color = "#22c55e"
    if pct >= 70:
        color = "#f59e0b"
    if pct >= 90:
        color = "#ef4444"
    st.markdown(
        f"""
<div class='card'>
  <b>{label}</b>
  <div style='margin-top:8px;height:10px;border-radius:999px;background:#334155;overflow:hidden;'>
    <div style='width:{pct:.1f}%;height:10px;background:{color};box-shadow:0 0 12px {color};'></div>
  </div>
  <div class='tiny' style='margin-top:6px;'>{value:.1f}% utilization</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_plan_cards(key_suffix: str = "") -> None:
    suf = key_suffix
    st.markdown("### Plans that scale with you")
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        st.markdown(
            "<div class='plan-card-wrap'><b>Starter Ops</b><div class='plan-price'>$49<small>/mo</small></div>"
            "<p>Small teams building AI-assisted incident response.</p></div>",
            unsafe_allow_html=True,
        )
        if st.button("Choose Starter", use_container_width=True, key=f"choose_starter{suf}"):
            st.session_state["selected_plan"] = "Starter Ops ($49/mo)"
            st.session_state["nexovo_view"] = "console"
            st.balloons()
            st.rerun()
    with pc2:
        st.markdown(
            "<div class='plan-card-wrap'><b>Growth SRE</b> <span class='chip'>Popular</span>"
            "<div class='plan-price'>$199<small>/mo</small></div>"
            "<p>Full anomaly, RCA, and safe auto-remediation.</p></div>",
            unsafe_allow_html=True,
        )
        if st.button("Choose Growth", use_container_width=True, key=f"choose_growth{suf}"):
            st.session_state["selected_plan"] = "Growth SRE ($199/mo)"
            st.session_state["nexovo_view"] = "console"
            st.balloons()
            st.rerun()
    with pc3:
        st.markdown(
            "<div class='plan-card-wrap'><b>Enterprise Autonomous</b>"
            "<div class='plan-price'>Custom</div>"
            "<p>Multi-cluster guardrails and dedicated reliability advisory.</p></div>",
            unsafe_allow_html=True,
        )
        if st.button("Contact Sales", use_container_width=True, key=f"choose_ent{suf}"):
            st.session_state["selected_plan"] = "Enterprise (custom)"
            st.session_state["nexovo_view"] = "contact"
            st.rerun()


with st.sidebar:
    st.markdown("## Operations")
    st.caption("Filters, theme, and refresh for the live console.")
    if st.button("Refresh now", use_container_width=True):
        st.rerun()
    theme_mode = st.selectbox("Theme", ["dark", "light"], index=0)
    auto_refresh = st.toggle("Auto refresh (15s)", value=False)
    selected_service = st.text_input("Filter service", value="")
    selected_severity = st.selectbox(
        "Filter severity", ["all", "critical", "high", "medium", "low"], index=0
    )
    selected_window = st.selectbox(
        "Time window", ["last_1h", "last_6h", "last_24h", "last_7d", "all_time"], index=2
    )
    only_open = st.toggle("Only unacknowledged incidents", value=False)
    show_marketing = st.toggle("Show SaaS hero section", value=True)
    st.markdown("---")
    st.caption("Use this panel to tune views and run scenario simulations.")

inject_theme(theme_mode)
if auto_refresh:
    st.caption("Auto refresh enabled. Click 'Refresh now' every few seconds.")

st.markdown("<div class='topnav'>", unsafe_allow_html=True)
nav_b1, nav_b2, nav_b3, nav_b4, nav_b5, nav_b6, nav_b7 = st.columns([2.0, 1, 1, 1, 1, 1, 1])
with nav_b1:
    st.markdown("<span class='nav-brand'>NEXOVO HELLING CLOUD</span>", unsafe_allow_html=True)
with nav_b2:
    if st.button("Home", use_container_width=True, key="nav_home"):
        st.session_state["nexovo_view"] = "home"
        st.rerun()
with nav_b3:
    if st.button("Console", use_container_width=True, key="nav_console"):
        st.session_state["nexovo_view"] = "console"
        st.rerun()
with nav_b4:
    if st.button("Pricing", use_container_width=True, key="nav_pricing"):
        st.session_state["nexovo_view"] = "pricing"
        st.rerun()
with nav_b5:
    if st.button("Integrations", use_container_width=True, key="nav_integ"):
        st.session_state["nexovo_view"] = "integrations"
        st.rerun()
with nav_b6:
    if st.button("Contact", use_container_width=True, key="nav_contact"):
        st.session_state["nexovo_view"] = "contact"
        st.rerun()
with nav_b7:
    st.link_button("Docs", "https://technexovo.com/blog", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.get("selected_plan"):
    st.success(
        f"Plan selected: **{st.session_state['selected_plan']}** — open the Console tab to run live operations."
    )

view = st.session_state["nexovo_view"]

if show_marketing and view == "home":
    st.markdown(
        """
<div class='landing-hero'>
  <div class='kicker'>Enterprise reliability · AI-native operations</div>
  <h1 class='headline-xl'>Cut incident MTTR and operational risk with AI-assisted self-healing</h1>
  <p class='lede'>Unify detection, root-cause analysis, and safe remediation across Kubernetes and cloud-native workloads. One control plane for SRE, platform, and leadership—with full audit trails and webhook integrations.</p>
  <div class='trust-row'>
    <span class='trust-pill'>Faster MTTR</span>
    <span class='trust-pill'>99.9% uptime focus</span>
    <span class='trust-pill'>Slack · Jira · Email</span>
    <span class='trust-pill'>Audit-ready</span>
  </div>
</div>
<div class='pillar-grid'>
  <div class='pillar'><h4>Why Nexovo</h4><p>Signal-rich detection, explainable RCA, and guardrailed automation so teams ship faster without fear.</p></div>
  <div class='pillar'><h4>Why enterprises</h4><p>Executive-grade visibility, incident ownership, escalation paths, and integration with your existing toolchain.</p></div>
  <div class='pillar'><h4>Why now</h4><p>Incidents are expensive; every minute of downtime compounds cost, churn, and compliance risk.</p></div>
</div>
""",
        unsafe_allow_html=True,
    )
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.link_button(
            "Book a demo",
            "https://technexovo.com/contact",
            use_container_width=True,
            type="primary",
        )
    with h2:
        if st.button("Open console", use_container_width=True, key="hero_open_console"):
            st.session_state["nexovo_view"] = "console"
            st.rerun()
    with h3:
        if st.button("View pricing", use_container_width=True, key="hero_pricing"):
            st.session_state["nexovo_view"] = "pricing"
            st.rerun()
    with h4:
        if st.button("ROI & contact", use_container_width=True, key="hero_contact"):
            st.session_state["nexovo_view"] = "contact"
            st.rerun()

    st.markdown("<div class='scene-3d'>", unsafe_allow_html=True)
    st.markdown(
        """
<div class='hero'>
  <p class='hero-title'>Nexovo Helling Cloud Platform</p>
  <p class='hero-sub'>Building scalable digital systems for the next generation.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption("Interactive 3D globe — move the pointer to explore.")
    components.html(THREE_GLOBE_HTML, height=320, scrolling=False)
    st.markdown(
        """
<div class='node-wrap'>
  <svg class='node-svg' viewBox='0 0 960 150' width='100%' height='150' xmlns='http://www.w3.org/2000/svg'>
    <defs>
      <linearGradient id='lg1' x1='0%' y1='0%' x2='100%' y2='0%'>
        <stop offset='0%' style='stop-color:#38bdf8;stop-opacity:0.35'/>
        <stop offset='50%' style='stop-color:#818cf8;stop-opacity:0.95'/>
        <stop offset='100%' style='stop-color:#22d3ee;stop-opacity:0.45'/>
      </linearGradient>
      <filter id='nexovoGlow' x='-40%' y='-40%' width='180%' height='180%'>
        <feGaussianBlur stdDeviation='2.2' result='b'/>
        <feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge>
      </filter>
    </defs>
    <line class='n-line' x1='80' y1='70' x2='280' y2='40' stroke='url(#lg1)' stroke-width='2.5' filter='url(#nexovoGlow)'/>
    <line class='n-line' x1='280' y1='40' x2='480' y2='72' stroke='url(#lg1)' stroke-width='2.5' filter='url(#nexovoGlow)'/>
    <line class='n-line' x1='480' y1='72' x2='690' y2='38' stroke='url(#lg1)' stroke-width='2.5' filter='url(#nexovoGlow)'/>
    <line class='n-line' x1='480' y1='72' x2='850' y2='94' stroke='url(#lg1)' stroke-width='2.5' filter='url(#nexovoGlow)'/>
    <circle class='n-node n-d1' cx='80' cy='70' r='11' fill='#0ea5e9' filter='url(#nexovoGlow)'/>
    <circle class='n-node n-d2' cx='280' cy='40' r='12' fill='#6366f1' filter='url(#nexovoGlow)'/>
    <circle class='n-node n-d3' cx='480' cy='72' r='14' fill='#22d3ee' filter='url(#nexovoGlow)'/>
    <circle class='n-node n-d4' cx='690' cy='38' r='11' fill='#0ea5e9' filter='url(#nexovoGlow)'/>
    <circle class='n-node n-d5' cx='850' cy='94' r='12' fill='#6366f1' filter='url(#nexovoGlow)'/>
  </svg>
</div>
<div class='feature-grid'>
  <div class='feature'><b>Real-Time Intelligence</b><br/>Actionable signal detection for smarter decisions.</div>
  <div class='feature'><b>AI RCA</b><br/>Correlate metrics, logs, and events in seconds.</div>
  <div class='feature'><b>Seamless Integration</b><br/>Slack, Jira, and email webhooks for every escalation.</div>
  <div class='feature'><b>Measurable Impact</b><br/>Track remediation success and operational ROI.</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    render_plan_cards("_home")

    c1, c2 = st.columns(2)
    with c1:
        st.link_button(
            "Book a strategy call",
            "https://technexovo.com/contact",
            use_container_width=True,
            type="primary",
        )
    with c2:
        st.link_button("Visit technexovo.com", "https://technexovo.com", use_container_width=True)

    st.markdown(
        """
<div class='steps'>
  <b>How it works:</b><br/>
  1) Observe metrics/logs/events &rarr; 2) Detect anomaly &rarr; 3) RCA &rarr; 4) Safe remediation &rarr; 5) Learn and improve
</div>
""",
        unsafe_allow_html=True,
    )

if show_marketing and view == "pricing":
    st.markdown(
        """
<div class='mini-hero'>
  <h2>Pricing that matches your stage</h2>
  <p>Start small, prove ROI, then scale autonomous remediation with enterprise guardrails.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    render_plan_cards("_price")
    st.markdown("### Frequently asked questions")
    with st.expander("What is included in the Growth plan?"):
        st.write(
            "Full anomaly detection, RCA correlation, remediation playbooks, audit timeline, "
            "and webhook integrations for Slack, Jira, and email-style HTTPS endpoints."
        )
    with st.expander("Do you support SOC2 / enterprise security reviews?"):
        st.write(
            "The platform is designed for audit trails, RBAC-style ownership, and encrypted outbound webhooks. "
            "Enterprise packages include dedicated security and compliance alignment."
        )
    with st.expander("Can we run a pilot?"):
        st.write("Yes. Book a demo and we will align a pilot scope and success metrics with your team.")
    st.link_button(
        "Book a demo — talk to sales",
        "https://technexovo.com/contact",
        use_container_width=True,
        type="primary",
    )

if show_marketing and view == "contact":
    st.markdown(
        """
<div class='section-label'>Talk to us</div>
<h2 style='margin-top:0;'>Book a demo, contact sales, or estimate ROI</h2>
<p style='opacity:0.88;'>Use the calculator to frame a business case. All figures are illustrative; we will validate with your data.</p>
""",
        unsafe_allow_html=True,
    )
    st.markdown("### ROI estimator")
    r1, r2 = st.columns(2)
    with r1:
        monthly_incidents = st.slider(
            "P1/P2 incidents per month", 1, 80, 14, help="Major incidents that trigger on-call response."
        )
        mttr_before_h = st.slider("Median MTTR today (hours)", 0.25, 12.0, 1.5, 0.25)
    with r2:
        hourly_cost = st.slider(
            "Fully loaded cost per incident hour (USD)", 75, 500, 180)
        mttr_after_h = st.slider(
            "Expected MTTR with Nexovo (hours)", 0.1, 6.0, 0.35, 0.05,
            help="Conservative improvement from faster RCA and automation.",
        )
    hours_saved = monthly_incidents * max(0.0, (mttr_before_h - mttr_after_h))
    monthly_savings = hours_saved * hourly_cost
    annual_savings = monthly_savings * 12
    st.markdown(
        f"""
<div class='roi-panel'>
  <h3>Estimated operational impact</h3>
  <p class='sub'>Hours saved per month: <b>{hours_saved:.1f}</b> · Monthly value: <b>${monthly_savings:,.0f}</b></p>
  <div class='roi-big'>${annual_savings:,.0f}</div>
  <p style='margin:0; opacity:0.85;'>Illustrative annual savings from reduced response time (before/after MTTR).</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='section-label' style='margin-top:18px;'>Next steps</div>", unsafe_allow_html=True)
    s1, s2 = st.columns(2)
    with s1:
        st.markdown(
            """
<div class='sales-card'>
  <h4>Book a demo</h4>
  <p>Walk through detection, RCA, remediation, and integrations with your stakeholders.</p>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button(
            "Schedule on technexovo.com",
            "https://technexovo.com/contact",
            use_container_width=True,
            type="primary",
        )
    with s2:
        st.markdown(
            """
<div class='sales-card'>
  <h4>Contact sales</h4>
  <p>Enterprise pricing, pilots, security reviews, and custom deployment options.</p>
</div>
""",
            unsafe_allow_html=True,
        )
        st.link_button(
            "Contact sales",
            "https://technexovo.com/contact",
            use_container_width=True,
        )
    if st.button("Open live console", use_container_width=True, key="contact_open_console"):
        st.session_state["nexovo_view"] = "console"
        st.rerun()

if show_marketing and view == "console":
    st.info("Operations console below — run detection, manage incidents, and review audit trail.")


def get_json(path: str):
    return httpx.get(f"{API_BASE}{path}", timeout=10.0).json()


def check_backend_online() -> bool:
    try:
        resp = httpx.get(f"{API_BASE}/health", timeout=8.0)
        if resp.status_code == 200:
            return True
    except Exception:
        pass
    try:
        # Fallback probe because some hosted free-tier setups may intermittently
        # return 404 on /health during cold starts while API routes are available.
        resp = httpx.get(f"{API_BASE}/v1/incidents", timeout=8.0)
        return resp.status_code == 200
    except Exception:
        return False


def synthetic_incident(service: str, namespace: str, cpu: int, memory: int, error_rate: float, latency: int):
    sev = "low"
    if error_rate > 5 or latency > 850:
        sev = "critical"
    elif error_rate > 3 or cpu > 90 or memory > 90:
        sev = "high"
    elif error_rate > 1.5 or latency > 450:
        sev = "medium"
    return {
        "id": str(uuid.uuid4()),
        "service": service,
        "severity": sev,
        "confidence": min(0.99, max(0.2, (error_rate + cpu / 30.0) / 10.0)),
        "hypothesis": "Simulated RCA: probable saturation or dependency latency.",
        "recommended_action": "scale_deployment" if cpu > 90 else "restart_pod",
        "executed": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "namespace": namespace,
            "cpu": f"{cpu:.2f}",
            "memory": f"{memory:.2f}",
            "error_rate": f"{error_rate:.2f}",
            "latency_ms": f"{latency:.2f}",
        },
    }


def incident_runbook(incident: dict) -> list[str]:
    severity = incident.get("severity", "low")
    action = incident.get("recommended_action", "notify_human")
    service = incident.get("service", "service")
    steps = [
        f"Validate impacted service `{service}` and confirm scope in namespace.",
        "Check last deployment and configuration changes in previous 30 minutes.",
        "Correlate p95 latency, error-rate, and pod health to confirm root cause.",
    ]
    if action == "rollback_deployment":
        steps.append("Trigger rollback to previous stable version and monitor 5-minute SLO recovery.")
    elif action == "scale_deployment":
        steps.append("Scale replicas and verify queue depth and CPU return below saturation thresholds.")
    elif action == "restart_pod":
        steps.append("Restart unhealthy pods in rolling manner and verify no spike in 5xx responses.")
    else:
        steps.append("Escalate to on-call engineer and capture diagnostics bundle.")
    if severity in {"high", "critical"}:
        steps.append("Open incident bridge, assign incident commander, and post updates every 10 minutes.")
    return steps


def reliability_score(incidents_count: int, critical_count: int, success_rate: float) -> float:
    base = 100.0
    penalty = (incidents_count * 1.2) + (critical_count * 4.0) + ((100.0 - success_rate) * 0.2)
    return max(0.0, min(100.0, base - penalty))


def in_selected_window(iso_timestamp: str, window: str) -> bool:
    if window == "all_time":
        return True
    if not iso_timestamp:
        return False
    try:
        event_time = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta_map = {
            "last_1h": timedelta(hours=1),
            "last_6h": timedelta(hours=6),
            "last_24h": timedelta(hours=24),
            "last_7d": timedelta(days=7),
        }
        return event_time >= (now - delta_map.get(window, timedelta(hours=24)))
    except Exception:
        return True


def incident_sla_minutes(severity: str) -> int:
    mapping = {"critical": 15, "high": 30, "medium": 60, "low": 120}
    return mapping.get(str(severity).lower(), 60)


def incident_age_minutes(iso_timestamp: str) -> float:
    try:
        event_time = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return max(0.0, (now - event_time).total_seconds() / 60.0)
    except Exception:
        return 0.0


status_col, _, endpoint_col = st.columns([1, 0.2, 2])
demo_mode = False
with status_col:
    if check_backend_online():
        health = {"status": "ok"}
        st.success("Orchestrator Online")
    else:
        health = {"status": "unreachable"}
        demo_mode = True
        st.warning("Orchestrator Offline (Dashboard running in demo mode)")
        st.caption(
            "To switch to live mode, deploy orchestrator API on Render and set Streamlit secret `ORCHESTRATOR_URL` to that public URL."
        )
with endpoint_col:
    st.markdown(
        f"<div class='card'><b>Control plane API:</b> {API_BASE}<br><b>Status:</b> {health.get('status', 'unknown')}<div class='tiny'>Orchestrator endpoint for detection, remediation, and audit.</div></div>",
        unsafe_allow_html=True,
    )

if show_marketing and st.session_state.get("nexovo_view") == "integrations":
    st.markdown("### Webhook integrations")
    st.caption(
        "Configure outbound webhooks for **acknowledgment** and **escalation** events. "
        "Slack: Incoming Webhook URL. Jira: Automation incoming webhook. "
        "Email: any HTTPS endpoint (Zapier, Make, SendGrid, etc.)."
    )
    if "demo_webhook_cfg" not in st.session_state:
        st.session_state["demo_webhook_cfg"] = {
            "slack_webhook_url": "",
            "jira_webhook_url": "",
            "email_webhook_url": "",
            "notify_on_ack": True,
            "notify_on_escalate": True,
        }
    if not demo_mode and not st.session_state.get("_webhook_hydrated"):
        try:
            remote_cfg = httpx.get(f"{API_BASE}/v1/integrations/webhooks", timeout=10.0).json()
            st.session_state["demo_webhook_cfg"] = remote_cfg
        except Exception:
            pass
        st.session_state["_webhook_hydrated"] = True

    cfg = st.session_state["demo_webhook_cfg"]
    slack_u = st.text_input("Slack Incoming Webhook URL", value=cfg.get("slack_webhook_url", "") or "")
    jira_u = st.text_input("Jira / generic webhook URL", value=cfg.get("jira_webhook_url", "") or "")
    email_u = st.text_input("Email relay webhook URL (HTTPS)", value=cfg.get("email_webhook_url", "") or "")
    n_ack = st.toggle("Notify on acknowledge", value=bool(cfg.get("notify_on_ack", True)))
    n_esc = st.toggle("Notify on escalate", value=bool(cfg.get("notify_on_escalate", True)))

    if st.button("Save integration settings", type="primary", key="save_webhooks"):
        payload = {
            "slack_webhook_url": slack_u,
            "jira_webhook_url": jira_u,
            "email_webhook_url": email_u,
            "notify_on_ack": n_ack,
            "notify_on_escalate": n_esc,
        }
        st.session_state["demo_webhook_cfg"] = payload
        if demo_mode:
            st.success("Saved locally (demo mode). Webhooks fire only when connected to live API.")
        else:
            try:
                r = httpx.put(f"{API_BASE}/v1/integrations/webhooks", json=payload, timeout=15.0)
                r.raise_for_status()
                st.success("Saved to orchestrator — ack/escalate will notify these endpoints.")
            except Exception as exc:
                st.error(f"Save failed: {exc}")

if show_marketing and view in ("home", "pricing", "contact", "integrations"):
    st.divider()
    st.markdown("### Live operations console")
    st.caption(
        "KPIs, incident feed, simulator, and intelligence toolkit — scroll to explore without switching tabs."
    )

st.markdown("<div class='console-shell'>", unsafe_allow_html=True)

try:
    incidents = get_json("/v1/incidents")
except Exception:
    incidents = []

try:
    actions = get_json("/v1/actions")
except Exception:
    actions = []

try:
    audit_events = get_json("/v1/audit")
except Exception:
    audit_events = []

if demo_mode and "demo_incidents" not in st.session_state:
    st.session_state["demo_incidents"] = []
if demo_mode and "demo_actions" not in st.session_state:
    st.session_state["demo_actions"] = []
if demo_mode and "demo_audit" not in st.session_state:
    st.session_state["demo_audit"] = []
if demo_mode and "demo_comments" not in st.session_state:
    st.session_state["demo_comments"] = {}
if demo_mode:
    incidents = st.session_state["demo_incidents"]
    actions = st.session_state["demo_actions"]
    audit_events = st.session_state.get("demo_audit", [])

incidents = [i for i in incidents if in_selected_window(i.get("created_at", ""), selected_window)]
actions = [a for a in actions if in_selected_window(a.get("created_at", ""), selected_window)]

if selected_service.strip():
    incidents = [i for i in incidents if i.get("service", "").lower() == selected_service.strip().lower()]

if selected_severity != "all":
    incidents = [i for i in incidents if i.get("severity") == selected_severity]

if only_open:
    incidents = [
        i for i in incidents if i.get("metadata", {}).get("acknowledged", "false").lower() != "true"
    ]

crit_count = sum(1 for i in incidents if i.get("severity") == "critical")
success_count = sum(1 for a in actions if a.get("success"))
success_rate = (success_count / len(actions) * 100) if actions else 0.0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Active Incidents", len(incidents))
kpi2.metric("Critical Incidents", crit_count)
kpi3.metric("Remediation Actions", len(actions))
kpi4.metric("Action Success Rate", f"{success_rate:.1f}%")

if incidents:
    tdf = pd.DataFrame(incidents)[["created_at", "severity", "confidence"]].copy()
    tdf["created_at"] = pd.to_datetime(tdf["created_at"], errors="coerce")
    tdf = tdf.dropna(subset=["created_at"]).sort_values("created_at")
    if not tdf.empty:
        tdf["incident_count"] = 1
        tdf["critical_count"] = (tdf["severity"] == "critical").astype(int)
        trend = tdf.set_index("created_at")[["incident_count", "critical_count", "confidence"]]
        st.markdown("#### KPI Trends")
        st.line_chart(trend)

cpu_avg = 0.0
mem_avg = 0.0
err_avg = 0.0
if incidents:
    cpu_vals = [float(i.get("metadata", {}).get("cpu", 0.0)) for i in incidents if i.get("metadata")]
    mem_vals = [float(i.get("metadata", {}).get("memory", 0.0)) for i in incidents if i.get("metadata")]
    err_vals = [float(i.get("metadata", {}).get("error_rate", 0.0)) for i in incidents if i.get("metadata")]
    cpu_avg = sum(cpu_vals) / len(cpu_vals) if cpu_vals else 0.0
    mem_avg = sum(mem_vals) / len(mem_vals) if mem_vals else 0.0
    err_avg = sum(err_vals) / len(err_vals) if err_vals else 0.0

g1, g2, g3 = st.columns(3)
with g1:
    gauge("CPU Load Gauge", cpu_avg)
with g2:
    gauge("Memory Load Gauge", mem_avg)
with g3:
    gauge("Error Rate Gauge", err_avg, max_value=20.0)

left, right = st.columns([2.2, 1.2], gap="large")

with right:
    st.markdown("### Simulate Production Signal")
    st.caption("Use this simulator to mimic real incidents and watch automated RCA/action flow.")
    st.caption("Tip: set CPU > 90 and Error Rate > 5 to emulate high-severity incidents.")
    with st.container(border=True):
        service = st.text_input("Service", value="checkout-service")
        namespace = st.text_input("Namespace", value="prod")
        cpu = st.slider("CPU %", 1, 100, 78)
        memory = st.slider("Memory %", 1, 100, 72)
        error_rate = st.slider("Error Rate %", 0.0, 20.0, 2.2)
        latency = st.slider("p95 Latency (ms)", 30, 2000, 460)
        log_errors = st.slider("Log Error Count", 0, 250, 22)
        deploy_changed = st.checkbox("Deployment changed in last 15m", value=False)

        if st.button("Run Detection and Remediation", type="primary", use_container_width=True):
            payload = {
                "service": service,
                "namespace": namespace,
                "cpu": cpu,
                "memory": memory,
                "error_rate": error_rate,
                "p95_latency_ms": latency,
                "log_error_count": log_errors,
                "deploy_changed_last_15m": deploy_changed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if demo_mode:
                incident = synthetic_incident(
                    service=service,
                    namespace=namespace,
                    cpu=cpu,
                    memory=memory,
                    error_rate=error_rate,
                    latency=latency,
                )
                action = {
                    "action": incident["recommended_action"],
                    "success": True,
                    "message": "Demo mode remediation executed locally in dashboard.",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                audit = {
                    "id": str(uuid.uuid4()),
                    "incident_id": incident["id"],
                    "event_type": "remediation_executed",
                    "actor": "demo-system",
                    "message": f"Executed {incident['recommended_action']} in demo mode",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                st.session_state["demo_incidents"] = [incident] + st.session_state["demo_incidents"]
                st.session_state["demo_actions"] = [action] + st.session_state["demo_actions"]
                st.session_state["demo_audit"] = [audit] + st.session_state["demo_audit"]
                st.success("Demo signal processed (no backend needed).")
                with st.expander("Detection Response", expanded=True):
                    st.json({"incident": incident, "action_result": action, "mode": "demo"})
            else:
                try:
                    resp = httpx.post(f"{API_BASE}/v1/detect", json=payload, timeout=10.0)
                    resp.raise_for_status()
                    data = resp.json()
                    st.success("Signal processed successfully.")
                    with st.expander("Detection Response", expanded=True):
                        st.json(data)
                except Exception as exc:
                    st.error(f"Failed to call orchestrator: {exc}")

with left:
    st.markdown("### Incident Feed")
    if incidents:
        df = pd.DataFrame(incidents)[
            [
                "id",
                "service",
                "severity",
                "confidence",
                "hypothesis",
                "recommended_action",
                "executed",
                "created_at",
            ]
        ]
        df["age_min"] = df["created_at"].map(incident_age_minutes).round(1)
        df["sla_min"] = df["severity"].map(incident_sla_minutes)
        df["sla_breached"] = df["age_min"] > df["sla_min"]
        df["confidence"] = df["confidence"].map(lambda x: f"{x:.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)

        sev_df = (
            pd.DataFrame(incidents)["severity"]
            .value_counts()
            .rename_axis("severity")
            .reset_index(name="count")
        )
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("#### Severity Distribution")
            st.bar_chart(sev_df.set_index("severity"))
        with chart_col2:
            st.markdown("#### Confidence Trend")
            conf_df = pd.DataFrame(incidents)[["created_at", "confidence"]].copy()
            conf_df["created_at"] = pd.to_datetime(conf_df["created_at"], errors="coerce")
            conf_df = conf_df.sort_values("created_at")
            conf_df = conf_df.set_index("created_at")
            st.line_chart(conf_df)

        latest = incidents[0]
        sev = latest.get("severity", "low")
        breached = int(
            sum(
                1
                for item in incidents
                if incident_age_minutes(item.get("created_at", ""))
                > incident_sla_minutes(item.get("severity", "medium"))
            )
        )
        acked = int(
            sum(
                1
                for item in incidents
                if item.get("metadata", {}).get("acknowledged", "false").lower() == "true"
            )
        )
        b1, b2, b3 = st.columns(3)
        b1.metric("SLA Breaches", breached)
        b2.metric("Acknowledged", acked)
        b3.metric("Unacknowledged", max(0, len(incidents) - acked))
        st.markdown(
            f"<div class='card'><b>Latest RCA:</b> {latest.get('hypothesis', 'n/a')}<br><b>Severity:</b> <span class='sev-{sev}'>{sev.upper()}</span><br><b>Recommended Action:</b> {latest.get('recommended_action', 'n/a')}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("### Incident Drill-down")
        incident_options = {
            f"{item.get('service','unknown')} | {item.get('severity','low')} | {item.get('id','')}": item
            for item in incidents[:25]
        }
        selected_key = st.selectbox("Select incident", list(incident_options.keys()))
        selected_incident = incident_options[selected_key]
        owner_default = selected_incident.get("metadata", {}).get("owner", "sre-oncall")
        owner_value = st.text_input("Incident owner", value=owner_default)
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("Acknowledge Incident", use_container_width=True):
                if demo_mode:
                    selected_incident.setdefault("metadata", {})["acknowledged"] = "true"
                    st.session_state["demo_audit"] = [
                        {
                            "id": str(uuid.uuid4()),
                            "incident_id": selected_incident.get("id", ""),
                            "event_type": "acknowledged",
                            "actor": "demo-user",
                            "message": "Incident acknowledged in demo mode",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    ] + st.session_state["demo_audit"]
                    st.success("Incident acknowledged in demo mode.")
                else:
                    try:
                        r = httpx.post(
                            f"{API_BASE}/v1/incidents/{selected_incident.get('id')}/ack", timeout=10.0
                        )
                        r.raise_for_status()
                        st.success("Incident acknowledged.")
                    except Exception as exc:
                        st.error(f"Acknowledge failed: {exc}")
        with action_col2:
            if st.button("Escalate to On-call", use_container_width=True):
                if demo_mode:
                    selected_incident.setdefault("metadata", {})["escalated"] = "true"
                    selected_incident["metadata"]["escalated_to"] = "sre-oncall"
                    st.session_state["demo_audit"] = [
                        {
                            "id": str(uuid.uuid4()),
                            "incident_id": selected_incident.get("id", ""),
                            "event_type": "escalated",
                            "actor": "demo-user",
                            "message": "Incident escalated to sre-oncall in demo mode",
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    ] + st.session_state["demo_audit"]
                    st.warning("Incident escalated in demo mode.")
                else:
                    try:
                        r = httpx.post(
                            f"{API_BASE}/v1/incidents/{selected_incident.get('id')}/escalate", timeout=10.0
                        )
                        r.raise_for_status()
                        st.warning("Incident escalated to on-call.")
                    except Exception as exc:
                        st.error(f"Escalation failed: {exc}")
        if st.button("Assign Owner", use_container_width=True):
            if demo_mode:
                selected_incident.setdefault("metadata", {})["owner"] = owner_value
                st.session_state["demo_audit"] = [
                    {
                        "id": str(uuid.uuid4()),
                        "incident_id": selected_incident.get("id", ""),
                        "event_type": "owner_assigned",
                        "actor": "demo-user",
                        "message": f"Assigned owner {owner_value} in demo mode",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                ] + st.session_state["demo_audit"]
                st.success(f"Assigned to {owner_value} (demo mode).")
            else:
                try:
                    r = httpx.post(
                        f"{API_BASE}/v1/incidents/{selected_incident.get('id')}/assign",
                        json={"owner": owner_value, "actor": "dashboard-user"},
                        timeout=10.0,
                    )
                    r.raise_for_status()
                    st.success(f"Assigned to {owner_value}.")
                except Exception as exc:
                    st.error(f"Owner assignment failed: {exc}")

        st.markdown("#### Incident comment thread")
        iid = selected_incident.get("id", "")
        if demo_mode:
            thread = list(st.session_state["demo_comments"].get(iid, []))
        else:
            try:
                thread = httpx.get(f"{API_BASE}/v1/incidents/{iid}/comments", timeout=10.0).json()
            except Exception:
                thread = []
        for c in thread[-50:]:
            ts = c.get("created_at", "")
            author = c.get("author", "user")
            body = c.get("body", "")
            st.markdown(f"**{author}** · `{ts}`  \n{body}")
            st.divider()
        c_author = st.text_input("Your name", value="operator", key=f"ct_auth_{iid}")
        c_body = st.text_area("Add a comment", key=f"ct_body_{iid}", height=90)
        if st.button("Post comment", key=f"ct_post_{iid}"):
            if not c_body.strip():
                st.warning("Enter comment text.")
            elif demo_mode:
                entry = {
                    "id": str(uuid.uuid4()),
                    "incident_id": iid,
                    "author": c_author,
                    "body": c_body.strip(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                st.session_state["demo_comments"].setdefault(iid, []).append(entry)
                st.session_state["demo_audit"] = [
                    {
                        "id": str(uuid.uuid4()),
                        "incident_id": iid,
                        "event_type": "comment_added",
                        "actor": c_author,
                        "message": c_body.strip()[:200],
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                ] + st.session_state.get("demo_audit", [])
                st.success("Comment added.")
                st.rerun()
            else:
                try:
                    httpx.post(
                        f"{API_BASE}/v1/incidents/{iid}/comments",
                        json={"author": c_author, "body": c_body.strip()},
                        timeout=10.0,
                    ).raise_for_status()
                    st.success("Comment posted.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Comment failed: {exc}")

        with st.expander("Detailed incident context", expanded=False):
            st.json(selected_incident)
    else:
        st.info("No incidents yet. Send a signal from the right panel.")

    st.markdown("### Remediation Timeline")
    if actions:
        adf = pd.DataFrame(actions)[["action", "success", "message", "created_at"]]
        adf["success"] = adf["success"].map(lambda x: "Success" if x else "Blocked")
        st.dataframe(adf, use_container_width=True, hide_index=True)
        action_stats = pd.DataFrame(actions)["action"].value_counts().reset_index()
        action_stats.columns = ["action", "count"]
        st.markdown("#### Action Mix")
        st.area_chart(action_stats.set_index("action"))
    else:
        st.info("No remediation actions recorded yet.")

st.markdown("## Operations Intelligence Toolkit")
ops_tab, runbook_tab, planner_tab, architecture_tab, audit_tab = st.tabs(
    [
        "Service Intelligence",
        "Runbook Assistant",
        "Scenario Planner",
        "Architecture Map",
        "Audit Timeline",
    ]
)

with ops_tab:
    if incidents:
        idf = pd.DataFrame(incidents)
        if "created_at" in idf.columns:
            idf["created_at"] = pd.to_datetime(idf["created_at"], errors="coerce")
        svc = (
            idf.groupby("service", as_index=False)
            .agg(
                incidents=("id", "count"),
                avg_confidence=("confidence", "mean"),
                critical=("severity", lambda s: int((s == "critical").sum())),
            )
            .sort_values(["incidents", "critical"], ascending=False)
        )
        svc["avg_confidence"] = svc["avg_confidence"].fillna(0.0).map(lambda x: round(float(x), 2))
        st.markdown("### Service Leaderboard")
        st.dataframe(svc, use_container_width=True, hide_index=True)

        left_ops, right_ops = st.columns(2)
        with left_ops:
            st.markdown("#### Incident Volume by Service")
            st.bar_chart(svc.set_index("service")[["incidents"]])
        with right_ops:
            st.markdown("#### Critical Incidents by Service")
            st.bar_chart(svc.set_index("service")[["critical"]])
    else:
        st.info("No incidents available for service intelligence yet.")

    export_col1, export_col2 = st.columns(2)
    with export_col1:
        if incidents:
            incident_csv = pd.DataFrame(incidents).to_csv(index=False)
            st.download_button(
                "Export Incidents CSV",
                data=incident_csv,
                file_name="nexovo_incidents.csv",
                mime="text/csv",
                use_container_width=True,
            )
    with export_col2:
        if actions:
            action_csv = pd.DataFrame(actions).to_csv(index=False)
            st.download_button(
                "Export Actions CSV",
                data=action_csv,
                file_name="nexovo_actions.csv",
                mime="text/csv",
                use_container_width=True,
            )

with runbook_tab:
    st.markdown("### AI-Guided Incident Runbook")
    if incidents:
        runbook_options = {
            f"{item.get('service','unknown')} | {item.get('severity','low')} | {item.get('id','')}": item
            for item in incidents[:25]
        }
        rb_key = st.selectbox("Choose incident for runbook", list(runbook_options.keys()))
        rb_incident = runbook_options[rb_key]
        steps = incident_runbook(rb_incident)
        for idx, step in enumerate(steps, start=1):
            st.markdown(f"{idx}. {step}")
        st.code(
            f"RCA: {rb_incident.get('hypothesis', 'N/A')}\n"
            f"Recommended Action: {rb_incident.get('recommended_action', 'N/A')}\n"
            f"Confidence: {rb_incident.get('confidence', 0):.2f}"
        )
    else:
        st.info("Generate or ingest incidents to enable runbook assistant.")

with planner_tab:
    st.markdown("### Capacity and Risk Planner")
    p_col1, p_col2, p_col3 = st.columns(3)
    with p_col1:
        projected_qps = st.slider("Projected QPS spike (%)", 0, 300, 80)
    with p_col2:
        current_error = st.slider("Current error rate (%)", 0.0, 20.0, 2.0)
    with p_col3:
        headroom = st.slider("Infra headroom (%)", 0, 100, 35)

    risk_score = (projected_qps * 0.45) + (current_error * 8.0) - (headroom * 0.4)
    risk_score = max(0.0, min(100.0, risk_score))
    st.metric("Predicted Incident Risk", f"{risk_score:.1f}%")
    if risk_score >= 70:
        st.error("High projected risk. Prepare scale-up + rollback guardrails.")
    elif risk_score >= 40:
        st.warning("Moderate risk. Recommend canary release and tighter alerting.")
    else:
        st.success("Risk is manageable under current assumptions.")

    rel = reliability_score(len(incidents), crit_count, success_rate)
    st.metric("Platform Reliability Score", f"{rel:.1f}/100")
    st.caption("Score combines incident load, critical events, and remediation success rate.")

with architecture_tab:
    st.markdown("### Self-Healing System Map")
    st.graphviz_chart(
        """
digraph G {
    rankdir=LR;
    node [shape=box, style=rounded];
    Traffic -> "Kubernetes Services";
    "Kubernetes Services" -> Prometheus;
    "Kubernetes Services" -> "Log Pipeline";
    Prometheus -> "Detection Engine";
    "Log Pipeline" -> "RCA Correlator";
    "Detection Engine" -> "Decision Engine";
    "RCA Correlator" -> "Decision Engine";
    "Decision Engine" -> "Remediation Executor";
    "Remediation Executor" -> "Kubernetes Services";
    "Decision Engine" -> "Nexovo Dashboard";
}
"""
    )
    st.markdown("### SLO Snapshot")
    slo_df = pd.DataFrame(
        [
            {"SLI": "Availability", "Target": "99.9%", "Current": "99.7%"},
            {"SLI": "p95 Latency", "Target": "< 250ms", "Current": "232ms"},
            {"SLI": "Error Rate", "Target": "< 1.0%", "Current": "0.8%"},
            {"SLI": "MTTR", "Target": "< 15 min", "Current": "11 min"},
        ]
    )
    st.dataframe(slo_df, use_container_width=True, hide_index=True)

with audit_tab:
    st.markdown("### Incident Audit Timeline")
    if audit_events:
        adf = pd.DataFrame(audit_events)[
            ["created_at", "incident_id", "event_type", "actor", "message"]
        ].copy()
        adf["created_at"] = pd.to_datetime(adf["created_at"], errors="coerce")
        adf = adf.sort_values("created_at", ascending=False)
        st.dataframe(adf, use_container_width=True, hide_index=True)
    else:
        st.info("No audit events yet. Perform acknowledge/escalate/assign actions to populate timeline.")

st.markdown("</div>", unsafe_allow_html=True)

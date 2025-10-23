# app_streamlit_reloj.py
# Ejecuta:
#   python -m streamlit run app_streamlit_reloj.py --server.port 8502
# Requisito Windows (zona horaria IANA):  pip install tzdata

from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Optional, List, Tuple
import base64, json, math
import streamlit as st
import streamlit.components.v1 as components

# --------------------------- Configurable ---------------------------
TIMEZONES: List[Tuple[str, str]] = [
    ("Chile (Santiago)", "America/Santiago"),
    ("España (Madrid)", "Europe/Madrid"),
    ("México (Ciudad de México)", "America/Mexico_City"),
    ("EE. UU. (Houston)", "America/Chicago"),
]

PAGE_TITLE = "Reloj Multizona"
DIGITAL_STACK = "'DS-Digital','Digital-7','Segment7Standard','Share Tech Mono','Consolas','Courier New',monospace"

# GIFs opcionales (mismos índices que TIMEZONES). Deja "" para omitir.
GIF_PATHS = [
    r"assets\mascota1.gif",
    r"assets\mascota2.gif",
    r"assets\mascota3.gif",
    r"assets\mascota4.gif",
]
GIF_SIZE_PX  = 64
GIF_MINI_PX  = 24

# --------------------------- Helpers ---------------------------
@st.cache_data(show_spinner=False)
def _file_to_data_uri(path_str: str) -> Optional[str]:
    try:
        if not path_str:
            return None
        p = Path(path_str)
        if not p.is_file():
            return None
        return "data:image/gif;base64," + base64.b64encode(p.read_bytes()).decode("ascii")
    except Exception:
        return None

def _zones_payload():
    out = []
    for i, (label, tz) in enumerate(TIMEZONES):
        out.append({"label": label, "tz": tz, "gif": _file_to_data_uri(GIF_PATHS[i]) if i < len(GIF_PATHS) else None})
    return out

# --------------------------- UI (Streamlit) ---------------------------
st.set_page_config(page_title=PAGE_TITLE, page_icon="🕒", layout="wide")

st.markdown(f"<h2 style='margin:0'>{PAGE_TITLE}</h2>", unsafe_allow_html=True)
st.markdown("<p style='margin:.25rem 0 1rem;color:#aab3c5'>Chile, España, México y EE. UU. — sin recargar la página.</p>",
            unsafe_allow_html=True)

# Controles
show_mini = st.checkbox("Mostrar versión mini", value=True)
fixed_cols = st.number_input("Columnas mini (desktop)", min_value=1, max_value=4, value=2, step=1, help="Solo afecta escritorio; en móvil cae a 1 columna.")
zones_json = json.dumps(_zones_payload(), ensure_ascii=False)

# --------------------------- HTML + CSS + JS (client only tick) ---------------------------
css = f"""
:root {{
  --bg:#0a0c14; --card:#111523; --led-green:#35e04f; --led-red:#ff3b3b; --text-dim:#aab3c5;
}}
* {{ box-sizing:border-box }}
html,body {{ background:var(--bg); color:#fff; font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif }}
.container {{ padding: 0 .25rem .5rem .25rem; }}
.grid {{
  display:grid; grid-template-columns:repeat(auto-fit,minmax(clamp(220px,40vw,440px),1fr));
  gap:clamp(8px,2vw,16px); align-items:stretch;
}}
.card {{
  background:linear-gradient(180deg,var(--card),#0c1020); border:1px solid #1e2640; border-radius:18px;
  padding:18px; box-shadow:0 8px 24px rgba(0,0,0,.35), inset 0 0 24px rgba(22,28,56,.45);
}}
.row {{ display:flex; align-items:center; justify-content:space-between; gap:12px }}
.city {{
  color:var(--led-green); font-family:{DIGITAL_STACK}; font-weight:700; letter-spacing:.5px;
  font-size:1.1rem; margin:0 0 6px 4px; text-transform:capitalize; text-shadow:0 0 10px rgba(53,224,79,.45);
}}
.time {{
  color:var(--led-red); font-family:{DIGITAL_STACK}; font-weight:900; line-height:1;
  font-size: clamp(1.8rem,6vw,3.6rem); letter-spacing:1px;
  text-shadow:0 0 14px rgba(255,59,59,.5),0 0 30px rgba(255,59,59,.2);
}}
.date {{ color:var(--text-dim); font-size:.95rem; margin-left:4px }}
.pet img {{ width:clamp(32px,8vw,{GIF_SIZE_PX}px); height:auto; border-radius:8px; box-shadow:0 4px 14px rgba(0,0,0,.35) }}

.mini-wrap {{ margin-top:10px }}
.mini-title {{ color:var(--text-dim); font-size:.9rem; margin:6px 0 }}
.mini-grid {{ display:grid; grid-template-columns:repeat({{fixed_cols}}, minmax(0,1fr)); gap:8px }}
@media (max-width: 520px) {{ .mini-grid {{ grid-template-columns: 1fr; }} }}
.mini-card {{
  background:linear-gradient(180deg,#0f1324,#0c1020); border:1px solid #1b2340; border-radius:12px; padding:10px 12px;
  box-shadow:inset 0 0 18px rgba(22,28,56,.45);
}}
.mini-row {{ display:flex; align-items:center; justify-content:space-between; gap:6px }}
.mini-city {{ color:var(--led-green); font-family:{DIGITAL_STACK}; font-weight:700; letter-spacing:.4px; font-size:.85rem; margin:0 0 4px 2px }}
.mini-time {{
  color:var(--led-red); font-family:{DIGITAL_STACK}; font-weight:900; line-height:1; letter-spacing:1px;
  font-size: clamp(1.1rem,4.5vw,1.6rem); text-shadow:0 0 10px rgba(255,59,59,.45),0 0 18px rgba(255,59,59,.18)
}}
.mini-pet img {{ width:{GIF_MINI_PX}px; height:auto; border-radius:6px; box-shadow:0 2px 10px rgba(0,0,0,.35) }}
"""

# Ojo: doblamos llaves para que Python no intente formatearlas (JS usa ${...}).
html = f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{css}</style></head>
<body>
<div class="container">
  <div id="grid" class="grid"></div>
  {"<div class='mini-wrap'><div class='mini-title'>Versión mini</div><div id='mini-grid' class='mini-grid'></div></div>" if show_mini else ""}
</div>

<script>
const ZONES = {zones_json};

function fmtTime(tz) {{
  return new Intl.DateTimeFormat('es-ES', {{
    hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false, timeZone: tz
  }}).format(new Date());
}}
function fmtDate(tz) {{
  return new Intl.DateTimeFormat('es-ES', {{
    weekday:'short', day:'2-digit', month:'short', year:'numeric', timeZone: tz
  }}).format(new Date());
}}

function render() {{
  const grid = document.getElementById('grid'); grid.innerHTML = '';
  ZONES.forEach((z, i) => {{
    const pet = z.gif ? `<div class='pet'><img src='${{z.gif}}' alt='gif'></div>` : '';
    grid.insertAdjacentHTML('beforeend', `
      <div class="card">
        <div class="city">${{z.label}}</div>
        <div class="row">
          <div class="time" id="t-${{i}}">--:--:--</div>
          ${{pet}}
        </div>
        <div class="date" id="d-${{i}}"></div>
      </div>`);
  }});

  const mgrid = document.getElementById('mini-grid');
  if (mgrid) {{
    mgrid.innerHTML = '';
    ZONES.forEach((z, i) => {{
      const pet = z.gif ? `<div class='mini-pet'><img src='${{z.gif}}' alt='gif'></div>` : '';
      mgrid.insertAdjacentHTML('beforeend', `
        <div class="mini-card">
          <div class="mini-city">${{z.label}}</div>
          <div class="mini-row">
            <div class="mini-time" id="mt-${{i}}">--:--:--</div>
            ${{pet}}
          </div>
        </div>`);
    }});
  }}
}}

function tick() {{
  ZONES.forEach((z, i) => {{
    const t = document.getElementById('t-'+i);
    const d = document.getElementById('d-'+i);
    if (t) t.textContent = fmtTime(z.tz);
    if (d) d.textContent = fmtDate(z.tz);
    const mt = document.getElementById('mt-'+i);
    if (mt) mt.textContent = fmtTime(z.tz);
  }});
}}

document.addEventListener('DOMContentLoaded', () => {{
  render();
  tick();
  setInterval(tick, 1000);   // ← actualización en cliente, sin rerun de Python
}});
</script>
</body></html>
"""

# --- Calcular altura del iframe para que no corte la versión mini ---
BASE_H = 420            # sección normal
MINI_CARD_H = 92        # alto aprox de mini-card
MINI_GAP = 8
MINI_TITLE_H = 36
if show_mini:
    cols = max(1, int(fixed_cols))
    rows = math.ceil(len(TIMEZONES) / cols)
    height = BASE_H + MINI_TITLE_H + rows * (MINI_CARD_H + MINI_GAP) + 32
else:
    height = BASE_H

# Permite scroll por si el contenedor se hace muy estrecho (responsive).
components.html(html, height=height, scrolling=True)

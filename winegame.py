import base64, html as _html, streamlit as st, streamlit.components.v1 as components, sqlite3, pandas as pd, json, random, io
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo


def now_cl():
    return datetime.now(ZoneInfo("America/Santiago")).replace(tzinfo=None)


DB = "wine_game.db"
WINE = "#722F37"
LETTERS = "ABCDEFGHIJ"
MAX_ALTS = 10
LEVELS = ["Novato", "Aficionado", "Avanzado", "Experto", "Maestro"]  # estrellas = posicion (1 a 5)
_STAR = '<svg viewBox="0 0 24 24"%s><polygon points="12,2 15.1,8.6 22,9.3 16.8,14 18.4,21 12,17.3 5.6,21 7.2,14 2,9.3 8.9,8.6"/></svg>'

def lvl_html(n):
    """Estrellas (SVG) + nombre del nivel."""
    if not isinstance(n, str) or n not in LEVELS:
        return ""
    k = LEVELS.index(n) + 1
    st_ = "".join(_STAR % ("" if i < k else ' class="off"') for i in range(5))
    return f'<div class="lvl"><span class="stars">{st_}</span><b>Nivel {n}</b></div>'

def norm_level(v):
    """Acepta nombre (sin tildes/mayusculas) o numero 1-5. Devuelve (nivel|None, ok)."""
    if v is None or (not isinstance(v, str) and pd.isna(v)) or str(v).strip() == "":
        return None, True
    t = str(v).strip().lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    for i, L in enumerate(LEVELS):
        if t == L.lower() or t == str(i + 1) or t == f"{i + 1}.0":
            return L, True
    return None, False
try:  # fuerza el tema claro de Streamlit aunque el celular este en modo oscuro (sin config.toml)
    for _k, _v in {"theme.base": "light", "theme.primaryColor": "#722F37", "theme.backgroundColor": "#FDF7F4",
                   "theme.secondaryBackgroundColor": "#F6EDEA", "theme.textColor": "#2A1A1D"}.items():
        st._config.set_option(_k, _v)
except Exception:
    pass
st.set_page_config(page_title="The Brillat Game", page_icon=":material/wine_bar:", layout="wide", initial_sidebar_state="expanded")


# ---------------- Tema visual: vino liquido + Andes/vinedo + estilo ----------------
GOLD = "#C9A24B"
FONTS = "@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;600;700&family=Inter:wght@400;500;600&display=swap');"
CSS = """
html{background:#240810!important}
.stApp,[data-testid=stAppViewContainer],[data-testid=stHeader]{background:transparent!important}
[data-testid=stToolbarActions],[data-testid=stDeployButton],[data-testid=stMainMenu],#MainMenu{display:none!important}
[data-testid=stExpandSidebarButton],[data-testid=stSidebarCollapsedControl],[data-testid=stSidebarCollapseButton]{display:flex!important;visibility:visible!important;opacity:1!important}
[data-testid=stExpandSidebarButton] button,[data-testid=stSidebarCollapsedControl] button,[data-testid=stSidebarCollapseButton] button{color:#f6e3b5!important;background:linear-gradient(135deg,#4a1520,#8a2f3f)!important;border:1px solid #C9A24B!important;border-radius:12px!important}
/* pestana al borde izquierdo: abre el menu si esta oculto */
.sbtab{display:none!important;position:fixed;left:0;top:42%;z-index:999990;width:28px;height:90px;border-radius:0 14px 14px 0;background:linear-gradient(135deg,#4a1520,#8a2f3f);border:1px solid #C9A24B;border-left:0;
 display:none;align-items:center;justify-content:center;cursor:pointer;box-shadow:4px 6px 16px rgba(0,0,0,.35);outline:none;transition:width .25s}
.sbtab:hover{width:36px}.sbtab svg{width:18px;height:18px;fill:none;stroke:#f6e3b5;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}

/* menu cerrado: se oculta por completo (sin la barrita con letras cortadas) */
section[data-testid=stSidebar][aria-expanded=false]{visibility:hidden!important;width:0!important;min-width:0!important;overflow:hidden!important;transform:none!important;border:0!important;box-shadow:none!important}
section[data-testid=stSidebar][aria-expanded=false]:hover{visibility:visible!important;width:min(320px,85vw)!important;min-width:min(320px,85vw)!important;
 position:fixed!important;left:0;top:0;height:100vh!important;z-index:999991;overflow:auto!important;border-right:1px solid rgba(201,162,75,.4)!important;box-shadow:12px 0 40px rgba(0,0,0,.4)!important}
[data-testid=stExpandSidebarButton],[data-testid=stSidebarCollapsedControl]{position:fixed!important;top:14px;left:14px;z-index:999995;width:auto!important;height:auto!important}
[data-testid=stExpandSidebarButton] button,[data-testid=stSidebarCollapsedControl] button{width:40px!important;height:46px!important;min-height:0!important;padding:0!important;background:#4a1520 url("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 80%22%3E%3Cpath d=%22M10 14 52 4q6-1 6 5v8H10z%22 fill=%22%232a0a10%22/%3E%3Crect x=%228%22 y=%2214%22 width=%2250%22 height=%2262%22 rx=%227%22 fill=%22%234a1a12%22/%3E%3Crect x=%2212%22 y=%2218%22 width=%2242%22 height=%2254%22 rx=%224%22 fill=%22none%22 stroke=%22%23e8d9d2%22 stroke-width=%221.2%22/%3E%3Cpath d=%22M19 22h20c1 9-1 17-5 19-2 1-2 1-2 3v9h6v3H20v-3h6v-9c0-2 0-2-2-3-4-2-6-10-5-19z%22 fill=%22%23aab4e6%22/%3E%3Cpath d=%22M20 30h18c0 7-3 11-9 11s-9-4-9-11z%22 fill=%22%233d0b18%22/%3E%3Cg fill=%22%23a3294f%22%3E%3Ccircle cx=%2242%22 cy=%2238%22 r=%225%22/%3E%3Ccircle cx=%2249%22 cy=%2240%22 r=%225%22/%3E%3Ccircle cx=%2244%22 cy=%2246%22 r=%225%22/%3E%3Ccircle cx=%2251%22 cy=%2248%22 r=%224.5%22/%3E%3Ccircle cx=%2246%22 cy=%2254%22 r=%224.5%22/%3E%3C/g%3E%3Cpath d=%22M38 36q4-8 9-6-1 7-9 6z%22 fill=%22%237bc24a%22/%3E%3Ctext x=%2232%22 y=%2269%22 font-family=%22Arial%2Csans-serif%22 font-weight=%22bold%22 font-size=%2210%22 fill=%22%23fff%22 text-anchor=%22middle%22%3EMENU%3C/text%3E%3C/svg%3E") center/28px 34px no-repeat!important}
[data-testid=stSidebarCollapseButton] button{width:40px!important;height:46px!important;min-height:0!important;padding:0!important;background:#4a1520 url("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 80%22%3E%3Cpath d=%22M10 14 52 4q6-1 6 5v8H10z%22 fill=%22%232a0a10%22/%3E%3Crect x=%228%22 y=%2214%22 width=%2250%22 height=%2262%22 rx=%227%22 fill=%22%234a1a12%22/%3E%3Crect x=%2212%22 y=%2218%22 width=%2242%22 height=%2254%22 rx=%224%22 fill=%22none%22 stroke=%22%23e8d9d2%22 stroke-width=%221.2%22/%3E%3Cpath d=%22M19 22h20c1 9-1 17-5 19-2 1-2 1-2 3v9h6v3H20v-3h6v-9c0-2 0-2-2-3-4-2-6-10-5-19z%22 fill=%22%23aab4e6%22/%3E%3Cpath d=%22M20 30h18c0 7-3 11-9 11s-9-4-9-11z%22 fill=%22%233d0b18%22/%3E%3Cg fill=%22%23a3294f%22%3E%3Ccircle cx=%2242%22 cy=%2238%22 r=%225%22/%3E%3Ccircle cx=%2249%22 cy=%2240%22 r=%225%22/%3E%3Ccircle cx=%2244%22 cy=%2246%22 r=%225%22/%3E%3Ccircle cx=%2251%22 cy=%2248%22 r=%224.5%22/%3E%3Ccircle cx=%2246%22 cy=%2254%22 r=%224.5%22/%3E%3C/g%3E%3Cpath d=%22M38 36q4-8 9-6-1 7-9 6z%22 fill=%22%237bc24a%22/%3E%3Ctext x=%2232%22 y=%2269%22 font-family=%22Arial%2Csans-serif%22 font-weight=%22bold%22 font-size=%2210%22 fill=%22%23fff%22 text-anchor=%22middle%22%3EMENU%3C/text%3E%3C/svg%3E") center/28px 34px no-repeat!important}
[data-testid=stSidebarCollapseButton] button>*,[data-testid=stSidebarCollapseButton] svg,[data-testid=stSidebarCollapseButton] [data-testid=stIconMaterial]{display:none!important}
button[data-testid=stExpandSidebarButton],[data-testid=stExpandSidebarButton] [role=button],[data-testid=stSidebarCollapsedControl] [role=button],[data-testid=stSidebarCollapsedControl] a{width:40px!important;height:46px!important;min-height:0!important;padding:0!important;border-radius:12px!important;border:1px solid #C9A24B!important;background:#4a1520 url("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 80%22%3E%3Cpath d=%22M10 14 52 4q6-1 6 5v8H10z%22 fill=%22%232a0a10%22/%3E%3Crect x=%228%22 y=%2214%22 width=%2250%22 height=%2262%22 rx=%227%22 fill=%22%234a1a12%22/%3E%3Crect x=%2212%22 y=%2218%22 width=%2242%22 height=%2254%22 rx=%224%22 fill=%22none%22 stroke=%22%23e8d9d2%22 stroke-width=%221.2%22/%3E%3Cpath d=%22M19 22h20c1 9-1 17-5 19-2 1-2 1-2 3v9h6v3H20v-3h6v-9c0-2 0-2-2-3-4-2-6-10-5-19z%22 fill=%22%23aab4e6%22/%3E%3Cpath d=%22M20 30h18c0 7-3 11-9 11s-9-4-9-11z%22 fill=%22%233d0b18%22/%3E%3Cg fill=%22%23a3294f%22%3E%3Ccircle cx=%2242%22 cy=%2238%22 r=%225%22/%3E%3Ccircle cx=%2249%22 cy=%2240%22 r=%225%22/%3E%3Ccircle cx=%2244%22 cy=%2246%22 r=%225%22/%3E%3Ccircle cx=%2251%22 cy=%2248%22 r=%224.5%22/%3E%3Ccircle cx=%2246%22 cy=%2254%22 r=%224.5%22/%3E%3C/g%3E%3Cpath d=%22M38 36q4-8 9-6-1 7-9 6z%22 fill=%22%237bc24a%22/%3E%3Ctext x=%2232%22 y=%2269%22 font-family=%22Arial%2Csans-serif%22 font-weight=%22bold%22 font-size=%2210%22 fill=%22%23fff%22 text-anchor=%22middle%22%3EMENU%3C/text%3E%3C/svg%3E") center/28px 34px no-repeat!important;font-size:0!important;color:transparent!important;display:flex!important}
button[data-testid=stExpandSidebarButton]>*,[data-testid=stExpandSidebarButton] [role=button]>*,[data-testid=stSidebarCollapsedControl] [role=button]>*,[data-testid=stSidebarCollapsedControl] a>*{display:none!important}
[data-testid=stExpandSidebarButton] button>*,[data-testid=stSidebarCollapsedControl] button>*,[data-testid=stExpandSidebarButton] svg,[data-testid=stSidebarCollapsedControl] svg{display:none!important}
html,body,.stApp{font-family:'Inter',sans-serif;color:#2a1a1d}
.block-container{max-width:1060px!important;margin:28px auto 40px!important;padding:2.2rem 2.6rem 3rem!important;
 background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='.8' numOctaves='2'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)' opacity='.03'/%3E%3C/svg%3E"),rgba(253,247,244,.94);
 backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(201,162,75,.45);border-radius:28px;
 box-shadow:0 30px 80px rgba(0,0,0,.55),inset 0 0 0 7px rgba(253,248,246,.5);animation:rise .7s ease both}
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
h1,h2,h3,h4,h5{font-family:'Playfair Display',serif!important;color:WINE!important;text-align:center!important;justify-content:center!important}
h2:after,h3:after{content:"";display:block;width:96px;height:2px;margin:10px auto 4px;background:linear-gradient(90deg,transparent,GOLD,transparent)}
h5{letter-spacing:2px;text-transform:uppercase;font-size:15px!important;font-family:'Inter',sans-serif!important;font-weight:600!important}
[data-testid=stMarkdownContainer],[data-testid=stCaptionContainer]{text-align:center}
[data-testid=stWidgetLabel]{justify-content:center;text-align:center}
[data-testid=stWidgetLabel] p{font-weight:500;color:#5a2a31}
[data-testid=stMetric]{text-align:center}[data-testid=stMetricValue],[data-testid=stMetricLabel]{justify-content:center}
[data-testid=stExpander] summary{justify-content:center}
/* hero animado */
.hdr{position:relative;overflow:hidden;text-align:center;border-radius:22px;margin-bottom:28px;padding:26px 24px 28px;color:#fff;
 background:linear-gradient(125deg,#2c0a12,#5a1a26,#8a2f3f,#3f1019,#2c0a12);background-size:300% 300%;animation:flow 16s ease-in-out infinite;
 box-shadow:0 18px 44px rgba(74,21,32,.4);border:1px solid rgba(201,162,75,.6)}
@keyframes flow{0%{background-position:0 50%}50%{background-position:100% 50%}100%{background-position:0 50%}}
.hdr>*{position:relative;z-index:2}
.hdr .sp{position:absolute;z-index:1;border-radius:50%;background:radial-gradient(circle,#f6dfa0,rgba(246,223,160,0) 70%);opacity:0;animation:rise2 7s ease-in infinite}
@keyframes rise2{0%{transform:translateY(20px) scale(.6);opacity:0}30%{opacity:.85}100%{transform:translateY(-110px) scale(1.2);opacity:0}}
.hdr .gh{height:1.2em;width:.7em;display:inline-block;margin:0 .03em;vertical-align:baseline;position:relative;top:.08em;transform-origin:50% 92%;animation:swirl 5s ease-in-out infinite;filter:drop-shadow(0 8px 18px rgba(0,0,0,.45))}
@keyframes swirl{0%,100%{transform:rotate(-4deg)}50%{transform:rotate(4deg)}}
.hdr .wv{animation:wave 2.2s linear infinite}
@keyframes wave{to{transform:translateX(8px)}}
.hdr .t{display:flex;align-items:center;justify-content:center;gap:0;margin-top:6px;font-family:'Playfair Display',serif;font-size:clamp(30px,6vw,52px);font-weight:700}
.hdr .t b.r{color:#b3202a}.hdr .prot{display:block;margin:20px auto 0;width:min(100%,400px);border-radius:18px;border:1px solid rgba(201,162,75,.7);box-shadow:0 14px 36px rgba(0,0,0,.5),0 0 0 6px rgba(201,162,75,.12);animation:fup 1s ease-out both,flt 6s ease-in-out 1s infinite}
@keyframes fup{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}@keyframes flt{50%{transform:translateY(-6px)}}
/* login se revela al pasar el cursor / tocar al protagonista */
.hdr .hint{margin-top:14px;font-size:12px;letter-spacing:3px;text-transform:uppercase;color:#f6e3b5;animation:pulse 2s ease-in-out infinite}
@keyframes pulse{50%{opacity:.35}}
.lvl{display:flex;align-items:center;gap:8px;margin:14px 0 -6px;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#8a6a70}
.lvl .stars{display:inline-flex;gap:2px}.lvl svg{width:16px;height:16px;fill:#C9A24B;stroke:#a8832f;stroke-width:1}.lvl svg.off{fill:none;stroke:#d9c9a3;opacity:.7}
/* ---- cuestionario tipo slider ---- */
.qmeta{display:flex;justify-content:space-between;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#8a6a70;margin:0 0 8px}
.qprog{height:8px;border-radius:99px;background:#eadfd9;overflow:hidden;margin-bottom:16px}
.qprog i{display:block;height:100%;background:linear-gradient(90deg,#8a2f3f,#C9A24B);transition:width .6s}
[class*="st-key-qr_"],[class*="st-key-ql_"]{background:#fff;border:1px solid rgba(201,162,75,.45);border-top:4px solid #C9A24B;border-radius:18px;padding:20px 24px 16px;box-shadow:0 12px 34px rgba(74,21,32,.14)}
[class*="st-key-qr_"]{animation:inR .5s cubic-bezier(.2,.9,.3,1) both}[class*="st-key-ql_"]{animation:inL .5s cubic-bezier(.2,.9,.3,1) both}
@keyframes inR{from{opacity:0;transform:translateX(80px)}to{opacity:1;transform:none}}@keyframes inL{from{opacity:0;transform:translateX(-80px)}to{opacity:1;transform:none}}
.qt{font:700 clamp(19px,3.4vw,26px)/1.35 'Playfair Display',serif;color:#4a1520;margin:10px 0 18px}
.qflag{display:inline-block;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#7a5a10;background:#f6e3b5;border-radius:99px;padding:2px 10px;margin-left:10px}
.st-key-qopts [role=radiogroup]{display:flex;flex-direction:column;gap:12px;counter-reset:opt}
.st-key-qopts [role=radiogroup]>label{counter-increment:opt;display:flex;align-items:center;gap:14px;margin:0;padding:14px 18px;border:1.5px solid #e2d4cf;border-radius:14px;background:#fbf8f6;
 cursor:pointer;transition:transform .25s,box-shadow .25s,background .25s,border-color .25s;animation:optin .5s cubic-bezier(.2,.9,.3,1) both}
@keyframes optin{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.st-key-qopts [role=radiogroup]>label>div:first-child{display:none}
.st-key-qopts [role=radiogroup]>label::before{content:counter(opt,upper-alpha);flex:0 0 36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;
 font:700 15px 'Playfair Display',serif;color:#722f37;background:#fff;border:1.5px solid #C9A24B;transition:all .25s}
.st-key-qopts [role=radiogroup]>label:hover{transform:translateX(6px);border-color:#C9A24B;box-shadow:0 8px 20px rgba(74,21,32,.12);background:#fff}
.st-key-qopts [role=radiogroup]>label:has(input:checked){background:linear-gradient(120deg,#4a1520,#8a2f3f);border-color:#C9A24B;transform:translateX(8px);box-shadow:0 10px 26px rgba(74,21,32,.35)}
.st-key-qopts [role=radiogroup]>label:has(input:checked) *{color:#fff!important}
.st-key-qopts [role=radiogroup]>label:has(input:checked)::before{background:#C9A24B;color:#3b0f18;border-color:#f6e3b5;transform:scale(1.1)}
.st-key-qopts [role=radiogroup]>label p{font-size:16.5px;line-height:1.4}
.st-key-qopts,.st-key-qopts [data-testid=stRadio],.st-key-qopts [data-testid=stRadio]>div{width:100%!important;max-width:100%!important;min-width:0!important}
.st-key-qopts [role=radiogroup]{width:100%!important;align-items:stretch!important}
.st-key-qopts [role=radiogroup]>label{width:100%!important;max-width:100%!important;min-width:0!important;box-sizing:border-box!important;display:flex!important;flex:0 0 auto!important}
.st-key-qopts [role=radiogroup]>label>div:not(:first-child){flex:1 1 0!important;min-width:0!important;width:auto!important}
.st-key-qopts [role=radiogroup]>label p{white-space:normal!important;overflow-wrap:anywhere!important;word-break:normal;max-width:100%}
.st-key-qopts [role=radiogroup]>label:nth-child(1){animation-delay:0.23s}.st-key-qopts [role=radiogroup]>label:nth-child(2){animation-delay:0.31s}.st-key-qopts [role=radiogroup]>label:nth-child(3){animation-delay:0.39s}.st-key-qopts [role=radiogroup]>label:nth-child(4){animation-delay:0.47s}.st-key-qopts [role=radiogroup]>label:nth-child(5){animation-delay:0.55s}.st-key-qopts [role=radiogroup]>label:nth-child(6){animation-delay:0.63s}.st-key-qopts [role=radiogroup]>label:nth-child(7){animation-delay:0.71s}.st-key-qopts [role=radiogroup]>label:nth-child(8){animation-delay:0.79s}.st-key-qopts [role=radiogroup]>label:nth-child(9){animation-delay:0.87s}.st-key-qopts [role=radiogroup]>label:nth-child(10){animation-delay:0.95s}
.st-key-qnav{margin-top:6px}.st-key-qnav [data-testid=stButtonGroup]{flex-wrap:wrap;justify-content:center;gap:6px}
.qleg{text-align:center;font-size:12px;color:#8a6a70;margin:2px 0 6px;letter-spacing:1px}
.qtimer{display:flex;justify-content:center;align-items:center;font:700 22px 'Playfair Display',serif;color:#722f37;margin:0 0 10px}.qtimer.low{color:#b3202a;animation:pulse 1s ease-in-out infinite}
/* ---- formularios de cata: secciones con icono y estrellas ---- */
.fsec{display:flex;align-items:center;justify-content:center;gap:12px;margin:28px 0 8px;padding-bottom:12px;border-bottom:1px solid rgba(201,162,75,.45);font:700 15px 'Inter',sans-serif;letter-spacing:4px;text-transform:uppercase;color:#722f37}
.fsec .ico{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#4a1520,#8a2f3f);box-shadow:0 6px 14px rgba(74,21,32,.3),0 0 0 2px rgba(201,162,75,.65)}
.fsec svg{width:22px;height:22px;fill:none;stroke:#f6e3b5;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}
[class*="st-key-star_"] [role=radiogroup]{flex-direction:row-reverse;justify-content:center;gap:6px}
[class*="st-key-star_"] [role=radiogroup]>label{padding:0;margin:0;cursor:pointer}
[class*="st-key-star_"] [role=radiogroup]>label>div{display:none}
[class*="st-key-star_"] [role=radiogroup]>label::before{content:"";display:block;width:36px;height:36px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23cdb98a' stroke-width='1.4' stroke-linejoin='round'%3E%3Cpolygon points='12,2 15.1,8.6 22,9.3 16.8,14 18.4,21 12,17.3 5.6,21 7.2,14 2,9.3 8.9,8.6'/%3E%3C/svg%3E") center/contain no-repeat;transition:transform .25s}
[class*="st-key-star_"] [role=radiogroup]>label:hover::before,[class*="st-key-star_"] [role=radiogroup]>label:hover~label::before,
[class*="st-key-star_"] [role=radiogroup]>label:has(input:checked)::before,[class*="st-key-star_"] [role=radiogroup]>label:has(input:checked)~label::before{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23C9A24B' stroke='%23a8832f' stroke-width='1.4' stroke-linejoin='round'%3E%3Cpolygon points='12,2 15.1,8.6 22,9.3 16.8,14 18.4,21 12,17.3 5.6,21 7.2,14 2,9.3 8.9,8.6'/%3E%3C/svg%3E")}
[class*="st-key-star_"] [role=radiogroup]>label:hover::before{transform:scale(1.25) rotate(-8deg)}


.hdr .prot{cursor:pointer;outline:none;transition:transform .4s,box-shadow .4s}
.hdr .prot:hover{box-shadow:0 14px 40px rgba(0,0,0,.55),0 0 0 6px rgba(201,162,75,.45),0 0 40px rgba(201,162,75,.35)}

.hdr .t span{background:linear-gradient(90deg,#C9A24B 0%,#f6e3b5 45%,#C9A24B 90%);background-size:220% 100%;-webkit-background-clip:text;background-clip:text;
 -webkit-text-fill-color:transparent;animation:shine 6s linear infinite}
@keyframes shine{from{background-position:120% 0}to{background-position:-100% 0}}
.hdr .v{margin-left:12px;font-family:'Inter',sans-serif;font-style:normal;font-size:12px;background:rgba(255,255,255,.2);padding:2px 10px;border-radius:99px}
.hdr small{display:block;font-size:13px;letter-spacing:4px;text-transform:uppercase;margin-top:6px;color:#f6e3b5}
.brand{display:flex;align-items:center;gap:10px;font:700 22px 'Playfair Display',serif;color:WINE;padding:4px 6px 14px;margin-bottom:12px;border-bottom:1px solid rgba(201,162,75,.5)}
.brand svg{width:30px;height:30px;color:GOLD}
.nav-t{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#8a6a70;margin:2px 6px 8px}
.who{display:flex;align-items:center;justify-content:center;gap:10px;margin:0 auto 6px;width:fit-content;padding:6px 18px 6px 6px;
 border-radius:999px;background:#fff;border:1px solid rgba(201,162,75,.55);box-shadow:0 4px 14px rgba(114,47,55,.12);font-weight:500;color:#4a1520}
.who .av{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,#a24b57,#4a1520);color:#fff;font-size:13px;font-weight:600}
/* etiquetas / formularios */
[data-testid=stForm],[data-testid=stExpander]{background:rgba(255,255,255,.72)!important;border:1px solid rgba(114,47,55,.16)!important;
 border-radius:20px!important;box-shadow:inset 0 0 0 6px rgba(253,248,246,.9),inset 0 0 0 7px rgba(201,162,75,.5),0 10px 30px rgba(114,47,55,.10)}
[data-testid=stForm]{padding:30px 32px}
.stTextInput input,.stNumberInput input,[data-baseweb=select]>div,.stDateInput input{border-radius:12px!important}
.stTextInput input:focus,.stNumberInput input:focus{box-shadow:0 0 0 2px rgba(114,47,55,.35)!important}
[data-testid=stRadio] label[data-baseweb=radio]{width:100%;background:#fff;border:1px solid rgba(114,47,55,.18);border-radius:14px;padding:11px 16px;
 margin:3px 0;transition:all .15s ease;text-align:left}
[data-testid=stRadio] label[data-baseweb=radio]:hover{border-color:WINE;transform:translateX(3px);box-shadow:0 4px 14px rgba(114,47,55,.14)}
[data-testid=stRadio] label[data-baseweb=radio]:has(input:checked){background:linear-gradient(135deg,#f9e9ec,#f1d2d7);border-color:WINE;font-weight:600}
[role=radiogroup]{width:100%}
[data-testid=stButton],[data-testid=stFormSubmitButton],[data-testid=stDownloadButton]{display:flex;justify-content:center;width:100%}
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{background:linear-gradient(135deg,#8a3a45,WINE 60%,#4a1520);
 color:#fff;border:1px solid GOLD;border-radius:999px;padding:.6rem 2rem;font-weight:600;letter-spacing:.4px;
 box-shadow:0 6px 18px rgba(114,47,55,.35);transition:transform .15s ease,box-shadow .15s ease,filter .15s ease}
.stButton>button:hover,.stFormSubmitButton>button:hover,.stDownloadButton>button:hover{color:#fff;transform:translateY(-2px);
 box-shadow:0 12px 26px rgba(114,47,55,.45);filter:brightness(1.12)}
.stButton>button p,.stFormSubmitButton>button p,.stDownloadButton>button p{color:inherit!important}
[data-testid=stSidebar]{background:rgba(253,248,246,.95)!important;backdrop-filter:blur(14px);border-right:1px solid rgba(201,162,75,.4)}
[data-testid=stSidebar] [data-testid=stBaseButton-secondary]{background:transparent!important;color:#4a1520!important;border:1px solid transparent!important;
 box-shadow:none!important;justify-content:flex-start;padding:.6rem 1rem;border-radius:14px;font-weight:500;filter:none!important;transform:none!important}
[data-testid=stSidebar] [data-testid=stBaseButton-secondary]:hover{background:rgba(114,47,55,.09)!important;color:WINE!important}
[data-testid=stSidebar] [data-testid=stBaseButton-primary]{justify-content:flex-start;padding:.6rem 1rem;border-radius:14px;box-shadow:0 6px 16px rgba(114,47,55,.35),inset 4px 0 0 GOLD}
[data-testid=stSidebar] button p{text-align:left;color:inherit!important}
.st-key-logout button{border:1px solid rgba(114,47,55,.35)!important}
.stTabs [data-baseweb=tab-list]{gap:8px;justify-content:center;width:100%;background:transparent;padding:0;border-bottom:1px solid rgba(114,47,55,.15);margin-bottom:18px}
.stTabs [data-baseweb=tab]{font-weight:600;color:#7a5a60;padding:10px 22px;height:auto;background:transparent}
.stTabs [aria-selected=true]{color:WINE;background:transparent;box-shadow:none}
.stTabs [data-baseweb=tab-highlight]{background:GOLD!important;height:3px!important;border-radius:3px}
.stTabs [data-baseweb=tab-border]{background:transparent!important}
[data-testid=stHeaderActionElements]{display:none!important}
[data-testid=stAlert]{border-radius:14px}
.element-container:has(.stHtml script),[data-testid=stElementContainer]:has(.stHtml script),.element-container:has(iframe[height="0"]){position:absolute;height:0;overflow:hidden;margin:0}
/* tablas */
.vt{overflow:auto;max-height:460px;border-radius:18px;border:1px solid rgba(114,47,55,.3);background:#fff;box-shadow:0 12px 32px rgba(74,21,32,.22);margin:.5rem 0 1.4rem}
.vt table{width:100%;border-collapse:collapse;font-size:14px;text-align:center}
.vt th{position:sticky;top:0;background:linear-gradient(135deg,#3a0f18,WINE);color:#fff;padding:13px 14px;font-weight:600;letter-spacing:.5px;white-space:nowrap;border-bottom:2px solid GOLD}
.vt td{padding:10px 14px;border-bottom:1px solid rgba(114,47,55,.12);color:#2a1a1d;vertical-align:middle}
.vt tbody tr:nth-child(even){background:#faeef0}.vt tbody tr:hover{background:#f0d3d8}.vt tbody tr:last-child td{border-bottom:0}
.vt .e{padding:22px;color:#8a6a70}
.medal svg{width:22px;height:22px;vertical-align:-5px;margin-right:6px}
.g{color:#d4a017}.s{color:#9aa3ad}.b{color:#b0703a}
/* podio */
.pod{display:flex;justify-content:center;align-items:flex-end;gap:14px;margin:14px 0 26px}
.pl{width:180px;text-align:center}
.pl .cup svg{width:58px;height:58px;filter:drop-shadow(0 4px 8px rgba(0,0,0,.25));animation:pop .7s cubic-bezier(.2,1.6,.4,1) both}
.pl .nm{font-family:'Playfair Display',serif;font-weight:700;font-size:17px;color:#4a1520;margin-top:4px;line-height:1.15}
.pl .sc{font-size:13px;color:#8a6a70;margin-bottom:8px}
.ped{display:flex;justify-content:center;padding-top:10px;border-radius:14px 14px 0 0;font:700 30px 'Playfair Display',serif;color:rgba(0,0,0,.45);
 transform-origin:bottom;animation:grow .9s cubic-bezier(.2,.9,.3,1) both;box-shadow:inset 0 2px 0 rgba(255,255,255,.5)}
.p1 .ped{height:132px;background:linear-gradient(180deg,#f3d77a,#b8860b);animation-delay:.7s}.p1 .cup svg{animation-delay:1.4s}
.p2 .ped{height:100px;background:linear-gradient(180deg,#e3e7eb,#8d97a1);animation-delay:.4s}.p2 .cup svg{animation-delay:1.1s}
.p3 .ped{height:78px;background:linear-gradient(180deg,#d9a273,#9a5b2b);animation-delay:.1s}.p3 .cup svg{animation-delay:.8s}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{from{transform:scale(0) rotate(-20deg);opacity:0}to{transform:none;opacity:1}}
/* resultado */
.res{position:relative;overflow:hidden;text-align:center;padding:30px 20px 28px;border-radius:26px;background:linear-gradient(160deg,#fff,#f8eaec);
 border:1px solid rgba(201,162,75,.6);box-shadow:0 18px 50px rgba(114,47,55,.22),inset 0 0 0 7px #fff,inset 0 0 0 8px rgba(201,162,75,.4)}
.res .eb{letter-spacing:4px;text-transform:uppercase;font-size:12px;color:#8a6a70}
.res .gl{width:150px;height:190px;margin:6px auto -4px;display:block}
.res .liq{transform:translateY(13px);animation:fill 2.6s cubic-bezier(.25,.8,.25,1) .3s forwards}
.res .num{font:700 84px/1 'Playfair Display',serif;color:WINE}
.res .num:after{counter-reset:n var(--n);content:counter(n);animation:cnt 2.6s cubic-bezier(.25,.8,.25,1) .3s forwards}
.res .of{font-size:24px;color:#8a6a70;margin-left:6px}
.res .pcl{font-size:15px;font-weight:600;color:GOLD;letter-spacing:2px;margin-top:2px}
.res .pcl:after{counter-reset:p var(--pc);content:counter(p) "% de aciertos";animation:cnp 2.6s cubic-bezier(.25,.8,.25,1) .3s forwards}
.res h3{margin:14px 0 2px!important}.res .sub{color:#6a4a50}
.res .chips{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-top:18px}
.res .chip{min-width:120px;padding:10px 16px;border-radius:14px;background:#fff;border:1px solid rgba(114,47,55,.15);
 animation:pop .6s both;animation-delay:2.4s}.res .chip:nth-child(2){animation-delay:2.6s}.res .chip:nth-child(3){animation-delay:2.8s}
.res .chip b{display:block;font:700 22px 'Playfair Display',serif;color:WINE}.res .chip span{font-size:12px;color:#8a6a70;letter-spacing:1px;text-transform:uppercase}
.res .dr{position:absolute;top:-14px;border-radius:50%;opacity:0;animation:fall 3.4s ease-in 2;box-shadow:inset -2px -2px 0 rgba(0,0,0,.18)}
@keyframes fall{0%{transform:translateY(0);opacity:0}12%{opacity:.9}100%{transform:translateY(460px);opacity:0}}
/* ---- responsive: tablets y celulares (iPhone / Android) ---- */
html,body{-webkit-text-size-adjust:100%;text-size-adjust:100%}
.stTextInput input,.stNumberInput input,.stDateInput input,[data-baseweb=select] input{font-size:16px!important}
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{min-height:44px}
@media (max-width:900px){
 .block-container{width:calc(100% - 20px)!important;box-sizing:border-box;margin:16px auto 24px!important;padding:1.4rem 1.2rem 2rem!important;border-radius:22px;overflow-x:hidden}
 .pl{width:30%}
}
@media (max-width:640px){
 .block-container{width:calc(100% - 12px)!important;margin:56px auto 16px!important;padding:1rem .8rem 1.6rem!important;border-radius:20px}
 h2,h3{font-size:1.4rem!important}
 .hdr{padding:18px 10px 20px;border-radius:18px;margin-bottom:18px}
 .hdr .t{font-size:clamp(20px,6.6vw,34px);white-space:nowrap}
 .hdr .v{margin-left:6px;font-size:10px;padding:1px 7px}
 .hdr small{font-size:11px;letter-spacing:3px}
 .hdr .prot{margin-top:14px;border-radius:14px}
 .hdr .hint{font-size:10px;letter-spacing:2px}
 [data-testid=stForm]{padding:16px 12px!important}
 .fsec{letter-spacing:2px;font-size:13px;gap:8px}.fsec .ico{width:36px;height:36px}
 [class*="st-key-qr_"],[class*="st-key-ql_"]{padding:14px 12px 10px;border-radius:14px}
 .qt{font-size:18px}
 .st-key-qopts [role=radiogroup]>label{padding:11px 12px;gap:10px}
 .st-key-qopts [role=radiogroup]>label::before{flex:0 0 30px;height:30px;font-size:13px}
 .st-key-qopts [role=radiogroup]>label p{font-size:15px}
 .qtimer{font-size:19px}
 [class*="st-key-star_"] [role=radiogroup]>label::before{width:32px;height:32px}
 .pod{gap:6px}.pl .cup svg{width:40px;height:40px}.pl .nm{font-size:13px}.pl .sc{font-size:11px}
 .p1 .ped{height:104px}.p2 .ped{height:80px}.p3 .ped{height:62px}
 .res{padding:22px 10px 20px}.res .num{font-size:64px}.res .gl{width:120px;height:152px}.res .chip{min-width:96px;padding:8px 10px}
 .vt{max-height:380px;border-radius:14px}.vt table{font-size:12.5px}.vt th,.vt td{padding:8px 9px}
 .stTabs [data-baseweb=tab-list]{justify-content:flex-start;gap:2px;overflow-x:auto}
 .stTabs [data-baseweb=tab]{padding:8px 12px;font-size:14px}
}
/* pantallas tactiles: no hay "hover", el login y el menu quedan siempre visibles */
@media (hover:none){
 .sbtab{display:none!important}
 .hdr .hint{display:none}
 .st-key-qopts [role=radiogroup]>label:hover,[data-testid=stRadio] label[data-baseweb=radio]:hover{transform:none}
 .stButton>button:hover,.stFormSubmitButton>button:hover,.stDownloadButton>button:hover{transform:none}
}

/* ---- forzar tema claro: el modo oscuro del celu/navegador no debe alterar colores ---- */
html,body,.stApp{color-scheme:light!important}
.st-key-qopts [role=radiogroup]>label:not(:has(input:checked)),.st-key-qopts [role=radiogroup]>label:not(:has(input:checked)) *{color:#2a1a1d!important;opacity:1}
.st-key-qopts [role=radiogroup]>label{background-color:#fbf8f6}
.st-key-qopts [role=radiogroup]>label:has(input:checked){background-color:#6b1f2c}
.block-container [data-testid=stRadio] label,.block-container [data-testid=stCheckbox] label,.block-container [data-testid=stRadio] label p,.block-container [data-testid=stCheckbox] label p{color:#2a1a1d}
.block-container input,.block-container textarea,.block-container [data-baseweb=select]>div,.block-container [data-baseweb=input],.block-container [data-baseweb=textarea]{background-color:#fff!important;color:#2a1a1d!important;-webkit-text-fill-color:#2a1a1d}
.block-container [data-testid=stCaptionContainer],.block-container [data-testid=stCaptionContainer] p{color:#6b4a50!important}

.st-key-qopts label[data-baseweb=radio]{background-color:#fbf8f6!important;border:1.5px solid #e2d4cf!important;border-radius:14px;display:flex!important;align-items:center;gap:14px;padding:14px 18px}
.st-key-qopts label[data-baseweb=radio]>div:first-child{display:none!important}
.st-key-qopts label[data-baseweb=radio]:not(:has(input:checked)) :is(p,span,div){color:#2a1a1d!important;-webkit-text-fill-color:#2a1a1d!important;opacity:1!important}
.st-key-qopts label[data-baseweb=radio]:has(input:checked){background:linear-gradient(120deg,#4a1520,#8a2f3f)!important;border-color:#C9A24B!important}
.st-key-qopts label[data-baseweb=radio]:has(input:checked) :is(p,span,div){color:#fff!important;-webkit-text-fill-color:#fff!important}

/* ---- robustez movil/oscuro: estrellas y opciones sin depender de la estructura exacta ---- */
[class*="st-key-star_"] [data-testid=stRadio] [role=radiogroup],[class*="st-key-star_"] [data-testid=stRadio] div:has(>label[data-baseweb=radio]){display:flex!important;flex-direction:row-reverse!important;justify-content:center!important;gap:6px!important;width:100%}
[class*="st-key-star_"] label[data-baseweb=radio]{width:auto!important;background:transparent!important;border:0!important;box-shadow:none!important;padding:0!important;margin:0!important;transform:none!important;display:block!important}
[class*="st-key-star_"] label[data-baseweb=radio]>:not(input){display:none!important}
[class*="st-key-star_"] label[data-baseweb=radio]::before{content:"";display:block;width:36px;height:36px;background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23cdb98a' stroke-width='1.4' stroke-linejoin='round'%3E%3Cpolygon points='12,2 15.1,8.6 22,9.3 16.8,14 18.4,21 12,17.3 5.6,21 7.2,14 2,9.3 8.9,8.6'/%3E%3C/svg%3E") center/contain no-repeat}
[class*="st-key-star_"] label[data-baseweb=radio]:hover::before,[class*="st-key-star_"] label[data-baseweb=radio]:hover~label::before,[class*="st-key-star_"] label[data-baseweb=radio]:has(input:checked)::before,[class*="st-key-star_"] label[data-baseweb=radio]:has(input:checked)~label::before{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23C9A24B' stroke='%23a8832f' stroke-width='1.4' stroke-linejoin='round'%3E%3Cpolygon points='12,2 15.1,8.6 22,9.3 16.8,14 18.4,21 12,17.3 5.6,21 7.2,14 2,9.3 8.9,8.6'/%3E%3C/svg%3E")}
.st-key-qopts label[data-baseweb=radio]{width:100%}
.st-key-qopts label[data-baseweb=radio]::before{content:counter(opt,upper-alpha);flex:0 0 34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font:700 15px 'Playfair Display',serif;color:#722f37;background:#fff;border:1.5px solid #C9A24B}
.st-key-qopts [data-testid=stRadio] [role=radiogroup],.st-key-qopts [data-testid=stRadio] div:has(>label[data-baseweb=radio]){display:flex!important;flex-direction:column;gap:12px;counter-reset:opt}
.st-key-qopts label[data-baseweb=radio]{counter-increment:opt}
.st-key-qopts label[data-baseweb=radio]:has(input:checked)::before{background:#C9A24B;color:#3b0f18}
/* tema claro forzado en widgets */
[data-testid=stWidgetLabel] *,[data-testid=stRadio] label *,[data-testid=stCheckbox] label *,[data-testid=stMetric] *,[data-testid=stExpander] summary *,[data-testid=stMarkdownContainer]>p,[data-testid=stMarkdownContainer]>ul li{color:#2a1a1d}
[data-baseweb=select] div,[data-baseweb=select] input,[data-baseweb=input] div,[data-baseweb=base-input],[data-baseweb=textarea],[data-baseweb=datepicker] div{background-color:#fff!important;color:#2a1a1d!important;-webkit-text-fill-color:#2a1a1d}
[data-baseweb=select] svg{fill:#722f37!important}
[data-baseweb=tag]{background:#f1d2d7!important}[data-baseweb=tag] *{color:#4a1520!important;background:transparent!important}
[data-baseweb=popover] *,[data-baseweb=menu],ul[role=listbox],ul[role=listbox] li{background-color:#fff!important;color:#2a1a1d!important}
[data-baseweb=popover] li:hover,ul[role=listbox] li[aria-selected=true]{background-color:#f6e3b5!important}


/* ---- bienvenida (QR): boton interactivo que lleva directo al registro ---- */
.hdr.wl .prot{cursor:default}
.wsteps{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin:6px 0 18px}
.wsteps div{min-width:140px;padding:12px 16px;border-radius:16px;background:#fff;border:1px solid rgba(201,162,75,.55);box-shadow:0 6px 18px rgba(114,47,55,.12);
 font-size:13px;letter-spacing:1px;text-transform:uppercase;color:#6a4a50;animation:optin .7s cubic-bezier(.2,.9,.3,1) both}
.wsteps div:nth-child(2){animation-delay:.2s}.wsteps div:nth-child(3){animation-delay:.4s}
.wsteps b{display:block;font:700 26px 'Playfair Display',serif;color:#722f37}
.st-key-cta button{font-size:clamp(17px,4.6vw,22px)!important;font-family:'Playfair Display',serif;padding:.9rem 2.8rem!important;min-height:58px;
 animation:ctaGlow 2.2s ease-in-out infinite!important}
.st-key-cta button:hover{transform:translateY(-3px) scale(1.04)!important}
@keyframes ctaGlow{0%,100%{box-shadow:0 6px 18px rgba(114,47,55,.35),0 0 0 0 rgba(201,162,75,.65)}50%{box-shadow:0 10px 26px rgba(114,47,55,.5),0 0 0 16px rgba(201,162,75,0)}}
.st-key-adminbox{margin-top:26px;opacity:.9}

/* ---- boton Quiero participar centrado ---- */
.st-key-cta{display:flex!important;flex-direction:column!important;align-items:center!important;width:100%!important}
.st-key-cta [data-testid=stElementContainer],.st-key-cta [data-testid=stButton]{display:flex!important;justify-content:center!important;width:100%!important}
.st-key-cta button{margin:0 auto!important}
/* ---- transicion "descorche": el vino sube, aparece el saludo y se desvanece ---- */
.splash{position:fixed;inset:0;z-index:999999;pointer-events:none;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;text-align:center;
 background:#240810;border-radius:28px;overflow:hidden;animation:splOut 2.5s ease forwards}
.splash .pour{position:absolute;left:0;right:0;bottom:0;height:0;background:linear-gradient(180deg,#8a2f3f,#3f1019);animation:pourUp 1.2s cubic-bezier(.5,0,.2,1) forwards}
.splash .pour:before{content:"";position:absolute;left:0;right:0;top:-14px;height:28px;background:radial-gradient(ellipse at 50% 100%,#8a2f3f 60%,transparent 62%) 0 0/60px 28px repeat-x;animation:wave 1.4s linear infinite}
.splash>*:not(.pour){position:relative;z-index:2;opacity:0;animation:fup .8s ease .5s forwards}
.splash .sg{font-size:0;line-height:0;animation:fup .8s ease .4s forwards}
.splash .sg svg{display:block;width:120px;height:auto;overflow:visible}
.splash .sg.pr svg{width:min(290px,80vw)}
.splash .sg svg.sgl{transform-origin:50% 92%;animation:sgt 2.4s ease-in-out .9s infinite}
.splash .sfill{animation:sfil 1.5s ease-out .6s both}
.splash .swv{animation:swv 1.1s linear infinite}
.splash .sbb{fill:#f6e3b5;opacity:0;animation:sbu 1.6s ease-in infinite}
.splash .sbb.b2{animation-delay:.5s}.splash .sbb.b3{animation-delay:1s}
@keyframes sgt{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(6deg)}}
@keyframes sfil{from{transform:translateY(100px)}to{transform:translateY(32px)}}
@keyframes swv{to{transform:translateX(-60px)}}
@keyframes sbu{0%{transform:translateY(0);opacity:0}20%{opacity:.8}100%{transform:translateY(-34px);opacity:0}}
.splash .st1{font:700 clamp(24px,7vw,38px) 'Playfair Display',serif;color:#f6e3b5}
.splash .st2{font-size:12px;letter-spacing:3px;text-transform:uppercase;color:#d9b8be}
@keyframes pourUp{to{height:112%}}
@keyframes splOut{0%,64%{opacity:1;visibility:visible}100%{opacity:0;visibility:hidden}}
/* ---- registro interactivo: copa que se llena ---- */
.glass{display:flex;flex-direction:column;align-items:center;margin:2px 0 6px}
.glass svg{width:118px;height:auto;filter:drop-shadow(0 8px 14px rgba(74,21,32,.25))}
.glass .gwv{animation:gwv 2.4s linear infinite}
@keyframes gwv{to{transform:translateX(60px)}}
.gmsg{font:600 13px 'Inter',sans-serif;letter-spacing:2.5px;text-transform:uppercase;color:#722f37;margin-top:4px}
.gbar{width:min(260px,70%);height:6px;border-radius:99px;background:#eadfd9;overflow:hidden;margin-top:8px}
.gbar i{display:block;height:100%;background:linear-gradient(90deg,#8a2f3f,#C9A24B);transition:width .9s}
.st-key-regbox{background:#fff;border:1px solid rgba(201,162,75,.45);border-top:4px solid #C9A24B;border-radius:18px;padding:16px 20px 18px;box-shadow:0 12px 34px rgba(74,21,32,.14)}
.st-key-regbox>*{animation:optin .6s cubic-bezier(.2,.9,.3,1) both}
.st-key-regbox>*:nth-child(2){animation-delay:.15s}.st-key-regbox>*:nth-child(3){animation-delay:.3s}.st-key-regbox>*:nth-child(4){animation-delay:.45s}.st-key-regbox>*:nth-child(5){animation-delay:.6s}.st-key-regbox>*:nth-child(6){animation-delay:.75s}
.st-key-regbox button{font-family:'Playfair Display',serif;font-size:18px!important;min-height:52px;margin:0 auto;display:flex}
.glass .gfill{transition:transform .55s cubic-bezier(.3,.9,.3,1)}
.glass .bb{fill:rgba(255,255,255,.35);animation:bub 2.6s ease-in infinite}.glass .b2{animation-delay:.9s}.glass .b3{animation-delay:1.6s}
@keyframes bub{0%{transform:translateY(20px);opacity:0}30%{opacity:.8}100%{transform:translateY(-34px);opacity:0}}
.glass.pop svg{animation:gpop .5s ease}
@keyframes gpop{0%{transform:scale(1)}40%{transform:scale(1.08) rotate(-3deg)}100%{transform:scale(1)}}
.glass.full svg{filter:drop-shadow(0 0 18px rgba(201,162,75,.75))}.glass.full .gmsg{color:#b3202a}
.st-key-regbox [data-testid=stElementContainer]:has(iframe){position:absolute;width:0;height:0;overflow:hidden;margin:0;padding:0}
/* ---- rendimiento en celulares: sin blur, sin animaciones pesadas ---- */
@media (max-width:900px),(hover:none){
 .block-container{backdrop-filter:none!important;-webkit-backdrop-filter:none!important;background:rgba(253,247,244,.98)!important;animation:none!important;box-shadow:0 10px 30px rgba(0,0,0,.4)!important}
 .hdr,.hdr .t span,.hdr .prot{animation:none!important}.hdr .sp{display:none!important}
 .hdr .gh{animation:swirl 5s ease-in-out infinite!important;will-change:transform}.hdr .wv{animation:wave 2.2s linear infinite!important}
 [class*="st-key-qr_"],[class*="st-key-ql_"],.st-key-qopts [role=radiogroup]>label,.st-key-qopts label[data-baseweb=radio]{animation:none!important;transition:none!important}
 [data-testid=stSidebar]{backdrop-filter:none!important}
 .st-key-usecbox [data-testid=stButtonGroup]{justify-content:center;flex-wrap:wrap}
}

/* ===== DISENO UNICO en computador, Android e iPhone: estrellas y alternativas (no dependen de la estructura interna) ===== */
[class*="st-key-star_"] [role=radiogroup]{display:flex!important;flex-direction:row-reverse!important;justify-content:center!important;align-items:center!important;gap:6px!important;width:100%!important}
[class*="st-key-star_"] [role=radiogroup] label{display:block!important;position:relative;flex:0 0 auto;width:36px!important;min-width:36px!important;height:36px!important;padding:0!important;margin:0!important;border:0!important;box-shadow:none!important;transform:none!important;overflow:hidden;cursor:pointer;font-size:0!important;line-height:0!important;
 background:transparent url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23cdb98a' stroke-width='1.4' stroke-linejoin='round'%3E%3Cpolygon points='12,2 15.1,8.6 22,9.3 16.8,14 18.4,21 12,17.3 5.6,21 7.2,14 2,9.3 8.9,8.6'/%3E%3C/svg%3E") center/contain no-repeat!important;transition:transform .15s}
[class*="st-key-star_"] [role=radiogroup] label>*{display:none!important}
[class*="st-key-star_"] [role=radiogroup] label::before,[class*="st-key-star_"] [role=radiogroup] label::after{content:none!important;display:none!important}
[class*="st-key-star_"] [role=radiogroup] label:hover,[class*="st-key-star_"] [role=radiogroup] label:hover~label,[class*="st-key-star_"] [role=radiogroup] label:has(input:checked),[class*="st-key-star_"] [role=radiogroup] label:has(input:checked)~label,[class*="st-key-star_"] [role=radiogroup]>:hover~* label,[class*="st-key-star_"] [role=radiogroup]>:has(input:checked)~* label{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23C9A24B' stroke='%23a8832f' stroke-width='1.4' stroke-linejoin='round'%3E%3Cpolygon points='12,2 15.1,8.6 22,9.3 16.8,14 18.4,21 12,17.3 5.6,21 7.2,14 2,9.3 8.9,8.6'/%3E%3C/svg%3E")!important}
[class*="st-key-star_"] [role=radiogroup] label:hover{transform:scale(1.2) rotate(-8deg)!important}
.st-key-qopts [role=radiogroup]{display:flex!important;flex-direction:column!important;gap:12px!important;counter-reset:opt;width:100%}
.st-key-qopts [role=radiogroup] label{counter-increment:opt;display:flex!important;align-items:center!important;gap:14px!important;margin:0!important;padding:14px 18px!important;border:1.5px solid #e2d4cf!important;border-radius:14px!important;background:#fbf8f6!important;cursor:pointer;
 transition:transform .2s,box-shadow .2s,border-color .2s;width:fit-content;max-width:100%}
.st-key-qopts [role=radiogroup] label::before{content:counter(opt,upper-alpha)!important;flex:0 0 36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font:700 15px 'Playfair Display',serif;color:#722f37;background:#fff;border:1.5px solid #C9A24B}
.st-key-qopts [role=radiogroup] label:hover{transform:translateX(6px);border-color:#C9A24B!important;background:#fff!important}
.st-key-qopts [role=radiogroup] label:not(:has(input:checked)) *{color:#2a1a1d!important;-webkit-text-fill-color:#2a1a1d!important;opacity:1!important}
.st-key-qopts [role=radiogroup] label:has(input:checked){background:linear-gradient(120deg,#4a1520,#8a2f3f)!important;border-color:#C9A24B!important;transform:translateX(8px);box-shadow:0 10px 26px rgba(74,21,32,.35)}
.st-key-qopts [role=radiogroup] label:has(input:checked) *{color:#fff!important;-webkit-text-fill-color:#fff!important}
.st-key-qopts [role=radiogroup] label:has(input:checked)::before{background:#C9A24B;color:#3b0f18;border-color:#f6e3b5;transform:scale(1.1)}
.st-key-qopts [role=radiogroup] label p{font-size:16.5px;line-height:1.4;margin:0}
@media (max-width:640px){
 [class*="st-key-star_"] [role=radiogroup] label{width:34px!important;min-width:34px!important;height:34px!important}
 .st-key-qopts [role=radiogroup] label{width:100%!important;padding:11px 12px!important;gap:10px!important}
 .st-key-qopts [role=radiogroup] label::before{flex:0 0 30px;height:30px;font-size:13px}
 .st-key-qopts [role=radiogroup] label p{font-size:15px}
}

/* la copa se llena cuando la tarjeta de resultado aparece en pantalla (celular y computador) */
.res.arm:not(.go) *,.res.arm:not(.go) .num:after,.res.arm:not(.go) .pcl:after{animation-play-state:paused!important}
.res .liq{will-change:transform}
.st-key-cheatbtn{display:none!important}
.cheat{max-width:440px;margin:10px auto 18px;border-radius:18px;overflow:hidden;border:2px solid #8a1a1a;box-shadow:0 14px 34px rgba(120,10,10,.35);background:#240810;text-align:center;
 animation:chFade .5s ease both,chShake .6s ease .75s both,chGlow 1.8s ease-in-out 1.5s infinite alternate}
.cheat img{display:block;width:100%;height:auto;animation:chSlam .9s cubic-bezier(.16,1.2,.3,1) .1s both}
.cheat div{padding:12px 14px;color:#f6c9c9;font-size:14px;letter-spacing:.5px;opacity:0;animation:fup .8s ease 1.4s forwards}
.cheatflash{position:fixed;inset:0;z-index:99999;pointer-events:none;background:radial-gradient(circle at 50% 45%,rgba(255,40,40,.65),rgba(120,0,0,.75));animation:chFlash 1.6s ease-out forwards}
@keyframes chFlash{0%{opacity:0}8%{opacity:1}30%{opacity:.55}45%{opacity:.9}100%{opacity:0;visibility:hidden}}
@keyframes chFade{from{opacity:0}to{opacity:1}}
@keyframes chSlam{0%{transform:scale(2.6) rotate(-5deg);filter:blur(10px) brightness(2.2);opacity:0}60%{opacity:1}100%{transform:none;filter:none;opacity:1}}
@keyframes chShake{0%,100%{transform:translateX(0)}15%{transform:translateX(-12px)}30%{transform:translateX(10px)}45%{transform:translateX(-8px)}60%{transform:translateX(6px)}80%{transform:translateX(-3px)}}
@keyframes chGlow{from{box-shadow:0 14px 34px rgba(120,10,10,.35)}to{box-shadow:0 0 46px 6px rgba(255,40,40,.55)}}
@media (prefers-reduced-motion:reduce){.cheat,.cheat img,.cheat div,.cheatflash{animation:none!important;opacity:1}.cheatflash{display:none}}
.wcard{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:6px 0 14px}
.wcard .wi{background:#fbf8f6;border:1px solid rgba(201,162,75,.5);border-radius:12px;padding:9px 14px;text-align:left}
.wcard .wi span{display:block;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#8a6a70}
.wcard .wi b{display:block;font-size:15px;color:#2a1a1d;font-weight:600;word-break:break-word}
.wcard .wi.full{grid-column:1/-1}
@media (max-width:640px){.wcard{grid-template-columns:1fr}}
/* ===== arreglos: alternativas siempre a todo el ancho; 3 pasos del inicio iguales ===== */
.st-key-qopts,.st-key-qopts [data-testid=stRadio],.st-key-qopts [data-testid=stRadio]>div{width:100%!important;max-width:100%!important}
.st-key-qopts [role=radiogroup] label,.st-key-qopts label[data-baseweb=radio]{width:100%!important;max-width:100%!important;box-sizing:border-box!important;transform:none!important;animation:none!important}
.st-key-qopts [role=radiogroup] label>div:last-child,.st-key-qopts label[data-baseweb=radio]>div:last-child{flex:1 1 auto!important;min-width:0!important}
.st-key-qopts [role=radiogroup] label p{white-space:normal!important;word-break:normal!important;overflow-wrap:break-word!important;text-align:left}
.wsteps{display:grid!important;grid-template-columns:repeat(3,1fr);gap:12px;max-width:620px;margin:6px auto 18px!important}
.wsteps div{min-width:0!important;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:flex-start}
@media (max-width:520px){.wsteps{gap:8px}.wsteps div{padding:10px 6px!important;font-size:11px!important;letter-spacing:.5px!important}}

/* ===== v4: alternativas a todo el ancho, sin circulo nativo; imagenes livianas ===== */
.st-key-qopts,.st-key-qopts [data-testid=stElementContainer],.st-key-qopts [data-testid=stRadio],.st-key-qopts [data-testid=stRadio]>div{width:100%!important;max-width:100%!important;min-width:0!important}
.st-key-qopts [role=radiogroup]{width:100%!important;display:flex!important;flex-direction:column!important}
.st-key-qopts [role=radiogroup] label{position:relative;width:100%!important;max-width:100%!important;box-sizing:border-box!important}
.st-key-qopts label>*{visibility:hidden!important}
.st-key-qopts label :is(p,[data-testid=stMarkdownContainer]){visibility:visible!important}
.st-key-qopts label>*:not(input):not(:has(p)){display:none!important}
.st-key-qopts label>*:has(p){display:block!important;flex:1 1 auto;min-width:0;text-align:left}
.st-key-prot{max-width:400px;margin:0 auto 22px;border-radius:18px;overflow:hidden;border:1px solid rgba(201,162,75,.7);box-shadow:0 14px 36px rgba(0,0,0,.35),0 0 0 6px rgba(201,162,75,.12)}
.st-key-prot img{display:block;width:100%;height:auto}
.st-key-prot [data-testid=stElementToolbar],.st-key-cheatbox [data-testid=stElementToolbar]{display:none!important}
.st-key-cheatbox{max-width:440px;margin:10px auto 18px;border-radius:18px;overflow:hidden;border:2px solid #8a1a1a;background:#240810;text-align:center;box-shadow:0 14px 34px rgba(120,10,10,.35);animation:chFade .5s ease both,chShake .6s ease .75s both,chGlow 1.8s ease-in-out 1.5s infinite alternate}
.st-key-cheatbox img{display:block;width:100%;height:auto;animation:chSlam .9s cubic-bezier(.16,1.2,.3,1) .1s both}
.cheatmsg{padding:12px 14px;color:#f6c9c9!important;font-size:14px;letter-spacing:.5px;opacity:0;animation:fup .8s ease 1.4s forwards}
"""

BUBBLES_JS = """<script>
(function(){
const P=window.parent,D=P.document;
if(P.__wb){cancelAnimationFrame(P.__wb.raf);P.__wb.off();}
const old=D.getElementById('wine-bg');if(old)old.remove();
const c=D.createElement('canvas');c.id='wine-bg';
c.style.cssText='position:fixed;inset:0;width:100%;height:100%;z-index:-1;pointer-events:none';
D.body.appendChild(c);
const x=c.getContext('2d');let W,H,t=0,mx=null,my=null,gx=0,gy=0,lx=-999,ly=-999,R=[],B=[];
const reduce=P.matchMedia&&P.matchMedia('(prefers-reduced-motion: reduce)').matches;
const lite=P.innerWidth<900||(P.matchMedia&&P.matchMedia('(hover:none)').matches);let last=0;
function tick(ts){if(D.hidden){P.__wb.raf=requestAnimationFrame(tick);return;}if(ts-last<33){P.__wb.raf=requestAnimationFrame(tick);return;}last=ts;draw();}
const BL=[[122,24,44,.9],[88,14,32,.9],[150,35,58,.7],[60,8,24,.9],[170,50,70,.5],[100,20,45,.8]];
function mk(init){const r=3+Math.random()*9;return{x:Math.random()*W,y:init?Math.random()*H:H+r+Math.random()*120,r:r,vy:.18+Math.random()*.45,vx:0,ph:Math.random()*6.28};}
function size(){W=P.innerWidth;H=P.innerHeight;c.width=W;c.height=H;const n=Math.min(30,Math.round(W*H/42000));
 while(B.length!==n){if(B.length>n)B.pop();else B.push(mk(true));}}
function blob(px,py,r,k,a){const g=x.createRadialGradient(px,py,0,px,py,r);
 g.addColorStop(0,'rgba('+k[0]+','+k[1]+','+k[2]+','+a+')');g.addColorStop(1,'rgba('+k[0]+','+k[1]+','+k[2]+',0)');
 x.fillStyle=g;x.fillRect(px-r,py-r,r*2,r*2);}
function ripple(px,py,big){if(R.length>39)return;R.push({x:px,y:py,r:big?6:3,a:big?.6:.25,s:big?2.8:1.7});}
function draw(){t+=.004;x.fillStyle='#240810';x.fillRect(0,0,W,H);const m=Math.max(W,H);
 BL.forEach((k,i)=>{blob(W*(.5+.42*Math.sin(t*(1+i*.23)+i*1.7)),H*(.5+.42*Math.cos(t*(.8+i*.19)+i*2.3)),m*(.38+.08*Math.sin(t*2+i)),k,k[3]);});
 if(mx!==null){gx+=(mx-gx)*.06;gy+=(my-gy)*.06;blob(gx,gy,m*.22,[190,55,80],.55);}
 for(let i=0;i!==B.length;i++){const b=B[i];
  if(mx!==null){const dx=b.x-mx,dy=b.y-my,d=Math.hypot(dx,dy)||1,f=Math.max(0,130-d)/130;b.vx+=dx/d*f*.8;b.vy+=dy/d*f*.12;}
  b.vx*=.94;b.vy+=(.3-b.vy)*.01;b.x+=b.vx+Math.sin(t*3+b.ph)*.3;b.y-=b.vy;
  if(0>b.y+b.r*2||0>b.x+80||b.x>W+80){B[i]=mk(false);continue;}
  const g=x.createRadialGradient(b.x-b.r*.3,b.y-b.r*.3,b.r*.1,b.x,b.y,b.r);
  g.addColorStop(0,'rgba(255,200,210,.10)');g.addColorStop(1,'rgba(214,80,108,.30)');
  x.beginPath();x.arc(b.x,b.y,b.r,0,6.283);x.fillStyle=g;x.fill();x.lineWidth=1;x.strokeStyle='rgba(255,185,196,.32)';x.stroke();
  x.beginPath();x.arc(b.x-b.r*.35,b.y-b.r*.35,b.r*.2,0,6.283);x.fillStyle='rgba(255,225,230,.4)';x.fill();}
 for(let i=R.length-1;i>=0;i--){const q=R[i];q.r+=q.s;q.a*=.972;if(.01>q.a){R.splice(i,1);continue;}
  x.lineWidth=2;x.strokeStyle='rgba(245,175,188,'+q.a+')';x.beginPath();x.arc(q.x,q.y,q.r,0,6.283);x.stroke();
  x.lineWidth=1;x.strokeStyle='rgba(255,215,220,'+q.a*.6+')';x.beginPath();x.arc(q.x,q.y,q.r*.62,0,6.283);x.stroke();}
 const v=x.createRadialGradient(W/2,H/2,m*.25,W/2,H/2,m*.8);
 v.addColorStop(0,'rgba(0,0,0,0)');v.addColorStop(1,'rgba(10,0,4,.5)');x.fillStyle=v;x.fillRect(0,0,W,H);
 if(!reduce&&!lite)P.__wb.raf=requestAnimationFrame(tick);}
const mv=e=>{if(mx===null){gx=e.clientX;gy=e.clientY;}mx=e.clientX;my=e.clientY;
 if(Math.hypot(mx-lx,my-ly)>80){lx=mx;ly=my;if(!reduce)ripple(mx,my,false);}};
const ck=e=>{if(!reduce)ripple(e.clientX,e.clientY,true);};
const rs=()=>size();
P.addEventListener('mousemove',mv);P.addEventListener('click',ck);P.addEventListener('resize',rs);
P.__wb={raf:0,off:()=>{P.removeEventListener('mousemove',mv);P.removeEventListener('click',ck);P.removeEventListener('resize',rs);}};
size();draw();
})();
</script>"""

_TP = ('<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/>'
       '<path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/>'
       '<path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>')
TROPHY = ('<svg viewBox="0 0 24 24" fill="currentColor" fill-opacity=".25" stroke="currentColor" stroke-width="1.6" '
          'stroke-linecap="round" stroke-linejoin="round">' + _TP + '</svg>')
ICON = ('<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M8 22h8"/><path d="M7 10h10"/><path d="M12 15v7"/><path d="M12 15a5 5 0 0 0 5-5c0-2-.5-4-2-8H9c-1.5 4-2 6-2 8a5 5 0 0 0 5 5Z"/></svg>')
_BOWL = "M12 15a5 5 0 0 0 5-5c0-2-.5-4-2-8H9c-1.5 4-2 6-2 8a5 5 0 0 0 5 5Z"
_SP = "".join(f'<b class="sp" style="left:{l}%;bottom:{b}px;width:{w}px;height:{w}px;animation-delay:{d}s"></b>'
              for l, b, w, d in [(10, 14, 8, 0), (22, 50, 5, 1.6), (36, 8, 6, 3.1), (64, 36, 7, .8), (78, 12, 5, 2.4), (90, 44, 8, 4)])
_GL = ('<svg class="gh" viewBox="5 0 14 24"><defs><clipPath id="hb"><path d="' + _BOWL + '"/></clipPath>'
       '<linearGradient id="hq" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c0566a"/><stop offset="1" stop-color="#5a1a26"/></linearGradient></defs>'
       '<g clip-path="url(#hb)"><g class="wv"><path d="M-8 7 q2 -1.3 4 0 t4 0 t4 0 t4 0 t4 0 t4 0 t4 0 t4 0 V16 H-8Z" fill="url(#hq)"/></g></g>'
       '<path d="' + _BOWL + '" fill="none" stroke="#C9A24B" stroke-width=".55" stroke-linejoin="round"/>'
       '<path d="M12 15v7M8 22h8" fill="none" stroke="#C9A24B" stroke-width=".55" stroke-linecap="round"/></svg>')
_TT = '<div class="t"><b class="r">T</b><span>he Br</span>' + _GL + '<span>llat Game</span><i class="v">v3</i></div><small>Cata · Trivia</small>'
HERO_IMG = "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"
HERO = '<div class="hdr">' + _SP + _TT + '</div>'
HERO_LOGIN = '<div class="hdr wl">' + _SP + _TT + '<div class="hint">Bienvenido a la cata</div></div>'
HERO_BYTES = base64.b64decode(HERO_IMG)

TIMER_HTML = """<style>@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');
html,body{margin:0;background:transparent}#t{display:flex;justify-content:center;align-items:center;height:40px;font:700 22px 'Playfair Display',serif;color:#722f37}
#t.low{color:#b3202a;animation:p 1s ease-in-out infinite}@keyframes p{50%{opacity:.35}}@media(max-width:640px){#t{font-size:19px}}</style>
<div id="t">Tiempo restante&nbsp;--:--:--</div>
<script>const E=__END__,el=document.getElementById('t'),z=n=>String(n).padStart(2,'0');
function tick(){const r=Math.max(0,Math.floor((E-Date.now())/1000));
el.innerHTML='Tiempo restante&nbsp;'+z(Math.floor(r/3600))+':'+z(Math.floor(r%3600/60))+':'+z(r%60);el.className=r<60?'low':'';}
tick();setInterval(tick,1000);</script>"""

INPUTMODE_JS = """<script>(function(){const P=window.parent,D=P.document;if(P.__imode)return;P.__imode=1;
function f(){D.querySelectorAll('[data-baseweb=select] input').forEach(function(i){if(i.getAttribute('inputmode')!=='none')i.setAttribute('inputmode','none');});}
new P.MutationObserver(f).observe(D.body,{childList:true,subtree:true});f();})();</script>"""

def theme():
    st.markdown("<style>" + FONTS + CSS.replace("WINE", WINE).replace("GOLD", GOLD) + "</style>", unsafe_allow_html=True)
    try:  # forma moderna: el script corre directo en la pagina
        st.html(BUBBLES_JS + INPUTMODE_JS, unsafe_allow_javascript=True, width="content")
    except TypeError:  # Streamlit antiguo: respaldo con componente (iframe)
        components.html(BUBBLES_JS + INPUTMODE_JS, height=0)

def show(d, raw=()):
    """Tabla con diseño propio (color vino). raw = columnas cuyo contenido es HTML de confianza."""
    if d is None or len(d) == 0:
        st.html('<div class="vt"><div class="e">Sin datos todavía</div></div>')
        return
    def cell(v, c):
        if c in raw:
            return str(v)
        try:
            if pd.isna(v):
                return ""
        except (TypeError, ValueError):
            pass
        return _html.escape(str(v))
    head = "".join(f"<th>{_html.escape(str(c))}</th>" for c in d.columns)
    body = "".join("<tr>" + "".join(f"<td>{cell(v, c)}</td>" for v, c in zip(r, d.columns)) + "</tr>"
                   for r in d.itertuples(index=False))
    st.html(f'<div class="vt"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')

CUP = {1: "g", 2: "s", 3: "b"}

def rank_table(rk):
    d = rk.copy()
    d["Posicion"] = [f'<span class="medal {CUP[p]}">{TROPHY}</span>{p}' if p in CUP else str(p) for p in d["Posicion"]]
    show(d, raw=("Posicion",))

def podium(rk):
    top = rk.head(3)
    if top.empty:
        return
    by = {int(r.Posicion): r for r in top.itertuples()}
    cols = "".join(
        f'<div class="pl p{p}"><div class="cup {CUP[p]}">{TROPHY}</div><div class="nm">{_html.escape(str(by[p].Participante))}</div>'
        f'<div class="sc">{int(by[p].Puntaje)} pts</div><div class="ped">{p}</div></div>'
        for p in (2, 1, 3) if p in by)
    st.markdown(f'<div class="pod">{cols}</div>', unsafe_allow_html=True)

def who(nombre, apellido):
    ini = (str(nombre)[:1] + str(apellido)[:1]).upper()
    st.markdown(f'<div class="who"><span class="av">{_html.escape(ini)}</span><span>{_html.escape(f"{nombre} {apellido}")}</span></div>',
                unsafe_allow_html=True)

def my_pos(eid, email, sno=None):
    rk = ranking(eid, sno)
    m = rk.index[rk["Correo"] == email]
    return (int(rk["Posicion"][m[0]]), len(rk)) if len(m) else (None, len(rk))

def result_card(score, total, pos=None, n=None):
    """Tarjeta animada: copa que se llena, puntaje que sube y gotas de vino."""
    pct = round(score / total * 100) if total else 0
    title, sub = (("Paladar de sommelier", "Una cata casi perfecta.") if pct >= 90 else
                  ("Gran cata", "Se nota que sabes de vinos.") if pct >= 70 else
                  ("Buen comienzo", "Vas por buen camino, sigue catando.") if pct >= 40 else
                  ("A seguir catando", "Cada copa enseña algo nuevo."))
    rnd, drops = random.Random(score * 7 + total), ""
    if pct >= 60:
        for _ in range(18):
            z = rnd.randint(6, 12)
            drops += (f'<i class="dr" style="left:{rnd.randint(3, 97)}%;width:{z}px;height:{z}px;'
                      f'animation-delay:{rnd.random() * 2.6:.2f}s;background:{rnd.choice([WINE, GOLD, "#a24b57"])}"></i>')
    kf = ("<style>@property --n{syntax:'<integer>';inherits:false;initial-value:0}"
          "@property --pc{syntax:'<integer>';inherits:false;initial-value:0}"
          "@keyframes cnt{to{--n:@S@}}@keyframes cnp{to{--pc:@P@}}"
          "@keyframes fill{to{transform:translateY(@T@px)}}</style>"
          ).replace("@S@", str(score)).replace("@P@", str(pct)).replace("@T@", f"{13 * (1 - pct / 100):.2f}")
    bowl = "M12 15a5 5 0 0 0 5-5c0-2-.5-4-2-8H9c-1.5 4-2 6-2 8a5 5 0 0 0 5 5Z"
    glass = (f'<svg class="gl" viewBox="5 0 14 24"><defs><clipPath id="bw"><path d="{bowl}"/></clipPath>'
             '<linearGradient id="lq" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a24b57"/><stop offset="1" stop-color="#4a1520"/></linearGradient></defs>'
             f'<g clip-path="url(#bw)"><rect class="liq" x="5" y="2" width="14" height="13.6" fill="url(#lq)"/></g>'
             f'<path d="{bowl}" fill="none" stroke="{GOLD}" stroke-width=".6" stroke-linejoin="round"/>'
             f'<path d="M12 15v7M8 22h8" fill="none" stroke="{GOLD}" stroke-width=".6" stroke-linecap="round"/></svg>')
    chips = (f'<div class="chip"><b>{score}</b><span>Aciertos</span></div>'
             f'<div class="chip"><b>{total - score}</b><span>Por mejorar</span></div>')
    if pos:
        chips += f'<div class="chip"><b>{pos}° de {n}</b><span>Tu puesto</span></div>'
    st.markdown(kf + f'<div class="res">{drops}<div class="eb">Tu resultado</div>{glass}'
                f'<div><span class="num"></span><span class="of">/ {total}</span></div><div class="pcl"></div>'
                f'<h3>{title}</h3><div class="sub">{sub}</div><div class="chips">{chips}</div></div>', unsafe_allow_html=True)
    js = ("<script>(function(){const P=window.parent,D=P.document;D.querySelectorAll('.res:not(.seen)').forEach(function(e){"
          "e.classList.add('seen','arm');const io=new P.IntersectionObserver(function(es){es.forEach(function(x){"
          "if(x.isIntersecting){e.classList.add('go');io.disconnect();}});},{threshold:.45});io.observe(e);"
          "setTimeout(function(){e.classList.add('go');},6000);});})();</script>")
    try:
        st.html(js, unsafe_allow_javascript=True, width="content")
    except TypeError:
        components.html(js, height=0)

theme()

# ---------------- Base de datos (SQLite, sin borrados) ----------------
def conn():
    c = sqlite3.connect(DB, timeout=30, check_same_thread=False)  # espera en vez de fallar si hay muchos escribiendo
    c.execute("PRAGMA busy_timeout=30000")
    c.execute("PRAGMA synchronous=NORMAL")
    c.execute("PRAGMA temp_store=MEMORY")
    c.execute("PRAGMA cache_size=-20000")
    return c

# tablas de escritura frecuente (usuarios respondiendo): no invalidan el cache de lectura
_HOT = ("INTO DRAFTS", "INTO SESSIONS", "INTO STARTS", "INTO ANSWERS", "INTO USERS", "INTO FORMS", "INSERT INTO WINES", "INTO VOTES", "INTO CHEATS")

def _bust(sql):
    u = " ".join(sql.upper().split())
    if not any(h in u for h in _HOT) and "DELETE FROM SESSIONS" not in u:
        st.cache_data.clear()

def run(sql, args=()):
    c = conn()
    with c:
        cur = c.execute(sql, args)
    c.close()
    _bust(sql)
    return cur.lastrowid

def many(sql, rows):
    c = conn()
    with c:
        c.executemany(sql, rows)
    c.close()
    _bust(sql)

def df(sql, args=()):
    c = conn()
    d = pd.read_sql_query(sql, c, params=args)
    c.close()
    return d

def now():
    return now_cl().strftime("%Y-%m-%d %H:%M:%S")

TABLES = ["events", "questions", "event_questions", "users", "answers", "forms", "wines", "sets", "starts", "drafts", "fnames", "votes", "cheats"]

@st.cache_resource
def init():
    c = conn()
    c.execute("PRAGMA journal_mode=WAL")  # lecturas y escrituras simultaneas sin bloquearse
    c.executescript("""
    CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE,
        n_preguntas INTEGER DEFAULT 0, n_formularios INTEGER DEFAULT 0, activo INTEGER DEFAULT 0, creado TEXT);
    CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT, pregunta TEXT,
        a TEXT, b TEXT, c TEXT, d TEXT, correcta TEXT, creada TEXT);
    CREATE TABLE IF NOT EXISTS event_questions(event_id INTEGER, question_id INTEGER, PRIMARY KEY(event_id, question_id));
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, apellido TEXT,
        edad INTEGER, email TEXT UNIQUE, genero TEXT, creado TEXT);
    CREATE TABLE IF NOT EXISTS answers(event_id INTEGER, user_id INTEGER, question_id INTEGER,
        elegida TEXT, correcta INTEGER, ts TEXT, PRIMARY KEY(event_id, user_id, question_id));
    CREATE TABLE IF NOT EXISTS forms(event_id INTEGER, user_id INTEGER, form_no INTEGER, data TEXT, ts TEXT,
        PRIMARY KEY(event_id, user_id, form_no));
    CREATE TABLE IF NOT EXISTS sets(event_id INTEGER, set_no INTEGER, duracion INTEGER, PRIMARY KEY(event_id, set_no));
    CREATE TABLE IF NOT EXISTS starts(event_id INTEGER, user_id INTEGER, set_no INTEGER, inicio TEXT, PRIMARY KEY(event_id, user_id, set_no));
    CREATE TABLE IF NOT EXISTS drafts(event_id INTEGER, user_id INTEGER, question_id INTEGER, elegida TEXT, PRIMARY KEY(event_id, user_id, question_id));
    CREATE TABLE IF NOT EXISTS fnames(event_id INTEGER, form_no INTEGER, nombre TEXT, PRIMARY KEY(event_id, form_no));
    CREATE TABLE IF NOT EXISTS votes(event_id INTEGER, user_id INTEGER, form_no INTEGER, ts TEXT,
        PRIMARY KEY(event_id, user_id));
    CREATE TABLE IF NOT EXISTS cheats(event_id INTEGER, user_id INTEGER, set_no INTEGER, ts TEXT,
        PRIMARY KEY(event_id, user_id, set_no));
    CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, role TEXT, uid INTEGER, state TEXT, ts TEXT);
    CREATE TABLE IF NOT EXISTS wines(event_id INTEGER, form_no INTEGER, data TEXT, ts TEXT,
        PRIMARY KEY(event_id, form_no));
    """)
    # migracion: columna con la lista de alternativas (cantidad variable). Las preguntas antiguas siguen funcionando.
    cols = [r[1] for r in c.execute("PRAGMA table_info(questions)")]
    if "alts" not in cols:
        c.execute("ALTER TABLE questions ADD COLUMN alts TEXT")
    if "telefono" not in [r[1] for r in c.execute("PRAGMA table_info(users)")]:
        c.execute("ALTER TABLE users ADD COLUMN telefono TEXT")
    if "nivel" not in cols:
        c.execute("ALTER TABLE questions ADD COLUMN nivel TEXT")
    ecols = [r[1] for r in c.execute("PRAGMA table_info(event_questions)")]
    for col, typ in (("orden", "INTEGER"), ("alts", "TEXT"), ("correcta", "TEXT"), ("set_no", "INTEGER DEFAULT 1")):  # orden y alternativas propias de cada evento
        if col not in ecols:
            c.execute(f"ALTER TABLE event_questions ADD COLUMN {col} {typ}")
    if "n_sets" not in [r[1] for r in c.execute("PRAGMA table_info(events)")]:
        c.execute("ALTER TABLE events ADD COLUMN n_sets INTEGER DEFAULT 1")
    for t in TABLES:  # proteccion: ningun registro se puede borrar
        c.execute(f"CREATE TRIGGER IF NOT EXISTS nodel_{t} BEFORE DELETE ON {t} "
                  f"BEGIN SELECT RAISE(ABORT,'Registros protegidos: no se pueden borrar'); END;")
    c.executescript("""
    CREATE INDEX IF NOT EXISTS ix_ans_user ON answers(user_id);
    CREATE INDEX IF NOT EXISTS ix_ans_ev ON answers(event_id, user_id);
    CREATE INDEX IF NOT EXISTS ix_eq_ev ON event_questions(event_id, set_no);
    CREATE INDEX IF NOT EXISTS ix_forms_user ON forms(user_id);
    """)
    c.commit()
    c.close()
init()

# ---------------- Preguntas con alternativas variables ----------------
EQ = """SELECT q.id, q.pregunta, q.a, q.b, q.c, q.d, q.creada, q.nivel, COALESCE(x.alts, q.alts) AS alts,
        COALESCE(x.correcta, q.correcta) AS correcta, COALESCE(x.set_no, 1) AS set_no FROM questions q JOIN event_questions x ON x.question_id=q.id
        WHERE x.event_id=? ORDER BY COALESCE(x.orden, q.id), q.id"""

def place(alts, ok, how, target=None):
    """Reordena alternativas para un evento. how: banco | azar | pos. Devuelve (alts, letra_correcta)."""
    alts = list(alts); right = alts[LETTERS.index(ok)]
    if how == "azar":
        random.shuffle(alts)
    elif how == "pos":
        alts.remove(right); alts.insert(LETTERS.index(target), right)
    return alts, LETTERS[alts.index(right)]

def alts_of(r):
    """Lista de alternativas de una pregunta (formato nuevo en JSON o formato antiguo a,b,c,d)."""
    raw = r["alts"] if "alts" in r else None
    if isinstance(raw, str) and raw.strip():
        return json.loads(raw)
    return [r[k] for k in ("a", "b", "c", "d") if k in r and isinstance(r[k], str) and r[k] != ""]

def save_question(p, alts, ok, nivel=None):
    four = (list(alts) + [None] * 4)[:4]
    return run("INSERT INTO questions(pregunta,a,b,c,d,correcta,creada,alts,nivel) VALUES(?,?,?,?,?,?,?,?,?)",
               (p, *four, ok, now(), json.dumps(list(alts), ensure_ascii=False), nivel))

def qview(d):
    rows = []
    for _, r in d.iterrows():
        row = {"id": r["id"], "pregunta": r["pregunta"], "Nivel": r["nivel"] if "nivel" in r and isinstance(r["nivel"], str) else "-"}
        for L, a in zip(LETTERS, alts_of(r)):
            row[f"Alternativa {L}"] = a
        row["Correcta"] = r["correcta"]
        if "set_no" in r:
            row["Test"] = r["set_no"]
        rows.append(row)
    return pd.DataFrame(rows)

def import_questions(d):
    """Devuelve (filas_validas, errores). Columnas: pregunta, a, b, c... (hasta j) y correcta."""
    d = d.copy()
    d.columns = [str(c).strip().lower() for c in d.columns]
    falta = [c for c in ("pregunta", "correcta", "a", "b") if c not in d.columns]
    if falta:
        return [], [f"Faltan las columnas: {', '.join(falta)}"]
    rows, errors = [], []
    for n, rec in enumerate(d.to_dict("records"), start=2):
        kept = []
        for L in LETTERS:
            v = rec.get(L.lower())
            if v is not None and pd.notna(v) and str(v).strip() != "":
                kept.append((L, str(v).strip()))
        ok = str(rec["correcta"]).strip().upper()
        mp = {old: LETTERS[i] for i, (old, _) in enumerate(kept)}
        p = str(rec["pregunta"]).strip() if pd.notna(rec["pregunta"]) else ""
        if not p:
            errors.append(f"Fila {n}: pregunta vacía")
        elif len(kept) < 2:
            errors.append(f"Fila {n}: necesita al menos 2 alternativas")
        elif ok not in mp:
            errors.append(f"Fila {n}: la alternativa correcta '{ok}' no existe en esa fila")
        else:
            nv, good = norm_level(rec.get("nivel"))
            if not good:
                errors.append(f"Fila {n}: nivel '{rec.get('nivel')}' no válido (use {', '.join(LEVELS)})")
            else:
                rows.append((p, [v for _, v in kept], mp[ok], nv))
    return rows, errors

# ---------------- Formulario de cata (opciones basadas en la realidad vitivinicola chilena) ----------------
LUGARES = ["Viña / bodega", "Enoteca / bar de vinos", "Restaurante", "Casa particular",
    "Arica", "Iquique", "Calama", "Antofagasta", "Copiapó", "La Serena", "Coquimbo", "Ovalle", "Valparaíso",
    "Viña del Mar", "Casablanca", "Santiago", "Rancagua", "Santa Cruz", "Curicó", "Talca", "Chillán",
    "Concepción", "Temuco", "Valdivia", "Osorno", "Puerto Montt", "Punta Arenas"]

ANIOS = [str(y) for y in range(now_cl().year, 1989, -1)] + ["Sin añada (NV)"]

# Denominaciones de Origen de Chile (Decreto 464): regiones vitícolas, valles y zonas
ORIGENES = [
    "Valle de Copiapó (Atacama)", "Valle del Huasco (Atacama)",
    "Valle del Elqui (Coquimbo)", "Valle del Limarí (Coquimbo)", "Valle del Choapa (Coquimbo)",
    "Valle del Aconcagua (Aconcagua)", "Panquehue (Aconcagua)", "Valle de Casablanca (Aconcagua)",
    "Valle de San Antonio (Aconcagua)", "Valle de Leyda (Aconcagua)", "Valle del Marga-Marga (Aconcagua)",
    "Valle del Maipo (Valle Central)", "Alto Maipo (Valle Central)", "Pirque (Valle Central)", "Buin (Valle Central)",
    "Isla de Maipo (Valle Central)", "Talagante (Valle Central)", "Melipilla (Valle Central)",
    "Valle del Cachapoal (Rapel)", "Peumo (Rapel)", "Requínoa (Rapel)",
    "Valle de Colchagua (Rapel)", "Apalta (Rapel)", "Los Lingues (Rapel)", "Marchigüe (Rapel)",
    "Peralillo (Rapel)", "Palmilla (Rapel)", "Lolol (Rapel)", "Paredones (Rapel)",
    "Valle de Curicó (Valle Central)", "Valle de Teno (Valle Central)", "Valle de Lontué (Valle Central)",
    "Valle del Maule (Valle Central)", "Valle del Claro (Valle Central)", "Valle del Loncomilla (Valle Central)",
    "Valle del Tutuvén (Valle Central)", "Cauquenes (Valle Central)",
    "Valle del Itata (Sur)", "Valle del Biobío (Sur)", "Valle del Malleco (Sur)",
    "Valle del Cautín (Austral)", "Valle de Osorno (Austral)", "Varios valles de Chile (blend)",
]

CEPAS = [
    "Cabernet Sauvignon", "Merlot", "Carmenère", "Syrah", "Pinot Noir", "Malbec", "Cabernet Franc",
    "Petit Verdot", "País", "Carignan", "Cinsault", "Garnacha", "Mourvèdre", "Tempranillo", "Tannat",
    "Petite Sirah", "Sangiovese", "Marselan", "Touriga Nacional",
    "Sauvignon Blanc", "Chardonnay", "Riesling", "Gewürztraminer", "Viognier", "Semillón",
    "Moscatel de Alejandría", "Moscatel Rosada", "Pinot Gris", "Torontel", "Marsanne", "Roussanne",
    "Albariño", "Chenin Blanc", "Pedro Ximénez", "Sauvignon Gris",
]

ESTILOS = ["Tinto joven y frutal", "Tinto con crianza en barrica", "Tinto de guarda", "Blanco fresco y aromático",
    "Blanco con crianza en barrica", "Rosado", "Espumoso (método tradicional)", "Espumoso (método Charmat)",
    "Naranjo (maceración con pieles)", "Dulce / cosecha tardía", "Fortificado", "Pipeño / vino de campo",
    "Natural / mínima intervención", "Ensamblaje (blend)"]

CATEGORIAS = ["Varietal / Estándar", "Reserva", "Reserva Especial", "Reserva Privada", "Gran Reserva", "Superior",
    "Premium", "Súper Premium", "Ícono", "Edición limitada", "Single Vineyard (viñedo único)", "Espumoso",
    "Cosecha tardía"]

CASAS = ["Concha y Toro", "Viña Santa Rita", "Cousiño Macul", "Viña Undurraga", "Viña Errázuriz", "Viña Montes",
    "Viña Santa Carolina", "Casa Silva", "Lapostolle", "Emiliana", "Viu Manent", "De Martino", "Miguel Torres Chile",
    "Casas del Bosque", "Viña Veramonte", "Cono Sur", "Viña San Pedro", "Viña Tarapacá", "Viña Carmen",
    "Almaviva", "Viña Seña", "Viña Tabalí", "Viña Morandé", "MontGras", "Viña Ventisquero", "Viña Koyle",
    "Viña Leyda", "Haras de Pirque", "Viña Aresti", "Casa Marín", "Viña Matetic", "Viña Maipo", "Los Vascos",
    "Santa Ema", "Calyptra", "Vik", "Viña Pérez Cruz", "Viña Echeverría", "Viña Tamaya", "Viña Falernia",
    "Viña Bisquertt", "Odfjell", "J. Bouchon", "Garage Wine Co.", "Viña Anakena", "Luis Felipe Edwards",
    "Viña Requingua", "Viña Terranoble", "Clos des Fous"]

ALCOHOLES = [f"{v / 2:g}".replace(".", ",") + "%" for v in range(17, 32)]

COLORES = ["Rojo violáceo / púrpura", "Rojo rubí", "Rojo cereza", "Rojo granate", "Rojo teja / ladrillo",
    "Rojo con borde anaranjado", "Amarillo verdoso", "Amarillo pálido", "Amarillo pajizo", "Amarillo dorado",
    "Dorado intenso", "Ámbar", "Rosa pálido", "Rosa salmón", "Rosa frambuesa", "Cebolla", "Naranja"]

APARIENCIAS = ["Limpio y brillante", "Cristalino", "Brillante", "Opaco", "Turbio", "Con sedimento / depósito",
    "Con lágrimas o piernas marcadas", "Con burbuja fina y persistente", "Con burbuja gruesa",
    "Con cristales de tartrato"]

AROMAS = ["Cereza", "Frambuesa", "Frutilla", "Ciruela", "Mora", "Cassis (grosella negra)", "Arándano",
    "Higo / fruta pasa", "Limón", "Pomelo", "Lima", "Cáscara de naranja", "Manzana verde", "Manzana roja", "Pera",
    "Durazno", "Damasco", "Piña", "Maracuyá", "Lichi", "Melón", "Plátano", "Violeta", "Rosa", "Azahar", "Jazmín",
    "Pimentón / pimiento verde", "Pimiento rojo", "Hierba cortada", "Hojas de tomate", "Menta", "Eucalipto",
    "Hierbas aromáticas (tomillo, romero)", "Pimienta negra", "Clavo de olor", "Canela", "Regaliz", "Vainilla",
    "Coco", "Tostado", "Ahumado", "Madera / roble", "Cedro", "Tabaco", "Cuero", "Café", "Chocolate", "Caramelo",
    "Mantequilla", "Pan tostado / brioche", "Levadura", "Miel", "Frutos secos (almendra, avellana)",
    "Mineral / piedra mojada", "Tierra / sotobosque", "Hongos", "Yodo / salino", "Petróleo"]

SABORES = ["Frutas rojas maduras", "Frutas negras", "Fruta confitada", "Cítricos", "Frutas tropicales",
    "Manzana / pera", "Hierbas", "Pimentón", "Especias", "Pimienta", "Vainilla", "Madera tostada",
    "Chocolate amargo", "Café", "Cuero", "Tabaco", "Mineral", "Salino", "Miel", "Frutos secos", "Mantequilla",
    "Regaliz", "Dulzor residual", "Notas terrosas"]

MARIDAJES = ["Asado / carnes a la parrilla", "Cordero al palo", "Lomo vetado", "Pastel de choclo",
    "Empanadas de pino", "Empanadas de queso", "Cazuela", "Charquicán", "Porotos granados", "Humitas",
    "Pastel de jaiba", "Congrio frito", "Ceviche", "Locos con mayonesa", "Machas a la parmesana", "Erizos",
    "Ostiones", "Salmón", "Pescados blancos (merluza, reineta)", "Mariscos", "Sushi", "Pastas", "Pizza", "Risotto",
    "Pollo", "Cerdo", "Charcutería", "Quesos duros", "Quesos blandos", "Quesos azules", "Ensaladas",
    "Comida picante", "Postres de chocolate", "Postres de frutas", "Frutos secos", "Aperitivo / solo"]

CONCLUSIONES = ["Excelente, lo recomiendo", "Muy bueno", "Bueno", "Correcto, sin sobresalir", "Equilibrado y elegante",
    "Potente y estructurado", "Fresco y fácil de beber", "Necesita más guarda", "Pasó su mejor momento",
    "Presenta defectos", "No lo volvería a probar"]

# tipos: c = elegir (o escribir otra), m = elegir varias (o escribir otras), d = calendario,
#        s = escala 1-5, n = numero, t = texto libre
SECTIONS = [
    ("Datos del vino", [("Lugar","lugar","c",LUGARES),("Fecha","fecha","d",None),("Nombre del vino","nombre","t",None),
        ("Año","anio","c",ANIOS),("Origen/Zona","origen","c",ORIGENES),("Alc.","alc","c",ALCOHOLES),
        ("Variedad(es)/Cepas","cepas","m",CEPAS),("Estilo","estilo","c",ESTILOS),
        ("Categoría","categoria","c",CATEGORIAS),("Casa productora","casa","c",CASAS)]),
    ("Vista", [("Color","color","c",COLORES),("Capa (1-5)","capa","s",None),
        ("Apariencia general","apariencia","c",APARIENCIAS),("Untuosidad (1-5)","untuosidad","s",None)]),
    ("Nariz", [("Aromas","aromas","m",AROMAS),("Intensidad (1-5)","int_nariz","s",None)]),
    ("Boca", [("Dulzor","dulzor","s",None),("Salado","salado","s",None),("Acidez","acidez","s",None),
        ("Amargor","amargor","s",None),("Intensidad","int_boca","s",None),("Persistencia","persistencia","s",None),
        ("Astringencia","astringencia","s",None),("Alcohol","alcohol","s",None),("Balance","balance","s",None)]),
    ("Final", [("Sabores","sabores","m",SABORES),("Maridaje","maridaje","m",MARIDAJES),
        ("Conclusión","conclusion","c",CONCLUSIONES),("Precio ($ CLP)","precio","n",None),
        ("Calificación (1-5 estrellas)","calificacion","s",None)]),
]
LABEL = {f[1]: f[0] for _, fs in SECTIONS for f in fs}

OWN = "Escribir respuesta propia"

def pick(box, label, opts, cur, key, multi=False):
    """Lista desplegable sin teclado. La primera opcion es 'Escribir respuesta propia' y recien ahi aparece la casilla de texto."""
    opts = list(opts)
    if multi:
        if isinstance(cur, list):
            vals = cur
        elif cur:
            vals = [x.strip() for x in str(cur).split(",") if x.strip()]
        else:
            vals = []
        custom = [v for v in vals if v not in opts]
        sel = box.multiselect(label, [OWN] + opts, default=[v for v in vals if v in opts] + ([OWN] if custom else []),
                              key=key, placeholder="Elija una o más opciones")
        res = [v for v in sel if v != OWN]
        if OWN in sel:
            t = box.text_input(f"{label}: tus respuestas (separe con coma)", ", ".join(custom), key=key + "_o")
            res += [x.strip() for x in t.split(",") if x.strip()]
        return res
    v = str(cur) if cur not in ("", None) else ""
    own = v != "" and v not in opts
    allopts = [OWN] + opts
    r = box.selectbox(label, allopts, index=0 if own else (allopts.index(v) if v else None), key=key,
                      placeholder="Elija una opción")
    if r == OWN:
        return box.text_input(f"{label}: su respuesta", v if own else "", key=key + "_o")
    return r or ""

def parse_date(s):
    try:
        return datetime.strptime(str(s), "%d/%m/%Y").date()
    except ValueError:
        return date.today()

SEC_ICON = {
    "Datos del vino": '<path d="M10 2h4v4l1.5 3v11a2 2 0 0 1-2 2h-3a2 2 0 0 1-2-2V9L10 6z"/><path d="M8.5 14h7"/>',
    "Vista": '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "Nariz": '<path d="M17.7 7.7a2.5 2.5 0 1 1 1.8 4.3H2"/><path d="M9.6 4.6A2 2 0 1 1 11 8H2"/><path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>',
    "Boca": '<path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/>',
    "Final": '<circle cx="12" cy="8" r="6"/><path d="M15.5 13.9 17 22l-5-3-5 3 1.5-8.1"/>',
}
FIELD_ICON = {"lugar": "location_on", "fecha": "calendar_month", "nombre": "wine_bar", "anio": "history", "origen": "terrain",
    "alc": "percent", "cepas": "grass", "estilo": "style", "categoria": "workspace_premium", "casa": "storefront",
    "color": "palette", "capa": "layers", "apariencia": "visibility", "untuosidad": "water_drop", "aromas": "local_florist",
    "int_nariz": "air", "dulzor": "cake", "salado": "grain", "acidez": "science", "amargor": "coffee", "int_boca": "bolt",
    "persistencia": "timer", "astringencia": "texture", "alcohol": "liquor", "balance": "balance", "sabores": "restaurant",
    "maridaje": "dinner_dining", "conclusion": "rate_review", "precio": "payments", "calificacion": "star"}

def wine_card(base):
    """Datos del vino (los carga el admin): los participantes solo los ven."""
    if not base:
        st.info("El administrador aún no cargó los datos de este vino.")
        return
    items = ""
    for l, k, t, o in SECTIONS[0][1]:
        v = base.get(k, "")
        v = ", ".join(map(str, v)) if isinstance(v, list) else str(v)
        items += f'<div class="wi{" full" if t == "m" else ""}"><span>{_html.escape(l)}</span><b>{_html.escape(v) if v else "-"}</b></div>'
    st.markdown(f'<div class="wcard">{items}</div>', unsafe_allow_html=True)

def form_widgets(key, d, base=None):
    """base != None -> la seccion 'Datos del vino' se muestra de solo lectura (vista del participante)."""
    out = {}
    for sec, fs in SECTIONS:
        st.markdown(f'<div class="fsec"><span class="ico"><svg viewBox="0 0 24 24">{SEC_ICON.get(sec, "")}</svg></span><span>{sec}</span></div>',
                    unsafe_allow_html=True)
        if base is not None and sec == SECTIONS[0][0]:
            wine_card(base)
            continue
        cols, j = st.columns(2), 0
        for l, k, t, opts in fs:
            w, cur = f"{key}_{k}", d.get(k, "")
            lab = f":material/{FIELD_ICON[k]}: {l}" if k in FIELD_ICON else l
            if t == "m":  # campos de varias opciones: ancho completo
                box = st
                cols, j = st.columns(2), 0
            else:
                box = cols[j % 2]
                j += 1
            if t == "c":
                out[k] = pick(box, lab, opts, cur, w)
            elif t == "m":
                out[k] = pick(box, lab, opts, cur, w, multi=True)
            elif t == "d":
                v = box.date_input(lab, parse_date(cur), format="DD/MM/YYYY", key=w)
                out[k] = v.strftime("%d/%m/%Y") if v else ""
            elif t == "s":  # estrellas 1-5 (el orden va invertido para que el relleno CSS funcione)
                vals = ["5", "4", "3", "2", "1"]
                try:
                    i0 = vals.index(str(int(float(cur)))) if cur not in ("", None) else None
                except (TypeError, ValueError):
                    i0 = None
                with box.container(key=f"star_{w}"):
                    r = st.radio(lab, vals, index=i0, horizontal=True, key=w)
                out[k] = int(r) if r else ""
            elif t == "n":
                try:
                    n0 = int(float(cur))
                except (TypeError, ValueError):
                    n0 = 0
                out[k] = int(box.number_input(lab, min_value=0, step=500, value=n0, key=w))
            else:
                out[k] = box.text_input(lab, cur, key=w)
    return out

def expand(d):
    if d.empty:
        return d.drop(columns="data")
    x = pd.json_normalize(d["data"].map(json.loads)).rename(columns=LABEL)
    for c in x.columns:  # listas (opciones multiples) a texto, para pantalla y Excel
        x[c] = x[c].map(lambda v: ", ".join(map(str, v)) if isinstance(v, list) else v)
    return pd.concat([d.drop(columns="data").reset_index(drop=True), x], axis=1)

@st.cache_data(ttl=30, show_spinner=False)
def fnames(eid):
    d = df("SELECT form_no, nombre FROM fnames WHERE event_id=?", (eid,))
    return {int(r.form_no): r.nombre.strip() for r in d.itertuples() if isinstance(r.nombre, str) and r.nombre.strip()}

# ---------------- Consultas con cache (miles de usuarios leen lo mismo) ----------------
@st.cache_data(ttl=20, show_spinner=False)
def q_active():
    return df("SELECT * FROM events WHERE activo=1")

@st.cache_data(ttl=30, show_spinner=False)
def q_eq(eid):
    return df(EQ, (eid,))

@st.cache_data(ttl=600, show_spinner=False)
def q_user(uid):
    return df("SELECT * FROM users WHERE id=?", (uid,))

@st.cache_data(ttl=30, show_spinner=False)
def q_durs(eid):
    return dict(df("SELECT set_no, duracion FROM sets WHERE event_id=?", (eid,)).itertuples(index=False, name=None))

@st.cache_data(ttl=30, show_spinner=False)
def q_nsets(eid):
    return int(df("SELECT COALESCE(MAX(set_no),1) n FROM event_questions WHERE event_id=?", (eid,)).n[0])

# ---------------- Consultas comunes ----------------
@st.cache_data(ttl=10, show_spinner=False)
def ranking(eid, sno=None):
    j = " JOIN event_questions x ON x.event_id=a.event_id AND x.question_id=a.question_id AND x.set_no=?" if sno else ""
    d = df("""SELECT u.nombre||' '||u.apellido AS Participante, u.email AS Correo,
              SUM(a.correcta) AS Puntaje, SUM(a.elegida<>'') AS Respondidas, MAX(a.ts) AS Hora
              FROM answers a JOIN users u ON u.id=a.user_id""" + j + """ WHERE a.event_id=?
              GROUP BY u.id ORDER BY Puntaje DESC, Hora ASC""", (sno, eid) if sno else (eid,))
    d.insert(0, "Posicion", range(1, len(d) + 1))
    return d

def detalle(eid):
    return df("""SELECT u.nombre||' '||u.apellido AS Participante, q.pregunta AS Pregunta, a.elegida AS Elegida,
              COALESCE(x.correcta, q.correcta) AS Correcta, a.correcta AS Acierto, x.set_no AS Test, a.ts AS Hora
              FROM answers a JOIN users u ON u.id=a.user_id JOIN questions q ON q.id=a.question_id
              LEFT JOIN event_questions x ON x.event_id=a.event_id AND x.question_id=a.question_id
              WHERE a.event_id=? ORDER BY u.apellido, u.nombre, q.id""", (eid,))

def forms_df(eid):
    return expand(df("""SELECT f.form_no AS Formulario, u.nombre AS Nombre, u.apellido AS Apellido,
              u.email AS Correo, f.data, f.ts AS Registrado FROM forms f JOIN users u ON u.id=f.user_id
              WHERE f.event_id=? ORDER BY f.form_no, u.apellido""", (eid,)))

def wines_df(eid):
    return expand(df("SELECT form_no AS Formulario, data, ts AS Registrado FROM wines WHERE event_id=? ORDER BY form_no", (eid,)))

def votes_df(eid):
    """Votos por vino (formulario) del evento, ordenados de mayor a menor."""
    n = int(df("SELECT n_formularios FROM events WHERE id=?", (eid,)).n_formularios[0])
    v = df("SELECT form_no, COUNT(*) votos FROM votes WHERE event_id=? GROUP BY form_no", (eid,))
    m = dict(zip(v.form_no.astype(int), v.votos.astype(int))); nm = fnames(eid)
    d = pd.DataFrame([{"Formulario": k, "Vino": nm.get(k, f"Formulario {k}"), "Votos": m.get(k, 0)} for k in range(1, n + 1)])
    if d.empty:
        return pd.DataFrame(columns=["Posicion", "Formulario", "Vino", "Votos"])
    d = d.sort_values(["Votos", "Formulario"], ascending=[False, True]).reset_index(drop=True)
    d.insert(0, "Posicion", d["Votos"].rank(method="min", ascending=False).astype(int))
    return d

def votes_detail(eid):
    d = df("""SELECT u.nombre||' '||u.apellido AS Participante, u.email AS Correo, v.form_no AS Formulario, v.ts AS Hora
              FROM votes v JOIN users u ON u.id=v.user_id WHERE v.event_id=? ORDER BY v.ts""", (eid,))
    nm = fnames(eid)
    d.insert(3, "Vino", [nm.get(int(k), f"Formulario {int(k)}") for k in d["Formulario"]])
    return d

def build_excel(eid):
    sheets = {
        "Evento": df("SELECT * FROM events WHERE id=?", (eid,)),
        "Preguntas": qview(df(EQ, (eid,))),
        "Participantes": df("""SELECT * FROM users WHERE id IN (SELECT user_id FROM answers WHERE event_id=?
                        UNION SELECT user_id FROM forms WHERE event_id=?) ORDER BY apellido, nombre""", (eid, eid)),
        "Ranking general": ranking(eid),
        **{f"Ranking Test {t}": ranking(eid, t) for t in sorted({int(v) for v in df(EQ, (eid,)).set_no})},
        "Respuestas": detalle(eid),
        "Formularios participantes": forms_df(eid),
        "Fichas del admin": wines_df(eid),
        "Trampas": cheats_df(eid),
        "Votacion vino": votes_df(eid),
        "Votos (detalle)": votes_detail(eid),
    }
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for n, d in sheets.items():
            d.to_excel(w, sheet_name=n, index=False)
    return buf.getvalue()

def pick_event(key):
    ev = df("SELECT id, nombre, activo FROM events ORDER BY activo DESC, id DESC")
    if ev.empty:
        st.info("Primero cree un evento.")
        return None
    names = dict(zip(ev.id, ev.nombre))
    act = set(ev.id[ev.activo == 1])
    return int(st.selectbox("Evento", list(ev.id), key=key,
               format_func=lambda x: names[x] + (" - ACTIVO" if x in act else "")))

# ---------------- Login ----------------
def login():
    """Pantalla del QR: los participantes entran con un toque; el admin tiene su acceso aparte."""
    st.markdown('<div class="wsteps"><div><b>1</b>Inscríbete</div><div><b>2</b>Responde el quiz</div><div><b>3</b>Completa tus fichas de cata</div></div>',
                unsafe_allow_html=True)
    with st.container(key="cta"):
        if st.button("Quiero participar", icon=":material/wine_bar:", type="primary", key="cta_go"):
            st.session_state.role = "user"; st.rerun()
    _, c, _ = st.columns([1, 2, 1])
    with c.container(key="adminbox"):
        with st.expander("Acceso administración"):
            with st.form("login"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Ingresar"):
                    if (u, p) == ("admin", "admin"):
                        st.session_state.role = "admin"; st.rerun()
                    elif (u, p) == ("usuario", "usuario"):
                        st.session_state.role = "user"; st.rerun()
                    else:
                        st.error("Credenciales incorrectas")

def parse_dur(t):
    try:
        h, m, sec = [int(x) for x in str(t).strip().split(":")]
        tot = h * 3600 + m * 60 + sec
        return tot if min(h, m, sec) >= 0 and tot > 0 else None
    except ValueError:
        return None

def fmt_dur(sec):
    sec = max(0, int(sec))
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"

def rank_views(eid, admin):
    ns = q_nsets(eid)
    names = [f"Test {k}" for k in range(1, ns + 1)] + (["General"] if ns > 1 else [])
    for tb, nm in zip(st.tabs(names), names):
        with tb:
            rk = ranking(eid, int(nm.split()[1]) if nm != "General" else None)
            if admin:
                podium(rk)
                rank_table(rk)
            else:
                rank_table(rk.drop(columns=["Correo", "Hora"]).head(20))

def saved(eid, uid, qids):
    d = df("SELECT question_id, elegida FROM drafts WHERE event_id=? AND user_id=?", (eid, uid))
    m = dict(zip(d.question_id.astype(int), d.elegida))
    return {q: m[q] for q in qids if q in m}

def finish_set(eid, uid, sno, qs):
    """Cierra un test: guarda lo respondido; lo omitido queda como erroneo."""
    ss = st.session_state; kk = f"{eid}_{uid}_{sno}"
    qids = [int(x) for x in qs.id]
    ans = ss.get(f"ans_{kk}") or saved(eid, uid, qids)
    corr = dict(zip(qids, qs.correcta))
    many("INSERT OR IGNORE INTO answers VALUES(?,?,?,?,?,?)",
         [(eid, uid, x, ans.get(x, ""), int(ans.get(x) == corr[x]), now()) for x in qids])
    for key in (f"ans_{kk}", f"flg_{kk}", f"cur_{kk}", f"nav_{kk}", f"cf_{kk}", "qdir"):
        ss.pop(key, None)
    ss[f"showres_{eid}_{uid}"] = sno

GUARD_JS = """<script>(function(){
const P=window.parent,D=P.document,fe=window.frameElement;if(!fe)return;
let hit=false,tm=null,bt=null;
function alive(){return fe.isConnected;}
function fire(){const b=D.querySelector('.st-key-cheatbtn button');if(b)b.click();}
function cleanup(){D.removeEventListener('visibilitychange',onVis);P.removeEventListener('blur',onBlur);P.removeEventListener('focus',onFocus);clearTimeout(tm);clearTimeout(bt);}
function trig(){if(!alive()){cleanup();return;}if(hit)return;hit=true;fire();}
function onVis(){if(!alive()){cleanup();return;}if(D.hidden){clearTimeout(tm);tm=setTimeout(trig,1000);}else if(hit){fire();}}
function onBlur(){clearTimeout(bt);bt=setTimeout(function(){if(!alive())return;const a=D.activeElement;if(!D.hasFocus()&&!(a&&a.tagName==='IFRAME'))trig();},3000);}
function onFocus(){clearTimeout(bt);}
D.addEventListener('visibilitychange',onVis);P.addEventListener('blur',onBlur);P.addEventListener('focus',onFocus);
})();</script>"""

CHEAT_IMG = "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"

def show_img(b):
    try:
        st.image(b, width="stretch")
    except TypeError:
        st.image(b, use_container_width=True)

def cheat_screen(sno):
    st.markdown('<div class="cheatflash"></div>', unsafe_allow_html=True)
    with st.container(key="cheatbox"):
        show_img(base64.b64decode(CHEAT_IMG))
        st.markdown(f'<div class="cheatmsg">Antonio ha detectado algo extraño... Test {sno} descalificado: 0 puntos.</div>', unsafe_allow_html=True)

def cheat_set(eid, uid, sno, qs):
    """Descalifica el test: queda en 0 (todo en blanco) y se registra la trampa para el admin."""
    qids = [int(x) for x in qs.id]; ss = st.session_state; kk = f"{eid}_{uid}_{sno}"
    run("INSERT OR IGNORE INTO cheats VALUES(?,?,?,?)", (eid, uid, int(sno), now()))
    many("INSERT OR IGNORE INTO answers VALUES(?,?,?,?,?,?)", [(eid, uid, x, "", 0, now()) for x in qids])
    for key in (f"ans_{kk}", f"flg_{kk}", f"cur_{kk}", f"nav_{kk}", f"cf_{kk}", "qdir"):
        ss.pop(key, None)
    ss[f"showres_{eid}_{uid}"] = sno

def cheats_df(eid):
    d = df("""SELECT u.nombre||' '||u.apellido AS Participante, u.email AS Correo, c.set_no AS Test, c.ts AS Hora
              FROM cheats c JOIN users u ON u.id=c.user_id WHERE c.event_id=? ORDER BY c.ts DESC""", (eid,))
    return d

def sets_ui(qs, eid, uid, email):
    dur = q_durs(eid)
    sl = sorted({int(x) for x in qs.set_no}); multi = len(sl) > 1
    g = df("""SELECT x.set_no s, COUNT(*) n, SUM(a.correcta) p FROM answers a JOIN event_questions x
              ON x.event_id=a.event_id AND x.question_id=a.question_id WHERE a.event_id=? AND a.user_id=? GROUP BY x.set_no""", (eid, uid))
    got = {int(r.s): (int(r.n), int(r.p)) for r in g.itertuples()}
    cheated = {int(x) for x in df("SELECT set_no FROM cheats WHERE event_id=? AND user_id=?", (eid, uid)).set_no}
    done = [k for k in sl if got.get(k, (0, 0))[0] >= int((qs.set_no == k).sum())]
    pend = [k for k in sl if k not in done]
    ss = st.session_state; rk = f"showres_{eid}_{uid}"
    if done and (not pend or ss.get(rk) in done):
        if multi:
            rows = []
            for k in done:
                if k in cheated:
                    rows.append({"Test": k, "Aciertos": "Descalificado (0)", "Tu puesto": "-"})
                    continue
                p, n = my_pos(eid, email, k)
                rows.append({"Test": k, "Aciertos": f"{got[k][1]} / {got[k][0]}", "Tu puesto": f"{p}° de {n}"})
            show(pd.DataFrame(rows))
        k = ss.get(rk) if ss.get(rk) in done else done[-1]
        if k in cheated:
            cheat_screen(k)
        else:
            p, n = my_pos(eid, email, k)
            result_card(got[k][1], got[k][0], p, n)
        if pend:
            if st.button(f"Continuar al Test {pend[0]}", icon=":material/arrow_forward:", type="primary", key="cont_test"):
                ss.pop(rk, None)
                st.rerun()
            return
        if multi:
            st.success("Completaste todos los tests.")
        return
    k = pend[0]; sq = qs[qs.set_no == k].reset_index(drop=True); d = dur.get(k, 3600)
    st.markdown(f"##### Test {k} de {len(sl)}" if multi else "##### Cuestionario")
    stt = df("SELECT inicio FROM starts WHERE event_id=? AND user_id=? AND set_no=?", (eid, uid, k))
    if stt.empty:
        st.info(f"{len(sq)} preguntas · duración {fmt_dur(d)}. El tiempo parte al presionar el botón; al terminar, las preguntas sin responder cuentan como erróneas.")
        if st.button(f"Comenzar Test {k}" if multi else "Comenzar", icon=":material/play_arrow:", key=f"go{k}"):
            run("INSERT OR IGNORE INTO starts VALUES(?,?,?,?)", (eid, uid, k, now()))
            ss[f"intro_{eid}_{uid}_{k}"] = True
            st.rerun()
        return
    deadline = datetime.strptime(stt.inicio[0], "%Y-%m-%d %H:%M:%S") + timedelta(seconds=d)
    if now_cl() >= deadline:
        finish_set(eid, uid, k, sq)
        st.rerun()
    if st.button("trampa", key="cheatbtn"):  # boton oculto: lo acciona la guardia JS al salir de la app
        cheat_set(eid, uid, k, sq)
        st.rerun()
    if ss.pop(f"intro_{eid}_{uid}_{k}", None):
        st.markdown(splash(f"Test {k}" if multi else "Cuestionario", f"{len(sq)} preguntas · {fmt_dur(d)}"), unsafe_allow_html=True)
    components.html(GUARD_JS, height=0)
    quiz_ui(sq, eid, uid, k, deadline)

# ---------------- Modo usuario ----------------
_WAVE = "M30 0q15 -6 30 0t30 0t30 0t30 0t30 0t30 0V90H30Z"

def _svg_glass():
    """Copa dorada que se llena de vino y se mece (sin emoji)."""
    bowl = "M22 8H98C98 66 84 98 60 98C36 98 22 66 22 8Z"
    return (f'<svg class="sgl" viewBox="0 0 120 160"><defs><clipPath id="sgb"><path d="{bowl}"/></clipPath>'
            '<linearGradient id="sgw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b3202a"/><stop offset="1" stop-color="#4a1520"/></linearGradient></defs>'
            f'<g clip-path="url(#sgb)"><g class="sfill" style="transform:translateY(100px)"><g class="swv"><path d="{_WAVE}" transform="translate(-30 8)" fill="url(#sgw)"/></g>'
            '<circle class="sbb" cx="48" cy="70" r="2.4"/><circle class="sbb b2" cx="68" cy="78" r="2"/><circle class="sbb b3" cx="58" cy="62" r="1.6"/></g></g>'
            f'<path d="{bowl}" fill="none" stroke="#C9A24B" stroke-width="3" stroke-linejoin="round"/>'
            '<path d="M60 98V142" stroke="#C9A24B" stroke-width="4" stroke-linecap="round"/>'
            '<ellipse cx="60" cy="146" rx="28" ry="6" fill="none" stroke="#C9A24B" stroke-width="3"/></svg>')

def _svg_pour():
    """Botella que se inclina y sirve vino en una copa que se llena (SMIL, sin emoji)."""
    bowl = "M92 120H148C148 162 138 182 120 182C102 182 92 162 92 120Z"
    return ('<svg viewBox="-30 -45 290 262"><defs><clipPath id="spb"><path d="' + bowl + '"/></clipPath>'
            '<linearGradient id="spw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b3202a"/><stop offset="1" stop-color="#4a1520"/></linearGradient>'
            '<linearGradient id="spg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2f6b3d"/><stop offset="1" stop-color="#173a21"/></linearGradient></defs>'
            # copa: vino que sube (detras del cristal)
            '<g clip-path="url(#spb)"><g transform="translate(0 190)"><animateTransform attributeName="transform" type="translate" from="0 190" to="0 142" begin="1.1s" dur="1.4s" fill="freeze"/>'
            '<g><animateTransform attributeName="transform" type="translate" from="0 0" to="-60 0" dur="1.1s" repeatCount="indefinite"/>'
            f'<path d="{_WAVE}" transform="translate(30 0)" fill="url(#spw)"/></g></g></g>'
            # chorro de vino
            '<rect x="118.6" y="70" width="2.8" height="0" rx="1.4" fill="#b3202a"><animate attributeName="height" from="0" to="104" begin="1s" dur=".35s" fill="freeze"/></rect>'
            # copa (vidrio)
            f'<path d="{bowl}" fill="none" stroke="#C9A24B" stroke-width="3" stroke-linejoin="round"/>'
            '<path d="M120 182V204" stroke="#C9A24B" stroke-width="4" stroke-linecap="round"/>'
            '<ellipse cx="120" cy="207" rx="26" ry="5" fill="none" stroke="#C9A24B" stroke-width="3"/>'
            # botella: parte vertical y se inclina hasta servir (pivote en la boca)
            '<g transform="translate(120 66)"><g><animateTransform attributeName="transform" type="rotate" from="-20" to="36" begin=".25s" dur=".8s" fill="freeze"/>'
            '<path d="M-150 -20C-150 -26 -146 -28 -140 -28H-66C-50 -28 -42 -16 -36 -7L-20 -6V6L-36 7C-42 16 -50 28 -66 28H-140C-146 28 -150 26 -150 20Z" fill="url(#spg)" stroke="#C9A24B" stroke-width="1.4"/>'
            '<rect x="-20" y="-7" width="20" height="14" rx="2" fill="#C9A24B"/>'
            '<rect x="-122" y="-17" width="46" height="34" rx="3" fill="#f6e3b5"/>'
            '<path d="M-114 -6H-84M-114 2H-92M-114 9H-88" stroke="#722f37" stroke-width="2" stroke-linecap="round"/>'
            '<path d="M-60 -22C-52 -22 -46 -14 -42 -8" fill="none" stroke="#ffffff" stroke-opacity=".28" stroke-width="2" stroke-linecap="round"/></g></g></svg>')

def splash(t1, t2="", kind="glass"):
    """Transicion animada a pantalla completa (vino que sube + saludo). kind: glass (copa) | pour (botella sirviendo)."""
    art = f'<div class="sg pr">{_svg_pour()}</div>' if kind == "pour" else f'<div class="sg">{_svg_glass()}</div>'
    return (f'<div class="splash"><div class="pour"></div>{art}'
            f'<div class="st1">{_html.escape(t1)}</div><div class="st2">{_html.escape(t2)}</div></div>')

def glass():
    """Copa SVG estatica; el JS de register() la llena en vivo mientras se escribe."""
    bowl = "M22 8H98C98 66 84 98 60 98C36 98 22 66 22 8Z"
    return (f'<div class="glass"><svg viewBox="0 0 120 160"><defs><clipPath id="gb"><path d="{bowl}"/></clipPath>'
            f'<linearGradient id="gw" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b3202a"/><stop offset="1" stop-color="#4a1520"/></linearGradient></defs>'
            f'<g clip-path="url(#gb)"><g class="gfill" style="transform:translateY(100px)"><g class="gwv">'
            f'<path d="M-60 8q15 -8 30 0t30 0t30 0t30 0t30 0t30 0t30 0t30 0V120H-60Z" fill="url(#gw)"/></g>'
            f'<circle class="bb b1" cx="45" cy="70" r="2.5"/><circle class="bb b2" cx="70" cy="80" r="2"/><circle class="bb b3" cx="58" cy="60" r="1.6"/></g></g>'
            f'<path d="{bowl}" fill="none" stroke="#C9A24B" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="M60 98V142" stroke="#C9A24B" stroke-width="4" stroke-linecap="round"/>'
            f'<ellipse cx="60" cy="146" rx="28" ry="6" fill="none" stroke="#C9A24B" stroke-width="3"/></svg>'
            f'<div class="gmsg">Vamos a servirte una copa</div><div class="gbar"><i style="width:0%"></i></div></div>')

GLASS_JS = """<script>
(function(){
 var P=window.parent.document, last=-1;
 function inp(l){return P.querySelector('input[aria-label="'+l+'"]');}
 function len(l){var e=inp(l);return e?e.value.trim().length:0;}
 function tick(){
  var g=P.querySelector('.gfill'); if(!g) return;
  var em=(inp('Correo electrónico')||{value:''}).value.trim();
  var ok=/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(em);
  var p=Math.min(1,len('Nombre')/4)/3+Math.min(1,len('Apellido')/4)/3+(ok?1:Math.min(em.length,8)/8*.8)/3;
  if(ok&&len('Nombre')>0&&len('Apellido')>0) p=1;
  p=Math.round(p*100)/100; if(p===last) return; last=p;
  g.style.transform='translateY('+(100-p*88)+'px)';
  var m=P.querySelector('.gmsg'), bar=P.querySelector('.gbar i'), gl=P.querySelector('.glass');
  if(bar) bar.style.width=Math.round(p*100)+'%';
  if(m) m.textContent=p===0?'Vamos a servirte una copa':p<.34?'Descorchando...':p<.67?'Decantando...':p<1?'Casi lista...':'¡Salud! Todo listo';
  if(gl){gl.classList.remove('pop');void gl.offsetWidth;gl.classList.add('pop');gl.classList.toggle('full',p===1);}
 }
 setInterval(tick,150);
})();
</script>"""

def register():
    st.markdown(splash("Descorchando tu experiencia", "Prepara tu copa"), unsafe_allow_html=True)
    st.subheader("Registro de participante")
    with st.container(key="regbox"):
        st.markdown(glass(), unsafe_allow_html=True)
        components.html(GLASS_JS, height=0)
        a1, a2 = st.columns(2)
        nombre = a1.text_input("Nombre", key="rg_n")
        apellido = a2.text_input("Apellido", key="rg_a")
        b1, b2 = st.columns(2)
        edad = b1.number_input("Edad", 10, 120, 18, key="rg_e")
        genero = b2.selectbox("Género", ["Hombre", "Mujer", "Otro"], key="rg_g")
        email = st.text_input("Correo electrónico", key="rg_m", placeholder="tucorreo@ejemplo.com")
        tel_raw = st.text_input("Teléfono (opcional)", value="+56 ", key="rg_t", placeholder="+56 9 1234 5678")
        em = email.strip().lower()
        n = int(bool(nombre.strip())) + int(bool(apellido.strip())) + int("@" in em and "." in em)
        if st.button("¡Salud! Entrar a la cata", icon=":material/wine_bar:", type="primary", key="rg_go"):
            if n < 3:
                st.error("Complete nombre, apellido y un correo válido.")
                return
            dig = "".join(ch for ch in tel_raw if ch.isdigit())
            dig = dig[2:] if dig.startswith("56") else dig
            if dig and len(dig) != 9:
                st.error("El teléfono debe tener 9 dígitos después del +56 (ej: +56 9 1234 5678), o déjelo vacío.")
                return
            tel = "+56" + dig if dig else None
            ex = df("SELECT id FROM users WHERE email=?", (em,))
            if len(ex):
                st.session_state.uid = int(ex.id[0])
                if tel:
                    run("UPDATE users SET telefono=? WHERE id=?", (tel, int(ex.id[0])))
            else:
                st.session_state.uid = run(
                    "INSERT INTO users(nombre,apellido,edad,email,genero,creado,telefono) VALUES(?,?,?,?,?,?,?)",
                    (nombre.strip(), apellido.strip(), int(edad), em, genero, now(), tel))
            st.session_state.welcome = nombre.strip()
            st.rerun()

def quiz_ui(qs, eid, uid, sno, deadline):
    ss = st.session_state; N = len(qs); kk = f"{eid}_{uid}_{sno}"
    ans = ss.setdefault(f"ans_{kk}", saved(eid, uid, [int(x) for x in qs.id])); flg = ss.setdefault(f"flg_{kk}", set())
    ck, nk = f"cur_{kk}", f"nav_{kk}"
    qids = [int(x) for x in qs.id]
    cur = max(0, min(N - 1, ss.get(ck, 0)))

    def go(i):
        i = max(0, min(N - 1, int(i)))
        ss["qdir"] = "r" if i >= ss.get(ck, 0) else "l"
        ss[ck] = i

    def jump():
        v = ss.get(nk)
        if v:
            go(int(str(v).split()[0]) - 1)

    def setans(q):
        v = ss.get(f"r_{kk}_{q}")
        if v is not None and now_cl() < deadline:
            ans[q] = v
            run("INSERT INTO drafts VALUES(?,?,?,?) ON CONFLICT(event_id,user_id,question_id) DO UPDATE SET elegida=excluded.elegida", (eid, uid, q, v))

    def flag(q):
        flg.symmetric_difference_update({q})

    q = qs.iloc[cur]; qid = qids[cur]

    @st.fragment(run_every="10s")  # el segundero corre en el navegador; el servidor solo vigila el vencimiento
    def clock():
        rem = int((deadline - now_cl()).total_seconds())
        if rem <= 0:
            finish_set(eid, uid, sno, qs)
            st.rerun()
        components.html(TIMER_HTML.replace("__END__", str(int(deadline.replace(tzinfo=ZoneInfo("America/Santiago")).timestamp() * 1000))), height=46)
    clock()
    done = sum(1 for x in qids if x in ans)
    st.markdown(f'<div class="qmeta"><span>Pregunta <b>{cur + 1}</b> de {N}</span><span>{done} respondidas</span></div>'
                f'<div class="qprog"><i style="width:{done / N * 100:.0f}%"></i></div>', unsafe_allow_html=True)

    with st.container(key=f"q{ss.get('qdir', 'r')}_{cur}"):
        fl = '<span class="qflag">Para revisar</span>' if qid in flg else ""
        st.markdown(lvl_html(q["nivel"]) + f'<div class="qt">{_html.escape(str(q.pregunta))}{fl}</div>', unsafe_allow_html=True)
        o = dict(zip(LETTERS, alts_of(q)))
        with st.container(key="qopts"):
            _rk = dict(index=list(o).index(ans[qid]) if qid in ans else None, key=f"r_{kk}_{qid}",
                       format_func=lambda x, o=o: o[x], label_visibility="collapsed", on_change=setans, args=(qid,))
            try:
                st.radio("Alternativas", list(o), width="stretch", **_rk)
            except TypeError:
                st.radio("Alternativas", list(o), **_rk)

    c1, c2, c3 = st.columns(3)
    c1.button("Anterior", icon=":material/arrow_back:", on_click=go, args=(cur - 1,), disabled=cur == 0, width="stretch", key="bprev")
    c2.button("Quitar marca" if qid in flg else "Marcar para revisar", icon=":material/flag:", on_click=flag, args=(qid,), width="stretch", key="bflag")
    send = False
    if cur == N - 1:
        send = c3.button("Enviar respuestas", type="primary", icon=":material/send:", width="stretch", key="bsend")
    else:
        c3.button("Siguiente", icon=":material/arrow_forward:", on_click=go, args=(cur + 1,), width="stretch", key="bnext")

    labels = [f"{i + 1} " + ("⚑" if x in flg else "✓" if x in ans else "○") for i, x in enumerate(qids)]
    st.markdown('<div class="qleg">✓ respondida &nbsp;·&nbsp; ○ en blanco &nbsp;·&nbsp; ⚑ para revisar</div>', unsafe_allow_html=True)
    ss[nk] = labels[cur]
    with st.container(key="qnav"):
        if hasattr(st, "pills"):
            st.pills("Ir a la pregunta", labels, selection_mode="single", key=nk, on_change=jump, label_visibility="collapsed")
        else:
            st.selectbox("Ir a la pregunta", labels, key=nk, on_change=jump)

    blanks = [i + 1 for i, x in enumerate(qids) if x not in ans]
    if blanks:
        st.button(f"Ir a la primera en blanco (N.º {blanks[0]})", icon=":material/skip_next:", on_click=go, args=(blanks[0] - 1,), key="bblank")
    if send:
        if blanks and not ss.get(f"cf_{kk}"):
            ss[f"cf_{kk}"] = True
            st.warning(f"Te faltan {len(blanks)} pregunta(s) en blanco: {', '.join(map(str, blanks))}. Si envías de nuevo, quedarán como erróneas.")
        else:
            finish_set(eid, uid, sno, qs)
            st.rerun()

def vote_ui(eid, uid, n):
    nm = fnames(eid)
    lab = lambda k: nm.get(k, f"Formulario {k}")
    if n == 0:
        st.info("Este evento no tiene vinos para votar.")
        return
    ex = df("SELECT form_no FROM votes WHERE event_id=? AND user_id=?", (eid, uid))
    if len(ex):
        st.success(f"Tu voto ya quedó registrado: {lab(int(ex.form_no[0]))}. No se puede cambiar.")
        return
    st.markdown("Elige **el vino que más te gustó** de la noche. Solo puedes votar una vez y no podrás cambiarlo.")
    k = st.selectbox("Tu vino favorito", list(range(1, n + 1)), format_func=lab, index=None,
                     placeholder="Elija un vino", key=f"vt_{eid}")
    if k is not None and st.button("Votar por este vino", icon=":material/how_to_vote:", type="primary", key="vt_go"):
        run("INSERT OR IGNORE INTO votes VALUES(?,?,?,?)", (eid, uid, int(k), now()))
        st.rerun()

def user_app():
    if "uid" not in st.session_state:
        return register()
    uid = st.session_state.uid
    u = q_user(uid).iloc[0]
    who(u.nombre, u.apellido)
    _w = st.session_state.pop("welcome", None)
    if _w:
        st.markdown(splash(f"¡Salud, {_w}!", "Que comience la cata", "pour"), unsafe_allow_html=True)
    ev = q_active()
    if ev.empty:
        st.info("No hay un evento activo en este momento.")
        return
    e = ev.iloc[0]
    eid = int(e.id)
    st.subheader(e.nombre)
    secs = [":material/quiz: Preguntas", ":material/wine_bar: Formularios de cata", ":material/leaderboard: Ranking", ":material/how_to_vote: Votación"]
    if st.session_state.get("usec") not in secs:
        st.session_state.usec = secs[0]
    with st.container(key="usecbox"):
        (st.segmented_control if hasattr(st, "segmented_control") else st.pills)("Sección", secs, key="usec", label_visibility="collapsed")
    sec = st.session_state.get("usec") or secs[0]

    if sec == secs[0]:
        qs = q_eq(eid)
        if qs.empty:
            st.info("Aún no hay preguntas para este evento.")
        else:
            sets_ui(qs, eid, uid, u.email)

    elif sec == secs[1]:
        n = int(e.n_formularios)
        if n == 0:
            st.info("Este evento no tiene formularios de cata.")
        for k in range(1, n + 1):
            ex = df("SELECT data FROM forms WHERE event_id=? AND user_id=? AND form_no=?", (eid, uid, k))
            d = json.loads(ex.data[0]) if len(ex) else {}
            with st.expander(fnames(eid).get(k, f"Formulario {k}") + (" (completado)" if d else "")):
                with st.container():
                    _w = df("SELECT data FROM wines WHERE event_id=? AND form_no=?", (eid, k))
                    data = form_widgets(f"u{k}", d, base=json.loads(_w.data[0]) if len(_w) else {})
                    if st.button("Guardar formulario", type="primary", key=f"sv_u{k}"):
                        run("""INSERT INTO forms VALUES(?,?,?,?,?) ON CONFLICT(event_id,user_id,form_no)
                               DO UPDATE SET data=excluded.data, ts=excluded.ts""",
                            (eid, uid, k, json.dumps(data, ensure_ascii=False), now()))
                        st.success("Formulario guardado")

    elif sec == secs[2]:
        rank_views(eid, False)

    else:
        vote_ui(eid, uid, int(e.n_formularios))

# ---------------- Modo admin ----------------
def pag_eventos():
    st.subheader("Eventos")
    with st.form("nuevo_ev"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre del evento (ej: Evento N°31)")
        nf = c2.number_input("Cantidad de formularios de cata", 0, 50, 6)
        if st.form_submit_button("Crear evento"):
            try:
                run("INSERT INTO events(nombre,n_formularios,creado) VALUES(?,?,?)", (nombre.strip(), int(nf), now()))
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Ya existe un evento con ese nombre (o el nombre está vacío).")
    show(df("SELECT id, nombre, n_preguntas, n_formularios, activo, creado FROM events ORDER BY id DESC"))
    eid = pick_event("ev_cfg")
    if eid is None:
        return
    e = df("SELECT * FROM events WHERE id=?", (eid,)).iloc[0]
    st.markdown("##### Formularios")
    nf = st.number_input("Cantidad de formularios", 0, 50, int(e.n_formularios), key=f"nf{eid}")
    if st.button("Actualizar cantidad de formularios"):
        run("UPDATE events SET n_formularios=? WHERE id=?", (int(nf), eid)); st.rerun()
    if int(e.n_formularios) > 0:
        nm = fnames(eid)
        with st.expander("Nombres de los formularios (ej: el nombre del vino)"):
            vals = {k: st.text_input(f"Formulario {k}", nm.get(k, ""), key=f"fn{eid}_{k}", placeholder=f"Formulario {k}")
                    for k in range(1, int(e.n_formularios) + 1)}
            if st.button("Guardar nombres", key=f"sfn{eid}"):
                many("INSERT INTO fnames VALUES(?,?,?) ON CONFLICT(event_id,form_no) DO UPDATE SET nombre=excluded.nombre",
                     [(eid, k, v.strip()) for k, v in vals.items()])
                st.success("Nombres guardados"); st.rerun()

    st.markdown("##### Tests y preguntas del evento")
    sel = df(EQ, (eid,))
    if len(sel):
        st.caption("Los tests de este evento ya quedaron guardados y bloqueados (preguntas, orden, alternativa correcta y duración).")
        sd = df("SELECT set_no AS Test, duracion FROM sets WHERE event_id=? ORDER BY set_no", (eid,))
        sd["Duración"] = sd.pop("duracion").map(fmt_dur)
        show(sd)
        show(qview(sel))
    else:
        bank = df("SELECT id, pregunta, alts, a, b, c, d, nivel FROM questions ORDER BY id")
        st.write(f"Preguntas en el banco: {len(bank)}")
        txt = dict(zip(bank.id, bank.pregunta)); nalt = {int(r.id): len(alts_of(r)) for _, r in bank.iterrows()}
        lv = {int(r.id): (r.nivel if isinstance(r.nivel, str) else "sin nivel") for _, r in bank.iterrows()}
        fmt = lambda i: f"{i} - [{lv[i]}] {txt[i][:70]} ({nalt[i]} alt.)"
        ns = int(st.number_input("Cantidad de tests (cada uno con su ranking)", 1, 50, 1, key=f"ns{eid}"))
        used, plan, bad = set(), [], False
        for k in range(1, ns + 1):
            with st.expander(f"Test {k}", expanded=(k == 1)):
                secs = parse_dur(st.text_input("Duración (hh:mm:ss)", "00:10:00", key=f"du{eid}_{k}"))
                if secs is None:
                    st.error("Formato inválido. Use hh:mm:ss (ej: 00:10:00)"); bad = True
                modo = st.radio("¿Cómo se eligen las preguntas?", ["Al azar desde el banco", "Elegir manualmente (en el orden que las marques)"], key=f"md{eid}_{k}")
                free = [int(i) for i in bank.id if int(i) not in used]
                if modo.startswith("Al azar"):
                    lvf = st.multiselect("Niveles a incluir", LEVELS + ["sin nivel"], default=LEVELS + ["sin nivel"], key=f"lf{eid}_{k}")
                    todo = st.checkbox("Usar todo el banco disponible (de esos niveles)", True, key=f"td{eid}_{k}")
                    pool = [i for i in free if lv[i] in lvf] if todo else [int(i) for i in st.multiselect("Preguntas candidatas", free, format_func=fmt, key=f"pc{eid}_{k}")]
                    mx = max(len(pool), 1)
                    n = st.number_input("Cantidad de preguntas a sortear", 1, mx, min(5, mx), key=f"nn{eid}_{k}")
                    sig, dk = (tuple(pool), int(n)), f"dr{eid}_{k}"
                    if st.button("Volver a sortear", key=f"rs{eid}_{k}"):
                        st.session_state.pop(dk, None)
                    if st.session_state.get(dk, (None,))[0] != sig:
                        st.session_state[dk] = (sig, random.sample(pool, min(int(n), len(pool))))
                    ch = st.session_state[dk][1]
                    st.caption("Sorteadas: " + " · ".join(f"{i}: {txt[i][:50]}" for i in ch))
                else:
                    ch = [int(i) for i in st.multiselect("Preguntas del test", free, format_func=fmt, key=f"pm{eid}_{k}")]
                how = st.radio("Posición de la alternativa correcta", ["Tal como está en el banco", "Aleatoria (se barajan las alternativas)", "Elegir una a una"], key=f"hw{eid}_{k}")
                tgt = {}
                if how.startswith("Elegir") and modo.startswith("Elegir"):
                    for i in ch:
                        tgt[i] = st.selectbox(f"Correcta en la pregunta {i}: {txt[i][:60]}", list(LETTERS[:nalt[i]]), key=f"tg{eid}_{k}_{i}")
                elif how.startswith("Elegir"):
                    st.caption("Con sorteo al azar se aplicará la posición del banco.")
                used.update(ch); plan.append((k, secs, ch, how, tgt))
        if st.button("Guardar tests del evento"):
            if len([i for p in plan for i in p[2]]) != len({i for p in plan for i in p[2]}):
                st.error("Hay preguntas repetidas entre tests.")
            elif bad or any(not p[2] for p in plan):
                st.error("Cada test necesita una duración válida y al menos una pregunta.")
            else:
                rows, o = [], 0
                for k, secs, ch, how, tgt in plan:
                    for i in ch:
                        o += 1
                        r = bank[bank.id == i].iloc[0]; q = df("SELECT correcta FROM questions WHERE id=?", (i,)).iloc[0]
                        mode = "azar" if how.startswith("Aleat") else ("pos" if i in tgt else "banco")
                        al, ok2 = place(alts_of(r), q.correcta, mode, tgt.get(i))
                        rows.append((eid, i, o, json.dumps(al, ensure_ascii=False), ok2, k))
                many("INSERT OR IGNORE INTO event_questions(event_id,question_id,orden,alts,correcta,set_no) VALUES(?,?,?,?,?,?)", rows)
                many("INSERT OR IGNORE INTO sets VALUES(?,?,?)", [(eid, p[0], p[1]) for p in plan])
                run("UPDATE events SET n_preguntas=?, n_sets=? WHERE id=?", (len(rows), ns, eid)); st.rerun()

    st.markdown("##### Estado")
    st.write("Estado actual: " + ("ACTIVO (visible para los participantes)" if e.activo else "inactivo"))
    c1, c2 = st.columns(2)
    if c1.button("Activar este evento"):
        if int(e.n_preguntas) == 0:
            st.error("Sortee las preguntas antes de activar.")
        else:
            run("UPDATE events SET activo=0"); run("UPDATE events SET activo=1 WHERE id=?", (eid,)); st.rerun()
    if c2.button("Desactivar / finalizar"):
        run("UPDATE events SET activo=0 WHERE id=?", (eid,)); st.rerun()

def pag_banco():
    st.subheader("Banco de preguntas")
    if "qmsg" in st.session_state:
        st.success(st.session_state.pop("qmsg"))
    k = st.session_state.setdefault("qk", 0)  # al guardar, cambia k y los campos quedan vacios
    st.markdown("##### Nueva pregunta")
    p = st.text_input("Pregunta", key=f"qp{k}")
    n = int(st.number_input(f"Cantidad de alternativas (mínimo 2, máximo {MAX_ALTS})", 2, MAX_ALTS, 4, key=f"qn{k}"))
    cols = st.columns(2)
    alts = [cols[i % 2].text_input(f"Alternativa {LETTERS[i]}", key=f"qa{k}_{i}") for i in range(n)]
    ok = st.selectbox("Alternativa correcta (solo una)", list(LETTERS[:n]), key=f"qok{k}")
    nv = st.selectbox("Nivel de la pregunta", ["Sin nivel"] + LEVELS, key=f"qlv{k}")
    if st.button("Guardar pregunta"):
        al = [a.strip() for a in alts]
        if not p.strip() or not all(al):
            st.error("Complete la pregunta y todas las alternativas.")
        elif len({a.lower() for a in al}) < len(al):
            st.error("Hay alternativas repetidas.")
        else:
            save_question(p.strip(), al, ok, None if nv == "Sin nivel" else nv)
            st.session_state.qk = k + 1
            st.session_state.qmsg = "Pregunta guardada"
            st.rerun()

    st.markdown("##### Carga masiva")
    up = st.file_uploader("CSV o Excel con columnas: pregunta, a, b, c, ... (hasta j) y correcta. Opcional: nivel (Novato, Aficionado, Avanzado, Experto, Maestro). "
                          "Las alternativas vacías se ignoran.", type=["csv", "xlsx"])
    tb = io.BytesIO()
    pd.DataFrame({"pregunta": ["¿Pregunta con 2 alternativas?", "¿Pregunta con 4 alternativas?", "¿Pregunta con 5 alternativas?"],
                  "a": ["Verdadero", "Opción 1", "Opción 1"], "b": ["Falso", "Opción 2", "Opción 2"],
                  "c": [None, "Opción 3", "Opción 3"], "d": [None, "Opción 4", "Opción 4"], "e": [None, None, "Opción 5"],
                  "correcta": ["A", "C", "E"], "nivel": ["Novato", "Avanzado", "Maestro"]}).to_excel(tb, index=False)
    st.download_button("Descargar plantilla Excel de ejemplo", tb.getvalue(), "plantilla_preguntas.xlsx", key="tpl")
    if up and st.button("Importar archivo"):
        try:
            d = pd.read_csv(up, dtype=str) if up.name.endswith(".csv") else pd.read_excel(up, dtype=str)
            rows, errors = import_questions(d)
            if errors:
                st.error("No se importó nada. " + " | ".join(errors[:5]) + (" ..." if len(errors) > 5 else ""))
            else:
                for p_, al, ok_, nv_ in rows:
                    save_question(p_, al, ok_, nv_)
                cnt = pd.Series([len(r_[1]) for r_ in rows]).value_counts().sort_index()
                st.success(f"{len(rows)} preguntas importadas y agregadas al banco (" + ", ".join(f"{v} con {k} alt." for k, v in cnt.items()) + ")")
        except Exception as ex:
            st.error(f"No se pudo importar: {ex}")

    b = df("SELECT * FROM questions ORDER BY id DESC")
    with st.expander("Cambiar el nivel de preguntas ya guardadas"):
        ids = st.multiselect("Preguntas", list(b.id), format_func=lambda i: f"{i} - {b[b.id == i].pregunta.iloc[0][:70]}", key="lvl_ids")
        nl = st.selectbox("Nuevo nivel", LEVELS + ["Sin nivel"], key="lvl_new")
        if st.button("Aplicar nivel") and ids:
            many("UPDATE questions SET nivel=? WHERE id=?", [(None if nl == "Sin nivel" else nl, int(i)) for i in ids])
            st.session_state.qmsg = f"Nivel actualizado en {len(ids)} pregunta(s)"; st.rerun()
    fl = st.multiselect("Filtrar por nivel", LEVELS, key="lvl_f")
    if fl:
        b = b[b.nivel.isin(fl)]
    st.write(f"Total en el banco: {len(b)} (se muestran las últimas 500)")
    show(qview(b.head(500)))

_frag = getattr(st, "fragment", None) or getattr(st, "experimental_fragment", None)

def live(fn, every="5s"):
    """Refresca solo (sin recargar la pagina) si esta version de Streamlit lo permite."""
    if _frag is None:
        return fn
    try:
        return _frag(run_every=every)(fn)
    except TypeError:
        return fn

def _participantes_live():
    d = df("SELECT id, nombre, apellido, edad, email, telefono, genero, creado AS ingreso FROM users ORDER BY ingreso DESC")
    s = st.text_input("Buscar", key="part_q")
    if s:
        d = d[d.apply(lambda r: s.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
    c1, c2 = st.columns(2)
    c1.metric("Total (en vivo)", len(d))
    with c2:
        show(d["genero"].value_counts().rename_axis("Género").reset_index(name="Cantidad"))
    st.caption("Se actualiza solo cada 5 segundos. Los últimos en ingresar aparecen primero.")
    show(d)

def pag_participantes():
    st.subheader("Participantes registrados")
    live(_participantes_live)()

def _trampas_live(eid):
    d = cheats_df(eid)
    st.metric("Trampas detectadas", len(d))
    if d.empty:
        st.info("Nadie ha hecho trampa (por ahora).")
    else:
        show(d)
    st.caption("Se actualiza solo cada 5 segundos.")

def pag_resultados():
    st.subheader("Respuestas y ranking")
    eid = pick_event("ev_res")
    if eid is None:
        return
    t1, t2, t3, t4 = st.tabs([":material/emoji_events: Ranking", ":material/fact_check: Detalle de respuestas", ":material/how_to_vote: Votación de vinos", ":material/gpp_bad: Trampas"])
    with t1:
        rank_views(eid, True)
    with t2:
        show(detalle(eid))
    with t3:
        vd = votes_df(eid)
        if vd.empty:
            st.info("Este evento no tiene formularios (vinos).")
        else:
            tot = int(vd.Votos.sum())
            st.metric("Votos recibidos", tot)
            if tot:
                top = vd[vd.Posicion == 1]
                st.success("Mejor vino de la noche: " + " / ".join(top.Vino) + f" ({int(top.Votos.iloc[0])} votos)")
            show(vd[["Posicion", "Vino", "Votos"]])
            with st.expander("Detalle de votos por participante"):
                show(votes_detail(eid))
    with t4:
        live(_trampas_live)(eid)

def pag_formularios():
    st.subheader("Formularios de cata")
    eid = pick_event("ev_frm")
    if eid is None:
        return
    n = int(df("SELECT n_formularios FROM events WHERE id=?", (eid,)).n_formularios[0])
    t1, t2 = st.tabs([":material/wine_bar: Ficha del vino (admin)", ":material/groups: Formularios de participantes"])
    with t1:
        if n == 0:
            st.info("El evento no tiene formularios.")
        else:
            nm = fnames(eid); k = st.selectbox("Formulario N°", list(range(1, n + 1)), format_func=lambda x: nm.get(x, f"Formulario {x}"))
            ex = df("SELECT data FROM wines WHERE event_id=? AND form_no=?", (eid, k))
            d = json.loads(ex.data[0]) if len(ex) else {}
            st.caption("Los datos del vino son obligatorios: los participantes los verán sin poder editarlos.")
            with st.container():
                data = form_widgets(f"a{eid}_{k}", d)
                if st.button("Guardar ficha", type="primary", key=f"sv_a{eid}_{k}"):
                    falta = [fld[0] for fld in SECTIONS[0][1] if data.get(fld[1]) in ("", None, [])]
                    if falta:
                        st.error("Los datos del vino son obligatorios. Falta: " + ", ".join(falta))
                    else:
                        run("""INSERT INTO wines VALUES(?,?,?,?) ON CONFLICT(event_id,form_no)
                               DO UPDATE SET data=excluded.data, ts=excluded.ts""",
                            (eid, k, json.dumps(data, ensure_ascii=False), now()))
                        st.success("Ficha guardada")
    with t2:
        show(forms_df(eid))

def pag_excel():
    st.subheader("Descargar Excel del evento")
    eid = pick_event("ev_xls")
    if eid is None:
        return
    nombre = df("SELECT nombre FROM events WHERE id=?", (eid,)).nombre[0]
    st.download_button("Descargar Excel", build_excel(eid),
                       file_name=f"{nombre.replace(' ', '_')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def admin_nav():
    """Menu lateral con iconos (Material). Devuelve la funcion de la pagina activa."""
    pages = {"Eventos": (":material/calendar_month:", pag_eventos),
             "Banco de preguntas": (":material/quiz:", pag_banco),
             "Participantes": (":material/groups:", pag_participantes),
             "Respuestas y ranking": (":material/leaderboard:", pag_resultados),
             "Formularios de cata": (":material/wine_bar:", pag_formularios),
             "Descargar Excel": (":material/download:", pag_excel)}
    cur = st.session_state.setdefault("page", "Eventos")
    st.sidebar.markdown('<div class="nav-t">Administración</div>', unsafe_allow_html=True)
    for name, (icon, _) in pages.items():
        if st.sidebar.button(name, icon=icon, key=f"nav_{name}", width="stretch",
                             type="primary" if name == cur else "secondary"):
            st.session_state.page = name
            st.rerun()
    return pages[cur][1]

# ---------------- Sesion persistente (sobrevive a F5 / recargar en celular o computador) ----------------
import secrets

def _snapshot():
    """Estado minimo que hay que recordar: pagina del admin, pregunta actual y marcas del test."""
    ss = st.session_state
    d = {"page": ss.get("page"), "usec": ss.get("usec")}
    for k, v in list(ss.items()):
        if k.startswith("cur_") and isinstance(v, int):
            d[k] = v
        elif k.startswith("flg_") and isinstance(v, set):
            d[k] = sorted(v)
    return json.dumps(d, ensure_ascii=False)

def restore_session():
    ss = st.session_state
    tk = st.query_params.get("s")
    if not tk and not st.query_params.get("lo"):
        try:
            tk = st.context.cookies.get("bg_tk")
        except Exception:
            tk = None
    if "role" in ss or not tk:
        return
    try:
        r = df("SELECT role, uid, state, ts FROM sessions WHERE token=?", (tk,))
        if r.empty or not r.role[0] or (now_cl() - datetime.strptime(r.ts[0], "%Y-%m-%d %H:%M:%S")).days > 3650:
            st.query_params.pop("s", None)
            return
        ss.role = r.role[0]
        if pd.notna(r.uid[0]):
            ss.uid = int(r.uid[0])
        ss._tk = tk
        d = json.loads(r.state[0] or "{}")
        for k, v in d.items():
            if k == "page":
                if v:
                    ss.page = v
            elif k == "usec":
                if v:
                    ss.usec = v
            elif k.startswith("flg_"):
                ss[k] = set(v)
            else:
                ss[k] = v
        ss._snap = r.state[0]
    except Exception:
        pass

def persist_session():
    ss = st.session_state
    if "role" not in ss:
        return
    try:
        if "_tk" not in ss:
            ss._tk = secrets.token_urlsafe(16)
        if st.query_params.get("s") != ss._tk:
            st.query_params["s"] = ss._tk
        snap = _snapshot()
        uid = ss.get("uid")
        sig = f"{ss.role}|{uid}|{snap}"
        if ss.get("_sig") != sig:
            run("""INSERT INTO sessions VALUES(?,?,?,?,?) ON CONFLICT(token) DO UPDATE
                   SET role=excluded.role, uid=excluded.uid, state=excluded.state, ts=excluded.ts""",
                (ss._tk, ss.role, uid, snap, now()))
            ss._sig = sig
    except Exception:
        pass

def tk_sync(tk=""):
    """Guarda el token de sesion en el navegador (permanente) y lo recupera si la pestana se cerro."""
    components.html("""<script>(function(){const P=window.parent,TK=%s;let L=null;try{L=P.localStorage}catch(e){return}
const U=new URL(P.location.href);
if(U.searchParams.get('lo')){try{L.removeItem('bg_tk')}catch(e){}try{P.document.cookie='bg_tk=; max-age=0; path=/'}catch(e){}U.searchParams.delete('lo');P.history.replaceState(null,'',U.toString());return}
if(TK){try{L.setItem('bg_tk',TK)}catch(e){}try{P.document.cookie='bg_tk='+TK+'; max-age=315360000; path=/; SameSite=Lax'+(P.location.protocol==='https:'?'; Secure':'')}catch(e){}return}
if(U.searchParams.get('s'))return;
let t=null;try{t=L.getItem('bg_tk')}catch(e){}
if(!t)return;
try{if(P.sessionStorage.getItem('bg_try')===t)return;P.sessionStorage.setItem('bg_try',t)}catch(e){}
U.searchParams.set('s',t);P.location.replace(U.toString());
})();</script>""" % json.dumps(tk), height=0)

def end_session():
    tk = st.session_state.get("_tk")
    if tk:
        try:
            run("DELETE FROM sessions WHERE token=?", (tk,))
        except Exception:
            pass
    st.query_params.clear()
    st.query_params["lo"] = "1"

# ---------------- Main ----------------
restore_session()
st.markdown(HERO if "role" in st.session_state else HERO_LOGIN, unsafe_allow_html=True)
if "role" not in st.session_state:
    with st.container(key="prot"):
        show_img(HERO_BYTES)
    tk_sync("")
    login()
else:
    components.html("""<script>(function(){const P=window.parent,D=P.document;if(P.__sbctl)return;P.__sbctl=1;
const TG='[data-testid=stExpandSidebarButton],[data-testid=stSidebarCollapsedControl],[data-testid=stSidebarCollapseButton]';
const sb=()=>D.querySelector('section[data-testid=stSidebar]');
const open=()=>{const s=sb();return !!s&&s.getAttribute('aria-expanded')!=='false'};
let busy=0;
function fire(sel){const e=D.querySelector(sel);const b=e&&(e.tagName==='BUTTON'?e:e.querySelector('button,[role=button],a'))||e;if(b){busy=1;b.click();busy=0;return true}return false}
function close(){if(!open())return;fire('[data-testid=stSidebarCollapseButton]')}
D.addEventListener('click',function(ev){if(busy)return;const t=ev.target;if(!t||!t.closest)return;
 if(t.closest(TG)){if(open()){ev.preventDefault();ev.stopPropagation();close()}return}
 if(open()&&!t.closest('section[data-testid=stSidebar]'))close()},true);
let x0=0,y0=0;
D.addEventListener('touchstart',function(e){const t=e.touches[0];x0=t.clientX;y0=t.clientY},{passive:true});
D.addEventListener('touchend',function(e){if(!open())return;const t=e.changedTouches[0],dx=t.clientX-x0,dy=t.clientY-y0;
 if(Math.abs(dx)>70&&Math.abs(dx)>2*Math.abs(dy)&&(x0<D.documentElement.clientWidth*0.9))close()},{passive:true});
})();</script>""", height=0)
    st.markdown('<div class="sbtab" tabindex="0" title="Abrir menú"><svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="brand">' + ICON + '<span>The Brillat Game</span></div>', unsafe_allow_html=True)
    run_page = admin_nav() if st.session_state.role == "admin" else user_app
    st.sidebar.divider()
    if st.sidebar.button("Cerrar sesión", icon=":material/logout:", key="logout", width="stretch"):
        end_session()
        st.session_state.clear()
        st.rerun()
    try:
        run_page()
    finally:
        persist_session()
        tk_sync(st.session_state.get("_tk", ""))

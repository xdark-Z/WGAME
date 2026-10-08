import html as _html, streamlit as st, streamlit.components.v1 as components, sqlite3, pandas as pd, json, random, io
from datetime import datetime, date, timedelta

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
.sbtab{position:fixed;left:0;top:42%;z-index:999990;width:28px;height:90px;border-radius:0 14px 14px 0;background:linear-gradient(135deg,#4a1520,#8a2f3f);border:1px solid #C9A24B;border-left:0;
 display:none;align-items:center;justify-content:center;cursor:pointer;box-shadow:4px 6px 16px rgba(0,0,0,.35);outline:none;transition:width .25s}
.sbtab:hover{width:36px}.sbtab svg{width:18px;height:18px;fill:none;stroke:#f6e3b5;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}
.stApp:has(section[data-testid=stSidebar][aria-expanded=false]) .sbtab{display:flex}
/* menu cerrado: se oculta por completo (sin la barrita con letras cortadas) */
section[data-testid=stSidebar][aria-expanded=false]{visibility:hidden!important;width:0!important;min-width:0!important;overflow:hidden!important;transform:none!important;border:0!important;box-shadow:none!important}
.stApp:has(.sbtab:hover) section[data-testid=stSidebar][aria-expanded=false],.stApp:has(.sbtab:focus) section[data-testid=stSidebar][aria-expanded=false],section[data-testid=stSidebar][aria-expanded=false]:hover{visibility:visible!important;width:min(320px,85vw)!important;min-width:min(320px,85vw)!important;
 position:fixed!important;left:0;top:0;height:100vh!important;z-index:999991;overflow:auto!important;border-right:1px solid rgba(201,162,75,.4)!important;box-shadow:12px 0 40px rgba(0,0,0,.4)!important}
[data-testid=stExpandSidebarButton],[data-testid=stSidebarCollapsedControl]{position:fixed!important;top:14px;left:14px;z-index:999995;width:auto!important;height:auto!important}
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
.stApp:has(.hdr.lg) [data-testid=stForm]{max-height:0;opacity:0;overflow:hidden;padding-top:0;padding-bottom:0;border-width:0;margin-top:-28px;transform:translateY(-30px) scale(.96);
 pointer-events:none;transition:max-height .7s ease .9s,opacity .5s ease .9s,transform .6s ease .9s,padding .6s ease .9s,margin .6s ease .9s}
.stApp:has(.hdr.lg:hover) [data-testid=stForm],.stApp:has(.hdr.lg:focus-within) [data-testid=stForm],.stApp:has(.hdr.lg) [data-testid=stForm]:hover,.stApp:has(.hdr.lg) [data-testid=stForm]:focus-within{
 max-height:700px;opacity:1;padding-top:1rem;padding-bottom:1rem;border-width:1px;margin-top:0;transform:none;pointer-events:auto;transition:max-height .8s cubic-bezier(.2,1,.3,1),opacity .6s,transform .7s cubic-bezier(.2,1.3,.4,1),padding .5s,margin .5s}
.stApp:has(.hdr.lg:hover) .hdr .hint,.stApp:has(.hdr.lg:focus-within) .hdr .hint{opacity:0;animation:none}

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
 .stApp:has(.hdr.lg) [data-testid=stForm]{max-height:none;opacity:1;overflow:visible;padding-top:30px;padding-bottom:30px;border-width:1px;margin-top:0;transform:none;pointer-events:auto;transition:none}
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
 if(!reduce)P.__wb.raf=requestAnimationFrame(draw);}
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
HERO_LOGIN = '<div class="hdr lg">' + _SP + _TT + '<img class="prot" tabindex="0" alt="The Brillat Game" src="data:image/jpeg;base64,' + HERO_IMG + '"><div class="hint">Toca o pasa el cursor para ingresar</div></div>'

def theme():
    st.markdown("<style>" + FONTS + CSS.replace("WINE", WINE).replace("GOLD", GOLD) + "</style>", unsafe_allow_html=True)
    try:  # forma moderna: el script corre directo en la pagina
        st.html(BUBBLES_JS, unsafe_allow_javascript=True, width="content")
    except TypeError:  # Streamlit antiguo: respaldo con componente (iframe)
        components.html(BUBBLES_JS, height=0)

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

theme()

# ---------------- Base de datos (SQLite, sin borrados) ----------------
def conn():
    return sqlite3.connect(DB)

def run(sql, args=()):
    c = conn()
    with c:
        cur = c.execute(sql, args)
    c.close()
    return cur.lastrowid

def many(sql, rows):
    c = conn()
    with c:
        c.executemany(sql, rows)
    c.close()

def df(sql, args=()):
    c = conn()
    d = pd.read_sql_query(sql, c, params=args)
    c.close()
    return d

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

TABLES = ["events", "questions", "event_questions", "users", "answers", "forms", "wines", "sets", "starts", "drafts", "fnames"]

@st.cache_resource
def init():
    c = conn()
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
    CREATE TABLE IF NOT EXISTS wines(event_id INTEGER, form_no INTEGER, data TEXT, ts TEXT,
        PRIMARY KEY(event_id, form_no));
    """)
    # migracion: columna con la lista de alternativas (cantidad variable). Las preguntas antiguas siguen funcionando.
    cols = [r[1] for r in c.execute("PRAGMA table_info(questions)")]
    if "alts" not in cols:
        c.execute("ALTER TABLE questions ADD COLUMN alts TEXT")
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

ANIOS = [str(y) for y in range(datetime.now().year, 1989, -1)] + ["Sin añada (NV)"]

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

def pick(box, label, opts, cur, key, multi=False):
    """Lista desplegable con opciones; el usuario tambien puede escribir su propia respuesta."""
    if multi:
        if isinstance(cur, list):
            vals = cur
        elif cur:
            vals = [x.strip() for x in str(cur).split(",") if x.strip()]
        else:
            vals = []
    else:
        vals = [str(cur)] if cur not in ("", None) else []
    allopts = list(opts) + [v for v in vals if v not in opts]
    try:
        if multi:
            return box.multiselect(label, allopts, default=vals, key=key, accept_new_options=True,
                                   placeholder="Elija una o más opciones, o escriba la suya")
        r = box.selectbox(label, allopts, index=allopts.index(vals[0]) if vals else None, key=key,
                          accept_new_options=True, placeholder="Elija una opción o escriba la suya")
        return r or ""
    except TypeError:  # version antigua de Streamlit: opcion "Otra" con casilla de texto
        if multi:
            sel = box.multiselect(label, allopts, default=vals, key=key)
            own = box.text_input(f"{label}: otras (separe con coma)", key=key + "_o")
            return sel + [x.strip() for x in own.split(",") if x.strip()]
        OTRA = "Otra (escribir abajo)"
        r = box.selectbox(label, allopts + [OTRA], index=allopts.index(vals[0]) if vals else None, key=key)
        if r == OTRA:
            return box.text_input(f"{label}: su respuesta", key=key + "_o")
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

def form_widgets(key, d):
    out = {}
    for sec, fs in SECTIONS:
        st.markdown(f'<div class="fsec"><span class="ico"><svg viewBox="0 0 24 24">{SEC_ICON.get(sec, "")}</svg></span><span>{sec}</span></div>',
                    unsafe_allow_html=True)
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

def fnames(eid):
    d = df("SELECT form_no, nombre FROM fnames WHERE event_id=?", (eid,))
    return {int(r.form_no): r.nombre.strip() for r in d.itertuples() if isinstance(r.nombre, str) and r.nombre.strip()}

# ---------------- Consultas comunes ----------------
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
    _, c, _ = st.columns([1, 2, 1])
    with c.form("login"):
        st.subheader("Ingreso")
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
    ns = int(df("SELECT COALESCE(MAX(set_no),1) n FROM event_questions WHERE event_id=?", (eid,)).n[0])
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

def sets_ui(qs, eid, uid, email):
    dur = dict(df("SELECT set_no, duracion FROM sets WHERE event_id=?", (eid,)).itertuples(index=False, name=None))
    sl = sorted({int(x) for x in qs.set_no}); multi = len(sl) > 1
    g = df("""SELECT x.set_no s, COUNT(*) n, SUM(a.correcta) p FROM answers a JOIN event_questions x
              ON x.event_id=a.event_id AND x.question_id=a.question_id WHERE a.event_id=? AND a.user_id=? GROUP BY x.set_no""", (eid, uid))
    got = {int(r.s): (int(r.n), int(r.p)) for r in g.itertuples()}
    done = [k for k in sl if got.get(k, (0, 0))[0] >= int((qs.set_no == k).sum())]
    if multi and done:
        rows = []
        for k in done:
            p, n = my_pos(eid, email, k)
            rows.append({"Test": k, "Aciertos": f"{got[k][1]} / {got[k][0]}", "Tu puesto": f"{p}° de {n}"})
        show(pd.DataFrame(rows))
    if done:
        k = done[-1]; p, n = my_pos(eid, email, k)
        result_card(got[k][1], got[k][0], p, n)
    pend = [k for k in sl if k not in done]
    if not pend:
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
            st.rerun()
        return
    deadline = datetime.strptime(stt.inicio[0], "%Y-%m-%d %H:%M:%S") + timedelta(seconds=d)
    if datetime.now() >= deadline:
        finish_set(eid, uid, k, sq)
        st.rerun()
    quiz_ui(sq, eid, uid, k, deadline)

# ---------------- Modo usuario ----------------
def register():
    st.subheader("Registro de participante")
    with st.form("reg"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre")
        apellido = c2.text_input("Apellido")
        edad = c1.number_input("Edad", 10, 120, 18)
        genero = c2.selectbox("Género", ["Hombre", "Mujer", "Otro"])
        email = st.text_input("Correo electrónico")
        if st.form_submit_button("Continuar"):
            email = email.strip().lower()
            if not (nombre.strip() and apellido.strip() and "@" in email):
                st.error("Complete nombre, apellido y un correo válido.")
                return
            ex = df("SELECT id FROM users WHERE email=?", (email,))
            if len(ex):
                st.session_state.uid = int(ex.id[0])
            else:
                st.session_state.uid = run(
                    "INSERT INTO users(nombre,apellido,edad,email,genero,creado) VALUES(?,?,?,?,?,?)",
                    (nombre.strip(), apellido.strip(), int(edad), email, genero, now()))
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
        if v is not None:
            ans[q] = v
            run("INSERT INTO drafts VALUES(?,?,?,?) ON CONFLICT(event_id,user_id,question_id) DO UPDATE SET elegida=excluded.elegida", (eid, uid, q, v))

    def flag(q):
        flg.symmetric_difference_update({q})

    q = qs.iloc[cur]; qid = qids[cur]

    @st.fragment(run_every="1s")
    def clock():
        rem = int((deadline - datetime.now()).total_seconds())
        if rem <= 0:
            finish_set(eid, uid, sno, qs)
            st.rerun()
        st.markdown(f'<div class="qtimer{" low" if rem < 60 else ""}">Tiempo restante&nbsp;{fmt_dur(rem)}</div>', unsafe_allow_html=True)
    clock()
    done = sum(1 for x in qids if x in ans)
    st.markdown(f'<div class="qmeta"><span>Pregunta <b>{cur + 1}</b> de {N}</span><span>{done} respondidas</span></div>'
                f'<div class="qprog"><i style="width:{done / N * 100:.0f}%"></i></div>', unsafe_allow_html=True)

    with st.container(key=f"q{ss.get('qdir', 'r')}_{cur}"):
        fl = '<span class="qflag">Para revisar</span>' if qid in flg else ""
        st.markdown(lvl_html(q["nivel"]) + f'<div class="qt">{_html.escape(str(q.pregunta))}{fl}</div>', unsafe_allow_html=True)
        o = dict(zip(LETTERS, alts_of(q)))
        with st.container(key="qopts"):
            st.radio("Alternativas", list(o), index=list(o).index(ans[qid]) if qid in ans else None, key=f"r_{kk}_{qid}",
                     format_func=lambda x, o=o: o[x], label_visibility="collapsed", on_change=setans, args=(qid,))

    c1, c2, c3 = st.columns(3)
    c1.button("Anterior", icon=":material/arrow_back:", on_click=go, args=(cur - 1,), disabled=cur == 0, width="stretch", key="bprev")
    c2.button("Quitar marca" if qid in flg else "Marcar para revisar", icon=":material/flag:", on_click=flag, args=(qid,), width="stretch", key="bflag")
    c3.button("Siguiente", icon=":material/arrow_forward:", on_click=go, args=(cur + 1,), disabled=cur == N - 1, width="stretch", key="bnext")

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
    if st.button("Enviar respuestas", type="primary", key="bsend"):
        if blanks and not ss.get(f"cf_{kk}"):
            ss[f"cf_{kk}"] = True
            st.warning(f"Te faltan {len(blanks)} pregunta(s) en blanco: {', '.join(map(str, blanks))}. Si envías de nuevo, quedarán como erróneas.")
        else:
            finish_set(eid, uid, sno, qs)
            st.rerun()

def user_app():
    if "uid" not in st.session_state:
        return register()
    uid = st.session_state.uid
    u = df("SELECT * FROM users WHERE id=?", (uid,)).iloc[0]
    who(u.nombre, u.apellido)
    ev = df("SELECT * FROM events WHERE activo=1")
    if ev.empty:
        st.info("No hay un evento activo en este momento.")
        return
    e = ev.iloc[0]
    eid = int(e.id)
    st.subheader(e.nombre)
    t1, t2, t3 = st.tabs([":material/quiz: Preguntas", ":material/wine_bar: Formularios de cata", ":material/leaderboard: Ranking"])

    with t1:
        qs = df(EQ, (eid,))
        if qs.empty:
            st.info("Aún no hay preguntas para este evento.")
        else:
            sets_ui(qs, eid, uid, u.email)

    with t2:
        n = int(e.n_formularios)
        if n == 0:
            st.info("Este evento no tiene formularios de cata.")
        for k in range(1, n + 1):
            ex = df("SELECT data FROM forms WHERE event_id=? AND user_id=? AND form_no=?", (eid, uid, k))
            d = json.loads(ex.data[0]) if len(ex) else {}
            with st.expander(fnames(eid).get(k, f"Formulario {k}") + (" (completado)" if d else "")):
                with st.form(f"f{k}"):
                    data = form_widgets(f"u{k}", d)
                    if st.form_submit_button("Guardar formulario"):
                        run("""INSERT INTO forms VALUES(?,?,?,?,?) ON CONFLICT(event_id,user_id,form_no)
                               DO UPDATE SET data=excluded.data, ts=excluded.ts""",
                            (eid, uid, k, json.dumps(data, ensure_ascii=False), now()))
                        st.success("Formulario guardado")

    with t3:
        rank_views(eid, False)

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

def pag_participantes():
    st.subheader("Participantes registrados")
    d = df("SELECT id, nombre, apellido, edad, email, genero, creado FROM users ORDER BY apellido, nombre")
    s = st.text_input("Buscar")
    if s:
        d = d[d.apply(lambda r: s.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
    c1, c2 = st.columns(2)
    c1.metric("Total", len(d))
    with c2:
        show(d["genero"].value_counts().rename_axis("Género").reset_index(name="Cantidad"))
    show(d)

def pag_resultados():
    st.subheader("Respuestas y ranking")
    eid = pick_event("ev_res")
    if eid is None:
        return
    t1, t2 = st.tabs([":material/emoji_events: Ranking", ":material/fact_check: Detalle de respuestas"])
    with t1:
        rank_views(eid, True)
    with t2:
        show(detalle(eid))

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
            with st.form(f"w{eid}_{k}"):
                data = form_widgets(f"a{eid}_{k}", d)
                if st.form_submit_button("Guardar ficha"):
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

# ---------------- Main ----------------
st.markdown(HERO if "role" in st.session_state else HERO_LOGIN, unsafe_allow_html=True)
if "role" not in st.session_state:
    login()
else:
    st.markdown('<div class="sbtab" tabindex="0" title="Abrir menú"><svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="brand">' + ICON + '<span>The Brillat Game</span></div>', unsafe_allow_html=True)
    run_page = admin_nav() if st.session_state.role == "admin" else user_app
    st.sidebar.divider()
    if st.sidebar.button("Cerrar sesión", icon=":material/logout:", key="logout", width="stretch"):
        st.session_state.clear()
        st.rerun()
    run_page()

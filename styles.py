"""Identidad visual: azul institucional, blanco y gris neutro."""
import base64
import os
from functools import lru_cache

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")


@lru_cache(maxsize=1)
def logo_b64():
    if not os.path.exists(LOGO_PATH):
        return ""
    with open(LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()


def logo_html(width=120, centered=True):
    b = logo_b64()
    if not b:
        return ""
    align = "display:block;margin:0 auto;" if centered else ""
    return f'<img src="data:image/png;base64,{b}" style="width:{width}px;{align}" alt="Logo UDONE"/>'


CSS = """
<style>
:root{--azul:#0B3C7A;--azul2:#1F5FA8;--azul-claro:#E8EFF8;--gris:#5F6B7A;--gris-claro:#F3F5F8;--borde:#D9DFE7;}
.stApp{background:#FFFFFF;color:#1F2933;}
html, body, [class*="css"]{font-family:"Segoe UI","Helvetica Neue",Arial,sans-serif;}
#MainMenu, footer{visibility:hidden;}
h1,h2,h3,h4{color:var(--azul);font-weight:600;}
section[data-testid="stSidebar"]{background:var(--gris-claro);border-right:1px solid var(--borde);}
section[data-testid="stSidebar"] *{color:#1F2933;}
.sb-brand{text-align:center;padding:6px 0 10px 0;border-bottom:2px solid var(--azul);margin-bottom:10px;}
.sb-brand .t1{color:var(--azul);font-weight:700;font-size:1.02rem;margin-top:8px;line-height:1.2;}
.sb-brand .t2{color:var(--gris);font-size:.78rem;}
.sb-user{background:#fff;border:1px solid var(--borde);border-left:4px solid var(--azul);border-radius:6px;
  padding:8px 10px;font-size:.85rem;margin-bottom:10px;}
.sb-user b{color:var(--azul);}
.hce-header{background:linear-gradient(90deg,var(--azul) 0%,var(--azul2) 100%);padding:16px 22px;border-radius:8px;margin-bottom:18px;}
.hce-header h2{color:#fff !important;margin:0;font-size:1.45rem;}
.hce-header p{color:#DCE7F5;margin:2px 0 0 0;font-size:.9rem;}
.pac-banner{background:var(--azul-claro);border:1px solid #C5D5EA;border-left:5px solid var(--azul);
  border-radius:6px;padding:10px 14px;margin:6px 0 14px 0;font-size:.92rem;}
.pac-banner b{color:var(--azul);}
.badge{display:inline-block;padding:2px 9px;border-radius:10px;font-size:.75rem;font-weight:600;}
.badge-ok{background:#E4EEF9;color:var(--azul);} .badge-gray{background:#E6E9ED;color:var(--gris);}
.login-card{background:#fff;border:1px solid var(--borde);border-top:5px solid var(--azul);border-radius:10px;
  padding:26px 30px;box-shadow:0 6px 24px rgba(11,60,122,.08);}
.login-title{text-align:center;color:var(--azul);font-weight:700;font-size:1.35rem;margin:8px 0 0 0;}
.login-sub{text-align:center;color:var(--gris);font-size:.88rem;margin-bottom:14px;}
.stButton>button,.stDownloadButton>button,div[data-testid="stFormSubmitButton"]>button{
  background:var(--azul);color:#fff;border:0;border-radius:6px;font-weight:600;}
.stButton>button:hover,.stDownloadButton>button:hover,div[data-testid="stFormSubmitButton"]>button:hover{
  background:var(--azul2);color:#fff;}
.stTabs [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid var(--borde);}
.stTabs [data-baseweb="tab"]{color:var(--gris);font-weight:600;}
.stTabs [aria-selected="true"]{color:var(--azul);border-bottom:3px solid var(--azul);}
div[data-testid="stExpander"]{border:1px solid var(--borde);border-radius:6px;}
.edu-note{color:var(--gris);font-size:.78rem;text-align:center;margin-top:12px;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)

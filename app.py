# ============================================================
# English / Deutsch Pitch & Talk + Immersive Vocab ── 統合・完全版
# 修正: ① google-genai 新APIに完全移行 (画像からの単語抽出も含む)
#       ② iPhone音声フォーマット自動判別 (音声入力解消)
#       ③ 「画像単語」「フラッシュ」タブの追加統合
# ============================================================
import streamlit as st
from google import genai
from google.genai import types
import json, base64, io, time, os, re, requests
from gtts import gTTS
from datetime import datetime
from PIL import Image

try:
    from pypdf import PdfReader; PDF_OK = True
except:
    try: from PyPDF2 import PdfReader; PDF_OK = True
    except: PDF_OK = False
try:
    from bs4 import BeautifulSoup; BS4_OK = True
except: BS4_OK = False

# ── MODEL NAME ──
GEMINI_MODEL = "gemini-3.5-flash"

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(page_title="Pitch & Talk Pro",
                   page_icon="🌐", layout="centered",
                   initial_sidebar_state="collapsed")

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp{background:#f0f2f5}
.block-container{padding-top:0!important;max-width:840px}
header[data-testid="stHeader"]{background:transparent}
.stTabs [data-baseweb="tab-list"]{background:white;border-bottom:2px solid #e2e8f0;
  gap:0;padding:0 6px;position:sticky;top:0;z-index:100;
  box-shadow:0 2px 8px rgba(0,0,0,.06)}
.stTabs [data-baseweb="tab"]{font-weight:700!important;font-size:11px!important;
  padding:11px 11px!important;border-radius:0!important;color:#94a3b8!important}
.stTabs [aria-selected="true"]{color:var(--acc,#1d4ed8)!important;
  border-bottom:3px solid var(--acc,#1d4ed8)!important;background:transparent!important}
.stTabs [data-baseweb="tab-panel"]{padding-top:14px!important}
.stButton>button{border-radius:12px!important;font-weight:700!important;
  transition:all .2s!important;border:none!important}
.stButton>button:hover{transform:translateY(-1px)!important;
  box-shadow:0 4px 14px rgba(0,0,0,.15)!important}
.stButton>button[kind="primary"]{background:var(--acc,#1d4ed8)!important}
.stTextArea textarea,.stTextInput input{border-radius:12px!important;
  border:2px solid #e5e7eb!important;font-family:inherit!important;
  transition:border-color .2s!important}
.stTextArea textarea:focus,.stTextInput input:focus{
  border-color:var(--acc,#1d4ed8)!important;box-shadow:none!important}
[data-testid="stSidebar"]{background:#1e293b!important}
[data-testid="stSidebar"] *{color:rgba(255,255,255,.85)!important}
[data-testid="stSidebar"] input{background:rgba(255,255,255,.1)!important;
  border:1px solid rgba(255,255,255,.2)!important;color:white!important;border-radius:8px!important}
.ep-card{background:white;border-radius:16px;padding:20px;margin:10px 0;
  box-shadow:0 2px 12px rgba(0,0,0,.07);border:1px solid #e8edf5}
.ep-script{border-radius:16px;padding:20px;margin-bottom:14px;
  border-left-width:6px;border-left-style:solid}
.ep-script-text{font-size:20px;font-weight:700;color:#1e293b;line-height:1.8;letter-spacing:.3px}
.ep-label{border-radius:20px;padding:4px 14px;font-size:11px;font-weight:800;
  display:inline-block;margin-bottom:10px;color:white;letter-spacing:.5px}
.ep-vocab{border-radius:20px;padding:4px 12px;font-size:12px;font-weight:600;
  display:inline-block;margin:3px}
.ep-qa{background:#f8fafc;border-radius:12px;padding:14px;margin-bottom:10px}
.ep-tip{background:#fffbeb;border:1px solid #fde68a;border-radius:14px;
  padding:14px 18px;margin:12px 0;font-size:13px;line-height:1.7}
.ep-score-box{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.ep-score-num{font-size:52px;font-weight:900;line-height:1}
.ep-bar-wrap{background:#f1f5f9;border-radius:8px;height:12px;overflow:hidden;margin-bottom:14px}
.ep-bar{height:100%;border-radius:8px}
.ep-chip-ok{background:#dcfce7;color:#16a34a;border-radius:6px;padding:3px 9px;
  font-weight:600;display:inline-block;margin:2px;font-size:13px}
.ep-chip-ng{background:#fee2e2;color:#dc2626;border-radius:6px;padding:3px 9px;
  font-weight:600;display:inline-block;margin:2px;font-size:13px;text-decoration:line-through}
.ep-chat-wrap{background:#f8fafc;border:1px solid #e2e8f0;border-radius:16px;padding:14px;
  min-height:200px;max-height:340px;overflow-y:auto;margin-bottom:10px}
.ep-bubble-user{border-radius:18px 18px 4px 18px;padding:10px 14px;
  margin:7px 0 7px 15%;font-size:13px;line-height:1.5;color:white}
.ep-bubble-ai{background:white;border:1px solid #e2e8f0;border-radius:18px 18px 18px 4px;
  padding:10px 14px;margin:7px 15% 7px 0;font-size:13px;line-height:1.5;
  box-shadow:0 1px 4px rgba(0,0,0,.05)}
.ep-bubble-label{font-size:11px;color:#94a3b8;margin-bottom:3px}
.ep-para{display:flex;gap:10px;align-items:center;padding:7px 12px;background:#fff7ed;
  border-radius:8px;margin-bottom:6px;font-size:13px;flex-wrap:wrap}
.ep-para-hard{text-decoration:line-through;color:#f87171}
.ep-para-easy{font-weight:800;color:#16a34a}
.ep-para-note{color:#94a3b8;font-size:11px}
.ep-filler-wrap{background:white;border:1px solid #e2e8f0;border-radius:16px;
  padding:14px;margin-top:20px}
.ep-filler-grid{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.ep-filler-card{border-radius:10px;padding:8px 12px}
.ep-filler-en{font-weight:700;font-size:12px}
.ep-filler-jp{color:#94a3b8;font-size:11px;margin-top:2px}
.ep-ph{text-align:center;padding:48px 20px;color:#94a3b8}
.ep-ph-icon{font-size:48px;margin-bottom:12px}
.ep-ph-title{font-size:15px;font-weight:700;margin-bottom:6px;color:#64748b}
.ep-ph-sub{font-size:12px}
.ep-alert-g{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;
  padding:12px;text-align:center;color:#16a34a;font-weight:700;font-size:13px;margin-top:12px}
.ep-alert-o{background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;
  padding:12px;text-align:center;color:#ea580c;font-size:12px;margin-top:12px}
.save-card{background:white;border:1px solid #e2e8f0;border-radius:14px;padding:16px;
  margin-bottom:12px;transition:box-shadow .2s}
.save-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.1)}

[data-testid="stAlert"][data-type="warning"]{
  background:#f0f9ff!important;border-color:#7dd3fc!important;color:#0369a1!important;border-radius:12px!important;}
[data-testid="stAlert"][data-type="info"]{
  background:#f0f9ff!important;border-color:#7dd3fc!important;color:#0369a1!important;border-radius:12px!important;}
[data-testid="stAlert"][data-type="success"]{border-radius:12px!important;}
[data-testid="stAlert"][data-type="error"]{border-radius:12px!important;}
[data-testid="stSpinner"]>div{border-radius:12px!important;}
[data-baseweb="select"] [data-baseweb="input"]{border-radius:10px!important;}
.stTextArea label,.stTextInput label,.stSelectbox label{
  font-size:12px!important;font-weight:700!important;color:#334155!important;}
</style>
""", unsafe_allow_html=True)


# ── 言語設定 ─────────────────────────────────────────────────
LANG = {
    'en': {
        'flag':'🇺🇸','name':'English','tts':'en',
        'app_title':'English Pitch & Talk',
        'sub_biz':'展示会・商談英語をマスター',
        'sub_daily':'日常英会話を基礎から学ぼう',
        'script_lbl':'英文スクリプト（チャンク読み）',
        'switch_btn':'🇩🇪 Deutschに切替',
        'persona_biz':'🧳 バイヤー','persona_daily':'💬 ネイティブ',
        'filler_label':'フィラーカード（時間かせぎフレーズ）',
        'accent':'#1d4ed8',
    },
    'de': {
        'flag':'🇩🇪','name':'Deutsch','tts':'de',
        'app_title':'Deutsch Pitch & Talk',
        'sub_biz':'展示会・商談ドイツ語をマスター',
        'sub_daily':'日常ドイツ会話を基礎から学ぼう',
        'script_lbl':'ドイツ語スクリプト（チャンク読み）',
        'switch_btn':'🇺🇸 Englishに切替',
        'persona_biz':'🧳 Käufer','persona_daily':'💬 Muttersprachler',
        'filler_label':'Filler-Karten（時間かせぎフレーズ・独語）',
        'accent':'#b45309',
    },
}

LEVELS = {
    "🌱 初学者 (A1)": {
        'en':"be動詞・have・like等の最基本動詞のみ。主語＋動詞の最小構造。5単語以内。",
        'de':"nur sein/haben/mögen. Einfachste Satzstruktur. Maximal 5 Wörter.",
    },
    "📗 基礎 (A2)": {
        'en':"中学英語。1文12単語以内。SVO構造のみ。関係代名詞・接続詞禁止。",
        'de':"Grundlegendes Deutsch. Max. 12 Wörter. Einfache SVO-Struktur.",
    },
    "📘 中級 (B1/B2)": {
        'en':"高校英語。接続詞（because/when）可。やや複雑な構造OK。",
        'de':"Mittelstufe. Konjunktionen (weil/obwohl) erlaubt.",
    },
    "📙 上級 (C1)": {
        'en':"ビジネス英語。受動態・完了形・専門用語適宜使用。",
        'de':"Geschäftsdeutsch. Passiv, Konjunktiv II, Fachvokabular erlaubt.",
    },
    "🚀 ネイティブ風": {
        'en':"ネイティブが日常的に使う自然な表現。慣用句・略語も使用可。",
        'de':"Natürliches Deutsch. Idiome und Umgangssprache erlaubt.",
    },
}

DAILY_SCENARIOS = {
    'en': {
        "🎯 おまかせ":"ユーザーの入力に最適な日常表現",
        "☕ カフェ/レストラン":"飲食店での注文、好みの表現、会計",
        "🗺️ 観光/道案内":"観光地での会話、道を聞く・教える",
        "🏨 ホテル/交通":"チェックイン、部屋のリクエスト、タクシー",
        "🛒 買い物":"商品の選び方、値段、返品・交換",
        "👋 自己紹介/雑談":"名前・職業・趣味の紹介、スモールトーク",
        "📞 電話/リモート":"ビジネス電話、オンライン会議",
        "🚨 緊急/トラブル":"困ったとき、体調不良、助けを求める",
        "✈️ 空港/機内":"搭乗手続き、入国審査、機内のやり取り",
    },
    'de': {
        "🎯 おまかせ":"passende Alltagsausdrücke",
        "☕ Café/Restaurant":"Bestellen, Präferenzen, Bezahlen",
        "🗺️ Tourismus/Wegbeschreibung":"Sehenswürdigkeiten, Weg fragen",
        "🏨 Hotel/Verkehr":"Check-in, Zimmerwünsche, Taxi",
        "🛒 Einkaufen":"Produktauswahl, Preise, Rückgabe",
        "👋 Vorstellung/Smalltalk":"Name, Beruf, Hobbys, Plauderei",
        "📞 Telefon/Remote":"Geschäftstelefonat, Online-Meeting",
        "🚨 Notfall/Probleme":"Hilfe suchen, Krankheit, Notfall",
        "✈️ Flughafen/Flug":"Boarding, Einreise, Bordgespräche",
    },
}

FILLERS = {
    'en': [
        ("That's a great question.","いい質問ですね"),
        ("Let me explain.","説明します"),
        ("In other words...","つまり..."),
        ("For example...","例えば..."),
        ("The key point is...","重要なのは..."),
        ("Could you repeat that?","繰り返してください"),
        ("One moment, please.","少々お待ちください"),
        ("I understand.","承知しました"),
        ("Good point!","おっしゃる通り"),
        ("Let me check.","確認させてください"),
    ],
    'de': [
        ("Das ist eine gute Frage.","いい質問ですね"),
        ("Lassen Sie mich erklären.","説明させてください"),
        ("Mit anderen Worten...","つまり..."),
        ("Zum Beispiel...","例えば..."),
        ("Der wichtigste Punkt ist...","重要なのは..."),
        ("Könnten Sie das wiederholen?","繰り返していただけますか？"),
        ("Einen Moment bitte.","少々お待ちください"),
        ("Ich verstehe.","承知しました"),
        ("Guter Punkt!","おっしゃる通り"),
        ("Lassen Sie mich das prüfen.","確認させてください"),
    ],
}


# ── HELPERS ──────────────────────────────────────────────────
def ac(is_biz, lang='en'):
    if is_biz:
        base = {"main":"#1d4ed8","light":"#eff6ff","border":"#bfdbfe"}
    else:
        base = {"main":"#0d9488","light":"#f0fdfa","border":"#99f6e4"}
    if lang == 'de':
        base["main"]  = "#b45309" if is_biz else "#0f766e"
        base["light"] = "#fffbeb" if is_biz else "#f0fdfa"
        base["border"]= "#fde68a" if is_biz else "#99f6e4"
    return base

def ph(name):
    return f"""<div class="ep-ph"><div class="ep-ph-icon">📝</div>
<div class="ep-ph-title">「📝 入力」タブで内容を入力してください</div>
<div class="ep-ph-sub">{name} はコンテンツ生成後に表示されます</div></div>"""

def gen_audio(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO(); tts.write_to_fp(fp); fp.seek(0)
        b64 = base64.b64encode(fp.read()).decode()
        return f"""<audio id="epA" style="width:100%;border-radius:12px;margin-bottom:8px;">
<source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>
<div style="display:flex;gap:8px;">
<button onclick="document.getElementById('epA').playbackRate=0.8;document.getElementById('epA').play();"
  style="flex:1;padding:9px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;cursor:pointer;font-weight:700;font-size:11px;">
  🐢 0.8x<br><span style="font-size:9px;opacity:.7;">ゆっくり</span></button>
<button onclick="document.getElementById('epA').playbackRate=1.0;document.getElementById('epA').play();"
  style="flex:1;padding:9px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;cursor:pointer;font-weight:700;font-size:11px;">
  ▶️ 1.0x<br><span style="font-size:9px;opacity:.7;">標準</span></button>
<button onclick="document.getElementById('epA').playbackRate=1.2;document.getElementById('epA').play();"
  style="flex:1;padding:9px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;cursor:pointer;font-weight:700;font-size:11px;">
  ⚡ 1.2x<br><span style="font-size:9px;opacity:.7;">速め</span></button>
</div>"""
    except Exception as e:
        return f'<div style="color:#ef4444;font-size:12px;">音声エラー: {e}</div>'

def detect_audio_mime(data: bytes) -> str:
    if not data or len(data) < 12: return 'audio/mp4'
    h = data[:12]
    if h[:4] == b'RIFF' and h[8:12] == b'WAVE': return 'audio/wav'
    if h[4:8] == b'ftyp' or h[8:12] == b'ftyp': return 'audio/mp4'
    if h[:4] == b'\x1aE\xdf\xa3': return 'audio/webm'
    if h[:4] == b'OggS': return 'audio/ogg'
    if h[:3] == b'ID3' or (h[0] == 0xFF and (h[1] & 0xE0) == 0xE0): return 'audio/mp3'
    return 'audio/mp4'

def extract_pdf(file) -> str:
    if not PDF_OK: return "※ requirements.txt に pypdf を追加してください"
    reader = PdfReader(io.BytesIO(file.read()))
    return "\n".join(p.extract_text() or "" for p in reader.pages[:10])[:3000]

def extract_url(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        if BS4_OK:
            soup = BeautifulSoup(r.text, "html.parser")
            for t in soup(["script","style","nav","footer","header"]): t.decompose()
            txt = soup.get_text(separator="\n", strip=True)
        else:
            txt = re.sub(r'<[^>]+>', '', r.text)
        return re.sub(r'\n{3,}', '\n\n', txt)[:3000]
    except Exception as e: return f"取得失敗: {e}"


# ── NEW API WRAPPERS (google-genai) ──────────────────────────
def call_text(prompt: str, system: str = "") -> str:
    if not st.session_state.get("_client"): raise RuntimeError("APIクライアント未初期化")
    cfg = types.GenerateContentConfig(system_instruction=system) if system else None
    resp = st.session_state["_client"].models.generate_content(
        model=GEMINI_MODEL, contents=prompt, config=cfg)
    return resp.text

def call_audio(prompt: str, audio_bytes: bytes) -> str:
    if not st.session_state.get("_client"): raise RuntimeError("APIクライアント未初期化")
    mime = detect_audio_mime(audio_bytes)
    resp = st.session_state["_client"].models.generate_content(
        model=GEMINI_MODEL,
        contents=[types.Part.from_text(prompt), types.Part.from_bytes(data=audio_bytes, mime_type=mime)])
    return resp.text

def extract_vocab_from_image(img_bytes: bytes, mime_type: str, lang: str = 'en') -> list:
    """Geminiを使って画像から単語をJSONとして抽出（新API版）"""
    if not st.session_state.get("_client"): raise RuntimeError("APIクライアント未初期化")
    
    target_lang = "英語" if lang == 'en' else "ドイツ語"
    prompt = f"""
    この画像に含まれる重要な{target_lang}の単語やフレーズを抽出し、以下のJSONフォーマットのリストで出力してください。
    Markdownの装飾（```json など）は省き、純粋なJSON配列のみを出力してください。
    [
      {{"word": "apple", "meaning": "りんご"}},
      {{"word": "negotiation", "meaning": "交渉"}}
    ]
    """
    resp = st.session_state["_client"].models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_text(prompt),
            types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
        ],
    )
    text = re.sub(r"

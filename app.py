# ============================================================
# English / Deutsch Pitch & Talk + Immersive Vocab ── ダークテーマ完全版
# ============================================================
import streamlit as st
from google import genai
from google.genai import types
import json
import base64
import io
import time
import os
import re
import requests
from gtts import gTTS

try:
    from pypdf import PdfReader
    PDF_OK = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
        PDF_OK = True
    except ImportError:
        PDF_OK = False

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False

# ── MODEL NAME ──
GEMINI_MODEL = "gemini-3.5-flash"

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="Pitch & Talk Pro",
    page_icon="🌐", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CSS (ダーク・ハイコントラストテーマ) ─────────────────────────
st.markdown("""
<style>
/* アプリ全体の背景と基本テキスト色 */
.stApp { background-color: #121212; }
.block-container { padding-top: 0 !important; max-width: 840px; }
header[data-testid="stHeader"] { background: transparent; }

/* Streamlitのデフォルトテキストを強制的に白・明るいグレーにする */
p, h1, h2, h3, h4, h5, h6, label, span, div.stMarkdown {
    color: #f8fafc !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #1e293b;
    border-bottom: 2px solid #334155;
    gap: 0;
    padding: 0 6px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 4px 12px rgba(0,0,0,.4);
}
.stTabs [data-baseweb="tab"] {
    font-weight: 700 !important;
    font-size: 11px !important;
    padding: 11px 11px !important;
    border-radius: 0 !important;
    color: #94a3b8 !important;
}
.stTabs [aria-selected="true"] {
    color: var(--acc, #3b82f6) !important;
    border-bottom: 3px solid var(--acc, #3b82f6) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 14px !important; }

/* Buttons & Inputs */
.stButton>button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    transition: all .2s !important;
    border: 1px solid #334155 !important;
    background: #1e293b !important;
    color: #f8fafc !important;
}
.stButton>button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(0,0,0,.4) !important;
    border-color: var(--acc, #3b82f6) !important;
}
.stTextArea textarea, .stTextInput input {
    border-radius: 12px !important;
    border: 2px solid #334155 !important;
    background: #0f172a !important;
    color: #f8fafc !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--acc, #3b82f6) !important;
    box-shadow: none !important;
}

/* Custom UI Components */
.ep-card {
    background: #1e293b;
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 12px rgba(0,0,0,.3);
    border: 1px solid #334155;
}
.ep-script {
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 14px;
    border-left-width: 6px;
    border-left-style: solid;
    background: #0f172a;
}
.ep-script-text {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff !important;
    line-height: 1.8;
}
.ep-label {
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 10px;
    color: white !important;
}
.ep-vocab {
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    margin: 3px;
    color: #ffffff !important;
}
.ep-ph {
    text-align: center;
    padding: 48px 20px;
    color: #64748b;
}
</style>
""", unsafe_allow_html=True)

# ── 言語・レベル設定 ──────────────────────────────────────────
LANG = {
    'en': {
        'flag': '🇺🇸', 'name': 'English', 'tts': 'en',
        'app_title': 'English Pitch & Talk',
        'sub_biz': '展示会・商談英語をマスター',
        'sub_daily': '日常英会話を基礎から学ぼう',
        'script_lbl': '英文スクリプト（チャンク読み）',
        'switch_btn': '🇩🇪 Deutschに切替',
        'persona_biz': '🧳 バイヤー',
        'persona_daily': '💬 ネイティブ',
    },
    'de': {
        'flag': '🇩🇪', 'name': 'Deutsch', 'tts': 'de',
        'app_title': 'Deutsch Pitch & Talk',
        'sub_biz': '展示会・商談ドイツ語をマスター',
        'sub_daily': '日常ドイツ会話を基礎から学ぼう',
        'script_lbl': 'ドイツ語スクリプト（チャンク読み）',
        'switch_btn': '🇺🇸 Englishに切替',
        'persona_biz': '🧳 Käufer',
        'persona_daily': '💬 Muttersprachler',
    },
}

LEVELS = {
    "🌱 初学者 (A1)": {
        'en': "be動詞・have・like等の最基本動詞のみ。主語＋動詞の最小構造。5単語以内。",
        'de': "nur sein/haben/mögen. Einfachste Satzstruktur. Maximal 5 Wörter.",
    },
    "📗 基礎 (A2)": {
        'en': "中学英語。1文12単語以内。SVO構造のみ。関係代名詞・接続詞禁止。",
        'de': "Grundlegendes Deutsch. Max. 12 Wörter. Einfache SVO-Struktur.",
    },
    "📘 中級 (B1/B2)": {
        'en': "高校英語。接続詞（because/when）可。やや複雑な構造OK。",
        'de': "Mittelstufe. Konjunktionen (weil/obwohl) erlaubt.",
    },
    "📙 上級 (C1)": {
        'en': "ビジネス英語。受動態・完了形・専門用語適宜使用。",
        'de': "Geschäftsdeutsch. Passiv, Konjunktiv II, Fachvokabular erlaubt.",
    }
}

DAILY_SCENARIOS = {
    'en': ["🎯 おまかせ", "☕ カフェ/レストラン", "🗺️ 観光/道案内", "🏨 ホテル/交通", "🛒 買い物", "👋 自己紹介/雑談", "🚨 緊急/トラブル"],
    'de': ["🎯 おまかせ", "☕ Café/Restaurant", "🗺️ Tourismus/Wegbeschreibung", "🏨 Hotel/Verkehr", "🛒 Einkaufen", "👋 Vorstellung/Smalltalk", "🚨 Notfall/Probleme"],
}

# ── HELPERS (ダークテーマ用カラーパレット) ─────────────────────
def ac(is_biz, lang='en'):
    if is_biz:
        base = {"main": "#3b82f6", "light": "#1e3a8a", "border": "#2563eb"}
    else:
        base = {"main": "#10b981", "light": "#064e3b", "border": "#059669"}
    
    if lang == 'de':
        base["main"] = "#f59e0b" if is_biz else "#14b8a6"
        base["light"] = "#78350f" if is_biz else "#134e4a"
        base["border"] = "#d97706" if is_biz else "#0d9488"
    return base

def ph(name):
    return f"""
    <div class="ep-ph">
        <div style="font-size:48px;margin-bottom:12px;">📝</div>
        <div style="font-size:15px;font-weight:700;margin-bottom:6px;color:#94a3b8;">「📝 入力」タブで内容を入力してください</div>
        <div style="font-size:12px;color:#64748b;">{name} はコンテンツ生成後に表示されます</div>
    </div>
    """

def gen_audio(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        b64 = base64.b64encode(fp.read()).decode()
        return f"""
        <audio id="epA" style="width:100%; border-radius:12px; margin-bottom:8px;" controls>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <div style="display:flex; gap:8px;">
            <button onclick="document.getElementById('epA').playbackRate=0.8; document.getElementById('epA').play();"
                style="flex:1; padding:9px 0; border:1px solid #334155; border-radius:10px; background:#1e293b; color:#f8fafc; cursor:pointer; font-weight:700;">
                🐢 0.8x
            </button>
            <button onclick="document.getElementById('epA').playbackRate=1.0; document.getElementById('epA').play();"
                style="flex:1; padding:9px 0; border:1px solid #334155; border-radius:10px; background:#1e293b; color:#f8fafc; cursor:pointer; font-weight:700;">
                ▶️ 1.0x
            </button>
            <button onclick="document.getElementById('epA').playbackRate=1.2; document.getElementById('epA').play();"
                style="flex:1; padding:9px 0; border:1px solid #334155; border-radius:10px; background:#1e293b; color:#f8fafc; cursor:pointer; font-weight:700;">
                ⚡ 1.2x
            </button>
        </div>
        """
    except Exception as e:
        return f'<div style="color:#ef4444; font-size:12px;">音声エラー: {e}</div>'

def detect_audio_mime(data: bytes) -> str:
    if not data or len(data) < 12: 
        return 'audio/mp4'
    h = data[:12]
    if h[:4] == b'RIFF' and h[8:12] == b'WAVE': return 'audio/wav'
    if h[4:8] == b'ftyp' or h[8:12] == b'ftyp': return 'audio/mp4'
    if h[:4] == b'\x1aE\xdf\xa3': return 'audio/webm'
    if h[:4] == b'OggS': return 'audio/ogg'
    if h[:3] == b'ID3' or (h[0] == 0xFF and (h[1] & 0xE0) == 0xE0): return 'audio/mp3'
    return 'audio/mp4'

def extract_pdf(file) -> str:
    if not PDF_OK: 
        return "※ requirements.txt に pypdf を追加してください"
    reader = PdfReader(io.BytesIO(file.read()))
    return "\n".join(p.extract_text() or "" for p in reader.pages[:10])[:3000]

def extract_url(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if BS4_OK:
            soup = BeautifulSoup(r.text, "html.parser")
            for t in soup(["script", "style", "nav", "footer", "header"]): 
                t.decompose()
            txt = soup.get_text(separator="\n", strip=True)
        else:
            txt = re.sub(r'<[^>]+>', '', r.text)
        return re.sub(r'\n{3,}', '\n\n', txt)[:3000]
    except Exception as e: 
        return f"取得失敗: {e}"

# ── NEW API WRAPPERS ─────────────────────────────────────────
def call_text(prompt: str, system: str = "") -> str:
    if not st.session_state.get("_client"): 
        raise RuntimeError("APIクライアント未初期化")
    cfg = types.GenerateContentConfig(system_instruction=system) if system else None
    resp = st.session_state["_client"].models.generate_content(
        model=GEMINI_MODEL, 
        contents=prompt, 
        config=cfg
    )
    return resp.text

def call_audio(prompt: str, audio_bytes: bytes) -> str:
    if not st.session_state.get("_client"): 
        raise RuntimeError("APIクライアント未初期化")
    mime = detect_audio_mime(audio_bytes)
    resp = st.session_state["_client"].models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_text(text=prompt), # エラー修正箇所
            types.Part.from_bytes(data=audio_bytes, mime_type=mime)
        ]
    )
    return resp.text

def extract_vocab_from_image(img_bytes: bytes, mime_type: str, lang: str = 'en') -> list:
    if not st.session_state.get("_client"): 
        raise RuntimeError("APIクライアント未初期化")
    
    target_lang = "英語" if lang == 'en' else "ドイツ語"
    prompt = f"""
    この画像に含まれる重要な{target_lang}の単語やフレーズを抽出し、以下のJSONフォーマットのリストで出力してください。
    Markdownの装飾は省き、純粋なJSON配列のみを出力してください。
    [
      {{"word": "apple", "meaning": "りんご"}},
      {{"word": "negotiation", "meaning": "交渉"}}
    ]
    """
    resp = st.session_state["_client"].models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_text(text=prompt), # エラー修正箇所
            types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
        ],
    )
    
    text = resp.text.replace("```json\n", "").replace("```json", "").replace("\n```", "").replace("```", "").strip()
    
    try: 
        return json.loads(text)
    except Exception as e:
        st.error(f"データの解析に失敗しました。詳細: {e}")
        return []

def do_generate(prompt: str, sys_p: str) -> dict:
    raw = call_text(prompt, system=sys_p)
    m = re.search(r'\{[\s\S]*\}', raw)
    if not m: 
        raise ValueError("JSONが見つかりません")
    return json.loads(m.group())

def transcribe(audio_bytes: bytes, lang: str = 'en') -> tuple:
    inst = "この音声を日本語として文字起こしし、テキストのみ出力してください。句読点は省略可。"
    try: 
        return call_audio(inst, audio_bytes).strip(), ""
    except Exception as e: 
        return "", str(e)

# ── PROMPT BUILDERS ──────────────────────────────────────────
def build_prompt(user_input, is_biz, level_key, lang, scenario=""):
    level_inst = LEVELS.get(level_key, LEVELS["📗 基礎 (A2)"])[lang]
    scene = ("Fachmesse/Business (Produkterklärung, Verhandlung)" if is_biz else f"Alltag – {scenario}") if lang == 'de' else ("展示会・ビジネス（製品説明・商談）" if is_biz else f"日常会話 ― {scenario}")
    target = "Deutschen" if lang == 'de' else "英語"
    rule = "Max. 12 Wörter pro Satz. SVO-Struktur. Grammatik dem Level anpassen." if lang == 'de' else "1文最大12単語。SVO構造優先。レベルに合わせた語彙・文法を厳守。"
    
    return f"""
以下の条件でスクリプトをJSONのみで生成してください（コードブロック不要）。
[入力文]: {user_input}
[目標言語]: {target}
[場面]: {scene}
[レベル指示]: {level_inst}
[ルール]: {rule}
{{
  "english": "{target}文（複数文はスペースで区切る）",
  "english_jp": "自然な日本語訳",
  "chunked": "スラッシュ区切り（Unser Produkt / ist leicht. / Es spart Energie.）",
  "grammar": "文法・フレーズ解説（日本語）",
  "vocab": {{"単語/Wort": "意味（日本語）"}},
  "blank_q": "穴埋め文（___）",
  "blank_a": "正解の単語",
  "hint": "ヒント（日本語）",
  "qa_pairs": [{{"question":"質問文","question_jp":"日本語訳","hint":"ヒント"}}],
  "paraphrases": [{{"difficult":"難しい表現","simple":"簡単な言い換え","note":"メモ（日本語）"}}]
}}
"""

# ── SESSION STATE ────────────────────────────────────────────
defaults = {
    "script_data": None,
    "chat_history": [],
    "saved_list": [],
    "voice_text": "",
    "url_text_cache": "",
    "language": "en",
    "_client": None, 
    "vocab_list": []
}
for k, v in defaults.items():
    if k not in st.session_state: 
        st.session_state[k] = v

# ── API KEY INIT ─────────────────────────────────────────────
api_key = ""
try: 
    api_key = st.secrets.get("GEMINI_API_KEY", st.secrets.get("API_KEY", ""))
except: 
    pass

if not api_key: 
    api_key = os.environ.get("GEMINI_API_KEY", "")

if api_key and st.session_state["_client"] is None:
    try: 
        st.session_state["_client"] = genai.Client(api_key=api_key)
    except Exception as e: 
        st.error(f"❌ クライアント初期化失敗: {e}")

lang = st.session_state.language
LS = LANG[lang]

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### {LS['flag']} {LS['app_title']}")
    st.markdown("AI言語トレーナー Pro")
    st.divider()
    
    if not api_key:
        mk = st.text_input("🔑 Gemini API Key", type="password")
        if mk:
            api_key = mk
            st.session_state["_client"] = genai.Client(api_key=mk)
            st.success("✅ APIキー設定済み")
        else:
            st.warning("⚠️ APIキー未設定")
    else:
        st.success("✅ APIキー自動連携済み")

# ── HEADER & MODE ────────────────────────────────────────────
mode = st.radio("モード", ["🏢 展示会・ビジネス", "☕ 日常会話・基礎"], horizontal=True, label_visibility="collapsed")
is_biz = "展示会" in mode
C = ac(is_biz, lang)

st.markdown(f"<style>:root{{--acc:{C['main']};}}</style>", unsafe_allow_html=True)

sys_p = {
    ('en', True):  "あなたはビジネス英語の専門家です。展示会で通じるシンプルな英文を作成してください。",
    ('en', False): "あなたは日常英会話のコーチです。旅行・生活・雑談で使えるシンプルな英文を作成してください。",
    ('de', True):  "Sie sind Experte für Geschäftsdeutsch. Erstellen Sie einfache Sätze für Fachmessen.",
    ('de', False): "Sie sind Deutschcoach für den Alltag. Erstellen Sie einfache Sätze für Reisen und Alltag.",
}.get((lang, is_biz), "")

st.markdown(f"""
<div style="background:linear-gradient(135deg,{C['main']},{C['main']}cc); color:white; padding:18px 22px 14px; border-radius:16px; margin-bottom:14px; box-shadow: 0 4px 12px rgba(0,0,0,.3);">
  <div style="font-size:21px; font-weight:900; margin-bottom:3px;">
    {LS['flag']} {LS['app_title']}
  </div>
  <div style="font-size:11px; opacity:.9;">
    {LS['sub_biz'] if is_biz else LS['sub_daily']}
  </div>
</div>
""", unsafe_allow_html=True)

col_sp, col_lang = st.columns([3, 1])
with col_lang:
    if st.button(LS['switch_btn'], key="lang_toggle", use_container_width=True):
        st.session_state.language = 'de' if lang == 'en' else 'en'
        st.session_state.script_data = None
        st.session_state.chat_history = []
        st.rerun()

# ── TABS ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📝 入力", "📖 読解", "🔊 音読", "🎤 発音", "✏️ 練習", "🎭 会話", "📸 画像単語", "▶️ フラッシュ", "📚 保存帳"
])
data = st.session_state.script_data

# ============================================================
# TAB 1: INPUT
# ============================================================
with tab1:
    level_key = st.selectbox("📊 学習レベル", list(LEVELS.keys()), index=1)
    
    scenario = ""
    if not is_biz: 
        scenario = st.selectbox("🎬 シナリオ", DAILY_SCENARIOS[lang])

    im = st.radio("入力方法", ["✏️ テキスト", "🎤 音声入力", "📄 PDF", "🔗 URL"], horizontal=True)
    user_input = ""

    if im == "✏️ テキスト":
        user_input = st.text_area("スクリプトにしたい内容を入力（日本語でOK）", height=100)

    elif im == "🎤 音声入力":
        st.info("🎤 マイクで録音して日本語で話してください。自動で文字起こしされます。")
        voice_audio = st.audio_input("録音")
        if voice_audio and st.session_state.get("_client"):
            with st.spinner("文字起こし中..."):
                txt, err = transcribe(voice_audio.getvalue(), lang)
                if txt:
                    st.session_state.voice_text = txt
                    st.success(f"✅ 認識: {txt}")
        if st.session_state.voice_text:
            user_input = st.text_area("認識されたテキスト（編集可）", value=st.session_state.voice_text, height=80)

    elif im == "📄 PDF":
        st.info("📄 製品カタログなどのPDFをアップロードすると、内容を要約してスクリプトを作ります。")
        pdf_file = st.file_uploader("PDFファイルを選択", type=["pdf"])
        if pdf_file:
            if not PDF_OK: 
                st.error("❌ requirements.txt に pypdf を追加してください。")
            else:
                with st.spinner("PDFを読み込み中..."): 
                    pdf_text = extract_pdf(pdf_file)
                st.text_area("抽出テキスト", value=pdf_text[:400]+"…", height=70, disabled=True)
                user_input = f"[PDF内容]: {pdf_text}"

    elif im == "🔗 URL":
        st.info("🔗 会社HPや製品ページのURLを入力してスクリプトを生成します。")
        url_in = st.text_input("URLを入力", placeholder="https://example.com/product")
        if url_in and st.button("🔍 URLを取得"):
            with st.spinner("Webページを取得中..."): 
                url_text = extract_url(url_in)
            if "失敗" in url_text: 
                st.error(url_text)
            else:
                st.session_state["url_text_cache"] = url_text
                st.success("✅ 取得完了")
        if st.session_state.get("url_text_cache"): 
            user_input = f"[URL内容]: {st.session_state['url_text_cache']}"

    if st.button("✨ スクリプト＆学習コンテンツを生成する", type="primary", use_container_width=True):
        if not api_key or not st.session_state.get("_client"): 
            st.error("❌ APIキーまたはクライアントが設定されていません。")
        elif not user_input or not user_input.strip(): 
            st.warning("📝 テキスト等で内容を入力してください。")
        else:
            with st.spinner(f"AIが{LS['name']}スクリプトを作成中... ✨"):
                try:
                    if user_input.startswith("[PDF内容]") or user_input.startswith("[URL内容]"):
                        prompt = f"""
                        提供されたテキストを要約し、{LS['name']}の学習コンテンツをJSONのみで作成してください。
                        [テキスト]: {user_input[:2000]}
                        [場面]: {"ビジネス" if is_biz else "日常"}
                        """
                        prompt += build_prompt("", is_biz, level_key, lang, scenario)
                    else: 
                        prompt = build_prompt(user_input, is_biz, level_key, lang, scenario)
                    
                    result = do_generate(prompt, sys_p)
                    result.update({
                        "_source_ja": user_input[:100],
                        "_level": level_key,
                        "_mode": "business" if is_biz else "daily",
                        "_lang": lang
                    })
                    st.session_state.script_data = result
                    st.session_state.chat_history = []
                    data = result
                    st.success("✅ 生成完了！「📖 読解」タブに進んでください。")
                except Exception as e: 
                    st.error(f"❌ エラー: {e}")

# ============================================================
# TAB 2: SCRIPT
# ============================================================
with tab2:
    if not data: 
        st.markdown(ph("📖 スクリプト"), unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="ep-script" style="border-left-color:{C['main']};">
            <div class="ep-label" style="background:{C['main']};">📖 {LS['script_lbl']}</div>
            <div class="ep-script-text">{data.get('chunked', data.get('english',''))}</div>
            <div style="font-size:13px; color:#cbd5e1; margin-top:10px; padding:8px; background:rgba(255,255,255,.05); border-radius:8px;">
                🇯🇵 {data.get('english_jp','')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if data.get('vocab'):
            st.markdown(f'<div class="ep-card"><div class="ep-label" style="background:{C["main"]};">📝 重要語彙</div><div>', unsafe_allow_html=True)
            for k, v in data['vocab'].items():
                st.markdown(f'<span class="ep-vocab" style="background:{C["light"]}; border:1px solid {C["border"]};"><strong>{k}</strong>: {v}</span>', unsafe_allow_html=True)
            st.markdown('</div></div>', unsafe_allow_html=True)
            
        st.markdown(f"""
        <div class="ep-card">
            <div class="ep-label" style="background:{C["main"]};">📚 文法・フレーズ解説</div>
            <div style="font-size:13px; color:#cbd5e1; line-height:1.8;">{data.get("grammar","")}</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# TAB 3: AUDIO
# ============================================================
with tab3:
    if not data: 
        st.markdown(ph("🔊 音読"), unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="ep-card">
            <div class="ep-label" style="background:{C['main']};">🎵 シャドーイング</div>
            <div style="font-size:16px; font-weight:600; margin-bottom:12px; color:#f8fafc;">{data.get('chunked','')}</div>
        </div>
        """, unsafe_allow_html=True)
        st.components.v1.html(gen_audio(data.get('english',''), LS['tts']), height=130)

# ============================================================
# TAB 4: PRONUNCIATION
# ============================================================
with tab4:
    if not data: 
        st.markdown(ph("🎤 発音"), unsafe_allow_html=True)
    else:
        st.markdown(f"**この文を読んでください:**\n### {data.get('english','')}")
        rec = st.audio_input("録音")
        if rec and st.session_state.get("_client"):
            if st.button("📈 採点する", type="primary", use_container_width=True):
                with st.spinner("AIが発音を分析中..."):
                    try:
                        mime = detect_audio_mime(rec.getvalue())
                        p_sys = f"あなたは{LS['name']}のネイティブ講師です。音声とスクリプトを比較し、JSONのみ出力。"
                        p_msg = f"スクリプト: {data.get('english','')}\n\n{{'score':(0-100),'feedback':'日本語で改善点','good_points':'日本語で良い点'}}"
                        resp = st.session_state["_client"].models.generate_content(
                            model=GEMINI_MODEL,
                            contents=[
                                types.Part.from_text(text=p_msg), # エラー修正箇所
                                types.Part.from_bytes(data=rec.getvalue(), mime_type=mime)
                            ],
                            config=types.GenerateContentConfig(system_instruction=p_sys)
                        )
                        
                        m = re.search(r'\{[\s\S]*\}', resp.text)
                        if m:
                            ev = json.loads(m.group())
                            st.success(f"### 総合スコア: {ev.get('score', 0)} / 100")
                            st.markdown(f"**✨ 良い点:** {ev.get('good_points', '')}")
                            st.markdown(f"**🔧 改善点:** {ev.get('feedback', '')}")
                        else: 
                            st.error("❌ 採点フォーマットエラー")
                    except Exception as e: 
                        st.error(f"❌ エラー: {e}")

# ============================================================
# TAB 5: PRACTICE
# ============================================================
with tab5:
    if not data: 
        st.markdown(ph("✏️ 練習"), unsafe_allow_html=True)
    else:
        st.markdown(f"### 🧩 穴埋めクイズ\n**{data.get('blank_q', '')}**\n\n💡 ヒント: {data.get('hint', '')}")
        ua = st.text_input("答えを入力してください")
        if ua:
            if ua.strip().lower() == data.get("blank_a", "").lower():
                st.success("🎉 正解！よくできました！")
            else:
                st.warning(f"惜しい！正解は **{data.get('blank_a', '')}** です。")

# ============================================================
# TAB 6: CONVERSATION
# ============================================================
with tab6:
    if not data: 
        st.markdown(ph("🎭 会話"), unsafe_allow_html=True)
    else:
        persona = LS['persona_biz'] if is_biz else LS['persona_daily']
        st.markdown(f"**{persona}** との模擬会話です。「{data.get('english', '')}」を使って話しかけてみましょう。")
        
        for c in st.session_state.chat_history:
            if c["role"] == "user": 
                st.markdown(f"**You:** {c['text']}")
            else: 
                st.markdown(f"**{persona}:** {c['text']}")

        cr = st.text_input("返答を入力...")
        if cr and st.button("💬 送信", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "text": cr})
            with st.spinner("相手が返答中..."):
                try:
                    cps = f"あなたは{persona}です。ユーザーが {lang} で話しかけます。2文以内のシンプルな {lang} で返答してください。"
                    resp = call_text(cr, system=cps)
                    st.session_state.chat_history.append({"role": "ai", "text": resp.strip()})
                    st.rerun()
                except Exception as e: 
                    st.error(e)

# ============================================================
# TAB 7: VOCAB EXTRACTION (IMAGE)
# ============================================================
with tab7:
    st.markdown("### 📸 カメラ / 画像から単語を取り込み")
    st.markdown("単語帳や書類を撮影して、自動でリスト化します。")
    
    camera_image = st.camera_input("📸 カメラで撮影")
    uploaded_image = st.file_uploader("📂 または画像をアップロード", type=["jpg", "jpeg", "png"])
    img_source = camera_image or uploaded_image
    
    if img_source:
        st.image(img_source, caption="読み込み画像", use_container_width=True)
        if st.button("✨ この画像から単語を抽出する", use_container_width=True, type="primary"):
            with st.spinner("AIが単語を解析中..."):
                try:
                    mime_type = img_source.type if hasattr(img_source, "type") and img_source.type else "image/jpeg"
                    extracted = extract_vocab_from_image(img_source.getvalue(), mime_type, lang)
                    if extracted:
                        st.session_state.vocab_list.extend(extracted)
                        st.success(f"✅ {len(extracted)}件の単語を保存しました！「▶️ フラッシュ」タブで再生できます。")
                except Exception as e:
                    st.error(f"❌ 抽出エラー: {e}")
    
    if st.session_state.vocab_list:
        st.markdown("### 📝 現在保存されている単語")
        st.dataframe(st.session_state.vocab_list, use_container_width=True)
        if st.button("🗑 リストをリセット"):
            st.session_state.vocab_list = []
            st.rerun()

# ============================================================
# TAB 8: FLASHCARDS (IMMERSIVE MODE)
# ============================================================
with tab8:
    st.markdown("### ▶️ 刷り込み再生モード")
    
    if not st.session_state.vocab_list:
        st.info("💡 まずは「📸 画像単語」タブで単語を追加してください。")
    else:
        # 3秒後に発音・訳表示を行うため、次の単語までの間隔は最低4秒以上に設定
        interval = st.slider("次の単語までの間隔（秒）", min_value=4.0, max_value=10.0, value=5.0, step=0.5)
        vocab_json = json.dumps(st.session_state.vocab_list)
        lang_code = 'en-US' if lang == 'en' else 'de-DE'
        btn_color = C["main"]
        
        html_code = f"""
        <div style="text-align: center; font-family: sans-serif; padding: 20px; background-color: #1e293b; border-radius: 16px; border: 1px solid #334155;">
            <button id="startBtn" style="padding: 12px 24px; font-size: 16px; font-weight: 700; color: white; background-color: {btn_color}; border: none; border-radius: 12px; margin-bottom: 20px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,.3);">
                ▶ 刷り込みスタート
            </button>
            <button id="stopBtn" style="padding: 12px 24px; font-size: 16px; font-weight: 700; color: white; background-color: #ef4444; border: none; border-radius: 12px; margin-bottom: 20px; cursor: pointer; display: none; box-shadow: 0 4px 12px rgba(0,0,0,.3);">
                ■ 停止
            </button>
            
            <div style="min-height: 160px; display: flex; flex-direction: column; justify-content: center; background: #0f172a; border-radius: 12px; padding: 20px; border: 1px solid #334155;">
                <div id="wordText" style="font-size: 38px; font-weight: 900; color: #ffffff; margin-bottom: 12px;">Ready...</div>
                <div id="meaningText" style="font-size: 20px; font-weight: 700; color: {btn_color};">ボタンを押して開始</div>
            </div>
        </div>

        <script>
            const vocab = {vocab_json};
            const intervalMs = {int(interval * 1000)};
            const langCode = "{lang_code}";
            let index = 0;
            let timerId = null;
            let timeoutId = null;

            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const wordText = document.getElementById('wordText');
            const meaningText = document.getElementById('meaningText');

            function speakAndDisplay() {{
                if (index >= vocab.length) {{ index = 0; }}
                const current = vocab[index];
                
                // 単語を表示し、訳をクリア
                wordText.innerText = current.word;
                meaningText.innerText = "";
                
                // 3秒後(3000ms)に訳を表示し、発音する
                timeoutId = setTimeout(() => {{
                    meaningText.innerText = current.meaning;
                    
                    const utterance = new SpeechSynthesisUtterance(current.word);
                    utterance.lang = langCode;
                    utterance.rate = 0.9;
                    window.speechSynthesis.speak(utterance);
                }}, 3000);
                
                index++;
            }}

            startBtn.addEventListener('click', () => {{
                // ブラウザの音声自動再生ブロック解除用
                const unlockAudio = new SpeechSynthesisUtterance('');
                window.speechSynthesis.speak(unlockAudio);
                
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
                
                index = 0;
                speakAndDisplay();
                timerId = setInterval(speakAndDisplay, intervalMs);
            }});

            stopBtn.addEventListener('click', () => {{
                clearInterval(timerId);
                clearTimeout(timeoutId); // 3秒待機中のタイマーも正確にキャンセル
                window.speechSynthesis.cancel();
                startBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
                wordText.innerText = "Stopped";
                meaningText.innerText = "お疲れ様でした";
            }});
        </script>
        """
        st.components.v1.html(html_code, height=350)

# ============================================================
# TAB 9: SAVED
# ============================================================
with tab9:
    if not st.session_state.saved_list:
        st.markdown(ph("📚 保存帳"), unsafe_allow_html=True)
    else:
        st.markdown("### 📚 保存したスクリプト")
        if st.button("🗑️ 全て削除"):
            st.session_state.saved_list = []
            st.rerun()
            
        for idx, item in enumerate(st.session_state.saved_list):
            st.markdown(f"""
            <div class="ep-card">
                <strong>{item.get('title', '無題')}</strong><br>
                <span style="font-size:12px; color:#cbd5e1;">{item.get('english_jp', '')}</span>
            </div>
            """, unsafe_allow_html=True)

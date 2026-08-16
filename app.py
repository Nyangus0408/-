# ============================================================
# English / Deutsch Pitch & Talk ── 多言語対応版
# 修正: ①JSON専用モデルの追加 ②iPhone音声データのセッション保持強化
# ============================================================
import streamlit as st
import google.generativeai as genai
import json, base64, io, time, os, re, requests
from gtts import gTTS
from datetime import datetime

try:
    from pypdf import PdfReader; PDF_OK = True
except:
    try: from PyPDF2 import PdfReader; PDF_OK = True
    except: PDF_OK = False

try:
    from bs4 import BeautifulSoup; BS4_OK = True
except: BS4_OK = False

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(page_title="Pitch & Talk",
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
</style>
""", unsafe_allow_html=True)

# ── 言語設定 ─────────────────────────────────────────────────
LANG = {
    'en': {
        'flag': '🇺🇸', 'name': 'English', 'tts': 'en',
        'app_title': 'English Pitch & Talk',
        'sub_biz':   '展示会・商談英語をマスター',
        'sub_daily': '日常英会話を基礎から学ぼう',
        'script_lbl': '英文スクリプト（チャンク読み）',
        'switch_btn': '🇩🇪 Deutschに切替',
        'persona_biz': '🧳 バイヤー',
        'persona_daily': '💬 ネイティブ',
        'filler_label': 'フィラーカード（時間かせぎフレーズ）',
    },
    'de': {
        'flag': '🇩🇪', 'name': 'Deutsch', 'tts': 'de',
        'app_title': 'Deutsch Pitch & Talk',
        'sub_biz':   '展示会・商談ドイツ語をマスター',
        'sub_daily': '日常ドイツ会話を基礎から学ぼう',
        'script_lbl': 'ドイツ語スクリプト（チャンク読み）',
        'switch_btn': '🇺🇸 Englishに切替',
        'persona_biz': '🧳 Käufer',
        'persona_daily': '💬 Muttersprachler',
        'filler_label': 'Filler-Karten（時間かせぎフレーズ・独語）',
    },
}

# ── レベル ─────────────────────────────────────────────────
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
    },
    "🚀 ネイティブ風": {
        'en': "ネイティブが日常的に使う自然な表現。慣用句・略語・フィラー語も使用可。",
        'de': "Natürliches Deutsch. Idiome, Umgangssprache und Füllwörter erlaubt.",
    },
}

# ── シナリオ ────────────────────────────────────────────────
DAILY_SCENARIOS = {
    'en': {
        "🎯 おまかせ": "ユーザーの入力に最適な日常表現",
        "☕ カフェ/レストラン": "飲食店での注文、好みの表現、会計",
        "🗺️ 観光/道案内": "観光地での会話、道を聞く・教える",
        "🏨 ホテル/交通": "チェックイン、部屋のリクエスト、タクシー",
        "🛒 買い物": "商品の選び方、値段、返品・交換",
        "👋 自己紹介/雑談": "名前・職業・趣味の紹介、スモールトーク",
        "📞 電話/リモート": "ビジネス電話、オンライン会議",
        "🚨 緊急/トラブル": "困ったとき、体調不良、助けを求める",
        "✈️ 空港/機内": "搭乗手続き、入国審査、機内のやり取り",
    },
    'de': {
        "🎯 おまかせ": "passende Alltagsausdrücke",
        "☕ Café/Restaurant": "Bestellen, Präferenzen, Bezahlen",
        "🗺️ Tourismus/Wegbeschreibung": "Sehenswürdigkeiten, Weg fragen/erklären",
        "🏨 Hotel/Verkehr": "Check-in, Zimmerwünsche, Taxi",
        "🛒 Einkaufen": "Produktauswahl, Preise, Rückgabe",
        "👋 Vorstellung/Smalltalk": "Name, Beruf, Hobbys, Plauderei",
        "📞 Telefon/Remote": "Geschäftstelefonat, Online-Meeting",
        "🚨 Notfall/Probleme": "Hilfe suchen, Krankheit, Notfall",
        "✈️ Flughafen/Flug": "Boarding, Einreise, Bordgespräche",
    },
}

# ── フィラーカード ───────────────────────────────────────────
FILLERS = {
    'en': [
        ("That's a great question.", "いい質問ですね"),
        ("Let me explain.", "説明します"),
        ("In other words...", "つまり..."),
        ("For example...", "例えば..."),
        ("The key point is...", "重要なのは..."),
        ("Could you repeat that?", "繰り返してください"),
        ("One moment, please.", "少々お待ちください"),
        ("I understand.", "承知しました"),
    ],
    'de': [
        ("Das ist eine gute Frage.", "いい質問ですね"),
        ("Lassen Sie mich erklären.", "説明させてください"),
        ("Mit anderen Worten...", "つまり..."),
        ("Zum Beispiel...", "例えば..."),
        ("Der wichtigste Punkt ist...", "重要なのは..."),
        ("Könnten Sie das wiederholen?", "繰り返していただけますか？"),
        ("Einen Moment bitte.", "少々お待ちください"),
        ("Ich verstehe.", "承知しました"),
    ],
}

# ── HELPERS ──────────────────────────────────────────────────
def ac(is_biz, lang='en'):
    if is_biz: base = {"main":"#1d4ed8","light":"#eff6ff","border":"#bfdbfe"}
    else: base = {"main":"#0d9488","light":"#f0fdfa","border":"#99f6e4"}
    if lang == 'de':
        base["main"] = "#b45309" if is_biz else "#0f766e"
        base["light"] = "#fffbeb" if is_biz else "#f0fdfa"
        base["border"] = "#fde68a" if is_biz else "#99f6e4"
    return base

def ph(name):
    return f"""<div class="ep-ph"><div class="ep-ph-icon">📝</div>
<div class="ep-ph-title">「📝 入力」タブで内容を入力してください</div>
<div class="ep-ph-sub">{name} はコンテンツ生成後に表示されます</div></div>"""

def gen_audio(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang); fp = io.BytesIO()
        tts.write_to_fp(fp); fp.seek(0)
        b64 = base64.b64encode(fp.read()).decode()
        return f"""<audio id="epA" style="width:100%;border-radius:12px;margin-bottom:8px;">
  <source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>
<div style="display:flex;gap:8px;">
  <button onclick="document.getElementById('epA').playbackRate=0.8;document.getElementById('epA').play();"
    style="flex:1;padding:9px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;
    cursor:pointer;font-weight:700;font-size:11px;">🐢 0.8x<br><span style="font-size:9px;opacity:.7;">ゆっくり</span></button>
  <button onclick="document.getElementById('epA').playbackRate=1.0;document.getElementById('epA').play();"
    style="flex:1;padding:9px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;
    cursor:pointer;font-weight:700;font-size:11px;">▶️ 1.0x<br><span style="font-size:9px;opacity:.7;">標準</span></button>
  <button onclick="document.getElementById('epA').playbackRate=1.2;document.getElementById('epA').play();"
    style="flex:1;padding:9px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;
    cursor:pointer;font-weight:700;font-size:11px;">⚡ 1.2x<br><span style="font-size:9px;opacity:.7;">速め</span></button>
</div>"""
    except Exception as e:
        return f'<div style="color:#ef4444;font-size:12px;">音声エラー: {e}</div>'

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

# 音声認識（テキストモデル用）
def transcribe(audio_file, mdl_text, lang='en') -> str:
    inst = "この音声を日本語として文字起こしし、テキストのみ出力してください。" if lang == 'en' else \
           "Schreibe dieses Audio als deutschen Text auf und gib nur den Text aus."
    try:
        res = mdl_text.generate_content([inst, {"mime_type": audio_file.type, "data": audio_file.getvalue()}])
        return res.text.strip()
    except Exception as e: return ""

def build_prompt(user_input, is_biz, level_key, lang, scenario=""):
    level_inst = LEVELS.get(level_key, LEVELS["📗 基礎 (A2)"])[lang]
    scene = ("Fachmesse/Business (Produkterklärung, Verhandlung)" if is_biz else f"Alltag – {scenario}") \
            if lang == 'de' else \
            ("展示会・ビジネス（製品説明・商談）" if is_biz else f"日常会話 ― {scenario}")
    target_lang_name = "Deutschen" if lang == 'de' else "英語"
    rule = ("Max. 12 Wörter pro Satz. Nur einfache SVO-Struktur. Grammatik dem Level anpassen." if lang == 'de'
            else "1文最大12単語。SVO構造優先。レベルに合わせた語彙・文法を厳守。")
    return f"""
以下の条件でスクリプトを生成してください。

[入力文]: {user_input}
[目標言語]: {target_lang_name}
[場面]: {scene}
[レベル指示]: {level_inst}
[ルール]: {rule}
"""

def build_context_prompt(context, src_label, is_biz, lang, level_key):
    level_inst = LEVELS.get(level_key, LEVELS["📗 基礎 (A2)"])[lang]
    target = "Deutschen" if lang == 'de' else "英語"
    return f"""
{src_label}のテキストを要約し、{target}学習コンテンツを作成してください。
[テキスト]: {context[:2000]}
[場面]: {"Business/Fachmesse" if is_biz else "Alltag"}
[レベル]: {level_inst}
"""

# スクリプト生成（JSON専用モデル用）
def do_generate(prompt, sys_p, mdl_json):
    res = mdl_json.generate_content([sys_p, prompt])
    text = res.text.strip()
    # JSONモデルの場合でもマークダウン記法が入ることがあるため除去
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return json.loads(text)


# ── API KEY & MODELS ─────────────────────────────────────────
api_key = ""
try: api_key = st.secrets.get("GEMINI_API_KEY", st.secrets.get("API_KEY",""))
except: pass
if not api_key: api_key = os.environ.get("GEMINI_API_KEY","")

mdl_text = None
mdl_json = None
if api_key:
    genai.configure(api_key=api_key)
    # テキスト出力やチャット用の標準モデル
    mdl_text = genai.GenerativeModel('gemini-1.5-flash')
    # ユーザー提案のJSON専用モデル
    mdl_json = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})

# ── SESSION STATE ────────────────────────────────────────────
defaults = {"script_data":None,"chat_history":[],"saved_list":[],
            "voice_text":"","last_audio_size":0,"language":"en",
            "url_text_cache":""}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

lang = st.session_state.language
LS = LANG[lang]

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
<div style="padding:14px 0 8px;">
  <div style="font-size:19px;font-weight:900;color:white;margin-bottom:3px;">
    {LS['flag']} {LS['app_title']}</div>
</div>
<hr style="border-color:rgba(255,255,255,.1);margin:8px 0 14px;">
""", unsafe_allow_html=True)
    if not api_key:
        mk = st.text_input("🔑 Gemini API Key", type="password")
        if mk: api_key = mk; st.markdown('<div style="color:#4ade80;font-size:12px;">✅ 完了</div>', unsafe_allow_html=True)
        else:  st.markdown('<div style="color:#fbbf24;font-size:12px;">⚠️ 未設定</div>', unsafe_allow_html=True)

# ── HEADER & モード選択 ──────────────────────────────────────
is_biz = True
C = ac(is_biz, lang)
st.markdown(f"<style>:root{{--acc:{C['main']};}}</style>", unsafe_allow_html=True)

schema_inst = f"""
出力は必ず以下の構造を持つJSONデータのみを返してください。
{{
  "english": "目標言語の文（複数文はスペースで区切る）",
  "english_jp": "自然な日本語訳",
  "chunked": "スラッシュ区切り（例: Unser Produkt / ist leicht.）",
  "grammar": "文法・フレーズ解説（日本語）",
  "vocab": {{"単語": "意味（日本語）"}},
  "blank_q": "穴埋め文（___ を含む）",
  "blank_a": "正解の単語",
  "hint": "ヒント（日本語）",
  "qa_pairs": [{{"question": "質問文", "question_jp": "日本語訳", "hint": "ヒント"}}],
  "paraphrases": [{{"difficult": "難しい表現", "simple": "簡単な言い換え", "note": "メモ（日本語）"}}]
}}
"""

sys_p = {
    ('en', True):  "あなたはビジネス英語の専門家です。展示会で通じるシンプルな英文を作成してください。\n" + schema_inst,
    ('en', False): "あなたは日常英会話のコーチです。旅行・生活・雑談で使えるシンプルな英文を作成してください。\n" + schema_inst,
    ('de', True):  "Sie sind Experte für Geschäftsdeutsch. Erstellen Sie einfache Sätze für Fachmessen.\n" + schema_inst,
    ('de', False): "Sie sind Deutschcoach für den Alltag. Erstellen Sie einfache Sätze für Reisen und Alltag.\n" + schema_inst,
}.get((lang, is_biz), "")

st.markdown(f"""
<div style="background:linear-gradient(135deg,{C['main']},{C['main']}cc);color:white;
     padding:18px 22px 14px;border-radius:16px;margin-bottom:4px;
     box-shadow:0 4px 20px rgba(0,0,0,.15);">
  <div style="font-size:21px;font-weight:900;letter-spacing:-.5px;margin-bottom:3px;">
    {LS['flag']} {LS['app_title']}</div>
  <div style="font-size:11px;opacity:.75;">
    {LS['sub_biz'] if is_biz else LS['sub_daily']}</div>
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
tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs(
    ["📝 入力","📖 スクリプト","🔊 音読","🎤 発音","✏️ 練習","🎭 会話","📚 マイ学習帳"])
data = st.session_state.script_data

# ============================================================
# TAB 1: INPUT
# ============================================================
with tab1:
    level_key = st.selectbox("📊 学習レベル", list(LEVELS.keys()), index=1)
    scenario = ""

    im = st.radio("入力方法",["✏️ テキスト","🎤 音声入力","📄 PDF","🔗 URL"],
                  horizontal=True, key="input_method_radio")

    user_input = ""

    if im == "✏️ テキスト":
        user_input = st.text_area("スクリプトにしたい内容を入力", height=100)

    elif im == "🎤 音声入力":
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:14px;
     padding:14px;margin-bottom:12px;">
  <div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:8px;">
    🎤 マイクで録音 → 自動文字起こし
  </div>
</div>""", unsafe_allow_html=True)
        
        voice_audio = st.audio_input("🎤 録音ボタンを押して話してください", key="voice_input_ja")
        
        # 音声が入力された場合の処理（iPhoneリセット対策）
        if voice_audio:
            current_audio_size = len(voice_audio.getvalue())
            # 同じ音声ファイルで何度もAPIを叩かないためのチェック
            if st.session_state.get("last_audio_size") != current_audio_size:
                if mdl_text:
                    with st.spinner("文字起こし中..."):
                        txt = transcribe(voice_audio, mdl_text, lang)
                        if txt:
                            st.session_state.voice_text = txt
                            st.session_state.last_audio_size = current_audio_size
                            st.success("✅ 音声を認識しました！")
                        else:
                            st.error("❌ 音声の認識に失敗しました。")
        
        # 音声テキストがセッションに存在する場合、テキストエリアに表示
        if st.session_state.voice_text:
            edit_txt = st.text_area("認識されたテキスト（編集可）",
                                    value=st.session_state.voice_text, height=80)
            # ユーザーが編集した内容をセッションに同期
            st.session_state.voice_text = edit_txt
            # 生成用に user_input にも格納
            user_input = edit_txt

    elif im == "📄 PDF":
        pdf_file = st.file_uploader("PDFファイルを選択", type=["pdf"])
        if pdf_file:
            with st.spinner("読み込み中..."):
                pdf_text = extract_pdf(pdf_file)
                user_input = f"[PDF内容]: {pdf_text}"

    elif im == "🔗 URL":
        url_in = st.text_input("URLを入力")
        if url_in and st.button("🔍 URLを取得"):
            with st.spinner("Webページを取得中..."):
                url_text = extract_url(url_in)
                st.session_state["url_text_cache"] = url_text
        if st.session_state.get("url_text_cache"):
            user_input = f"[URL内容]: {st.session_state['url_text_cache']}"

    if st.button("✨ スクリプト＆学習コンテンツを生成する", type="primary", use_container_width=True):
        if not api_key: st.error("❌ APIキーが設定されていません。")
        elif not user_input or not user_input.strip(): st.warning("内容を入力してください。")
        elif not mdl_json: st.error("❌ モデルの初期化に失敗しました。")
        else:
            with st.spinner("AIがスクリプトを作成中... ✨"):
                try:
                    if user_input.startswith("[PDF内容]") or user_input.startswith("[URL内容]"):
                        prompt = build_context_prompt(user_input, im, is_biz, lang, level_key)
                    else:
                        prompt = build_prompt(user_input, is_biz, level_key, lang, scenario)
                    
                    # JSON専用モデルで生成
                    result = do_generate(prompt, sys_p, mdl_json)
                    result.update({"_source_ja": user_input[:100], "_level": level_key,
                                   "_mode": "business" if is_biz else "daily", "_lang": lang})
                    
                    st.session_state.script_data = result
                    st.session_state.chat_history = []
                    # 生成が終わったら次の入力のために音声テキストをクリアする
                    st.session_state.voice_text = ""
                    st.session_state.last_audio_size = 0
                    
                    st.success("✅ 生成完了！「📖 スクリプト」タブに進んでください。")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ 生成エラー: {e}")

# ============================================================
# TAB 2: SCRIPT
# ============================================================
with tab2:
    if not data: st.markdown(ph("📖 スクリプト"), unsafe_allow_html=True)
    else:
        dl = data.get('_lang', 'en'); DC = ac(is_biz, dl); DLS = LANG[dl]
        st.markdown(f"""
<div class="ep-script" style="background:{DC['light']};border:2px solid {DC['border']};border-left-color:{DC['main']};">
  <div class="ep-label" style="background:{DC['main']};">📖 {DLS['script_lbl']}</div>
  <div class="ep-script-text">{data.get('chunked', data.get('english',''))}</div>
  <div style="font-size:13px;color:#475569;margin-top:10px;padding:8px;
       background:rgba(255,255,255,.7);border-radius:8px;">🇯🇵 {data.get('english_jp','')}</div>
</div>""", unsafe_allow_html=True)
        if st.button("📚 マイ学習帳に保存", use_container_width=True):
            st.session_state.saved_list.append({"id": int(time.time()), "title": data.get("english","")[:40]+"…", "english": data.get("english",""), "english_jp": data.get("english_jp",""), "chunked": data.get("chunked",""), "level": data.get("_level",""), "mode": data.get("_mode",""), "lang": data.get("_lang","en"), "source_ja": data.get("_source_ja",""), "saved_at": datetime.now().strftime("%m/%d %H:%M"), "data": data})
            st.success("✅ 保存しました！")
        
        st.markdown(f'<div class="ep-card"><div class="ep-label" style="background:{DC["main"]};">📚 文法・フレーズ解説</div><div style="font-size:13px;">{data.get("grammar","")}</div></div>', unsafe_allow_html=True)
        
        if data.get('vocab'):
            v_html = "".join([f'<span class="ep-vocab" style="background:{DC["light"]};color:{DC["main"]};"><strong>{k}</strong>: {v}</span>' for k,v in data['vocab'].items()])
            st.markdown(f'<div class="ep-card"><div class="ep-label" style="background:{DC["main"]};">📝 重要語彙</div><div>{v_html}</div></div>', unsafe_allow_html=True)

# ============================================================
# TAB 3: AUDIO
# ============================================================
with tab3:
    if not data: st.markdown(ph("🔊 音読"), unsafe_allow_html=True)
    else:
        dl = data.get('_lang', 'en'); DC = ac(is_biz, dl); DLS = LANG[dl]
        st.markdown(f'<div style="background:{DC["light"]};border:1px solid {DC["border"]};border-radius:16px;padding:18px;margin-bottom:14px;"><div class="ep-label" style="background:{DC["main"]};">🎵 シャドーイング</div><div style="font-size:16px;font-weight:600;margin-bottom:12px;">{data.get("chunked","")}</div></div>', unsafe_allow_html=True)
        st.components.v1.html(gen_audio(data.get('english',''), DLS['tts']), height=130)

# ============================================================
# TAB 4: PRONUNCIATION
# ============================================================
with tab4:
    if not data: st.markdown(ph("🎤 発音"), unsafe_allow_html=True)
    else:
        dl = data.get('_lang', 'en'); DC = ac(is_biz, dl)
        audio_val = st.audio_input("マイクを押して録音")
        if audio_val and mdl_json:
            with st.spinner("AIが発音を分析中... 🎯"):
                ap = f"""この音声を{'Deutschen' if dl=='de' else '英語'}として文字起こしし、「{data.get('english','')}」と比較採点してください。
JSONのみ出力: {{"score":85,"transcript":"認識テキスト","good_words":["正解単語"],"bad_words":["要練習単語"],"feedback":"フィードバック"}}"""
                try:
                    # ここでもJSON専用モデルを使用
                    res = mdl_json.generate_content([ap, {"mime_type": audio_val.type, "data": audio_val.getvalue()}])
                    rd = json.loads(res.text.strip())
                    st.json(rd) # 採点結果の表示（レイアウトを簡略化）
                except Exception as e: st.error(f"分析エラー: {e}")

# ============================================================
# TAB 5, 6, 7 (Practice, Roleplay, Savings) 
# ============================================================
with tab5:
    if not data: st.markdown(ph("✏️ 練習"), unsafe_allow_html=True)
    else:
        st.markdown(f"**Q:** {data.get('blank_q','')} (Hint: {data.get('hint','')})")
        if st.text_input("答え") == data.get('blank_a',''): st.success("正解！")

with tab6:
    if not data: st.markdown(ph("🎭 会話"), unsafe_allow_html=True)
    else:
        user_msg = st.chat_input("メッセージを入力...")
        if user_msg and mdl_text:
            st.session_state.chat_history.append({"role":"user", "content":user_msg})
            try:
                chat_res = mdl_text.generate_content(f"返答してください: {user_msg}")
                st.session_state.chat_history.append({"role":"assistant", "content":chat_res.text.strip()})
                st.rerun()
            except Exception as e: st.error(f"エラー: {e}")
        for m in st.session_state.chat_history: st.write(f"**{m['role']}**: {m['content']}")

with tab7:
    for item in reversed(st.session_state.saved_list):
        st.write(f"📚 {item['title']} ({item['saved_at']})")

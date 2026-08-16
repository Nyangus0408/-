# ============================================================
# English / Deutsch Pitch & Talk  ── 完全修正版
# 修正: ① google-genai 新APIに移行 (モデルエラー解消)
#       ② iPhone音声フォーマット自動判別 (音声入力解消)
# ============================================================
import streamlit as st
from google import genai
from google.genai import types
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

# ── MODEL NAME ── 最新モデルに更新
GEMINI_MODEL = "gemini-2.5-flash"

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
    """iPhone(mp4/aac)・Android(webm)・PC(wav/webm)の音声フォーマットを自動判別"""
    if not data or len(data) < 12:
        return 'audio/mp4'
    h = data[:12]
    # WAV: RIFF....WAVE
    if h[:4] == b'RIFF' and h[8:12] == b'WAVE':
        return 'audio/wav'
    # MP4 / M4A / AAC (iPhone標準): ftyp マジックバイト
    if h[4:8] == b'ftyp' or h[8:12] == b'ftyp':
        return 'audio/mp4'
    # WebM (Chrome/Android): 1A 45 DF A3
    if h[:4] == b'\x1aE\xdf\xa3':
        return 'audio/webm'
    # OGG
    if h[:4] == b'OggS':
        return 'audio/ogg'
    # MP3: ID3 タグ or FFフレーム
    if h[:3] == b'ID3' or (h[0] == 0xFF and (h[1] & 0xE0) == 0xE0):
        return 'audio/mp3'
    # デフォルト: iPhone対応のmp4
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
    """テキスト生成 ― 新APIラッパー"""
    if not st.session_state.get("_client"):
        raise RuntimeError("APIクライアント未初期化")
    cfg = types.GenerateContentConfig(system_instruction=system) if system else None
    resp = st.session_state["_client"].models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=cfg,
    )
    return resp.text

def call_audio(prompt: str, audio_bytes: bytes) -> str:
    """音声+テキスト生成 ― 新APIラッパー（iPhoneフォーマット自動対応）"""
    if not st.session_state.get("_client"):
        raise RuntimeError("APIクライアント未初期化")
    mime = detect_audio_mime(audio_bytes)
    resp = st.session_state["_client"].models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_text(prompt),
            types.Part.from_bytes(data=audio_bytes, mime_type=mime),
        ],
    )
    return resp.text

def do_generate(prompt: str, sys_p: str) -> dict:
    raw = call_text(prompt, system=sys_p)
    m = re.search(r'\{[\s\S]*\}', raw)
    if not m: raise ValueError("JSONが見つかりません")
    return json.loads(m.group())

def transcribe(audio_bytes: bytes, lang: str = 'en') -> str:
    inst = ("この音声を日本語として文字起こしし、テキストのみ出力してください。"
            if lang == 'en' else
            "Schreibe dieses Audio als deutschen Text auf und gib nur den Text aus.")
    try:
        return call_audio(inst, audio_bytes).strip()
    except: return ""


# ── PROMPT BUILDERS ──────────────────────────────────────────
def build_prompt(user_input, is_biz, level_key, lang, scenario=""):
    level_inst = LEVELS.get(level_key, LEVELS["📗 基礎 (A2)"])[lang]
    scene = (("Fachmesse/Business (Produkterklärung, Verhandlung)" if is_biz else f"Alltag – {scenario}")
             if lang == 'de' else
             ("展示会・ビジネス（製品説明・商談）" if is_biz else f"日常会話 ― {scenario}"))
    target = "Deutschen" if lang == 'de' else "英語"
    rule   = ("Max. 12 Wörter pro Satz. SVO-Struktur. Grammatik dem Level anpassen."
              if lang == 'de' else "1文最大12単語。SVO構造優先。レベルに合わせた語彙・文法を厳守。")
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

def build_context_prompt(context, src_label, is_biz, lang, level_key):
    level_inst = LEVELS.get(level_key, LEVELS["📗 基礎 (A2)"])[lang]
    target = "Deutschen" if lang == 'de' else "英語"
    return f"""
{src_label}のテキストを要約し、{target}学習コンテンツをJSONのみで作成（コードブロック不要）。
[テキスト]: {context[:2000]}
[場面]: {"Business/Fachmesse" if is_biz else "Alltag"}
[レベル]: {level_inst}
{{
  "english":"{target}文","english_jp":"日本語訳","chunked":"チャンク区切り",
  "grammar":"文法解説（日本語）","vocab":{{"単語":"意味"}},
  "blank_q":"穴埋め（___）","blank_a":"正解","hint":"ヒント（日本語）",
  "qa_pairs":[{{"question":"質問","question_jp":"訳","hint":"ヒント"}}],
  "paraphrases":[{{"difficult":"難表現","simple":"簡単","note":"メモ（日本語）"}}]
}}
"""


# ── API KEY ──────────────────────────────────────────────────
api_key = ""
try: api_key = st.secrets.get("GEMINI_API_KEY", st.secrets.get("API_KEY",""))
except: pass
if not api_key: api_key = os.environ.get("GEMINI_API_KEY","")

# ── SESSION STATE ────────────────────────────────────────────
defaults = {"script_data":None,"chat_history":[],"saved_list":[],
            "voice_text":"","url_text_cache":"","language":"en","_client":None}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ── CLIENT INIT (新API) ──────────────────────────────────────
if api_key and st.session_state["_client"] is None:
    try:
        st.session_state["_client"] = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"❌ クライアント初期化失敗: {e}")

lang = st.session_state.language
LS   = LANG[lang]

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
<div style="padding:14px 0 8px;">
  <div style="font-size:19px;font-weight:900;color:white;margin-bottom:3px;">
    {LS['flag']} {LS['app_title']}</div>
  <div style="font-size:11px;color:rgba(255,255,255,.5);">AI言語トレーナー Pro</div>
</div><hr style="border-color:rgba(255,255,255,.1);margin:8px 0 14px;">
""", unsafe_allow_html=True)
    if not api_key:
        mk = st.text_input("🔑 Gemini API Key", type="password", placeholder="AIzaSy...")
        if mk:
            api_key = mk
            st.session_state["_client"] = genai.Client(api_key=mk)
            st.markdown('<div style="color:#4ade80;font-size:12px;font-weight:700;">✅ APIキー設定済み</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#fbbf24;font-size:12px;font-weight:700;">⚠️ APIキー未設定</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#4ade80;font-size:12px;font-weight:700;">✅ APIキー自動連携済み</div>', unsafe_allow_html=True)
    st.markdown(f"""
<hr style="border-color:rgba(255,255,255,.1);margin:14px 0;">
<div style="font-size:11px;font-weight:700;color:rgba(255,255,255,.6);margin-bottom:8px;">📖 使い方</div>
<div style="font-size:11px;color:rgba(255,255,255,.7);line-height:2.1;">
① モード＆レベルを選択<br>② 右上ボタンで言語切替<br>③ テキスト/音声/PDFで入力<br>④「生成する」→ 各タブで学習！<br>⑤ 気に入ったら📚に保存
</div>
<hr style="border-color:rgba(255,255,255,.1);margin:14px 0;">
<div style="font-size:10px;color:rgba(255,255,255,.3);line-height:1.8;">
🔧 モデル: {GEMINI_MODEL}<br>📦 SDK: google-genai (新API)<br>🔊 TTS: gTTS ({lang})<br>🎤 STT: Gemini Audio (自動MIME判別)
</div>
""", unsafe_allow_html=True)

# ── HEADER & MODE ────────────────────────────────────────────
mode = st.radio("モード",["🏢 展示会・ビジネス","☕ 日常会話・基礎"],
                horizontal=True, label_visibility="collapsed")
is_biz = "展示会" in mode
C = ac(is_biz, lang)
st.markdown(f"<style>:root{{--acc:{C['main']};}}</style>", unsafe_allow_html=True)

sys_p = {
    ('en',True):  "あなたはビジネス英語の専門家です。展示会で通じるシンプルな英文を作成してください。",
    ('en',False): "あなたは日常英会話のコーチです。旅行・生活・雑談で使えるシンプルな英文を作成してください。",
    ('de',True):  "Sie sind Experte für Geschäftsdeutsch. Erstellen Sie einfache Sätze für Fachmessen.",
    ('de',False): "Sie sind Deutschcoach für den Alltag. Erstellen Sie einfache Sätze für Reisen und Alltag.",
}.get((lang, is_biz), "")

# ヘッダー (バッジなし)
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

# 言語切替ボタン（元バッジ位置）
col_sp, col_lang = st.columns([3, 1])
with col_lang:
    if st.button(LS['switch_btn'], key="lang_toggle", use_container_width=True):
        st.session_state.language  = 'de' if lang == 'en' else 'en'
        st.session_state.script_data   = None
        st.session_state.chat_history  = []
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
    st.markdown(f'<div style="font-size:11px;color:#94a3b8;margin-bottom:12px;">📌 {LEVELS[level_key][lang][:45]}…</div>',
                unsafe_allow_html=True)

    scenario = ""
    if not is_biz:
        scenario = st.selectbox("🎬 シナリオ", list(DAILY_SCENARIOS[lang].keys()))

    im = st.radio("入力方法",["✏️ テキスト","🎤 音声入力","📄 PDF","🔗 URL"],
                  horizontal=True, key="input_method_radio")
    user_input = ""

    if im == "✏️ テキスト":
        ph_txt = {('en',True):"例: 弊社のセンサーは従来品より30%省エネです。",
                  ('en',False):"例: コーヒーを1杯ください。",
                  ('de',True):"例: Unser Sensor spart 30% mehr Energie.",
                  ('de',False):"例: Ich hätte gerne einen Kaffee."}.get((lang,is_biz),"")
        user_input = st.text_area("スクリプトにしたい内容を入力（日本語でOK）",
                                  placeholder=ph_txt, height=100, key="text_input_main")

    elif im == "🎤 音声入力":
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:14px;
     padding:14px;margin-bottom:12px;">
  <div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:6px;">
    🎤 マイクで録音 → 自動文字起こし</div>
  <div style="font-size:11px;color:#64748b;">
    録音ボタンを押して話してください。iPhone・Androidどちらでも動作します。</div>
</div>""", unsafe_allow_html=True)
        voice_audio = st.audio_input("🎤 録音ボタンを押して話してください", key="voice_input_ja")
        if voice_audio and st.session_state.get("_client"):
            with st.spinner("文字起こし中..."):
                txt = transcribe(voice_audio.getvalue(), lang)
                if txt:
                    st.session_state.voice_text = txt
                    st.success(f"✅ 認識: {txt}")
                else:
                    st.warning("⚠️ 音声を認識できませんでした。もう一度お試しください。")
        if st.session_state.voice_text:
            user_input = st.text_area("認識されたテキスト（編集可）",
                                      value=st.session_state.voice_text,
                                      height=80, key="voice_edit")

    elif im == "📄 PDF":
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:14px;
     padding:14px;margin-bottom:12px;">
  <div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:6px;">
    📄 製品カタログ・資料PDF → スクリプト自動生成</div>
  <div style="font-size:11px;color:#64748b;">
    PDFをアップロードすると内容を要約してスクリプトを作ります。</div>
</div>""", unsafe_allow_html=True)
        pdf_file = st.file_uploader("PDFファイルを選択", type=["pdf"], key="pdf_upload")
        if pdf_file:
            if not PDF_OK:
                st.error("❌ requirements.txt に pypdf を追加してください。")
            else:
                with st.spinner("PDFを読み込み中..."): pdf_text = extract_pdf(pdf_file)
                st.text_area("抽出テキスト（確認用）", value=pdf_text[:400]+"…", height=70, disabled=True)
                user_input = f"[PDF内容]: {pdf_text}"
                st.success("✅ PDFを読み込みました。下の「生成する」を押してください。")

    elif im == "🔗 URL":
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:14px;
     padding:14px;margin-bottom:12px;">
  <div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:6px;">
    🔗 WebサイトURL → 内容要約 → スクリプト生成</div>
  <div style="font-size:11px;color:#64748b;">
    会社HP・製品ページなどのURLを入力してください。</div>
</div>""", unsafe_allow_html=True)
        url_in = st.text_input("URLを入力", placeholder="https://example.com/product", key="url_input")
        if url_in and st.button("🔍 URLを取得", key="fetch_url"):
            with st.spinner("Webページを取得中..."):
                url_text = extract_url(url_in)
            if "失敗" in url_text: st.error(url_text)
            else:
                st.text_area("取得テキスト", value=url_text[:400]+"…", height=70, disabled=True)
                st.session_state["url_text_cache"] = url_text
                st.success("✅ 取得完了。「生成する」を押してください。")
        if st.session_state.get("url_text_cache"):
            user_input = f"[URL内容]: {st.session_state['url_text_cache']}"

    st.markdown('<div style="font-size:10px;color:#94a3b8;margin-top:4px;margin-bottom:10px;">💡 短い文・要点ほど高品質なコンテンツが生成されます</div>',
                unsafe_allow_html=True)

    if st.button("✨ スクリプト＆学習コンテンツを生成する", type="primary",
                 use_container_width=True, key="gen_btn"):
        if not api_key:
            st.error("❌ APIキーが設定されていません。左のサイドバーから入力してください。")
        elif not st.session_state.get("_client"):
            st.error("❌ APIクライアントが初期化されていません。ページを再読み込みしてください。")
        elif not user_input or not user_input.strip():
            st.warning("内容を入力してください。")
        else:
            with st.spinner(f"AIが{LS['name']}スクリプトを作成中... ✨"):
                try:
                    if user_input.startswith("[PDF内容]") or user_input.startswith("[URL内容]"):
                        prompt = build_context_prompt(user_input, im, is_biz, lang, level_key)
                    else:
                        prompt = build_prompt(user_input, is_biz, level_key, lang, scenario)
                    result = do_generate(prompt, sys_p)
                    result.update({"_source_ja":user_input[:100],"_level":level_key,
                                   "_mode":"business" if is_biz else "daily","_lang":lang})
                    st.session_state.script_data = result
                    st.session_state.chat_history = []
                    st.session_state.voice_text = ""
                    data = result
                    st.success("✅ 生成完了！「📖 スクリプト」タブに進んでください。")
                    st.balloons()
                except Exception as e:
                    err = str(e)
                    if "API_KEY" in err.upper() or "403" in err:
                        st.error(f"❌ APIキーエラー: {err}")
                    elif "429" in err or "QUOTA" in err.upper():
                        st.error("❌ レート制限: しばらく待ってから再試行してください。")
                    else:
                        st.error(f"❌ エラー: {err}")


# ============================================================
# TAB 2: SCRIPT
# ============================================================
with tab2:
    if not data: st.markdown(ph("📖 スクリプト"), unsafe_allow_html=True)
    else:
        dl = data.get('_lang','en'); DC = ac(is_biz,dl); DLS = LANG[dl]
        st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
  <span style="font-size:11px;color:#94a3b8;">{DLS['flag']} {DLS['name']} ｜ レベル:
  <strong style="color:{DC['main']};">{data.get('_level','')}</strong></span>
</div>
<div class="ep-script" style="background:{DC['light']};border:2px solid {DC['border']};border-left-color:{DC['main']};">
  <div class="ep-label" style="background:{DC['main']};">📖 {DLS['script_lbl']}</div>
  <div class="ep-script-text">{data.get('chunked', data.get('english',''))}</div>
  <div style="font-size:13px;color:#475569;margin-top:10px;padding:8px;
       background:rgba(255,255,255,.7);border-radius:8px;">🇯🇵 {data.get('english_jp','')}</div>
  <div style="font-size:11px;color:#94a3b8;margin-top:6px;">/ はチャンク（意味の塊）の区切りです</div>
</div>""", unsafe_allow_html=True)
        if st.button("📚 マイ学習帳に保存", use_container_width=True, key="save_btn"):
            item = {"id":int(time.time()),"title":data.get("english","")[:40]+"…",
                    "english":data.get("english",""),"english_jp":data.get("english_jp",""),
                    "chunked":data.get("chunked",""),"level":data.get("_level",""),
                    "mode":data.get("_mode",""),"lang":data.get("_lang","en"),
                    "source_ja":data.get("_source_ja",""),
                    "saved_at":datetime.now().strftime("%m/%d %H:%M"),"data":data}
            st.session_state.saved_list.append(item)
            st.success(f"✅ 保存しました！（📚 {len(st.session_state.saved_list)} 件）")
        st.markdown(f"""
<div class="ep-card">
  <div class="ep-label" style="background:{DC['main']};">📚 文法・フレーズ解説</div>
  <div style="font-size:13px;color:#475569;line-height:1.8;">{data.get('grammar','')}</div>
</div>""", unsafe_allow_html=True)
        if data.get('vocab'):
            vh = "".join([f'<span class="ep-vocab" style="background:{DC["light"]};color:{DC["main"]};"><strong>{k}</strong>: {v}</span>'
                          for k,v in data['vocab'].items()])
            st.markdown(f'<div class="ep-card"><div class="ep-label" style="background:{DC["main"]};">📝 重要語彙</div><div>{vh}</div></div>', unsafe_allow_html=True)
        if is_biz and data.get('qa_pairs'):
            qh = "".join([f'<div class="ep-qa"><div style="font-size:13px;font-weight:600;color:#1e293b;">{q.get("question","")}</div><div style="font-size:11px;color:#94a3b8;">{q.get("question_jp","")}</div><div style="font-size:11px;color:{DC["main"]};font-weight:600;margin-top:5px;">💡 {q.get("hint","")}</div></div>'
                          for q in data['qa_pairs']])
            st.markdown(f'<div class="ep-card"><div class="ep-label" style="background:{DC["main"]};">🙋 想定Q&A</div>{qh}</div>', unsafe_allow_html=True)
        st.markdown('<div class="ep-tip">💡 <strong>チャンク読みのコツ：</strong>スラッシュで区切り、<strong>左から順番に</strong>意味をつかみながら読みましょう！</div>', unsafe_allow_html=True)


# ============================================================
# TAB 3: AUDIO
# ============================================================
with tab3:
    if not data: st.markdown(ph("🔊 音読"), unsafe_allow_html=True)
    else:
        dl = data.get('_lang','en'); DC = ac(is_biz,dl); DLS = LANG[dl]
        st.markdown(f"""
<div style="background:{DC['light']};border:1px solid {DC['border']};border-radius:16px;padding:18px;margin-bottom:14px;">
  <div class="ep-label" style="background:{DC['main']};">🎵 シャドーイング・音読プレイヤー</div>
  <div style="background:white;border:1px solid {DC['border']};border-radius:12px;padding:14px;
       margin-bottom:12px;font-size:16px;font-weight:600;color:#1e293b;line-height:1.8;">
    {data.get('chunked','')}</div>
  <div style="font-size:12px;color:#475569;padding:6px 10px;background:rgba(255,255,255,.6);
       border-radius:8px;margin-bottom:12px;">🇯🇵 {data.get('english_jp','')}</div>
</div>""", unsafe_allow_html=True)
        st.components.v1.html(gen_audio(data.get('english',''), DLS['tts']), height=130)
        st.markdown(f"""
<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:14px;padding:16px;margin-top:14px;">
  <div style="font-size:12px;font-weight:800;color:#92400e;margin-bottom:10px;">💡 安河内式 音読 3ステップ</div>
  <div style="display:flex;flex-direction:column;gap:8px;">
    <div style="display:flex;gap:10px;align-items:flex-start;font-size:12px;color:#78350f;">
      <span style="background:{DC['main']};color:white;width:20px;height:20px;border-radius:50%;
            display:flex;align-items:center;justify-content:center;font-weight:900;font-size:10px;flex-shrink:0;">1</span>
      <span><strong>0.8x</strong> → 音声を聴きながら口をパクパク（オーバーラッピング）</span></div>
    <div style="display:flex;gap:10px;align-items:flex-start;font-size:12px;color:#78350f;">
      <span style="background:{DC['main']};color:white;width:20px;height:20px;border-radius:50%;
            display:flex;align-items:center;justify-content:center;font-weight:900;font-size:10px;flex-shrink:0;">2</span>
      <span><strong>1.0x</strong> → 声に出して一緒に読む（シャドーイング）</span></div>
    <div style="display:flex;gap:10px;align-items:flex-start;font-size:12px;color:#78350f;">
      <span style="background:{DC['main']};color:white;width:20px;height:20px;border-radius:50%;
            display:flex;align-items:center;justify-content:center;font-weight:900;font-size:10px;flex-shrink:0;">3</span>
      <span><strong>1.2x</strong> → スクリプトを見ずに追いかける（スピードトレーニング）</span></div>
  </div>
</div>""", unsafe_allow_html=True)


# ============================================================
# TAB 4: PRONUNCIATION
# ============================================================
with tab4:
    if not data: st.markdown(ph("🎤 発音"), unsafe_allow_html=True)
    else:
        dl = data.get('_lang','en'); DC = ac(is_biz,dl); DLS = LANG[dl]
        st.markdown(f"""
<div style="background:{DC['light']};border:1px solid {DC['border']};border-radius:16px;padding:18px;margin-bottom:14px;">
  <div class="ep-label" style="background:{DC['main']};">🎤 発音チェック ({DLS['name']})</div>
  <div style="font-size:15px;font-weight:600;color:#1e293b;line-height:1.7;margin-bottom:8px;">
    {data.get('english','')}</div>
  <div style="font-size:12px;color:#64748b;">🇯🇵 {data.get('english_jp','')}</div>
</div>""", unsafe_allow_html=True)
        st.markdown('<div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:8px;">🔊 手本の発音を聴く</div>', unsafe_allow_html=True)
        st.components.v1.html(gen_audio(data.get('english',''), DLS['tts']), height=130)
        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:4px;">🎤 マイクで音読（iPhone・Android対応）</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:11px;color:#94a3b8;margin-bottom:8px;">録音後に自動で採点します</div>', unsafe_allow_html=True)
        audio_val = st.audio_input("マイクを押して録音")
        if audio_val and st.session_state.get("_client"):
            with st.spinner("AIが発音を分析中... 🎯"):
                lang_name = "Deutschen" if dl == 'de' else "英語"
                ap = f"""この音声を{lang_name}として文字起こしし、元の文「{data.get('english','')}」と比較して採点してください。
JSONのみ出力（コードブロック不要）:
{{"score":85,"transcript":"認識テキスト","good_words":["正解単語"],"bad_words":["要練習単語"],"feedback":"フィードバック（日本語1文）"}}"""
                try:
                    raw = call_audio(ap, audio_val.getvalue())
                    m = re.search(r'\{[\s\S]*\}', raw)
                    if m:
                        rd = json.loads(m.group()); sc = rd.get('score',0)
                        col = "#22c55e" if sc>=80 else "#eab308" if sc>=60 else "#ef4444"
                        ok_c = "".join([f'<span class="ep-chip-ok">{w}</span>' for w in rd.get('good_words',[])])
                        ng_c = "".join([f'<span class="ep-chip-ng">{w}</span>' for w in rd.get('bad_words',[])])
                        st.markdown(f"""
<div class="ep-card" style="margin-top:14px;">
  <div class="ep-score-box"><span style="font-size:13px;font-weight:800;color:#334155;">発音マッチ度</span>
    <span class="ep-score-num" style="color:{col};">{sc}%</span></div>
  <div class="ep-bar-wrap"><div class="ep-bar" style="width:{sc}%;background:{col};"></div></div>
  <div style="margin-bottom:10px;">{ok_c}{ng_c}</div>
  <div style="font-size:11px;color:#94a3b8;">認識テキスト: "{rd.get('transcript','')}"</div>
  {'<div style="font-size:12px;color:#475569;margin-top:8px;padding:8px;background:#f8fafc;border-radius:8px;">💬 ' + rd.get("feedback","") + '</div>' if rd.get('feedback') else ''}
</div>""", unsafe_allow_html=True)
                        if sc>=80: st.markdown('<div class="ep-alert-g">🎉 素晴らしい！次のステップへ！</div>', unsafe_allow_html=True)
                        elif sc<60: st.markdown('<div class="ep-alert-o">💡 0.8xでゆっくり練習→チャンク単位で確認しましょう</div>', unsafe_allow_html=True)
                    else: st.info(raw)
                except Exception as e: st.error(f"分析エラー: {e}")


# ============================================================
# TAB 5: PRACTICE
# ============================================================
with tab5:
    if not data: st.markdown(ph("✏️ 穴埋め練習"), unsafe_allow_html=True)
    else:
        dl = data.get('_lang','en'); DC = ac(is_biz,dl); DLS = LANG[dl]
        bq = data.get('blank_q',''); ba = data.get('blank_a',''); ht = data.get('hint','')
        st.markdown(f"""
<div style="background:{DC['light']};border:1px solid {DC['border']};border-radius:16px;padding:18px;margin-bottom:14px;">
  <div class="ep-label" style="background:{DC['main']};">✏️ 瞬発力トレーニング</div>
  <div style="font-size:11px;color:#94a3b8;margin-bottom:14px;">3秒以内に空欄の単語を思い出してください</div>
  <div style="background:white;border:2px dashed #cbd5e1;border-radius:14px;
       padding:18px;text-align:center;margin-bottom:14px;">
    <div style="font-size:19px;font-weight:700;color:#1e293b;">{bq}</div>
    <div style="font-size:12px;color:#94a3b8;margin-top:6px;">💡 {ht}</div>
  </div>
</div>""", unsafe_allow_html=True)
        if st.button("⏱ 3秒カウントダウンスタート", use_container_width=True, key="timer_btn"):
            ph_t = st.empty()
            for i in range(3,0,-1):
                ph_t.markdown(f'<div style="text-align:center;font-size:84px;font-weight:900;color:{DC["main"]};padding:6px 0;">{i}</div>', unsafe_allow_html=True)
                time.sleep(1)
            ph_t.markdown('<div style="text-align:center;font-size:26px;font-weight:900;color:#f97316;">答えて！</div>', unsafe_allow_html=True)
        user_ans = st.text_input("答えを入力", placeholder="単語を入力...", key="prac_ans")
        c1,c2 = st.columns(2)
        with c1: chk = st.button("✅ 答え合わせ", use_container_width=True, type="primary", key="chk_btn")
        with c2: ply = st.button("🔊 正解の文を聴く", use_container_width=True, key="ply_btn")
        if chk and user_ans:
            ok = user_ans.lower().strip() == ba.lower().strip()
            msg = "🎉 正解！素晴らしい！" if ok else f'あなたの回答: "<strong>{user_ans}</strong>" → もう一度！'
            st.markdown(f"""
<div style="background:white;border:1px solid #e2e8f0;border-radius:16px;padding:18px;text-align:center;margin-top:10px;">
  <div style="font-size:11px;color:#94a3b8;margin-bottom:3px;">正解:</div>
  <div style="font-size:28px;font-weight:900;color:#22c55e;margin-bottom:8px;">{ba}</div>
  <div style="color:{"#22c55e" if ok else "#f97316"};font-size:13px;">{msg}</div>
</div>""", unsafe_allow_html=True)
        if ply: st.components.v1.html(gen_audio(data.get('english',''), DLS['tts']), height=130)
        if st.button("🔄 別の穴埋め問題を生成", key="regen_blank"):
            if st.session_state.get("_client") and data.get('english'):
                with st.spinner():
                    try:
                        rp = f"""文「{data['english']}」から別の単語を空欄にした穴埋め問題を作ってください。
JSONのみ: {{"blank_q":"穴埋め文（___）","blank_a":"正解","hint":"ヒント（日本語）"}}"""
                        raw = call_text(rp)
                        m = re.search(r'\{[\s\S]*\}', raw)
                        if m:
                            nd = json.loads(m.group())
                            st.session_state.script_data.update(nd); st.rerun()
                    except: pass
        if data.get('paraphrases'):
            with st.expander("🆘 言い換えレスキュー"):
                for p in data['paraphrases']:
                    st.markdown(f'<div class="ep-para"><span class="ep-para-hard">{p.get("difficult","")}</span><span style="color:#94a3b8;">→</span><span class="ep-para-easy">{p.get("simple","")}</span><span class="ep-para-note">（{p.get("note","")}）</span></div>', unsafe_allow_html=True)


# ============================================================
# TAB 6: ROLEPLAY
# ============================================================
with tab6:
    if not data: st.markdown(ph("🎭 ロールプレイ"), unsafe_allow_html=True)
    else:
        dl = data.get('_lang','en'); DC = ac(is_biz,dl); DLS = LANG[dl]
        if not st.session_state.chat_history:
            openers = {
                ('en',True):"Hello! I'm visiting your booth today. Tell me about your product.",
                ('en',False):"Hi there! Nice to meet you. How are you today?",
                ('de',True):"Guten Tag! Ich besuche Ihren Stand heute. Erzählen Sie mir von Ihrem Produkt.",
                ('de',False):"Hallo! Schön, Sie kennenzulernen. Wie geht es Ihnen?",
            }
            st.session_state.chat_history = [{"role":"assistant","content":openers.get((dl,is_biz),"Hello!")}]

        chat_html = '<div class="ep-chat-wrap">'
        for msg in st.session_state.chat_history:
            if msg["role"]=="user":
                chat_html += f'<div class="ep-bubble-user" style="background:{DC["main"]};">{msg["content"]}</div>'
            else:
                lbl = DLS['persona_biz'] if is_biz else DLS['persona_daily']
                chat_html += f'<div class="ep-bubble-ai"><div class="ep-bubble-label">{lbl}</div>{msg["content"]}</div>'
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        if data.get('paraphrases'):
            with st.expander("🆘 言い換えレスキュー"):
                for p in data['paraphrases']:
                    st.markdown(f'<div class="ep-para"><span class="ep-para-hard">{p.get("difficult","")}</span><span>→</span><span class="ep-para-easy">{p.get("simple","")}</span></div>', unsafe_allow_html=True)

        show_hint = st.checkbox("💡 AIの返答の日本語訳を表示", value=True, key="show_trans")
        user_msg = st.chat_input(f"{DLS['name']}で返事を入力してください...")
        if user_msg and st.session_state.get("_client"):
            st.session_state.chat_history.append({"role":"user","content":user_msg})
            with st.spinner("AIが返答中..."):
                role_prompts = {
                    ('en',True):"You are a foreign buyer at a trade show. Ask follow-up product questions in English.",
                    ('en',False):"You are a friendly native English speaker. Continue the conversation in simple English.",
                    ('de',True):"Sie sind ein ausländischer Käufer auf einer Messe. Stellen Sie Folgefragen auf Deutsch.",
                    ('de',False):"Sie sind ein freundlicher Muttersprachler. Setzen Sie das Gespräch auf einfachem Deutsch fort.",
                }
                cp = role_prompts.get((dl,is_biz),"")
                cp += f"\nKontext/文脈: {data.get('english','')}"
                if show_hint: cp += "\n返答後に（日本語訳）を括弧で添えてください。"
                cp += f"\nユーザー: {user_msg}"
                try:
                    reply = call_text(cp)
                    st.session_state.chat_history.append({"role":"assistant","content":reply.strip()})
                    st.rerun()
                except Exception as e: st.error(f"返答エラー: {e}")

        c_r, c_d = st.columns([1,1])
        with c_r:
            if st.button("🔄 会話リセット", key="reset_chat"):
                st.session_state.chat_history=[]; st.rerun()
        with c_d:
            if st.button("📈 少し難しく話しかける", key="bump_diff"):
                if st.session_state.get("_client"):
                    with st.spinner():
                        try:
                            bp = f"{'Auf Deutsch' if dl=='de' else 'In English'}, ask a more advanced follow-up question about: {data.get('english','')}"
                            reply = call_text(bp)
                            st.session_state.chat_history.append({"role":"assistant","content":reply.strip()})
                            st.rerun()
                        except: pass


# ============================================================
# TAB 7: マイ学習帳
# ============================================================
with tab7:
    saved = st.session_state.saved_list
    st.markdown(f"""
<div style="background:linear-gradient(135deg,#1e293b,#334155);color:white;
     padding:18px 22px;border-radius:16px;margin-bottom:16px;">
  <div style="font-size:18px;font-weight:900;margin-bottom:4px;">📚 マイ学習帳</div>
  <div style="font-size:12px;opacity:.75;">保存したスクリプトをいつでも呼び出せます</div>
  <div style="display:inline-block;background:rgba(255,255,255,.2);border-radius:20px;
       padding:3px 12px;font-size:12px;font-weight:700;margin-top:8px;">
    {len(saved)} 件保存済み</div>
</div>""", unsafe_allow_html=True)
    if not saved:
        st.markdown('<div class="ep-ph"><div class="ep-ph-icon">📭</div><div class="ep-ph-title">まだ保存されていません</div><div class="ep-ph-sub">「📖 スクリプト」タブの「📚 マイ学習帳に保存」から保存できます</div></div>', unsafe_allow_html=True)
    else:
        exp = json.dumps([{"title":s["title"],"script":s["english"],"jp":s.get("english_jp",""),
                           "level":s["level"],"lang":s.get("lang","en"),"saved_at":s["saved_at"]}
                          for s in saved], ensure_ascii=False, indent=2)
        st.download_button("⬇️ 学習リストをJSONでダウンロード", data=exp,
                           file_name="pitch_saved.json", mime="application/json")
        st.markdown("---")
        for item in reversed(saved):
            il = item.get("lang","en"); IC = ac(item.get("mode")=="business",il); ILS = LANG[il]
            st.markdown(f"""
<div class="save-card">
  <div style="margin-bottom:8px;">
    <span style="font-size:10px;background:{IC['light']};color:{IC['main']};
          border-radius:12px;padding:2px 8px;font-weight:700;">
      {ILS['flag']} {item.get('level','')[:10]}</span>
    <span style="font-size:10px;color:#94a3b8;margin-left:8px;">📅 {item['saved_at']}</span>
  </div>
  <div style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:4px;">{item['english']}</div>
  <div style="font-size:12px;color:#64748b;margin-bottom:8px;">🇯🇵 {item.get('english_jp','')}</div>
  <div style="font-size:11px;color:#94a3b8;">元の入力: {item.get('source_ja','')[:50]}…</div>
</div>""", unsafe_allow_html=True)
            cl, cd = st.columns([2,1])
            with cl:
                if st.button("📂 この内容で学習再開", key=f"load_{item['id']}", use_container_width=True):
                    st.session_state.script_data = item["data"]
                    st.session_state.chat_history = []
                    st.success("✅ 読み込みました！「📖 スクリプト」タブを確認してください。")
            with cd:
                if st.button("🗑️ 削除", key=f"del_{item['id']}", use_container_width=True):
                    st.session_state.saved_list = [s for s in saved if s["id"]!=item["id"]]
                    st.rerun()


# ── フィラーカード ────────────────────────────────────────────
if is_biz and data:
    dl = data.get('_lang','en'); DC = ac(True,dl); DLS = LANG[dl]
    fb_bg  = "#eff6ff" if dl=='en' else "#fffbeb"
    fb_bdr = "#bfdbfe" if dl=='en' else "#fde68a"
    fb_tx  = "#1d4ed8" if dl=='en' else "#b45309"
    fc = "".join([
        f'<div class="ep-filler-card" style="background:{fb_bg};border:1px solid {fb_bdr};">'
        f'<div class="ep-filler-en" style="color:{fb_tx};">{fp_}</div>'
        f'<div class="ep-filler-jp">{jp}</div></div>'
        for fp_,jp in FILLERS[dl]
    ])
    st.markdown(f"""
<div class="ep-filler-wrap">
  <div style="font-size:11px;font-weight:700;color:#94a3b8;">{DLS['flag']} {DLS['filler_label']}</div>
  <div class="ep-filler-grid">{fc}</div>
</div>""", unsafe_allow_html=True)

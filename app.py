# ============================================================
# English Pitch & Talk  ── 完全改良版
# 改善点: ①例文パネル廃止 ②音声入力 ③PDF ④URL ⑤日常強化
#         ⑥学習帳保存 ⑦レベル選択 ⑧学習効率UP機能 + モデル修正
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
except:
    BS4_OK = False

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(page_title="🇺🇸 English Pitch & Talk",
                   page_icon="🇺🇸", layout="centered",
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
.ep-filler-card{background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:8px 12px}
.ep-filler-en{font-weight:700;color:#1d4ed8;font-size:12px}
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
.level-pill{display:inline-block;border-radius:20px;padding:3px 10px;font-size:11px;
  font-weight:700;margin-right:6px}
.input-method-tab{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}
.imt-btn{padding:7px 14px;border-radius:20px;border:2px solid #e2e8f0;
  background:white;font-weight:700;font-size:12px;cursor:pointer;
  transition:all .15s;color:#64748b}
.imt-btn.active{color:white;border-color:transparent}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ────────────────────────────────────────────────
LEVELS = {
    "🌱 初学者 (A1)":      "be動詞・have・like等の最基本動詞のみ。主語＋動詞の最小構造。5単語以内。",
    "📗 基礎 (A2/TOEIC400)": "中学英語。1文12単語以内。SVO構造のみ。関係代名詞・接続詞禁止。",
    "📘 中級 (B1/TOEIC600)": "高校英語。because/when等の接続詞可。やや自然な流れ。",
    "📙 上級 (B2/TOEIC800)": "ビジネス英語。受動態・完了形・専門用語適宜使用。",
    "🚀 ネイティブ風":       "ネイティブが日常的に使う自然な表現。慣用句・略語・フィラー語も使用可。",
}
DAILY_SCENARIOS = {
    "🎯 おまかせ":         "ユーザーの入力に最適な日常表現",
    "☕ カフェ/レストラン": "飲食店での注文、好みの表現、会計",
    "🗺️ 観光/道案内":      "観光地での会話、道を聞く・教える",
    "🏨 ホテル/交通":       "チェックイン、部屋のリクエスト、タクシー",
    "🛒 買い物":            "商品の選び方、値段、返品・交換",
    "👋 自己紹介/雑談":     "名前・職業・趣味の紹介、スモールトーク",
    "📞 電話/リモート":     "ビジネス電話、オンライン会議でのフレーズ",
    "🚨 緊急/トラブル":     "困ったとき、体調不良、助けを求める",
    "✈️ 空港/機内":         "搭乗手続き、入国審査、機内でのやり取り",
}
FILLERS = [
    ("That's a great question.", "いい質問ですね"),
    ("Let me explain.", "説明します"),
    ("In other words...", "つまり..."),
    ("For example...", "例えば..."),
    ("The key point is...", "重要なのは..."),
    ("Could you repeat that?", "繰り返してください"),
    ("One moment, please.", "少々お待ちください"),
    ("I understand.", "承知しました"),
    ("Good point!", "おっしゃる通り"),
    ("Let me check.", "確認させてください"),
]
EXAMPLES = {
    True:  ["このセンサーは従来品の半分の電力で動作します",
            "弊社の新製品は防水・防塵性能を備えています",
            "納期は2週間です。大量注文も対応可能です",
            "このシステムは導入コストを30%削減できます"],
    False: ["コーヒーを1杯ください",
            "駅への行き方を教えてください",
            "おすすめのランチは何ですか？",
            "空港までどのくらいかかりますか？"],
}

# ── HELPERS ──────────────────────────────────────────────────
def ac(is_biz):
    return ({"main":"#1d4ed8","light":"#eff6ff","border":"#bfdbfe"} if is_biz
            else {"main":"#0d9488","light":"#f0fdfa","border":"#99f6e4"})

def ph(name):
    return f"""<div class="ep-ph"><div class="ep-ph-icon">📝</div>
<div class="ep-ph-title">「📝 入力」タブで日本語を入力してください</div>
<div class="ep-ph-sub">{name} はコンテンツ生成後に表示されます</div></div>"""

def gen_audio(text):
    try:
        tts = gTTS(text=text, lang='en'); fp = io.BytesIO()
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
    if not PDF_OK:
        return "※ requirements.txt に pypdf を追加してください"
    reader = PdfReader(io.BytesIO(file.read()))
    txt = "\n".join(p.extract_text() or "" for p in reader.pages[:10])
    return txt[:3000]

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
    except Exception as e:
        return f"取得失敗: {e}"

def transcribe_ja(audio_bytes, mdl) -> str:
    try:
        res = mdl.generate_content(
            ["この音声を日本語として文字起こしし、テキストのみ出力してください。",
             {"mime_type":"audio/wav","data":audio_bytes}])
        return res.text.strip()
    except:
        return ""

def build_prompt(user_input, is_biz, level_key, scenario=""):
    level_inst = LEVELS.get(level_key, LEVELS["📗 基礎 (A2/TOEIC400)"])
    scene = f"展示会・ビジネス（製品説明・技術紹介・商談）" if is_biz else f"日常会話 ― {scenario}"
    return f"""
以下の条件で英語学習コンテンツをJSONで生成してください。コードブロック不要。

[入力文]: {user_input}
[場面]: {scene}
[レベル指示]: {level_inst}

[ルール] 1文最大12単語。SVO構造優先。レベルに合わせた語彙・文法を厳守。

{{
  "english": "完成英文（複数文はスペースで区切る）",
  "english_jp": "英文の自然な日本語訳",
  "chunked": "スラッシュ区切り英文（Our product / is light. It saves / energy.）",
  "grammar": "文法・フレーズ解説（日本語、2〜3行）",
  "vocab": {{"単語": "意味（日本語）"}},
  "blank_q": "穴埋め問題文（___で空欄を示す）",
  "blank_a": "正解の単語",
  "hint": "穴埋めヒント（日本語）",
  "qa_pairs": [
    {{"question": "英語質問", "question_jp": "日本語訳", "hint": "回答ヒント（英語）"}}
  ],
  "paraphrases": [
    {{"difficult": "難しい表現", "simple": "簡単な言い換え", "note": "メモ（日本語）"}}
  ]
}}
"""

def build_context_prompt(context, src_label, is_biz, level_key):
    level_inst = LEVELS.get(level_key, LEVELS["📗 基礎 (A2/TOEIC400)"])
    return f"""
以下は{src_label}から取得したテキストです。
最も重要な内容を1〜3文で要約し、英語学習コンテンツを作成してください。

[テキスト]: {context[:2000]}
[場面]: {"展示会・ビジネス" if is_biz else "日常会話"}
[レベル]: {level_inst}

コードブロック不要でJSONのみ出力:
{{
  "english": "要約英文",
  "english_jp": "日本語訳",
  "chunked": "スラッシュ区切り英文",
  "grammar": "文法解説（日本語）",
  "vocab": {{"単語": "意味"}},
  "blank_q": "穴埋め問題文（___）",
  "blank_a": "正解",
  "hint": "ヒント（日本語）",
  "qa_pairs": [{{"question": "英語質問", "question_jp": "日本語訳", "hint": "ヒント"}}],
  "paraphrases": [{{"difficult": "難表現", "simple": "簡単な言い換え", "note": "メモ（日本語）"}}]
}}
"""

def do_generate(prompt, sys_p, mdl):
    """Generate and parse JSON from model"""
    res = mdl.generate_content([sys_p, prompt])
    m = re.search(r'\{[\s\S]*\}', res.text)
    if not m:
        raise ValueError("JSONが見つかりません")
    return json.loads(m.group())

# ── API KEY ──────────────────────────────────────────────────
api_key = ""
try:
    api_key = st.secrets.get("GEMINI_API_KEY", st.secrets.get("API_KEY", ""))
except:
    pass
if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY", "")

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:14px 0 8px;">
  <div style="font-size:19px;font-weight:900;color:white;margin-bottom:3px;">🇺🇸 English Pitch & Talk</div>
  <div style="font-size:11px;color:rgba(255,255,255,.5);">AI英会話トレーナー Pro</div>
</div>
<hr style="border-color:rgba(255,255,255,.1);margin:8px 0 14px;">
""", unsafe_allow_html=True)
    if not api_key:
        mk = st.text_input("🔑 Gemini API Key", type="password", placeholder="AIzaSy...")
        if mk:
            api_key = mk
            st.markdown('<div style="color:#4ade80;font-size:12px;font-weight:700;">✅ APIキー設定済み</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#fbbf24;font-size:12px;font-weight:700;">⚠️ APIキー未設定</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#4ade80;font-size:12px;font-weight:700;">✅ APIキー自動連携済み</div>', unsafe_allow_html=True)
    st.markdown("""
<hr style="border-color:rgba(255,255,255,.1);margin:14px 0;">
<div style="font-size:11px;font-weight:700;color:rgba(255,255,255,.6);margin-bottom:8px;">📖 使い方</div>
<div style="font-size:11px;color:rgba(255,255,255,.7);line-height:2.1;">
① モード＆レベルを選択<br>② 日本語を入力（テキスト/音声/PDF/URL）<br>③「生成する」ボタン<br>④ 各タブで学習！<br>⑤ 気に入ったら📚に保存
</div>
<hr style="border-color:rgba(255,255,255,.1);margin:14px 0;">
<div style="font-size:10px;color:rgba(255,255,255,.3);line-height:1.8;">
🔧 モデル: gemini-2.0-flash<br>🔊 TTS: gTTS<br>🎤 STT: Gemini Audio
</div>
""", unsafe_allow_html=True)

# ── SESSION STATE ────────────────────────────────────────────
defaults = {"script_data":None,"chat_history":[],"saved_list":[],
            "input_method":"✏️ テキスト","voice_text":"","gen_count":0}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ── MODEL ★ gemini-2.0-flash ★ ─────────────────────────────
mdl = None
if api_key:
    genai.configure(api_key=api_key)
    mdl = genai.GenerativeModel('gemini-2.0-flash')

# ── HEADER & MODE ────────────────────────────────────────────
mode = st.radio("モード",["🏢 展示会・ビジネス","☕ 日常会話・基礎"],
                horizontal=True, label_visibility="collapsed")
is_biz = "展示会" in mode
C = ac(is_biz)
st.markdown(f"<style>:root{{--acc:{C['main']};}}</style>", unsafe_allow_html=True)

st.markdown(f"""
<div style="background:linear-gradient(135deg,{C['main']},{C['main']}cc);color:white;
     padding:18px 22px 16px;border-radius:16px;margin-bottom:4px;
     box-shadow:0 4px 20px rgba(0,0,0,.15);">
  <div style="font-size:21px;font-weight:900;letter-spacing:-.5px;margin-bottom:3px;">
    🇺🇸 English Pitch & Talk</div>
  <div style="font-size:11px;opacity:.75;">
    {"展示会・商談英語をマスター" if is_biz else "日常英会話を基礎から学ぼう"}</div>
  <div style="display:inline-block;background:rgba(255,255,255,.2);
       border:1px solid rgba(255,255,255,.4);border-radius:20px;
       padding:3px 12px;font-size:11px;font-weight:700;margin-top:8px;">
    {"🏢 展示会モード" if is_biz else "☕ 日常会話モード"}</div>
</div>
""", unsafe_allow_html=True)

sys_p = ("あなたはビジネス英語の専門家です。展示会で通じるシンプルな英文を作成してください。" if is_biz
         else "あなたは日常英会話のコーチです。旅行・生活・雑談で使えるシンプルな英文を作成してください。")

# ── TABS ─────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs(
    ["📝 入力","📖 スクリプト","🔊 音読","🎤 発音","✏️ 練習","🎭 会話","📚 マイ学習帳"])
data = st.session_state.script_data

# ============================================================
# TAB 1: INPUT ── ①例文パネル廃止 ②音声入力 ③PDF ④URL ⑦レベル
# ============================================================
with tab1:
    # ── レベル選択 ⑦
    level_key = st.selectbox("📊 英語レベル",list(LEVELS.keys()),index=1,
                             help="生成される英文の難易度を選択してください")
    st.markdown(f'<div style="font-size:11px;color:#94a3b8;margin-bottom:12px;">📌 {LEVELS[level_key][:40]}…</div>',
                unsafe_allow_html=True)

    # ── シナリオ（日常モードのみ）
    scenario = ""
    if not is_biz:
        scenario = st.selectbox("🎬 シナリオ", list(DAILY_SCENARIOS.keys()))

    # ── 入力方法選択 ① ② ③ ④
    im = st.radio("入力方法",["✏️ テキスト","🎤 音声入力","📄 PDF","🔗 URL"],
                  horizontal=True, key="input_method_radio",
                  help="テキスト直接入力・マイク音声・PDFファイル・Webサイトから入力できます")

    user_input = ""

    # ── テキスト入力
    if im == "✏️ テキスト":
        # ① 例文ボタンを小さいピルに変更（大きなパネル廃止）
        st.markdown('<div style="font-size:11px;color:#64748b;font-weight:600;margin-bottom:6px;">💡 例文：</div>',
                    unsafe_allow_html=True)
        ex_cols = st.columns(len(EXAMPLES[is_biz]))
        chosen = ""
        for i, ex in enumerate(EXAMPLES[is_biz]):
            with ex_cols[i]:
                if st.button(ex[:10]+"…", key=f"ex_{i}", use_container_width=True):
                    chosen = ex
        init_val = chosen if chosen else ""
        user_input = st.text_area("英語にしたい日本語を入力",value=init_val,
                                  placeholder="例: 弊社の新製品は従来より30%軽量です。",
                                  height=100, key="text_input_main")

    # ── 音声入力 ②
    elif im == "🎤 音声入力":
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:14px;
     padding:14px;margin-bottom:12px;">
  <div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:8px;">
    🎤 マイクで日本語を録音 → 自動文字起こし
  </div>
  <div style="font-size:11px;color:#64748b;">ボタンを押して話してください。Gemini AIが文字起こしします。</div>
</div>
""", unsafe_allow_html=True)
        voice_audio = st.audio_input("🎤 録音ボタンを押して日本語を話してください",
                                     key="voice_input_ja")
        if voice_audio and mdl:
            with st.spinner("文字起こし中..."):
                txt = transcribe_ja(voice_audio.getvalue(), mdl)
                if txt:
                    st.session_state.voice_text = txt
                    st.success(f"✅ 認識: {txt}")
        if st.session_state.voice_text:
            user_input = st.text_area("認識されたテキスト（編集可）",
                                      value=st.session_state.voice_text,
                                      height=80, key="voice_edit")
        else:
            user_input = ""

    # ── PDF ③
    elif im == "📄 PDF":
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:14px;
     padding:14px;margin-bottom:12px;">
  <div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:6px;">
    📄 製品カタログ・資料PDF → 英語セリフ自動生成
  </div>
  <div style="font-size:11px;color:#64748b;">PDFをアップロードすると、内容を要約して英語の説明文を作成します。</div>
</div>
""", unsafe_allow_html=True)
        pdf_file = st.file_uploader("PDFファイルを選択", type=["pdf"], key="pdf_upload")
        if pdf_file:
            if not PDF_OK:
                st.error("❌ PyPDF がインストールされていません。requirements.txt に pypdf を追加してください。")
            else:
                with st.spinner("PDFを読み込み中..."):
                    pdf_text = extract_pdf(pdf_file)
                st.text_area("抽出テキスト（確認用）", value=pdf_text[:500]+"…", height=80, disabled=True)
                user_input = f"[PDF内容の要約]: {pdf_text}"
                st.success("✅ PDFを読み込みました。「英文を生成する」を押してください。")

    # ── URL ④
    elif im == "🔗 URL":
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:14px;
     padding:14px;margin-bottom:12px;">
  <div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:6px;">
    🔗 WebサイトURL → 内容要約 → 英語セリフ生成
  </div>
  <div style="font-size:11px;color:#64748b;">会社HP・製品ページなどのURLを入力してください。</div>
</div>
""", unsafe_allow_html=True)
        url_in = st.text_input("URLを入力", placeholder="https://example.com/product",
                               key="url_input")
        if url_in and st.button("🔍 URLを取得", key="fetch_url"):
            with st.spinner("Webページを取得中..."):
                url_text = extract_url(url_in)
            if "失敗" in url_text:
                st.error(url_text)
                user_input = ""
            else:
                st.text_area("取得テキスト（確認用）", value=url_text[:400]+"…", height=70, disabled=True)
                st.session_state["url_text_cache"] = url_text
                st.success("✅ Webページを取得しました。")
        if st.session_state.get("url_text_cache"):
            user_input = f"[URL内容の要約]: {st.session_state['url_text_cache']}"

    st.markdown('<div style="font-size:10px;color:#94a3b8;margin-top:4px;margin-bottom:10px;">💡 短い文・箇条書き・要点ほど高品質なコンテンツが生成されます</div>',
                unsafe_allow_html=True)

    # ── 生成ボタン
    if st.button("✨ 英文＆学習コンテンツを生成する", type="primary",
                 use_container_width=True, key="gen_btn"):
        if not api_key:
            st.error("❌ APIキーが設定されていません。")
        elif not user_input or not user_input.strip():
            st.warning("テキスト・音声・PDF・URLのいずれかで内容を入力してください。")
        elif not mdl:
            st.error("❌ モデルの初期化に失敗しました。")
        else:
            with st.spinner("AIが英文を作成中... ✨"):
                try:
                    if user_input.startswith("[PDF内容") or user_input.startswith("[URL内容"):
                        prompt = build_context_prompt(user_input, im, is_biz, level_key)
                    else:
                        prompt = build_prompt(user_input, is_biz, level_key, scenario)
                    result = do_generate(prompt, sys_p, mdl)
                    result["_source_ja"] = user_input[:100]
                    result["_level"] = level_key
                    result["_mode"] = "business" if is_biz else "daily"
                    st.session_state.script_data = result
                    st.session_state.chat_history = []
                    st.session_state.voice_text = ""
                    st.session_state.gen_count += 1
                    data = result
                    st.success("✅ 生成完了！「📖 スクリプト」タブに進んでください。")
                    st.balloons()
                except Exception as e:
                    err = str(e)
                    if "404" in err or "not found" in err.lower():
                        st.error("❌ モデルエラー: gemini-2.0-flash が見つかりません。APIキーを確認してください。")
                    elif "403" in err or "PERMISSION" in err:
                        st.error("❌ 認証エラー: APIキーを再確認してください。")
                    else:
                        st.error(f"❌ エラー: {err}")


# ============================================================
# TAB 2: SCRIPT
# ============================================================
with tab2:
    if not data:
        st.markdown(ph("📖 スクリプト"), unsafe_allow_html=True)
    else:
        lv = data.get("_level","")
        st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
  <span style="font-size:11px;color:#94a3b8;">レベル: <strong style="color:{C['main']};">{lv}</strong></span>
</div>
<div class="ep-script" style="background:{C['light']};border:2px solid {C['border']};
     border-left-color:{C['main']};">
  <div class="ep-label" style="background:{C['main']};">📖 英文スクリプト（チャンク読み）</div>
  <div class="ep-script-text">{data.get('chunked', data.get('english',''))}</div>
  <div style="font-size:13px;color:#475569;margin-top:10px;padding:8px;background:rgba(255,255,255,.7);
       border-radius:8px;">🇯🇵 {data.get('english_jp','')}</div>
  <div style="font-size:11px;color:#94a3b8;margin-top:6px;">/ はチャンク（意味の塊）の区切りです</div>
</div>
""", unsafe_allow_html=True)

        col_save, col_copy = st.columns([1,1])
        with col_save:
            if st.button("📚 マイ学習帳に保存", use_container_width=True, key="save_btn"):
                item = {
                    "id": int(time.time()),
                    "title": data.get("english","")[:40]+"…",
                    "english": data.get("english",""),
                    "english_jp": data.get("english_jp",""),
                    "chunked": data.get("chunked",""),
                    "level": data.get("_level",""),
                    "mode": data.get("_mode",""),
                    "source_ja": data.get("_source_ja",""),
                    "saved_at": datetime.now().strftime("%m/%d %H:%M"),
                    "data": data,
                }
                if not any(x["id"]==item["id"] for x in st.session_state.saved_list):
                    st.session_state.saved_list.append(item)
                    st.success(f"✅ 保存しました！（📚 マイ学習帳に {len(st.session_state.saved_list)} 件）")

        st.markdown(f"""
<div class="ep-card">
  <div class="ep-label" style="background:{C['main']};">📚 文法・フレーズ解説</div>
  <div style="font-size:13px;color:#475569;line-height:1.8;">{data.get('grammar','')}</div>
</div>
""", unsafe_allow_html=True)
        if data.get('vocab'):
            v_html = "".join([
                f'<span class="ep-vocab" style="background:{C["light"]};color:{C["main"]};"><strong>{k}</strong>: {v}</span>'
                for k,v in data['vocab'].items()])
            st.markdown(f"""
<div class="ep-card">
  <div class="ep-label" style="background:{C['main']};">📝 重要語彙</div><div>{v_html}</div>
</div>""", unsafe_allow_html=True)

        if is_biz and data.get('qa_pairs'):
            qa_html = "".join([f"""
<div class="ep-qa">
  <div style="font-size:13px;font-weight:600;color:#1e293b;">{q.get('question','')}</div>
  <div style="font-size:11px;color:#94a3b8;">{q.get('question_jp','')}</div>
  <div style="font-size:11px;color:{C['main']};font-weight:600;margin-top:5px;">💡 {q.get('hint','')}</div>
</div>""" for q in data['qa_pairs']])
            st.markdown(f"""
<div class="ep-card">
  <div class="ep-label" style="background:{C['main']};">🙋 想定Q&A</div>{qa_html}
</div>""", unsafe_allow_html=True)

        st.markdown(f"""
<div class="ep-tip">
  💡 <strong>チャンク読みのコツ：</strong>スラッシュ（/）で区切り、<strong>左から順番に</strong>
  意味をつかみながら読みましょう。日本語のように後ろから返り読みするのはNGです！
</div>""", unsafe_allow_html=True)


# ============================================================
# TAB 3: AUDIO
# ============================================================
with tab3:
    if not data:
        st.markdown(ph("🔊 音読"), unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:16px;
     padding:18px;margin-bottom:14px;">
  <div class="ep-label" style="background:{C['main']};">🎵 シャドーイング・音読プレイヤー</div>
  <div style="background:white;border:1px solid {C['border']};border-radius:12px;
       padding:14px;margin-bottom:14px;font-size:16px;font-weight:600;
       color:#1e293b;line-height:1.8;">{data.get('chunked','')}</div>
  <div style="font-size:12px;color:#475569;padding:6px 10px;background:rgba(255,255,255,.6);
       border-radius:8px;margin-bottom:12px;">🇯🇵 {data.get('english_jp','')}</div>
</div>""", unsafe_allow_html=True)
        st.components.v1.html(gen_audio(data.get('english','')), height=130)
        st.markdown(f"""
<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:14px;padding:16px;margin-top:14px;">
  <div style="font-size:12px;font-weight:800;color:#92400e;margin-bottom:10px;">💡 安河内式 音読 3ステップ</div>
  {"".join([f'<div style="display:flex;gap:10px;align-items:flex-start;font-size:12px;color:#78350f;margin-bottom:8px;"><span style="background:{C[chr(39)]};color:white;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:10px;flex-shrink:0;">{n}</span><span>{t}</span></div>' for n,t in [("1","<strong>0.8x</strong> → 音声を聴きながら口をパクパク（オーバーラッピング）"),("2","<strong>1.0x</strong> → 声に出して一緒に読む（シャドーイング）"),("3","<strong>1.2x</strong> → スクリプトを見ずに追いかける（スピードトレーニング）")]])}
</div>""".replace("{C[chr(39)]}", C['main']), unsafe_allow_html=True)


# ============================================================
# TAB 4: PRONUNCIATION
# ============================================================
with tab4:
    if not data:
        st.markdown(ph("🎤 発音"), unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:16px;
     padding:18px;margin-bottom:14px;">
  <div class="ep-label" style="background:{C['main']};">🎤 発音チェック</div>
  <div style="font-size:15px;font-weight:600;color:#1e293b;line-height:1.7;margin-bottom:8px;">
    {data.get('english','')}</div>
  <div style="font-size:12px;color:#64748b;">🇯🇵 {data.get('english_jp','')}</div>
</div>""", unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:8px;">🔊 手本の発音を聴く</div>', unsafe_allow_html=True)
        st.components.v1.html(gen_audio(data.get('english','')), height=130)
        st.markdown("<hr style='margin:14px 0;'>", unsafe_allow_html=True)
        st.markdown('<div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:8px;">🎤 マイクで音読（録音後に自動採点）</div>', unsafe_allow_html=True)
        audio_val = st.audio_input("マイクを押して録音")
        if audio_val and mdl:
            with st.spinner("AIが発音を分析中... 🎯"):
                ap = f"""この音声を英語として文字起こしし、元の文「{data.get('english','')}」と比較して採点してください。
JSONのみ出力（コードブロック不要）:
{{"score":85,"transcript":"認識テキスト","good_words":["正解単語"],"bad_words":["要練習単語"],"feedback":"フィードバック（日本語1文）"}}"""
                try:
                    res = mdl.generate_content([ap,{"mime_type":"audio/wav","data":audio_val.getvalue()}])
                    m = re.search(r'\{[\s\S]*\}', res.text)
                    if m:
                        rd = json.loads(m.group())
                        sc = rd.get('score',0)
                        col = "#22c55e" if sc>=80 else "#eab308" if sc>=60 else "#ef4444"
                        ok_chips = "".join([f'<span class="ep-chip-ok">{w}</span>' for w in rd.get('good_words',[])])
                        ng_chips = "".join([f'<span class="ep-chip-ng">{w}</span>' for w in rd.get('bad_words',[])])
                        st.markdown(f"""
<div class="ep-card" style="margin-top:14px;">
  <div class="ep-score-box">
    <span style="font-size:13px;font-weight:800;color:#334155;">発音マッチ度</span>
    <span class="ep-score-num" style="color:{col};">{sc}%</span>
  </div>
  <div class="ep-bar-wrap"><div class="ep-bar" style="width:{sc}%;background:{col};"></div></div>
  <div style="margin-bottom:10px;">{ok_chips}{ng_chips}</div>
  <div style="font-size:11px;color:#94a3b8;">認識テキスト: "{rd.get('transcript','')}"</div>
  {'<div style="font-size:12px;color:#475569;margin-top:8px;padding:8px;background:#f8fafc;border-radius:8px;">💬 ' + rd.get('feedback','') + '</div>' if rd.get('feedback') else ''}
</div>""", unsafe_allow_html=True)
                        if sc>=80: st.markdown('<div class="ep-alert-g">🎉 素晴らしい！次のステップへ！</div>', unsafe_allow_html=True)
                        elif sc<60: st.markdown('<div class="ep-alert-o">💡 0.8xでゆっくり練習→スラッシュ単位で確認しましょう</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"分析エラー: {e}")


# ============================================================
# TAB 5: PRACTICE
# ============================================================
with tab5:
    if not data:
        st.markdown(ph("✏️ 穴埋め練習"), unsafe_allow_html=True)
    else:
        blank_q = data.get('blank_q','')
        blank_a = data.get('blank_a','')
        hint    = data.get('hint','')
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:16px;
     padding:18px;margin-bottom:14px;">
  <div class="ep-label" style="background:{C['main']};">✏️ 瞬発力トレーニング</div>
  <div style="font-size:11px;color:#94a3b8;margin-bottom:14px;">3秒以内に空欄の単語を思い出してください</div>
  <div style="background:white;border:2px dashed #cbd5e1;border-radius:14px;
       padding:18px;text-align:center;margin-bottom:14px;">
    <div style="font-size:19px;font-weight:700;color:#1e293b;">{blank_q}</div>
    <div style="font-size:12px;color:#94a3b8;margin-top:6px;">💡 {hint}</div>
  </div>
</div>""", unsafe_allow_html=True)
        if st.button("⏱ 3秒カウントダウンスタート", use_container_width=True, key="timer_btn"):
            ph_t = st.empty()
            for i in range(3,0,-1):
                ph_t.markdown(f'<div style="text-align:center;font-size:84px;font-weight:900;color:{C["main"]};padding:6px 0;">{i}</div>', unsafe_allow_html=True)
                time.sleep(1)
            ph_t.markdown('<div style="text-align:center;font-size:26px;font-weight:900;color:#f97316;">答えて！</div>', unsafe_allow_html=True)

        user_ans = st.text_input("答えを入力", placeholder="英単語を入力...", key="prac_ans")
        c1,c2 = st.columns(2)
        with c1:
            chk = st.button("✅ 答え合わせ", use_container_width=True, type="primary", key="chk_btn")
        with c2:
            ply = st.button("🔊 正解の文を聴く", use_container_width=True, key="ply_btn")
        if chk and user_ans:
            ok = user_ans.lower().strip() == blank_a.lower().strip()
            col_txt = "#22c55e" if ok else "#f97316"
            msg = "🎉 正解！素晴らしい！" if ok else f'あなたの回答: "<strong>{user_ans}</strong>" → もう一度！'
            st.markdown(f"""
<div style="background:white;border:1px solid #e2e8f0;border-radius:16px;
     padding:18px;text-align:center;margin-top:10px;">
  <div style="font-size:11px;color:#94a3b8;margin-bottom:3px;">正解:</div>
  <div style="font-size:28px;font-weight:900;color:#22c55e;margin-bottom:8px;">{blank_a}</div>
  <div style="color:{col_txt};font-size:13px;">{msg}</div>
</div>""", unsafe_allow_html=True)
        if ply:
            st.components.v1.html(gen_audio(data.get('english','')), height=130)

        # ⑧ 類似問題生成ボタン
        if st.button("🔄 類似問題を別パターンで生成", key="regen_blank"):
            if mdl and data.get('english'):
                with st.spinner("別の穴埋め問題を生成中..."):
                    try:
                        rp = f"""英文「{data['english']}」から、別の単語を空欄にした穴埋め問題を作ってください。
JSONのみ出力: {{"blank_q": "穴埋め文（___）", "blank_a": "正解単語", "hint": "ヒント（日本語）"}}"""
                        res = mdl.generate_content(rp)
                        m = re.search(r'\{[\s\S]*\}', res.text)
                        if m:
                            nd = json.loads(m.group())
                            st.session_state.script_data['blank_q'] = nd['blank_q']
                            st.session_state.script_data['blank_a'] = nd['blank_a']
                            st.session_state.script_data['hint']    = nd['hint']
                            st.rerun()
                    except: pass

        if data.get('paraphrases'):
            with st.expander("🆘 言い換えレスキュー（単語が出ない時）"):
                for p in data['paraphrases']:
                    st.markdown(f"""
<div class="ep-para">
  <span class="ep-para-hard">{p.get('difficult','')}</span>
  <span style="color:#94a3b8;">→</span>
  <span class="ep-para-easy">{p.get('simple','')}</span>
  <span class="ep-para-note">（{p.get('note','')}）</span>
</div>""", unsafe_allow_html=True)


# ============================================================
# TAB 6: ROLEPLAY ── ⑤日常強化
# ============================================================
with tab6:
    if not data:
        st.markdown(ph("🎭 ロールプレイ"), unsafe_allow_html=True)
    else:
        if not st.session_state.chat_history:
            opener = ("Hello! I'm visiting your booth today. Tell me about your product." if is_biz
                      else "Hi there! Nice to meet you. How are you today?")
            st.session_state.chat_history = [{"role":"assistant","content":opener}]

        chat_html = '<div class="ep-chat-wrap">'
        for msg in st.session_state.chat_history:
            if msg["role"]=="user":
                chat_html += f'<div class="ep-bubble-user" style="background:{C["main"]};">{msg["content"]}</div>'
            else:
                lbl = "🧳 バイヤー" if is_biz else "💬 ネイティブ"
                chat_html += f'<div class="ep-bubble-ai"><div class="ep-bubble-label">{lbl}</div>{msg["content"]}</div>'
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        if data.get('paraphrases'):
            with st.expander("🆘 言い換えレスキュー"):
                for p in data['paraphrases']:
                    st.markdown(f'<div class="ep-para"><span class="ep-para-hard">{p.get("difficult","")}</span><span>→</span><span class="ep-para-easy">{p.get("simple","")}</span></div>', unsafe_allow_html=True)

        # ⑧ AIが先に日本語訳を出してから英語入力
        show_hint = st.checkbox("💡 AIの返答の日本語訳を表示", value=True, key="show_trans")

        user_msg = st.chat_input("英語で返事を入力してください...")
        if user_msg and mdl:
            st.session_state.chat_history.append({"role":"user","content":user_msg})
            with st.spinner("AIが返答中..."):
                mode_desc = "展示会のバイヤー（外国のお客さん）" if is_biz else "フレンドリーなネイティブスピーカー"
                cp = f"""あなたは{mode_desc}です。ユーザーの英語: {user_msg}
製品/話題: {data.get('english','')}
英語（1〜2文）で返答{"し、その後に括弧で日本語訳も添えてください" if show_hint else "してください"}。"""
                try:
                    chat_res = mdl.generate_content(cp)
                    st.session_state.chat_history.append({"role":"assistant","content":chat_res.text.strip()})
                    st.rerun()
                except Exception as e:
                    st.error(f"返答エラー: {e}")

        c_r, c_d = st.columns([1,1])
        with c_r:
            if st.button("🔄 会話リセット", key="reset_chat"): st.session_state.chat_history=[]; st.rerun()
        with c_d:
            # ⑧ 難易度調整
            if st.button("📈 少し難しく話しかける", key="bump_diff"):
                if mdl and st.session_state.chat_history:
                    with st.spinner():
                        try:
                            bp = f"""あなたは{('バイヤー' if is_biz else 'ネイティブ')}です。少し難しい英語表現を使って、学習者に新しい質問を1文だけしてください。文脈: {data.get('english','')}"""
                            br = mdl.generate_content(bp)
                            st.session_state.chat_history.append({"role":"assistant","content":br.text.strip()})
                            st.rerun()
                        except: pass


# ============================================================
# TAB 7: マイ学習帳 ── ⑥保存・呼び出し
# ============================================================
with tab7:
    saved = st.session_state.saved_list
    st.markdown(f"""
<div style="background:linear-gradient(135deg,#1e293b,#334155);color:white;
     padding:18px 22px;border-radius:16px;margin-bottom:16px;">
  <div style="font-size:18px;font-weight:900;margin-bottom:4px;">📚 マイ学習帳</div>
  <div style="font-size:12px;opacity:.75;">保存した英文スクリプトを呼び出せます</div>
  <div style="display:inline-block;background:rgba(255,255,255,.2);border-radius:20px;
       padding:3px 12px;font-size:12px;font-weight:700;margin-top:8px;">
    {len(saved)} 件保存済み
  </div>
</div>""", unsafe_allow_html=True)

    if not saved:
        st.markdown("""
<div class="ep-ph">
  <div class="ep-ph-icon">📭</div>
  <div class="ep-ph-title">まだ保存されていません</div>
  <div class="ep-ph-sub">「📖 スクリプト」タブの「📚 マイ学習帳に保存」ボタンから保存できます</div>
</div>""", unsafe_allow_html=True)
    else:
        # ⑧ ダウンロードボタン
        export_data = json.dumps([{
            "title":s["title"],"english":s["english"],"english_jp":s.get("english_jp",""),
            "level":s["level"],"saved_at":s["saved_at"],"source_ja":s["source_ja"]
        } for s in saved], ensure_ascii=False, indent=2)
        st.download_button("⬇️ 学習リストをJSONでダウンロード",
                           data=export_data, file_name="ep_saved.json",
                           mime="application/json")
        st.markdown("---")

        for i, item in enumerate(reversed(saved)):
            mode_badge = "🏢" if item.get("mode")=="business" else "☕"
            lv_badge = item.get("level","")[:10]
            c_item = ac(item.get("mode")=="business")
            st.markdown(f"""
<div class="save-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
    <div>
      <span style="font-size:10px;background:{c_item['light']};color:{c_item['main']};
            border-radius:12px;padding:2px 8px;font-weight:700;">{mode_badge} {lv_badge}</span>
      <span style="font-size:10px;color:#94a3b8;margin-left:8px;">📅 {item['saved_at']}</span>
    </div>
  </div>
  <div style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:4px;">{item['english']}</div>
  <div style="font-size:12px;color:#64748b;margin-bottom:8px;">🇯🇵 {item.get('english_jp','')}</div>
  <div style="font-size:11px;color:#94a3b8;">元の日本語: {item.get('source_ja','')[:50]}…</div>
</div>""", unsafe_allow_html=True)
            col_load, col_del = st.columns([2,1])
            with col_load:
                if st.button("📂 この英文で学習再開", key=f"load_{item['id']}", use_container_width=True):
                    st.session_state.script_data = item["data"]
                    st.session_state.chat_history = []
                    st.success(f"✅ 「{item['english'][:30]}...」を読み込みました！「📖 スクリプト」タブで確認してください。")
            with col_del:
                if st.button("🗑️ 削除", key=f"del_{item['id']}", use_container_width=True):
                    st.session_state.saved_list = [s for s in saved if s["id"]!=item["id"]]
                    st.rerun()


# ============================================================
# フィラーカード ─ 展示会モード・コンテンツ生成後に表示
# ============================================================
if is_biz and data:
    fc = "".join([f'<div class="ep-filler-card"><div class="ep-filler-en">{en}</div><div class="ep-filler-jp">{jp}</div></div>' for en,jp in FILLERS])
    st.markdown(f"""
<div class="ep-filler-wrap">
  <div style="font-size:11px;font-weight:700;color:#94a3b8;">
    💬 フィラーカード ─ 時間かせぎフレーズ集
  </div>
  <div class="ep-filler-grid">{fc}</div>
</div>""", unsafe_allow_html=True)

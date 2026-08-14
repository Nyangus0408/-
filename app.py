import streamlit as st
import google.generativeai as genai
import json
import base64
import io
import time
import re
from gtts import gTTS

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="🇺🇸 English Pitch & Talk",
    page_icon="🇺🇸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CSS --- マニュアルと同じデザイン言語
# ============================================================
st.markdown("""
<style>
/* ===== BASE ===== */
.stApp { background: #f0f2f5; }
.block-container { padding-top: 0 !important; max-width: 820px; }
header[data-testid="stHeader"] { background: transparent; }

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 0;
    border-bottom: 2px solid #e2e8f0;
    gap: 0;
    padding: 0 8px;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
.stTabs [data-baseweb="tab"] {
    font-weight: 700 !important;
    font-size: 12px !important;
    padding: 12px 14px !important;
    border-radius: 0 !important;
    color: #94a3b8 !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent, #1d4ed8) !important;
    border-bottom: 3px solid var(--accent, #1d4ed8) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 16px !important; }

/* ===== BUTTONS ===== */
.stButton > button {
    border-radius: 12px !important;
    font-weight: 700 !important;
    transition: all .2s !important;
    border: none !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(0,0,0,.15) !important;
}
.stButton > button[kind="primary"] {
    background: var(--accent, #1d4ed8) !important;
}

/* ===== INPUTS ===== */
.stTextArea textarea, .stTextInput input {
    border-radius: 12px !important;
    border: 2px solid #e5e7eb !important;
    font-family: inherit !important;
    transition: border-color .2s !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--accent, #1d4ed8) !important;
    box-shadow: none !important;
}

/* ===== SIDEBAR ===== */
[data-testid="stSidebar"] {
    background: #1e293b !important;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,.85) !important; }
[data-testid="stSidebar"] input {
    background: rgba(255,255,255,.1) !important;
    border: 1px solid rgba(255,255,255,.2) !important;
    color: white !important;
    border-radius: 8px !important;
}

/* ===== CARD ===== */
.ep-card {
    background: white;
    border-radius: 16px;
    padding: 20px;
    margin: 12px 0;
    box-shadow: 0 2px 12px rgba(0,0,0,.07);
    border: 1px solid #e8edf5;
}

/* ===== SCRIPT BOX ===== */
.ep-script {
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    border-left-width: 6px;
    border-left-style: solid;
}
.ep-script-text {
    font-size: 19px;
    font-weight: 700;
    color: #1e293b;
    line-height: 1.8;
    letter-spacing: .3px;
}
.ep-script-note { font-size: 11px; color: #94a3b8; margin-top: 8px; }

/* ===== SECTION LABEL ===== */
.ep-section-label {
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 800;
    display: inline-block;
    margin-bottom: 10px;
    color: white;
    letter-spacing: .5px;
}

/* ===== PHRASE ROW ===== */
.ep-phrase {
    display: flex;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid #f1f5f9;
    align-items: flex-start;
    font-size: 13px;
}
.ep-phrase:last-child { border-bottom: none; }
.ep-phrase-code {
    border-radius: 6px;
    padding: 3px 10px;
    font-weight: 700;
    font-size: 12px;
    white-space: nowrap;
    flex-shrink: 0;
    font-family: monospace;
}

/* ===== VOCAB ===== */
.ep-vocab {
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
    margin: 3px;
}

/* ===== Q&A ===== */
.ep-qa {
    background: #f8fafc;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 10px;
}

/* ===== TIP ===== */
.ep-tip {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-radius: 14px;
    padding: 16px 18px;
    margin: 14px 0;
    font-size: 13px;
    line-height: 1.7;
}

/* ===== SCORE ===== */
.ep-score-box {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}
.ep-score-num { font-size: 52px; font-weight: 900; line-height: 1; }
.ep-score-bar-wrap {
    background: #f1f5f9;
    border-radius: 8px;
    height: 12px;
    overflow: hidden;
    margin-bottom: 16px;
}
.ep-score-bar { height: 100%; border-radius: 8px; }

/* ===== WORD CHIPS ===== */
.ep-chip {
    border-radius: 6px;
    padding: 3px 9px;
    font-weight: 600;
    display: inline-block;
    margin: 2px;
    font-size: 13px;
}
.ep-chip-ok { background: #dcfce7; color: #16a34a; }
.ep-chip-ng { background: #fee2e2; color: #dc2626; text-decoration: line-through; }

/* ===== CHAT ===== */
.ep-chat-wrap {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 16px;
    min-height: 220px;
    max-height: 380px;
    overflow-y: auto;
    margin-bottom: 12px;
}
.ep-bubble-user {
    border-radius: 18px 18px 4px 18px;
    padding: 10px 14px;
    margin: 8px 0 8px 15%;
    font-size: 13px;
    line-height: 1.5;
    color: white;
}
.ep-bubble-ai {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 18px 18px 18px 4px;
    padding: 10px 14px;
    margin: 8px 15% 8px 0;
    font-size: 13px;
    line-height: 1.5;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.ep-bubble-label { font-size: 11px; color: #94a3b8; margin-bottom: 4px; }

/* ===== PARAPHRASE ===== */
.ep-para {
    display: flex;
    gap: 10px;
    align-items: center;
    padding: 8px 12px;
    background: #fff7ed;
    border-radius: 8px;
    margin-bottom: 6px;
    font-size: 13px;
    flex-wrap: wrap;
}
.ep-para-hard { text-decoration: line-through; color: #f87171; }
.ep-para-easy { font-weight: 800; color: #16a34a; }
.ep-para-note { color: #94a3b8; font-size: 11px; }

/* ===== FILLER ===== */
.ep-filler-wrap {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 16px;
    margin-top: 24px;
}
.ep-filler-grid { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.ep-filler-card {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 10px;
    padding: 8px 14px;
    cursor: default;
}
.ep-filler-en { font-weight: 700; color: #1d4ed8; font-size: 12px; }
.ep-filler-jp { color: #94a3b8; font-size: 11px; margin-top: 2px; }

/* ===== PLACEHOLDER ===== */
.ep-placeholder {
    text-align: center;
    padding: 56px 20px;
    color: #94a3b8;
}
.ep-placeholder-icon { font-size: 52px; margin-bottom: 14px; }
.ep-placeholder-title { font-size: 15px; font-weight: 700; margin-bottom: 6px; color: #64748b; }
.ep-placeholder-sub { font-size: 12px; }

/* ===== ALERT BOXES ===== */
.ep-alert {
    border-radius: 12px;
    padding: 12px 16px;
    text-align: center;
    font-weight: 700;
    font-size: 13px;
    margin-top: 14px;
}
.ep-alert-green { background: #f0fdf4; border: 1px solid #bbf7d0; color: #16a34a; }
.ep-alert-orange { background: #fff7ed; border: 1px solid #fed7aa; color: #ea580c; font-size: 12px; font-weight: 400; }

/* ===== EXAMPLE BUTTONS ===== */
.stButton > button[data-testid*="ex_"] {
    background: #f8fafc !important;
    color: #475569 !important;
    border: 1px solid #e2e8f0 !important;
    font-size: 11px !important;
    padding: 6px 10px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def ac(is_biz):
    """Return accent colors for current mode"""
    if is_biz:
        return {"main": "#1d4ed8", "light": "#eff6ff", "border": "#bfdbfe", "badge": "#dbeafe", "text": "#1d4ed8"}
    else:
        return {"main": "#0d9488", "light": "#f0fdfa", "border": "#99f6e4", "badge": "#ccfbf1", "text": "#0f766e"}


def generate_audio_html(text: str) -> str:
    """Generate TTS audio with speed control buttons"""
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        b64 = base64.b64encode(fp.read()).decode()
        return f"""
<audio id="epAudio" style="width:100%; border-radius:12px; margin-bottom:8px;">
  <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
</audio>
<div style="display:flex; gap:8px;">
  <button onclick="document.getElementById('epAudio').playbackRate=0.8;document.getElementById('epAudio').play();"
    style="flex:1;padding:10px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;cursor:pointer;font-weight:700;font-size:12px;transition:all .15s;"
    onmouseover="this.style.borderColor='#94a3b8'" onmouseout="this.style.borderColor='#e2e8f0'">
    🐢 0.8x<br><span style="font-size:10px;opacity:.7;">ゆっくり</span>
  </button>
  <button onclick="document.getElementById('epAudio').playbackRate=1.0;document.getElementById('epAudio').play();"
    style="flex:1;padding:10px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;cursor:pointer;font-weight:700;font-size:12px;transition:all .15s;"
    onmouseover="this.style.borderColor='#94a3b8'" onmouseout="this.style.borderColor='#e2e8f0'">
    ▶️ 1.0x<br><span style="font-size:10px;opacity:.7;">標準</span>
  </button>
  <button onclick="document.getElementById('epAudio').playbackRate=1.2;document.getElementById('epAudio').play();"
    style="flex:1;padding:10px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;cursor:pointer;font-weight:700;font-size:12px;transition:all .15s;"
    onmouseover="this.style.borderColor='#94a3b8'" onmouseout="this.style.borderColor='#e2e8f0'">
    ⚡ 1.2x<br><span style="font-size:10px;opacity:.7;">速め</span>
  </button>
</div>"""
    except Exception as e:
        return f'<div style="color:#ef4444;font-size:12px;">音声生成エラー: {e}</div>'


def compare_words(target: str, spoken: str):
    """Word-level comparison, returns (results, score)"""
    def normalize(text):
        return re.sub(r'[^\w\s]', '', text.lower()).split()
    tw = normalize(target)
    sw = set(normalize(spoken))
    results = [(w, w in sw) for w in tw]
    score = round(sum(1 for _, ok in results if ok) / max(len(results), 1) * 100)
    return results, score


def placeholder_html(tab_name: str) -> str:
    return f"""
<div class="ep-placeholder">
  <div class="ep-placeholder-icon">📝</div>
  <div class="ep-placeholder-title">「📝 入力」タブで日本語を生成してください</div>
  <div class="ep-placeholder-sub">英文が生成されると {tab_name} のコンテンツが表示されます</div>
</div>"""


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
<div style="padding:16px 0 8px;">
  <div style="font-size:20px; font-weight:900; color:white; margin-bottom:4px;">🇺🇸 English Pitch & Talk</div>
  <div style="font-size:11px; color:rgba(255,255,255,.5);">AI英会話トレーナー</div>
</div>
<hr style="border-color:rgba(255,255,255,.1); margin:8px 0 16px;">
""", unsafe_allow_html=True)

    api_key = st.text_input(
        "🔑 Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Google AI Studio（aistudio.google.com）から無料で取得できます"
    )
    if api_key:
        st.markdown('<div style="color:#4ade80;font-size:12px;font-weight:700;margin-top:4px;">✅ APIキー設定済み</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#fbbf24;font-size:12px;font-weight:700;margin-top:4px;">⚠️ APIキーを入力してください</div>', unsafe_allow_html=True)

    st.markdown("""
<hr style="border-color:rgba(255,255,255,.1); margin:16px 0;">
<div style="font-size:12px; font-weight:700; color:rgba(255,255,255,.6); margin-bottom:10px;">📖 かんたん使い方</div>
<div style="font-size:12px; color:rgba(255,255,255,.75); line-height:2;">
① APIキーを入力<br>
② モードを選択<br>
③ 日本語テキストを入力<br>
④ 「生成する」ボタン<br>
⑤ 各タブで学習！
</div>
<hr style="border-color:rgba(255,255,255,.1); margin:16px 0;">
<div style="font-size:10px; color:rgba(255,255,255,.35); line-height:1.8;">
🔧 使用モデル: gemini-2.0-flash<br>
🔊 TTS: gTTS（Google）<br>
🎤 STT: Gemini Audio API
</div>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================
if "script_data" not in st.session_state:
    st.session_state.script_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "example_input" not in st.session_state:
    st.session_state.example_input = ""


# ============================================================
# API SETUP
# ============================================================
model = None
audio_model = None
if api_key:
    genai.configure(api_key=api_key)
    # ✅ FIX: gemini-1.5-flash → gemini-2.0-flash
    model = genai.GenerativeModel(
        'gemini-2.0-flash',
        generation_config={"response_mime_type": "application/json"}
    )
    audio_model = genai.GenerativeModel('gemini-2.0-flash')


# ============================================================
# HEADER
# ============================================================
mode = st.radio(
    "モード選択",
    ["🏢 展示会・ビジネス", "☕ 日常会話・基礎"],
    horizontal=True,
    label_visibility="collapsed"
)
is_biz = "展示会" in mode
C = ac(is_biz)

# Dynamic accent CSS
st.markdown(f"""<style>:root {{ --accent: {C['main']}; }}</style>""", unsafe_allow_html=True)

# Header banner
st.markdown(f"""
<div style="background:linear-gradient(135deg,{C['main']},{C['main']}cc);color:white;padding:20px 24px 18px;border-radius:16px;margin-bottom:4px;box-shadow:0 4px 20px rgba(0,0,0,.15);">
  <div style="font-size:22px;font-weight:900;letter-spacing:-.5px;margin-bottom:4px;">🇺🇸 English Pitch & Talk</div>
  <div style="font-size:11px;opacity:.75;">{"展示会・商談英語をマスター" if is_biz else "日常英会話を基礎から学ぼう"}</div>
  <div style="display:inline-block;background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);border-radius:20px;padding:4px 14px;font-size:11px;font-weight:700;margin-top:10px;">
    {"🏢 展示会・ビジネスモード" if is_biz else "☕ 日常会話・基礎モード"}
  </div>
</div>
""", unsafe_allow_html=True)

sys_prompt = (
    "あなたはビジネス英語の専門家です。中学レベルのSVO文法を使い、展示会で通じるシンプルな英文を作成してください。1文は必ず12単語以内。"
    if is_biz else
    "あなたは日常英会話のコーチです。旅行・カフェ・自己紹介など日常で使えるシンプルで温かみのある英文を作成してください。1文は必ず12単語以内。"
)

# Example inputs
EXAMPLES = {
    True: [
        "このセンサーは従来品の半分の電力で動作します",
        "弊社の新製品は防水・防塵性能を備えています",
        "納期は2週間です。大量注文も対応可能です",
        "このシステムは導入コストを30%削減できます",
    ],
    False: [
        "コーヒーを1杯ください",
        "駅への行き方を教えてください",
        "田中と申します。よろしくお願いします",
        "おすすめのランチは何ですか？",
    ]
}

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📝 入力", "📖 スクリプト", "🔊 音読", "🎤 発音", "✏️ 穴埋め", "🎭 会話"
])
data = st.session_state.script_data


# ============================================================
# TAB 1: INPUT
# ============================================================
with tab1:
    # Example buttons
    st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:14px;padding:14px;margin-bottom:14px;">
  <div style="font-size:11px;color:#64748b;font-weight:700;margin-bottom:10px;">💡 クイックスタート例文（タップで入力）</div>
""", unsafe_allow_html=True)

    ex_cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES[is_biz]):
        with ex_cols[i % 2]:
            if st.button(ex[:18] + "…", key=f"ex_{i}", use_container_width=True):
                st.session_state.example_input = ex

    st.markdown("</div>", unsafe_allow_html=True)

    user_input = st.text_area(
        "英語にしたい日本語を入力",
        value=st.session_state.example_input,
        placeholder="例: 弊社のセンサーは従来品の半分の電力で動作します。",
        height=110,
        key="main_input"
    )

    st.markdown('<div style="font-size:10px;color:#94a3b8;margin-top:2px;margin-bottom:12px;">💡 短い文（1〜2文）ほど高品質なコンテンツが生成されます</div>', unsafe_allow_html=True)

    generate_btn = st.button(
        "✨ 英文＆学習コンテンツを生成する",
        type="primary",
        use_container_width=True,
        key="gen_btn"
    )

    if generate_btn:
        if not api_key:
            st.error("⬅️ 左のサイドバーに Gemini API キーを入力してください。")
        elif not user_input.strip():
            st.warning("日本語の文章を入力してください。")
        else:
            with st.spinner("AIが学習コンテンツを作成中... ✨"):
                prompt = f"""
以下のルールに従い、純粋なJSONのみで出力してください（\`\`\`不要）。

[入力文]: {user_input}
[場面]: {"展示会・ビジネス（製品説明・技術紹介・商談）" if is_biz else "日常会話（カフェ・買い物・道案内・自己紹介）"}

[絶対ルール]
- 1文最大12単語
- TOEIC 400点レベルの語彙・文法のみ
- 関係代名詞・複文禁止。SVO構造優先

[出力形式]
{{
  "english": "完成英文（複数文はスペースで区切る）",
  "chunked": "スラッシュ区切り英文（Our product / is light. It saves / energy.）",
  "grammar": "文法・フレーズ解説（日本語、2〜3行）",
  "vocab": {{"単語": "意味（日本語）"}},
  "blank_q": "穴埋め問題文（___で空欄）",
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
                try:
                    response = model.generate_content([sys_prompt, prompt])
                    raw = response.text
                    # Robust JSON extraction
                    json_match = re.search(r'\{[\s\S]*\}', raw)
                    if json_match:
                        st.session_state.script_data = json.loads(json_match.group())
                        st.session_state.chat_history = []
                        data = st.session_state.script_data
                        st.success("✅ 生成完了！上の「📖 スクリプト」タブに進んでください。")
                        st.balloons()
                    else:
                        st.error("JSONの解析に失敗しました。もう一度お試しください。")
                except Exception as e:
                    err = str(e)
                    if "NotFound" in err or "404" in err:
                        st.error("❌ モデルエラー: gemini-2.0-flash が見つかりません。APIキーとネットワーク接続を確認してください。")
                    elif "PERMISSION_DENIED" in err or "403" in err:
                        st.error("❌ APIキーのエラー: キーが正しいか確認してください。Google AI Studioで再発行をお試しください。")
                    else:
                        st.error(f"❌ エラーが発生しました: {err}")


# ============================================================
# TAB 2: SCRIPT
# ============================================================
with tab2:
    if not data:
        st.markdown(placeholder_html("📖 スクリプト"), unsafe_allow_html=True)
    else:
        # Main script with chunks
        st.markdown(f"""
<div class="ep-script" style="background:{C['light']};border:2px solid {C['border']};border-left-color:{C['main']};">
  <div class="ep-section-label" style="background:{C['main']};">📖 英文スクリプト（チャンク読み）</div>
  <div class="ep-script-text">{data.get('chunked', data.get('english', ''))}</div>
  <div class="ep-script-note">/ はチャンク（意味の塊）の区切りです。左から順番に理解しましょう。</div>
</div>
""", unsafe_allow_html=True)

        # Grammar notes
        st.markdown(f"""
<div class="ep-card">
  <div class="ep-section-label" style="background:{C['main']};">📚 文法・フレーズ解説</div>
  <div style="font-size:13px;color:#475569;line-height:1.8;">{data.get('grammar','')}</div>
</div>
""", unsafe_allow_html=True)

        # Vocabulary
        vocab = data.get('vocab', {})
        if vocab:
            vocab_html = "".join([
                f'<span class="ep-vocab" style="background:{C["light"]};color:{C["main"]};"><strong>{k}</strong>: {v}</span>'
                for k, v in vocab.items()
            ])
            st.markdown(f"""
<div class="ep-card">
  <div class="ep-section-label" style="background:{C['main']};">📝 重要語彙</div>
  <div>{vocab_html}</div>
</div>
""", unsafe_allow_html=True)

        # Q&A pairs (business mode only)
        if is_biz and data.get('qa_pairs'):
            qa_html = ""
            for qa in data['qa_pairs']:
                qa_html += f"""
<div class="ep-qa">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div style="font-size:13px;font-weight:600;color:#1e293b;margin-bottom:3px;">{qa.get('question','')}</div>
      <div style="font-size:11px;color:#94a3b8;">{qa.get('question_jp','')}</div>
    </div>
  </div>
  <div style="font-size:11px;color:{C['main']};font-weight:600;margin-top:6px;">💡 {qa.get('hint','')}</div>
</div>"""
            st.markdown(f"""
<div class="ep-card">
  <div class="ep-section-label" style="background:{C['main']};">🙋 想定Q&A（展示会バイヤーからの質問）</div>
  {qa_html}
</div>
""", unsafe_allow_html=True)

        st.markdown(f"""
<div class="ep-tip">
  💡 <strong>チャンク読みのコツ：</strong>スラッシュ（/）の前で少し間を取り、<strong>左から順番に</strong>意味をつかみながら読みましょう。日本語のように後ろから返り読みするのはNGです！
</div>
""", unsafe_allow_html=True)


# ============================================================
# TAB 3: AUDIO
# ============================================================
with tab3:
    if not data:
        st.markdown(placeholder_html("🔊 音読"), unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:16px;padding:20px;margin-bottom:16px;">
  <div class="ep-section-label" style="background:{C['main']};">🎵 シャドーイング・音読プレイヤー</div>
  <div style="background:white;border:1px solid {C['border']};border-radius:12px;padding:14px;margin-bottom:16px;">
    <div style="font-size:16px;font-weight:600;color:#1e293b;line-height:1.8;">{data.get('chunked','')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

        audio_html = generate_audio_html(data.get('english', ''))
        st.components.v1.html(audio_html, height=130)

        st.markdown("""
<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:16px;padding:18px;margin-top:16px;">
  <div style="font-size:12px;font-weight:800;color:#92400e;margin-bottom:12px;">💡 安河内式 音読 3ステップ</div>
  <div style="display:flex;flex-direction:column;gap:10px;">
    <div style="display:flex;gap:12px;align-items:flex-start;font-size:12px;color:#78350f;line-height:1.6;">
      <span style="background:#d97706;color:white;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:11px;flex-shrink:0;margin-top:1px;">1</span>
      <span><strong>0.8x</strong> → 音声を聴きながら口をパクパクさせる（オーバーラッピング）</span>
    </div>
    <div style="display:flex;gap:12px;align-items:flex-start;font-size:12px;color:#78350f;line-height:1.6;">
      <span style="background:#d97706;color:white;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:11px;flex-shrink:0;margin-top:1px;">2</span>
      <span><strong>1.0x</strong> → 声に出して一緒に読む（シャドーイング）</span>
    </div>
    <div style="display:flex;gap:12px;align-items:flex-start;font-size:12px;color:#78350f;line-height:1.6;">
      <span style="background:#d97706;color:white;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:11px;flex-shrink:0;margin-top:1px;">3</span>
      <span><strong>1.2x</strong> → スクリプトを見ずに音声を追いかける（スピードトレーニング）</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# TAB 4: PRONUNCIATION
# ============================================================
with tab4:
    if not data:
        st.markdown(placeholder_html("🎤 発音"), unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:16px;padding:20px;margin-bottom:16px;">
  <div class="ep-section-label" style="background:{C['main']};">🎤 発音チェック</div>
  <div style="font-size:15px;font-weight:600;color:#1e293b;line-height:1.7;margin-bottom:16px;">{data.get('english','')}</div>
</div>
""", unsafe_allow_html=True)

        # Reference audio
        st.markdown(f'<div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:8px;">🔊 手本の発音を聴く</div>', unsafe_allow_html=True)
        ref_html = generate_audio_html(data.get('english', ''))
        st.components.v1.html(ref_html, height=130)

        st.markdown("<hr style='margin:16px 0;'>", unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:12px;font-weight:700;color:#334155;margin-bottom:8px;">🎤 マイクで音読する（録音後に自動採点）</div>', unsafe_allow_html=True)

        # iPhone-compatible mic input
        audio_value = st.audio_input("マイクを押して録音してください")

        if audio_value is not None:
            with st.spinner("AIが発音を分析中... 🎯"):
                analysis_prompt = f"""
この音声を英語として文字起こしし、元の文「{data.get('english', '')}」と比較して採点してください。

以下のJSONのみで回答（\`\`\`不要）:
{{
  "score": 85,
  "transcript": "認識されたテキスト",
  "good_words": ["正しく言えた単語"],
  "bad_words": ["うまく言えなかった単語"],
  "feedback": "日本語でのフィードバック（1文）"
}}
"""
                audio_file = {"mime_type": "audio/wav", "data": audio_value.getvalue()}
                try:
                    result = audio_model.generate_content([analysis_prompt, audio_file])
                    json_match = re.search(r'\{[\s\S]*\}', result.text)
                    if json_match:
                        rd = json.loads(json_match.group())
                        score = rd.get('score', 0)
                        transcript = rd.get('transcript', '')
                        good_words = rd.get('good_words', [])
                        bad_words = rd.get('bad_words', [])
                        feedback = rd.get('feedback', '')

                        score_color = "#22c55e" if score >= 80 else "#eab308" if score >= 60 else "#ef4444"

                        # Score display
                        st.markdown(f"""
<div class="ep-card" style="margin-top:16px;">
  <div class="ep-score-box">
    <span style="font-size:13px;font-weight:800;color:#334155;">発音マッチ度</span>
    <span class="ep-score-num" style="color:{score_color};">{score}%</span>
  </div>
  <div class="ep-score-bar-wrap">
    <div class="ep-score-bar" style="width:{score}%;background:{score_color};"></div>
  </div>
  <div style="margin-bottom:12px;">
    {"".join([f'<span class="ep-chip ep-chip-ok">{w}</span>' for w in good_words])}
    {"".join([f'<span class="ep-chip ep-chip-ng">{w}</span>' for w in bad_words])}
  </div>
  <div style="font-size:11px;color:#94a3b8;">認識テキスト: "{transcript}"</div>
  {f'<div style="font-size:12px;color:#475569;margin-top:8px;padding:8px;background:#f8fafc;border-radius:8px;">💬 {feedback}</div>' if feedback else ''}
</div>
""", unsafe_allow_html=True)

                        if score >= 80:
                            st.markdown('<div class="ep-alert ep-alert-green">🎉 素晴らしい！次のステップへ進みましょう！</div>', unsafe_allow_html=True)
                        elif score < 60:
                            st.markdown('<div class="ep-alert ep-alert-orange">💡 0.8xでゆっくり練習し、スラッシュ単位で区切って確認しましょう</div>', unsafe_allow_html=True)
                    else:
                        st.info(result.text)
                except Exception as e:
                    st.error(f"分析エラー: {str(e)}")


# ============================================================
# TAB 5: PRACTICE
# ============================================================
with tab5:
    if not data:
        st.markdown(placeholder_html("✏️ 穴埋め練習"), unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div style="background:{C['light']};border:1px solid {C['border']};border-radius:16px;padding:20px;margin-bottom:16px;">
  <div class="ep-section-label" style="background:{C['main']};">✏️ 瞬発力トレーニング</div>
  <div style="font-size:11px;color:#94a3b8;margin-bottom:16px;">3秒以内に空欄に入る英単語を思い出してください</div>
  <div style="background:white;border:2px dashed #cbd5e1;border-radius:14px;padding:20px;text-align:center;margin-bottom:16px;">
    <div style="font-size:19px;font-weight:700;color:#1e293b;">{data.get('blank_q','')}</div>
    <div style="font-size:12px;color:#94a3b8;margin-top:8px;">💡 ヒント: {data.get('hint','')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

        # Countdown
        if st.button("⏱ 3秒カウントダウンスタート", use_container_width=True, key="timer_start"):
            ph = st.empty()
            for i in range(3, 0, -1):
                ph.markdown(
                    f'<div style="text-align:center;font-size:84px;font-weight:900;color:{C["main"]};padding:8px 0;">{i}</div>',
                    unsafe_allow_html=True
                )
                time.sleep(1)
            ph.markdown(
                '<div style="text-align:center;font-size:26px;font-weight:900;color:#f97316;padding:8px 0;">答えて！</div>',
                unsafe_allow_html=True
            )

        user_ans = st.text_input("答えを入力してください", placeholder="英単語を入力...", key="practice_answer")

        col_check, col_audio = st.columns(2)
        with col_check:
            check_btn = st.button("✅ 答え合わせ", use_container_width=True, key="check_answer", type="primary")
        with col_audio:
            play_btn = st.button("🔊 正解の文を聴く", use_container_width=True, key="play_answer")

        if check_btn and user_ans:
            correct = data.get('blank_a', '')
            is_correct = user_ans.lower().strip() == correct.lower().strip()
            if is_correct:
                st.markdown(f"""
<div style="background:white;border:1px solid #e2e8f0;border-radius:16px;padding:20px;text-align:center;margin-top:12px;">
  <div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">正解:</div>
  <div style="font-size:28px;font-weight:900;color:#22c55e;margin-bottom:10px;">{correct}</div>
  <div class="ep-alert ep-alert-green">🎉 正解！素晴らしい！</div>
</div>
""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div style="background:white;border:1px solid #e2e8f0;border-radius:16px;padding:20px;text-align:center;margin-top:12px;">
  <div style="font-size:11px;color:#94a3b8;margin-bottom:4px;">正解:</div>
  <div style="font-size:28px;font-weight:900;color:#22c55e;margin-bottom:10px;">{correct}</div>
  <div style="color:#f97316;font-size:13px;">あなたの回答: "<strong>{user_ans}</strong>" → もう一度チャレンジ！</div>
</div>
""", unsafe_allow_html=True)

        if play_btn:
            eng = data.get('english', '')
            if eng:
                audio_html_play = generate_audio_html(eng)
                st.components.v1.html(audio_html_play, height=130)

        # Paraphrase rescue
        if data.get('paraphrases'):
            with st.expander("🆘 言い換えレスキュー（単語が出ない時）"):
                para_html = ""
                for p in data['paraphrases']:
                    para_html += f"""
<div class="ep-para">
  <span class="ep-para-hard">{p.get('difficult','')}</span>
  <span style="color:#94a3b8;">→</span>
  <span class="ep-para-easy">{p.get('simple','')}</span>
  <span class="ep-para-note">（{p.get('note','')}）</span>
</div>"""
                st.markdown(para_html, unsafe_allow_html=True)


# ============================================================
# TAB 6: ROLEPLAY
# ============================================================
with tab6:
    if not data:
        st.markdown(placeholder_html("🎭 ロールプレイ"), unsafe_allow_html=True)
    else:
        # Init chat
        if not st.session_state.chat_history:
            opener = (
                f"Hello! I'm visiting your booth today. Tell me about your product."
                if is_biz else
                "Hi there! Nice to meet you. How are you doing today?"
            )
            st.session_state.chat_history = [{"role": "assistant", "content": opener}]

        # Chat bubbles
        chat_html = '<div class="ep-chat-wrap">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f'<div class="ep-bubble-user" style="background:{C["main"]};">{msg["content"]}</div>'
            else:
                label = "🧳 バイヤー" if is_biz else "💬 ネイティブ"
                chat_html += f'<div class="ep-bubble-ai"><div class="ep-bubble-label">{label}</div>{msg["content"]}</div>'
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        # Paraphrase rescue
        if data.get('paraphrases'):
            with st.expander("🆘 言い換えレスキュー"):
                for p in data['paraphrases']:
                    st.markdown(f"""
<div class="ep-para">
  <span class="ep-para-hard">{p.get('difficult','')}</span>
  <span>→</span>
  <span class="ep-para-easy">{p.get('simple','')}</span>
</div>""", unsafe_allow_html=True)

        # Input
        user_msg = st.chat_input("英語で返事を入力してください...")
        if user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with st.spinner("AIが返答中..."):
                role_desc = "展示会のバイヤー（外国のお客さん）" if is_biz else "フレンドリーなネイティブスピーカー"
                chat_prompt = f"""
あなたは{role_desc}です。
ユーザーの英語: {user_msg}
製品/話題の文脈: {data.get('english','')}

ユーザーの英語に対し、自然で短い英語（1〜2文）で返答してください。
ビジネスモードなら製品について質問を続け、日常モードなら会話を発展させてください。
"""
                try:
                    res = audio_model.generate_content(chat_prompt)
                    st.session_state.chat_history.append({"role": "assistant", "content": res.text.strip()})
                    st.rerun()
                except Exception as e:
                    st.error(f"返答エラー: {str(e)}")

        col_reset, _ = st.columns([1, 2])
        with col_reset:
            if st.button("🔄 会話をリセット", key="reset_chat"):
                st.session_state.chat_history = []
                st.rerun()


# ============================================================
# FILLER CARDS (Business mode + data exists)
# ============================================================
if is_biz and data:
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
    filler_cards = "".join([
        f'<div class="ep-filler-card"><div class="ep-filler-en">{en}</div><div class="ep-filler-jp">{jp}</div></div>'
        for en, jp in FILLERS
    ])
    st.markdown(f"""
<div class="ep-filler-wrap">
  <div style="font-size:11px;font-weight:700;color:#94a3b8;">💬 フィラーカード（時間かせぎフレーズ） ― 覚えてすぐに使おう！</div>
  <div class="ep-filler-grid">{filler_cards}</div>
</div>
""", unsafe_allow_html=True)

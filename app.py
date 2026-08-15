import streamlit as st
import google.generativeai as genai
import json
import base64
import io
import time
import re
import os
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
# CSS
# ============================================================
st.markdown("""
<style>
/* ===== BASE ===== */
.stApp { background: #f0f2f5; }
.block-container { padding-top: 2rem !important; max-width: 820px; }
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
[data-testid="stSidebar"] { background: #1e293b !important; }
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
.ep-score-box { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.ep-score-num { font-size: 52px; font-weight: 900; line-height: 1; }
.ep-score-bar-wrap { background: #f1f5f9; border-radius: 8px; height: 12px; overflow: hidden; margin-bottom: 16px; }
.ep-score-bar { height: 100%; border-radius: 8px; }

/* ===== WORD CHIPS ===== */
.ep-chip { border-radius: 6px; padding: 3px 9px; font-weight: 600; display: inline-block; margin: 2px; font-size: 13px; }
.ep-chip-ok { background: #dcfce7; color: #16a34a; }
.ep-chip-ng { background: #fee2e2; color: #dc2626; text-decoration: line-through; }

/* ===== CHAT ===== */
.ep-chat-wrap { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; padding: 16px; min-height: 220px; max-height: 380px; overflow-y: auto; margin-bottom: 12px; }
.ep-bubble-user { border-radius: 18px 18px 4px 18px; padding: 10px 14px; margin: 8px 0 8px 15%; font-size: 13px; line-height: 1.5; color: white; }
.ep-bubble-ai { background: white; border: 1px solid #e2e8f0; border-radius: 18px 18px 18px 4px; padding: 10px 14px; margin: 8px 15% 8px 0; font-size: 13px; line-height: 1.5; box-shadow: 0 1px 4px rgba(0,0,0,.05); }
.ep-bubble-label { font-size: 11px; color: #94a3b8; margin-bottom: 4px; }

/* ===== PARAPHRASE ===== */
.ep-para { display: flex; gap: 10px; align-items: center; padding: 8px 12px; background: #fff7ed; border-radius: 8px; margin-bottom: 6px; font-size: 13px; flex-wrap: wrap; }
.ep-para-hard { text-decoration: line-through; color: #f87171; }
.ep-para-easy { font-weight: 800; color: #16a34a; }
.ep-para-note { color: #94a3b8; font-size: 11px; }

/* ===== FILLER ===== */
.ep-filler-wrap { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 16px; margin-top: 24px; }
.ep-filler-grid { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.ep-filler-card { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 10px; padding: 8px 14px; cursor: default; }
.ep-filler-en { font-weight: 700; color: #1d4ed8; font-size: 12px; }
.ep-filler-jp { color: #94a3b8; font-size: 11px; margin-top: 2px; }

/* ===== PLACEHOLDER ===== */
.ep-placeholder { text-align: center; padding: 56px 20px; color: #94a3b8; }
.ep-placeholder-icon { font-size: 52px; margin-bottom: 14px; }
.ep-placeholder-title { font-size: 15px; font-weight: 700; margin-bottom: 6px; color: #64748b; }
.ep-placeholder-sub { font-size: 12px; }

/* ===== ALERT BOXES ===== */
.ep-alert { border-radius: 12px; padding: 12px 16px; text-align: center; font-weight: 700; font-size: 13px; margin-top: 14px; }
.ep-alert-green { background: #f0fdf4; border: 1px solid #bbf7d0; color: #16a34a; }
.ep-alert-orange { background: #fff7ed; border: 1px solid #fed7aa; color: #ea580c; font-size: 12px; font-weight: 400; }

/* ===== EXAMPLE BUTTONS ===== */
.stButton > button[data-testid*="ex_"] { background: #f8fafc !important; color: #475569 !important; border: 1px solid #e2e8f0 !important; font-size: 11px !important; padding: 6px 10px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def ac(is_biz):
    if is_biz:
        return {"main": "#1d4ed8", "light": "#eff6ff", "border": "#bfdbfe", "badge": "#dbeafe", "text": "#1d4ed8"}
    else:
        return {"main": "#0d9488", "light": "#f0fdfa", "border": "#99f6e4", "badge": "#ccfbf1", "text": "#0f766e"}

def generate_audio_html(text: str) -> str:
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
  <button onclick="document.getElementById('epAudio').playbackRate=0.8;document.getElementById('epAudio').play();" style="flex:1;padding:10px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;cursor:pointer;font-weight:700;font-size:12px;transition:all .15s;">🐢 0.8x</button>
  <button onclick="document.getElementById('epAudio').playbackRate=1.0;document.getElementById('epAudio').play();" style="flex:1;padding:10px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;cursor:pointer;font-weight:700;font-size:12px;transition:all .15s;">▶️ 1.0x</button>
  <button onclick="document.getElementById('epAudio').playbackRate=1.2;document.getElementById('epAudio').play();" style="flex:1;padding:10px 0;border:2px solid #e2e8f0;border-radius:10px;background:white;cursor:pointer;font-weight:700;font-size:12px;transition:all .15s;">⚡ 1.2x</button>
</div>"""
    except Exception as e:
        return f'<div style="color:#ef4444;font-size:12px;">音声生成エラー: {e}</div>'

def placeholder_html(tab_name: str) -> str:
    return f"""
<div class="ep-placeholder">
  <div class="ep-placeholder-icon">📝</div>
  <div class="ep-placeholder-title">「📝 入力」タブで日本語を生成してください</div>
  <div class="ep-placeholder-sub">英文が生成されると {tab_name} のコンテンツが表示されます</div>
</div>"""


# ============================================================
# API KEY & SECRETS SETUP
# ============================================================
# ★修正: Streamlit SecretsからAPIキーを自動取得するロジック
api_key = ""
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
elif "API_KEY" in st.secrets:
    api_key = st.secrets["API_KEY"]
elif "GEMINI_API_KEY" in os.environ:
    api_key = os.environ["GEMINI_API_KEY"]

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

    # APIキーが裏側で取得できていない場合のみ、入力欄を表示する
    if not api_key:
        api_key_input = st.text_input("🔑 Gemini API Key", type="password", placeholder="AIza または AQ.Ab...")
        if api_key_input:
            api_key = api_key_input
            st.markdown('<div style="color:#4ade80;font-size:12px;font-weight:700;margin-top:4px;">✅ APIキー手動設定済み</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#fbbf24;font-size:12px;font-weight:700;margin-top:4px;">⚠️ APIキーが見つかりません</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#4ade80;font-size:12px;font-weight:700;margin-top:4px;">✅ APIキー自動連携済み (Secrets)</div>', unsafe_allow_html=True)

    st.markdown("""
<hr style="border-color:rgba(255,255,255,.1); margin:16px 0;">
<div style="font-size:12px; font-weight:700; color:rgba(255,255,255,.6); margin-bottom:10px;">📖 かんたん使い方</div>
<div style="font-size:12px; color:rgba(255,255,255,.75); line-height:2;">
① モードを選択<br>
② 日本語テキストを入力<br>
③ 「生成する」ボタン<br>
④ 各タブで学習！
</div>
<hr style="border-color:rgba(255,255,255,.1); margin:16px 0;">
<div style="font-size:10px; color:rgba(255,255,255,.35); line-height:1.8;">
🔧 使用モデル: gemini-1.5-flash<br>
🔊 TTS: gTTS（Google）
</div>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE & API INIT
# ============================================================
if "script_data" not in st.session_state:
    st.session_state.script_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "main_input" not in st.session_state:
    st.session_state.main_input = ""

model = None
audio_model = None
if api_key:
    genai.configure(api_key=api_key)
    # ★修正: 安定板の gemini-1.5-flash に固定
   model = genai.GenerativeModel('gemini-1.5-flash-latest', generation_config={"response_mime_type": "application/json"})
   audio_model = genai.GenerativeModel('gemini-1.5-flash-latest')


# ============================================================
# HEADER
# ============================================================
mode = st.radio("モード選択", ["🏢 展示会・ビジネス", "☕ 日常会話・基礎"], horizontal=True, label_visibility="collapsed")
is_biz = "展示会" in mode
C = ac(is_biz)

st.markdown(f"""<style>:root {{ --accent: {C['main']}; }}</style>""", unsafe_allow_html=True)

st.markdown(f"""
<div style="background:linear-gradient(135deg,{C['main']},{C['main']}cc);color:white;padding:20px 24px 18px;border-radius:16px;margin-bottom:4px;box-shadow:0 4px 20px rgba(0,0,0,.15);">
  <div style="font-size:22px;font-weight:900;letter-spacing:-.5px;margin-bottom:4px;">🇺🇸 English Pitch & Talk</div>
  <div style="font-size:11px;opacity:.75;">{"展示会・商談英語をマスター" if is_biz else "日常英会話を基礎から学ぼう"}</div>
</div>
""", unsafe_allow_html=True)

sys_prompt = "あなたはビジネス英語の専門家です。中学レベルのSVO文法を使い、展示会で通じるシンプルな英文を作成してください。1文は必ず12単語以内。" if is_biz else "あなたは日常英会話のコーチです。旅行・カフェ・自己紹介など日常で使えるシンプルで温かみのある英文を作成してください。1文は必ず12単語以内。"

EXAMPLES = {
    True: ["このセンサーは従来品の半分の電力で動作します", "弊社の新製品は防水・防塵性能を備えています", "納期は2週間です。大量注文も対応可能です", "このシステムは導入コストを30%削減できます"],
    False: ["コーヒーを1杯ください", "駅への行き方を教えてください", "田中と申します。よろしくお願いします", "おすすめのランチは何ですか？"]
}


# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 入力", "📖 スクリプト", "🔊 音読", "🎤 発音", "✏️ 穴埋め", "🎭 会話"])
data = st.session_state.script_data


# ============================================================
# TAB 1: INPUT
# ============================================================
with tab1:
    st.markdown(f"""<div style="background:{C['light']};border:1px solid {C['border']};border-radius:14px;padding:14px;margin-bottom:14px;"><div style="font-size:11px;color:#64748b;font-weight:700;margin-bottom:10px;">💡 クイックスタート例文（タップで入力）</div>""", unsafe_allow_html=True)
    ex_cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES[is_biz]):
        with ex_cols[i % 2]:
            if st.button(ex[:18] + "…", key=f"ex_{i}", use_container_width=True):
                st.session_state.main_input = ex
    st.markdown("</div>", unsafe_allow_html=True)

    user_input = st.text_area("英語にしたい日本語を入力", key="main_input", placeholder="例: 弊社のセンサーは従来品の半分の電力で動作します。", height=110)

    if st.button("✨ 英文＆学習コンテンツを生成する", type="primary", use_container_width=True, key="gen_btn"):
        if not api_key:
            st.error("❌ APIキーが設定されていません。")
        elif not user_input.strip():
            st.warning("日本語の文章を入力してください。")
        else:
            with st.spinner("AIが学習コンテンツを作成中... ✨"):
                prompt = f"""
以下のルールに従い、純粋なJSONのみで出力してください（```不要）。
[入力文]: {user_input}
[場面]: {"展示会・ビジネス（製品説明・技術紹介・商談）" if is_biz else "日常会話（カフェ・買い物・道案内・自己紹介）"}
[絶対ルール] 1文最大12単語。SVO構造優先。
[出力形式]
{{
  "english": "完成英文",
  "chunked": "スラッシュ区切り英文",
  "grammar": "文法解説",
  "vocab": {{"単語": "意味"}},
  "blank_q": "穴埋め問題文（___で空欄）",
  "blank_a": "正解",
  "hint": "ヒント",
  "qa_pairs": [{{"question": "英語質問", "question_jp": "日本語訳", "hint": "回答ヒント"}}],
  "paraphrases": [{{"difficult": "難しい表現", "simple": "簡単な言い換え", "note": "メモ"}}]
}}
"""
                try:
                    response = model.generate_content([sys_prompt, prompt])
                    json_match = re.search(r'\{[\s\S]*\}', response.text)
                    if json_match:
                        st.session_state.script_data = json.loads(json_match.group())
                        st.session_state.chat_history = []
                        st.success("✅ 生成完了！上の「📖 スクリプト」タブに進んでください。")
                        st.rerun()
                    else:
                        st.error("データの解析に失敗しました。もう一度お試しください。")
                except Exception as e:
                    st.error(f"❌ 通信エラー: {str(e)}")


# ============================================================
# TAB 2: SCRIPT
# ============================================================
with tab2:
    if not data:
        st.markdown(placeholder_html("📖 スクリプト"), unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ep-script" style="background:{C["light"]};border:2px solid {C["border"]};border-left-color:{C["main"]};"><div class="ep-section-label" style="background:{C["main"]};">📖 英文スクリプト</div><div class="ep-script-text">{data.get("chunked", data.get("english", ""))}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ep-card"><div class="ep-section-label" style="background:{C["main"]};">📚 文法解説</div><div style="font-size:13px;color:#475569;">{data.get("grammar","")}</div></div>', unsafe_allow_html=True)
        if data.get('vocab'):
            v_html = "".join([f'<span class="ep-vocab" style="background:{C["light"]};color:{C["main"]};"><strong>{k}</strong>: {v}</span>' for k, v in data['vocab'].items()])
            st.markdown(f'<div class="ep-card"><div class="ep-section-label" style="background:{C["main"]};">📝 重要語彙</div><div>{v_html}</div></div>', unsafe_allow_html=True)


# ============================================================
# TAB 3: AUDIO
# ============================================================
with tab3:
    if not data:
        st.markdown(placeholder_html("🔊 音読"), unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background:{C["light"]};border:1px solid {C["border"]};border-radius:16px;padding:20px;margin-bottom:16px;"><div class="ep-section-label" style="background:{C["main"]};">🎵 音読プレイヤー</div><div style="font-size:16px;font-weight:600;background:white;padding:14px;border-radius:12px;">{data.get("chunked","")}</div></div>', unsafe_allow_html=True)
        st.components.v1.html(generate_audio_html(data.get('english', '')), height=130)


# ============================================================
# TAB 4: PRONUNCIATION
# ============================================================
with tab4:
    if not data:
        st.markdown(placeholder_html("🎤 発音"), unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background:{C["light"]};border:1px solid {C["border"]};border-radius:16px;padding:20px;"><div class="ep-section-label" style="background:{C["main"]};">🎤 発音チェック</div><div style="font-size:15px;font-weight:600;">{data.get("english","")}</div></div>', unsafe_allow_html=True)
        audio_value = st.audio_input("マイクを押して録音")
        if audio_value is not None:
            with st.spinner("発音を分析中..."):
                p = f"""この音声を文字起こしし、「{data.get('english', '')}」と比較して採点。以下のJSONのみ出力(```不要): {{"score": 85, "transcript": "認識テキスト", "good_words": ["正解"], "bad_words": ["不正解"], "feedback": "フィードバック"}}"""
                try:
                    res = audio_model.generate_content([p, {"mime_type": "audio/wav", "data": audio_value.getvalue()}])
                    m = re.search(r'\{[\s\S]*\}', res.text)
                    if m:
                        rd = json.loads(m.group())
                        st.markdown(f'<div class="ep-card"><h3>スコア: {rd.get("score", 0)}%</h3><p>認識: {rd.get("transcript", "")}</p><p>{rd.get("feedback","")}</p></div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error("分析エラー")


# ============================================================
# TAB 5: PRACTICE
# ============================================================
with tab5:
    if not data:
        st.markdown(placeholder_html("✏️ 穴埋め"), unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background:{C["light"]};border:1px solid {C["border"]};border-radius:16px;padding:20px;text-align:center;"><div style="font-size:19px;font-weight:700;">{data.get("blank_q","")}</div><div style="font-size:12px;color:#94a3b8;margin-top:8px;">ヒント: {data.get("hint","")}</div></div>', unsafe_allow_html=True)
        user_ans = st.text_input("答えを入力", key="prac_ans")
        if st.button("✅ 答え合わせ", type="primary") and user_ans:
            c = data.get('blank_a', '')
            if user_ans.lower().strip() == c.lower().strip():
                st.success(f"🎉 正解！ ({c})")
            else:
                st.warning(f"不正解。正解は {c}")


# ============================================================
# TAB 6: ROLEPLAY
# ============================================================
with tab6:
    if not data:
        st.markdown(placeholder_html("🎭 会話"), unsafe_allow_html=True)
    else:
        if not st.session_state.chat_history:
            st.session_state.chat_history = [{"role": "assistant", "content": "Hello! Tell me about this." if is_biz else "Hi! Nice to meet you."}]
        
        chat_html = '<div class="ep-chat-wrap">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user": chat_html += f'<div class="ep-bubble-user" style="background:{C["main"]};">{msg["content"]}</div>'
            else: chat_html += f'<div class="ep-bubble-ai">{msg["content"]}</div>'
        chat_html += "</div>"
        st.markdown(chat_html, unsafe_allow_html=True)

        user_msg = st.chat_input("英語で返事を入力...")
        if user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with st.spinner("返答中..."):
                try:
                    res = audio_model.generate_content(f"相手の英語: {user_msg}\n文脈: {data.get('english','')}\n自然で短い英語（1〜2文）で返答して。")
                    st.session_state.chat_history.append({"role": "assistant", "content": res.text.strip()})
                    st.rerun()
                except Exception as e:
                    st.error("エラー")

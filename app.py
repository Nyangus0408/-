import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import json
import time
import base64
import os

# ==========================================
# 1. ページ設定とデザイン（CSS）
# ==========================================
st.set_page_config(page_title="English Pitch & Talk", page_icon="🇺🇸", layout="centered")

st.markdown("""
<style>
    .mode-business { background-color: #1d4ed8; color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; }
    .mode-daily { background-color: #0d9488; color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; }
    .chunk-text { font-size: 1.2rem; background: #f0fdfa; border: 1px solid #99f6e4; padding: 10px; border-radius: 8px; font-weight: bold; }
    .filler-card { background: #eff6ff; border: 1px solid #bfdbfe; padding: 8px; border-radius: 8px; font-size: 12px; display: inline-block; margin: 4px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Gemini APIの初期設定
# ==========================================
# Streamlit CloudのSecretsからキーを取得。なければテキストボックスで入力
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Keyを入力してください", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # JSON構造で出力させるためにGemini 2.0 Pro/Flashを使用
model = genai.GenerativeModel('gemini-2.0-flash', generation_config={"response_mime_type": "application/json"})
audio_model = genai.GenerativeModel('gemini-2.0-flash')

# ==========================================
# 3. 状態管理（Session State）
# ==========================================
if "script_data" not in st.session_state:
    st.session_state.script_data = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==========================================
# 4. ヘッダーとモード選択
# ==========================================
st.title("🇺🇸 English Pitch & Talk")
mode = st.radio("学習モードを選択", ["🏢 展示会・ビジネス", "☕ 日常会話・基礎"], horizontal=True)

if "ビジネス" in mode:
    st.markdown('<div class="mode-business">展示会・ビジネスモード 選択中</div>', unsafe_allow_html=True)
    sys_prompt = "あなたはビジネス英語の専門家です。中学レベルの文法(SVOなど)を使い、展示会で伝わるシンプルな英文を作成してください。"
else:
    st.markdown('<div class="mode-daily">日常会話・基礎モード 選択中</div>', unsafe_allow_html=True)
    sys_prompt = "あなたは日常英会話のコーチです。海外旅行やカフェで使える、シンプルで親しみやすい英文を作成してください。"

# ==========================================
# 5. 音声生成機能（TTS）
# ==========================================
def generate_audio_html(text, speed=1.0):
    tts = gTTS(text=text, lang='en')
    tts.save("temp.mp3")
    with open("temp.mp3", "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    # HTMLのaudioタグを使って再生速度をJavaScriptで制御可能にする
    audio_html = f"""
        <audio id="myAudio" controls style="width: 100%;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <div style="margin-top: 10px;">
            <button onclick="document.getElementById('myAudio').playbackRate = 0.8" style="padding: 5px; border-radius:5px;">0.8x ゆっくり</button>
            <button onclick="document.getElementById('myAudio').playbackRate = 1.0" style="padding: 5px; border-radius:5px;">1.0x 標準</button>
            <button onclick="document.getElementById('myAudio').playbackRate = 1.2" style="padding: 5px; border-radius:5px;">1.2x 速め</button>
        </div>
    """
    return audio_html

# ==========================================
# 6. メイン機能（タブ構成）
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 入力", "📖 スクリプト", "🔊 音読", "🎤 発音", "✏️ 穴埋め", "🎭 会話"])

# --- STEP 1: 入力 ---
with tab1:
    st.subheader("ステップ①：日本語を入力する")
    user_input = st.text_area("英語にしたい日本語の文章を入力してください", height=100)
    
    if st.button("✨ 英文＆学習コンテンツを生成する"):
        if not api_key:
            st.error("左のサイドバーにGemini API Keyを入力してください。")
        elif not user_input:
            st.warning("日本語の文章を入力してください。")
        else:
            with st.spinner("AIが学習コンテンツを作成中..."):
                prompt = f"""
                以下のルールに従ってJSON形式で出力してください。
                【入力文】: {user_input}
                【ルール】
                1. "english": 最適な英文
                2. "chunked": 意味の塊ごとにスラッシュ(/)で区切った英文
                3. "grammar": 文法解説の短いテキスト
                4. "vocab": {{単語: 意味}}の辞書
                5. "blank_q": 穴埋め問題用の文（1語を___にする）
                6. "blank_a": 穴埋め問題の答え
                7. "hint": 穴埋め問題の日本語ヒント
                """
                response = model.generate_content([sys_prompt, prompt])
                st.session_state.script_data = json.loads(response.text)
            st.success("生成完了！となりの「📖 スクリプト」タブに進んでください。")

if st.session_state.script_data:
    data = st.session_state.script_data
    
    # --- STEP 2: スクリプト ---
    with tab2:
        st.subheader("ステップ②：スクリプトを確認する")
        st.markdown(f'<div class="chunk-text">{data["chunked"]}</div>', unsafe_allow_html=True)
        st.info(f"**📚 文法解説**\n\n{data['grammar']}")
        st.write("**📝 重要語彙**")
        for k, v in data["vocab"].items():
            st.write(f"- **{k}**: {v}")

    # --- STEP 3: 音読 ---
    with tab3:
        st.subheader("ステップ③：音読・シャドーイング")
        st.write("安河内式 3ステップ（0.8xで口パク → 1.0xで声出し → 1.2xで追っかけ）")
        st.markdown(f"**{data['english']}**")
        html = generate_audio_html(data["english"])
        st.components.v1.html(html, height=100)

    # --- STEP 4: 発音（iPhone対応 st.audio_input） ---
    with tab4:
        st.subheader("ステップ④：発音チェック")
        st.write(f"お手本: **{data['english']}**")
        
        # iPhoneのネイティブマイクUIを呼び出す魔法のコンポーネント
        audio_value = st.audio_input("🎤 マイクを押して音読を録音")
        
        if audio_value is not None:
            with st.spinner("AIが発音を分析中..."):
                # 録音データをGeminiに渡してテキスト化＆採点
                prompt = f"この音声データを英語として文字起こしし、元の文「{data['english']}」と比較して、100点満点でスコアをつけてください。また、うまく発音できていなかった単語を指摘してください。"
                
                # audio_value は BytesIO オブジェクト
                audio_file = {"mime_type": "audio/wav", "data": audio_value.getvalue()}
                result = audio_model.generate_content([prompt, audio_file])
                
                st.success("分析完了！")
                st.write(result.text)

    # --- STEP 5: 穴埋め ---
    with tab5:
        st.subheader("ステップ⑤：穴埋め練習（瞬発力）")
        st.markdown(f"**{data['blank_q']}**")
        st.caption(f"💡 ヒント: {data['hint']}")
        
        if st.button("⏱ 3秒カウントダウンスタート"):
            placeholder = st.empty()
            for i in range(3, 0, -1):
                placeholder.markdown(f"## {i}")
                time.sleep(1)
            placeholder.markdown("## 答えて！")
            
        user_ans = st.text_input("答えを入力してください")
        if user_ans:
            if user_ans.lower().strip() == data['blank_a'].lower():
                st.success("正解！🎉")
            else:
                st.error(f"惜しい！正解は **{data['blank_a']}** です。")

    # --- STEP 6: 会話 ---
    with tab6:
        st.subheader("ステップ⑥：AIとロールプレイ")
        st.write("バイヤー（お客さん）になりきったAIと会話します。")
        
        # 初期メッセージ
        if not st.session_state.chat_history:
            st.session_state.chat_history.append({"role": "assistant", "content": f"Hello! Tell me about this. ({data['english']} に関連して話しかけています)"})

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
        user_msg = st.chat_input("英語で返答を入力してください...")
        if user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with st.chat_message("user"):
                st.write(user_msg)
            
            with st.chat_message("assistant"):
                # 文脈を渡して返答を生成
                chat_prompt = f"あなたは展示会のバイヤーです。以下のユーザーの英語に対して、短く自然な英語で返答してください。ユーザー: {user_msg}"
                res = audio_model.generate_content(chat_prompt)
                st.write(res.text)
                st.session_state.chat_history.append({"role": "assistant", "content": res.text})

# ==========================================
# 7. フィラーカード（ビジネスモード時のみフッター表示）
# ==========================================
if "ビジネス" in mode:
    st.markdown("---")
    st.caption("💬 時間かせぎ用 フィラーカード")
    fillers = [
        ("That's a great question.", "いい質問ですね"),
        ("Let me explain.", "説明します"),
        ("One moment, please.", "少々お待ちください")
    ]
    for en, jp in fillers:
        st.markdown(f'<div class="filler-card"><span style="color:#1d4ed8;font-weight:bold;">{en}</span><br><span style="color:gray;">{jp}</span></div>', unsafe_allow_html=True)

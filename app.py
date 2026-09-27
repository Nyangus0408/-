# ============================================================
# English / Deutsch Pitch & Talk + Immersive Vocab ── ダークテーマ完全版
# + 「2秒戻る」機能 ＆ Turso(クラウドDB) 統合バージョン
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
from PIL import Image
import pillow_heif
pillow_heif.register_heif_opener()
import libsql_experimental as libsql

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Pitch & Talk Pro",
    page_icon="🌐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# Turso DB
# ==========================================
try:
    import libsql_experimental as libsql
    LIBSQL_OK = True
except ImportError:
    LIBSQL_OK = False


def get_db_conn():
    """Tursoへの接続。未設定の場合はNoneを返す。"""
    if not LIBSQL_OK:
        return None

    try:
        url = st.secrets.get("TURSO_DATABASE_URL", "")
        token = st.secrets.get("TURSO_AUTH_TOKEN", "")

        if not url or not token:
            return None

        return libsql.connect(
            database=url,
            auth_token=token
        )
    except Exception:
        return None


def init_db():
    """必要なDBテーブルを作成する。"""
    conn = get_db_conn()

    if not conn:
        return

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                meaning TEXT NOT NULL,
                example TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                review_count INTEGER DEFAULT 0,
                last_reviewed TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

    except Exception as e:
        st.warning(f"⚠️ データベース初期化エラー: {e}")

    finally:
        conn.close()


def save_words_to_turso(word_list):
    conn = get_db_conn()

    if not conn:
        raise RuntimeError("Turso DBに接続できません。")

    count = 0

    try:
        for item in word_list:
            conn.execute(
                """
                INSERT INTO vocabulary
                (word, meaning, example)
                VALUES (?, ?, ?)
                """,
                (
                    item.get("word", ""),
                    item.get("meaning", ""),
                    item.get("example", "")
                )
            )
            count += 1

        conn.commit()
        return count

    finally:
        conn.close()


def save_words_to_turso(vocab_list, lang_code):
    conn = get_db_conn()
    if not conn: return 0
    
    # 過去のデータベースに「language（言語）」の枠を自動追加（すでにある場合はスキップ）
    try:
        conn.execute("ALTER TABLE vocabulary ADD COLUMN language TEXT")
        conn.commit()
    except:
        pass 

    count = 0
    try:
        cursor = conn.cursor()
        for item in vocab_list:
            word = item.get("word", "")
            meaning = item.get("meaning", "")
            example = item.get("example", "")
            
            # 1. まず単語が既にデータベースに存在するかチェック
            cursor.execute("SELECT id FROM vocabulary WHERE word = ?", (word,))
            existing_row = cursor.fetchone()
            
            if existing_row:
                # 2-A. すでに存在する場合は内容を上書き（UPDATE）
                cursor.execute("""
                    UPDATE vocabulary 
                    SET meaning = ?, example = ?, language = ?
                    WHERE word = ?
                """, (meaning, example, lang_code, word))
            else:
                # 2-B. 存在しない場合は新規追加（INSERT）
                cursor.execute("""
                    INSERT INTO vocabulary (word, meaning, example, language)
                    VALUES (?, ?, ?, ?)
                """, (word, meaning, example, lang_code))
            count += 1
        conn.commit()
    except Exception as e:
        st.error(f"保存エラー: {e}")
    finally:
        conn.close()
    return count

# 1. 選択した言語の単語をクラウドDBから一括削除する関数
def delete_all_words_from_turso(lang_code):
    conn = get_db_conn()
    if not conn: return
    try:
        conn.execute("DELETE FROM vocabulary WHERE language = ? OR (language IS NULL AND ? = 'English')", (lang_code, lang_code))
        conn.commit()
    except Exception as e:
        st.error(f"一括削除エラー: {e}")
    finally:
        conn.close()

# 2. 既存のドイツ語単語に定冠詞（der/die/das）を一括付与する関数
def auto_add_articles_to_vocab(vocab_list):
    if not vocab_list: return vocab_list
    
    prompt = f"""
以下のドイツ語単語リストを受け取り、名詞であるものにはすべて適切な定冠詞（der, die, das）を補完してください。
すでに定冠詞がついているものや、動詞・形容詞などはそのまま維持してください。

【入力リスト】
{json.dumps(vocab_list, ensure_ascii=False)}

【出力ルール】
入力と同じJSON配列形式（[{{\"word\": \"...\", \"meaning\": \"...\"}}]）のみを返してください。
Markdownや```jsonは含めないでください。
"""
    try:
        response = st.session_state["_client"].models.generate_content(
            model=GEMINI_MODEL,
            contents=[prompt]
        )
        result_text = response.text.strip()
        result_text = re.sub(r"^```(?:json)?\s*", "", result_text)
        result_text = re.sub(r"\s*```$", "", result_text)
        updated_list = json.loads(result_text.strip())
        return updated_list
    except Exception as e:
        st.error(f"定冠詞の付与中にエラーが発生しました: {e}")
        return vocab_list

def load_words_from_turso(lang_code):
    conn = get_db_conn() # ← ここを修正しました
    if not conn: return []
    
    # 【重要】ここでも念のため言語枠の追加を実行
    try:
        conn.execute("ALTER TABLE vocabulary ADD COLUMN language TEXT")
        conn.commit()
    except:
        pass

    try:
        cursor = conn.cursor()
        # 選択した言語、または昔保存した言語未設定(NULL)の単語だけを読み込む
        cursor.execute("""
            SELECT id, word, meaning, example, language 
            FROM vocabulary 
            WHERE language = ? OR language IS NULL
            ORDER BY id DESC
        """, (lang_code,))
        rows = cursor.fetchall()
        return [{"id": row[0], "word": row[1], "meaning": row[2], "example": row[3], "language": row[4]} for row in rows]
    except Exception as e:
        st.error(f"読み込みエラー: {e}")
        return []
    finally:
        conn.close()

# 新規追加：クラウドDBから特定の単語を削除する関数
def delete_word_from_turso(word_id):
    conn = get_db_conn() # ← ここを修正しました
    if not conn: return
    try:
        conn.execute("DELETE FROM vocabulary WHERE id = ?", (word_id,))
        conn.commit()
    except Exception as e:
        st.error(f"削除エラー: {e}")
    finally:
        conn.close()

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

# Turso DB用ライブラリ
try:
    import libsql_experimental as libsql
    LIBSQL_OK = True
except ImportError:
    LIBSQL_OK = False
def load_scripts_from_db():
    conn = get_db_conn()
    if not conn: return []
    try:
        cursor = conn.cursor()
        # テーブルが存在しない場合は自動作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        cursor.execute("SELECT id, title, content FROM scripts ORDER BY id DESC")
        rows = cursor.fetchall()
        return [{"id": row[0], "title": row[1], "content": row[2]} for row in rows]
    except Exception as e:
        st.error(f"スクリプト読み込みエラー: {e}")
        return []
    finally:
        conn.close()

def save_script_to_db(title, content):
    conn = get_db_conn()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("INSERT INTO scripts (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
    except Exception as e:
        st.error(f"スクリプト保存エラー: {e}")
    finally:
        conn.close()

def delete_script_from_db(script_id):
    conn = get_db_conn()
    if not conn: return
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scripts WHERE id = ?", (script_id,))
        conn.commit()
    except Exception as e:
        st.error(f"スクリプト削除エラー: {e}")
    finally:
        conn.close()
        
# ── MODEL NAME ──
GEMINI_MODEL = "gemini-3.5-flash"


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
        'app_title': 'AI Language Tutor',
        'subtitle': '日常会話・旅行・基礎学習ツール',
        'script_lbl': '英文スクリプト（チャンク読み）',
    },
    'de': {
        'flag': '🇩🇪', 'name': 'Deutsch', 'tts': 'de',
        'app_title': 'AI Sprachlehrer',
        'subtitle': '日常会話・旅行・基礎学習ツール',
        'script_lbl': 'ドイツ語スクリプト（チャンク読み）',
    },
    'zh': {
        'flag': '🇨🇳', 'name': '中文', 'tts': 'zh-CN',
        'app_title': 'AI 语言导师',
        'subtitle': '日常会話・旅行・基礎学習ツール',
        'script_lbl': '中国語スクリプト（ピンイン付き）',
    },
}

LEVELS = {
    "🌱 初学者 (A1)": {
        'en':"最基本の単語のみ。主語＋動詞の最小構造。5単語以内。",
        'de':"Einfachste Satzstruktur. Maximal 5 Wörter.",
        'zh':"最も基本的な単語のみ。主語＋動詞の最小構造。5単語以内。",
    },
    "📗 基礎 (A2)": {
        'en':"基礎的な表現。1文12単語以内。シンプルな構造のみ。",
        'de':"Grundlegendes Deutsch. Max. 12 Wörter. Einfache Struktur.",
        'zh':"基礎的な表現。1文12単語以内。シンプルな構造のみ。",
    },
    "📘 中級 (B1/B2)": {
        'en':"日常会話レベル。接続詞を使った少し複雑な構造もOK。",
        'de':"Mittelstufe. Konjunktionen erlaubt.",
        'zh':"日常会話レベル。接続詞を使った少し複雑な構造もOK。",
    },
    "📙 上級 (C1)": {
        'en':"自然で流暢な表現。豊かな語彙を使用。",
        'de':"Fließendes Deutsch. Breiter Wortschatz.",
        'zh':"自然で流暢な表現。豊かな語彙を使用。",
    },
    "🚀 ネイティブ風": {
        'en':"ネイティブが日常的に使う自然な表現。慣用句も使用可。",
        'de':"Natürliches Deutsch. Idiome und Umgangssprache erlaubt.",
        'zh':"ネイティブが日常的に使う自然な表現。成語や慣用句も使用可。",
    },
}

DAILY_SCENARIOS = {
    'en': ["🎯 おまかせ", "☕ カフェ/レストラン", "🗺️ 観光/道案内", "🏨 ホテル/交通", "🛒 買い物", "👋 自己紹介/雑談", "🚨 緊急/トラブル"],
    'de': ["🎯 おまかせ", "☕ Café/Restaurant", "🗺️ Tourismus/Wegbeschreibung", "🏨 Hotel/Verkehr", "🛒 Einkaufen", "👋 Vorstellung/Smalltalk", "🚨 Notfall/Probleme"],
    'zh': ["🎯 おまかせ", "☕ カフェ/レストラン", "🗺️ 観光/道案内", "🏨 ホテル/交通", "🛒 買い物", "👋 自己紹介/雑談", "🚨 緊急/トラブル"],
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
        # ★ ここに「2秒戻る」を追加 ★
        return f"""
        <audio id="epA" style="width:100%; border-radius:12px; margin-bottom:8px;" controls>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <div style="display:flex; gap:8px;">
            <button onclick="document.getElementById('epA').currentTime -= 2; document.getElementById('epA').play();"
                style="flex:1; padding:9px 0; border:1px solid #334155; border-radius:10px; background:#1e293b; color:#f8fafc; cursor:pointer; font-weight:700;">
                ⏪ 2秒戻る
            </button>
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
            types.Part.from_text(text=prompt),
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
            types.Part.from_text(text=prompt),
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
def build_prompt(topic, level_name, level_desc, lang):
    target = "ドイツ語" if lang == 'de' else ("中国語（必ずピンインを付与）" if lang == 'zh' else "英語")
    
    return f"""
あなたはプロの語学教師です。以下の【入力内容】を、誰でも日常的に使える自然な{target}に翻訳・構成してください。

【重要ルール】
・ユーザーの入力意図を忠実に反映してください。
・勝手に「ビジネス」「展示会」「会社代表」などの特殊な文脈を付け加えないでください（例：「私は日本人です」という入力に対し、「日本の会社を代表しています」などと飛躍させないこと）。

【入力内容】: {topic}
【学習レベル】: {level_name} ({level_desc})

出力は必ず以下のJSONフォーマットのみにしてください。マークダウン(```json)は不要です。
{{
  "english": "{target}の自然なフレーズ",
  "english_jp": "日本語訳",
  "vocab": {{
    "単語1": "意味1",
    "単語2": "意味2"
  }},
  "grammar": "文法やフレーズの簡潔な解説",
  "blank_q": "{target}フレーズの一部を[___]にした穴埋め問題",
  "blank_a": "[___]に入る正解の単語",
  "hint": "穴埋め問題の日本語ヒント"
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
    "vocab_list": [],
    "db_initialized": False
}
for k, v in defaults.items():
    if k not in st.session_state: 
        st.session_state[k] = v

if not st.session_state.db_initialized:
    init_db()
    st.session_state.db_initialized = True

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
    st.header("⚙️ 学習設定")
    learning_language = st.selectbox(
        "学習する言語を選択",
        ["English (US)", "Deutsch (ドイツ語)", "中文 (中国語・簡体字)"]
    )
    st.session_state["learning_language"] = learning_language

    base_system_prompt = f"""
    あなたはプロの{learning_language}教師です。
    回答には、自然な{learning_language}の表現を使用してください。
    ※中国語の場合はピンイン（発音記号）を、ドイツ語・英語の場合は重要なアクセントや発音のコツを必ず添えてください。
    """
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
        
    if LIBSQL_OK and get_db_conn():
        st.success("☁️ Turso DB 接続済み")
    else:
        st.warning("⚠️ Turso DB 未接続（一時保存のみ）")

# ── HEADER & MODE ────────────────────────────────────────────

is_biz = False
C = ac(is_biz, lang)

st.markdown(f"<style>:root{{--acc:{C['main']};}}</style>", unsafe_allow_html=True)

sys_p = {
    'en': "あなたはプロの英語教師です。ユーザーの入力文を、自然で日常的な英文に翻訳・構成してください。勝手に文脈を付け加えないでください。",
    'de': "あなたはプロのドイツ語教師です。ユーザーの入力文を、自然で日常的なドイツ語文に翻訳・構成してください。勝手に文脈を付け加えないでください。",
    'zh': "あなたはプロの中国語教師です。ユーザーの入力文を、自然で日常的な中国語文に翻訳・構成し、必ずピンインを併記してください。勝手に文脈を付け加えないでください。",
}.get(lang, "")

st.markdown(f"""
<div style="background:linear-gradient(135deg,{C['main']},{C['main']}cc); color:white; padding:18px 22px 14px; border-radius:16px; margin-bottom:14px; box-shadow: 0 4px 12px rgba(0,0,0,.3);">
  <div style="font-size:21px; font-weight:900; margin-bottom:3px;">
    {LS['flag']} {LS['app_title']}
  </div>
  <div style="font-size:12px; opacity:.9;">
    {LS['subtitle']}
  </div>
</div>
""", unsafe_allow_html=True)

# ▼▼▼ ボタンをプルダウンメニューに変更 ▼▼▼
col_sp, col_lang = st.columns([2, 1])
with col_lang:
    lang_options = {'en': '🇺🇸 English', 'de': '🇩🇪 Deutsch', 'zh': '🇨🇳 中文'}
    current_lang = st.session_state.language
    current_index = list(lang_options.keys()).index(current_lang) if current_lang in lang_options else 0
    
    selected_label = st.selectbox(
        "🌐 言語", 
        options=list(lang_options.values()),
        index=current_index,
        label_visibility="collapsed"
    )
    
    selected_key = [k for k, v in lang_options.items() if v == selected_label][0]
    if selected_key != current_lang:
        st.session_state.language = selected_key
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
                        """
                        prompt += build_prompt("", level_key, LEVELS[level_key][lang], lang)
                    else:
                        prompt = build_prompt(user_input, level_key, LEVELS[level_key][lang], lang)

                    result = do_generate(prompt, sys_p)
                    result.update({
                        "_source_ja": user_input[:100],
                        "_level": level_key,
                        "_mode": "daily",
                        "_lang": lang
                    })
                    st.session_state.script_data = result
                    st.session_state.chat_history = []
                    data = result
                    st.success("✔ 生成完了！「📖 読解」タブに進んでください。")
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

        st.divider()
        if st.button("💾 このスクリプトを保存帳(クラウド)に保存", type="primary", use_container_width=True):
            title = data.get('_source_ja', '無題のスクリプト')[:20]
            if save_script_to_db(title, data):
                st.success("☁️ クラウドデータベースに保存しました！「📚 保存帳」で確認できます。")
            else:
                if data not in st.session_state.saved_list:
                    data['title'] = title
                    st.session_state.saved_list.append(data)
                st.warning("⚠️ クラウドDB未接続のため、このセッションに一時保存しました。")

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
            <div style="font-size:16px; font-weight:600; margin-bottom:12px; color:#f8fafc;">{data.get('english','')}</div>
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
        rec = st.audio_input("録音", key="main_audio_record")
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
                                types.Part.from_text(text=p_msg),
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
        persona = f"あなたは親切な{LS['name']}の語学チューターです。ユーザーのレベルに合わせて自然で分かりやすい日本語と{LS['name']}で会話・指導を行ってください。"
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
# TAB 7: 画像単語 (IMAGE VOCAB) - 複数一括読み込み対応版
# ============================================================
with tab7:
    st.markdown("### 📸 カメラ / 画像から単語を抽出")
    st.write(
        "単語帳や書類を撮影、または画像ファイルを選択して、自動で単語リスト化します。"
        "**複数の画像を一度に選んで一括処理できます（HEIC対応）。**"
    )

    input_method = st.radio(
        "取り込み方法を選択",
        ["ファイルから選択（ギャラリー・フォルダ）", "カメラで撮影"],
        horizontal=True,
        key="image_input_method"
    )

    images_to_process = []

    if input_method == "カメラで撮影":
        camera_image = st.camera_input("カメラで撮影", key="vocab_camera")
        if camera_image:
            images_to_process = [camera_image]
    else:
        # accept_multiple_files=True で複数選択を可能に
        uploaded_images = st.file_uploader(
            "画像ファイルを選択（複数選択可。PNG, JPG, HEICなど）",
            type=["png", "jpg", "jpeg", "heic", "HEIC"],
            accept_multiple_files=True,
            key="img_uploader"
        )
        if uploaded_images:
            images_to_process = uploaded_images

    if images_to_process:
        st.write(f"📁 **{len(images_to_process)} 枚**の画像が選択されています。")
        
        # 選択された画像のプレビューを横並びで表示
        cols = st.columns(min(len(images_to_process), 3))
        for idx, img_file in enumerate(images_to_process):
            with cols[idx % 3]:
                st.image(img_file, use_container_width=True)

        if st.button("✨ 選択した画像から単語を一括抽出する", type="primary", use_container_width=True, key="extract_vocab_from_images"):
            with st.spinner("Geminiが画像を解析して単語を一括抽出中..."):
                try:
                    # 言語ごとの設定とAIへの追加指示
                    if lang == "en":
                        target_lang = "英語"
                        extra_rule = ""
                        example_json = '[\n  {"word": "apple", "meaning": "りんご"},\n  {"word": "negotiation", "meaning": "交渉"}\n]'
                    elif lang == "de":
                        target_lang = "ドイツ語"
                        # ドイツ語の時だけ、AIに定冠詞をつけるよう強く指示する
                        extra_rule = "【重要】抽出する単語が名詞の場合は、必ず先頭に定冠詞（der, die, das）を付けてください。"
                        example_json = '[\n  {"word": "der Apfel", "meaning": "りんご"},\n  {"word": "die Verhandlung", "meaning": "交渉"}\n]'
                    else:
                        target_lang = "中国語"
                        extra_rule = ""
                        example_json = '[\n  {"word": "苹果", "meaning": "りんご"},\n  {"word": "谈判", "meaning": "交渉"}\n]'

                    prompt = f"""
これらの画像に含まれる{target_lang}の重要な単語やフレーズをすべて抽出してください。
複数の画像がある場合は、すべての画像から抽出してください。
{extra_rule}

以下のJSON形式の配列のみを返してください。Markdownや```jsonは使用しないでください。
{example_json}

"""
                    # AIに送るデータのリスト（最初はテキストプロンプト）
                    contents_to_send = [types.Part.from_text(text=prompt)]
                    
                    # 選択された画像をすべて変換してリストに追加
                    for img_file in images_to_process:
                        # HEICなどの画像をPillowで開き、標準的なJPEGデータに変換（エラー対策）
                        img = Image.open(img_file)
                        if img.mode != "RGB":
                            img = img.convert("RGB")
                        
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG")
                        
                        # JPEGデータとしてAIへの送信リストに追加
                        contents_to_send.append(
                            types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")
                        )

                    # まとめて1回だけAIにリクエストを送信
                    response = st.session_state["_client"].models.generate_content(
                        model=GEMINI_MODEL,
                        contents=contents_to_send
                    )

                    result_text = response.text.strip()
                    result_text = re.sub(r"^```(?:json)?\s*", "", result_text)
                    result_text = re.sub(r"\s*```$", "", result_text)

                    extracted_items = json.loads(result_text.strip())

                    if extracted_items:
                        existing_words = {
                            item.get("word") for item in st.session_state.vocab_list if isinstance(item, dict)
                        }
                        new_added = 0

                        for item in extracted_items:
                            if isinstance(item, dict) and item.get("word") and item.get("word") not in existing_words:
                                st.session_state.vocab_list.append(item)
                                existing_words.add(item.get("word"))
                                new_added += 1

                        st.success(f"🎉 {new_added}件の単語を新しく追加しました！（合計: {len(st.session_state.vocab_list)}件）")
                    else:
                        st.warning("画像から単語を検出できませんでした。")

                except json.JSONDecodeError:
                    st.error("AIからのJSONデータ受け取りに失敗しました。もう一度お試しください。")
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    # 現在の単語リスト
    st.divider()
    st.subheader("📝 現在の単語リスト")

    if st.session_state.vocab_list:
        for i, item in enumerate(st.session_state.vocab_list, 1):
            st.markdown(f"**{i}. {item.get('word', '')}** — {item.get('meaning', '')}")
    else:
        st.info("まだ単語がありません。画像から単語を抽出してください。")
        
# ============================================================
# TAB 8: FLASHCARDS (IMMERSIVE MODE)
# ============================================================
with tab8:
    st.markdown("### ☁️ クラウド単語帳（言語別＆管理機能）")
    
    selected_vocab_lang = st.selectbox(
        "📚 扱う言語を選択してください", 
        ["English", "German", "Chinese"], 
        key="vocab_lang_select"
    )
    
    col_load, col_save = st.columns(2)
    
    with col_load:
        if st.button(f"🔄 {selected_vocab_lang} をロード", use_container_width=True, key="tab8_load"):
            with st.spinner("データを取得中..."):
                db_words = load_words_from_turso(selected_vocab_lang)
            if db_words:
                st.session_state.vocab_list = db_words
                st.success(f"✅ {len(db_words)} 件の {selected_vocab_lang} 単語を読み込みました！")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.vocab_list = []
                st.info(f"DBに保存されている {selected_vocab_lang} の単語はありません。")

    with col_save:
        if st.button("💾 現在のリストを保存", use_container_width=True, key="tab8_save"):
            if not st.session_state.vocab_list:
                st.warning("保存する単語がありません。")
            else:
                with st.spinner("クラウドDBに保存中..."):
                    try:
                        saved_count = save_words_to_turso(st.session_state.vocab_list, selected_vocab_lang)
                        st.success(f"✅ {saved_count}件の単語を {selected_vocab_lang} として保存しました！")
                    except Exception as e:
                        st.error(f"保存中にエラーが発生しました: {e}")

    # ▼▼▼ 便利機能・一括操作パネル ▼▼▼
    st.divider()
    
    col_tools1, col_tools2 = st.columns(2)
    
    # ドイツ語選択時のみ「定冠詞の一括補完」ボタンを表示
    with col_tools1:
        if selected_vocab_lang == "German" and st.session_state.get("vocab_list"):
            if st.button("✨ 既存単語に定冠詞(der/die/das)を一括付与", use_container_width=True, type="secondary"):
                with st.spinner("AIが名詞を判定して定冠詞を補完中..."):
                    updated_vocab = auto_add_articles_to_vocab(st.session_state.vocab_list)
                    st.session_state.vocab_list = updated_vocab
                    # 補完後に自動でクラウド保存
                    save_words_to_turso(updated_vocab, "German")
                    st.success("✅ 定冠詞の補完と保存が完了しました！")
                    import time
                    time.sleep(1)
                    st.rerun()

    # 一括削除ボタン
    with col_tools2:
        if st.session_state.get("vocab_list"):
            if st.button(f"🚨 {selected_vocab_lang} の全単語を一括削除", use_container_width=True, type="primary"):
                delete_all_words_from_turso(selected_vocab_lang)
                st.session_state.vocab_list = []
                st.success(f"🗑️ {selected_vocab_lang} の単語をすべて削除しました。")
                import time
                time.sleep(1)
                st.rerun()

    st.divider()

    # （※ここから下は既存の st.expander による単語リスト表示やフラッシュカード処理が続きます）

    if not st.session_state.get("vocab_list"):
        st.info("💡 単語リストが空です。上のボタンでロードするか、「📷 画像単語」タブで追加してください。")
    else:
        # ▼▼▼【改善ポイント】単語リストを折りたたみ（アコーディオン）の中に収納 ▼▼▼
        with st.expander(f"📖 {selected_vocab_lang} の単語リスト一覧・編集（クリックで開閉）", expanded=False):
            
            # リストの見出し行
            col_w, col_m, col_e, col_d = st.columns([2, 2, 4, 1])
            col_w.caption("単語")
            col_m.caption("意味")
            col_e.caption("例文")
            col_d.caption("操作")
            
            # 単語データと「削除」ボタンの表示
            for i, word_data in enumerate(st.session_state.vocab_list):
                col_w, col_m, col_e, col_d = st.columns([2, 2, 4, 1])
                col_w.write(f"**{word_data.get('word', '')}**")
                col_m.write(word_data.get('meaning', ''))
                col_e.write(word_data.get('example', ''))
                
                # DBに保存済み（idがある）単語のみ削除可能にする
                if "id" in word_data:
                    with col_d:
                        if st.button("🗑️ 削除", key=f"del_vocab_{word_data['id']}"):
                            delete_word_from_turso(word_data["id"])
                            st.success(f"「{word_data['word']}」を削除しました")
                            st.session_state.vocab_list.pop(i) # 画面上からも消す
                            import time
                            time.sleep(1)
                            st.rerun()

        st.divider()

        st.markdown("#### 🎴 フラッシュカード")
        

    if not st.session_state.vocab_list:
        st.info("💡 まずは「📷 画像単語」タブで単語を追加してください。")
    else:
        interval = st.slider(
            "単語表示から訳・音声が出るまでの時間（秒）",
            min_value=1.0,
            max_value=4.0,
            value=2.0,
            step=0.5,
            key="slider_word_interval_unique"
        )

        vocab_json = json.dumps(st.session_state.vocab_list)
        lang_code = 'en-US' if lang == 'en' else 'de-DE'
        btn_color = C["main"]

        html_code = f"""
        <div style="font-family: sans-serif; padding: 15px; background-color: #1e293b; border-radius: 16px; border: 1px solid #334155;">
            
            <!-- コントロールボタン群 -->
            <div style="text-align: center; margin-bottom: 15px; display: flex; justify-content: center; flex-wrap: wrap; gap: 10px;">
                <button id="startBtn" style="padding: 10px 20px; font-size: 15px; font-weight: bold; color: white; background-color: {btn_color}; border: none; border-radius: 8px; cursor: pointer;">
                    ▶ スタート
                </button>
                <button id="stopBtn" style="padding: 10px 20px; font-size: 15px; font-weight: bold; color: white; background-color: #ef4444; border: none; border-radius: 8px; cursor: pointer; display: none;">
                    ■ 停止
                </button>
                <button id="resetBtn" style="padding: 10px 20px; font-size: 15px; font-weight: bold; color: white; background-color: #64748b; border: none; border-radius: 8px; cursor: pointer;">
                    🔄 最初から
                </button>
                <button id="shuffleBtn" style="padding: 10px 20px; font-size: 15px; font-weight: bold; color: #1e293b; background-color: #f8fafc; border: none; border-radius: 8px; cursor: pointer;">
                    🔀 シャッフル: OFF
                </button>
            </div>
            
            <!-- フラッシュカード表示エリア -->
            <div style="text-align: center; min-height: 140px; display: flex; flex-direction: column; justify-content: center; background: #0f172a; border-radius: 12px; padding: 20px; border: 1px solid #334155; margin-bottom: 20px;">
                <div id="wordText" style="font-size: 34px; font-weight: 900; color: #ffffff; margin-bottom: 8px;">Ready...</div>
                <div id="meaningText" style="font-size: 20px; font-weight: 700; color: {btn_color};">リストの単語を押すとそこから始まります</div>
            </div>

            <!-- 単語リスト表示エリア -->
            <div style="font-size: 14px; font-weight: bold; color: #cbd5e1; margin-bottom: 8px;">📋 単語リスト（クリックで再生開始）</div>
            <div id="vocabList" style="height: 250px; overflow-y: auto; background-color: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 5px;">
            </div>
        </div>

        <style>
            .list-item {{
                padding: 12px; 
                border-bottom: 1px solid #1e293b; 
                color: #cbd5e1; 
                cursor: pointer; 
                border-radius: 6px;
                transition: background 0.2s;
            }}
            .list-item:hover {{
                background-color: #1e293b;
            }}
            .list-item.active {{
                background-color: {btn_color};
                color: white;
            }}
            #vocabList::-webkit-scrollbar {{ width: 8px; }}
            #vocabList::-webkit-scrollbar-thumb {{ background: #475569; border-radius: 4px; }}
        </style>

        <script>
            const vocab = {vocab_json};
            const waitBeforeAnswerMs = {int(interval * 1000)};
            const waitAfterAnswerMs = 2500;
            const langCode = "{lang_code}";
            
            let playOrder = vocab.map((_, i) => i);
            let index = 0; 
            let isPlaying = false;
            let isShuffle = false;
            let interrupt = false; 
            let currentUtterance = null;

            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            const resetBtn = document.getElementById('resetBtn');
            const shuffleBtn = document.getElementById('shuffleBtn');
            const wordText = document.getElementById('wordText');
            const meaningText = document.getElementById('meaningText');
            const vocabListDiv = document.getElementById('vocabList');

            function renderList() {{
                vocabListDiv.innerHTML = '';
                vocab.forEach((item, originalIdx) => {{
                    const div = document.createElement('div');
                    div.className = 'list-item';
                    div.id = 'item-' + originalIdx;
                    div.innerHTML = `<strong>${{originalIdx + 1}}. ${{item.word}}</strong> <span style="font-size:0.9em; opacity:0.8; margin-left:8px;">${{item.meaning}}</span>`;
                    
                    div.onclick = () => {{
                        let pIdx = playOrder.indexOf(originalIdx);
                        if (pIdx !== -1) {{
                            index = pIdx;
                            interrupt = true;
                            window.speechSynthesis.cancel();
                            if (!isPlaying) {{
                                startBtn.click();
                            }}
                        }}
                    }};
                    vocabListDiv.appendChild(div);
                }});
            }}

            renderList();

            function updateHighlight(originalIdx) {{
                document.querySelectorAll('.list-item').forEach(el => el.classList.remove('active'));
                const activeEl = document.getElementById('item-' + originalIdx);
                if (activeEl) {{
                    activeEl.classList.add('active');
                    activeEl.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
            }}

            function shuffleArray(array) {{
                for (let i = array.length - 1; i > 0; i--) {{
                    const j = Math.floor(Math.random() * (i + 1));
                    [array[i], array[j]] = [array[j], array[i]];
                }}
            }}

            shuffleBtn.addEventListener('click', () => {{
                isShuffle = !isShuffle;
                shuffleBtn.innerText = isShuffle ? "🔀 シャッフル: ON" : "🔀 シャッフル: OFF";
                shuffleBtn.style.backgroundColor = isShuffle ? "#f59e0b" : "#f8fafc";
                shuffleBtn.style.color = isShuffle ? "white" : "#1e293b";
                
                playOrder = vocab.map((_, i) => i);
                if (isShuffle) {{
                    shuffleArray(playOrder);
                }}
                index = 0;
                interrupt = true;

                if (!isPlaying) {{
                    wordText.innerText = "Order Updated";
                    meaningText.innerText = "順番が変更されました";
                }}
            }});

            const sleep = async (ms) => {{
                let waited = 0;
                while (waited < ms && isPlaying && !interrupt) {{
                    await new Promise(r => setTimeout(r, 100));
                    waited += 100;
                }}
            }};

            function speakText(text) {{
                if (!text) return;
                if (window.speechSynthesis.paused) window.speechSynthesis.resume();
                window.speechSynthesis.cancel();
                
                currentUtterance = new SpeechSynthesisUtterance(text);
                currentUtterance.lang = langCode;
                currentUtterance.rate = 0.9;
                window.speechSynthesis.speak(currentUtterance);
            }}

            async function playLoop() {{
                while (isPlaying) {{
                    interrupt = false;

                    if (index >= vocab.length) {{
                        index = 0;
                    }}
                    
                    let originalIdx = playOrder[index];
                    const current = vocab[originalIdx];
                    
                    updateHighlight(originalIdx);
                    
                    wordText.innerText = current.word;
                    meaningText.innerText = "";
                    
                    await sleep(waitBeforeAnswerMs);

                    if (!isPlaying) break;
                    if (interrupt) continue;
                    
                    meaningText.innerText = current.meaning;
                    speakText(current.word);
                    
                    await sleep(waitAfterAnswerMs);

                    if (!isPlaying) break;
                    if (interrupt) continue;
                    
                    index++;
                }}
            }}

            startBtn.addEventListener('click', () => {{
                const unlockAudio = new SpeechSynthesisUtterance('');
                window.speechSynthesis.speak(unlockAudio);
                
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
                
                isPlaying = true;
                playLoop();
            }});

            stopBtn.addEventListener('click', () => {{
                isPlaying = false;
                window.speechSynthesis.cancel();
                startBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
                wordText.innerText = "Stopped";
                meaningText.innerText = "一時停止中（▶で続きから）";
            }});

            resetBtn.addEventListener('click', () => {{
                isPlaying = false;
                interrupt = true;
                window.speechSynthesis.cancel();
                index = 0;
                startBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
                wordText.innerText = "Ready...";
                meaningText.innerText = "最初に戻りました";
                document.querySelectorAll('.list-item').forEach(el => el.classList.remove('active'));
            }});
        </script>
        """

        st.components.v1.html(html_code, height=650, scrolling=False)

# ============================================================
# TAB 9: SAVED (クラウド対応版)
# ============================================================
with tab9:
    db_scripts = load_scripts_from_db()
    
    if not db_scripts and not st.session_state.saved_list:
        st.markdown(ph("📚 保存帳"), unsafe_allow_html=True)
    else:
        st.markdown("### 📚 保存したスクリプト")
        
        # クラウド保存分
        if db_scripts:
            st.success(f"☁️ クラウド上に {len(db_scripts)} 件のスクリプトが保存されています")
            for item in db_scripts:
                with st.expander(f"📄 {item.get('_title', '無題')} ({item.get('_created_at', '')[:10]})"):
                    st.markdown(f"**{item.get('_lang', '言語').upper()}:** {item.get('english', '')}")
                    st.markdown(f"**日本語:** {item.get('english_jp', '')}")
                    if st.button("🗑️ 削除", key=f"del_{item.get('_db_id')}"):
                        delete_script_from_db(item.get('_db_id'))
                        st.rerun()
                        
        # 一時保存分（DB未接続時などのフォールバック）
        if st.session_state.saved_list:
            st.info("💻 このセッションでの一時保存")
            if st.button("🗑️ 一時保存を全て削除"):
                st.session_state.saved_list = []
                st.rerun()
                
            for idx, item in enumerate(st.session_state.saved_list):
                st.markdown(f"""
                <div class="ep-card">
                    <strong>{item.get('title', '無題')}</strong><br>
                    <span style="font-size:12px; color:#cbd5e1;">{item.get('english_jp', '')}</span>
                </div>
                """, unsafe_allow_html=True)

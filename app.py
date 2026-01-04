import streamlit as st
import os
import tempfile
import json
import uuid
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from streamlit_js_eval import streamlit_js_eval

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="音声配信AIアシスタント",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- LocalStorage Functions ---

STORAGE_KEY = "audio_ai_assistant_history"

def load_history_from_storage():
    """LocalStorageから履歴を読み込む（初回のみ）"""
    # 既に読み込み済みの場合はスキップ
    if st.session_state.get('history_loaded', False):
        return
    
    # JavaScriptでLocalStorageから読み込み
    stored_data = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{STORAGE_KEY}')",
        key="load_history_initial"
    )
    
    # stored_dataがNoneでない場合（JavaScriptが実行完了した場合）
    if stored_data is not None and stored_data != "null" and stored_data != "":
        try:
            loaded_history = json.loads(stored_data)
            if isinstance(loaded_history, list):
                st.session_state.history = loaded_history
                st.session_state.history_loaded = True
        except (json.JSONDecodeError, TypeError):
            st.session_state.history_loaded = True
    elif stored_data == "null" or stored_data == "":
        # LocalStorageが空の場合
        st.session_state.history_loaded = True


def save_history_to_storage():
    """LocalStorageに履歴を保存する"""
    if 'history' in st.session_state and st.session_state.history:
        history_json = json.dumps(st.session_state.history, ensure_ascii=False)
        # JavaScriptでLocalStorageに保存（エスケープ処理）
        escaped_json = history_json.replace('\\', '\\\\').replace("'", "\\'")
        streamlit_js_eval(
            js_expressions=f"localStorage.setItem('{STORAGE_KEY}', '{escaped_json}')",
            key=f"save_history_{len(st.session_state.history)}_{datetime.now().strftime('%H%M%S')}"
        )


def clear_storage():
    """LocalStorageの履歴をクリア"""
    streamlit_js_eval(
        js_expressions=f"localStorage.removeItem('{STORAGE_KEY}')",
        key=f"clear_history_{datetime.now().strftime('%H%M%S')}"
    )


# --- Script History Storage Functions ---

SCRIPT_STORAGE_KEY = "audio_ai_assistant_saved_scripts"

def load_saved_scripts():
    """LocalStorageから保存済み台本を読み込む（初回のみ）"""
    if st.session_state.get('scripts_loaded', False):
        return
    
    stored_data = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{SCRIPT_STORAGE_KEY}')",
        key="load_scripts_initial"
    )
    
    if stored_data is not None and stored_data != "null" and stored_data != "":
        try:
            loaded_scripts = json.loads(stored_data)
            if isinstance(loaded_scripts, list):
                st.session_state.saved_scripts = loaded_scripts
                st.session_state.scripts_loaded = True
        except (json.JSONDecodeError, TypeError):
            st.session_state.scripts_loaded = True
    elif stored_data == "null" or stored_data == "":
        st.session_state.scripts_loaded = True


def save_scripts_to_storage():
    """LocalStorageに台本を保存する"""
    if 'saved_scripts' in st.session_state and st.session_state.saved_scripts:
        scripts_json = json.dumps(st.session_state.saved_scripts, ensure_ascii=False)
        escaped_json = scripts_json.replace('\\', '\\\\').replace("'", "\\'")
        streamlit_js_eval(
            js_expressions=f"localStorage.setItem('{SCRIPT_STORAGE_KEY}', '{escaped_json}')",
            key=f"save_scripts_{len(st.session_state.saved_scripts)}_{datetime.now().strftime('%H%M%S')}"
        )


def clear_scripts_storage():
    """台本履歴をクリア"""
    streamlit_js_eval(
        js_expressions=f"localStorage.removeItem('{SCRIPT_STORAGE_KEY}')",
        key=f"clear_scripts_{datetime.now().strftime('%H%M%S')}"
    )


# --- Settings Storage Functions ---

SETTINGS_STORAGE_KEY = "audio_ai_assistant_settings"

def get_default_settings():
    """デフォルト設定を返す"""
    return {
        "broadcaster_name": "",
        "target_audience": "",
        "speaking_style": "親しみやすく",
        "episodes": []
    }


def load_settings_from_storage():
    """LocalStorageから設定を読み込む"""
    if st.session_state.get('settings_loaded', False):
        return
    
    stored_data = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{SETTINGS_STORAGE_KEY}')",
        key="load_settings_initial"
    )
    
    if stored_data is not None and stored_data != "null" and stored_data != "":
        try:
            loaded_settings = json.loads(stored_data)
            if isinstance(loaded_settings, dict):
                st.session_state.user_settings = loaded_settings
                st.session_state.settings_loaded = True
        except (json.JSONDecodeError, TypeError):
            st.session_state.user_settings = get_default_settings()
            st.session_state.settings_loaded = True
    elif stored_data == "null" or stored_data == "":
        st.session_state.user_settings = get_default_settings()
        st.session_state.settings_loaded = True


def save_settings_to_storage():
    """LocalStorageに設定を保存する"""
    if 'user_settings' in st.session_state:
        settings_json = json.dumps(st.session_state.user_settings, ensure_ascii=False)
        escaped_json = settings_json.replace('\\', '\\\\').replace("'", "\\'")
        streamlit_js_eval(
            js_expressions=f"localStorage.setItem('{SETTINGS_STORAGE_KEY}', '{escaped_json}')",
            key=f"save_settings_{datetime.now().strftime('%H%M%S%f')}"
        )


# セッション状態の初期化
if 'history' not in st.session_state:
    st.session_state.history = []

if 'saved_scripts' not in st.session_state:
    st.session_state.saved_scripts = []

if 'viewing_history_index' not in st.session_state:
    st.session_state.viewing_history_index = None

# Apply custom CSS for modern, clean design
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #12121a 100%);
        color: #f0f0f5;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 800px;
    }
    
    /* Headers */
    h1 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em;
    }
    
    h2, h3 {
        font-weight: 600 !important;
        color: #e8e8ed !important;
        letter-spacing: -0.01em;
    }
    
    /* Subtitle text */
    .stMarkdown p {
        color: #9898a6;
        line-height: 1.6;
    }
    
    /* Input Fields */
    .stTextArea textarea, .stTextInput input {
        background-color: #18181f !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #2a2a35 !important;
        padding: 14px !important;
        font-size: 15px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: #18181f;
        border-radius: 12px;
        border: 2px dashed #2a2a35;
        padding: 1.5rem;
    }
    
    .stFileUploader:hover {
        border-color: #6366f1;
    }
    
    /* Primary Buttons */
    .stButton > button[kind="primary"], 
    .stButton > button:not([kind="secondary"]) {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        border: none !important;
        color: white !important;
        padding: 12px 24px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25) !important;
    }
    
    .stButton > button[kind="primary"]:hover,
    .stButton > button:not([kind="secondary"]):hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35) !important;
    }
    
    /* Secondary Buttons */
    .stButton > button[kind="secondary"] {
        background: transparent !important;
        border: 1px solid #3a3a45 !important;
        color: #9898a6 !important;
        padding: 10px 20px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #1f1f28 !important;
        border-color: #6366f1 !important;
        color: #e8e8ed !important;
    }
    
    /* Link buttons */
    .stLinkButton a {
        background: transparent !important;
        border: 1px solid #3a3a45 !important;
        color: #9898a6 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stLinkButton a:hover {
        background: #1f1f28 !important;
        border-color: #6366f1 !important;
        color: #ffffff !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #18181f;
        padding: 4px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        padding: 10px 16px;
        color: #9898a6;
        font-weight: 500;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #6366f1 !important;
        color: white !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #18181f !important;
        border-radius: 10px !important;
        color: #e8e8ed !important;
        font-weight: 500 !important;
    }
    
    .streamlit-expanderContent {
        background-color: #18181f !important;
        border-radius: 0 0 10px 10px !important;
    }
    
    /* Success/Info/Error messages */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 10px !important;
        font-weight: 500 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #12121a !important;
        border-right: 1px solid #1f1f28;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h2 {
        font-size: 1.1rem !important;
        color: #e8e8ed !important;
        margin-bottom: 1rem !important;
    }
    
    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {
        background: #1f1f28 !important;
        border: 1px solid #2a2a35 !important;
        color: #e8e8ed !important;
        font-size: 13px !important;
        padding: 10px 12px !important;
        box-shadow: none !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #2a2a35 !important;
        border-color: #6366f1 !important;
    }
    
    /* Divider */
    hr {
        border-color: #2a2a35 !important;
        margin: 1.5rem 0 !important;
    }
    
    /* Audio player */
    audio {
        width: 100%;
        border-radius: 10px;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #6366f1 !important;
    }
    
    /* Storage badge */
    .storage-badge {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%);
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Caption text */
    .stCaption {
        color: #6b6b78 !important;
    }
</style>
""", unsafe_allow_html=True)


# --- Prompt Templates ---

def get_transcription_prompt():
    """文字起こし用プロンプト"""
    return """
この音声ファイルを文字起こししてください。

【指示】
- 話された内容を一言一句漏らさず書き起こす
- 「えー」「あー」「うーん」などのフィラー（つなぎ言葉）は除去する
- 言い直しや重複は整理して読みやすくする
- 段落分けして見やすく整形する
- 要約はせず、必ず全文を書き起こすこと

【出力形式】
文字起こしのテキストのみを出力してください。余計な説明は不要です。
"""


def get_combined_prompt(transcript):
    """概要欄とタイトルを同時生成するプロンプト（API節約）"""
    return f"""
以下の文字起こしを元に、「概要欄」と「タイトル案3つ」を同時に作成してください。

【文字起こし】
{transcript}

===== 出力形式（この形式を厳守）=====

---DESCRIPTION_START---
▼このチャンネルでは
理学療法士、Webライター、副業、インタビュー企画など、実体験をもとに発信しています。
"今、挑戦している人"の背中を押せるような内容を目指しています。

▪️X（旧Twitter）
https://x.com/kurayota0714

▪️おもろい図鑑
https://omoroi-zukan.jp/

【AI要約】
（ここに整形した文字起こしを出力。話し言葉を残しつつ読みやすく整形。要約ではなく全文を整形。）
---DESCRIPTION_END---

---TITLES_START---
1. タイトル案1（30文字以内、キャッチーに）
2. タイトル案2（30文字以内、キャッチーに）
3. タイトル案3（30文字以内、キャッチーに）
---TITLES_END---
"""


def get_script_prompt(memo, settings, selected_episodes):
    """台本生成用プロンプト"""
    style_guide = {
        "親しみやすく": "フレンドリーで親近感のある話し方。「〜だよね」「〜かな」など。",
        "丁寧に": "敬語を使い、落ち着いた丁寧な話し方。「〜です」「〜ますね」など。",
        "熱血": "情熱的でエネルギッシュな話し方。「絶対に〜！」「〜しようぜ！」など。",
        "毒舌": "ズバッと本音を言う話し方。皮肉やユーモアを交えて。"
    }
    
    style = settings.get("speaking_style", "親しみやすく")
    style_description = style_guide.get(style, style_guide["親しみやすく"])
    
    episodes_text = ""
    if selected_episodes:
        episodes_text = "\n\n【関連エピソード（台本に組み込むこと）】\n"
        for ep in selected_episodes:
            episodes_text += f"・{ep['title']}: {ep['detail']}\n"
    
    broadcaster = settings.get("broadcaster_name", "")
    target = settings.get("target_audience", "")
    
    return f"""
以下のメモを元に、音声配信（5〜7分、約1,500〜2,000文字）用の台本を作成してください。

【配信者情報】
- 名前: {broadcaster if broadcaster else "未設定"}
- ターゲット: {target if target else "一般リスナー"}
- 口調: {style}（{style_description}）

【メモ】
{memo}
{episodes_text}

【台本のルール】
1. Markdownの見出し（##）を必ず使う（オープニング、メインパート、クロージングなど）
2. 箇条書き形式で話すポイントを記載（完全な文章でなくてよい）
3. 1,500〜2,000文字で作成する
4. 関連エピソードがある場合は自然に組み込む
5. 指定された口調で統一する

【出力形式】
## オープニング
- 挨拶
- 今日のテーマ紹介

## メインパート
（内容に応じてセクション分け）

## クロージング
- まとめ
- 次回予告や告知
"""


def add_to_history(titles, description, transcript, filename):
    """履歴に追加する"""
    # タイトル案から最初のタイトルを抽出（表示用）
    first_title = ""
    for line in titles.split('\n'):
        if line.strip().startswith('1.'):
            first_title = line.strip()[2:].strip()
            break
    if not first_title:
        first_title = filename[:20] + "..."
    
    history_item = {
        'datetime': datetime.now().strftime('%Y/%m/%d %H:%M'),
        'display_title': first_title[:30],
        'titles': titles,
        'description': description,
        'transcript': transcript,
        'filename': filename
    }
    
    # 先頭に追加（新しいものが上に来るように）
    st.session_state.history.insert(0, history_item)
    
    # 最大20件まで保持
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[:20]
    
    # LocalStorageに保存
    save_history_to_storage()


def render_sidebar():
    """サイドバーに履歴を表示"""
    with st.sidebar:
        st.markdown("## 📚 生成履歴")
        
        if not st.session_state.history:
            st.markdown("*まだ履歴がありません*")
            st.markdown("音声をアップロードして概要欄を生成すると、ここに履歴が表示されます。")
        else:
            st.markdown(f"*過去{len(st.session_state.history)}件の履歴*")
            
            # 全削除ボタン（上部に配置）
            st.markdown("---")
            if st.button("🗑️ すべての履歴を削除", type="secondary", use_container_width=True):
                st.session_state.history = []
                st.session_state.viewing_history_index = None
                clear_storage()  # LocalStorageもクリア
                if 'description' in st.session_state:
                    del st.session_state.description
                if 'titles' in st.session_state:
                    del st.session_state.titles
                if 'transcript' in st.session_state:
                    del st.session_state.transcript
                st.rerun()
            
            st.markdown("---")
            
            # 各履歴を表示
            for i, item in enumerate(st.session_state.history):
                # 履歴カード
                with st.container():
                    # 履歴を表示するボタン
                    if st.button(
                        f"📄 {item['display_title'][:25]}...\n\n🕐 {item['datetime']}",
                        key=f"history_{i}",
                        use_container_width=True
                    ):
                        st.session_state.viewing_history_index = i
                        # 現在の表示内容を履歴のものに切り替え
                        st.session_state.transcript = item['transcript']
                        st.session_state.description = item['description']
                        st.session_state.titles = item['titles']
                        st.rerun()
                    
                    # 個別削除ボタン（履歴の下に配置）
                    if st.button(
                        "🗑️ この履歴を削除",
                        key=f"delete_{i}",
                        type="secondary",
                        use_container_width=True
                    ):
                        st.session_state.history.pop(i)
                        save_history_to_storage()  # 削除後に保存
                        if st.session_state.viewing_history_index == i:
                            st.session_state.viewing_history_index = None
                        st.rerun()
                    
                    st.markdown("---")


# --- Main App ---

DEFAULT_API_KEY = "AIzaSyASXSSBXpcmZHI6l33plPg5uXJo9iQD0VY"


def render_home():
    """ホーム画面（既存の概要欄作成機能）"""
    st.markdown("### 🏠 概要欄作成")
    st.markdown("音声をアップロードするだけで、Stand.fm用の概要欄を自動生成します。")
    
    # 履歴表示中の通知
    if st.session_state.viewing_history_index is not None:
        st.info(f"📚 履歴を表示中（サイドバーから選択）")
        if st.button("✨ 新規作成に戻る"):
            st.session_state.viewing_history_index = None
            if 'description' in st.session_state:
                del st.session_state.description
            if 'titles' in st.session_state:
                del st.session_state.titles
            if 'transcript' in st.session_state:
                del st.session_state.transcript
            st.rerun()
    
    with st.expander("⚙️ API設定", expanded=False):
        api_key = st.text_input(
            "Google API Key",
            value=DEFAULT_API_KEY,
            type="password",
            placeholder="APIキーを入力",
            key="home_api_key"
        )
        if api_key:
            st.success("✓ APIキー設定済み")
    
    st.markdown("---")
    
    # ファイルアップロード
    st.markdown("### 📁 音声ファイルをアップロード")
    uploaded_file = st.file_uploader(
        "対応形式: mp3, m4a, wav",
        type=['mp3', 'm4a', 'wav'],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.audio(uploaded_file)
    
    # 生成ボタン
    if st.button("🚀 概要欄を生成する", disabled=not uploaded_file):
        if not api_key:
            st.error("APIキーを設定してください。")
            return
        
        try:
            # 一時ファイルに保存
            suffix = "." + uploaded_file.name.split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Gemini API設定
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            
            # Step 1: 文字起こし
            with st.spinner("🎧 音声を文字起こし中..."):
                remote_file = genai.upload_file(tmp_path, mime_type=uploaded_file.type)
                transcript_response = model.generate_content([
                    remote_file,
                    get_transcription_prompt()
                ])
                transcript = transcript_response.text
            
            st.success("✓ 文字起こし完了")
            
            # Step 2: 概要欄 + タイトルを同時生成（API節約）
            with st.spinner("📝 概要欄とタイトルを生成中..."):
                combined_response = model.generate_content(get_combined_prompt(transcript))
                combined_text = combined_response.text
                
                # 結果をパース
                if "---DESCRIPTION_START---" in combined_text and "---DESCRIPTION_END---" in combined_text:
                    description = combined_text.split("---DESCRIPTION_START---")[1].split("---DESCRIPTION_END---")[0].strip()
                else:
                    description = combined_text
                
                if "---TITLES_START---" in combined_text and "---TITLES_END---" in combined_text:
                    titles = combined_text.split("---TITLES_START---")[1].split("---TITLES_END---")[0].strip()
                else:
                    titles = "1. タイトル生成エラー\n2. もう一度お試しください\n3. -"
            
            # 一時ファイル削除
            os.remove(tmp_path)
            
            # 結果をセッションに保存
            st.session_state.transcript = transcript
            st.session_state.description = description
            st.session_state.titles = titles
            
            # 履歴に追加（LocalStorageにも自動保存）
            add_to_history(titles, description, transcript, uploaded_file.name)
            st.session_state.viewing_history_index = None
            
            st.success("✅ 生成完了！サイドバーに履歴が追加されました。")
            
            # ページを再描画してサイドバーを更新
            st.rerun()
            
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "Quota" in err_msg or "Resource has been exhausted" in err_msg:
                st.error("⚠️ API利用制限に達しました")
                st.info("💡 1〜2分待ってから再度お試しください。Gemini無料枠は1分あたりのリクエスト数に制限があります。")
                with st.expander("エラー詳細を確認"):
                    st.code(err_msg)
            else:
                st.error(f"エラーが発生しました: {e}")
            
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    # 結果表示
    if 'description' in st.session_state:
        st.markdown("---")
        
        # タブで結果を表示
        result_tab1, result_tab2, result_tab3 = st.tabs(["📋 概要欄", "🏷️ タイトル案", "📄 文字起こし"])
        
        with result_tab1:
            st.markdown("### 📋 概要欄（編集してコピー）")
            edited_description = st.text_area(
                "description_output",
                value=st.session_state.description,
                height=400,
                label_visibility="collapsed",
                key="editable_description"
            )
            # 編集内容をセッションに保存
            st.session_state.description = edited_description
            
            # 履歴表示中の場合、編集した内容で履歴を更新
            if st.session_state.viewing_history_index is not None:
                idx = st.session_state.viewing_history_index
                if idx < len(st.session_state.history):
                    st.session_state.history[idx]['description'] = edited_description
                    save_history_to_storage()  # 編集を保存
            
            # コピーボタンとスタエフボタンを横並びに
            col1, col2 = st.columns(2)
            with col1:
                # コピーボタン（JavaScriptでクリップボードにコピー）
                if st.button("📋 概要欄をコピー", use_container_width=True, type="primary"):
                    # JavaScriptでクリップボードにコピー
                    escaped_text = edited_description.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
                    streamlit_js_eval(
                        js_expressions=f"navigator.clipboard.writeText(`{escaped_text}`).then(() => true)",
                        key=f"copy_description_{datetime.now().strftime('%H%M%S%f')}"
                    )
                    st.success("✅ コピーしました！")
            
            with col2:
                st.link_button("🚀 スタエフの投稿画面を開く", "https://stand.fm/creator/broadcast/create", use_container_width=True)
        
        with result_tab2:
            st.markdown("### 🏷️ タイトル案")
            st.markdown(st.session_state.titles)
        
        with result_tab3:
            st.markdown("### 📄 文字起こし（参考用）")
            with st.expander("全文を表示", expanded=False):
                st.markdown(st.session_state.transcript)


def render_settings():
    """設定画面"""
    st.markdown("### ⚙️ ユーザー設定")
    st.markdown("配信スタイルやエピソードを保存して、台本作成に活用できます。")
    
    # 設定を読み込み
    if 'user_settings' not in st.session_state:
        st.session_state.user_settings = get_default_settings()
    
    settings = st.session_state.user_settings
    
    st.markdown("---")
    
    # 基本情報
    st.markdown("#### 👤 基本情報")
    
    broadcaster_name = st.text_input(
        "配信者名",
        value=settings.get("broadcaster_name", ""),
        placeholder="例: よーちゃん",
        key="settings_broadcaster"
    )
    
    target_audience = st.text_input(
        "ターゲット層",
        value=settings.get("target_audience", ""),
        placeholder="例: 20〜30代の副業に興味がある会社員",
        key="settings_target"
    )
    
    speaking_style = st.selectbox(
        "話し方の口調",
        options=["親しみやすく", "丁寧に", "熱血", "毒舌"],
        index=["親しみやすく", "丁寧に", "熱血", "毒舌"].index(settings.get("speaking_style", "親しみやすく")),
        key="settings_style"
    )
    
    st.markdown("---")
    
    # エピソード管理
    st.markdown("#### 📖 エピソード管理")
    st.markdown("*台本作成時に、関連するエピソードが自動で選ばれます*")
    
    episodes = settings.get("episodes", [])
    
    # 新しいエピソード追加
    with st.expander("➕ 新しいエピソードを追加", expanded=False):
        new_title = st.text_input("エピソードのタイトル", placeholder="例: 副業で初めて1万円稼いだ話", key="new_ep_title")
        new_detail = st.text_area("詳細", placeholder="どんな経験だったか、学びなどを記載", key="new_ep_detail", height=100)
        
        if st.button("✅ エピソードを追加", key="add_episode"):
            if new_title and new_detail:
                episodes.append({"title": new_title, "detail": new_detail})
                st.session_state.user_settings["episodes"] = episodes
                save_settings_to_storage()
                st.success("エピソードを追加しました！")
                st.rerun()
            else:
                st.warning("タイトルと詳細を入力してください")
    
    # 既存のエピソード表示
    if episodes:
        st.markdown(f"*登録済み: {len(episodes)}件*")
        for i, ep in enumerate(episodes):
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{ep['title']}**")
                    st.caption(ep['detail'][:100] + "..." if len(ep['detail']) > 100 else ep['detail'])
                with col2:
                    if st.button("🗑️", key=f"del_ep_{i}"):
                        episodes.pop(i)
                        st.session_state.user_settings["episodes"] = episodes
                        save_settings_to_storage()
                        st.rerun()
                st.markdown("---")
    else:
        st.info("まだエピソードが登録されていません")
    
    # 保存ボタン
    st.markdown("---")
    if st.button("💾 設定を保存", type="primary", use_container_width=True):
        st.session_state.user_settings = {
            "broadcaster_name": broadcaster_name,
            "target_audience": target_audience,
            "speaking_style": speaking_style,
            "episodes": episodes
        }
        save_settings_to_storage()
        st.success("✅ 設定を保存しました！")


def render_script():
    """台本作成画面"""
    st.markdown("### 📝 台本作成")
    st.markdown("メモを入力すると、設定に基づいた台本を生成します。")
    
    # 設定をチェック
    if 'user_settings' not in st.session_state:
        st.session_state.user_settings = get_default_settings()
    
    settings = st.session_state.user_settings
    
    # 現在の設定を表示
    with st.expander("📋 現在の設定", expanded=False):
        st.markdown(f"- **配信者名**: {settings.get('broadcaster_name') or '未設定'}")
        st.markdown(f"- **ターゲット**: {settings.get('target_audience') or '未設定'}")
        st.markdown(f"- **口調**: {settings.get('speaking_style', '親しみやすく')}")
        st.markdown(f"- **エピソード**: {len(settings.get('episodes', []))}件登録済み")
        st.markdown("*設定を変更するには「⚙️ 設定」タブへ*")
    
    st.markdown("---")
    
    # メモ入力
    memo = st.text_area(
        "📝 話したいことのメモ",
        placeholder="例:\n・今日あった面白い出来事\n・最近読んだ本の感想\n・リスナーからの質問への回答",
        height=200,
        key="script_memo"
    )
    
    # エピソード選択（オプション）
    episodes = settings.get("episodes", [])
    selected_episodes = []
    
    if episodes:
        st.markdown("#### 📖 使用するエピソード（任意）")
        st.caption("選択しない場合、AIが自動で関連エピソードを選びます")
        
        for i, ep in enumerate(episodes):
            if st.checkbox(ep['title'], key=f"use_ep_{i}"):
                selected_episodes.append(ep)
    
    st.markdown("---")
    
    # 生成ボタン
    if st.button("🚀 台本を生成する", disabled=not memo, type="primary", use_container_width=True):
        try:
            genai.configure(api_key=DEFAULT_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            
            with st.spinner("📝 台本を生成中..."):
                # エピソードが選択されていない場合、AIに選んでもらう
                eps_to_use = selected_episodes if selected_episodes else episodes
                
                response = model.generate_content(get_script_prompt(memo, settings, eps_to_use))
                script = response.text
            
            st.session_state.generated_script = script
            st.success("✅ 台本を生成しました！")
            
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "Quota" in err_msg:
                st.error("⚠️ API利用制限に達しました")
                st.info("💡 1〜2分待ってから再度お試しください")
            else:
                st.error(f"エラーが発生しました: {e}")
    
    # 生成結果表示
    if 'generated_script' in st.session_state:
        st.markdown("---")
        st.markdown("### 📄 生成された台本")
        
        # 編集可能なテキストエリア
        edited_script = st.text_area(
            "script_output",
            value=st.session_state.generated_script,
            height=500,
            label_visibility="collapsed",
            key="editable_script"
        )
        
        # 文字数カウント
        char_count = len(edited_script)
        if char_count < 1500:
            st.warning(f"文字数: {char_count}字（目標: 1,500〜2,000字）")
        elif char_count > 2000:
            st.warning(f"文字数: {char_count}字（目標: 1,500〜2,000字）")
        else:
            st.success(f"文字数: {char_count}字 ✓")
        
        # コピーボタンと保存ボタン
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 台本をコピー", type="primary", use_container_width=True):
                escaped_text = edited_script.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
                streamlit_js_eval(
                    js_expressions=f"navigator.clipboard.writeText(`{escaped_text}`).then(() => true)",
                    key=f"copy_script_{datetime.now().strftime('%H%M%S%f')}"
                )
                st.success("✅ コピーしました！")
        
        with col2:
            if st.button("💾 履歴に保存する", use_container_width=True):
                # タイトルを生成（メモの冒頭20文字）
                memo_text = st.session_state.get('script_memo', '')
                title = memo_text[:20] + "..." if len(memo_text) > 20 else memo_text
                if not title:
                    title = "無題の台本"
                
                # 台本を保存
                script_item = {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'content': edited_script,
                    'createdAt': datetime.now().strftime('%Y/%m/%d %H:%M')
                }
                
                st.session_state.saved_scripts.insert(0, script_item)
                
                # 最大20件まで保持
                if len(st.session_state.saved_scripts) > 20:
                    st.session_state.saved_scripts = st.session_state.saved_scripts[:20]
                
                save_scripts_to_storage()
                st.success("✅ 履歴に保存しました！")


def render_script_history():
    """台本履歴ページ"""
    st.markdown("### 📚 保存した台本")
    st.markdown("作成した台本の履歴を確認できます。")
    
    if not st.session_state.saved_scripts:
        st.info("まだ保存された台本がありません。\n\n「📝 台本作成」タブで台本を作成し、「💾 履歴に保存する」ボタンで保存してください。")
        return
    
    st.markdown(f"*保存済み: {len(st.session_state.saved_scripts)}件*")
    
    # 全削除ボタン
    if st.button("🗑️ すべての履歴を削除", type="secondary"):
        st.session_state.saved_scripts = []
        clear_scripts_storage()
        st.rerun()
    
    st.markdown("---")
    
    # 各台本を表示
    for i, script in enumerate(st.session_state.saved_scripts):
        with st.expander(f"📄 {script['title']} ─ {script['createdAt']}", expanded=False):
            # 台本本文を表示
            st.markdown(script['content'])
            
            st.markdown("---")
            
            # ボタン
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📋 コピー", key=f"copy_saved_{i}", use_container_width=True):
                    escaped_text = script['content'].replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
                    streamlit_js_eval(
                        js_expressions=f"navigator.clipboard.writeText(`{escaped_text}`).then(() => true)",
                        key=f"copy_saved_script_{i}_{datetime.now().strftime('%H%M%S%f')}"
                    )
                    st.success("✅ コピーしました！")
            
            with col2:
                if st.button("🗑️ 削除", key=f"delete_saved_{i}", type="secondary", use_container_width=True):
                    st.session_state.saved_scripts.pop(i)
                    save_scripts_to_storage()
                    st.rerun()


def main():
    # LocalStorageから履歴と設定を読み込む
    load_history_from_storage()
    load_settings_from_storage()
    load_saved_scripts()
    
    # サイドバーの履歴を表示
    render_sidebar()
    
    # ヘッダー
    st.title("🎙️ 音声配信AIアシスタント")
    
    # メインナビゲーション（タブ）
    tab_home, tab_script, tab_history, tab_settings = st.tabs(["🏠 ホーム", "📝 台本作成", "📚 履歴", "⚙️ 設定"])
    
    with tab_home:
        render_home()
    
    with tab_script:
        render_script()
    
    with tab_history:
        render_script_history()
    
    with tab_settings:
        render_settings()


if __name__ == "__main__":
    main()

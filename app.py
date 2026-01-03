import streamlit as st
import os
import tempfile
import json
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


# セッション状態の初期化
if 'history' not in st.session_state:
    st.session_state.history = []


if 'viewing_history_index' not in st.session_state:
    st.session_state.viewing_history_index = None

# Apply custom CSS for mobile-friendly design
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Input Fields */
    .stTextArea textarea, .stTextInput input {
        background-color: #1c1f26; 
        color: #ffffff;
        border-radius: 12px;
        border: 1px solid #30363d;
        padding: 15px;
        font-size: 16px;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #4facfe;
        box-shadow: 0 0 0 1px #4facfe;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        font-size: 18px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        font-weight: bold;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
        color: white;
    }
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
    }
    
    /* Card-like container */
    .output-card {
        background-color: #1c1f26;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #30363d;
        margin-top: 15px;
    }
    
    /* Success message */
    .success-box {
        background-color: #1a3d2e;
        border: 1px solid #2ecc71;
        border-radius: 8px;
        padding: 10px 15px;
        margin: 10px 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1c1f26;
        border-radius: 8px;
        padding: 10px 20px;
        border: 1px solid #30363d;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4facfe;
    }
    
    /* Sidebar history items */
    .history-item {
        background-color: #1c1f26;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
        border: 1px solid #30363d;
        cursor: pointer;
        transition: all 0.2s;
    }
    .history-item:hover {
        border-color: #4facfe;
        transform: translateX(2px);
    }
    .history-date {
        color: #888;
        font-size: 12px;
    }
    .history-title {
        color: #fff;
        font-size: 14px;
        font-weight: 500;
        margin-top: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Storage indicator */
    .storage-badge {
        background-color: #1a3d2e;
        color: #2ecc71;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        margin-left: 8px;
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


def get_description_prompt(transcript):
    """概要欄生成用プロンプト"""
    return f"""
以下の文字起こしを元に、Stand.fm用の概要欄を作成してください。

【文字起こし】
{transcript}

【出力ルール】
- まず固定テキスト（チャンネル情報）を出力する
- その後に「【AI要約】」の見出しを入れる
- 文字起こしの内容を、話し言葉を残しつつ読みやすく整形する
- 要約ではなく「整形された文字起こし」に近い形にする
- 重複や言い淀みのみ整理し、内容は削らない

【出力形式】（この形式を厳守）
▼このチャンネルでは
理学療法士、Webライター、副業、インタビュー企画など、実体験をもとに発信しています。
"今、挑戦している人"の背中を押せるような内容を目指しています。

▪️X（旧Twitter）
https://x.com/kurayota0714

▪️おもろい図鑑
https://omoroi-zukan.jp/

【AI要約】
（ここに整形した文字起こしを出力）
"""


def get_title_prompt(transcript):
    """タイトル生成用プロンプト"""
    return f"""
以下の文字起こしを元に、Stand.fm配信用のタイトルを3つ提案してください。

【文字起こし】
{transcript}

【ルール】
- 各タイトルは30文字以内
- リスナーが興味を持つキャッチーな表現
- 内容の核心を突いたもの

【出力形式】
1. タイトル案1
2. タイトル案2
3. タイトル案3
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
        st.markdown('<span class="storage-badge">💾 永続保存</span>', unsafe_allow_html=True)
        st.caption("ブラウザに保存されます")
        
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

def main():
    # LocalStorageから履歴を読み込む
    load_history_from_storage()
    
    # サイドバーの履歴を表示
    render_sidebar()
    
    st.title("🎙️ 音声配信AIアシスタント")
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
    
    # API Key設定
    with st.expander("⚙️ API設定", expanded=False):
        env_google_key = os.getenv("GOOGLE_API_KEY")
        try:
            if not env_google_key and "GOOGLE_API_KEY" in st.secrets:
                env_google_key = st.secrets["GOOGLE_API_KEY"]
        except Exception:
            pass
        
        api_key = st.text_input(
            "Google API Key",
            value=env_google_key if env_google_key else "",
            type="password",
            placeholder="APIキーを入力"
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
            model = genai.GenerativeModel("gemini-2.0-flash-lite")
            
            # Step 1: 文字起こし
            with st.spinner("🎧 音声を文字起こし中..."):
                remote_file = genai.upload_file(tmp_path, mime_type=uploaded_file.type)
                transcript_response = model.generate_content([
                    remote_file,
                    get_transcription_prompt()
                ])
                transcript = transcript_response.text
            
            st.success("✓ 文字起こし完了")
            
            # Step 2: 概要欄生成
            with st.spinner("📝 概要欄を生成中..."):
                description_response = model.generate_content(get_description_prompt(transcript))
                description = description_response.text
            
            # Step 3: タイトル生成
            with st.spinner("✨ タイトルを生成中..."):
                title_response = model.generate_content(get_title_prompt(transcript))
                titles = title_response.text
            
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
        tab1, tab2, tab3 = st.tabs(["📋 概要欄", "🏷️ タイトル案", "📄 文字起こし"])
        
        with tab1:
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
        
        with tab2:
            st.markdown("### 🏷️ タイトル案")
            st.markdown(st.session_state.titles)
        
        with tab3:
            st.markdown("### 📄 文字起こし（参考用）")
            with st.expander("全文を表示", expanded=False):
                st.markdown(st.session_state.transcript)


if __name__ == "__main__":
    main()

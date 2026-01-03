import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="音声配信AIアシスタント",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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


# --- Main App ---

def main():
    st.title("🎙️ 音声配信AIアシスタント")
    st.markdown("音声をアップロードするだけで、Stand.fm用の概要欄を自動生成します。")
    
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
            model = genai.GenerativeModel("models/gemini-2.5-flash")
            
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
            
            st.success("✅ 生成完了！")
            
            # 結果をセッションに保存
            st.session_state.transcript = transcript
            st.session_state.description = description
            st.session_state.titles = titles
            
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
            st.link_button("🚀 スタエフの投稿画面を開く", "https://stand.fm/creator/broadcast/create")
        
        with tab2:
            st.markdown("### 🏷️ タイトル案")
            st.markdown(st.session_state.titles)
        
        with tab3:
            st.markdown("### 📄 文字起こし（参考用）")
            with st.expander("全文を表示", expanded=False):
                st.markdown(st.session_state.transcript)


if __name__ == "__main__":
    main()

import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
import google.generativeai as genai
# from standfm_uploader import StandfmUploader

# Load environment variables
load_dotenv()

# Set page configuration safely as the first command
st.set_page_config(
    page_title="音声配信AIアシスタント",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for mobile-friendly and premium feel
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

    /* Radio Buttons */
    .stRadio > div {
        background-color: #1c1f26;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #30363d;
    }
    
    /* Buttons */
    .stButton > button {
        width: 100%;
        background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
        border: none;
        color: white;
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
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
    
    /* Card-like container for output */
    .output-container {
        background-color: #1c1f26;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #30363d;
        margin-top: 20px;
        height: 100%;
    }
    
    /* Custom columns layout hack if needed */
    div[data-testid="column"] {
        background-color: #161920;
        border-radius: 12px;
        padding: 10px;
        border: 1px solid #262a33;
    }
</style>
""", unsafe_allow_html=True)

# --- Logic Functions ---

def get_script_prompt(memo):
    return f"""
あなたはロジカルで話上手なStand.fm配信者です。
私の【メモ】をもとに、PREP法に基づいた「話すための骨組み（箇条書き）」を作成してください。

# 制約事項
- **文章にはしないこと**。
- 読み上げ原稿ではなく、話す内容を思い出すための「キーワード」や「短いフレーズ」で出力すること。

# 出力フォーマット

## タイトル案（3つ）
・

## 1. Point（結論・今日のテーマ）
※冒頭でリスナーに伝える「聴くメリット」や「主張」
・

## 2. Reason（理由）
※なぜそう言えるのか？
・
・

## 3. Example（具体例・体験談）
※私のメモにあるエピソードや、リスナーの日常に当てはめた例
・
・

## 4. Point（まとめ・アクション）
※再度結論を伝え、リスナーにどうしてほしいか（コメント、実験など）を促す
・まとめ：
・アクション（問いかけ）：

---
【メモ】
{memo}
"""

def get_converter_prompt(transcript):
    return f"""
あなたは熟練のコンテンツエディターです。
以下の【音声書き起こし】を元に、3種類のコンテンツを作成し、指定されたフォーマットで出力してください。

【音声書き起こしコンテキスト】
{transcript}

【出力要件】
1. **ブログ記事風**: 
   - 話し言葉を丁寧な「です・ます調」の書き言葉にリライト。
   - 適切な見出し（H2）をつけて構造化する。
   - 魅力的なタイトルをつける。
2. **X（Twitter）投稿**: 
   - 内容のハイライトを抽出。
   - 絵文字を適度に使用。
   - 箇条書きなどを活用し140文字程度にまとめる。
   - ハッシュタグを2-3個つける。
4. **スタエフ用タイトル**: 
   - 音声配信のキャッチーなタイトル（30文字以内）。
5. **スタエフ用概要欄**: 
   - 音声の内容を要約した、配信の概要欄に載せるテキスト（ハッシュタグ付き）。

【出力フォーマット】
必ず以下のセパレーターを使って5つのセクションを明確に分けて出力してください。

### BLOG_START
（ここにブログ記事を出力）
### BLOG_END

### X_START
（ここにX投稿を出力）
### X_END

### SUMMARY_START
（ここに要約を出力）
### SUMMARY_END

### STANDFM_TITLE_START
（ここにスタエフ用タイトルを出力）
### STANDFM_TITLE_END

### STANDFM_DESC_START
（ここにスタエフ用概要欄を出力）
### STANDFM_DESC_END
"""

def get_gemini_audio_prompt():
    return """
この音声ファイルを解析してください。以下の形式で出力してください。

1. 【文字起こし】: 音声の内容を一言一句漏らさず、ただし「えー」「あー」などの不要な言葉（フィラー）は除いて読みやすく整形した全文書き起こし。
   ※重要：要約はせず、必ず話された内容をすべて書き起こしてください。途中で省略することは許されません。
2. 【ブログ記事】: 音声の内容を元にした、読みやすいブログ記事（タイトルと見出し付き）
3. 【SNS投稿】: 音声の要点をまとめた140文字以内の投稿文
4. 【スタエフ用タイトル】: 音声配信のキャッチーなタイトル（30文字以内）
5. 【スタエフ用概要欄】: 以下の「出力ルール」に従って作成された概要欄テキスト

# 【スタエフ用概要欄】出力ルール
・構成は必ず以下の順番を守る
・文章は話し言葉を残しつつ、読みやすく整える
・内容の削除はせず、重複や言い淀みのみ整理する
・要約ではなく「整形された全文文字起こし」に近い形にする
・見出し名は必ず指定どおりに使う
・余計な解説や前置きは一切書かない

# 固定で入れる文章（そのまま使用）
▼このチャンネルでは
理学療法士、Webライター、副業、インタビュー企画など、実体験をもとに発信しています。
“今、挑戦している人”の背中を押せるような内容を目指しています。

▪️X（旧Twitter）
https://x.com/kurayota0903

▪️おもろい図鑑
https://omoroi-zukan.jp/

# 【スタエフ用概要欄】出力形式（厳守）
【AI要約】
（ここに文字起こしを、読みやすく整形した文章を出力する）

（その下に固定で入れる文章を続ける）
"""

def call_ai_model(prompt, api_key):
    genai.configure(api_key=api_key)
    # Using gemini-flash-latest as per recent update
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content(prompt)
    return response.text



# --- Page Render Functions ---

def render_script_maker(api_key):
    st.title("🎙️ 台本メーカー (Script Maker)")
    st.markdown("断片的なメモから、PREP法に基づいたトーク構成を生成します。")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📝 今日のメモ")
        memo = st.text_area(
            "話したいこと、キーワードなどを入力",
            height=200,
            placeholder="例：\n- 朝の時間を有効活用したい\n- 早起きは三文の徳っていうけど実際どう？"
        )

    with col2:
        st.markdown("### ⚙️ オプション")
        # Currently the prompt is fixed strictly to PREP as per latest request, 
        # so we don't show pattern selection to avoid confusion, or we can leave it as dummy.
        st.info("現在は「ロジカル（PREP法）」モードで固定されています。")
        
        generate_btn = st.button("✨ 台本を生成")

    if generate_btn:
        if not memo:
            st.warning("メモを入力してください。")
        elif not api_key:
            st.error("APIキーが設定されていません。サイドバーを確認してください。")
        else:
            with st.spinner("AIが構成を考えています..."):
                try:

                    prompt = get_script_prompt(memo)
                    result = call_ai_model(prompt, api_key)
                    
                    st.success("生成完了！")
                    st.markdown('<div class="output-container">', unsafe_allow_html=True)
                    st.markdown(result)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("### 📋 コピー用")
                    st.text_area("コピー用テキスト", value=result, height=200)
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

def render_content_converter(api_key):
    st.title("🔄 コンテンツ変換 (Repurposing)")
    st.markdown("収録した音声を「ブログ」「SNS」「要約」に自動変換します。")

    uploaded_file = st.file_uploader("音声ファイルをアップロード (mp3, m4a, wav)", type=['mp3', 'm4a', 'wav'])

    # Initialize session state for generated content if not present
    if 'gen_transcript' not in st.session_state: st.session_state.gen_transcript = ""
    if 'gen_blog' not in st.session_state: st.session_state.gen_blog = ""
    if 'gen_sns' not in st.session_state: st.session_state.gen_sns = ""
    if 'gen_standfm_title' not in st.session_state: st.session_state.gen_standfm_title = ""
    if 'gen_standfm_desc' not in st.session_state: st.session_state.gen_standfm_desc = ""
    if 'generated_raw' not in st.session_state: st.session_state.generated_raw = ""

    if st.button("🚀 変換を開始する"):
        if not uploaded_file:
            st.warning("音声ファイルをアップロードしてください。")
            return
        
        if not api_key:
            st.error("Google API Keyが設定されていません。サイドバーで設定してください。")
            return
        
        try:
            # 1. Save to temp file
            suffix = "." + uploaded_file.name.split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name

            # 2. Upload to Gemini & Generate
            with st.spinner("AIが音声を聴いています..."):
                genai.configure(api_key=api_key)
                
                # Upload file
                remote_file = genai.upload_file(tmp_path, mime_type=uploaded_file.type)
                
                # Generate
                model = genai.GenerativeModel("gemini-flash-latest")
                prompt = get_gemini_audio_prompt()
                
                response = model.generate_content([remote_file, prompt])
                try:
                    generated_text = response.text
                except ValueError:
                    st.warning("AIからの応答が制限された可能性があります（Safety Filter等）。自動投稿処理を継続するため、ダミーテキストを使用します。")
                    generated_text = """
【文字起こし】
（生成不可）
【ブログ記事】
（生成不可）
【SNS投稿】
（生成不可）
【スタエフ用タイトル】
AI生成エラー
【スタエフ用概要欄】
AIの応答生成に失敗しました。
"""
                
                # Cleanup temp file (Delete immediately as we re-create it if needed for upload)
                os.remove(tmp_path)
                
                st.success("生成完了！")
                
                # Attempt to parse specific sections using checks
                # Format: 1. 【文字起こし】... 2. 【ブログ記事】... 3. 【SNS投稿】...
                
                # Use regex to find sections
                import re
                
                # Initialize parts
                transcript_part = ""
                blog_part = ""
                sns_part = ""
                standfm_title = ""
                standfm_desc = ""
                
                # Regex strategies
                match_transcript = re.search(r"【文字起こし】[:：]?\s*(.*?)(?=\n.*?【ブログ記事】|\Z)", generated_text, re.DOTALL)
                match_blog = re.search(r"【ブログ記事】[:：]?\s*(.*?)(?=\n.*?【SNS投稿】|\Z)", generated_text, re.DOTALL)
                match_sns = re.search(r"【SNS投稿】[:：]?\s*(.*?)(?=\n.*?【スタエフ用タイトル】|\Z)", generated_text, re.DOTALL)
                match_title = re.search(r"【スタエフ用タイトル】[:：]?\s*(.*?)(?=\n.*?【スタエフ用概要欄】|\Z)", generated_text, re.DOTALL)
                match_desc = re.search(r"【スタエフ用概要欄】[:：]?\s*(.*?)(?=$|\Z)", generated_text, re.DOTALL)
                
                if match_transcript: transcript_part = match_transcript.group(1).strip()
                if match_blog: blog_part = match_blog.group(1).strip()
                if match_sns: sns_part = match_sns.group(1).strip()
                if match_title: standfm_title = match_title.group(1).strip()
                if match_desc: standfm_desc = match_desc.group(1).strip()
                
                # Save to session state
                st.session_state.gen_transcript = transcript_part
                st.session_state.gen_blog = blog_part
                st.session_state.gen_sns = sns_part
                st.session_state.gen_standfm_title = standfm_title
                st.session_state.gen_standfm_desc = standfm_desc
                st.session_state.generated_raw = generated_text

        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "Quota exceeded" in err_msg:
                st.error("⚠️ AIモデルの利用制限（429 Quota Exceeded）に達しました。")
                st.warning("Google Gemini API（無料枠）の短時間利用制限にかかっています。約1分ほど待ってから、再度「変換を開始する」ボタンを押してください。")
            else:
                st.error(f"エラーが発生しました: {e}")
            
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Display Results if available
    if st.session_state.generated_raw:
        st.success("生成完了！")
        
        # Transcript
        with st.expander("文字起こしテキストを確認する", expanded=False):
            st.markdown(st.session_state.gen_transcript if st.session_state.gen_transcript else "（解析できませんでした）")
                
        col1, col2 = st.columns(2)
        with col1:
             st.info("📝 ブログ記事が生成されました")
             st.caption("サイドバーの「ブログ記事編集」で確認・編集できます。")
        with col2:
             st.info("📱 SNS投稿が生成されました")
             st.caption("サイドバーの「SNS投稿編集」で確認・編集できます。")

        # Stand.fm Support Area (Auto or Manual)
        st.markdown("---")
        st.subheader("🎙️ スタエフ投稿サポート")
        
        st.caption("AIが作成した以下の内容を編集し、コピーして使用してください。")

        st.markdown("##### タイトル (編集可能)")
        st.text_input("title_edit", value=st.session_state.gen_standfm_title, key="edited_title", label_visibility="collapsed")

        st.markdown("##### 概要欄 (編集可能)")
        st.text_area("desc_edit", value=st.session_state.gen_standfm_desc, height=300, key="edited_desc", label_visibility="collapsed")

        st.link_button("🚀 スタエフの投稿画面を開く", "https://stand.fm/creator/broadcast/create")

# --- Main App ---

# --- New Editor Pages ---

def render_blog_editor():
    st.title("📝 ブログ記事編集")
    
    if 'gen_blog' not in st.session_state or not st.session_state.gen_blog:
        st.info("まずは「コンテンツ変換」ページで音声を変換してください。")
        return

    st.markdown("生成されたブログ記事を編集・プレビューできます。")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("編集")
        # Update session state on change
        edited_blog = st.text_area("Blog Editor", value=st.session_state.gen_blog, height=600, label_visibility="collapsed")
        st.session_state.gen_blog = edited_blog
        
    with col2:
        st.subheader("プレビュー")
        st.markdown('<div class="output-container" style="height:600px; overflow-y:auto;">' + st.session_state.gen_blog + '</div>', unsafe_allow_html=True)

def render_sns_editor():
    st.title("📱 SNS投稿編集")
    
    if 'gen_sns' not in st.session_state or not st.session_state.gen_sns:
        st.info("まずは「コンテンツ変換」ページで音声を変換してください。")
        return

    st.markdown("生成されたSNS投稿を編集・プレビューできます。")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("編集")
        edited_sns = st.text_area("SNS Editor", value=st.session_state.gen_sns, height=400, label_visibility="collapsed")
        st.session_state.gen_sns = edited_sns
        st.caption(f"現在の文字数: {len(edited_sns)}")
        
    with col2:
        st.subheader("プレビュー")
        st.info(st.session_state.gen_sns)


# --- Main App ---

def main():
    st.sidebar.title("Audio AI Tools")
    
    # Navigation
    page = st.sidebar.radio("機能を選択", ["台本メーカー", "コンテンツ変換", "ブログ記事編集", "SNS投稿編集"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("---")
    st.sidebar.header("API設定")
    
    # Get Keys from Env
    # Check both env and st.secrets for Google Key as per instructions
    env_google_key = os.getenv("GOOGLE_API_KEY")
    if not env_google_key and "GOOGLE_API_KEY" in st.secrets:
        env_google_key = st.secrets["GOOGLE_API_KEY"]
    
    google_key_input = st.sidebar.text_input(
        "Google API Key",
        value=env_google_key if env_google_key else "",
        type="password",
        placeholder="必須"
    )
    
    st.sidebar.markdown("---")
    
    if page == "台本メーカー":
        render_script_maker(google_key_input)
    elif page == "コンテンツ変換":
        render_content_converter(google_key_input)
    elif page == "ブログ記事編集":
        render_blog_editor()
    elif page == "SNS投稿編集":
        render_sns_editor()

if __name__ == "__main__":
    main()

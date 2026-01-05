"""
ホーム画面（概要欄作成）
"""
import streamlit as st
import os
import tempfile
import uuid
from datetime import datetime
import google.generativeai as genai
from streamlit_js_eval import streamlit_js_eval

from config import DEFAULT_API_KEY, GEMINI_MODEL
from storage import add_to_history, save_transcriptions_to_storage
from prompts import get_transcription_prompt, get_combined_prompt


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
            suffix = "." + uploaded_file.name.split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            with st.spinner("🎧 音声を文字起こし中..."):
                remote_file = genai.upload_file(tmp_path, mime_type=uploaded_file.type)
                transcript_response = model.generate_content([
                    remote_file,
                    get_transcription_prompt()
                ])
                transcript = transcript_response.text
            
            st.success("✓ 文字起こし完了")
            
            with st.spinner("📝 概要欄とタイトルを生成中..."):
                combined_response = model.generate_content(get_combined_prompt(transcript))
                combined_text = combined_response.text
                
                if "---DESCRIPTION_START---" in combined_text and "---DESCRIPTION_END---" in combined_text:
                    description = combined_text.split("---DESCRIPTION_START---")[1].split("---DESCRIPTION_END---")[0].strip()
                else:
                    description = combined_text
                
                if "---TITLES_START---" in combined_text and "---TITLES_END---" in combined_text:
                    titles = combined_text.split("---TITLES_START---")[1].split("---TITLES_END---")[0].strip()
                else:
                    titles = "1. タイトル生成エラー\n2. もう一度お試しください\n3. -"
            
            os.remove(tmp_path)
            
            st.session_state.transcript = transcript
            st.session_state.description = description
            st.session_state.titles = titles
            
            add_to_history(titles, description, transcript, uploaded_file.name)
            st.session_state.viewing_history_index = None
            
            # 文字起こしデータにも自動登録
            first_title = ""
            for line in titles.split('\n'):
                if line.strip().startswith('1.'):
                    first_title = line.strip()[2:].strip()
                    break
            if not first_title:
                first_title = uploaded_file.name[:30]
            
            trans_item = {
                'id': str(uuid.uuid4()),
                'title': first_title,
                'date': datetime.now().strftime('%Y/%m/%d'),
                'content': transcript,
                'tags': []
            }
            st.session_state.transcriptions.insert(0, trans_item)
            if len(st.session_state.transcriptions) > 20:
                st.session_state.transcriptions = st.session_state.transcriptions[:20]
            save_transcriptions_to_storage()
            
            st.success("✅ 生成完了！文字起こしが自動登録され、台本作成に活用できます。")
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
            st.session_state.description = edited_description
            
            if st.session_state.viewing_history_index is not None:
                idx = st.session_state.viewing_history_index
                if idx < len(st.session_state.history):
                    st.session_state.history[idx]['description'] = edited_description
                    from storage import save_history_to_storage
                    save_history_to_storage()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 概要欄をコピー", use_container_width=True, type="primary"):
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

"""
台本作成画面
"""
import streamlit as st
import uuid
from datetime import datetime
import google.generativeai as genai
from streamlit_js_eval import streamlit_js_eval

from config import DEFAULT_API_KEY, GEMINI_MODEL, get_default_settings
from storage import save_scripts_to_storage
from prompts import search_relevant_transcriptions, get_script_prompt_with_transcriptions


def render_script():
    """台本作成画面"""
    st.markdown("### 📝 台本作成")
    st.markdown("メモを入力すると、過去の文字起こしを参考に台本を生成します。")
    
    if 'user_settings' not in st.session_state:
        st.session_state.user_settings = get_default_settings()
    
    settings = st.session_state.user_settings
    
    with st.expander("📋 現在の設定", expanded=False):
        st.markdown(f"- **配信者名**: {settings.get('broadcaster_name') or '未設定'}")
        st.markdown(f"- **ターゲット**: {settings.get('target_audience') or '未設定'}")
        st.markdown(f"- **口調**: {settings.get('speaking_style', '親しみやすく')}")
        trans_count = len(st.session_state.get('transcriptions', []))
        st.markdown(f"- **文字起こしデータ**: {trans_count}件登録済み")
        st.markdown("*設定を変更するには「⚙️ 設定」タブへ*")
    
    st.markdown("---")
    
    memo = st.text_area(
        "📝 話したいことのメモ",
        placeholder="例:\n・今日あった面白い出来事\n・最近読んだ本の感想\n・リスナーからの質問への回答",
        height=200,
        key="script_memo"
    )
    
    transcriptions = st.session_state.get('transcriptions', [])
    if transcriptions:
        with st.expander(f"📄 参照される文字起こしデータ（{len(transcriptions)}件）", expanded=False):
            st.caption("メモのキーワードに基づいて、最大2件の文字起こしが自動選択されます")
            for trans in transcriptions[:5]:
                st.markdown(f"- **{trans.get('title', '無題')}** ({trans.get('date', '')})")
    else:
        st.info("💡 「📄 文字起こし」タブで過去の放送を登録すると、あなたの口調を模倣した台本が生成されます")
    
    st.markdown("---")
    
    if st.button("🚀 台本を生成する", disabled=not memo, type="primary", use_container_width=True):
        try:
            genai.configure(api_key=DEFAULT_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            with st.spinner("📝 台本を生成中..."):
                relevant_transcriptions = search_relevant_transcriptions(
                    memo, 
                    st.session_state.get('transcriptions', []),
                    max_results=2
                )
                
                if relevant_transcriptions:
                    st.session_state.used_transcriptions = [t.get('title', '無題') for t in relevant_transcriptions]
                
                response = model.generate_content(
                    get_script_prompt_with_transcriptions(memo, settings, relevant_transcriptions)
                )
                script = response.text
            
            st.session_state.generated_script = script
            
            if relevant_transcriptions:
                st.success(f"✅ 台本を生成しました！（参照: {', '.join(st.session_state.used_transcriptions)}）")
            else:
                st.success("✅ 台本を生成しました！")
            
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "Quota" in err_msg:
                st.error("⚠️ API利用制限に達しました")
                st.info("💡 1〜2分待ってから再度お試しください")
            else:
                st.error(f"エラーが発生しました: {e}")
    
    if 'generated_script' in st.session_state:
        st.markdown("---")
        st.markdown("### 📄 生成された台本")
        
        edited_script = st.text_area(
            "script_output",
            value=st.session_state.generated_script,
            height=500,
            label_visibility="collapsed",
            key="editable_script"
        )
        
        char_count = len(edited_script)
        if char_count < 1500:
            st.warning(f"文字数: {char_count}字（目標: 1,500〜2,000字）")
        elif char_count > 2000:
            st.warning(f"文字数: {char_count}字（目標: 1,500〜2,000字）")
        else:
            st.success(f"文字数: {char_count}字 ✓")
        
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
                memo_text = st.session_state.get('script_memo', '')
                title = memo_text[:20] + "..." if len(memo_text) > 20 else memo_text
                if not title:
                    title = "無題の台本"
                
                script_item = {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'content': edited_script,
                    'createdAt': datetime.now().strftime('%Y/%m/%d %H:%M')
                }
                
                st.session_state.saved_scripts.insert(0, script_item)
                
                if len(st.session_state.saved_scripts) > 20:
                    st.session_state.saved_scripts = st.session_state.saved_scripts[:20]
                
                save_scripts_to_storage()
                st.success("✅ 履歴に保存しました！")

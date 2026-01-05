"""
LocalStorage 操作関連の関数
注意: streamlit_js_evalは固定キーを使用すること（動的キーは無限ループの原因）
"""
import streamlit as st
import json
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

from config import (
    STORAGE_KEY,
    SCRIPT_STORAGE_KEY,
    TRANSCRIPTION_STORAGE_KEY,
    SETTINGS_STORAGE_KEY,
    get_default_settings
)


# =============================================================================
# History Storage
# =============================================================================

def load_history_from_storage():
    """LocalStorageから履歴を読み込む（初回のみ）"""
    if st.session_state.get('history_loaded', False):
        return
    
    # 固定キーを使用
    stored_data = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{STORAGE_KEY}')",
        key="load_history_fixed"
    )
    
    # None = JSがまだ実行されていない → 次のリロードを待つ
    if stored_data is None:
        return
    
    # "null" or "" = LocalStorageが空 → フラグを立てて終了
    if stored_data == "null" or stored_data == "":
        st.session_state.history_loaded = True
        return
    
    # データがある場合は読み込み
    try:
        loaded_history = json.loads(stored_data)
        if isinstance(loaded_history, list):
            st.session_state.history = loaded_history
    except (json.JSONDecodeError, TypeError):
        pass
    
    st.session_state.history_loaded = True


def save_history_to_storage():
    """LocalStorageに履歴を保存する"""
    if 'history' in st.session_state and st.session_state.history:
        history_json = json.dumps(st.session_state.history, ensure_ascii=False)
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


# =============================================================================
# Script Storage
# =============================================================================

def load_saved_scripts():
    """LocalStorageから台本を読み込む（初回のみ）"""
    if st.session_state.get('scripts_loaded', False):
        return
    
    stored_data = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{SCRIPT_STORAGE_KEY}')",
        key="load_scripts_fixed"
    )
    
    if stored_data is None:
        return
    
    if stored_data == "null" or stored_data == "":
        st.session_state.scripts_loaded = True
        return
    
    try:
        loaded_scripts = json.loads(stored_data)
        if isinstance(loaded_scripts, list):
            st.session_state.saved_scripts = loaded_scripts
    except (json.JSONDecodeError, TypeError):
        pass
    
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


# =============================================================================
# Transcription Storage
# =============================================================================

def load_transcriptions():
    """LocalStorageから文字起こしを読み込む（初回のみ）"""
    if st.session_state.get('transcriptions_loaded', False):
        return
    
    stored_data = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{TRANSCRIPTION_STORAGE_KEY}')",
        key="load_transcriptions_fixed"
    )
    
    if stored_data is None:
        return
    
    if stored_data == "null" or stored_data == "":
        st.session_state.transcriptions_loaded = True
        return
    
    try:
        loaded_transcriptions = json.loads(stored_data)
        if isinstance(loaded_transcriptions, list):
            st.session_state.transcriptions = loaded_transcriptions
    except (json.JSONDecodeError, TypeError):
        pass
    
    st.session_state.transcriptions_loaded = True


def save_transcriptions_to_storage():
    """LocalStorageに文字起こしデータを保存する"""
    if 'transcriptions' in st.session_state and st.session_state.transcriptions:
        transcriptions_json = json.dumps(st.session_state.transcriptions, ensure_ascii=False)
        escaped_json = transcriptions_json.replace('\\', '\\\\').replace("'", "\\'")
        streamlit_js_eval(
            js_expressions=f"localStorage.setItem('{TRANSCRIPTION_STORAGE_KEY}', '{escaped_json}')",
            key=f"save_transcriptions_{len(st.session_state.transcriptions)}_{datetime.now().strftime('%H%M%S')}"
        )


def clear_transcriptions_storage():
    """文字起こしデータをクリア"""
    streamlit_js_eval(
        js_expressions=f"localStorage.removeItem('{TRANSCRIPTION_STORAGE_KEY}')",
        key=f"clear_transcriptions_{datetime.now().strftime('%H%M%S')}"
    )


# =============================================================================
# Settings Storage
# =============================================================================

def load_settings_from_storage():
    """LocalStorageから設定を読み込む（初回のみ）"""
    if st.session_state.get('settings_loaded', False):
        return
    
    stored_data = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{SETTINGS_STORAGE_KEY}')",
        key="load_settings_fixed"
    )
    
    if stored_data is None:
        return
    
    if stored_data == "null" or stored_data == "":
        st.session_state.user_settings = get_default_settings()
        st.session_state.settings_loaded = True
        return
    
    try:
        loaded_settings = json.loads(stored_data)
        if isinstance(loaded_settings, dict):
            st.session_state.user_settings = loaded_settings
    except (json.JSONDecodeError, TypeError):
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


# =============================================================================
# Helper Functions
# =============================================================================

def add_to_history(titles, description, transcript, filename):
    """履歴に追加する"""
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
    
    st.session_state.history.insert(0, history_item)
    
    if len(st.session_state.history) > 20:
        st.session_state.history = st.session_state.history[:20]
    
    save_history_to_storage()


def init_session_state():
    """セッション状態の初期化"""
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    if 'saved_scripts' not in st.session_state:
        st.session_state.saved_scripts = []
    
    if 'transcriptions' not in st.session_state:
        st.session_state.transcriptions = []
    
    if 'viewing_history_index' not in st.session_state:
        st.session_state.viewing_history_index = None


def load_all_data():
    """全データをLocalStorageから読み込む"""
    load_history_from_storage()
    load_settings_from_storage()
    load_saved_scripts()
    load_transcriptions()

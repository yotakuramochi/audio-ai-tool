# 音声配信AIアシスタント

音声ファイルから概要欄・台本を自動生成するStreamlitアプリ

## 機能

- 🏠 **ホーム**: 音声アップロード → 概要欄 + タイトル案生成
- 📝 **台本作成**: メモから台本生成（過去の文字起こしを参考に）
- 📄 **文字起こし**: 過去の放送データをインポート
- 📚 **履歴**: 保存した台本の管理
- ⚙️ **設定**: 配信者情報・エピソード管理

## 技術スタック

- **フロントエンド**: Streamlit
- **AI**: Google Gemini (gemini-2.0-flash-exp)
- **ストレージ**: ブラウザ LocalStorage

## ファイル構成

```
.
├── app.py              # メインエントリーポイント
├── config.py           # 設定・定数・CSS
├── storage.py          # LocalStorage関連の関数
├── prompts.py          # AIプロンプトテンプレート
├── components/
│   ├── __init__.py
│   ├── sidebar.py      # サイドバー
│   ├── home.py         # ホーム画面
│   ├── script.py       # 台本作成
│   ├── transcriptions.py  # 文字起こし管理
│   └── settings.py     # 設定画面
├── requirements.txt
├── .env
└── README.md
```

## セットアップ

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 環境変数

`.env` ファイルに以下を設定:

```
GOOGLE_API_KEY=your_api_key_here
```

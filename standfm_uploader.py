import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StandfmUploader:
    def __init__(self, email, password, headless=False):
        self.email = email
        self.password = password
        self.headless = headless
        self.driver = None

    def _setup_driver(self):
        options = Options()
        # ブラウザを閉じないようにするオプション（最優先）
        options.add_experimental_option("detach", True)

        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1280,1080')
        
        # 自動化検知回避のためのオプション
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def login(self):
        try:
            if not self.driver:
                self._setup_driver()

            logger.info("Accessing Stand.fm top page...")
            self.driver.get("https://stand.fm/")

            # Step 0: Click "Sign up / Login" from top page header
            # 画像によると右上に「新規登録・ログイン」ボタンがある。
            # テキストの前後に空白がある可能性や、タグがa/button/divのどれか不明なため、広めに検索する。
            wait = WebDriverWait(self.driver, 15)
            try:
                 logger.info("Looking for 'Sign up / Login' button...")
                 # テキストを含む要素を探す（タグ指定なし）
                 header_login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '新規登録・ログイン')]")))
                 
                 logger.info("Button found. Clicking...")
                 # 通常のclickで反応しない場合があるため、JavaScriptで強制クリック
                 self.driver.execute_script("arguments[0].click();", header_login_btn)
                 
                 time.sleep(3) # モーダル/遷移のアニメーション待機
            except Exception as e:
                 logger.warning(f"Header login button not found or clickable: {e}")
                 # 既に見つからない場合でも、次のステップでリカバリできる可能性があるため続行
                 # （すでにログイン済みの場合など）

            # Step 1: Click "Login with Email"
            # Step 1: Click "Login with Email"
            # すでにフォームが表示されているか確認
            try:
                # 短いタイムアウトでフォームを探す
                wait_short = WebDriverWait(self.driver, 3)
                wait_short.until(EC.presence_of_element_located((By.NAME, "email")))
                logger.info("Login form already visible. Skipping 'Login with Email' button click.")
            except Exception:
                # フォームが見つからない場合のみボタンを探す
                try:
                    logger.info("Looking for 'Login with Email' button...")
                    mail_login_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'メールアドレスでログイン')] | //div[contains(text(), 'メールアドレスでログイン')] | //span[contains(text(), 'メールアドレスでログイン')]")))
                    self.driver.execute_script("arguments[0].click();", mail_login_btn)
                except Exception:
                    logger.info("Email login button not found or could not be clicked.")

            # Email入力
            logger.info("Looking for email input...")
            try:
                # 複数の条件で探す: name, type, placeholder
                email_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='email'], input[type='email'], input[placeholder*='メールアドレス']")))
                email_input.click()
                email_input.clear()
                email_input.send_keys(self.email)
            except Exception as e:
                logger.error(f"Email input not found: {e}")
                raise e

            # Password入力
            logger.info("Looking for password input...")
            try:
                pass_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='password'], input[type='password'], input[placeholder*='パスワード']")))
                pass_input.click()
                pass_input.clear()
                pass_input.send_keys(self.password)
            except Exception as e:
                logger.error(f"Password input not found: {e}")
                raise e

            # ログインボタンクリック
            logger.info("Clicking submit button...")
            try:
                # type='submit' または テキストが「ログイン」のボタンを探す
                submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit'] | //button[contains(text(), 'ログイン')]")))
                self.driver.execute_script("arguments[0].click();", submit_btn)
            except Exception as e:
                logger.error(f"Failed to click submit button: {e}")
                # フォールバック: エンターキー送信
                try:
                    logger.info("Trying Enter key...")
                    pass_input.send_keys(Keys.RETURN)
                except Exception:
                    pass
            
            # ログイン完了待機（URLの遷移や特有の要素で判定）
            logger.info("Waiting for login to complete...")
            time.sleep(5) # 簡易的な待機
            
            # ログイン成功確認（マイページへの遷移など詳細な判定は省略し、次の処理へ）
            logger.info("Login process executed.")

        except Exception as e:
            logger.error(f"Login failed: {e}")
            # Debug用に開いたままにするためquitしない
            # if self.driver:
            #     self.driver.quit()
            raise e

    def upload_content(self, file_path, title, description, is_draft=True):
        try:
            logger.info("Navigating to upload page...")
            self.driver.get("https://stand.fm/creator/broadcast/create")
            
            wait = WebDriverWait(self.driver, 30) # アップロード考慮して長めに待機

            # 1. 音声ファイルアップロード (OSダイアログ回避)
            # input[type='file'] を探して直接パスを渡す
            logger.info(f"Uploading file: {file_path}")
            try:
                # input要素は非表示(hidden)の可能性があるため visibility_of ではなく presence_of を使う
                file_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
                file_input.send_keys(file_path)
                logger.info("File path send_keys executed.")
            except Exception as e:
                logger.error(f"File input not found or upload failed: {e}")
                raise e
            
            # --- アップロード処理待ちの間にメタデータを入力 ---

            # 2. タイトル入力
            logger.info("Setting title...")
            try:
                title_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder*='タイトル'], input[name='title']")))
                # React制御対策: JSクリック & clear
                self.driver.execute_script("arguments[0].click();", title_input)
                title_input.clear()
                title_input.send_keys(title)
            except Exception as e:
                logger.error(f"Title input error: {e}")
                raise e

            # 3. 概要欄入力
            logger.info("Setting description...")
            try:
                desc_input = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "textarea[placeholder*='説明'], textarea[name='description']")))
                self.driver.execute_script("arguments[0].click();", desc_input)
                desc_input.send_keys(description)
            except Exception:
                logger.warning("Description input not found, skipping.")

            # 4. アップロード完了待機 & 保存ボタンクリック
            logger.info("Waiting for upload completion and save button...")
            
            # Step A: 確認ボタンがある場合は押す (モーダルやウィザード形式の場合)
            try:
                wait_short = WebDriverWait(self.driver, 5)
                confirm_btn = wait_short.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '確認') or contains(., '次へ')]")))
                logger.info(f"Found confirmation button: {confirm_btn.text}")
                self.driver.execute_script("arguments[0].click();", confirm_btn)
                time.sleep(3)
            except Exception:
                logger.info("Confirmation button not found. Assuming direct save/publish flow.")

            # Step B: 最終的な「下書き保存」または「投稿」ボタンをクリック
            # ユーザー指示に従い、Wait処理とJSクリックを徹底する
            target_keyword = "下書き" if is_draft else "投稿"
            
            try:
                logger.info(f"Waiting for final button (keyword: '{target_keyword}') to be clickable...")
                
                # アップロード処理が終わるまでボタンがdisabledの可能性があるため、長めに待つ
                wait_long = WebDriverWait(self.driver, 30)
                
                # テキストを含むボタンをXPathで特定
                xpath = f"//button[contains(., '{target_keyword}')]"
                
                final_btn = wait_long.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                
                logger.info(f"Button found: {final_btn.text}")
                
                # 念のためスクロール
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", final_btn)
                time.sleep(1)
                
                # JSを使った強制クリック (ユーザー指定)
                self.driver.execute_script("arguments[0].click();", final_btn)
                
                logger.info("Click executed via JavaScript.")
                time.sleep(5)
                return True

            except Exception as e:
                logger.error(f"Failed to click final button: {e}")
                # デバッグ情報
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    logger.info(f"Available buttons: {[b.text for b in buttons]}")
                except:
                    pass
                raise e

        except Exception as e:
            logger.error(f"Upload process failed: {e}")
            return False
        # finally:
        #     if self.driver:
        #         self.driver.quit()

# テスト用
if __name__ == "__main__":
    # 環境変数から読み込み
    email = os.getenv("STANDFM_EMAIL")
    password = os.getenv("STANDFM_PASSWORD")
    if email and password:
        uploader = StandfmUploader(email, password, headless=False)
        uploader.login()
        # uploader.upload_content("/path/to/dummy.mp3", "Test Title", "Test Description")
    else:
        print("Please set STANDFM_EMAIL and STANDFM_PASSWORD env vars for testing.")

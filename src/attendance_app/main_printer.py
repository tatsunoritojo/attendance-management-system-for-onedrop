from pathlib import Path
import sys
import threading
import os # osをインポート
import time # timeをインポート

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.uix.image import Image # Imageをインポート

# --- アプリ内モジュール ---
from .drive_handler import list_qr_files_from_drive, download_file_from_drive, get_qr_download_path
from .spreadsheet import get_student_list_for_printing, update_sample_csv, update_selected_student_csv # 新しい関数をインポート
from .print_dialog import PrintDialog
from .printer_control import print_label
from .print_history import add_record
from .config import load_settings


# --- フォント登録関連 (main.pyからコピー) ---
def register_font() -> bool:
    """
    フォントを安全に登録する。
    """
    try:
        from importlib import resources as res
        from pathlib import Path
        with res.path("src.attendance_app.assets.fonts", "UDDigiKyokashoN-R.ttc") as p:
            LabelBase.register(name="UDDigiKyokashoN-R", fn_regular=str(p))
            return True
    except FileNotFoundError:
        pass

    # fallback for development or alternative paths
    try:
        from pathlib import Path
        legacy_path = Path(__file__).resolve().parent.parent / "Font" / "UDDigiKyokashoN-R.ttc"
        if legacy_path.exists():
            LabelBase.register(name="UDDigiKyokashoN-R", fn_regular=str(legacy_path))
            return True
    except Exception:
        pass

    print(f"Warning: フォントが見つかりません")
    return False

FONT_AVAILABLE = register_font()

# --- エラーポップアップ関連 (main.pyからコピー) ---
from kivy.uix.popup import Popup

def show_error_popup(title, message):
    """エラーメッセージを表示するポップアップ（日本語フォント対応）"""
    content_label = Label(
        text=message, 
        font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
        font_size="18sp",
        text_size=(None, None),
        halign="center",
        valign="middle"
    )
    
    popup = Popup(
        title=title,
        content=content_label,
        size_hint=(0.8, 0.4),
        title_font="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto"
    )
    popup.open()


class PrintScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.qr_file_list = []  # QRコードファイルリストを保持
        self.selected_qr_path = None # 選択されたQRのローカルパス
        self.is_list_loaded = False # リストが読み込まれているかのフラグ
        self.drive_files_cache = {} # Google Driveファイルリストのキャッシュ
        self.cache_timestamp = 0 # キャッシュのタイムスタンプ
        self.cache_expiry = 300 # キャッシュの有効期限（5分）

        # 背景色設定（メイン画面と同じ薄いグレー）
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(0.96, 0.96, 0.96, 1)  # 薄いグレー背景
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        # ヘッダー - より洗練されたデザイン
        header_layout = BoxLayout(size_hint_y=None, height="80dp", padding=[20, 10])
        header_label = Label(
            text="QRコード印刷システム",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="28sp",
            color=(0, 0, 0, 1),  # 黒色
            halign="center"
        )
        header_label.text_size = (None, None)
        header_layout.add_widget(header_label)
        main_layout.add_widget(header_layout)

        # コンテンツエリア (リストとプレビュー) - カード風デザイン
        content_layout = BoxLayout(orientation="horizontal", spacing=30, padding=[10, 0])

        # QRコードリスト表示エリア - カード風デザイン
        list_card = BoxLayout(orientation="vertical", size_hint_x=0.6, padding=20, spacing=10)
        
        # リストタイトル
        list_title = Label(
            text="印刷対象選択",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="20sp",
            color=(0, 0, 0, 1),  # 黒色
            size_hint_y=None,
            height="40dp",
            halign="left"
        )
        list_title.text_size = (None, None)
        list_card.add_widget(list_title)
        
        # スクロールビューエリア - 白背景で視認性向上
        self.qr_list_layout = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.qr_list_layout.bind(minimum_height=self.qr_list_layout.setter('height'))
        scroll_view = ScrollView(
            bar_width=8,
            bar_color=(0.7, 0.7, 0.7, 0.8),
            bar_inactive_color=(0.9, 0.9, 0.9, 0.5)
        )
        
        # スクロールビュー背景を白に
        from kivy.graphics import Color, Rectangle
        with scroll_view.canvas.before:
            Color(1, 1, 1, 1)
            scroll_view.bg_rect = Rectangle(size=scroll_view.size, pos=scroll_view.pos)
        scroll_view.bind(size=lambda instance, value: setattr(scroll_view.bg_rect, 'size', value))
        scroll_view.bind(pos=lambda instance, value: setattr(scroll_view.bg_rect, 'pos', value))
        
        scroll_view.add_widget(self.qr_list_layout)
        list_card.add_widget(scroll_view)
        content_layout.add_widget(list_card)

        # プレビュー＆印刷ボタンエリア - カード風デザイン
        preview_card = BoxLayout(orientation='vertical', size_hint_x=0.4, padding=20, spacing=15)
        
        # プレビュータイトル
        preview_title = Label(
            text="プレビュー",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="20sp",
            color=(0, 0, 0, 1),  # 黒色
            size_hint_y=None,
            height="40dp",
            halign="left"
        )
        preview_title.text_size = (None, None)
        preview_card.add_widget(preview_title)
        
        # プレビュー画像エリア - 白背景で整理、正方形に
        image_container = BoxLayout(orientation='vertical', spacing=0, size_hint=(1, None), height="250dp")
        
        # プレビュー画像背景を白に
        with image_container.canvas.before:
            Color(1, 1, 1, 1)
            image_container.bg_rect = Rectangle(size=image_container.size, pos=image_container.pos)
        image_container.bind(size=lambda instance, value: setattr(image_container.bg_rect, 'size', value))
        image_container.bind(pos=lambda instance, value: setattr(image_container.bg_rect, 'pos', value))
        
        self.preview_image = Image(source='', allow_stretch=True, keep_ratio=True)
        image_container.add_widget(self.preview_image)
        preview_card.add_widget(image_container)
        
        # 印刷ボタン - より目立つデザイン
        print_button = Button(
            text="このQRコードを印刷",
            size_hint_y=None,
            height="80dp",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="22sp",
            background_color=(0.5, 0.8, 0.6, 1),  # 柔らかい緑系
            color=(1, 1, 1, 1),  # 白文字
            background_normal=''
        )
        print_button.bind(on_release=self.confirm_print)
        preview_card.add_widget(print_button)
        
        content_layout.add_widget(preview_card)

        main_layout.add_widget(content_layout)

        # 下部ボタンエリア - より洗練されたデザイン
        button_layout = BoxLayout(size_hint_y=None, height="90dp", spacing=20, padding=[40, 0])
        
        # リスト更新ボタン
        refresh_button = Button(
            text="リスト更新",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="24sp",
            background_color=(0.4, 0.7, 0.8, 1),  # 柔らかい水色
            color=(1, 1, 1, 1),  # 白文字
            background_normal=''
        )
        refresh_button.bind(on_release=self.load_qr_list_from_drive)
        
        # 戻るボタン
        back_button = Button(
            text="戻る",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="24sp",
            background_color=(0.6, 0.6, 0.6, 1),  # グレー系
            color=(1, 1, 1, 1),  # 白文字
            background_normal=''
        )
        back_button.bind(on_release=lambda *_: setattr(self.manager, "current", "wait"))
        
        button_layout.add_widget(refresh_button)
        button_layout.add_widget(back_button)
        main_layout.add_widget(button_layout)

        self.add_widget(main_layout)
        
        # 初期メッセージを表示
        self._show_initial_message()
    
    def _update_rect(self, instance, value):
        """Canvas背景更新"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_enter(self, *args):
        """画面に入るたびに初期状態にリセット"""
        super().on_enter(*args)
        if not self.is_list_loaded:
            self._show_initial_message()

    def _get_cached_drive_files(self):
        """キャッシュ機能付きでGoogle Driveファイルリストを取得"""
        current_time = time.time()
        
        # キャッシュが有効期限内であれば使用
        if (self.drive_files_cache and 
            current_time - self.cache_timestamp < self.cache_expiry):
            print(f"[キャッシュ] Google Driveファイルリストをキャッシュから取得")
            return self.drive_files_cache
        
        # キャッシュが無効または期限切れの場合、新しく取得
        print(f"[キャッシュ] Google Driveファイルリストを新規取得")
        drive_files = list_qr_files_from_drive()
        
        # キャッシュを更新
        self.drive_files_cache = {f['name']: f['id'] for f in drive_files}
        self.cache_timestamp = current_time
        
        return self.drive_files_cache

    def _show_initial_message(self):
        """初期状態でリスト更新を促すメッセージを表示"""
        self.qr_list_layout.clear_widgets()
        self.preview_image.source = ''
        self.selected_qr_path = None
        
        # より目立つ初期メッセージ
        initial_message = Label(
            text="🔄 「リスト更新」をクリックしてください", 
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="18sp",
            color=(0.5, 0.5, 0.5, 1),  # ミディアムグレー
            halign="center",
            valign="middle"
        )
        initial_message.text_size = (400, None)
        self.qr_list_layout.add_widget(initial_message)

    def load_qr_list_from_drive(self, *args):
        self.qr_list_layout.clear_widgets()
        self.preview_image.source = ''
        self.selected_qr_path = None
        # ローディングメッセージを表示（日本語フォント指定）
        loading_label = Label(
            text="⏳ リストを読み込み中...", 
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="18sp",
            color=(0.2, 0.4, 0.8, 1),  # 青系でアクティブな感じ
            halign="center",
            valign="middle"
        )
        loading_label.text_size = (400, None)
        self.qr_list_layout.add_widget(loading_label)
        threading.Thread(target=self._load_printable_list_thread).start()

    def _load_printable_list_thread(self):
        """スプレッドシートとDriveを連携して印刷可能なリストを作成する"""
        try:
            print("--- デバッグ開始: 印刷可能リストの読み込み ---")
            
            # 0. sample_data.csvをスプレッドシートの最新データで更新
            print("[DEBUG] sample_data.csvを更新中...")
            csv_updated = update_sample_csv()
            if csv_updated:
                print("[DEBUG] sample_data.csvの更新が完了しました")
            else:
                print("[DEBUG] sample_data.csvの更新に失敗しました")
            
            # 1. スプレッドシートから塾生リストを取得
            student_list = get_student_list_for_printing()
            print(f"[DEBUG] スプレッドシートから取得した塾生数: {len(student_list)}")
            if student_list:
                print(f"[DEBUG] 取得した塾生リスト (先頭5件): {student_list[:5]}")

            if not student_list:
                Clock.schedule_once(lambda dt: self._update_qr_list_ui([]), 0)
                print("--- デバッグ終了: 塾生リストが空のため処理終了 ---")
                return

            # 2. Google DriveからQRファイルリストを取得（キャッシュ使用）
            drive_files_map = self._get_cached_drive_files()
            print(f"[DEBUG] Google Driveから取得したファイル数: {len(drive_files_map)}")
            if drive_files_map:
                print(f"[DEBUG] 取得したファイルリスト (先頭5件): {list(drive_files_map.items())[:5]}")
            
            # 3. スプレッドシートの全塾生が印刷可能（QRコードはテキストベースで生成）
            # 修正: Google DriveにQRコードファイルが存在する塾生のみをフィルタリング
            printable_students = []
            for student in student_list:
                qr_filename = f"{student['id']}.png"
                if qr_filename in drive_files_map:
                    printable_students.append(student)
                else:
                    print(f"[DEBUG] QRコードファイルが見つかりません: {qr_filename}")

            print(f"[DEBUG] 最終的に印刷可能な塾生数: {len(printable_students)}")
            Clock.schedule_once(lambda dt: self._update_qr_list_ui(printable_students), 0)
            # リスト読み込み完了フラグを設定
            self.is_list_loaded = True
            print("--- デバッグ終了: 正常終了 ---")

        except Exception as e:
            error_message = f"リストの読み込みに失敗: {e}"
            print(f"[ERROR] {error_message}")
            import traceback
            traceback.print_exc()
            Clock.schedule_once(lambda dt: show_error_popup("エラー", error_message), 0)
            Clock.schedule_once(lambda dt: self._update_qr_list_ui([]), 0) # エラー時もUIをクリア
            print("--- デバッグ終了: 例外発生 ---")

    def _update_qr_list_ui(self, printable_students):
        self.qr_list_layout.clear_widgets()
        self.qr_file_list = printable_students # プロパティに保持

        if not self.qr_file_list:
            empty_message = Label(
                text="⚠️ 印刷可能なQRコードが見つかりません\n\n確認事項：\n・ スプレッドシートに塾生が登録されているか\n・ Google DriveにQRファイル(塾生番号.png)があるか", 
                font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto", 
                font_size="16sp",
                halign="center",
                valign="middle",
                text_size=(400, None),
                color=(0.8, 0.4, 0.4, 1)  # 赤っぽい色で警告
            )
            self.qr_list_layout.add_widget(empty_message)
            return

        for student_data in self.qr_file_list:
            display_text = f"👤 {student_data['id']} - {student_data['name']}"
            btn = Button(
                text=display_text,
                size_hint_y=None,
                height="55dp",
                font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
                font_size="16sp",
                background_color=(0.6, 0.6, 0.6, 1),  # グレー
                color=(1, 1, 1, 1),  # 白文字
                halign="left",
                text_size=(None, None),
                background_normal=''
            )
            btn.bind(on_release=lambda _, data=student_data: self.select_qr_code(data))
            self.qr_list_layout.add_widget(btn)

    def select_qr_code(self, student_data):
        # 選択された生徒の情報を保持
        self.current_student_id = student_data['id'] # 塾生IDを保持
        self.current_student_name = student_data['name'] # 氏名を保持
        self.selected_qr_path = "selected" # 選択状態のフラグとして使用

        # 即座にsample_data.csvを選択された塾生のデータで更新（ワンクリック印刷対応）
        threading.Thread(target=self._update_csv_for_selected_student, 
                        args=(student_data['id'], student_data['name'])).start()

        # Google DriveからQRコード画像をダウンロードしてプレビュー表示（UIフィードバック用）
        expected_filename = f"{student_data['id']}.png"
        threading.Thread(target=self._download_and_preview_for_feedback, 
                        args=(student_data['id'], expected_filename)).start()

        print(f"塾生を選択しました: {student_data['name']} (ID: {student_data['id']})")

    def _update_csv_for_selected_student(self, student_id, student_name):
        """選択された塾生のデータでCSVファイルを更新する"""
        try:
            print(f"[CSV更新] 選択塾生用にCSVファイルを更新中: {student_name} (ID: {student_id})")
            success = update_selected_student_csv(student_id, student_name)
            if success:
                print(f"[CSV更新] CSVファイルの更新が完了しました。P-touch Editorのテンプレートが更新されています。")
            else:
                print(f"[CSV更新] CSVファイルの更新に失敗しました。")
        except Exception as e:
            print(f"[CSV更新] エラーが発生しました: {e}")

    def _download_and_preview_for_feedback(self, student_id, filename):
        """UIフィードバック用にQRコード画像をダウンロードしてプレビュー表示（高速化版）"""
        try:
            # まず、ローカルファイルが既に存在するかチェック
            local_path = os.path.join(get_qr_download_path(), filename)
            
            if os.path.exists(local_path):
                print(f"[プレビュー] ローカルファイルを使用: {filename}")
                Clock.schedule_once(lambda dt: self._update_preview_image(local_path), 0)
                return
            
            # ローカルにない場合、キャッシュからGoogle Driveファイルマップを取得
            drive_files_map = self._get_cached_drive_files()
            
            if filename in drive_files_map:
                file_id = drive_files_map[filename]
                print(f"[プレビュー] QRコード画像をダウンロード中: {filename}")
                local_path = download_file_from_drive(file_id, filename)
                
                if local_path and os.path.exists(local_path):
                    # UIスレッドでプレビュー画像を更新
                    Clock.schedule_once(lambda dt: self._update_preview_image(local_path), 0)
                    print(f"[プレビュー] プレビュー画像を更新: {local_path}")
                else:
                    print(f"[プレビュー] ダウンロードに失敗: {filename}")
                    Clock.schedule_once(lambda dt: self._clear_preview_image(), 0)
            else:
                print(f"[プレビュー] Google Driveにファイルが見つかりません: {filename}")
                Clock.schedule_once(lambda dt: self._clear_preview_image(), 0)
                
        except Exception as e:
            print(f"[プレビュー] エラーが発生しました: {e}")
            Clock.schedule_once(lambda dt: self._clear_preview_image(), 0)

    def _clear_preview_image(self):
        """プレビュー画像をクリア"""
        self.preview_image.source = ''

    def _download_and_preview_thread(self, file_id, file_name):
        try:
            local_path = download_file_from_drive(file_id, file_name)
            if local_path:
                self.selected_qr_path = local_path
                # UIスレッドでプレビュー画像を更新
                Clock.schedule_once(lambda dt: self._update_preview_image(local_path), 0)
                print(f"プレビュー画像を設定: {local_path}")
            else:
                Clock.schedule_once(lambda dt: show_error_popup("エラー", "QRコードのダウンロードに失敗しました。"), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt, err=str(e): show_error_popup("エラー", f"プレビュー表示に失敗: {err}"), 0)
        finally:
            # プレビュー処理が終わったらポップアップを閉じる
            Clock.schedule_once(lambda dt: self.download_popup.dismiss(), 0)
    
    def _update_preview_image(self, image_path):
        """UIスレッドでプレビュー画像を更新"""
        try:
            print(f"プレビュー画像の更新を開始: {image_path}")
            print(f"ファイル存在確認: {os.path.exists(image_path)}")
            
            if os.path.exists(image_path):
                # パスを正規化（Kivyが正しく処理できるように）
                normalized_path = os.path.normpath(image_path)
                print(f"正規化されたパス: {normalized_path}")
                
                # 現在のソースをクリア
                self.preview_image.source = ''
                
                # 新しい画像を設定
                self.preview_image.source = normalized_path
                self.preview_image.reload()
                print(f"プレビュー画像を正常に設定しました")
                
                # 画像サイズ情報も確認
                file_size = os.path.getsize(image_path)
                print(f"画像ファイルサイズ: {file_size} bytes")
            else:
                print(f"プレビュー画像ファイルが見つかりません: {image_path}")
                show_error_popup("エラー", f"プレビュー画像ファイルが見つかりません: {image_path}")
        except Exception as e:
            print(f"プレビュー画像の更新に失敗: {e}")
            show_error_popup("エラー", f"プレビュー画像の更新に失敗: {e}")

    def confirm_print(self, *args):
        # リストが読み込まれていない場合の処理
        if not self.is_list_loaded:
            show_error_popup("リスト未更新", "リスト更新を押してください。")
            return
            
        if not self.selected_qr_path:
            show_error_popup("選択エラー", "印刷する塾生をリストから選択してください。")
            return

        # 保持しておいた塾生IDと氏名を使う
        student_id = self.current_student_id
        student_name = self.current_student_name

        def on_confirm():
            threading.Thread(target=self._print_qr_thread, args=(student_id, student_name)).start()

        dialog = PrintDialog(f"{student_name} のQRコード", on_confirm, lambda: None)
        dialog.open()

    def _print_qr_thread(self, student_id, student_name):
        try:
            print_label(student_id, student_name)
            add_record(student_id, student_name, 'success')
        except Exception as e:
            add_record(student_id, student_name, 'failure', str(e))
            Clock.schedule_once(lambda dt, error_msg=str(e): show_error_popup("エラー", f"印刷に失敗しました: {error_msg}"), 0)
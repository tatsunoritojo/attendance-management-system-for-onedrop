# attendance_app.py

import sys
import os

# --- Environment Debug ---
log_path = os.path.join(os.path.expanduser("~"), "env_debug.log")
with open(log_path, "w", encoding="utf-8") as f:
    f.write(f"Python Executable: {sys.executable}\n")
    f.write(f"sys.path: {sys.path}\n")
# --- End Debug ---

import threading
import importlib.resources as res  # 3.9+ 標準

from datetime import datetime
from pathlib import Path
import subprocess

import openpyxl
from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import FadeTransition, Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window
from kivy.core.audio import SoundLoader

try:
    from .config import load_settings, save_settings
    from .spreadsheet import get_student_name, get_last_record, write_exit, append_entry, write_response
    from .main_printer import PrintScreen # PrintScreenをインポート
    from .report_screen import ReportScreen # ReportScreenをインポート
    from .report_editor_screen import ReportEditorScreen # ReportEditorScreenをインポート
except ImportError as e:
    print(f"相対インポートに失敗、絶対インポートを試行します: {e}")
    try:
        # PyInstallerで実行される場合は絶対インポート
        from attendance_app.config import load_settings, save_settings
        from attendance_app.spreadsheet import get_student_name, get_last_record, write_exit, append_entry, write_response
        from attendance_app.main_printer import PrintScreen # PrintScreenをインポート
        from attendance_app.report_screen import ReportScreen # ReportScreenをインポート
        from attendance_app.report_editor_screen import ReportEditorScreen # ReportEditorScreenをインポート
    except ImportError as e2:
        print(f"絶対インポートも失敗しました: {e2}")
        print("必要なモジュールがインポートできません。アプリケーションを終了します。")
        import sys
        sys.exit(1)


# ── 実行ファイル対応のベースディレクトリ取得 ──
def get_base_dir():
    """実行ファイルでも動作するベースディレクトリを取得"""
    if getattr(sys, "frozen", False):
        # PyInstallerで実行ファイル化されている場合
        return sys._MEIPASS
    else:
        # 通常のPythonスクリプトとして実行されている場合
        return os.path.dirname(os.path.abspath(__file__))
    
BASE_DIR = get_base_dir()
    
def register_font() -> bool:
    """
    フォントを安全に登録する。

    1. パッケージ同梱 assets/fonts/ を優先
    2. 開発時のみ BASE_DIR/Font/ も探す（後方互換）
    """
    # --- ① パッケージ内リソースを探す ------------------------
    try:
        with res.path("src.attendance_app.assets.fonts", "UDDigiKyokashoN-R.ttc") as p:
            LabelBase.register(name="UDDigiKyokashoN-R", fn_regular=str(p))
            return True
    except FileNotFoundError:
        pass  # 見つからなければ次へ

    # --- ② 従来の BASE_DIR/Font/ も試す ----------------------
    legacy_path = Path(__file__).resolve().parent.parent / "Font" / "UDDigiKyokashoN-R.ttc"
    if legacy_path.exists():
        LabelBase.register(name="UDDigiKyokashoN-R", fn_regular=str(legacy_path))
        return True

    print(f"Warning: フォントが見つかりません -> {legacy_path}")
    return False


# フォント登録実行
FONT_AVAILABLE = register_font()

def get_image_path(subfolder: str, filename: str) -> str:
    """
    パッケージ同梱 images から画像ファイルの絶対パスを返す。
    1. src/attendance_app/assets/images/… を最優先
    2. 開発時のみ従来の BASE_DIR/assets/images も fallback
    """
    try:
        # パッケージ内リソースを解決
        with res.path("src.attendance_app.assets.images", Path(subfolder) / filename) as p:
            return str(p)
    except FileNotFoundError:
        # ---- fallback: 開発中だけ BASE_DIR も見る -----------------
        legacy = Path(BASE_DIR) / "assets" / "images" / subfolder / filename
        if legacy.exists():
            return str(legacy)

        # どこにも無ければ警告だけ出して空文字を返す
        print(f"Warning: 画像が見つかりません -> {legacy}")
        return ""

def get_sound_path(filename: str) -> str:
    """
    パッケージ同梱 sounds から音声ファイルの絶対パスを返す。
    """
    try:
        # パッケージ内リソースを解決
        with res.path("src.attendance_app.assets.sounds", filename) as p:
            return str(p)
    except FileNotFoundError:
        # fallback: 開発中だけ BASE_DIR も見る
        legacy = Path(BASE_DIR) / "assets" / "sounds" / filename
        if legacy.exists():
            return str(legacy)

        # どこにも無ければ警告だけ出して空文字を返す
        print(f"Warning: 音声ファイルが見つかりません -> {legacy}")
        return ""
    # --- エラーハンドリング付きユーティリティ関数 ---
def show_error_popup(title, message):
    """エラーメッセージを表示するポップアップ - 改善されたデザイン"""
    from kivy.graphics import Color, Rectangle
    
    # カスタムコンテンツレイアウト
    content_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
    
    # メッセージラベル
    content_label = Label(
        text=message,
        font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
        font_size="18sp",
        color=(1, 1, 1, 1),
        halign="center",
        valign="middle"
    )
    content_label.text_size = (None, None)
    content_layout.add_widget(content_label)
    
    # 閉じるボタン
    close_btn = Button(
        text="確認",
        size_hint_y=None,
        height="50dp",
        font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
        font_size="16sp",
        background_color=(0.4, 0.7, 0.8, 1),  # 柔らかい水色
        color=(1, 1, 1, 1),  # 白文字
        background_normal=''
    )
    content_layout.add_widget(close_btn)
    
    popup = Popup(
        title=title,
        content=content_layout,
        size_hint=(0.8, 0.5),
        title_font="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
        auto_dismiss=False
    )
    
    # 背景色設定
    with popup.canvas.before:
        Color(0.98, 0.98, 0.98, 1)  # 薄いグレー背景
        popup.bg_rect = Rectangle(size=popup.size, pos=popup.pos)
    popup.bind(size=lambda instance, value: setattr(popup.bg_rect, 'size', value))
    popup.bind(pos=lambda instance, value: setattr(popup.bg_rect, 'pos', value))
    
    close_btn.bind(on_release=popup.dismiss)
    popup.open()

class HelpPopup(Popup):
    def __init__(self, title, message, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.title_font = "UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto"
        self.size_hint = (0.9, 0.9)
        self.auto_dismiss = False

        # テキストコンテンツの左右パディング
        self.text_horizontal_padding = 40  # ここでパディングを調整できます

        self.content_label = Label(
            text=message,
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="18sp",
            size_hint_y=None,
            valign="top",
            halign="left",
            text_size=(600, None)  # 適切な幅を設定
        )
        self.content_label.bind(texture_size=self.content_label.setter('size'))

        scroll_view = ScrollView(size_hint=(1, 0.9))
        scroll_view.add_widget(self.content_label)

        close_button = Button(
            text="閉じる",
            size_hint=(1, 0.1),
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
        )
        close_button.bind(on_release=self.dismiss)

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        layout.add_widget(scroll_view)
        layout.add_widget(close_button)
        self.content = layout

    def on_size(self, instance, value):
        # ポップアップのサイズ変更時にテキストの幅を更新
        if self.content_label:
            # content (BoxLayout) の幅から明示的なパディングを引く
            content_width = max(400, self.content.width - self.text_horizontal_padding)
            self.content_label.text_size = (content_width, None)


# --- 各画面定義 ---
class WaitScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._keyboard = None
        
        # 音声ファイルを読み込み
        try:
            sound_path = get_sound_path("selected_sound.mp3")
            self.sound = SoundLoader.load(sound_path) if sound_path else None
        except Exception as e:
            print(f"音声ファイルの読み込みに失敗しました: {e}")
            self.sound = None
        
        # 背景色設定（薄いグレー）
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(0.96, 0.96, 0.96, 1)  # 薄いグレー背景
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        root = BoxLayout(orientation="vertical")
        
        # メインコンテンツエリア - カード風デザイン
        layout = BoxLayout(orientation="vertical", padding=60, spacing=30)
        
        # Onedropロゴ表示
        logo_path = Path(__file__).resolve().parent / "assets" / "images" / "Onedrop_logo" / "ChatGPT Image 2025年9月6日 16_41_22.png"
        title_label = Image(
            source=str(logo_path),
            size_hint_y=None,
            height="720dp",
            allow_stretch=True,
            keep_ratio=True,
            mipmap=True
        )
        layout.add_widget(title_label)
        
        # 入力フィールド - より視認性の高いデザイン
        input_container = BoxLayout(orientation="vertical", spacing=15)
        
        # 入力フィールド背景を白にして視認性向上
        self.input = TextInput(
            hint_text="タッチしてください",
            multiline=False,
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="40sp",
            size_hint_y=None,
            height="120dp",
            background_color=(1, 1, 1, 1),  # 白背景
            foreground_color=(0.2, 0.2, 0.2, 1),  # ダークグレー文字
            padding=[20, 20]
        )
        # エンターキーでの送信対応
        self.input.bind(on_text_validate=self.on_submit)
        # タッチイベントをオーバーライド
        self.input.on_touch_down = self.on_input_touch_down
        input_container.add_widget(self.input)
        
        # 送信ボタン - より目立つデザイン
        btn = Button(
            text="送信",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="24sp",
            size_hint=(1, None),
            height="80dp",
            background_color=(0.5, 0.8, 0.6, 1),  # 柔らかい緑系
            color=(1, 1, 1, 1),  # 白文字
            background_normal=''
        )
        btn.bind(on_press=self.on_submit)
        input_container.add_widget(btn)
        
        layout.add_widget(input_container)
        root.add_widget(layout)
        self.add_widget(root)
    
    def on_enter(self):
        """画面が表示されるタイミングでキーボード監視を開始"""
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        if self._keyboard:
            self._keyboard.bind(on_key_down=self._on_keyboard_down)
    
    def on_leave(self):
        """画面から離れるタイミングでキーボード監視を解除"""
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard = None
        
    def _keyboard_closed(self):
        if self._keyboard:
            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if 'alt' in modifiers:
            if keycode[1] == 's':
                setattr(self.manager, "current", "settings")
            elif keycode[1] == 'p':
                setattr(self.manager, "current", "print_screen")
            elif keycode[1] == 'r':
                setattr(self.manager, "current", "report")
        return True
        
    def _update_rect(self, instance, value):
        """背景の矩形を更新"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_touch_down(self, touch):
        """画面全体のタッチイベントを処理"""
        print(f"DEBUG: Screen touched at {touch.pos}")
        
        # 入力フィールド以外がタッチされた場合、ヒントテキストを待機状態に戻す
        if not self.input.collide_point(*touch.pos):
            print("DEBUG: Touch outside input field - resetting hint text and colors")
            if self.input.hint_text == "スキャナーに塾生カードをかざしてください":
                self.input.hint_text = "タッチしてください"
                # 待機状態の色に戻す（白背景）
                self.input.background_color = (1, 1, 1, 1)  # 白背景
                self.input.foreground_color = (0.2, 0.2, 0.2, 1)  # ダークグレー文字
        
        # 通常のタッチ処理を継続
        return super().on_touch_down(touch)

    def on_input_touch_down(self, touch):
        """入力フィールドがタッチされた時の処理"""
        print(f"DEBUG: Input field touched at {touch.pos}")
        
        # タッチ位置が入力フィールド内かチェック
        if self.input.collide_point(*touch.pos):
            print("DEBUG: Touch is inside input field")
            # ヒントテキストを変更
            if self.input.hint_text == "タッチしてください":
                print("DEBUG: Changing hint text to scan message and activating colors")
                self.input.hint_text = "スキャナーに塾生カードをかざしてください"
                # アクティブ状態の色に変更（薄い青背景）
                self.input.background_color = (0.9, 0.95, 1.0, 1)  # 薄い青
                self.input.foreground_color = (0.1, 0.3, 0.7, 1)  # 濃い青
                # 音を再生
                if self.sound:
                    self.sound.play()
            
            # 元のTextInputのtouch処理を実行
            return TextInput.on_touch_down(self.input, touch)
        return False

    def on_submit(self, *_):
        sid = self.input.text.strip()
        print(f"DEBUG: Student ID entered: {sid}")
        if not sid:
            print("DEBUG: Student ID is empty, returning.")
            return

        app = App.get_running_app()
        app.student_id = sid # Store student_id for later use
        self.manager.current = "loading" # Show loading screen

        # Run the processing in a separate thread
        threading.Thread(target=self._process_student_id, args=(sid,)).start()

        self.input.text = ""
        # ヒントテキストと色を元に戻す
        self.input.hint_text = "タッチしてください"
        self.input.background_color = (1, 1, 1, 1)  # 白背景
        self.input.foreground_color = (0.2, 0.2, 0.2, 1)  # ダークグレー文字

    def _process_student_id(self, sid):
        app = App.get_running_app()
        try:
            name = get_student_name(sid)
            print(f"DEBUG: Student name retrieved: {name}")
            
            # 未登録塾生番号のチェック
            if name == "Unknown":
                error_message = f"""塾生番号が登録されていません: {sid}

以下の点をご確認ください。

①QRコードが正しくスキャンされなかった可能性があります。
  もう一度スキャンしなおしてください。

②塾生として登録されているか、生徒名簿を参照してください。
  登録されていなかった場合、手動で生徒名簿に情報を記載して、
  もう一度スキャンを行ってください。"""
                Clock.schedule_once(lambda dt: show_error_popup("エラー", error_message), 0)
                Clock.schedule_once(lambda dt: setattr(self.manager, "current", "wait"), 0)
                return
            
            last_row, last_exit = get_last_record(sid)
            print(f"DEBUG: Last record for {sid}: row={last_row}, exit_time={last_exit}")

            # ── 退室処理 ──
            if last_row and not last_exit:
                print(f"DEBUG: Attempting to write exit for {sid} at row {last_row}")
                if write_exit(last_row):
                    print(f"DEBUG: Exit written successfully for {sid} at row {last_row}")
                    app.student_name = name
                    Clock.schedule_once(lambda dt: setattr(self.manager, "current", "goodbye"), 0)
                else:
                    print(f"DEBUG: Failed to write exit for {sid} at row {last_row}")
                    Clock.schedule_once(lambda dt: show_error_popup("エラー", "退室処理に失敗しました"), 0)

            # ── 入室処理 ──
            else:
                print(f"DEBUG: Attempting to append entry for {sid}")
                row_idx = append_entry(sid, name)
                if row_idx is not None:
                    print(f"DEBUG: Entry appended successfully at row {row_idx}")
                    app.current_record_row = row_idx
                    app.student_name = name
                    Clock.schedule_once(lambda dt: setattr(self.manager, "current", "greeting"), 0)
                else:
                    print(f"DEBUG: Failed to append entry for {sid}")
                    Clock.schedule_once(lambda dt: show_error_popup("エラー", "入室処理に失敗しました"), 0)
        except Exception as e:
            print(f"ERROR: An error occurred during student ID processing: {e}")
            Clock.schedule_once(lambda dt: show_error_popup("エラー", f"処理中にエラーが発生しました: {e}"), 0)


class GreetingScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        
        # 背景色設定（薄い緑）
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(0.9, 0.98, 0.9, 1)  # 薄い緑背景
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        layout = BoxLayout(orientation="vertical", padding=60, spacing=30)
        
        # 挨拶ラベル - より親しみやすいデザイン
        greeting_label = Label(
            text=f"こんにちは！\n{App.get_running_app().student_name} さん",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="36sp",
            color=(0.2, 0.6, 0.2, 1),  # 濃い緑
            halign="center",
            valign="middle"
        )
        greeting_label.text_size = (None, None)
        layout.add_widget(greeting_label)
        
        # 2秒後に質問画面へ
        Clock.schedule_once(lambda dt: setattr(self.manager, "current", "q1"), 2)
        self.add_widget(layout)
        
    def _update_rect(self, instance, value):
        """背景の矩形を更新"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class WeatherToggle(ToggleButton):
    value = StringProperty()


class QuestionScreen(Screen):
    def __init__(self, key, question, next_screen, question_type="weather", **kw):
        super().__init__(**kw)
        self.key = key
        self.next_screen = next_screen
        self.question_type = question_type
        self.answer_selected = False  # 重複回答防止フラグ
        try:
            sound_path = get_sound_path("selected_sound.mp3")
            self.sound = SoundLoader.load(sound_path) if sound_path else None
        except Exception as e:
            print(f"音声ファイルの読み込みに失敗しました: {e}")
            self.sound = None

        # 背景を白色に設定
        from kivy.graphics import Color, Rectangle

        with self.canvas.before:
            Color(1, 1, 1, 1)  # 白色 (R, G, B, A)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        layout = BoxLayout(orientation="vertical", padding=40, spacing=30)

        # 質問文
        question_label = Label(
            text=question,
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="30pt",
            size_hint_y=None,
            height="120dp",
            valign="top",
            color=(0, 0, 0, 1),
        )
        question_label.text_size = (None, None)
        layout.add_widget(question_label)

        # スペーサーを追加
        from kivy.uix.widget import Widget

        layout.add_widget(Widget(size_hint_y=0.3))

        # 質問タイプに応じて選択肢を作成
        if question_type == "weather":
            self._create_weather_options(layout)
        elif question_type == "sleep":
            self._create_sleep_options(layout)
        elif question_type == "purpose":
            self._create_purpose_options(layout)

        # 下部スペーサー
        layout.add_widget(Widget(size_hint_y=0.3))

        self.add_widget(layout)

    def on_enter(self):
        """画面表示時にフラグをリセット"""
        self.answer_selected = False

    def _update_rect(self, instance, value):
        """背景の矩形を更新"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def _create_weather_options(self, layout):
        """天気アイコンの選択肢を作成"""
        icon_bar = BoxLayout(
            orientation="horizontal",
            spacing=20,
            size_hint_y=None,
            height="260dp",  # 正方形の天気アイコンに合わせて調整
        )

        weather_options = [
            ("sun.png", "快晴"),
            ("sun_cloud.png", "晴れ"),
            ("cloud.png", "くもり"),
            ("rain.png", "雨"),
            ("heavyrain.png", "豪雨"),
        ]

        for filename, value in weather_options:
            image_path = get_image_path("weather", filename)
            if image_path:
                btn = WeatherToggle(
                    background_normal=image_path,
                    background_down=image_path,
                    size_hint=(0.2, 1),  # 全て同じサイズに統一
                    value=value,
                    group=f"question_{self.key}",
                    allow_no_selection=False,
                )
            else:
                # 画像がない場合は通常のボタンを使用
                btn = ToggleButton(
                    text=value,
                    font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
                    font_size="16sp",
                    size_hint=(0.2, 1),  # 全て同じサイズに統一
                    group=f"question_{self.key}",
                    allow_no_selection=False,
                )

            btn.bind(on_press=lambda button, val=value: self.on_answer(val))
            icon_bar.add_widget(btn)

        layout.add_widget(icon_bar)

    def _create_sleep_options(self, layout):
        """睡眠満足度のビーカーアイコン選択肢を作成"""
        icon_bar = BoxLayout(
            orientation="horizontal",
            spacing=20,
            size_hint_y=None,
            height="350dp",  # 縦長のビーカーに合わせて高さを大きく
        )

        sleep_options = [
            ("beaker1.png", "100％"),
            ("beaker2.png", "75％"),
            ("beaker3.png", "50％"),
            ("beaker4.png", "25％"),
            ("beaker5.png", "0％"),
        ]

        for filename, value in sleep_options:
            image_path = get_image_path("sleep", filename)
            if image_path:
                btn = WeatherToggle(
                    background_normal=image_path,
                    background_down=image_path,
                    size_hint=(1, 1),
                    size_hint_min_x=130,  # 縦長に合わせて幅を調整
                    value=value,
                    group=f"question_{self.key}",
                    allow_no_selection=False,
                )
            else:
                # 画像がない場合は通常のボタンを使用
                btn = ToggleButton(
                    text=value,
                    font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
                    font_size="20sp",
                    size_hint=(1, 1),
                    size_hint_min_x=130,
                    group=f"question_{self.key}",
                    allow_no_selection=False,
                )

            btn.bind(on_press=lambda button, val=value: self.on_answer(val))
            icon_bar.add_widget(btn)

        layout.add_widget(icon_bar)

    def _create_purpose_options(self, layout):
        """目的の文字ボタン選択肢を作成"""
        # 画像挿入枠を追加（中段）
        icon_bar = BoxLayout(orientation="horizontal", spacing=20, size_hint_y=None, height="300dp")

        purpose_images = [
            ("purpose1.png", "来る"),
            ("purpose2.png", "学ぶ"),
            ("purpose3.png", "話す"),
            ("purpose4.png", "楽しむ"),
            ("purpose5.png", "整える"),
        ]

        for filename, value in purpose_images:
            image_path = get_image_path("purpose", filename)
            if image_path:
                btn = WeatherToggle(
                    background_normal=image_path,
                    background_down=image_path,
                    size_hint=(1, 1),
                    size_hint_min_x=120,
                    value=value,
                    group=f"question_{self.key}",
                    allow_no_selection=False,
                )
            else:
                # 画像がない場合は空のプレースホルダーを使用
                btn = ToggleButton(
                    text="",
                    size_hint=(1, 1),
                    size_hint_min_x=120,
                    group=f"question_{self.key}",
                    allow_no_selection=False,
                    background_color=(0.9, 0.9, 0.9, 1),  # 薄いグレーで表示
                )

            btn.bind(on_press=lambda button, val=value: self.on_answer(val))
            icon_bar.add_widget(btn)

        layout.add_widget(icon_bar)

        # スペーサーを追加してボタンを下に移動
        from kivy.uix.widget import Widget

        layout.add_widget(Widget(size_hint_y=0.2))

        # ボタンレイアウト（下段）
        button_layout = BoxLayout(
            orientation="horizontal", spacing=20, size_hint_y=None, height="80dp", size_hint_x=1
        )

        purpose_options = ["来る", "学ぶ", "話す", "楽しむ", "整える"]

        for purpose in purpose_options:
            btn = Button(
                text=purpose,
                font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
                font_size="24sp",  # 文字サイズを大きく
                size_hint=(1, 1),  # 均等に配置
                size_hint_min_x=140,  # 最小幅を確保
            )
            btn.bind(on_press=lambda button, val=purpose: self.on_answer(val))
            button_layout.add_widget(btn)

        layout.add_widget(button_layout)

    def on_answer(self, value):
        """回答処理 - 視覚的フィードバック強化版"""
        # 重複回答防止
        if self.answer_selected:
            return
        
        self.answer_selected = True
        
        # 音声再生
        if self.sound:
            self.sound.play()
        
        # 選択フィードバック表示
        self._show_selection_feedback(value)
        
        print(f"=== on_answer デバッグ開始 ===")
        print(f"回答が選択されました: {value}")
        print(f"値の型: {type(value)}")
        print(f"値の内容: {repr(value)}")
        
        app = App.get_running_app()
        col = {"q1": 4, "q2": 5, "q3": 6}[self.key]
        
        print(f"self.key: {self.key}")
        print(f"計算された列: {col}")
        print(f"現在の記録行: {app.current_record_row}")
        print(f"次の画面: {self.next_screen}")
        
        try:
            print(f"write_response を呼び出し中...")
            result = write_response(app.current_record_row, col, value)
            print(f"write_response の戻り値: {result}")
            
            if result:
                print(f"次の画面に移行: {self.next_screen}")
                # 少し遅延を入れてフィードバックを見せる
                Clock.schedule_once(lambda dt: setattr(self.manager, "current", self.next_screen), 0.8)
            else:
                print("write_response が False を返しました")
                show_error_popup("エラー", "スプレッドシートへの書き込みに失敗しました")
                self.answer_selected = False  # エラー時はフラグをリセット
                
        except Exception as e:
            print(f"=== エラー詳細 ===")
            print(f"エラーメッセージ: {str(e)}")
            print(f"エラーの型: {type(e)}")
            print(f"エラーの args: {e.args}")
            
            # より詳細なトレースバック
            import traceback
            print(f"トレースバック:")
            traceback.print_exc()
            
            show_error_popup("エラー", f"スプレッドシートへの書き込みに失敗しました: {e}")
            self.answer_selected = False  # エラー時はフラグをリセット
        
        print(f"=== on_answer デバッグ終了 ===")
    
    def _show_selection_feedback(self, selected_value):
        """選択時の視覚的フィードバックを表示"""
        from kivy.graphics import Color, Rectangle
        from kivy.uix.widget import Widget
        
        # フィードバック用のオーバーレイを作成
        feedback_overlay = Widget()
        
        # 緑色の半透明オーバーレイ
        with feedback_overlay.canvas:
            Color(0.2, 0.8, 0.4, 0.3)  # 薄い緑色、半透明
            feedback_overlay.bg_rect = Rectangle(size=Window.size, pos=(0, 0))
        
        # 選択メッセージラベル
        feedback_label = Label(
            text=f"✓ {selected_value} を選択しました",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="28sp",
            color=(1, 1, 1, 1),  # 白文字
            halign="center",
            valign="middle",
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        feedback_label.text_size = (None, None)
        
        # オーバーレイにラベルを追加
        feedback_overlay.add_widget(feedback_label)
        
        # 画面に追加
        self.add_widget(feedback_overlay)
        
        # 0.7秒後にフィードバックを削除
        Clock.schedule_once(lambda dt: self.remove_widget(feedback_overlay), 0.7)

class WelcomeScreen(Screen):
    """入室後の最終画面"""

    def on_enter(self):
        self.clear_widgets()
        
        # 背景色設定（薄い青）
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(0.9, 0.95, 1, 1)  # 薄い青背景
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        layout = BoxLayout(orientation="vertical", padding=60, spacing=30)
        
        # ウェルカムラベル - より温かみのあるデザイン
        welcome_label = Label(
            text=f"ようこそ\n{App.get_running_app().student_name} さん",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="36sp",
            color=(0.3, 0.6, 0.7, 1),  # 柔らかい水色
            halign="center",
            valign="middle"
        )
        welcome_label.text_size = (None, None)
        layout.add_widget(welcome_label)
        
        Clock.schedule_once(lambda dt: setattr(self.manager, "current", "wait"), 2)
        self.add_widget(layout)
        
    def _update_rect(self, instance, value):
        """背景の矩形を更新"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class GoodbyeScreen(Screen):
    """退室時画面"""

    def on_enter(self):
        self.clear_widgets()
        
        # 背景色設定（薄いオレンジ）
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(1, 0.95, 0.9, 1)  # 薄いオレンジ背景
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        layout = BoxLayout(orientation="vertical", padding=60, spacing=30)
        
        # お別れラベル - より親しみやすいデザイン
        goodbye_label = Label(
            text=f"{App.get_running_app().student_name} さん\n\nまたね！",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="36sp",
            color=(0.5, 0.8, 0.6, 1),  # 柔らかい緑系
            halign="center",
            valign="middle"
        )
        goodbye_label.text_size = (None, None)
        layout.add_widget(goodbye_label)
        
        Clock.schedule_once(lambda dt: setattr(self.manager, "current", "wait"), 2)
        self.add_widget(layout)
        
    def _update_rect(self, instance, value):
        """背景の矩形を更新"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class SettingsScreen(Screen):
    """環境設定画面"""

    def __init__(self, **kw):
        super().__init__(**kw)
        
        # 背景色設定（薄いグレー）
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(0.96, 0.96, 0.96, 1)  # 薄いグレー背景
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        # 入力フィールド - より整理されたスタイル
        self.spread_input = TextInput(
            multiline=False, 
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto", 
            font_size="18sp",
            background_color=(1, 1, 1, 1),
            foreground_color=(0.2, 0.2, 0.2, 1),
            padding=[10, 8]
        )
        self.folder_input = TextInput(
            multiline=False, 
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto", 
            font_size="18sp",
            background_color=(1, 1, 1, 1),
            foreground_color=(0.2, 0.2, 0.2, 1),
            padding=[10, 8]
        )
        self.qr_folder_input = TextInput(
            multiline=False, 
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto", 
            font_size="18sp",
            background_color=(1, 1, 1, 1),
            foreground_color=(0.2, 0.2, 0.2, 1),
            padding=[10, 8]
        )
        self.ptouch_path_input = TextInput(
            multiline=False, 
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto", 
            font_size="18sp",
            background_color=(1, 1, 1, 1),
            foreground_color=(0.2, 0.2, 0.2, 1),
            padding=[10, 8]
        )

        # メインレイアウト - より整理されたデザイン
        main_layout = BoxLayout(orientation="vertical", padding=40, spacing=25)
        
        # タイトルヘッダー
        title_layout = BoxLayout(size_hint_y=None, height="60dp")
        title_label = Label(
            text="システム設定",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="24sp",
            color=(0.2, 0.2, 0.2, 1),
            halign="center"
        )
        title_label.text_size = (None, None)
        title_layout.add_widget(title_label)
        main_layout.add_widget(title_layout)

        # スプレッドシートIDセクション - カード風デザイン
        spread_section = BoxLayout(orientation="vertical", size_hint_y=None, height="100dp", spacing=8)
        spread_id_header = BoxLayout(size_hint_y=None, height="35dp", spacing=10)
        
        spread_label = Label(
            text="スプレッドシートID",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="16sp",
            color=(0.3, 0.3, 0.3, 1),
            halign="left",
            valign="middle",
            text_size=(None, None)
        )
        spread_id_header.add_widget(spread_label)
        
        spread_id_help_btn = Button(
            text="?",
            size_hint=(None, None),
            size=("35dp", "35dp"),
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="14sp",
            background_color=(0.4, 0.7, 0.8, 1),  # 柔らかい水色
            color=(1, 1, 1, 1),
            background_normal=''
        )
        spread_id_help_btn.bind(on_release=self.show_spreadsheet_id_help)
        spread_id_header.add_widget(spread_id_help_btn)
        
        spread_section.add_widget(spread_id_header)
        spread_section.add_widget(self.spread_input)
        main_layout.add_widget(spread_section)

        # 通知フォルダパスセクション - カード風デザイン
        folder_section = BoxLayout(orientation="vertical", size_hint_y=None, height="100dp", spacing=8)
        folder_path_header = BoxLayout(size_hint_y=None, height="35dp", spacing=10)
        
        folder_label = Label(
            text="ドライブフォルダのパス",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="16sp",
            color=(0.3, 0.3, 0.3, 1),
            halign="left",
            valign="middle",
            text_size=(None, None)
        )
        folder_path_header.add_widget(folder_label)
        
        folder_path_help_btn = Button(
            text="?",
            size_hint=(None, None),
            size=("35dp", "35dp"),
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="14sp",
            background_color=(0.4, 0.7, 0.8, 1),  # 柔らかい水色
            color=(1, 1, 1, 1),
            background_normal=''
        )
        folder_path_help_btn.bind(on_release=self.show_folder_path_help)
        folder_path_header.add_widget(folder_path_help_btn)
        
        folder_section.add_widget(folder_path_header)
        folder_section.add_widget(self.folder_input)
        main_layout.add_widget(folder_section)

        # QRコードローカル保存フォルダパスセクション - カード風デザイン
        qr_folder_section = BoxLayout(orientation="vertical", size_hint_y=None, height="100dp", spacing=8)
        qr_folder_path_header = BoxLayout(size_hint_y=None, height="35dp", spacing=10)
        
        qr_folder_label = Label(
            text="QRコードローカル保存フォルダパス",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="16sp",
            color=(0.3, 0.3, 0.3, 1),
            halign="left",
            valign="middle",
            text_size=(None, None)
        )
        qr_folder_path_header.add_widget(qr_folder_label)
        
        qr_folder_path_help_btn = Button(
            text="?",
            size_hint=(None, None),
            size=("35dp", "35dp"),
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="14sp",
            background_color=(0.4, 0.7, 0.8, 1),  # 柔らかい水色
            color=(1, 1, 1, 1),
            background_normal=''
        )
        qr_folder_path_help_btn.bind(on_release=self.show_qr_folder_path_help)
        qr_folder_path_header.add_widget(qr_folder_path_help_btn)
        
        qr_folder_section.add_widget(qr_folder_path_header)
        qr_folder_section.add_widget(self.qr_folder_input)
        main_layout.add_widget(qr_folder_section)
        
        # P-touch Editorパスセクション - カード風デザイン
        ptouch_section = BoxLayout(orientation="vertical", size_hint_y=None, height="100dp", spacing=8)
        ptouch_path_header = BoxLayout(size_hint_y=None, height="35dp", spacing=10)
        
        ptouch_label = Label(
            text="P-touch Editorパス",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="16sp",
            color=(0.3, 0.3, 0.3, 1),
            size_hint_x=0.5,
            halign="left"
        )
        ptouch_label.text_size = (None, None)
        ptouch_path_header.add_widget(ptouch_label)
        
        # P-touch Editor自動検索ボタン
        ptouch_auto_find_btn = Button(
            text="自動検索",
            size_hint=(None, 1),
            width=80,
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="12sp",
            background_color=(0.5, 0.8, 0.6, 1),  # 柔らかい緑色
            color=(1, 1, 1, 1),
            background_normal=''
        )
        ptouch_auto_find_btn.bind(on_release=self.auto_find_ptouch_editor)
        ptouch_path_header.add_widget(ptouch_auto_find_btn)
        
        # P-touch Editorパスヘルプボタン
        ptouch_path_help_btn = Button(
            text="?",
            size_hint=(None, 1),
            width=30,
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="14sp",
            background_color=(0.4, 0.7, 0.8, 1),  # 柔らかい水色
            color=(1, 1, 1, 1),
            background_normal=''
        )
        ptouch_path_help_btn.bind(on_release=self.show_ptouch_path_help)
        ptouch_path_header.add_widget(ptouch_path_help_btn)
        
        ptouch_section.add_widget(ptouch_path_header)
        ptouch_section.add_widget(self.ptouch_path_input)
        main_layout.add_widget(ptouch_section)


        # スペーサー
        main_layout.add_widget(BoxLayout())

        # ボタンレイアウト - より洗練されたデザイン
        btn_layout = BoxLayout(size_hint_y=None, height="90dp", spacing=20, padding=[20, 10])
        
        save_btn = Button(
            text="保存",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="26sp",
            background_color=(0.5, 0.8, 0.6, 1),  # 柔らかい緑系
            color=(1, 1, 1, 1),
            background_normal=''
        )
        
        cancel_btn = Button(
            text="キャンセル",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="26sp",
            background_color=(0.6, 0.6, 0.6, 1),  # グレー系
            color=(1, 1, 1, 1),
            background_normal=''
        )
        
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        main_layout.add_widget(btn_layout)

        self.add_widget(main_layout)

        save_btn.bind(on_release=self.on_save)
        cancel_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "wait"))
        
    def _update_rect(self, instance, value):
        """背景の矩形を更新"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def show_spreadsheet_id_help(self, instance):
        title = "スプレッドシートIDの取得方法"
        message = (
            "【Google スプレッドシートIDの取得手順】\n\n"
            "1. Googleスプレッドシートを開く\n"
            "   • Google Driveまたは直接スプレッドシートにアクセス\n\n"
            "2. URLを確認する\n"
            "   • ブラウザのアドレスバーのURLをコピー\n\n"
            "3. URLの形式\n"
            "   • https://docs.google.com/spreadsheets/d/\n"
            "   • 【スプレッドシートID】\n"
            "   • /edit#gid=0\n\n"
            "4. IDを抽出\n"
            "   • 「/d/」と「/edit」の間の文字列がスプレッドシートIDです\n"
            "   • 例：1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T\n\n"
            "5. 設定に貼り付け\n"
            "   • コピーしたIDを設定画面に貼り付けてください"
        )
        popup = HelpPopup(title, message)
        popup.open()

    def show_folder_path_help(self, instance):
        title = "ドライブフォルダのパス（ID）の取得方法"
        message = (
            "【Google ドライブフォルダIDの取得手順】\n\n"
            "1. Googleドライブを開く\n"
            "   • https://drive.google.com にアクセス\n\n"
            "2. QRコード画像が保存されているフォルダを選択\n"
            "   • QRコード画像ファイルが入っているフォルダを開く\n\n"
            "3. URLを確認する\n"
            "   • フォルダを開いた状態でURLをコピー\n\n"
            "4. URLの形式\n"
            "   • https://drive.google.com/drive/folders/\n"
            "   • 【フォルダID】\n\n"
            "5. IDを抽出\n"
            "   • 「/folders/」以降の文字列がフォルダIDです\n"
            "   • 例：1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T\n\n"
            "6. 設定に貼り付け\n"
            "   • コピーしたIDを設定画面に貼り付けてください\n\n"
            "※注意※\n"
            "フォルダは共有設定で「リンクを知っている全員」に\n"
            "設定しておくことをお勧めします。"
        )
        popup = HelpPopup(title, message)
        popup.open()

    def show_qr_folder_path_help(self, instance):
        title = "QRコードローカル保存フォルダパスの設定方法"
        message = (
            "【QRコードローカル保存フォルダパス】\n\n"
            "QRコード画像をGoogle Driveからダウンロードして保存する\n"
            "ローカルフォルダのパスを設定してください。\n\n"
            "例：\n"
            "C:\\\\Users\\\\ユーザー名\\\\Pictures\\\\塾生QRコード\n\n"
            "注意事項：\n"
            "• フォルダが存在しない場合は自動的に作成されます\n"
            "• Google Driveからダウンロードしたこちらの地ファイルを\n"
            "  プレビュー表示する際に使用されます\n"
            "• パス区切り文字は \\\\\\\\ を使用してください（Windows）"
        )
        popup = HelpPopup(title, message)
        popup.open()
    
    def show_ptouch_path_help(self, instance):
        title = "P-touch Editor実行ファイルパスの設定方法"
        message = (
            "【P-touch Editor実行ファイルパス】\n\n"
            "Brother P-touch Editorの実行ファイル（ptedit54.exe）の\n"
            "フルパスを設定してください。\n\n"
            "デフォルトのインストール場所：\n"
            "C:\\\\Program Files (x86)\\\\Brother\\\\Ptedit54\\\\ptedit54.exe\n\n"
            "または\n"
            "C:\\\\Program Files\\\\Brother\\\\Ptedit54\\\\ptedit54.exe\n\n"
            "注意事項：\n"
            "• Brother P-touch Editor 5.4がインストールされている必要があります\n"
            "• 正確なファイルパスを入力してください\n"
            "• パス区切り文字は \\\\\\\\ を使用してください（Windows）"
        )
        popup = HelpPopup(title, message)
        popup.open()
    
    def auto_find_ptouch_editor(self, instance):
        """プログラムファイル内でP-touch Editorを自動検索する"""
        import os
        import threading
        
        def search_ptouch_editor():
            possible_paths = [
                r"C:\Program Files (x86)\Brother\Ptedit54\ptedit54.exe",
                r"C:\Program Files\Brother\Ptedit54\ptedit54.exe",
                r"C:\Program Files (x86)\Brother\P-touch Editor 5.4\ptedit54.exe",
                r"C:\Program Files\Brother\P-touch Editor 5.4\ptedit54.exe",
                r"C:\Program Files (x86)\Brother\P-touch Editor\ptedit54.exe",
                r"C:\Program Files\Brother\P-touch Editor\ptedit54.exe",
            ]
            
            found_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    found_path = path
                    break
            
            # メインスレッドでUIを更新
            from kivy.clock import Clock
            if found_path:
                Clock.schedule_once(lambda dt: self._update_ptouch_path(found_path), 0)
                Clock.schedule_once(lambda dt: show_error_popup("検索結果", f"P-touch Editorが見つかりました！\n{found_path}"), 0)
            else:
                Clock.schedule_once(lambda dt: show_error_popup("検索結果", "P-touch Editorが見つかりませんでした。\n手動でパスを設定してください。"), 0)
        
        # 検索中メッセージを表示
        show_error_popup("検索中", "P-touch Editorを検索中です...")
        
        # 別スレッドで検索実行
        threading.Thread(target=search_ptouch_editor).start()
    
    def _update_ptouch_path(self, path):
        """検索結果でパスを更新する"""
        self.ptouch_path_input.text = path

    def on_pre_enter(self, *_):
        data = load_settings()
        self.spread_input.text = data.get('spreadsheet_id', '')
        self.folder_input.text = data.get('drive_qr_folder_id', '')  # 統一したフィールド名
        self.qr_folder_input.text = data.get('qr_code_folder', '')
        self.ptouch_path_input.text = data.get('ptouch_editor_path', r'C:\Program Files (x86)\Brother\Ptedit54\ptedit54.exe')

    def on_save(self, *_):
        data = {
            'spreadsheet_id': self.spread_input.text.strip(),
            'drive_qr_folder_id': self.folder_input.text.strip(),  # 統一したフィールド名
            'qr_code_folder': self.qr_folder_input.text.strip(),
            'ptouch_editor_path': self.ptouch_path_input.text.strip(),
        }
        save_settings(data)
        self.manager.current = "wait"


class LoadingScreen(Screen):
    def on_enter(self, *args):
        self.clear_widgets()
        
        # 背景色設定（薄いグレー）
        from kivy.graphics import Color, Rectangle
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # 薄いグレー背景
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        layout = BoxLayout(orientation="vertical", padding=60, spacing=30)
        
        # ローディングラベル - より視認性の高いデザイン
        loading_label = Label(
            text="読み込み中...",
            font_name="UDDigiKyokashoN-R" if FONT_AVAILABLE else "Roboto",
            font_size="32sp",
            color=(0.4, 0.4, 0.4, 1),  # ミディアムグレー
            halign="center",
            valign="middle"
        )
        loading_label.text_size = (None, None)
        layout.add_widget(loading_label)
        
        self.add_widget(layout)
        
    def _update_rect(self, instance, value):
        """背景の矩形を更新"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size


# --- アプリ本体 ---
class AttendanceApp(App):
    def build(self):
        # スプレッドシートIDが設定されているか確認
        settings = load_settings()
        if not settings.get('spreadsheet_id'):
            show_error_popup("警告", "スプレッドシートIDが設定されていません")

        sm = ScreenManager(transition=FadeTransition())
        self.screen_manager = sm
        sm.add_widget(WaitScreen(name="wait"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(LoadingScreen(name="loading"))
        sm.add_widget(PrintScreen(name="print_screen")) # PrintScreenを追加
        sm.add_widget(ReportScreen(name="report")) # ReportScreenを追加
        sm.add_widget(ReportEditorScreen(name="report_editor")) # ReportEditorScreenを追加
        sm.add_widget(GreetingScreen(name="greeting"))

        # 各質問画面
        sm.add_widget(
            QuestionScreen(
                key="q1",
                question="Q1.今日の気分は？",
                next_screen="q2",
                question_type="weather",
                name="q1",
            )
        )
        sm.add_widget(
            QuestionScreen(
                key="q2",
                question="Q2.昨日の睡眠の満足度は？",
                next_screen="q3",
                question_type="sleep",
                name="q2",
            )
        )
        sm.add_widget(
            QuestionScreen(
                key="q3",
                question="Q3.今日は何しに来た？",
                next_screen="welcome",
                question_type="purpose",
                name="q3",
            )
        )

        sm.add_widget(WelcomeScreen(name="welcome"))
        sm.add_widget(GoodbyeScreen(name="goodbye"))
        return sm




# === ここから追記 ==========================================
def main() -> None:
    """
    CLI エントリポイント.
    `python -m attendance_app` から呼ばれる。
    """
    # 既存の GUI 起動処理を呼び出す
    AttendanceApp().run()


if __name__ == "__main__":  # 単体実行も可能にしておく
    main()
# === ここまで追記 ==========================================
import os
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.text import LabelBase

from .config import load_settings, save_settings
from .report_system.excel_report_generator import generate_excel_reports
from .report_system.data_analyzer import get_students_with_attendance, get_all_students_list
from .report_system.utils import get_current_month_year, get_month_name_japanese, list_generated_reports


class ReportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "report"
        self.setup_font()
        self.create_ui()
        
    def setup_font(self):
        """フォントの設定"""
        try:
            font_path = Path(__file__).parent / "assets" / "fonts" / "UDDigiKyokashoN-R.ttc"
            if font_path.exists():
                LabelBase.register(name="UDDigiKyokashoN-R", fn_regular=str(font_path))
                self.font_available = True
                print(f"ReportScreen: フォントを登録しました: {font_path}")
            else:
                self.font_available = False
                print(f"ReportScreen: フォントファイルが見つかりません: {font_path}")
        except Exception as e:
            self.font_available = False
            print(f"ReportScreen: フォント設定エラー: {e}")
            
    def get_font_name(self):
        """適切なフォント名を取得"""
        return "UDDigiKyokashoN-R" if self.font_available else "Roboto"
        
    def create_ui(self):
        """レポート画面のUIを作成"""
        # メインレイアウト
        main_layout = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=[20, 20, 20, 20]
        )
        
        # 背景色を設定
        with main_layout.canvas.before:
            Color(0.95, 0.97, 0.98, 1)  # 柔らかい水色背景
            self.rect = Rectangle(size=main_layout.size, pos=main_layout.pos)
            
        main_layout.bind(size=self._update_rect, pos=self._update_rect)
        
        # タイトル
        title_label = Label(
            text="月次レポート生成",
            font_name=self.get_font_name(),
            font_size="24sp",
            size_hint_y=None,
            height="60dp",
            color=(0.17, 0.24, 0.31, 1)  # ダークブルーグレー
        )
        main_layout.add_widget(title_label)
        
        # タイトル下のスペース
        main_layout.add_widget(BoxLayout(size_hint_y=None, height="10dp"))
        
        # 年月選択セクション
        date_section = self.create_date_selection_section()
        main_layout.add_widget(date_section)
        
        # セクション間のスペース
        main_layout.add_widget(BoxLayout(size_hint_y=None, height="15dp"))
        
        # 生成オプションセクション
        options_section = self.create_options_section()
        main_layout.add_widget(options_section)
        
        # 進捗表示ラベル
        self.progress_label = Label(
            text="",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="30dp",
            color=(0.5, 0.5, 0.5, 1)
        )
        main_layout.add_widget(self.progress_label)
        
        # 生成されたレポートのリスト
        reports_section = self.create_reports_list_section()
        main_layout.add_widget(reports_section)
        
        # 戻るボタン
        back_button = Button(
            text="メインメニューに戻る",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="50dp",
            background_color=(0.286, 0.796, 0.98, 1)
        )
        back_button.bind(on_press=self.go_back)
        main_layout.add_widget(back_button)
        
        self.add_widget(main_layout)
        
    def _update_rect(self, instance, value):
        """背景の矩形を更新"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        
    def create_date_selection_section(self):
        """年月選択セクションを作成"""
        section = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height="120dp",
            spacing=10
        )
        
        # セクションタイトル
        section_title = Label(
            text="対象年月の選択",
            font_name=self.get_font_name(),
            font_size="18sp",
            size_hint_y=None,
            height="30dp",
            color=(0.17, 0.24, 0.31, 1)
        )
        section.add_widget(section_title)
        
        # 年月選択UI - 横一列レイアウト
        date_layout = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="60dp",
            spacing=15,
            padding=[20, 10]
        )
        
        # 現在の年月を取得
        current_year, current_month = get_current_month_year()
        
        # 対象年月の選択ラベル
        select_label = Label(
            text="対象年月の選択：",
            font_name=self.get_font_name(),
            font_size="16sp",
            size_hint_x=None,
            width="120dp",
            color=(0.17, 0.24, 0.31, 1)
        )
        date_layout.add_widget(select_label)
        
        # 年選択
        self.year_spinner = Spinner(
            text=str(current_year),
            values=[str(year) for year in range(2020, 2030)],
            font_name=self.get_font_name(),
            font_size="16sp",
            size_hint_x=None,
            width="80dp"
        )
        date_layout.add_widget(self.year_spinner)
        
        # 年ラベル
        year_label = Label(
            text="年",
            font_name=self.get_font_name(),
            font_size="16sp",
            size_hint_x=None,
            width="30dp",
            color=(0.17, 0.24, 0.31, 1)
        )
        date_layout.add_widget(year_label)
        
        # 月選択
        self.month_spinner = Spinner(
            text=str(current_month),
            values=[str(month) for month in range(1, 13)],
            font_name=self.get_font_name(),
            font_size="16sp",
            size_hint_x=None,
            width="80dp"
        )
        date_layout.add_widget(self.month_spinner)
        
        # 月ラベル
        month_label = Label(
            text="月",
            font_name=self.get_font_name(),
            font_size="16sp",
            size_hint_x=None,
            width="30dp",
            color=(0.17, 0.24, 0.31, 1)
        )
        date_layout.add_widget(month_label)
        
        section.add_widget(date_layout)
        
        return section
        
    def create_options_section(self):
        """生成オプションセクションを作成"""
        section = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height="140dp",
            spacing=10
        )
        
        # セクションタイトル
        section_title = Label(
            text="レポート生成オプション",
            font_name=self.get_font_name(),
            font_size="18sp",
            size_hint_y=None,
            height="30dp",
            color=(0.17, 0.24, 0.31, 1)
        )
        section.add_widget(section_title)
        
        # ボタンレイアウト
        button_layout = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="60dp",
            spacing=10
        )
        
        # 全生徒Excelレポート生成ボタン（ヘルプ付き）
        all_excel_container = BoxLayout(orientation="horizontal", spacing=5)
        all_excel_button = Button(
            text="全生徒Excelレポート生成",
            font_name=self.get_font_name(),
            background_color=(0.61, 0.35, 0.71, 1)  # 紫色
        )
        all_excel_button.bind(on_press=self.generate_all_excel_reports)
        all_excel_help_btn = Button(
            text="?",
            font_name=self.get_font_name(),
            size_hint_x=None,
            width="30dp",
            background_color=(0.7, 0.7, 0.7, 1)
        )
        all_excel_help_btn.bind(on_press=lambda x: self.show_help_popup("全生徒Excelレポート生成", "指定した年月に出席記録がある全ての生徒の\nExcelレポートを一括で生成します。"))
        all_excel_container.add_widget(all_excel_button)
        all_excel_container.add_widget(all_excel_help_btn)
        button_layout.add_widget(all_excel_container)
        
        # 生成されたレポートを開くボタン（ヘルプ付き）
        open_container = BoxLayout(orientation="horizontal", spacing=5)
        open_button = Button(
            text="レポートフォルダを開く",
            font_name=self.get_font_name(),
            background_color=(0.85, 0.65, 0.13, 1)  # オレンジ色
        )
        open_button.bind(on_press=self.open_reports_folder)
        open_help_btn = Button(
            text="?",
            font_name=self.get_font_name(),
            size_hint_x=None,
            width="30dp",
            background_color=(0.7, 0.7, 0.7, 1)
        )
        open_help_btn.bind(on_press=lambda x: self.show_help_popup("レポートフォルダを開く", "生成されたPDFレポートが保存されている\nフォルダをエクスプローラーで開きます。"))
        open_container.add_widget(open_button)
        open_container.add_widget(open_help_btn)
        button_layout.add_widget(open_container)
        
        
        
        section.add_widget(button_layout)
        
        return section
        
    def create_reports_list_section(self):
        """生成されたレポートのリストセクションを作成"""
        section = BoxLayout(
            orientation="vertical",
            spacing=10
        )
        
        # セクションタイトル
        section_title = Label(
            text="生成されたレポート",
            font_name=self.get_font_name(),
            font_size="18sp",
            size_hint_y=None,
            height="30dp",
            color=(0.17, 0.24, 0.31, 1)
        )
        section.add_widget(section_title)
        
        # リスト更新ボタン
        refresh_button = Button(
            text="リストを更新",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="40dp",
            background_color=(0.286, 0.796, 0.98, 1)
        )
        refresh_button.bind(on_press=self.refresh_reports_list)
        section.add_widget(refresh_button)
        
        # スクロール可能なリスト
        scroll = ScrollView()
        
        self.reports_list_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=5
        )
        self.reports_list_layout.bind(minimum_height=self.reports_list_layout.setter('height'))
        
        scroll.add_widget(self.reports_list_layout)
        section.add_widget(scroll)
        
        # 初期リストを読み込み
        self.refresh_reports_list()
        
        return section
        
    def refresh_reports_list(self, instance=None):
        """レポートリストを更新"""
        self.reports_list_layout.clear_widgets()
        
        reports = list_generated_reports()
        
        if not reports:
            no_reports_label = Label(
                text="生成されたレポートはありません",
                font_name=self.get_font_name(),
                size_hint_y=None,
                height="40dp",
                color=(0.5, 0.5, 0.5, 1)
            )
            self.reports_list_layout.add_widget(no_reports_label)
        else:
            for report in reports:
                report_layout = BoxLayout(
                    orientation="horizontal",
                    size_hint_y=None,
                    height="40dp",
                    spacing=10
                )
                
                # ファイル名
                name_label = Label(
                    text=report['name'],
                    font_name=self.get_font_name(),
                    size_hint_x=0.6,
                    text_size=(None, None),
                    halign="left",
                    color=(0.17, 0.24, 0.31, 1)  # ダークブルーグレー
                )
                report_layout.add_widget(name_label)
                
                # ファイルサイズ
                size_label = Label(
                    text=report['size_formatted'],
                    font_name=self.get_font_name(),
                    size_hint_x=0.15,
                    color=(0.5, 0.5, 0.5, 1)
                )
                report_layout.add_widget(size_label)
                
                # 開くボタン
                open_btn = Button(
                    text="開く",
                    font_name=self.get_font_name(),
                    size_hint_x=0.125,
                    background_color=(0.286, 0.796, 0.98, 1)
                )
                open_btn.bind(on_press=lambda x, path=report['full_path']: self.open_report(path))
                report_layout.add_widget(open_btn)
                
                # 削除ボタン
                delete_btn = Button(
                    text="削除",
                    font_name=self.get_font_name(),
                    size_hint_x=0.125,
                    background_color=(0.85, 0.40, 0.40, 1)  # 赤色
                )
                delete_btn.bind(on_press=lambda x, path=report['full_path'], name=report['name']: self.delete_report(path, name))
                report_layout.add_widget(delete_btn)
                
                self.reports_list_layout.add_widget(report_layout)
        
        
    def show_student_selection(self, instance):
        """生徒選択ダイアログを表示"""
        try:
            year = int(self.year_spinner.text)
            month = int(self.month_spinner.text)
            
            students = get_students_with_attendance(year, month)
            
            if not students:
                self.show_popup("エラー", f"{year}年{month}月に出席記録がある生徒はいません")
                return
                
            # 生徒選択ポップアップを作成
            content = BoxLayout(orientation="vertical", spacing=10)
            
            scroll = ScrollView()
            students_layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=5)
            students_layout.bind(minimum_height=students_layout.setter('height'))
            
            for student in students:
                btn = Button(
                    text=f"{student['name']} ({student['id']})",
                    font_name=self.get_font_name(),
                    size_hint_y=None,
                    height="40dp"
                )
                btn.bind(on_press=lambda x, s=student: self.generate_individual_report(s))
                students_layout.add_widget(btn)
                
            scroll.add_widget(students_layout)
            content.add_widget(scroll)
            
            # 閉じるボタン
            close_btn = Button(
                text="閉じる", 
                font_name=self.get_font_name(),
                size_hint_y=None, 
                height="40dp"
            )
            content.add_widget(close_btn)
            
            popup = Popup(
                title="生徒を選択してください",
                content=content,
                size_hint=(0.8, 0.8)
            )
            close_btn.bind(on_press=popup.dismiss)
            popup.open()
            
        except Exception as e:
            self.show_popup("エラー", f"生徒リストの取得中にエラーが発生しました: {e}")
            
    def generate_individual_report(self, student):
        """個別レポートを生成"""
        year = int(self.year_spinner.text)
        month = int(self.month_spinner.text)
        
        self.progress_label.text = f"{student['name']}のレポートを生成中..."
        
        def generate_in_thread():
            try:
                pdf_path = generate_monthly_report(student['id'], year, month)
                Clock.schedule_once(lambda dt: self.on_generation_complete(pdf_path, f"{student['name']}のレポートが生成されました"))
            except Exception as e:
                error_msg = str(e)
                Clock.schedule_once(lambda dt: self.on_generation_error(error_msg))
        
        threading.Thread(target=generate_in_thread, daemon=True).start()
        
    def generate_all_excel_reports(self, instance):
        """全生徒のExcelレポートを生成"""
        year = int(self.year_spinner.text)
        month = int(self.month_spinner.text)
        
        # 入力値の検証
        if not (2020 <= year <= 2030): # 例: 2020年から2030年の範囲
            self.show_popup("エラー", "有効な年を選択してください (2020-2030)。")
            return
        if not (1 <= month <= 12):
            self.show_popup("エラー", "有効な月を選択してください (1-12)。")
            return

        # スプレッドシートにデータが存在するかチェック
        students_with_data = get_students_with_attendance(year, month)
        if not students_with_data:
            self.show_popup("エラー", f"{year}年{month}月には出席記録がありません。")
            return

        self.progress_label.text = "データを取得中..."
        
        def generate_in_thread():
            try:
                # 対象生徒を事前に取得
                students_with_data = get_students_with_attendance(year, month)
                Clock.schedule_once(lambda dt: self.update_progress("Excelレポートを生成中..."))
                
                excel_path = generate_excel_reports(year, month)
                
                # 成功メッセージに対象者リストを含める
                student_list = "\n".join([f"• {s['name']} (ID: {s['id']})" for s in students_with_data])
                message = f"""Excel月次レポートが生成されました

【重要】対象者を確認してください（{len(students_with_data)}名）:
{student_list}

※ 対象者が少ない場合は、もう一度生成してください

ファイル: {os.path.basename(excel_path)}"""
                
                Clock.schedule_once(lambda dt: self.on_generation_complete(excel_path, message))
            except Exception as e:
                error_msg = str(e)
                Clock.schedule_once(lambda dt: self.on_generation_error(error_msg))
        
        threading.Thread(target=generate_in_thread, daemon=True).start()
        
    def open_reports_folder(self, instance):
        """レポートフォルダを開く"""
        try:
            reports_dir = Path(__file__).parent / "output" / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Windowsのエクスプローラーで開く
            os.startfile(str(reports_dir))
        except Exception as e:
            self.show_popup("エラー", f"フォルダを開けませんでした: {e}")
            
    def open_report_editor(self, instance):
        """レポートエディタをブラウザで開く"""
        try:
            # ローカルのFlaskアプリケーションURL
            editor_url = "http://localhost:5000"
            webbrowser.open(editor_url)
        except Exception as e:
            self.show_popup("エラー", f"ブラウザでレポートエディタを開けませんでした: {e}")
            
    def open_report(self, file_path):
        """レポートファイルを開く"""
        try:
            os.startfile(file_path)
        except Exception as e:
            self.show_popup("エラー", f"ファイルを開けませんでした: {e}")
            
    def delete_report(self, file_path, file_name):
        """レポートファイルを削除"""
        # 確認ダイアログを表示
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        confirm_label = Label(
            text=f"以下のファイルを削除しますか？\n\n{file_name}",
            font_name=self.get_font_name(),
            text_size=(None, None),
            halign="center",
            valign="middle"
        )
        content.add_widget(confirm_label)
        
        button_layout = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height="40dp")
        
        # キャンセルボタン
        cancel_btn = Button(
            text="キャンセル",
            font_name=self.get_font_name(),
            background_color=(0.7, 0.7, 0.7, 1)
        )
        button_layout.add_widget(cancel_btn)
        
        # 削除ボタン
        confirm_delete_btn = Button(
            text="削除する",
            font_name=self.get_font_name(),
            background_color=(0.85, 0.40, 0.40, 1)
        )
        button_layout.add_widget(confirm_delete_btn)
        
        content.add_widget(button_layout)
        
        popup = Popup(
            title="ファイル削除の確認",
            content=content,
            size_hint=(0.6, 0.4)
        )
        
        def do_delete(instance):
            try:
                os.remove(file_path)
                popup.dismiss()
                self.refresh_reports_list()
                self.show_popup("削除完了", f"ファイルを削除しました: {file_name}")
            except Exception as e:
                popup.dismiss()
                self.show_popup("エラー", f"ファイルを削除できませんでした: {e}")
        
        cancel_btn.bind(on_press=popup.dismiss)
        confirm_delete_btn.bind(on_press=do_delete)
        popup.open()
            
    def update_progress(self, message):
        """進捗表示を更新"""
        self.progress_label.text = message
        
    def on_generation_complete(self, pdf_path, message):
        """生成完了時の処理"""
        self.progress_label.text = ""
        self.refresh_reports_list()
        self.show_detailed_popup("完了", message)
        
    def on_generation_error(self, error_message):
        """生成エラー時の処理"""
        self.progress_label.text = ""
        self.show_popup("エラー", f"レポート生成中にエラーが発生しました: {error_message}")
        
    def show_popup(self, title, message):
        """ポップアップを表示"""
        popup = Popup(
            title=title,
            content=Label(text=message, font_name=self.get_font_name()),
            size_hint=(0.8, 0.4)
        )
        popup.open()
        
    def show_detailed_popup(self, title, message):
        """詳細情報を表示するポップアップ"""
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        # スクロール可能なテキスト表示
        scroll = ScrollView()
        message_label = Label(
            text=message,
            font_name=self.get_font_name(),
            text_size=(None, None),
            halign="left",
            valign="top",
            markup=True
        )
        scroll.add_widget(message_label)
        content.add_widget(scroll)
        
        # 閉じるボタン
        close_btn = Button(
            text="閉じる",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="40dp",
            background_color=(0.286, 0.796, 0.98, 1)
        )
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.9, 0.8)
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
        
    def show_help_popup(self, title, message):
        """ヘルプポップアップを表示"""
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        help_label = Label(
            text=message,
            font_name=self.get_font_name(),
            text_size=(None, None),
            halign="center",
            valign="middle"
        )
        content.add_widget(help_label)
        
        close_btn = Button(
            text="閉じる",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="40dp",
            background_color=(0.286, 0.796, 0.98, 1)
        )
        content.add_widget(close_btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.5)
        )
        close_btn.bind(on_press=popup.dismiss)
        popup.open()
        
    def go_back(self, instance):
        """メインメニューに戻る"""
        self.manager.current = "wait"
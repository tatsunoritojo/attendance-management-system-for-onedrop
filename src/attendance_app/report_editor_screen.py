import json
import threading
from pathlib import Path
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.core.text import LabelBase
from kivy.clock import Clock

from .report_system.template_loader import load_report_template, save_report_template, get_template_path
from .report_system.report_generator import generate_sample_report_with_dummy_data
from .report_system.preview_generator import generate_report_preview, create_layout_preview


class ReportEditorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "report_editor"
        self.template_data = load_report_template()
        self.setup_font()
        self.create_ui()
        
    def setup_font(self):
        """フォントの設定"""
        try:
            font_path = Path(__file__).parent / "assets" / "fonts" / "UDDigiKyokashoN-R.ttc"
            if font_path.exists():
                LabelBase.register(name="UDDigiKyokashoN-R", fn_regular=str(font_path))
                self.font_available = True
            else:
                self.font_available = False
        except Exception as e:
            self.font_available = False
            print(f"ReportEditorScreen: フォント設定エラー: {e}")
            
    def get_font_name(self):
        """適切なフォント名を取得"""
        return "UDDigiKyokashoN-R" if self.font_available else "Roboto"
        
    def create_ui(self):
        """レポートエディタのUIを作成"""
        # メインレイアウト
        main_layout = BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=[15, 15, 15, 15]
        )
        
        # 背景色を設定
        with main_layout.canvas.before:
            Color(0.97, 0.98, 0.99, 1)  # 薄いグレー背景
            self.rect = Rectangle(size=main_layout.size, pos=main_layout.pos)
            
        main_layout.bind(size=self._update_rect, pos=self._update_rect)
        
        # タイトル
        title_label = Label(
            text="レポートレイアウトエディタ",
            font_name=self.get_font_name(),
            font_size="20sp",
            size_hint_y=None,
            height="50dp",
            color=(0.2, 0.3, 0.4, 1)
        )
        main_layout.add_widget(title_label)
        
        # メインコンテンツレイアウト
        content_layout = BoxLayout(
            orientation="horizontal",
            spacing=10
        )
        
        # 左側: タブパネル
        left_panel = BoxLayout(
            orientation="vertical",
            size_hint_x=0.6
        )
        
        tab_panel = TabbedPanel(
            do_default_tab=False,
            tab_height="40dp"
        )
        
        # 基本設定タブ
        basic_tab = TabbedPanelItem(
            text="基本設定",
            font_name=self.get_font_name()
        )
        basic_tab.add_widget(self.create_basic_settings_panel())
        tab_panel.add_widget(basic_tab)
        
        # セクション設定タブ
        sections_tab = TabbedPanelItem(
            text="セクション設定",
            font_name=self.get_font_name()
        )
        sections_tab.add_widget(self.create_sections_panel())
        tab_panel.add_widget(sections_tab)
        
        # レイアウト設定タブ
        layout_tab = TabbedPanelItem(
            text="レイアウト設定",
            font_name=self.get_font_name()
        )
        layout_tab.add_widget(self.create_layout_panel())
        tab_panel.add_widget(layout_tab)
        
        # デザイン設定タブ
        design_tab = TabbedPanelItem(
            text="デザイン設定",
            font_name=self.get_font_name()
        )
        design_tab.add_widget(self.create_design_panel())
        tab_panel.add_widget(design_tab)
        
        # JSONエディタタブ
        json_tab = TabbedPanelItem(
            text="詳細設定",
            font_name=self.get_font_name()
        )
        json_tab.add_widget(self.create_json_editor_panel())
        tab_panel.add_widget(json_tab)
        
        left_panel.add_widget(tab_panel)
        
        # 右側: プレビューパネル
        right_panel = BoxLayout(
            orientation="vertical",
            size_hint_x=0.4,
            spacing=10
        )
        
        # プレビュータイトル
        preview_title = Label(
            text="リアルタイムプレビュー",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="30dp",
            color=(0.2, 0.3, 0.4, 1)
        )
        right_panel.add_widget(preview_title)
        
        # プレビュー画像
        self.preview_image = Image(
            source="",
            size_hint_y=0.6
        )
        right_panel.add_widget(self.preview_image)
        
        # レイアウトプレビュー
        layout_preview_title = Label(
            text="レイアウト構成",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="30dp",
            color=(0.2, 0.3, 0.4, 1)
        )
        right_panel.add_widget(layout_preview_title)
        
        self.layout_preview_image = Image(
            source="",
            size_hint_y=0.4
        )
        right_panel.add_widget(self.layout_preview_image)
        
        content_layout.add_widget(left_panel)
        content_layout.add_widget(right_panel)
        
        main_layout.add_widget(content_layout)
        
        # 初期プレビュー生成
        self.update_preview()
        
        # ボタンエリア
        button_layout = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="60dp",
            spacing=10
        )
        
        # プレビューボタン
        preview_btn = Button(
            text="プレビュー生成",
            font_name=self.get_font_name(),
            background_color=(0.3, 0.7, 0.4, 1)
        )
        preview_btn.bind(on_press=self.generate_preview)
        button_layout.add_widget(preview_btn)
        
        # 保存ボタン
        save_btn = Button(
            text="設定を保存",
            font_name=self.get_font_name(),
            background_color=(0.286, 0.796, 0.98, 1)
        )
        save_btn.bind(on_press=self.save_settings)
        button_layout.add_widget(save_btn)
        
        # リセットボタン
        reset_btn = Button(
            text="デフォルトに戻す",
            font_name=self.get_font_name(),
            background_color=(0.8, 0.5, 0.2, 1)
        )
        reset_btn.bind(on_press=self.reset_to_default)
        button_layout.add_widget(reset_btn)
        
        # 戻るボタン
        back_btn = Button(
            text="戻る",
            font_name=self.get_font_name(),
            background_color=(0.6, 0.6, 0.6, 1)
        )
        back_btn.bind(on_press=self.go_back)
        button_layout.add_widget(back_btn)
        
        main_layout.add_widget(button_layout)
        
        # 進捗表示
        self.progress_label = Label(
            text="",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="30dp",
            color=(0.5, 0.5, 0.5, 1)
        )
        main_layout.add_widget(self.progress_label)
        
        self.add_widget(main_layout)
        
    def _update_rect(self, instance, value):
        """背景の矩形を更新"""
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        
    def create_basic_settings_panel(self):
        """基本設定パネルを作成"""
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        # レポートタイトル
        title_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height="40dp")
        title_layout.add_widget(Label(
            text="レポートタイトル:",
            font_name=self.get_font_name(),
            size_hint_x=0.3
        ))
        self.title_input = TextInput(
            text=self.template_data.get("report_title", ""),
            font_name=self.get_font_name(),
            size_hint_x=0.7
        )
        self.title_input.bind(text=lambda instance, value: self.update_preview())
        title_layout.add_widget(self.title_input)
        layout.add_widget(title_layout)
        
        # 余白設定
        layout.add_widget(Label(
            text="ページ余白設定",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="30dp"
        ))
        
        margins = self.template_data.get("formatting", {}).get("page_margins", {})
        self.margin_sliders = {}
        
        for margin_type, default_value in [
            ("top", 1.2), ("bottom", 1.2), ("left", 1.2), ("right", 1.2)
        ]:
            margin_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height="40dp")
            margin_layout.add_widget(Label(
                text=f"{margin_type.capitalize()}:",
                font_name=self.get_font_name(),
                size_hint_x=0.2
            ))
            
            slider = Slider(
                min=0.5, max=3.0, step=0.1,
                value=margins.get(margin_type, default_value),
                size_hint_x=0.6
            )
            self.margin_sliders[margin_type] = slider
            slider.bind(value=lambda instance, value: self.update_preview())
            margin_layout.add_widget(slider)
            
            value_label = Label(
                text=f"{slider.value:.1f}cm",
                font_name=self.get_font_name(),
                size_hint_x=0.2
            )
            slider.bind(value=lambda instance, value, label=value_label: 
                        setattr(label, 'text', f"{value:.1f}cm"))
            margin_layout.add_widget(value_label)
            
            layout.add_widget(margin_layout)
        
        return layout
        
    def create_sections_panel(self):
        """セクション設定パネルを作成"""
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        sections = self.template_data.get("sections", {})
        self.section_widgets = {}
        
        for section_key, section_data in sections.items():
            # セクション枠
            section_frame = BoxLayout(
                orientation="vertical",
                spacing=5,
                size_hint_y=None,
                height="120dp"
            )
            
            # セクション名
            section_frame.add_widget(Label(
                text=section_data.get("title", section_key),
                font_name=self.get_font_name(),
                size_hint_y=None,
                height="30dp",
                color=(0.3, 0.3, 0.3, 1)
            ))
            
            # 有効/無効スイッチ
            enabled_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height="40dp")
            enabled_layout.add_widget(Label(
                text="有効:",
                font_name=self.get_font_name(),
                size_hint_x=0.3
            ))
            enabled_switch = Switch(
                active=section_data.get("enabled", True),
                size_hint_x=0.7
            )
            enabled_switch.bind(active=lambda instance, value: self.update_preview())
            enabled_layout.add_widget(enabled_switch)
            section_frame.add_widget(enabled_layout)
            
            # タイトル編集
            title_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height="40dp")
            title_layout.add_widget(Label(
                text="タイトル:",
                font_name=self.get_font_name(),
                size_hint_x=0.3
            ))
            title_input = TextInput(
                text=section_data.get("title", ""),
                font_name=self.get_font_name(),
                size_hint_x=0.7
            )
            title_input.bind(text=lambda instance, value: self.update_preview())
            title_layout.add_widget(title_input)
            section_frame.add_widget(title_layout)
            
            self.section_widgets[section_key] = {
                "enabled": enabled_switch,
                "title": title_input
            }
            
            layout.add_widget(section_frame)
        
        scroll.add_widget(layout)
        return scroll
        
    def create_layout_panel(self):
        """レイアウト設定パネルを作成"""
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        # レイアウトタイトル
        layout.add_widget(Label(
            text="セクション配置順序",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="30dp"
        ))
        
        # セクション順序設定
        self.section_order_widgets = {}
        sections = self.template_data.get("sections", {})
        
        # 位置順にソート
        sorted_sections = sorted(
            sections.items(),
            key=lambda x: x[1].get("position", 0)
        )
        
        for section_key, section_data in sorted_sections:
            if not section_data.get("enabled", True):
                continue
                
            section_layout = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height="40dp",
                spacing=10
            )
            
            # セクション名
            section_layout.add_widget(Label(
                text=section_data.get("title", section_key),
                font_name=self.get_font_name(),
                size_hint_x=0.5
            ))
            
            # 位置設定スライダー
            position_slider = Slider(
                min=1, max=5, step=1,
                value=section_data.get("position", 1),
                size_hint_x=0.3
            )
            position_slider.bind(value=self.on_position_change)
            self.section_order_widgets[section_key] = position_slider
            section_layout.add_widget(position_slider)
            
            # 位置表示
            position_label = Label(
                text=f"{int(position_slider.value)}",
                font_name=self.get_font_name(),
                size_hint_x=0.1
            )
            position_slider.bind(value=lambda instance, value, label=position_label: 
                                setattr(label, 'text', f"{int(value)}"))
            section_layout.add_widget(position_label)
            
            # 上下移動ボタン
            up_btn = Button(
                text="↑",
                size_hint_x=0.05,
                background_color=(0.7, 0.7, 0.9, 1)
            )
            up_btn.bind(on_press=lambda x, key=section_key: self.move_section_up(key))
            section_layout.add_widget(up_btn)
            
            down_btn = Button(
                text="↓",
                size_hint_x=0.05,
                background_color=(0.7, 0.7, 0.9, 1)
            )
            down_btn.bind(on_press=lambda x, key=section_key: self.move_section_down(key))
            section_layout.add_widget(down_btn)
            
            layout.add_widget(section_layout)
        
        scroll.add_widget(layout)
        return scroll
        
    def create_design_panel(self):
        """デザイン設定パネルを作成"""
        scroll = ScrollView()
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        # フォントサイズ設定
        layout.add_widget(Label(
            text="フォントサイズ設定",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="30dp"
        ))
        
        fonts = self.template_data.get("formatting", {}).get("fonts", {})
        self.font_sliders = {}
        
        for font_type, default_size in [
            ("title_size", 18), ("heading_size", 13), ("normal_size", 10), ("stats_size", 11)
        ]:
            font_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height="40dp")
            font_layout.add_widget(Label(
                text=f"{font_type.replace('_', ' ').title()}:",
                font_name=self.get_font_name(),
                size_hint_x=0.3
            ))
            
            slider = Slider(
                min=8, max=24, step=1,
                value=fonts.get(font_type, default_size),
                size_hint_x=0.5
            )
            self.font_sliders[font_type] = slider
            slider.bind(value=lambda instance, value: self.update_preview())
            font_layout.add_widget(slider)
            
            value_label = Label(
                text=f"{int(slider.value)}pt",
                font_name=self.get_font_name(),
                size_hint_x=0.2
            )
            slider.bind(value=lambda instance, value, label=value_label: 
                        setattr(label, 'text', f"{int(value)}pt"))
            font_layout.add_widget(value_label)
            
            layout.add_widget(font_layout)
        
        scroll.add_widget(layout)
        return scroll
        
    def on_position_change(self, instance, value):
        """位置変更時の処理"""
        self.update_preview()
        
    def move_section_up(self, section_key):
        """セクションを上に移動"""
        if section_key in self.section_order_widgets:
            slider = self.section_order_widgets[section_key]
            if slider.value > 1:
                slider.value -= 1
                
    def move_section_down(self, section_key):
        """セクションを下に移動"""
        if section_key in self.section_order_widgets:
            slider = self.section_order_widgets[section_key]
            if slider.value < 5:
                slider.value += 1
                
    def update_preview(self):
        """プレビューを更新"""
        def update_in_thread():
            try:
                # 現在の設定を収集
                self.collect_settings()
                
                # プレビュー生成
                preview_path = generate_report_preview(self.template_data)
                layout_path = create_layout_preview(self.template_data)
                
                # UIスレッドで画像を更新
                Clock.schedule_once(lambda dt: self.update_preview_images(preview_path, layout_path))
                
            except Exception as e:
                print(f"プレビュー更新エラー: {e}")
                
        threading.Thread(target=update_in_thread, daemon=True).start()
        
    def update_preview_images(self, preview_path, layout_path):
        """プレビュー画像を更新"""
        if preview_path:
            self.preview_image.source = preview_path
            self.preview_image.reload()
            
        if layout_path:
            self.layout_preview_image.source = layout_path
            self.layout_preview_image.reload()
        
    def create_json_editor_panel(self):
        """JSON編集パネルを作成"""
        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)
        
        # 説明
        layout.add_widget(Label(
            text="詳細設定 (JSON形式)",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="30dp"
        ))
        
        # JSONテキストエリア
        self.json_editor = TextInput(
            text=json.dumps(self.template_data, ensure_ascii=False, indent=2),
            font_name="Roboto",
            font_size="12sp",
            multiline=True
        )
        layout.add_widget(self.json_editor)
        
        # 更新ボタン
        update_btn = Button(
            text="JSONから更新",
            font_name=self.get_font_name(),
            size_hint_y=None,
            height="40dp"
        )
        update_btn.bind(on_press=self.update_from_json)
        layout.add_widget(update_btn)
        
        return layout
        
    def update_from_json(self, instance):
        """JSON編集内容を反映"""
        try:
            new_data = json.loads(self.json_editor.text)
            self.template_data = new_data
            self.show_popup("成功", "JSON設定が更新されました")
        except json.JSONDecodeError as e:
            self.show_popup("エラー", f"JSON形式エラー: {e}")
            
    def generate_preview(self, instance):
        """プレビューレポートを生成"""
        self.progress_label.text = "プレビューを生成中..."
        
        def generate_in_thread():
            try:
                # 現在の設定を保存
                self.collect_settings()
                save_report_template(self.template_data)
                
                # プレビュー生成
                pdf_path = generate_sample_report_with_dummy_data()
                Clock.schedule_once(lambda dt: self.on_preview_complete(pdf_path))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.on_preview_error(str(e)))
        
        threading.Thread(target=generate_in_thread, daemon=True).start()
        
    def collect_settings(self):
        """UI設定を収集"""
        # 基本設定
        self.template_data["report_title"] = self.title_input.text
        
        # 余白設定
        if "formatting" not in self.template_data:
            self.template_data["formatting"] = {}
        if "page_margins" not in self.template_data["formatting"]:
            self.template_data["formatting"]["page_margins"] = {}
            
        for margin_type, slider in self.margin_sliders.items():
            self.template_data["formatting"]["page_margins"][margin_type] = slider.value
            
        # フォント設定
        if "fonts" not in self.template_data["formatting"]:
            self.template_data["formatting"]["fonts"] = {}
            
        for font_type, slider in self.font_sliders.items():
            self.template_data["formatting"]["fonts"][font_type] = int(slider.value)
            
        # セクション設定
        for section_key, widgets in self.section_widgets.items():
            if section_key in self.template_data["sections"]:
                self.template_data["sections"][section_key]["enabled"] = widgets["enabled"].active
                self.template_data["sections"][section_key]["title"] = widgets["title"].text
                
        # 位置設定
        if hasattr(self, 'section_order_widgets'):
            for section_key, slider in self.section_order_widgets.items():
                if section_key in self.template_data["sections"]:
                    self.template_data["sections"][section_key]["position"] = int(slider.value)
                
    def save_settings(self, instance):
        """設定を保存"""
        try:
            self.collect_settings()
            if save_report_template(self.template_data):
                self.show_popup("成功", "設定が保存されました")
            else:
                self.show_popup("エラー", "設定の保存に失敗しました")
        except Exception as e:
            self.show_popup("エラー", f"保存エラー: {e}")
            
    def reset_to_default(self, instance):
        """デフォルト設定に戻す"""
        from .report_system.template_loader import get_default_template
        self.template_data = get_default_template()
        self.show_popup("完了", "デフォルト設定に戻しました")
        
    def on_preview_complete(self, pdf_path):
        """プレビュー完了"""
        self.progress_label.text = ""
        self.show_popup("完了", f"プレビューが生成されました: {pdf_path}")
        
    def on_preview_error(self, error_msg):
        """プレビューエラー"""
        self.progress_label.text = ""
        self.show_popup("エラー", f"プレビュー生成エラー: {error_msg}")
        
    def show_popup(self, title, message):
        """ポップアップを表示"""
        popup = Popup(
            title=title,
            content=Label(text=message, font_name=self.get_font_name()),
            size_hint=(0.8, 0.4)
        )
        popup.open()
        
    def go_back(self, instance):
        """前の画面に戻る"""
        self.manager.current = "report"
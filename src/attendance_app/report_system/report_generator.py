import os
import io
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .data_analyzer import get_monthly_attendance_data, get_students_with_attendance
from .template_manager import render_bar_chart, render_colored_bar_chart, format_date_japanese
from .template_loader import load_report_template
import calendar
from ..config import load_settings
from PIL import Image as PILImage


def get_output_directory() -> Path:
    """レポート出力ディレクトリを取得"""
    return Path(__file__).parent.parent / "output" / "reports"


def get_sleep_image(sleep_percentage: str) -> Optional[str]:
    """睡眠パーセンテージに対応する画像パスを取得"""
    assets_dir = Path(__file__).parent.parent / "assets" / "images" / "sleep"
    
    image_map = {
        "０％": "beaker1.png",
        "２５％": "beaker2.png", 
        "５０％": "beaker3.png",
        "７５％": "beaker4.png",
        "１００％": "beaker5.png"
    }
    
    if sleep_percentage in image_map:
        image_path = assets_dir / image_map[sleep_percentage]
        if image_path.exists():
            return str(image_path)
    
    return None


def get_mood_image(mood: str) -> Optional[str]:
    """気分に対応する画像パスを取得"""
    assets_dir = Path(__file__).parent.parent / "assets" / "images" / "weather"
    
    image_map = {
        "快晴": "sun.png",
        "晴れ": "sun_cloud.png",
        "くもり": "cloud.png"
    }
    
    if mood in image_map:
        image_path = assets_dir / image_map[mood]
        if image_path.exists():
            return str(image_path)
    
    return None


def get_purpose_image(purpose: str) -> Optional[str]:
    """目的に対応する画像パスを取得"""
    assets_dir = Path(__file__).parent.parent / "assets" / "images" / "purpose"
    
    image_map = {
        "学ぶ": "purpose1.png",
        "来る": "purpose2.png"
    }
    
    if purpose in image_map:
        image_path = assets_dir / image_map[purpose]
        if image_path.exists():
            return str(image_path)
    
    return None


def ensure_output_directory() -> None:
    """出力ディレクトリが存在することを確認"""
    output_dir = get_output_directory()
    output_dir.mkdir(parents=True, exist_ok=True)


def setup_fonts() -> None:
    """フォントの設定を行う"""
    try:
        # UDDigiKyokashoN-R フォントのパスを設定
        font_path = Path(__file__).parent.parent / "assets" / "fonts" / "UDDigiKyokashoN-R.ttc"
        if font_path.exists():
            pdfmetrics.registerFont(TTFont('UDDigiKyokashoN-R', str(font_path)))
            print(f"フォントを登録しました: {font_path}")
        else:
            print(f"フォントファイルが見つかりません: {font_path}")
            print("デフォルトフォントを使用します")
    except Exception as e:
        print(f"フォント設定エラー: {e}")
        print("デフォルトフォントを使用します")


def create_calendar_view(daily_records: List[dict], year: int, month: int) -> Table:
    """出席記録のカレンダー表示を作成"""
    # 月の日数を取得
    _, days_in_month = calendar.monthrange(year, month)
    
    # 出席日を辞書で管理
    attendance_days = {}
    for record in daily_records:
        try:
            date_obj = datetime.strptime(record['date'], '%Y-%m-%d')
            day = date_obj.day
            attendance_days[day] = "●"
        except (ValueError, KeyError):
            # 無効な日付データはスキップ
            continue
    
    # カレンダーテーブルのデータを作成
    calendar_data = []
    
    # 週単位でカレンダーを作成
    weeks = []
    current_week = []
    
    for day in range(1, days_in_month + 1):
        day_str = str(day)
        if day in attendance_days:
            day_str = f"{day} ●"
        current_week.append(day_str)
        
        # 7日ごとに新しい週を開始
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
    
    # 最後の週を追加
    if current_week:
        # 残りの日を空文字で埋める
        while len(current_week) < 7:
            current_week.append("")
        weeks.append(current_week)
    
    # 週の行数を制限（最大5週）
    if len(weeks) > 5:
        weeks = weeks[:5]
    
    # テーブルを作成
    calendar_table = Table(weeks, colWidths=[0.7*cm] * 7)
    
    # フォント設定を取得
    registered_fonts = pdfmetrics.getRegisteredFontNames()
    font_name = 'UDDigiKyokashoN-R' if 'UDDigiKyokashoN-R' in registered_fonts else 'Helvetica'
    
    calendar_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#333333')),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f9f9f9')),
    ]))
    
    return calendar_table


def get_styles() -> dict:
    """PDF用のスタイルを取得"""
    styles = getSampleStyleSheet()
    template = load_report_template()
    
    # 登録されているフォント名をチェック
    registered_fonts = pdfmetrics.getRegisteredFontNames()
    font_name = 'UDDigiKyokashoN-R' if 'UDDigiKyokashoN-R' in registered_fonts else 'Helvetica'
    bold_font_name = 'UDDigiKyokashoN-R' if 'UDDigiKyokashoN-R' in registered_fonts else 'Helvetica-Bold'
    
    # テンプレートから設定を取得
    fonts = template.get('formatting', {}).get('fonts', {})
    colors = template.get('colors', {})
    
    # カスタムスタイルを定義
    custom_styles = {
        'title': ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=fonts.get('title_size', 18),
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=HexColor(colors.get('title_color', '#2c3e50')),
            fontName=bold_font_name
        ),
        'heading': ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=fonts.get('heading_size', 13),
            spaceAfter=8,
            textColor=HexColor(colors.get('heading_color', '#2c3e50')),
            fontName=bold_font_name
        ),
        'normal': ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=fonts.get('normal_size', 10),
            spaceAfter=4,
            fontName=font_name
        ),
        'stats': ParagraphStyle(
            'CustomStats',
            parent=styles['Normal'],
            fontSize=fonts.get('stats_size', 11),
            spaceAfter=6,
            textColor=HexColor(colors.get('stats_color', '#34495e')),
            fontName=bold_font_name
        )
    }
    
    return custom_styles


def save_image_from_data_url(data_url: str, temp_dir: Path) -> Optional[str]:
    """Data URLから画像を一時ファイルに保存"""
    try:
        if ',' in data_url:
            header, data = data_url.split(',', 1)
            image_data = base64.b64decode(data)
            
            # 画像形式を判定
            if 'png' in header.lower():
                ext = '.png'
            elif 'jpeg' in header.lower() or 'jpg' in header.lower():
                ext = '.jpg'
            else:
                ext = '.png'
            
            # 一時ファイルに保存
            temp_file = temp_dir / f"temp_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            with open(temp_file, 'wb') as f:
                f.write(image_data)
            
            return str(temp_file)
        return None
    except Exception as e:
        print(f"画像保存エラー: {e}")
        return None

def create_pdf_content(data: dict) -> List:
    """PDFコンテンツを作成"""
    content = []
    styles = get_styles()
    template = load_report_template()
    
    # 画像データを処理
    images_data = template.get('images', {})
    uploaded_images = images_data.get('uploaded', [])
    image_settings = images_data.get('settings', {})
    
    # 一時ディレクトリを作成
    temp_dir = Path(__file__).parent.parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    # 背景画像の処理（透かしとして処理）
    background_image_path = None
    if uploaded_images:
        position = image_settings.get('position', 'background')
        if position in ['background', 'custom', 'watermark']:
            background_image_path = save_image_from_data_url(uploaded_images[0]['data'], temp_dir)
    
    # ヘッダー画像を追加
    if uploaded_images and image_settings.get('position') == 'header':
        image_path = save_image_from_data_url(uploaded_images[0]['data'], temp_dir)
        if image_path:
            try:
                img_width = image_settings.get('width', 50) / 100 * 15*cm  # A4幅の割合
                img = Image(image_path, width=img_width, height=None)
                content.append(img)
                content.append(Spacer(1, 0.3*cm))
            except Exception as e:
                print(f"ヘッダー画像挿入エラー: {e}")
    
    # タイトル
    title = Paragraph(template.get('report_title', 'Onedrop 月次レポート'), styles['title'])
    content.append(title)
    
    # 基本情報
    info_text = f"生徒名: {data['student_name']} | 対象期間: {data['year']}年{data['month']}月"
    info = Paragraph(info_text, styles['normal'])
    content.append(info)
    content.append(Spacer(1, 0.3*cm))
    
    # 区切り線
    content.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=HexColor('#333333')))
    content.append(Spacer(1, 0.3*cm))
    
    # セクションを位置順にソート
    sections = template.get('sections', {})
    enabled_sections = [(k, v) for k, v in sections.items() if v.get('enabled', True)]
    sorted_sections = sorted(enabled_sections, key=lambda x: x[1].get('position', 0))
    
    max_attendance = max(data['attendance_count'], 1)
    
    # セクションを位置順に処理
    for section_key, section_data in sorted_sections:
        if section_key == 'attendance_status':
            attendance_title = section_data.get('title', '■ 出席状況')
            content.append(Paragraph(attendance_title, styles['heading']))
            stats_text = f"出席日数: {data['attendance_count']}日　　平均滞在時間: {data['average_stay_minutes']}分"
            content.append(Paragraph(stats_text, styles['stats']))
            content.append(Spacer(1, 0.3*cm))
            
        elif section_key == 'attendance_details':
            details_title = section_data.get('title', '■ 出席詳細')
            content.append(Paragraph(details_title, styles['heading']))
            if data['daily_records']:
                # カレンダー風の表示を作成
                calendar_view = create_calendar_view(data['daily_records'], data['year'], data['month'])
                content.append(calendar_view)
                content.append(Spacer(1, 0.2*cm))
                
                # 詳細リスト
                for record in data['daily_records']:
                    date_formatted = format_date_japanese(record['date'])
                    record_text = f"{date_formatted} {record['entry_time']}-{record['exit_time']} ({record['stay_minutes']}分)"
                    content.append(Paragraph(record_text, styles['normal']))
            else:
                content.append(Paragraph("この月の出席記録はありません", styles['normal']))
            content.append(Spacer(1, 0.3*cm))
            
        elif section_key == 'mood_analysis':
            mood_title = section_data.get('title', '■ 気分の様子')
            content.append(Paragraph(mood_title, styles['heading']))
            for mood, count in data['mood_distribution'].items():
                bar = render_colored_bar_chart(count, max_attendance, category="mood")
                
                # 画像を含むテーブルを作成
                mood_image = get_mood_image(mood)
                if mood_image:
                    try:
                        # 画像とテキストを水平に配置
                        table_data = [
                            [Image(mood_image, width=0.4*cm, height=0.4*cm), f"{bar} {mood} ({count}回)"]
                        ]
                        table = Table(table_data, colWidths=[0.6*cm, None])
                        table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 0),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#000000')),
                            ('FONTNAME', (0, 0), (-1, -1), styles['normal'].fontName),
                        ]))
                        content.append(table)
                    except Exception as e:
                        print(f"画像読み込みエラー: {e}")
                        mood_text = f"{bar} {mood} ({count}回)"
                        content.append(Paragraph(mood_text, styles['normal']))
                else:
                    mood_text = f"{bar} {mood} ({count}回)"
                    content.append(Paragraph(mood_text, styles['normal']))
            content.append(Spacer(1, 0.3*cm))
            
        elif section_key == 'sleep_analysis':
            sleep_title = section_data.get('title', '■ 睡眠の状況')
            content.append(Paragraph(sleep_title, styles['heading']))
            for sleep_range, count in data['sleep_stats']['distribution'].items():
                bar = render_colored_bar_chart(count, max_attendance, category="sleep")
                
                # 画像を含むテーブルを作成
                sleep_image = get_sleep_image(sleep_range)
                if sleep_image:
                    try:
                        # 画像とテキストを水平に配置
                        table_data = [
                            [Image(sleep_image, width=0.4*cm, height=0.4*cm), f"{bar} {sleep_range} ({count}回)"]
                        ]
                        table = Table(table_data, colWidths=[0.6*cm, None])
                        table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 0),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#000000')),
                            ('FONTNAME', (0, 0), (-1, -1), styles['normal'].fontName),
                        ]))
                        content.append(table)
                    except Exception as e:
                        print(f"画像読み込みエラー: {e}")
                        sleep_text = f"{bar} {sleep_range} ({count}回)"
                        content.append(Paragraph(sleep_text, styles['normal']))
                else:
                    sleep_text = f"{bar} {sleep_range} ({count}回)"
                    content.append(Paragraph(sleep_text, styles['normal']))
            content.append(Spacer(1, 0.3*cm))
            
        elif section_key == 'purpose_analysis':
            purpose_title = section_data.get('title', '■ 来塾の目的')
            content.append(Paragraph(purpose_title, styles['heading']))
            for purpose, count in data['purpose_distribution'].items():
                bar = render_colored_bar_chart(count, max_attendance, category="purpose")
                
                # 画像を含むテーブルを作成
                purpose_image = get_purpose_image(purpose)
                if purpose_image:
                    try:
                        # 画像とテキストを水平に配置
                        table_data = [
                            [Image(purpose_image, width=0.4*cm, height=0.4*cm), f"{bar} {purpose} ({count}回)"]
                        ]
                        table = Table(table_data, colWidths=[0.6*cm, None])
                        table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 0),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                            ('TOPPADDING', (0, 0), (-1, -1), 2),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                            ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#000000')),
                            ('FONTNAME', (0, 0), (-1, -1), styles['normal'].fontName),
                        ]))
                        content.append(table)
                    except Exception as e:
                        print(f"画像読み込みエラー: {e}")
                        purpose_text = f"{bar} {purpose} ({count}回)"
                        content.append(Paragraph(purpose_text, styles['normal']))
                else:
                    purpose_text = f"{bar} {purpose} ({count}回)"
                    content.append(Paragraph(purpose_text, styles['normal']))
            content.append(Spacer(1, 0.3*cm))
            
        elif section_key == 'monthly_summary':
            monthly_title = section_data.get('title', '■ 月次サマリー')
            content.append(Paragraph(monthly_title, styles['heading']))
            
            # 出席率計算
            total_days = 30  # 月の日数（仮）
            attendance_rate = (data['attendance_count'] / total_days) * 100
            
            summary_text = f"出席率: {attendance_rate:.1f}% ({data['attendance_count']}/{total_days}日)"
            content.append(Paragraph(summary_text, styles['stats']))
            
            avg_text = f"平均滞在時間: {data['average_stay_minutes']}分"
            content.append(Paragraph(avg_text, styles['stats']))
            
            # 前月比較（ダミーデータ）
            comparison_text = "前月比: 出席率 +5%, 滞在時間 -3分"
            content.append(Paragraph(comparison_text, styles['normal']))
            content.append(Spacer(1, 0.3*cm))
            
        elif section_key == 'goals_achievements':
            goals_title = section_data.get('title', '■ 目標と達成度')
            content.append(Paragraph(goals_title, styles['heading']))
            
            # 目標設定（サンプル）
            goals = [
                ("週3回以上の出席", "達成" if data['attendance_count'] >= 12 else "未達成"),
                ("1日30分以上の滞在", "達成" if data['average_stay_minutes'] >= 30 else "未達成"),
                ("継続的な参加", "達成" if len(data['daily_records']) >= 5 else "未達成")
            ]
            
            for goal, status in goals:
                status_symbol = "✓" if status == "達成" else "✗"
                goal_text = f"• {goal} → {status} {status_symbol}"
                content.append(Paragraph(goal_text, styles['normal']))
            content.append(Spacer(1, 0.3*cm))
            
        elif section_key == 'feedback_comments':
            feedback_title = section_data.get('title', '■ フィードバック・コメント')
            content.append(Paragraph(feedback_title, styles['heading']))
            
            # サンプルコメント
            comments = [
                "積極的な学習姿勢が見られます。",
                "質問が活発で、理解度が向上しています。",
                "継続的な努力が成果に結びついています。"
            ]
            
            for comment in comments:
                content.append(Paragraph(f"• {comment}", styles['normal']))
            content.append(Spacer(1, 0.3*cm))
            
        elif section_key == 'improvement_suggestions':
            improvement_title = section_data.get('title', '■ 改善提案')
            content.append(Paragraph(improvement_title, styles['heading']))
            
            # 改善提案
            suggestions = [
                "朝の時間帯（9-11時）の利用を推奨します",
                "集中時間を30分から45分に延長することを検討",
                "週1回のレビューセッションの実施"
            ]
            
            for suggestion in suggestions:
                content.append(Paragraph(f"• {suggestion}", styles['normal']))
            content.append(Spacer(1, 0.3*cm))
            
        elif section_key == 'next_month_plan':
            plan_title = section_data.get('title', '■ 来月の計画')
            content.append(Paragraph(plan_title, styles['heading']))
            
            # 来月の計画
            plans = [
                "週4回の出席を目標とします",
                "新しい学習テーマに挑戦します",
                "グループ学習にも参加予定です"
            ]
            
            for plan in plans:
                content.append(Paragraph(f"• {plan}", styles['normal']))
            content.append(Spacer(1, 0.3*cm))
    
    # フッター画像を追加
    if uploaded_images and image_settings.get('position') == 'footer':
        image_path = save_image_from_data_url(uploaded_images[0]['data'], temp_dir)
        if image_path:
            try:
                content.append(Spacer(1, 0.5*cm))
                img_width = image_settings.get('width', 50) / 100 * 15*cm  # A4幅の割合
                img = Image(image_path, width=img_width, height=None)
                content.append(img)
            except Exception as e:
                print(f"フッター画像挿入エラー: {e}")
    
    return content


def generate_monthly_report(student_id: str, year: int, month: int) -> str:
    """
    月次レポートPDFを生成
    
    Args:
        student_id: 塾生番号
        year: 対象年
        month: 対象月
        
    Returns:
        str: 生成されたPDFファイルのパス
    """
    try:
        # フォント設定
        setup_fonts()
        
        # 出席データを取得
        attendance_data = get_monthly_attendance_data(student_id, year, month)
        
        # 年月の情報を追加
        attendance_data["year"] = year
        attendance_data["month"] = month
        
        # 出力ディレクトリを確保
        ensure_output_directory()
        
        # PDFファイル名を生成
        student_name = attendance_data["student_name"]
        safe_student_name = "".join(c for c in student_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{year:04d}-{month:02d}_{student_id}_{safe_student_name}_{timestamp}.pdf"
        output_path = get_output_directory() / filename
        
        # PDFドキュメントを作成
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=1.2*cm,
            leftMargin=1.2*cm,
            topMargin=1.2*cm,
            bottomMargin=1.2*cm
        )
        
        # PDFコンテンツを作成
        content = create_pdf_content(attendance_data)
        
        # PDFを生成
        doc.build(content)
        
        # ファイル作成の確認
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"レポートが生成されました: {output_path} (サイズ: {file_size} bytes)")
        else:
            print(f"警告: レポートファイルが作成されませんでした: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        print(f"レポート生成中にエラーが発生しました: {e}")
        raise


def generate_all_reports(year: int, month: int) -> List[str]:
    """
    全生徒の月次レポートを一括生成
    
    Args:
        year: 対象年
        month: 対象月
        
    Returns:
        List[str]: 生成されたPDFファイルのパスのリスト
    """
    try:
        # 対象月に出席記録がある生徒を取得
        students = get_students_with_attendance(year, month)
        
        if not students:
            print(f"{year}年{month}月に出席記録がある生徒はいません")
            return []
        
        generated_files = []
        
        for student in students:
            try:
                print(f"生徒 {student['name']} ({student['id']}) のレポートを生成中...")
                pdf_path = generate_monthly_report(student["id"], year, month)
                generated_files.append(pdf_path)
                print(f"[OK] 完了: {student['name']} -> {pdf_path}")
            except Exception as e:
                print(f"[ERROR] エラー: {student['name']} - {e}")
                continue
        
        print(f"\n一括生成完了: {len(generated_files)}件のレポートが生成されました")
        return generated_files
        
    except Exception as e:
        print(f"一括生成中にエラーが発生しました: {e}")
        raise


def test_report_generation() -> None:
    """テスト用のレポート生成"""
    try:
        # テストデータで生成
        test_student_id = "2025070019"
        test_year = 2025
        test_month = 7
        
        print("テストレポートを生成中...")
        pdf_path = generate_monthly_report(test_student_id, test_year, test_month)
        print(f"テストレポートが生成されました: {pdf_path}")
        
    except Exception as e:
        print(f"テスト生成中にエラーが発生しました: {e}")
        raise


def generate_sample_report_with_dummy_data() -> str:
    """ダミーデータを使用してサンプルレポートを生成"""
    try:
        # フォント設定
        setup_fonts()
        
        # ダミーデータを作成
        dummy_data = {
            "student_name": "東城立憲",
            "year": 2025,
            "month": 7,
            "attendance_count": 7,
            "average_stay_minutes": 29.0,
            "daily_records": [
                {
                    "date": "2025-07-15",
                    "entry_time": "10:56",
                    "exit_time": "11:00",
                    "stay_minutes": 4,
                    "mood": "快晴",
                    "sleep_satisfaction": "75%",
                    "purpose": "学ぶ"
                },
                {
                    "date": "2025-07-15",
                    "entry_time": "11:05",
                    "exit_time": "11:06",
                    "stay_minutes": 1,
                    "mood": "晴れ",
                    "sleep_satisfaction": "50%",
                    "purpose": "来る"
                },
                {
                    "date": "2025-07-16",
                    "entry_time": "10:45",
                    "exit_time": "10:46",
                    "stay_minutes": 1,
                    "mood": "快晴",
                    "sleep_satisfaction": "100%",
                    "purpose": "学ぶ"
                }
            ],
            "mood_distribution": {
                "快晴": 4,
                "晴れ": 3,
                "くもり": 0
            },
            "sleep_stats": {
                "average_percentage": 64.0,
                "distribution": {
                    "０％": 1,
                    "２５％": 1,
                    "５０％": 2,
                    "７５％": 2,
                    "１００％": 1
                }
            },
            "purpose_distribution": {
                "学ぶ": 5,
                "来る": 2
            }
        }
        
        # 出力ディレクトリを確保
        ensure_output_directory()
        
        # PDFファイル名を生成
        filename = f"sample_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = get_output_directory() / filename
        
        # PDFドキュメントを作成
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=1.2*cm,
            leftMargin=1.2*cm,
            topMargin=1.2*cm,
            bottomMargin=1.2*cm
        )
        
        # PDFコンテンツを作成
        content = create_pdf_content(dummy_data)
        
        # PDFを生成
        doc.build(content)
        
        print(f"サンプルレポートが生成されました: {output_path}")
        return str(output_path)
        
    except Exception as e:
        print(f"サンプルレポート生成中にエラーが発生しました: {e}")
        raise


def get_report_config() -> dict:
    """レポート生成設定を取得"""
    return {
        'juku_name': 'Onedrop',
        'output_directory': 'output/reports',
        'template_directory': 'templates',
        'font_family': 'UDDigiKyokashoN-R',
        'page_size': 'A4',
        'margins': {'top': 20, 'bottom': 20, 'left': 15, 'right': 15},
        'bar_chart_width': 5,
        'date_format': '%m/%d (%a)',
        'time_format': '%H:%M'
    }


if __name__ == "__main__":
    # テスト実行
    print("レポート生成システムのテストを開始します...")
    
    # サンプルレポートの生成
    try:
        sample_path = generate_sample_report_with_dummy_data()
        print(f"サンプルレポートの生成が完了しました: {sample_path}")
    except Exception as e:
        print(f"サンプルレポート生成エラー: {e}")
    
    # 実データでのテスト（スプレッドシートが設定されている場合）
    try:
        test_report_generation()
    except Exception as e:
        print(f"実データテストエラー: {e}")
        print("スプレッドシートの設定を確認してください")
"""レポートプレビュー生成機能"""

import io
import tempfile
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import json

def generate_report_preview(template_data: Dict[str, Any], width: int = 400, height: int = 600) -> str:
    """レポートテンプレートのプレビュー画像を生成"""
    try:
        # PILで画像を作成
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # 画像データをチェック
        images_data = template_data.get('images', {})
        uploaded_images = images_data.get('uploaded', [])
        image_settings = images_data.get('settings', {})
        
        print(f"Preview generation: Found {len(uploaded_images)} images")
        print(f"Image settings: {image_settings}")
        
        # フォント設定（テンプレートから動的に取得）
        fonts = template_data.get('formatting', {}).get('fonts', {})
        title_size = fonts.get('title_size', 18)
        heading_size = fonts.get('heading_size', 13)
        normal_size = fonts.get('normal_size', 10)
        
        try:
            # 日本語フォント（MS Gothic）を試行
            try:
                title_font = ImageFont.truetype("msgothic.ttc", size=title_size)
                heading_font = ImageFont.truetype("msgothic.ttc", size=heading_size)
                normal_font = ImageFont.truetype("msgothic.ttc", size=normal_size)
            except:
                # システムフォントのフォールバック
                try:
                    title_font = ImageFont.truetype("arial.ttf", size=title_size)
                    heading_font = ImageFont.truetype("arial.ttf", size=heading_size)
                    normal_font = ImageFont.truetype("arial.ttf", size=normal_size)
                except:
                    # デフォルトフォントで適切なサイズ調整
                    title_font = ImageFont.load_default()
                    heading_font = ImageFont.load_default()
                    normal_font = ImageFont.load_default()
        except Exception as e:
            print(f"フォント読み込みエラー: {e}")
            return None
        
        # 背景画像を最初に描画（文字の下レイヤー）
        if uploaded_images:
            position = image_settings.get('position', 'background')
            if position == 'background':
                draw_background_image(img, uploaded_images[0], image_settings, width, height)
            elif position == 'custom':
                draw_custom_positioned_image(img, uploaded_images[0], image_settings, width, height)
            elif position == 'watermark':
                draw_watermark_image(img, uploaded_images[0], image_settings, width, height)
        
        y_offset = 20
        
        # ヘッダー画像を描画
        if uploaded_images and image_settings.get('position') == 'header':
            y_offset = draw_header_image(img, draw, uploaded_images[0], image_settings, width, y_offset)
        
        # タイトル描画
        title = template_data.get('report_title', 'レポート')
        colors = template_data.get('colors', {})
        title_color = colors.get('title_color', '#2c3e50')
        try:
            # anchor引数を使わないバージョン
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text((width//2 - title_width//2, y_offset), title, font=title_font, fill=title_color)
        except:
            # さらにシンプルなバージョン
            draw.text((width//2 - 60, y_offset), title, font=title_font, fill=title_color)
        y_offset += 40
        
        # 基本情報エリア
        draw.text((20, y_offset), "生徒名: サンプル太郎 | 対象期間: 2025年7月", font=normal_font, fill='black')
        y_offset += 30
        
        # 区切り線
        draw.line([(20, y_offset), (width-20, y_offset)], fill='black', width=1)
        y_offset += 20
        
        # セクション描画
        sections = template_data.get('sections', {})
        enabled_sections = sorted(
            [(k, v) for k, v in sections.items() if v.get('enabled', True)],
            key=lambda x: x[1].get('position', 0)
        )
        
        for section_key, section_data in enabled_sections:
            if y_offset > height - 80:  # 画面下部に近づいたら停止
                break
                
            # セクションタイトル
            section_title = section_data.get('title', section_key)
            # 色設定を取得
            colors = template_data.get('colors', {})
            heading_color = colors.get('heading_color', '#2c3e50')
            draw.text((20, y_offset), section_title, font=heading_font, fill=heading_color)
            y_offset += 25
            
            # セクション内容のプレビュー
            if section_key == 'attendance_status':
                stats_color = colors.get('stats_color', '#34495e')
                draw.text((40, y_offset), "出席日数: 7日　　平均滞在時間: 29分", font=normal_font, fill=stats_color)
                y_offset += 20
                if section_data.get('show_calendar', True):
                    # カレンダー風の表示
                    calendar_y = y_offset
                    for week in range(2):  # 2週間分を表示
                        for day in range(7):
                            x = 40 + day * 25
                            y = calendar_y + week * 20
                            if week == 0 and day < 3:  # 最初の3日は出席マーク
                                draw.text((x, y), "●", font=normal_font, fill='blue')
                            else:
                                draw.text((x, y), str(day + 1), font=normal_font, fill='gray')
                    y_offset += 50
                    
            elif section_key == 'mood_analysis':
                draw.text((40, y_offset), "■■■■□ 快晴 (4回)", font=normal_font, fill='black')
                y_offset += 15
                draw.text((40, y_offset), "■■■□□ 晴れ (3回)", font=normal_font, fill='black')
                y_offset += 15
                draw.text((40, y_offset), "□□□□□ くもり (0回)", font=normal_font, fill='black')
                y_offset += 20
                
            elif section_key == 'sleep_analysis':
                draw.text((40, y_offset), "■■□□□ 75% (2回)", font=normal_font, fill='black')
                y_offset += 15
                draw.text((40, y_offset), "■■□□□ 50% (2回)", font=normal_font, fill='black')
                y_offset += 15
                draw.text((40, y_offset), "■□□□□ 25% (1回)", font=normal_font, fill='black')
                y_offset += 20
                
            elif section_key == 'purpose_analysis':
                draw.text((40, y_offset), "■■■■■ 学ぶ (5回)", font=normal_font, fill='black')
                y_offset += 15
                draw.text((40, y_offset), "■■□□□ 来る (2回)", font=normal_font, fill='black')
                y_offset += 20
                
            elif section_key == 'attendance_details':
                draw.text((40, y_offset), "07/15 10:56-11:00 (4分)", font=normal_font, fill='black')
                y_offset += 15
                draw.text((40, y_offset), "07/15 11:05-11:06 (1分)", font=normal_font, fill='black')
                y_offset += 15
                draw.text((40, y_offset), "07/16 10:45-10:46 (1分)", font=normal_font, fill='black')
                y_offset += 20
                
            elif section_key == 'monthly_summary':
                draw.text((40, y_offset), "[統計] 出席率: 87.5% (前月比+5%)", font=normal_font, fill='black')
                y_offset += 15
                draw.text((40, y_offset), "[傾向] 平均滞在時間: 29分 (前月比-3分)", font=normal_font, fill='black')
                y_offset += 15
                draw.text((40, y_offset), "[評価] 目標達成度: 良好", font=normal_font, fill='black')
                y_offset += 20
                
            elif section_key == 'goals_achievements':
                draw.text((40, y_offset), "[目標] 今月の目標:", font=normal_font, fill='black')
                y_offset += 15
                draw.text((50, y_offset), "• 週3回以上の出席 → 達成 ✓", font=normal_font, fill='green')
                y_offset += 15
                draw.text((50, y_offset), "• 1日30分以上の滞在 → 未達成 ✗", font=normal_font, fill='red')
                y_offset += 20
                
            elif section_key == 'feedback_comments':
                draw.text((40, y_offset), "[講師] コメント:", font=normal_font, fill='black')
                y_offset += 15
                draw.text((50, y_offset), "「積極的な姿勢が見られます」", font=normal_font, fill='blue')
                y_offset += 15
                draw.text((50, y_offset), "「次回は質問をもっと活発に」", font=normal_font, fill='blue')
                y_offset += 20
                
            elif section_key == 'improvement_suggestions':
                draw.text((40, y_offset), "[提案] 改善案:", font=normal_font, fill='black')
                y_offset += 15
                draw.text((50, y_offset), "• 朝の時間帯の利用を推奨", font=normal_font, fill='purple')
                y_offset += 15
                draw.text((50, y_offset), "• 集中時間を30分→45分に延長", font=normal_font, fill='purple')
                y_offset += 20
                
            elif section_key == 'next_month_plan':
                draw.text((40, y_offset), "[計画] 来月の予定:", font=normal_font, fill='black')
                y_offset += 15
                draw.text((50, y_offset), "• 週4回出席を目標", font=normal_font, fill='orange')
                y_offset += 15
                draw.text((50, y_offset), "• 新しい学習テーマに挑戦", font=normal_font, fill='orange')
                y_offset += 20
            
            y_offset += 15  # セクション間のスペース
        
        # フッター画像を描画
        if uploaded_images and image_settings.get('position') == 'footer':
            draw_footer_image(img, draw, uploaded_images[0], image_settings, width, height)
        
        # 透かし画像を描画
        if uploaded_images and image_settings.get('position') == 'watermark':
            draw_watermark_image(img, uploaded_images[0], image_settings, width, height)
        
        # 一時ファイルに保存
        temp_dir = Path(tempfile.gettempdir()) / "attendance_preview"
        temp_dir.mkdir(exist_ok=True)
        
        preview_path = temp_dir / "preview.png"
        img.save(preview_path, "PNG")
        
        return str(preview_path)
        
    except Exception as e:
        print(f"プレビュー生成エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_layout_preview(template_data: Dict[str, Any], width: int = 300, height: int = 400) -> str:
    """レイアウトプレビュー（A4用紙風）を生成"""
    try:
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # A4用紙の境界線
        draw.rectangle([(10, 10), (width-10, height-10)], outline='black', width=2)
        
        # フォント設定（テンプレートから動的に取得）
        fonts = template_data.get('formatting', {}).get('fonts', {})
        font_size = max(8, min(fonts.get('normal_size', 10), 12))  # 8-12の範囲で調整
        
        try:
            # 日本語フォント（MS Gothic）を試行
            try:
                font = ImageFont.truetype("msgothic.ttc", size=font_size)
            except:
                # システムフォントのフォールバック
                try:
                    font = ImageFont.truetype("arial.ttf", size=font_size)
                except:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # タイトルエリア
        draw.rectangle([(20, 20), (width-20, 50)], outline='blue', width=1)
        draw.text((25, 25), "タイトル", font=font, fill='blue')
        
        y_current = 60
        section_height = 40
        
        # セクション描画
        sections = template_data.get('sections', {})
        enabled_sections = sorted(
            [(k, v) for k, v in sections.items() if v.get('enabled', True)],
            key=lambda x: x[1].get('position', 0)
        )
        
        for i, (section_key, section_data) in enumerate(enabled_sections):
            if y_current + section_height > height - 20:
                break
                
            # セクションボックス
            draw.rectangle([(20, y_current), (width-20, y_current + section_height)], 
                          outline='gray', width=1)
            
            # セクション名
            section_title = section_data.get('title', section_key)[:10]  # 短縮表示
            draw.text((25, y_current + 5), section_title, font=font, fill='black')
            
            # 位置番号
            draw.text((width-40, y_current + 5), f"#{i+1}", font=font, fill='red')
            
            y_current += section_height + 5
        
        # 一時ファイルに保存
        temp_dir = Path(tempfile.gettempdir()) / "attendance_preview"
        temp_dir.mkdir(exist_ok=True)
        
        layout_path = temp_dir / "layout.png"
        img.save(layout_path, "PNG")
        
        return str(layout_path)
        
    except Exception as e:
        print(f"レイアウトプレビュー生成エラー: {e}")
        return None

def load_image_from_data_url(data_url: str) -> Optional[Image.Image]:
    """Data URLから画像を読み込む"""
    try:
        # data:image/png;base64, の部分を除去
        if ',' in data_url:
            header, data = data_url.split(',', 1)
            image_data = base64.b64decode(data)
            return Image.open(io.BytesIO(image_data))
        return None
    except Exception as e:
        print(f"画像読み込みエラー: {e}")
        return None

def draw_header_image(base_img: Image.Image, draw: ImageDraw.Draw, image_data: Dict[str, Any], 
                     settings: Dict[str, Any], canvas_width: int, y_offset: int) -> int:
    """ヘッダー画像を描画"""
    try:
        # Base64データから画像を読み込み
        uploaded_img = load_image_from_data_url(image_data['data'])
        if not uploaded_img:
            return y_offset
        
        # 画像サイズを計算
        target_width = int(canvas_width * settings.get('width', 50) / 100)
        aspect_ratio = uploaded_img.height / uploaded_img.width
        target_height = int(target_width * aspect_ratio)
        
        # リサイズ
        resized_img = uploaded_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 透明度を適用
        opacity = settings.get('opacity', 100) / 100
        if opacity < 1.0:
            alpha = int(255 * opacity)
            if resized_img.mode != 'RGBA':
                resized_img = resized_img.convert('RGBA')
            # 透明度を適用
            resized_img.putalpha(alpha)
        
        # 配置位置を計算
        alignment = settings.get('alignment', 'center')
        if alignment == 'left':
            x = 20
        elif alignment == 'right':
            x = canvas_width - target_width - 20
        else:  # center
            x = (canvas_width - target_width) // 2
        
        # 画像を貼り付け
        if resized_img.mode == 'RGBA':
            base_img.paste(resized_img, (x, y_offset), resized_img)
        else:
            base_img.paste(resized_img, (x, y_offset))
        
        return y_offset + target_height + 10
        
    except Exception as e:
        print(f"ヘッダー画像描画エラー: {e}")
        return y_offset

def draw_footer_image(base_img: Image.Image, draw: ImageDraw.Draw, image_data: Dict[str, Any], 
                     settings: Dict[str, Any], canvas_width: int, canvas_height: int):
    """フッター画像を描画"""
    try:
        uploaded_img = load_image_from_data_url(image_data['data'])
        if not uploaded_img:
            return
        
        # 画像サイズを計算
        target_width = int(canvas_width * settings.get('width', 50) / 100)
        aspect_ratio = uploaded_img.height / uploaded_img.width
        target_height = int(target_width * aspect_ratio)
        
        # リサイズ
        resized_img = uploaded_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 透明度を適用
        opacity = settings.get('opacity', 100) / 100
        if opacity < 1.0:
            alpha = int(255 * opacity)
            if resized_img.mode != 'RGBA':
                resized_img = resized_img.convert('RGBA')
            resized_img.putalpha(alpha)
        
        # 配置位置を計算（フッター）
        alignment = settings.get('alignment', 'center')
        if alignment == 'left':
            x = 20
        elif alignment == 'right':
            x = canvas_width - target_width - 20
        else:  # center
            x = (canvas_width - target_width) // 2
        
        y = canvas_height - target_height - 20
        
        # 画像を貼り付け
        if resized_img.mode == 'RGBA':
            base_img.paste(resized_img, (x, y), resized_img)
        else:
            base_img.paste(resized_img, (x, y))
            
    except Exception as e:
        print(f"フッター画像描画エラー: {e}")

def draw_watermark_image(base_img: Image.Image, image_data: Dict[str, Any], 
                        settings: Dict[str, Any], canvas_width: int, canvas_height: int):
    """透かし画像を描画"""
    try:
        uploaded_img = load_image_from_data_url(image_data['data'])
        if not uploaded_img:
            return
        
        # 画像サイズを計算（透かしは小さめ）
        target_width = int(canvas_width * settings.get('width', 30) / 100)
        aspect_ratio = uploaded_img.height / uploaded_img.width
        target_height = int(target_width * aspect_ratio)
        
        # リサイズ
        resized_img = uploaded_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 透明度を適用（透かしはより透明に）
        opacity = min(settings.get('opacity', 50), 50) / 100  # 最大50%
        if resized_img.mode != 'RGBA':
            resized_img = resized_img.convert('RGBA')
        alpha = int(255 * opacity)
        resized_img.putalpha(alpha)
        
        # 中央に配置
        x = (canvas_width - target_width) // 2
        y = (canvas_height - target_height) // 2
        
        # 画像を貼り付け
        base_img.paste(resized_img, (x, y), resized_img)
            
    except Exception as e:
        print(f"透かし画像描画エラー: {e}")

def draw_background_image(base_img: Image.Image, image_data: Dict[str, Any], 
                         settings: Dict[str, Any], canvas_width: int, canvas_height: int):
    """背景画像を描画（文字の下レイヤー）"""
    try:
        uploaded_img = load_image_from_data_url(image_data['data'])
        if not uploaded_img:
            return
        
        # 画像サイズを計算
        target_width = int(canvas_width * settings.get('width', 50) / 100)
        aspect_ratio = uploaded_img.height / uploaded_img.width
        target_height = int(target_width * aspect_ratio)
        
        # リサイズ
        resized_img = uploaded_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 透明度を適用（背景画像は薄くする）
        opacity = settings.get('opacity', 30) / 100  # デフォルト30%
        if resized_img.mode != 'RGBA':
            resized_img = resized_img.convert('RGBA')
        alpha = int(255 * opacity)
        resized_img.putalpha(alpha)
        
        # 配置位置を計算
        alignment = settings.get('alignment', 'center')
        if alignment == 'left':
            x = 20
        elif alignment == 'right':
            x = canvas_width - target_width - 20
        else:  # center
            x = (canvas_width - target_width) // 2
        
        # 垂直方向は中央に配置
        y = (canvas_height - target_height) // 2
        
        # 画像を貼り付け
        base_img.paste(resized_img, (x, y), resized_img)
            
    except Exception as e:
        print(f"背景画像描画エラー: {e}")

def draw_custom_positioned_image(base_img: Image.Image, image_data: Dict[str, Any], 
                                settings: Dict[str, Any], canvas_width: int, canvas_height: int):
    """カスタム位置に画像を描画"""
    try:
        uploaded_img = load_image_from_data_url(image_data['data'])
        if not uploaded_img:
            return
        
        # 画像サイズを計算
        target_width = int(canvas_width * settings.get('width', 50) / 100)
        aspect_ratio = uploaded_img.height / uploaded_img.width
        target_height = int(target_width * aspect_ratio)
        
        # リサイズ
        resized_img = uploaded_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 透明度を適用
        opacity = settings.get('opacity', 70) / 100
        if resized_img.mode != 'RGBA':
            resized_img = resized_img.convert('RGBA')
        alpha = int(255 * opacity)
        resized_img.putalpha(alpha)
        
        # カスタム位置を計算
        x_percent = settings.get('x', 10) / 100
        y_percent = settings.get('y', 10) / 100
        
        x = int((canvas_width - target_width) * x_percent)
        y = int((canvas_height - target_height) * y_percent)
        
        # 境界チェック
        x = max(0, min(x, canvas_width - target_width))
        y = max(0, min(y, canvas_height - target_height))
        
        # 画像を貼り付け
        base_img.paste(resized_img, (x, y), resized_img)
            
    except Exception as e:
        print(f"カスタム位置画像描画エラー: {e}")
import pandas as pd
import openpyxl
from pathlib import Path

# テンプレートファイルのパスを設定
template_path = Path("src/attendance_app/assets/reports_template.xlsx")

try:
    # openpyxlを使用してExcelファイルを読み込み
    workbook = openpyxl.load_workbook(template_path)
    
    # templateシートの画像情報を詳細に確認
    sheet = workbook['template']
    
    print("=== テンプレートシートの画像詳細情報 ===")
    
    # 画像が存在するか確認
    if sheet._images:
        print(f"画像数: {len(sheet._images)}")
        
        for i, img in enumerate(sheet._images):
            print(f"\n【画像 {i+1}】")
            try:
                # 基本情報
                print(f"画像形式: {type(img)}")
                print(f"画像パス: {img.path if hasattr(img, 'path') else 'N/A'}")
                
                # サイズ情報
                print(f"幅: {img.width}px")
                print(f"高さ: {img.height}px")
                
                # アンカー情報
                if hasattr(img, 'anchor'):
                    anchor = img.anchor
                    print(f"アンカータイプ: {type(anchor)}")
                    
                    # OneCellAnchorの場合
                    if hasattr(anchor, '_from'):
                        from_info = anchor._from
                        print(f"開始位置:")
                        print(f"  列: {from_info.col}")
                        print(f"  行: {from_info.row}")
                        print(f"  列オフセット: {from_info.colOff}")
                        print(f"  行オフセット: {from_info.rowOff}")
                    
                    # TwoCellAnchorの場合
                    if hasattr(anchor, 'to'):
                        to_info = anchor.to
                        print(f"終了位置:")
                        print(f"  列: {to_info.col}")
                        print(f"  行: {to_info.row}")
                        print(f"  列オフセット: {to_info.colOff}")
                        print(f"  行オフセット: {to_info.rowOff}")
                
                # 実際の表示サイズを取得
                print(f"実際の表示幅: {img.width}px")
                print(f"実際の表示高さ: {img.height}px")
                
                # 変換情報（トリミング、拡大など）
                if hasattr(img, 'pic'):
                    pic = img.pic
                    print(f"pic情報があります")
                    
                    if hasattr(pic, 'blipFill') and pic.blipFill:
                        blip_fill = pic.blipFill
                        print(f"blipFill情報があります")
                        
                        if hasattr(blip_fill, 'srcRect') and blip_fill.srcRect:
                            src_rect = blip_fill.srcRect
                            print(f"ソース矩形（トリミング）情報:")
                            print(f"  左: {getattr(src_rect, 'l', 'N/A')}")
                            print(f"  上: {getattr(src_rect, 't', 'N/A')}")
                            print(f"  右: {getattr(src_rect, 'r', 'N/A')}")
                            print(f"  下: {getattr(src_rect, 'b', 'N/A')}")
                        else:
                            print("トリミング情報なし")
                    
                    if hasattr(pic, 'spPr') and pic.spPr:
                        sp_pr = pic.spPr
                        print(f"図形プロパティ情報があります")
                        
                        if hasattr(sp_pr, 'xfrm') and sp_pr.xfrm:
                            xfrm = sp_pr.xfrm
                            print(f"変換情報があります")
                            
                            if hasattr(xfrm, 'ext') and xfrm.ext:
                                ext = xfrm.ext
                                print(f"拡張情報:")
                                print(f"  幅: {ext.cx} EMU")
                                print(f"  高さ: {ext.cy} EMU")
                                # EMUからピクセルに変換（1 EMU = 1/914400 インチ、96 DPI）
                                width_px = ext.cx * 96 / 914400
                                height_px = ext.cy * 96 / 914400
                                print(f"  幅（ピクセル）: {width_px:.1f}px")
                                print(f"  高さ（ピクセル）: {height_px:.1f}px")
                            
                            if hasattr(xfrm, 'off') and xfrm.off:
                                off = xfrm.off
                                print(f"オフセット:")
                                print(f"  X: {off.x} EMU")
                                print(f"  Y: {off.y} EMU")
                                # EMUからピクセルに変換
                                x_px = off.x * 96 / 914400
                                y_px = off.y * 96 / 914400
                                print(f"  X（ピクセル）: {x_px:.1f}px")
                                print(f"  Y（ピクセル）: {y_px:.1f}px")
                
                # 詳細なアンカー情報を取得
                if hasattr(img, 'anchor') and img.anchor:
                    anchor = img.anchor
                    print(f"\n詳細アンカー情報:")
                    print(f"  アンカータイプ: {type(anchor)}")
                    
                    # 各属性の値を詳細に確認
                    for attr in dir(anchor):
                        if not attr.startswith('_'):
                            try:
                                value = getattr(anchor, attr)
                                print(f"  {attr}: {value}")
                            except Exception as e:
                                print(f"  {attr}: 取得できません ({e})")
                
                # 画像の実際の描画情報を取得
                print(f"\n画像の実際の描画情報:")
                
                # 各属性の値を詳細に確認
                for attr in dir(img):
                    if not attr.startswith('_') and attr not in ['width', 'height', 'path', 'anchor']:
                        try:
                            value = getattr(img, attr)
                            print(f"  {attr}: {value}")
                        except Exception as e:
                            print(f"  {attr}: 取得できません ({e})")
                
            except Exception as e:
                print(f"画像 {i+1} の詳細情報取得エラー: {e}")
                import traceback
                traceback.print_exc()
    else:
        print("画像が見つかりません")
        
    workbook.close()
    
except Exception as e:
    print(f"エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
# Git 運用ルール・ワークフロー

## 📋 ブランチ戦略

### ブランチ構成
```
main (production)
├── feature/機能名     # 新機能開発
├── hotfix/修正名      # 緊急バグ修正
└── release/vX.X      # リリース準備
```

### ブランチ運用ルール

#### mainブランチ
- **目的**: 本番環境用の安定版
- **保護**: 直接pushは禁止
- **マージ**: プルリクエスト経由のみ
- **品質基準**: 全テスト通過、動作確認完了

#### feature/ブランチ
- **命名**: `feature/機能の概要` (例: `feature/excel-report-enhancement`)
- **作成元**: main ブランチから分岐
- **目的**: 新機能・機能改善の開発
- **ライフサイクル**: 機能完成後に main へマージして削除

#### hotfix/ブランチ
- **命名**: `hotfix/修正内容` (例: `hotfix/printer-connection-error`)
- **作成元**: main ブランチから分岐
- **目的**: 緊急バグ修正
- **優先度**: 最高（他の作業を中断して対応）

#### release/ブランチ（必要に応じて）
- **命名**: `release/v3.3` など
- **目的**: リリース前の最終調整・テスト
- **使用タイミング**: 大きなバージョンアップ時

## 📝 コミットメッセージ規約

### 基本フォーマット
```
[種類]: 概要（50文字以内）

詳細説明（必要に応じて）
- 変更点1
- 変更点2

関連: #issue番号（該当する場合）
```

### コミット種類
- `feat`: 新機能追加
- `fix`: バグ修正
- `update`: 既存機能の改善・更新
- `refactor`: リファクタリング
- `docs`: ドキュメント更新
- `style`: コードスタイル修正（機能に影響なし）
- `test`: テスト追加・修正
- `chore`: その他（依存関係更新、設定変更など）

### コミットメッセージ例
```bash
# 良い例
feat: Excel レポートにプルダウンリスト機能を追加

- 講師コメント欄にプルダウン選択肢を実装
- プランニング・カウンセリング・個別対応の3択
- テンプレートファイルの更新も含む

# 悪い例  
fix: bug
update: コード修正
```

## 🔄 開発ワークフロー

### 1. 新機能開発フロー
```bash
# 1. 最新のmainブランチに移動
git checkout main
git pull origin main

# 2. featureブランチを作成
git checkout -b feature/新機能名

# 3. 開発作業
# コードを編集...

# 4. 変更をコミット
git add .
git commit -m "feat: 新機能の概要"

# 5. GitHub にプッシュ
git push -u origin feature/新機能名

# 6. プルリクエスト作成（GitHub上で）

# 7. レビュー・承認後、マージ

# 8. ローカルでクリーンアップ
git checkout main
git pull origin main
git branch -d feature/新機能名
```

### 2. バグ修正フロー
```bash
# 1. 緊急度が高い場合は即座に開始
git checkout main
git pull origin main

# 2. hotfixブランチを作成
git checkout -b hotfix/バグの概要

# 3. 修正作業
# バグを修正...

# 4. テスト・動作確認
python -m src.attendance_app.main  # 動作確認

# 5. コミット
git add .
git commit -m "fix: バグの概要と修正内容"

# 6. 即座にプッシュ・マージ
git push -u origin hotfix/バグの概要
# GitHub でプルリクエスト → 即座にマージ

# 7. クリーンアップ
git checkout main
git pull origin main
git branch -d hotfix/バグの概要
```

### 3. 日常メンテナンスフロー
```bash
# 設定ファイル更新、ドキュメント更新など
git checkout main
git pull origin main

# 軽微な変更は直接mainに（ただし慎重に）
git add .
git commit -m "docs: マニュアル更新"
git push origin main

# または軽微でもブランチを使用（推奨）
git checkout -b chore/設定更新
# ... 作業 ...
git commit -m "chore: 設定ファイル更新"
git push -u origin chore/設定更新
# プルリクエスト経由でマージ
```

## 🔍 プルリクエスト（PR）ガイドライン

### PR作成前チェックリスト
- [ ] コードが正常に動作することを確認
- [ ] 関連ファイルの更新漏れがない
- [ ] コミットメッセージが規約に準拠
- [ ] 機密情報が含まれていない

### PRテンプレート
```markdown
## 概要
このPRの目的と変更内容を簡潔に説明

## 変更内容
- [ ] 新機能追加
- [ ] バグ修正  
- [ ] リファクタリング
- [ ] ドキュメント更新
- [ ] その他: ___________

## テスト
- [ ] ローカルでの動作確認完了
- [ ] 関連機能に影響がないことを確認
- [ ] エラーハンドリングの確認

## スクリーンショット（該当する場合）
変更前後の画面キャプチャなど

## 注意事項
レビュアーに特に確認してほしい点や、注意すべき事項
```

### レビューポイント
1. **機能性**: 要求通りに動作するか
2. **安全性**: セキュリティリスクはないか
3. **保守性**: コードは理解しやすいか
4. **互換性**: 既存機能に影響しないか

## 🚨 緊急時対応

### システム停止を伴う重要なバグの場合
```bash
# 1. 即座にhotfixブランチ作成
git checkout main
git checkout -b hotfix/critical-システム停止

# 2. 最小限の修正で問題解決
# 修正...

# 3. 即座にコミット・プッシュ
git add .
git commit -m "fix: 緊急修正 - システム停止問題の解決"
git push -u origin hotfix/critical-システム停止

# 4. 即座にプルリクエスト作成・マージ
# GitHub UI で作成、即座にマージ

# 5. mainブランチをデプロイ/配布
```

### ロールバックが必要な場合
```bash
# 1. 問題のあるコミットを特定
git log --oneline -10

# 2. revert実行（安全な方法）
git revert <問題のコミットハッシュ>

# 3. 即座にプッシュ
git push origin main
```

## 📊 リリース管理

### バージョニング規則
- **Major**: 大幅な機能追加・変更（v3.0 → v4.0）
- **Minor**: 新機能追加（v3.2 → v3.3）
- **Patch**: バグ修正（v3.2.0 → v3.2.1）

### リリースフロー
```bash
# 1. リリース準備
git checkout main
git pull origin main

# 2. バージョンタグ作成
git tag -a v3.3.0 -m "リリース v3.3.0: Excel機能強化"

# 3. タグをプッシュ
git push origin v3.3.0

# 4. GitHub Release作成
# GitHub UI でリリースノート作成

# 5. 配布パッケージ更新
pyinstaller attendance_app.spec --clean
# dist/ フォルダをZIP化して配布
```

## 🛠️ 開発環境での Git 設定

### 初回設定
```bash
# ユーザー情報設定（既に設定済み）
git config user.name "tatsunoritojo"
git config user.email "tatsunoritojo@users.noreply.github.com"

# エディタ設定（推奨）
git config core.editor "code --wait"  # VS Code使用の場合

# 改行コード設定（Windows）
git config core.autocrlf true

# デフォルトブランチ設定
git config init.defaultBranch main
```

### よく使用するエイリアス設定
```bash
git config alias.st status
git config alias.co checkout
git config alias.br branch
git config alias.cm commit
git config alias.ps push
git config alias.pl pull
git config alias.lg "log --oneline --graph --decorate"
```

## 📋 チーム開発での注意事項

### コラボレーション原則
1. **コミット前**: 必ず `git pull` で最新版を取得
2. **プッシュ前**: ローカルでの動作確認を実施
3. **マージ後**: 不要ブランチは即座に削除
4. **コンフリクト**: 慌てずに相談・協議して解決

### 避けるべき行為
- `git push --force` の使用（緊急時以外）
- main ブランチへの直接 commit
- 大量のファイルを一度にコミット
- 意味のないコミットメッセージ

### 推奨する習慣
- 小さな単位でのコミット
- 定期的な `git pull` 実行
- ブランチの目的を明確に
- PR作成前の自己レビュー

---

## 🎯 Claude Code 向け Git クイックリファレンス

### 現状確認コマンド
```bash
# 現在の状況
git status
git branch -v
git log --oneline -5

# リモートとの差分
git fetch
git status
```

### よくある作業
```bash
# 新機能開発開始
git checkout main && git pull && git checkout -b feature/機能名

# 作業中断・復帰
git stash                    # 作業を一時保存
git stash pop               # 作業を復元

# 間違えた場合の取り消し
git reset HEAD~1            # 最後のコミット取り消し（変更は保持）
git checkout -- ファイル名    # ファイルの変更を取り消し
```

---

**運用開始日**: 2025-08-02  
**最終更新**: 2025-08-02  
**次回見直し**: 機能追加・問題発生時
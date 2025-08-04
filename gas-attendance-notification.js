// ===== 設定（グローバル） =====
var INPUT_SHEET_NAME = "生徒出席情報";
var STUDENT_ROSTER_SHEET_NAME = "生徒名簿";
var QR_SHEET_NAME = "塾生番号＿名前＿QRコード";
var LOG_SHEET_NAME = "通知ログ";

// ===== 重複実行防止用キャッシュ =====
var processingCache = {};
var CACHE_TIMEOUT = 5000; // 5秒

// ===== 共通ユーティリティ =====
function toDate(v) {
  if (v instanceof Date) return v;
  if (!v) return null;
  var s = String(v).trim();
  if (/^\d{4}-\d{2}-\d{2}T/.test(s)) {
    var d = new Date(s);
    return isNaN(d) ? null : d;
  }
  s = s.replace(/-/g, '/');
  var d = new Date(s);
  return isNaN(d) ? null : d;
}

function ymd(d) {
  return Utilities.formatDate(d, Session.getScriptTimeZone(), "yyyy/MM/dd");
}

function formatTimestamp(timestamp) {
  if (!timestamp) return "";
  var date = new Date(timestamp);
  if (isNaN(date.getTime())) return String(timestamp);
  return Utilities.formatDate(date, Session.getScriptTimeZone(), "yyyy/MM/dd HH:mm:ss");
}

// ===== 重複実行防止機能 =====
function isRecentlyProcessed(key) {
  var now = new Date().getTime();
  if (processingCache[key] && (now - processingCache[key]) < CACHE_TIMEOUT) {
    Logger.log("重複実行を防止: " + key);
    return true;
  }
  processingCache[key] = now;
  
  // 古いキャッシュをクリーンアップ
  for (var k in processingCache) {
    if ((now - processingCache[k]) > CACHE_TIMEOUT) {
      delete processingCache[k];
    }
  }
  
  return false;
}

// ===== IDベース処理の中核: 学生ごとの未退出・最新行を探す =====
function findLatestOpenRowByStudentId(sheet, studentId, limitToToday) {
  var data = sheet.getDataRange().getValues(); // [header,...]
  var todayStr = ymd(new Date());
  for (var i = data.length - 1; i >= 1; i--) {
    var row = data[i];
    if (String(row[1]) !== String(studentId)) continue;       // B列=塾生番号
    if (row[6]) continue;                                     // G列=退出が既に入っていればスキップ
    if (limitToToday) {
      var entry = toDate(row[0]);                             // A列=入室
      if (!entry || ymd(entry) !== todayStr) continue;
    }
    return i + 1; // 1-based row number
  }
  return null;
}

// ===== 最新タイムスタンプの行と列を特定（入室は最新行、退出は当日全体） =====
function findLatestTimestampRowAndColumn(sheet) {
  try {
    var data = sheet.getDataRange().getValues();
    var todayStr = ymd(new Date());
    var latestTimestamp = null;
    var latestRow = null;
    var latestColumn = null;

    // 入室処理：最新行のA列をチェック
    var lastRowIndex = data.length - 1;
    if (lastRowIndex >= 1) { // ヘッダー行より下がある場合
      var lastRow = data[lastRowIndex];
      var lastEntryTime = toDate(lastRow[0]); // A列
      
      if (lastEntryTime) {
        latestTimestamp = lastEntryTime;
        latestRow = lastRowIndex + 1;
        latestColumn = 1;
        Logger.log("最新行の入室時刻を検出: " + latestTimestamp);
      }
    }

    // 退出処理：当日全体のG列から最新タイムスタンプを検索
    for (var i = data.length - 1; i >= 1; i--) { // ヘッダー行をスキップ
      var row = data[i];
      var exitTime = toDate(row[6]); // G列
      
      if (exitTime) {
        var exitDateStr = ymd(exitTime);
        
        // 当日の退出時刻のみを対象にする
        if (exitDateStr === todayStr) {
          // 既存の最新タイムスタンプと比較
          if (!latestTimestamp || exitTime > latestTimestamp) {
            latestTimestamp = exitTime;
            latestRow = i + 1;
            latestColumn = 7;
            Logger.log("当日の退出時刻を検出: " + latestTimestamp + " (行: " + latestRow + ")");
          }
        }
      }
    }

    if (latestTimestamp) {
      return {
        timestamp: latestTimestamp,
        row: latestRow,
        column: latestColumn
      };
    }
    
    return null;
  } catch (error) {
    Logger.log("findLatestTimestampRowAndColumn処理中にエラー: " + error.toString());
    return null;
  }
}

// ===== 名前引き（既存ロジック流用可） =====
function getStudentNameById(studentId) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(QR_SHEET_NAME);
    if (!sheet) {
      Logger.log("エラー: シート '" + QR_SHEET_NAME + "' が見つかりません。");
      return null;
    }
    var data = sheet.getDataRange().getValues();
    for (var i = 1; i < data.length; i++) {
      if (String(data[i][0]) === String(studentId)) return data[i][1]; // B列: 名前
    }
    return null;
  } catch (error) {
    Logger.log("getStudentNameById処理中にエラーが発生しました: " + error.toString());
    return null;
  }
}

// ===== 保護者情報取得 =====
function getGuardianInfo(studentName) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(STUDENT_ROSTER_SHEET_NAME);
    if (!sheet) {
      Logger.log("エラー: シート '" + STUDENT_ROSTER_SHEET_NAME + "' が見つかりません。");
      return null;
    }

    var data = sheet.getDataRange().getValues();
    for (var i = 1; i < data.length; i++) { // ヘッダー行をスキップ
      if (data[i][1] === studentName) { // B列: 利用者名前
        return {
          guardianName: data[i][5] || "", // F列: 保護者氏名
          email: data[i][11] || "", // L列: メールアドレス
          notificationSetting: data[i][12] || "" // M列: 出席通知
        };
      }
    }
    return null;
  } catch (error) {
    Logger.log("getGuardianInfo処理中にエラーが発生しました: " + error.toString());
    return null;
  }
}

// ===== 通知設定判定 =====
function isNotificationEnabled(setting) {
  if (!setting) return false;
  var enabledValues = ["希望する", "Y", "TRUE", "true", "1"];
  return enabledValues.indexOf(String(setting)) !== -1;
}

// ===== 重複送信防止チェック =====
function isDuplicateNotification(uniqueKey) {
  try {
    var sheet = getOrCreateLogSheet();
    var data = sheet.getDataRange().getValues();

    for (var i = 1; i < data.length; i++) { // ヘッダー行をスキップ
      if (data[i][6] === uniqueKey) { // G列: ユニークキー
        return true;
      }
    }
    return false;
  } catch (error) {
    Logger.log("isDuplicateNotification処理中にエラーが発生しました: " + error.toString());
    return false;
  }
}

// ===== ログシート作成/取得 =====
function getOrCreateLogSheet() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName(LOG_SHEET_NAME);

  if (!sheet) {
    sheet = spreadsheet.insertSheet(LOG_SHEET_NAME);
    // ヘッダー行を追加
    sheet.appendRow([
      "送信日時", "塾生番号", "生徒名", "送信先メール", "ステータス", "送信結果", "ユニークキー"
    ]);
  }

  return sheet;
}

// ===== メール送信 =====
function sendEmail(guardianInfo, studentName, status, timestamp) {
  try {
    // メールアドレスの基本的な形式チェックのみ実施
    if (!guardianInfo.email || !guardianInfo.email.includes("@")) {
      Logger.log("無効なメールアドレス形式です: " + guardianInfo.email);
      return false;
    }

    var subject = "【Onedrop】" + studentName + "さんの" + status + "通知";
    var body = guardianInfo.guardianName + " 様へ\n\n" +
               formatTimestamp(timestamp) + "\n\n" +
               studentName + " さんが " + status + " しました。";

    MailApp.sendEmail(guardianInfo.email, subject, body);
    Logger.log("メール送信成功: " + guardianInfo.email);
    return true;

  } catch (error) {
    Logger.log("メール送信エラー: " + error.toString());
    Logger.log("送信先: " + guardianInfo.email + ", 学生名: " + studentName);
    return false;
  }
}

// ===== ログ記録 =====
function logNotification(studentId, studentName, email, status, timestamp, success, uniqueKey) {
  try {
    var sheet = getOrCreateLogSheet();
    var now = new Date();

    sheet.appendRow([
      now, // A列: 送信日時
      studentId, // B列: 塾生番号
      studentName, // C列: 生徒名
      email, // D列: 送信先メール
      status, // E列: ステータス（入室/退出）
      success ? "OK" : "ERROR", // F列: 送信結果
      uniqueKey // G列: ユニークキー
    ]);

  } catch (error) {
    Logger.log("logNotification処理中にエラーが発生しました: " + error.toString());
  }
}

// ===== 出席通知メール送信（統合版） =====
function sendAttendanceNotification(studentId, studentName, status, timestamp, editedRow, triggerSource) {
  try {
    Logger.log("=== 通知送信開始 ===");
    Logger.log("パラメータ: " + JSON.stringify({
      studentId: studentId,
      studentName: studentName,
      status: status,
      timestamp: timestamp,
      editedRow: editedRow,
      triggerSource: triggerSource
    }));

    // 生徒名簿から保護者情報を取得
    var guardianInfo = getGuardianInfo(studentName);
    if (!guardianInfo) {
      Logger.log("生徒 " + studentName + " の保護者情報が見つかりません。");
      return;
    }

    // 通知設定をチェック
    if (!isNotificationEnabled(guardianInfo.notificationSetting)) {
      Logger.log("生徒 " + studentName + " は通知対象外です。設定: " + guardianInfo.notificationSetting);
      return;
    }

    // 重複送信防止チェック（行番号とミリ秒とトリガー種別を含む）
    var uniqueKey = studentId + "_" + status + "_" + (editedRow || "0") + "_" + new Date(timestamp).getTime() + "_" + (triggerSource || "manual");
    if (isDuplicateNotification(uniqueKey)) {
      Logger.log("重複送信を防止しました。キー: " + uniqueKey);
      return;
    }

    // メール送信
    var success = sendEmail(guardianInfo, studentName, status, timestamp);

    // ログ記録
    logNotification(studentId, studentName, guardianInfo.email, status, timestamp, success, uniqueKey);

    Logger.log("=== 通知送信完了 ===");

  } catch (error) {
    Logger.log("sendAttendanceNotification処理中にエラーが発生しました: " + error.toString());
  }
}

// ===== doPost: 入室/退出を studentId で完結 =====
// 期待ペイロード例：
// { "action":"enter", "studentId":"25D005", "mood":"くもり", "sleep":"50％", "purpose":"話す" }
// { "action":"exit",  "studentId":"25D005" }
function doPost(e) {
  var resp = { status: "error", message: "不明なエラー", row: null };
  var lock = LockService.getScriptLock();
  
  try {
    if (!lock.tryLock(30000)) {
      resp.message = "処理中です。しばらくお待ちください。";
      return ContentService.createTextOutput(JSON.stringify(resp)).setMimeType(ContentService.MimeType.JSON);
    }

    if (!e || !e.postData || !e.postData.contents) {
      resp.message = "postDataが空です。";
      return ContentService.createTextOutput(JSON.stringify(resp)).setMimeType(ContentService.MimeType.JSON);
    }

    var body = JSON.parse(e.postData.contents);
    var action = (body.action || "").toLowerCase();
    var studentId = body.studentId;
    
    if (!studentId || !action || (action !== "enter" && action !== "exit")) {
      resp.message = "action または studentId が不正です。";
      return ContentService.createTextOutput(JSON.stringify(resp)).setMimeType(ContentService.MimeType.JSON);
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName(INPUT_SHEET_NAME);
    if (!sheet) {
      resp.message = "シートが見つかりません: " + INPUT_SHEET_NAME;
      return ContentService.createTextOutput(JSON.stringify(resp)).setMimeType(ContentService.MimeType.JSON);
    }

    var now = new Date();
    var studentName = getStudentNameById(studentId) || "";

    if (action === "enter") {
      // 入室：新規行を追加（A:入室, B:ID, C:名前, D:気分, E:睡眠, F:目的, G:退出(空)）
      var row = [
        now,
        studentId,
        studentName,
        body.mood || "",
        body.sleep || "",
        body.purpose || "",
        "" // exit
      ];
      sheet.appendRow(row);
      var newRow = sheet.getLastRow();

      // 通知（統合版の sendAttendanceNotification を利用）
      sendAttendanceNotification(studentId, studentName, "入室", now, newRow, "doPost");
      resp.status = "success";
      resp.message = "入室記録を追加しました。";
      resp.row = newRow;

    } else if (action === "exit") {
      // 退出：当該IDの未退出・最新行を特定（同日制限は要件に応じて true/false）
      var targetRow = findLatestOpenRowByStudentId(sheet, studentId, /*limitToToday=*/false);
      if (!targetRow) {
        resp.message = "未退出の入室記録が見つかりません。";
        resp.status = "not_found";
      } else {
        // G列に退出時刻を書き込み
        sheet.getRange(targetRow, 7).setValue(now);

        // 通知
        sendAttendanceNotification(studentId, studentName, "退出", now, targetRow, "doPost");

        resp.status = "success";
        resp.message = "退出記録を更新しました。";
        resp.row = targetRow;
      }
    }

  } catch (err) {
    Logger.log("doPost処理中にエラーが発生しました: " + err.toString());
    resp.message = "エラー: " + err.toString();
  } finally {
    try { 
      if (lock) lock.releaseLock(); 
    } catch (_) {}
  }

  return ContentService.createTextOutput(JSON.stringify(resp))
    .setMimeType(ContentService.MimeType.JSON);
}

// ===== 出席変更処理関数（トリガー用）- 改善版 =====
function processAttendanceChange(sheet, editedRow, triggerSource) {
  try {
    Logger.log("=== processAttendanceChange開始 ===");
    Logger.log("処理対象行: " + editedRow + ", トリガー種別: " + triggerSource);

    if (editedRow <= 1) { // ヘッダー行は無視
      Logger.log("ヘッダー行のため処理終了");
      return;
    }

    // 重複実行防止チェック
    var cacheKey = sheet.getName() + "_" + editedRow + "_" + triggerSource;
    if (isRecentlyProcessed(cacheKey)) {
      Logger.log("重複実行のため処理をスキップします");
      return;
    }

    // 編集された行のデータを取得
    var rowData = sheet.getRange(editedRow, 1, 1, 7).getValues()[0];
    Logger.log("行データ: " + JSON.stringify(rowData));

    var timestamp = rowData[0]; // A列: 入室時刻
    var studentId = rowData[1]; // B列: 塾生番号
    var exitTime = rowData[6]; // G列: 退出時刻

    Logger.log("解析結果 - 入室時刻: " + timestamp + ", 塾生番号: " + studentId + ", 退出時刻: " + exitTime);

    // 塾生番号が空の場合はスキップ
    if (!studentId) {
      Logger.log("塾生番号が空のため処理をスキップします。行: " + editedRow);
      return;
    }

    // 入室・退出の判定（改善版）
    var status = "";
    var notificationTimestamp = null;

    Logger.log("判定開始 - トリガー種別: " + triggerSource);

    // onChangeトリガーの場合：新規行追加なので入室処理のみ
    if (triggerSource === "onChange") {
      if (timestamp && studentId && !exitTime) {
        status = "入室";
        notificationTimestamp = timestamp;
        Logger.log("onChange: 入室処理を実行");
      } else {
        Logger.log("onChange: 処理条件に該当せず終了");
        return;
      }
    }
    // onEditトリガーの場合：編集内容に基づいて判定
    else if (triggerSource === "onEdit") {
      // 優先順位1: 退出処理（G列に値があり、A列とB列にも値がある場合）
      if (exitTime && timestamp && studentId) {
        // 入室時刻と退出時刻を比較
        var entryDate = new Date(timestamp);
        var exitDate = new Date(exitTime);

        Logger.log("時刻比較 - 入室: " + entryDate + ", 退出: " + exitDate);

        // 退出時刻が入室時刻より後の場合は退出処理
        if (exitDate > entryDate) {
          status = "退出";
          notificationTimestamp = exitTime;
          Logger.log("onEdit: 退出処理を実行（退出時刻が入室時刻より後）");
        }
        // 退出時刻が入室時刻と同じかそれより前の場合は入室処理
        else {
          status = "入室";
          notificationTimestamp = timestamp;
          Logger.log("onEdit: 入室処理を実行（退出時刻が入室時刻以前）");
        }
      }
      // 優先順位2: 入室のみの処理（G列が空で、A列とB列に値がある場合）
      else if (timestamp && studentId && !exitTime) {
        status = "入室";
        notificationTimestamp = timestamp;
        Logger.log("onEdit: 入室処理を実行（退出時刻なし）");
      }
      // 優先順位3: 退出のみの処理（G列のみ編集された場合）
      else if (exitTime) {
        status = "退出";
        notificationTimestamp = exitTime;
        Logger.log("onEdit: 退出処理を実行（G列のみ編集）");
      }
      // 条件に該当しない場合
      else {
        Logger.log("onEdit: 処理条件に該当せず終了");
        return;
      }
    }

    Logger.log("決定された処理: " + status + ", 通知時刻: " + notificationTimestamp);

    // 塾生番号から生徒名を取得
    var studentName = getStudentNameById(studentId);
    if (!studentName) {
      Logger.log("塾生番号 " + studentId + " に対応する生徒名が見つかりません。");
      return;
    }
    Logger.log("生徒名取得成功: " + studentName);

    // 通知送信処理
    Logger.log("通知送信処理開始: " + status);
    sendAttendanceNotification(studentId, studentName, status, notificationTimestamp, editedRow, triggerSource);
    Logger.log("=== processAttendanceChange完了 ===");

  } catch (error) {
    Logger.log("❌ processAttendanceChange処理中にエラーが発生しました: " + error.toString());
    Logger.log("エラースタック: " + error.stack);
  }
}

// ===== onChangeトリガー - タイムスタンプベース判定 =====
function onChange(e) {
  try {
    Logger.log("=== onChange開始 ===");
    Logger.log("変更タイプ: " + e.changeType);

    var sheet = SpreadsheetApp.getActiveSheet();
    if (sheet.getName() !== INPUT_SHEET_NAME) {
      Logger.log("対象外シートのため処理終了");
      return;
    }

    // 最新のタイムスタンプを持つ行と列を特定
    var result = findLatestTimestampRowAndColumn(sheet);
    if (!result) {
      Logger.log("処理対象となる行が見つかりませんでした");
      return;
    }

    Logger.log("最新タイムスタンプ: " + result.timestamp + ", 行: " + result.row + ", 列: " + result.column);

    var rowData = sheet.getRange(result.row, 1, 1, 7).getValues()[0];
    var studentId = rowData[1]; // B列: 塾生番号
    var studentName = getStudentNameById(studentId);

    if (!studentId || !studentName) {
      Logger.log("塾生番号または名前が取得できませんでした");
      return;
    }

    // A列（入室）かG列（退出）かで処理を分岐
    var status = (result.column === 1) ? "入室" : "退出";
    Logger.log("処理内容: " + status + ", 生徒: " + studentName);

    // 通知送信処理
    sendAttendanceNotification(studentId, studentName, status, result.timestamp, result.row, "onChange");
    Logger.log("=== onChange完了 ===");

  } catch (error) {
    Logger.log("❌ onChange処理中にエラーが発生しました: " + error.toString());
  }
}

// ===== onEditトリガー - 改善版 =====
function onEdit(e) {
  try {
    Logger.log("=== onEdit開始 ===");
    Logger.log("編集された範囲: " + e.range.getA1Notation());
    Logger.log("編集された値: " + e.value);

    var sheet = e.source.getActiveSheet();
    var sheetName = sheet.getName();
    Logger.log("編集されたシート: " + sheetName);

    if (sheetName !== INPUT_SHEET_NAME) {
      Logger.log("対象外シートのため処理終了");
      return;
    }

    var range = e.range;
    var editedColumn = range.getColumn();
    var editedRow = range.getRow();

    Logger.log("編集位置: " + editedColumn + "列目、" + editedRow + "行目");

    if (editedRow <= 1) { // ヘッダー行は無視
      Logger.log("ヘッダー行のため処理終了");
      return;
    }

    // A列、B列、G列の編集を処理対象にする
    if (editedColumn !== 1 && editedColumn !== 2 && editedColumn !== 7) {
      Logger.log("対象外の列のため処理終了: " + editedColumn + "列目");
      return;
    }

    // トリガー種別を明示して共通処理関数を呼び出し
    processAttendanceChange(sheet, editedRow, "onEdit");
    Logger.log("=== onEdit完了 ===");

  } catch (error) {
    Logger.log("❌ onEdit処理中にエラーが発生しました: " + error.toString());
    Logger.log("エラースタック: " + error.stack);
  }
}

// ===== 権限テスト用関数 =====
function testMailPermission() {
  try {
    Logger.log("=== メール権限テスト開始 ===");
    MailApp.sendEmail(
      "onedrop202507@gmail.com",
      "【テスト】GAS権限確認",
      "このメールが届いていれば、Gmail送信権限は正常に動作しています。\n\n送信日時: " + new Date()
    );
    Logger.log("✅ 成功: メール送信権限OK");
    return "メール送信成功！";
  } catch (error) {
    Logger.log("❌ エラー: " + error.toString());
    return "エラー: " + error.toString();
  }
}

// ===== 強制権限要求関数 =====
function forceMailPermission() {
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  MailApp.sendEmail(
    Session.getActiveUser().getEmail(),
    "【強制権限要求】トリガー用権限確認",
    "この関数により、スプレッドシートとメール送信の両権限が要求されます。\n\nスプレッドシート名: " + spreadsheet.getName()
  );
  Logger.log("✅ 強制権限要求完了");
}

// ===== 権限承認用関数 =====
function authorizeSendMail() {
  try {
    MailApp.sendEmail(
      Session.getActiveUser().getEmail(),
      "【権限テスト】トリガー権限確認",
      "この関数実行により、トリガー経由でのメール送信権限が承認されます。"
    );
    Logger.log("✅ トリガー用メール権限承認完了");
  } catch (error) {
    Logger.log("❌ 権限承認エラー: " + error.toString());
  }
}
function doPost(e) {
  // レスポンスのコンテンツタイプをJSONに設定
  ContentService.createTextOutput();
  
  var response = {
    status: "error",
    message: "不明なエラーが発生しました。",
    last_row: null,
    last_exit: null
  };

  try {
    // POSTリクエストの本文から生徒IDを解析
    var params = JSON.parse(e.postData.contents);
    var studentId = params.studentId;

    if (!studentId) {
      response.message = "エラー: studentIdパラメータがありません。";
      return ContentService.createTextOutput(JSON.stringify(response))
        .setMimeType(ContentService.MimeType.JSON);
    }

    // --- 設定 ---
    var INPUT_SHEET_NAME = "生徒出席情報";
    
    // アクティブなスプレッドシートと特定のシートを取得
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(INPUT_SHEET_NAME);
    if (!sheet) {
        response.message = "エラー: シート '" + INPUT_SHEET_NAME + "' が見つかりません。";
        return ContentService.createTextOutput(JSON.stringify(response))
            .setMimeType(ContentService.MimeType.JSON);
    }

    var data = sheet.getDataRange().getValues();
    var today = new Date();
    today.setHours(0, 0, 0, 0); // 日付比較のために時刻をリセット

    var lastRow = null;
    var lastExit = null;

    // 今日の日付で、まだ退出時刻が記録されていない最新のレコードを逆順に探す
    for (var i = data.length - 1; i >= 1; i--) { // ヘッダー行をスキップ
      var row = data[i];
      var rowStudentId = row[1]; // B列（インデックス1）が生徒ID
      
      if (String(rowStudentId) === String(studentId)) {
        var entryTimestamp = row[0]; // A列（インデックス0）が入室時刻
        var entryDate;

        // Pythonからの文字列形式の日付と、シート上の日付オブジェクトの両方に対応
        if (entryTimestamp instanceof Date) {
            entryDate = new Date(entryTimestamp);
        } else if (typeof entryTimestamp === 'string' && entryTimestamp.length > 0) {
            var parts = entryTimestamp.split(' ')[0].split('/');
            if (parts.length === 3) {
                entryDate = new Date(parts[0], parts[1] - 1, parts[2]);
            } else {
                continue; // 想定外の日付形式はスキップ
            }
        } else {
            continue; // タイムスタンプが空や無効な場合はスキップ
        }

        entryDate.setHours(0, 0, 0, 0);

        // 今日の日付で、退出時刻（G列、インデックス6）が空欄かチェック
        if (entryDate.getTime() === today.getTime() && (row.length < 7 || !row[6])) {
          lastRow = i + 1; // 1から始まる行番号を返す
          lastExit = (row.length >= 7) ? row[6] : null;
          break; // 該当レコードを見つけたらループを終了
        }
      }
    }
    
    response.status = "success";
    response.message = "レコードの確認が完了しました。";
    response.last_row = lastRow;
    response.last_exit = lastExit;

  } catch (e) {
    response.message = "リクエスト処理中にエラーが発生しました: " + e.toString();
    Logger.log("エラー: " + e.toString());
  }
  
  // レスポンスをJSON文字列として返す
  return ContentService.createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}
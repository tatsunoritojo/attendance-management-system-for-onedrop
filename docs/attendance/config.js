/*
 * Onedrop塾 出席状況表示 - API設定
 * 
 * Google Apps Script デプロイ後にGAS_API_URLを更新してください
 */

// Google Apps Script Web App URL
// デプロイ後に実際のURLに置き換える
const GAS_API_URL = 'https://script.google.com/macros/s/YOUR_SCRIPT_ID_HERE/exec';

// API設定
const API_CONFIG = {
    // リクエストタイムアウト（ミリ秒）
    timeout: 10000,
    
    // 自動更新間隔（ミリ秒）- 30秒
    updateInterval: 30000,
    
    // リトライ設定
    maxRetries: 3,
    retryDelay: 2000
};

// エラーメッセージ
const ERROR_MESSAGES = {
    network: 'ネットワークエラーが発生しました。接続を確認してください。',
    timeout: 'リクエストがタイムアウトしました。しばらくしてからお試しください。',
    server: 'サーバーエラーが発生しました。管理者に連絡してください。',
    parse: 'データの解析に失敗しました。',
    unknown: '予期しないエラーが発生しました。'
};

// デバッグモード（本番では false に設定）
const DEBUG_MODE = true;

// デバッグ用ログ関数
function debugLog(message, data = null) {
    if (DEBUG_MODE) {
        console.log(`[出席アプリ] ${message}`, data || '');
    }
}

// 設定検証
function validateConfig() {
    if (GAS_API_URL.includes('YOUR_SCRIPT_ID_HERE')) {
        console.warn('⚠️ GAS_API_URLが設定されていません。config.jsを更新してください。');
        return false;
    }
    return true;
}

// 初期化時に設定を検証
debugLog('設定ファイル読み込み完了');
validateConfig();
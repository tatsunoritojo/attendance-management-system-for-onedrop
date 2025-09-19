/*
 * Onedrop塾 出席状況表示 - メインアプリケーション
 * Google Apps Script API と連携してリアルタイム出席状況を表示
 */

class AttendanceDisplay {
    constructor() {
        this.updateTimeElement = document.getElementById('updateTime');
        this.attendeeCountElement = document.getElementById('attendeeCount');
        this.attendeeListElement = document.getElementById('attendeeList');
        
        this.retryCount = 0;
        this.updateTimer = null;
        
        // 初期化
        this.init();
    }
    
    init() {
        debugLog('AttendanceDisplayを初期化中...');
        
        // 設定確認
        if (!validateConfig()) {
            this.showError('設定エラー: Google Apps Script URLが設定されていません');
            return;
        }
        
        // 初回データ取得
        this.fetchAttendance();
        
        // 定期更新を開始
        this.startAutoUpdate();
        
        debugLog('初期化完了');
    }
    
    async fetchAttendance() {
        debugLog('出席データを取得中...');
        
        try {
            const response = await this.makeAPIRequest();
            const data = await response.json();
            
            debugLog('取得したデータ:', data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.displayAttendance(data);
            this.retryCount = 0; // 成功時はリトライカウントをリセット
            
        } catch (error) {
            debugLog('エラー発生:', error);
            this.handleError(error);
        }
    }
    
    async makeAPIRequest() {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);
        
        try {
            const response = await fetch(`${GAS_API_URL}?action=attendance&_=${Date.now()}`, {
                method: 'GET',
                signal: controller.signal,
                headers: {
                    'Accept': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response;
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('timeout');
            }
            throw error;
        }
    }
    
    displayAttendance(data) {
        debugLog('出席データを表示中...', data);
        
        // 最終更新時刻を更新
        this.updateTimeElement.textContent = 
            `最終更新: ${new Date().toLocaleString('ja-JP')}`;
        
        // 在席者数を更新
        const count = data.attendees ? data.attendees.length : 0;
        this.attendeeCountElement.textContent = `現在の在席者: ${count}名`;
        
        // 在席者リストを表示
        if (!data.attendees || data.attendees.length === 0) {
            this.attendeeListElement.innerHTML = 
                '<div class="no-attendees">📚 現在、在席中の生徒はいません</div>';
            return;
        }
        
        // 生徒カードを生成
        this.attendeeListElement.innerHTML = data.attendees.map(student => 
            this.createStudentCard(student)
        ).join('');
    }
    
    createStudentCard(student) {
        const duration = student.duration || this.calculateDuration(student.entryTime);
        
        return `
            <div class="student-card">
                <div class="student-info">
                    <span class="status-indicator"></span>
                    <div class="student-details">
                        <div class="student-name">${this.escapeHtml(student.name)}</div>
                        <div class="student-meta">
                            <span>ID: ${this.escapeHtml(student.id)}</span>
                            <span>入室: ${this.escapeHtml(student.entryTime)}</span>
                        </div>
                    </div>
                </div>
                <div class="duration">${this.escapeHtml(duration)}</div>
            </div>
        `;
    }
    
    calculateDuration(entryTimeStr) {
        if (!entryTimeStr) return '0h 0m';
        
        try {
            const now = new Date();
            const today = now.toDateString();
            const entryTime = new Date(`${today} ${entryTimeStr}`);
            
            // 入室時間が未来の場合は前日として扱う
            if (entryTime > now) {
                entryTime.setDate(entryTime.getDate() - 1);
            }
            
            const diffMs = now.getTime() - entryTime.getTime();
            const diffMins = Math.floor(diffMs / (1000 * 60));
            
            if (diffMins < 0) return '0h 0m';
            
            const hours = Math.floor(diffMins / 60);
            const minutes = diffMins % 60;
            
            return `${hours}h ${minutes}m`;
            
        } catch (error) {
            debugLog('時間計算エラー:', error);
            return '不明';
        }
    }
    
    handleError(error) {
        debugLog('エラーハンドリング:', error);
        
        let errorMessage = ERROR_MESSAGES.unknown;
        
        if (error.message === 'timeout') {
            errorMessage = ERROR_MESSAGES.timeout;
        } else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = ERROR_MESSAGES.network;
        } else if (error.message.includes('HTTP')) {
            errorMessage = ERROR_MESSAGES.server;
        } else if (error.message.includes('JSON')) {
            errorMessage = ERROR_MESSAGES.parse;
        }
        
        this.showError(errorMessage);
        
        // リトライロジック
        if (this.retryCount < API_CONFIG.maxRetries) {
            this.retryCount++;
            debugLog(`${API_CONFIG.retryDelay}ms後にリトライ... (${this.retryCount}/${API_CONFIG.maxRetries})`);
            
            setTimeout(() => {
                this.fetchAttendance();
            }, API_CONFIG.retryDelay);
        }
    }
    
    showError(message) {
        this.attendeeListElement.innerHTML = 
            `<div class="error-message">⚠️ ${this.escapeHtml(message)}</div>`;
    }
    
    startAutoUpdate() {
        debugLog(`${API_CONFIG.updateInterval}msごとの自動更新を開始`);
        
        this.updateTimer = setInterval(() => {
            this.fetchAttendance();
        }, API_CONFIG.updateInterval);
    }
    
    stopAutoUpdate() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
            debugLog('自動更新を停止');
        }
    }
    
    escapeHtml(text) {
        if (typeof text !== 'string') return '';
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// ページ読み込み完了時に初期化
document.addEventListener('DOMContentLoaded', () => {
    debugLog('DOMContentLoaded - アプリケーションを開始');
    
    // グローバルインスタンスとして保存（デバッグ用）
    window.attendanceApp = new AttendanceDisplay();
});

// ページを離れる際のクリーンアップ
window.addEventListener('beforeunload', () => {
    if (window.attendanceApp) {
        window.attendanceApp.stopAutoUpdate();
    }
});

// ウィンドウフォーカス時に即座に更新
window.addEventListener('focus', () => {
    if (window.attendanceApp) {
        debugLog('ウィンドウフォーカス - データを即座に更新');
        window.attendanceApp.fetchAttendance();
    }
});
// ========== 全局状态管理 ==========
const state = {
    history: [],
    totalProcessed: 0,
    totalFailed: 0
};

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    checkConfig();
    updateStats();
    updateHistoryDisplay();

    // 监听批量文本框变化
    const batchTextarea = document.getElementById('batch-urls');
    batchTextarea.addEventListener('input', updateBatchUrlCount);
});

// ========== API调用函数 ==========

/**
 * 检查配置状态
 */
async function checkConfig() {
    const statusBox = document.getElementById('api-status');

    try {
        const response = await fetch('/api/config/check');
        const data = await response.json();

        if (data.configured) {
            statusBox.innerHTML = `<div class="success">✅ ${data.message}</div>`;
            statusBox.className = 'status-box success';
        } else {
            statusBox.innerHTML = `<div class="error">❌ ${data.message}</div>`;
            statusBox.className = 'status-box error';
        }
    } catch (error) {
        statusBox.innerHTML = `<div class="error">❌ 配置检查失败</div>`;
        statusBox.className = 'status-box error';
        console.error('Config check error:', error);
    }
}

/**
 * 处理单个视频
 */
async function processSingle() {
    const urlInput = document.getElementById('single-url');
    const url = urlInput.value.trim();

    if (!url) {
        showToast('请输入视频URL', 'error');
        return;
    }

    if (!validateUrl(url)) {
        showToast('无效的URL格式', 'error');
        return;
    }

    const genXiaohongshu = document.getElementById('gen-xiaohongshu').checked;
    const genBlog = document.getElementById('gen-blog').checked;

    // 显示进度
    const progressContainer = document.getElementById('single-progress');
    const progressBar = document.getElementById('single-progress-bar');
    const statusText = document.getElementById('single-status');
    const resultContainer = document.getElementById('single-result');

    progressContainer.style.display = 'block';
    progressBar.style.width = '30%';
    statusText.textContent = '正在处理视频...';
    resultContainer.innerHTML = '';

    try {
        // 添加超时控制 - 30分钟超时（适合长视频）
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1800000); // 30分钟

        statusText.innerHTML = '正在处理视频...<br><small style="color: var(--text-muted);">这可能需要几分钟到30分钟（取决于视频长度），请耐心等待</small>';

        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: url,
                generate_xiaohongshu: genXiaohongshu,
                generate_blog: genBlog
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        progressBar.style.width = '70%';

        const data = await response.json();

        progressBar.style.width = '100%';

        if (data.success) {
            // 成功
            showToast('处理成功！', 'success');
            addToHistory({
                url: url,
                time: new Date().toLocaleString('zh-CN'),
                files: data.files,
                status: 'success'
            });

            // 显示结果
            displaySingleResult(data, url);

        } else {
            // 失败
            showToast('处理失败', 'error');
            addToHistory({
                url: url,
                time: new Date().toLocaleString('zh-CN'),
                files: [],
                status: 'failed',
                error: data.error
            });

            resultContainer.innerHTML = `
                <div class="error-box">
                    ❌ ${data.error || data.message}
                </div>
            `;
        }

        // 清空输入
        urlInput.value = '';

        // 隐藏进度
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
        }, 1000);

    } catch (error) {
        console.error('Process error:', error);

        let errorMessage = '处理失败';
        let errorDetail = '';

        if (error.name === 'AbortError') {
            errorMessage = '处理超时（30分钟）';
            errorDetail = '视频处理时间过长，可能是网络问题或视频太大。建议：<br>1. 检查网络连接<br>2. 如果访问YouTube，请配置代理<br>3. 尝试使用较短的视频<br>4. 对于超长视频，建议分段处理';
        } else if (error.message.includes('Failed to fetch')) {
            errorMessage = '网络连接失败';
            errorDetail = '无法连接到服务器，请检查：<br>1. 服务器是否正常运行<br>2. 网络连接是否正常<br>3. 防火墙设置';
        } else {
            errorDetail = error.message;
        }

        showToast(errorMessage, 'error');
        resultContainer.innerHTML = `
            <div class="error-box">
                <h4 style="margin-bottom: 0.5rem;">❌ ${errorMessage}</h4>
                <p style="margin: 0; line-height: 1.6;">${errorDetail}</p>
            </div>
        `;
        progressContainer.style.display = 'none';

        addToHistory({
            url: url,
            time: new Date().toLocaleString('zh-CN'),
            files: [],
            status: 'failed',
            error: errorMessage + ': ' + errorDetail.replace(/<br>/g, ' ')
        });
    }
}

/**
 * 批量处理视频
 */
async function processBatch() {
    const batchTextarea = document.getElementById('batch-urls');
    const urlsText = batchTextarea.value.trim();

    if (!urlsText) {
        showToast('请输入至少一个视频URL', 'error');
        return;
    }

    const urls = urlsText.split('\n').map(u => u.trim()).filter(u => u);

    if (urls.length === 0) {
        showToast('请输入有效的URL', 'error');
        return;
    }

    // 验证所有URL
    const invalidUrls = urls.filter(url => !validateUrl(url));
    if (invalidUrls.length > 0) {
        showToast(`发现 ${invalidUrls.length} 个无效URL`, 'error');
        return;
    }

    const genXiaohongshu = document.getElementById('gen-xiaohongshu').checked;
    const genBlog = document.getElementById('gen-blog').checked;

    // 显示进度
    const progressContainer = document.getElementById('batch-progress');
    const progressBar = document.getElementById('batch-progress-bar');
    const statusText = document.getElementById('batch-status');
    const resultContainer = document.getElementById('batch-result');

    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    statusText.textContent = `正在处理 ${urls.length} 个视频...`;
    resultContainer.innerHTML = '';

    try {
        const response = await fetch('/api/batch-process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                urls: urls,
                generate_xiaohongshu: genXiaohongshu,
                generate_blog: genBlog
            })
        });

        const data = await response.json();

        progressBar.style.width = '100%';

        // 添加到历史
        data.results.forEach((result, index) => {
            addToHistory({
                url: urls[index],
                time: new Date().toLocaleString('zh-CN'),
                files: result.files || [],
                status: result.success ? 'success' : 'failed',
                error: result.error
            });
        });

        // 显示批量结果摘要
        displayBatchResults(data);

        showToast(`批量处理完成！成功: ${data.success_count}, 失败: ${data.failed_count}`, 'success');

        // 清空输入
        batchTextarea.value = '';
        updateBatchUrlCount();

        // 隐藏进度
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
        }, 1000);

    } catch (error) {
        console.error('Batch process error:', error);
        showToast('批量处理失败: ' + error.message, 'error');
        resultContainer.innerHTML = `
            <div class="error-box">
                ❌ 批量处理失败: ${error.message}
            </div>
        `;
        progressContainer.style.display = 'none';
    }
}

// ========== UI辅助函数 ==========

/**
 * 切换标签页
 */
function switchTab(tabName) {
    // 隐藏所有标签页内容
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    // 移除所有按钮的active类
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // 显示选中的标签页
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // 激活对应的按钮
    event.target.classList.add('active');

    // 如果切换到历史记录，刷新显示
    if (tabName === 'history') {
        updateHistoryDisplay();
    }
}

/**
 * 显示单个处理结果
 */
function displaySingleResult(data, url) {
    const resultContainer = document.getElementById('single-result');

    let html = `
        <div class="result-item success">
            <div class="result-header">
                <div class="result-title">✅ ${data.message}</div>
            </div>
            <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1rem;">
                ${url}
            </p>
    `;

    if (data.files && data.files.length > 0) {
        html += `
            <div style="margin-bottom: 1rem;">
                <button class="btn btn-primary" onclick="previewAllFiles([${data.files.map(f => `'${f}'`).join(',')}])" style="margin-right: 1rem;">
                    👁️ 查看所有文件
                </button>
                <button class="btn btn-primary" onclick="downloadAllFiles([${data.files.map(f => `'${f}'`).join(',')}])">
                    📥 下载所有文件
                </button>
            </div>
        `;

        html += `<ul class="file-list">`;
        data.files.forEach(file => {
            const fileName = file.split('/').pop();
            const fileType = fileName.includes('xiaohongshu') ? '📱 小红书笔记' :
                            fileName.includes('blog') ? '📝 博客文章' :
                            fileName.includes('organized') ? '📋 整理版' : '📄 原始转录';

            html += `
                <li class="file-item">
                    <div>
                        <div class="file-name">${fileType}</div>
                        <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">${fileName}</div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-download" onclick="previewFile('${file}')">
                            👁️ 预览
                        </button>
                        <button class="btn btn-download" onclick="copyFileContent('${file}')">
                            📋 复制
                        </button>
                        <button class="btn btn-download" onclick="downloadFile('${file}')">
                            📥 下载
                        </button>
                    </div>
                </li>
            `;
        });
        html += `</ul>`;
    }

    html += `</div>`;

    resultContainer.innerHTML = html;
}

/**
 * 显示批量处理结果
 */
function displayBatchResults(data) {
    const resultContainer = document.getElementById('batch-result');

    let html = `
        <h3>📊 批量处理完成</h3>
        <div class="batch-summary">
            <div class="summary-card">
                <div class="summary-number total">${data.total}</div>
                <div class="summary-label">总数</div>
            </div>
            <div class="summary-card">
                <div class="summary-number success">${data.success_count}</div>
                <div class="summary-label">成功</div>
            </div>
            <div class="summary-card">
                <div class="summary-number failed">${data.failed_count}</div>
                <div class="summary-label">失败</div>
            </div>
        </div>

        <h4 style="margin-top: 2rem; margin-bottom: 1rem;">详细结果</h4>
    `;

    data.results.forEach((result, index) => {
        const url = result.files && result.files.length > 0
            ? result.files[0].split('/').slice(0, -1).join('/')
            : '';

        html += `
            <div class="result-item ${result.success ? 'success' : 'error'}">
                <div class="result-header">
                    <div class="result-title">
                        ${result.success ? '✅' : '❌'}
                        视频 ${index + 1}
                    </div>
                </div>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem;">
                    ${result.message}
                </p>
        `;

        if (result.success && result.files && result.files.length > 0) {
            html += `<ul class="file-list">`;
            result.files.forEach(file => {
                const fileName = file.split('/').pop();
                html += `
                    <li class="file-item">
                        <span class="file-name">📄 ${fileName}</span>
                        <div class="file-actions">
                            <button class="btn btn-download" onclick="previewFile('${file}')">
                                👁️ 预览
                            </button>
                            <button class="btn btn-download" onclick="downloadFile('${file}')">
                                📥 下载
                            </button>
                        </div>
                    </li>
                `;
            });
            html += `</ul>`;
        } else if (!result.success) {
            html += `
                <div class="error-box" style="margin-top: 0.5rem;">
                    ${result.error || '未知错误'}
                </div>
            `;
        }

        html += `</div>`;
    });

    resultContainer.innerHTML = html;
}

/**
 * 更新批量URL计数
 */
function updateBatchUrlCount() {
    const batchTextarea = document.getElementById('batch-urls');
    const urlCount = document.getElementById('batch-url-count');
    const urls = batchTextarea.value.trim().split('\n').filter(u => u.trim());

    if (urls.length > 0) {
        urlCount.textContent = `📊 共 ${urls.length} 个URL`;
    } else {
        urlCount.textContent = '';
    }
}

/**
 * 预览文件
 */
async function previewFile(filePath) {
    try {
        const response = await fetch(`/api/file-content/${encodeURIComponent(filePath)}`);
        const data = await response.json();

        // 创建预览弹窗
        const preview = document.createElement('div');
        preview.className = 'preview-modal';
        preview.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 2000;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
        `;

        preview.innerHTML = `
            <div style="
                background: var(--bg-secondary);
                border-radius: 12px;
                max-width: 900px;
                width: 100%;
                max-height: 80vh;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            ">
                <div style="
                    padding: 1.5rem;
                    border-bottom: 1px solid var(--border-color);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <h3 style="margin: 0;">📄 ${data.filename}</h3>
                    <button class="modal-close-btn"
                            style="
                                background: none;
                                border: none;
                                color: var(--text-primary);
                                font-size: 1.5rem;
                                cursor: pointer;
                                padding: 0.5rem;
                                transition: transform 0.2s;
                            "
                            onmouseover="this.style.transform='scale(1.2)'"
                            onmouseout="this.style.transform='scale(1)'">
                        ✕
                    </button>
                </div>
                <div style="
                    padding: 1.5rem;
                    overflow-y: auto;
                    flex: 1;
                ">
                    <pre style="
                        margin: 0;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        font-family: monospace;
                        font-size: 0.9rem;
                        line-height: 1.6;
                        color: var(--text-primary);
                    ">${escapeHtml(data.content)}</pre>
                </div>
                <div style="
                    padding: 1rem 1.5rem;
                    border-top: 1px solid var(--border-color);
                    display: flex;
                    justify-content: flex-end;
                ">
                    <button class="btn btn-download" onclick="downloadFile('${filePath}')">
                        📥 下载文件
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(preview);

        // 关闭按钮点击事件
        const closeBtn = preview.querySelector('.modal-close-btn');
        closeBtn.addEventListener('click', () => {
            preview.remove();
        });

        // 点击背景关闭
        preview.addEventListener('click', (e) => {
            if (e.target === preview) {
                preview.remove();
            }
        });

        // ESC键关闭
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                preview.remove();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

    } catch (error) {
        console.error('Preview error:', error);
        showToast('预览失败', 'error');
    }
}

/**
 * 下载文件
 */
function downloadFile(filePath) {
    window.location.href = `/api/download/${encodeURIComponent(filePath)}`;
}

/**
 * 显示Toast通知
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;

    // 触发动画
    setTimeout(() => toast.classList.add('show'), 10);

    // 3秒后隐藏
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ========== 历史记录管理 ==========

/**
 * 加载历史记录
 */
function loadHistory() {
    const saved = localStorage.getItem('videoHistory');
    if (saved) {
        try {
            const data = JSON.parse(saved);
            state.history = data.history || [];
            state.totalProcessed = data.totalProcessed || 0;
            state.totalFailed = data.totalFailed || 0;
        } catch (e) {
            console.error('Failed to load history:', e);
            state.history = [];
            state.totalProcessed = 0;
            state.totalFailed = 0;
        }
    }
}

/**
 * 保存历史记录
 */
function saveHistory() {
    localStorage.setItem('videoHistory', JSON.stringify({
        history: state.history,
        totalProcessed: state.totalProcessed,
        totalFailed: state.totalFailed
    }));
}

/**
 * 添加到历史记录
 */
function addToHistory(record) {
    state.history.unshift(record);

    // 只保留最近100条
    if (state.history.length > 100) {
        state.history = state.history.slice(0, 100);
    }

    if (record.status === 'success') {
        state.totalProcessed++;
    } else {
        state.totalFailed++;
    }

    saveHistory();
    updateStats();
    updateHistoryDisplay();
}

/**
 * 清空历史记录
 */
function clearHistory() {
    if (confirm('确定要清空所有历史记录吗？')) {
        state.history = [];
        state.totalProcessed = 0;
        state.totalFailed = 0;
        saveHistory();
        updateStats();
        updateHistoryDisplay();
        showToast('历史记录已清空', 'success');
    }
}

/**
 * 更新统计显示
 */
function updateStats() {
    document.getElementById('stat-success').textContent = state.totalProcessed;
    document.getElementById('stat-failed').textContent = state.totalFailed;
}

/**
 * 更新历史记录显示
 */
function updateHistoryDisplay() {
    const historyList = document.getElementById('history-list');

    if (state.history.length === 0) {
        historyList.innerHTML = '<div class="info-box">暂无处理记录</div>';
        return;
    }

    let html = '';

    state.history.forEach((record, index) => {
        const statusIcon = record.status === 'success' ? '✅' : '❌';
        const statusClass = record.status === 'success' ? 'success' : 'failed';

        html += `
            <div class="history-item ${statusClass}" onclick="toggleHistoryDetails(${index})">
                <div class="history-header">
                    <span>${statusIcon} ${record.time}</span>
                    <span class="history-time">${record.status === 'success' ? '成功' : '失败'}</span>
                </div>
                <div class="history-url">${record.url}</div>

                <div id="history-details-${index}" style="display: none; margin-top: 1rem;">
        `;

        if (record.status === 'success' && record.files && record.files.length > 0) {
            html += `
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 0.5rem;">
                    生成了 ${record.files.length} 个文件
                </p>
                <ul class="file-list">
            `;
            record.files.forEach(file => {
                const fileName = file.split('/').pop();
                html += `
                    <li class="file-item">
                        <span class="file-name">📄 ${fileName}</span>
                        <div class="file-actions">
                            <button class="btn btn-download" onclick="event.stopPropagation(); previewFile('${file}')">
                                👁️ 预览
                            </button>
                            <button class="btn btn-download" onclick="event.stopPropagation(); downloadFile('${file}')">
                                📥 下载
                            </button>
                        </div>
                    </li>
                `;
            });
            html += `</ul>`;
        } else if (record.status === 'failed') {
            html += `
                <div class="error-box" style="margin-top: 0.5rem;">
                    ${record.error || '未知错误'}
                </div>
            `;
        }

        html += `
                </div>
            </div>
        `;
    });

    historyList.innerHTML = html;
}

/**
 * 切换历史记录详情显示
 */
function toggleHistoryDetails(index) {
    const details = document.getElementById(`history-details-${index}`);
    if (details) {
        details.style.display = details.style.display === 'none' ? 'block' : 'none';
    }
}

// ========== 工具函数 ==========

/**
 * 验证URL格式
 */
function validateUrl(url) {
    return url.startsWith('http://') || url.startsWith('https://');
}

/**
 * HTML转义
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * 复制文件内容到剪贴板
 */
async function copyFileContent(filePath) {
    try {
        const response = await fetch(`/api/file-content/${encodeURIComponent(filePath)}`);
        const data = await response.json();

        await navigator.clipboard.writeText(data.content);
        showToast('✅ 内容已复制到剪贴板', 'success');

    } catch (error) {
        console.error('Copy error:', error);
        showToast('复制失败', 'error');
    }
}

/**
 * 预览所有文件
 */
async function previewAllFiles(filePaths) {
    try {
        // 创建预览窗口
        const preview = document.createElement('div');
        preview.className = 'preview-all-modal';
        preview.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 2000;
            overflow-y: auto;
            padding: 2rem;
        `;

        let contentHtml = `
            <div style="
                max-width: 1200px;
                margin: 0 auto;
                background: var(--bg-secondary);
                border-radius: 16px;
                padding: 2rem;
            ">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 2rem;
                    padding-bottom: 1rem;
                    border-bottom: 2px solid var(--border-glass);
                ">
                    <h2 style="margin: 0; color: var(--text-primary);">📄 所有生成的文件</h2>
                    <button class="modal-close-all-btn"
                            style="
                                background: var(--bg-glass);
                                border: 1px solid var(--border-glass);
                                color: var(--text-primary);
                                font-size: 1.5rem;
                                cursor: pointer;
                                padding: 0.5rem 1rem;
                                border-radius: 8px;
                                transition: transform 0.2s;
                            "
                            onmouseover="this.style.transform='scale(1.1)'"
                            onmouseout="this.style.transform='scale(1)'">
                        ✕
                    </button>
                </div>
        `;

        // 加载所有文件内容
        for (const filePath of filePaths) {
            const response = await fetch(`/api/file-content/${encodeURIComponent(filePath)}`);
            const data = await response.json();
            const fileName = filePath.split('/').pop();
            const fileType = fileName.includes('xiaohongshu') ? '📱 小红书笔记' :
                            fileName.includes('blog') ? '📝 博客文章' :
                            fileName.includes('organized') ? '📋 整理版笔记' : '📄 原始转录';

            contentHtml += `
                <div style="
                    background: var(--bg-glass);
                    border: 1px solid var(--border-glass);
                    border-radius: 12px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                ">
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 1rem;
                        padding-bottom: 0.75rem;
                        border-bottom: 1px solid var(--border-glass);
                    ">
                        <h3 style="margin: 0; color: var(--text-primary);">${fileType}</h3>
                        <div>
                            <button class="btn btn-download" onclick="copyText(\`${data.content.replace(/`/g, '\\`')}\`)" style="margin-right: 0.5rem;">
                                📋 复制
                            </button>
                            <button class="btn btn-download" onclick="downloadFile('${filePath}')">
                                📥 下载
                            </button>
                        </div>
                    </div>
                    <div style="
                        font-size: 0.85rem;
                        color: var(--text-muted);
                        margin-bottom: 1rem;
                    ">${fileName}</div>
                    <pre style="
                        margin: 0;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        font-family: 'Courier New', monospace;
                        font-size: 0.9rem;
                        line-height: 1.6;
                        color: var(--text-primary);
                        max-height: 500px;
                        overflow-y: auto;
                    ">${escapeHtml(data.content)}</pre>
                </div>
            `;
        }

        contentHtml += `</div>`;
        preview.innerHTML = contentHtml;
        document.body.appendChild(preview);

        // 关闭按钮点击事件
        const closeBtn = preview.querySelector('.modal-close-all-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                preview.remove();
            });
        }

        // 点击背景关闭
        preview.addEventListener('click', (e) => {
            if (e.target === preview) {
                preview.remove();
            }
        });

        // ESC键关闭
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                preview.remove();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);

    } catch (error) {
        console.error('Preview all error:', error);
        showToast('预览失败', 'error');
    }
}

/**
 * 下载所有文件（打包）
 */
async function downloadAllFiles(filePaths) {
    showToast('开始下载所有文件...', 'info');

    for (const filePath of filePaths) {
        await downloadFile(filePath);
        // 添加小延迟避免浏览器阻止多个下载
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    showToast('✅ 所有文件下载完成', 'success');
}

/**
 * 复制文本到剪贴板（辅助函数）
 */
async function copyText(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('✅ 内容已复制到剪贴板', 'success');
    } catch (error) {
        console.error('Copy error:', error);
        showToast('复制失败', 'error');
    }
}

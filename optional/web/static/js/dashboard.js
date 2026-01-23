// SOCKS5代理池 Dashboard - JavaScript

let allProxies = [];
let filteredProxies = [];
let sortColumn = 'avg_score';
let sortAscending = false;
let autoRefreshInterval = null;
let countryChart = null;
let sourcesChart = null;

// 初始化
document.addEventListener('DOMContentLoaded', function () {
    refreshAll();
    startAutoRefresh();
});

// 刷新所有数据
function refreshAll() {
    Promise.all([
        fetchStats(),
        fetchProxies(),
        fetchSources()
    ]).then(() => {
        updateLastUpdateTime();
    });
}

// 获取统计数据
async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const result = await response.json();

        if (result.success) {
            const stats = result.data;

            // 更新统计卡片
            document.getElementById('total-proxies').textContent = stats.total_proxies;
            document.getElementById('active-proxies').textContent = stats.active_proxies_24h;
            document.getElementById('success-rate').textContent =
                (stats.success_rate_24h * 100).toFixed(1) + '%';
            document.getElementById('total-validations').textContent = stats.total_validations;

            // 更新国家分布图表
            updateCountryChart(stats.top_countries);

            // 更新国家过滤器
            updateCountryFilter(stats.top_countries);
        }
    } catch (error) {
        console.error('获取统计数据失败:', error);
    }
}

// 获取代理列表
async function fetchProxies() {
    try {
        const response = await fetch('/api/proxies?limit=100');
        const result = await response.json();

        if (result.success) {
            allProxies = result.data;
            filteredProxies = [...allProxies];
            renderProxies();
        }
    } catch (error) {
        console.error('获取代理列表失败:', error);
        document.getElementById('proxy-table-body').innerHTML =
            '<tr><td colspan="7" class="loading">加载失败: ' + error.message + '</td></tr>';
    }
}

// 获取代理源状态
async function fetchSources() {
    try {
        const response = await fetch('/api/sources');
        const result = await response.json();

        if (result.success) {
            updateSourcesChart(result.data);
        }
    } catch (error) {
        console.error('获取代理源状态失败:', error);
    }
}

// 渲染代理列表
function renderProxies() {
    const tbody = document.getElementById('proxy-table-body');

    if (filteredProxies.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="loading">暂无数据</td></tr>';
        return;
    }

    const html = filteredProxies.map(proxy => {
        const score = proxy.avg_score || 0;
        const scoreClass = score >= 70 ? 'score-high' : score >= 50 ? 'score-medium' : 'score-low';
        const successRate = (proxy.success_rate * 100).toFixed(0);
        const responseTime = proxy.avg_response_time ? proxy.avg_response_time.toFixed(2) : 'N/A';

        return `
            <tr>
                <td><span class="proxy-address">${proxy.proxy_address}</span></td>
                <td>${proxy.country || '未知'}</td>
                <td><span class="score-badge ${scoreClass}">${score.toFixed(1)}</span></td>
                <td>${successRate}%</td>
                <td>${responseTime}s</td>
                <td>${proxy.total_checks}</td>
                <td>
                    <button class="action-btn" onclick="showProxyDetails('${proxy.proxy_address}')">
                        详情
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    tbody.innerHTML = html;
}

// 过滤代理
function filterProxies() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const countryFilter = document.getElementById('country-filter').value;

    filteredProxies = allProxies.filter(proxy => {
        // 搜索过滤
        const matchesSearch = !searchTerm ||
            proxy.proxy_address.toLowerCase().includes(searchTerm) ||
            (proxy.country && proxy.country.toLowerCase().includes(searchTerm));

        // 国家过滤
        const matchesCountry = !countryFilter || proxy.country === countryFilter;

        return matchesSearch && matchesCountry;
    });

    renderProxies();
}

// 排序表格
function sortTable(column) {
    if (sortColumn === column) {
        sortAscending = !sortAscending;
    } else {
        sortColumn = column;
        sortAscending = false;
    }

    filteredProxies.sort((a, b) => {
        let valA = a[column];
        let valB = b[column];

        // 处理null/undefined
        if (valA == null) valA = sortAscending ? Number.MAX_VALUE : Number.MIN_VALUE;
        if (valB == null) valB = sortAscending ? Number.MAX_VALUE : Number.MIN_VALUE;

        // 字符串比较
        if (typeof valA === 'string') {
            return sortAscending ?
                valA.localeCompare(valB) :
                valB.localeCompare(valA);
        }

        // 数字比较
        return sortAscending ? valA - valB : valB - valA;
    });

    renderProxies();
}

// 更新国家分布图表
function updateCountryChart(countries) {
    const ctx = document.getElementById('countryChart').getContext('2d');

    if (countryChart) {
        countryChart.destroy();
    }

    const labels = countries.slice(0, 8).map(c => c.country);
    const data = countries.slice(0, 8).map(c => c.count);

    countryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b',
                    '#10b981', '#3b82f6', '#ef4444', '#14b8a6'
                ],
                borderWidth: 2,
                borderColor: '#1e293b'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#f1f5f9',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

// 更新代理源图表
function updateSourcesChart(sources) {
    const ctx = document.getElementById('sourcesChart').getContext('2d');

    if (sourcesChart) {
        sourcesChart.destroy();
    }

    // 只显示活跃源的前10个
    const activeSources = sources.filter(s => s.is_active).slice(0, 10);
    const labels = activeSources.map(s => {
        const url = s.source_url;
        return url.length > 30 ? url.substring(0, 27) + '...' : url;
    });
    const data = activeSources.map(s => s.total_proxies_found);

    sourcesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: '代理数量',
                data: data,
                backgroundColor: '#6366f1',
                borderColor: '#4f46e5',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#94a3b8'
                    },
                    grid: {
                        color: '#334155'
                    }
                },
                x: {
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: '#334155'
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// 更新国家过滤器
function updateCountryFilter(countries) {
    const select = document.getElementById('country-filter');
    const currentValue = select.value;

    // 保留"所有国家"选项
    select.innerHTML = '<option value="">所有国家</option>';

    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country.country;
        option.textContent = `${country.country} (${country.count})`;
        select.appendChild(option);
    });

    // 恢复之前的选择
    if (currentValue) {
        select.value = currentValue;
    }
}

// 显示代理详情
async function showProxyDetails(proxyAddress) {
    try {
        const response = await fetch(`/api/proxy/${encodeURIComponent(proxyAddress)}`);
        const result = await response.json();

        if (result.success) {
            const proxy = result.data;
            const successRate = (proxy.success_rate * 100).toFixed(1);

            const html = `
                <div style="line-height: 1.8;">
                    <p><strong>代理地址:</strong> <code>${proxy.proxy_address}</code></p>
                    <p><strong>国家:</strong> ${proxy.country || '未知'}</p>
                    <p><strong>城市:</strong> ${proxy.city || '未知'}</p>
                    <p><strong>ISP:</strong> ${proxy.isp || '未知'}</p>
                    <hr style="margin: 20px 0; border-color: #334155;">
                    <p><strong>总检查次数:</strong> ${proxy.total_checks}</p>
                    <p><strong>成功次数:</strong> ${proxy.success_count}</p>
                    <p><strong>成功率:</strong> ${successRate}%</p>
                    <p><strong>平均响应时间:</strong> ${proxy.avg_response_time?.toFixed(2) || 'N/A'}s</p>
                    <p><strong>平均评分:</strong> ${proxy.avg_score?.toFixed(1) || 'N/A'}</p>
                    <hr style="margin: 20px 0; border-color: #334155;">
                    <p><strong>首次发现:</strong> ${proxy.first_seen}</p>
                    <p><strong>最后检查:</strong> ${proxy.last_check || 'N/A'}</p>
                </div>
            `;

            document.getElementById('proxy-details').innerHTML = html;
            document.getElementById('proxy-modal').style.display = 'block';
        }
    } catch (error) {
        console.error('获取代理详情失败:', error);
        alert('获取代理详情失败: ' + error.message);
    }
}

// 关闭模态框
function closeModal() {
    document.getElementById('proxy-modal').style.display = 'none';
}

// 点击模态框外部关闭
window.onclick = function (event) {
    const modal = document.getElementById('proxy-modal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
}

// 导出代理
function exportProxies() {
    const format = prompt('选择导出格式:\n1. JSON\n2. TXT\n3. CSV\n\n请输入数字 (1-3):', '1');

    let formatType = 'json';
    if (format === '2') formatType = 'txt';
    else if (format === '3') formatType = 'csv';

    window.open(`/api/export?format=${formatType}`, '_blank');
}

// 自动刷新
function toggleAutoRefresh() {
    const checkbox = document.getElementById('auto-refresh');
    if (checkbox.checked) {
        startAutoRefresh();
    } else {
        stopAutoRefresh();
    }
}

function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    // 每30秒刷新一次
    autoRefreshInterval = setInterval(refreshAll, 30000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// 更新最后更新时间
function updateLastUpdateTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('zh-CN');
    document.getElementById('last-update').textContent = timeStr;
}

const { ipcRenderer } = require('electron');
const path = require('path');

const PERSONALITIES = ["开朗", "胆小", "急躁", "平和", "沉默", "踏实", "固执", "聪明", "悠闲", "懒散", "天真", "大胆", "调皮", "勇敢", "逞强", "稳重", "坦率", "专注", "偏执", "冷静", "理性", "警惕", "温顺", "害羞", "慎重", "焦虑", "莽撞", "热情", "忧郁", "粗心"];
const EGG_GROUPS = ["巨灵组", "两栖组", "昆虫组", "天空组", "动物组", "妖精组", "植物组", "拟人组", "软体组", "大地组", "魔力组", "海洋组", "龙组", "机械组"];

// 获取图标路径 (在 Electron 中处理)
function getIconPath(iconName) {
    const isPackaged = __dirname.includes('app.asar');
    const base = isPackaged ? path.join(process.resourcesPath, 'icons') : path.join(__dirname, 'icons');
    return `file://${path.join(base, iconName)}`;
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    switchTab('warehouse');
    loadWarehouse();
    loadProduction();
    loadSold();
    loadAftersales();
    setDefaultDate();
});

function switchTab(tabId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    event.target.classList.add('active');
    if (tabId === 'warehouse') loadWarehouse();
    if (tabId === 'production') loadProduction();
    if (tabId === 'sold') loadSold();
    if (tabId === 'aftersales') loadAftersales();
}

function setDefaultDate() {
    const now = new Date();
    const str = `${now.getFullYear()}年${now.getMonth()+1}月${now.getDate()}日 ${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`;
    document.getElementById('eggDate').value = str;
}

// ========== 仓库逻辑 ==========
async function loadWarehouse() {
    let sql = `SELECT * FROM eggs WHERE status IN ('在库', '需售后')`;
    const rows = await ipcRenderer.invoke('db-query', sql);
    const tbody = document.querySelector('#warehouseTable tbody');
    tbody.innerHTML = '';
    
    rows.forEach((row, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${idx+1}</td>
            <td>${row.account}</td>
            <td>${row.name}</td>
            <td>${row.personality}</td>
            <td>${row.size}</td>
            <td>${row.weight}</td>
            <td>${row.date}</td>
            <td>${row.price}</td>
            <td>${row.status}</td>
            <td>${row.notes}</td>
            <td>${renderMedal(row.medal1, 'size')}</td>
            <td>${renderMedal(row.medal2, 'sound')}</td>
            <td>${renderNest(row.nest_type)}</td>
            <td><button onclick='editEgg(${JSON.stringify(row)})'>编辑</button></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderMedal(medalText, type) {
    if (!medalText || medalText === '无') return '';
    const map = type === 'size' 
        ? {'大块头':'big.png','满重':'heavy.png','小不点':'small.png','满轻':'light.png'}
        : {'婉转声':'sound_melodious.png','满音婉转声':'sound_full_melodious.png','粗嗓门':'sound_rough.png','满音粗嗓门':'sound_full_rough.png'};
    if (map[medalText]) {
        return `<img src="${getIconPath(map[medalText])}" class="icon-img" title="${medalText}" onerror="this.style.display='none'; this.parentNode.innerText='${medalText}'">`;
    }
    return medalText;
}

function renderNest(nestType) {
    const iconName = nestType === 'green_nest' ? 'green_nest.png' : 'normal_nest.png';
    return `<img src="${getIconPath(iconName)}" class="icon-img" onerror="this.style.display='none'; this.parentNode.innerText='${nestType === 'green_nest' ? '绿窝' : '普窝'}'">`;
}

// ========== 弹窗逻辑 ==========
function openEggModal() {
    document.getElementById('eggModal').style.display = 'block';
    document.getElementById('eggName').value = '';
    document.getElementById('eggPersonality').value = '';
    document.getElementById('eggSize').value = '';
    document.getElementById('eggWeight').value = '';
    document.getElementById('eggPrice').value = '';
    document.getElementById('eggNotes').value = '';
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

async function saveEgg() {
    const eggData = {
        account: document.getElementById('eggAccount').value,
        name: document.getElementById('eggName').value,
        personality: document.getElementById('eggPersonality').value,
        size: document.getElementById('eggSize').value,
        weight: document.getElementById('eggWeight').value,
        date: document.getElementById('eggDate').value,
        price: document.getElementById('eggPrice').value,
        status: document.getElementById('eggStatus').value,
        notes: document.getElementById('eggNotes').value,
        medal1: document.getElementById('eggMedal1').value,
        medal2: document.getElementById('eggMedal2').value,
        nest_type: document.getElementById('eggNest').value
    };
    
    const sql = `INSERT INTO eggs (account, name, personality, size, weight, date, price, status, notes, medal1, medal2, nest_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`;
    await ipcRenderer.invoke('db-query', sql, Object.values(eggData));
    closeModal('eggModal');
    loadWarehouse();
}

function editEgg(row) {
    alert('编辑功能待实现：' + row.name);
}

// ========== 产线逻辑 (简写) ==========
async function loadProduction() {
    const rows = await ipcRenderer.invoke('db-query', 'SELECT * FROM production_lines');
    const tbody = document.querySelector('#productionTable tbody');
    tbody.innerHTML = '';
    rows.forEach((row, idx) => {
        tbody.innerHTML += `<tr><td>${idx+1}</td><td>${row.account_name}</td><td>${row.account_id}</td><td>${row.egg_name}</td><td>${row.personality}</td><td>${row.decibel}</td><td>${row.egg_group}</td></tr>`;
    });
}

// ========== 售出/售后逻辑 (简写，原理同上) ==========
async function loadSold() {
    const rows = await ipcRenderer.invoke('db-query', `SELECT * FROM eggs WHERE status IN ('已售出', '补发蛋')`);
    // 渲染逻辑...
}

async function loadAftersales() {
    const rows = await ipcRenderer.invoke('db-query', `SELECT * FROM eggs WHERE status IN ('需售后', '已售后')`);
    // 渲染逻辑及底色判断...
}

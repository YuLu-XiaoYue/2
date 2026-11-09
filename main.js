const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();

let mainWindow;
let db;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  mainWindow.loadFile('index.html');
}

// 初始化数据库
function initDB() {
  const dbPath = path.join(app.getPath('userData'), 'warehouse.db');
  db = new sqlite3.Database(dbPath);
  
  db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS eggs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      account TEXT, name TEXT, personality TEXT, size REAL, weight REAL,
      date TEXT, price REAL, status TEXT, notes TEXT,
      medal1 TEXT, medal2 TEXT, nest_type TEXT, buyer_platform TEXT, buyer_name TEXT, buyer_id TEXT
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS production_lines (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      account_name TEXT, account_id TEXT, egg_name TEXT, personality TEXT, decibel TEXT, egg_group TEXT
    )`);
  });
}

app.whenReady().then(() => {
  initDB();
  createWindow();
});

// 接收前端发来的数据库请求
ipcMain.handle('db-query', (event, sql, params = []) => {
  return new Promise((resolve, reject) => {
    if (sql.trim().toUpperCase().startsWith('SELECT')) {
      db.all(sql, params, (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    } else {
      db.run(sql, params, function(err) {
        if (err) reject(err);
        else resolve({ id: this.lastID, changes: this.changes });
      });
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

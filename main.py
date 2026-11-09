import sys
import os
import sqlite3
import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem, 
                               QComboBox, QLineEdit, QLabel, QPushButton, QDialog, 
                               QDialogButtonBox, QCheckBox, QDateEdit, QTimeEdit, 
                               QHeaderView, QMessageBox, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QIcon, QPixmap

# ================= 数据库配置 =================
DB_NAME = "lock_kingdom.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # 表结构：id, 所属账号, 精灵蛋名, 性格, 尺寸, 重量, 拿蛋日期, 定价, 状态, 备注, 奖牌1, 奖牌2, 窝类型, 分贝值, 蛋组, 买家平台, 买家名称, 买家ID
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eggs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT, name TEXT, personality TEXT, size REAL, weight REAL,
            date TEXT, price REAL, status TEXT, notes TEXT,
            medal1 TEXT, medal2 TEXT, nest_type TEXT,
            decibel TEXT, egg_group TEXT,
            buyer_platform TEXT, buyer_name TEXT, buyer_id TEXT
        )
    ''')
    # 产线表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS production_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT, account_id TEXT, egg_name TEXT, personality TEXT,
            decibel TEXT, egg_group TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ================= 数据字典 =================
PERSONALITIES = ["开朗", "胆小", "急躁", "平和", "沉默", "踏实", "固执", "聪明", "悠闲", "懒散", "天真", "大胆", "调皮", "勇敢", "逞强", "稳重", "坦率", "专注", "偏执", "冷静", "理性", "警惕", "温顺", "害羞", "慎重", "焦虑", "莽撞", "热情", "忧郁", "粗心"]
EGG_GROUPS = ["巨灵组", "两栖组", "昆虫组", "天空组", "动物组", "妖精组", "植物组", "拟人组", "软体组", "大地组", "魔力组", "海洋组", "龙组", "机械组"]
MEDALS_SIZE = ["无", "大块头", "满重", "小不点", "满轻"]
MEDALS_SOUND = ["无", "婉转声", "满音婉转声", "粗嗓门", "满音粗嗓门"]
STATUS_OPTIONS = ["在库", "已售出", "需售后", "补发蛋", "已售后"]

# 获取图标路径
def get_icon(name):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    path = os.path.join(base_path, 'icons', name)
    return path if os.path.exists(path) else ""

# ================= 自定义组件 =================

# 自定义浮窗多选/单选组件
class FloatingSelector(QLineEdit):
    def __init__(self, items, multi_select=False, max_select=1):
        super().__init__()
        self.items = items
        self.multi_select = multi_select
        self.max_select = max_select
        self.setReadOnly(True)
        self.setPlaceholderText("点击选择...")
        self.mousePressEvent = self.show_popup

    def show_popup(self, event):
        dialog = QDialog(self)
        dialog.setWindowTitle("请选择")
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        
        for item_text in self.items:
            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            if self.multi_select:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Unchecked)
            list_widget.addItem(item)
            
        # 如果是单选，点击直接确定
        if not self.multi_select:
            list_widget.itemClicked.connect(lambda i: self.confirm_single(i, dialog))
        
        layout.addWidget(list_widget)
        
        if self.multi_select:
            btn = QPushButton("确定")
            btn.clicked.connect(lambda: self.confirm_multi(list_widget, dialog))
            layout.addWidget(btn)
            
        dialog.exec()

    def confirm_single(self, item, dialog):
        self.setText(item.text())
        dialog.accept()

    def confirm_multi(self, list_widget, dialog):
        selected = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.text())
        if len(selected) > self.max_select:
            QMessageBox.warning(self, "警告", f"最多只能选择 {self.max_select} 个！")
            return
        self.setText(", ".join(selected))
        dialog.accept()

# 价格自动计算逻辑
class PriceInput(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("自动计算/手动修改")
        # 默认价格区间示例
        self.price_ranges = [(0, 1.5, 1.0), (1.5, 3, 1.5), (3, 6, 2.5), (6, 100, 5.0)]

    def update_price_by_weight(self, weight_str):
        try:
            weight = float(weight_str)
            for min_w, max_w, price in self.price_ranges:
                if min_w <= weight < max_w:
                    self.setText(f"{price:.2f}")
                    return
            self.setText("0.00")
        except ValueError:
            self.setText("")

# ================= 主窗口 =================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("洛克王国精灵蛋仓库")
        self.resize(1400, 800)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # 初始化四个页面
        self.tab_warehouse = QWidget()
        self.tab_production = QWidget()
        self.tab_sold = QWidget()
        self.tab_aftersales = QWidget()
        
        self.tabs.addTab(self.tab_warehouse, "仓库")
        self.tabs.addTab(self.tab_production, "产线")
        self.tabs.addTab(self.tab_sold, "已售出/补发")
        self.tabs.addTab(self.tab_aftersales, "售后蛋")
        
        self.setup_warehouse()
        self.setup_production()
        self.setup_sold()
        self.setup_aftersales()
        
        # 监听标签页切换，自动刷新数据
        self.tabs.currentChanged.connect(self.refresh_all_tables)

    # ====== 页面 1：仓库 ======
    def setup_warehouse(self):
        layout = QVBoxLayout(self.tab_warehouse)
        
        # 工具栏
        toolbar = QHBoxLayout()
        btn_add = QPushButton("添加精灵蛋")
        btn_add.clicked.connect(self.add_egg_dialog)
        toolbar.addWidget(btn_add)
        
        # 全局筛选
        self.filter_account = QComboBox(); self.filter_account.addItem("全部账号")
        self.filter_name = QComboBox(); self.filter_name.addItem("全部精灵蛋")
        self.filter_medal = QComboBox(); self.filter_medal.addItem("全部奖牌")
        self.filter_medal.addItems(MEDALS_SIZE[1:] + MEDALS_SOUND[1:])
        self.filter_nest = QComboBox(); self.filter_nest.addItems(["全部窝", "普窝", "绿窝"])
        self.filter_sort = QComboBox(); self.filter_sort.addItems(["默认排序", "重量由轻到重", "重量由重到轻", "时间由近到远", "时间由远到近"])
        
        for w in [self.filter_account, self.filter_name, self.filter_medal, self.filter_nest, self.filter_sort]:
            toolbar.addWidget(w)
            w.currentIndexChanged.connect(self.load_warehouse_data)
            
        layout.addLayout(toolbar)
        
        # 表格
        self.table_warehouse = QTableWidget()
        cols = ["序号", "所属账号", "精灵蛋名", "性格", "尺寸", "重量", "拿蛋日期", "定价", "状态", "备注", "尺寸奖牌", "声音奖牌", "窝类型", "操作"]
        self.table_warehouse.setColumnCount(len(cols))
        self.table_warehouse.setHorizontalHeaderLabels(cols)
        self.table_warehouse.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_warehouse)

    def load_warehouse_data(self):
        self.table_warehouse.setRowCount(0)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        query = "SELECT * FROM eggs WHERE status IN ('在库', '需售后')" # 仓库显示在库和需售后
        params = []
        
        # 筛选条件处理
        if self.filter_account.currentText() != "全部账号":
            query += " AND account = ?"
            params.append(self.filter_account.currentText())
        if self.filter_name.currentText() != "全部精灵蛋":
            query += " AND name = ?"
            params.append(self.filter_name.currentText())
        if self.filter_nest.currentText() != "全部窝":
            nest_val = "green_nest" if self.filter_nest.currentText() == "绿窝" else "normal_nest"
            query += " AND nest_type = ?"
            params.append(nest_val)
            
        # 排序处理
        sort_text = self.filter_sort.currentText()
        if sort_text == "重量由轻到重": query += " ORDER BY weight ASC"
        elif sort_text == "重量由重到轻": query += " ORDER BY weight DESC"
        elif sort_text == "时间由近到远": query += " ORDER BY date DESC"
        elif sort_text == "时间由远到近": query += " ORDER BY date ASC"
        else: query += " ORDER BY id ASC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        for idx, row in enumerate(rows):
            self.table_warehouse.insertRow(idx)
            
            # 字段映射: id[0], account[1], name[2], personality[3], size[4], weight[5], date[6], price[7], status[8], notes[9], medal1[10], medal2[11], nest_type[12]
            self.table_warehouse.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.table_warehouse.setItem(idx, 1, QTableWidgetItem(row[1]))
            self.table_warehouse.setItem(idx, 2, QTableWidgetItem(row[2]))
            self.table_warehouse.setItem(idx, 3, QTableWidgetItem(row[3]))
            self.table_warehouse.setItem(idx, 4, QTableWidgetItem(str(row[4])))
            self.table_warehouse.setItem(idx, 5, QTableWidgetItem(str(row[5])))
            self.table_warehouse.setItem(idx, 6, QTableWidgetItem(row[6]))
            self.table_warehouse.setItem(idx, 7, QTableWidgetItem(str(row[7])))
            self.table_warehouse.setItem(idx, 8, QTableWidgetItem(row[8]))
            self.table_warehouse.setItem(idx, 9, QTableWidgetItem(row[9]))
            self.table_warehouse.setItem(idx, 10, QTableWidgetItem(row[10]))
            self.table_warehouse.setItem(idx, 11, QTableWidgetItem(row[11]))
            
            # 窝类型图标显示
            lbl_nest = QLabel()
            pix = QPixmap(get_icon(row[12]))
            if not pix.isNull():
                lbl_nest.setPixmap(pix.scaled(30, 30, Qt.KeepAspectRatio))
            else:
                lbl_nest.setText("绿窝" if row[12] == "green_nest" else "普窝")
            self.table_warehouse.setCellWidget(idx, 12, lbl_nest)
            
            # 操作按钮
            btn_edit = QPushButton("编辑")
            btn_edit.clicked.connect(lambda checked, r=row: self.edit_egg_dialog(r))
            self.table_warehouse.setCellWidget(idx, 13, btn_edit)
            
        # 更新筛选下拉框数据
        self.update_filter_combos()
        conn.close()

    def update_filter_combos(self):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        self.filter_account.clear(); self.filter_account.addItem("全部账号")
        cursor.execute("SELECT DISTINCT account FROM eggs WHERE account != ''")
        for r in cursor.fetchall(): self.filter_account.addItem(r[0])
        
        self.filter_name.clear(); self.filter_name.addItem("全部精灵蛋")
        cursor.execute("SELECT DISTINCT name FROM eggs WHERE name != ''")
        for r in cursor.fetchall(): self.filter_name.addItem(r[0])
        conn.close()

    # ====== 添加/编辑 弹窗 ======
    def add_egg_dialog(self, row_data=None):
        dialog = QDialog(self)
        dialog.setWindowTitle("添加/编辑精灵蛋" if row_data else "添加精灵蛋")
        dialog.setMinimumWidth(600)
        layout = QVBoxLayout(dialog)
        
        # 表单
        form_layout = QHBoxLayout()
        col1 = QVBoxLayout()
        col2 = QVBoxLayout()
        
        # 账号 (需从产线读取，这里模拟)
        col1.addWidget(QLabel("所属账号："))
        acc_combo = QComboBox()
        acc_combo.addItems(["1234567890 (主号)", "0987654321 (小号)"]) # 实际中从产线表读取
        col1.addWidget(acc_combo)
        
        col1.addWidget(QLabel("精灵蛋名："))
        name_input = QLineEdit()
        col1.addWidget(name_input)
        
        col1.addWidget(QLabel("性格："))
        personality_input = FloatingSelector(PERSONALITIES, multi_select=False)
        col1.addWidget(personality_input)
        
        col1.addWidget(QLabel("尺寸："))
        size_input = QLineEdit()
        col1.addWidget(size_input)
        
        col1.addWidget(QLabel("重量："))
        weight_input = QLineEdit()
        col1.addWidget(weight_input)
        
        col1.addWidget(QLabel("拿蛋日期："))
        date_input = QLineEdit(datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"))
        col1.addWidget(date_input)
        
        col1.addWidget(QLabel("定价："))
        price_input = PriceInput()
        col1.addWidget(price_input)
        
        # 重量联动价格
        weight_input.textChanged.connect(lambda text: price_input.update_price_by_weight(text))
        
        # 第二列
        col2.addWidget(QLabel("状态："))
        status_combo = QComboBox()
        status_combo.addItems(STATUS_OPTIONS)
        col2.addWidget(status_combo)
        
        col2.addWidget(QLabel("备注："))
        notes_input = QLineEdit()
        col2.addWidget(notes_input)
        
        col2.addWidget(QLabel("尺寸奖牌(互斥)："))
        medal1_combo = QComboBox()
        medal1_combo.addItems(MEDALS_SIZE)
        col2.addWidget(medal1_combo)
        
        col2.addWidget(QLabel("声音奖牌(互斥)："))
        medal2_combo = QComboBox()
        medal2_combo.addItems(MEDALS_SOUND)
        col2.addWidget(medal2_combo)
        
        col2.addWidget(QLabel("窝类型："))
        nest_combo = QComboBox()
        nest_combo.addItems(["普窝", "绿窝"])
        col2.addWidget(nest_combo)
        
        form_layout.addLayout(col1)
        form_layout.addLayout(col2)
        layout.addLayout(form_layout)
        
        # 保存按钮
        btn_save = QPushButton("保存")
        layout.addWidget(btn_save)
        
        # 如果是编辑，回显数据
        if row_data:
            name_input.setText(row_data[2])
            personality_input.setText(row_data[3])
            size_input.setText(str(row_data[4]))
            weight_input.setText(str(row_data[5]))
            date_input.setText(row_data[6])
            price_input.setText(str(row_data[7]))
            status_combo.setCurrentText(row_data[8])
            notes_input.setText(row_data[9])
            medal1_combo.setCurrentText(row_data[10])
            medal2_combo.setCurrentText(row_data[11])
            nest_combo.setCurrentText("绿窝" if row_data[12] == "green_nest" else "普窝")
            
        def save_data():
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            # 确定窝类型的英文标识
            nest_val = "green_nest" if nest_combo.currentText() == "绿窝" else "normal_nest"
            
            if row_data: # 更新
                cursor.execute('''UPDATE eggs SET account=?, name=?, personality=?, size=?, weight=?, date=?, price=?, status=?, notes=?, medal1=?, medal2=?, nest_type=? WHERE id=?''',
                               (acc_combo.currentText(), name_input.text(), personality_input.text(), size_input.text(), weight_input.text(),
                                date_input.text(), price_input.text(), status_combo.currentText(), notes_input.text(),
                                medal1_combo.currentText(), medal2_combo.currentText(), nest_val, row_data[0]))
            else: # 插入
                cursor.execute('''INSERT INTO eggs (account, name, personality, size, weight, date, price, status, notes, medal1, medal2, nest_type) 
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (acc_combo.currentText(), name_input.text(), personality_input.text(), size_input.text(), weight_input.text(),
                                date_input.text(), price_input.text(), status_combo.currentText(), notes_input.text(),
                                medal1_combo.currentText(), medal2_combo.currentText(), nest_val))
            conn.commit()
            conn.close()
            dialog.accept()
            self.refresh_all_tables()
            
        btn_save.clicked.connect(save_data)
        dialog.exec()

    def edit_egg_dialog(self, row_data):
        self.add_egg_dialog(row_data)

    # ====== 页面 2：产线 ======
    def setup_production(self):
        layout = QVBoxLayout(self.tab_production)
        toolbar = QHBoxLayout()
        btn_add = QPushButton("添加产线")
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)
        
        self.table_production = QTableWidget()
        cols = ["序号", "游戏账号名称", "游戏账号ID", "精灵蛋名", "精灵蛋性格", "分贝值", "蛋组"]
        self.table_production.setColumnCount(len(cols))
        self.table_production.setHorizontalHeaderLabels(cols)
        self.table_production.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_production)
        
        btn_add.clicked.connect(self.add_production_dialog)

    def load_production_data(self):
        self.table_production.setRowCount(0)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM production_lines")
        for idx, row in enumerate(cursor.fetchall()):
            self.table_production.insertRow(idx)
            self.table_production.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.table_production.setItem(idx, 1, QTableWidgetItem(row[1]))
            self.table_production.setItem(idx, 2, QTableWidgetItem(row[2]))
            self.table_production.setItem(idx, 3, QTableWidgetItem(row[3]))
            self.table_production.setItem(idx, 4, QTableWidgetItem(row[4]))
            self.table_production.setItem(idx, 5, QTableWidgetItem(row[5]))
            self.table_production.setItem(idx, 6, QTableWidgetItem(row[6]))
        conn.close()

    def add_production_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("添加产线")
        layout = QVBoxLayout(dialog)
        
        acc_name = QLineEdit(); acc_name.setPlaceholderText("游戏账号名称")
        acc_id = QLineEdit(); acc_id.setPlaceholderText("游戏账号ID")
        egg_name = QLineEdit(); egg_name.setPlaceholderText("精灵蛋名")
        personality = FloatingSelector(PERSONALITIES, False)
        decibel = QLineEdit(); decibel.setPlaceholderText("分贝值")
        egg_group = FloatingSelector(EGG_GROUPS, multi_select=True, max_select=2)
        
        for label, w in [("账号名称:", acc_name), ("账号ID:", acc_id), ("精灵蛋名:", egg_name), 
                         ("性格:", personality), ("分贝值:", decibel), ("蛋组(选2):", egg_group)]:
            layout.addWidget(QLabel(label))
            layout.addWidget(w)
            
        btn = QPushButton("保存")
        btn.clicked.connect(lambda: (
            sqlite3.connect(DB_NAME).execute("INSERT INTO production_lines (account_name, account_id, egg_name, personality, decibel, egg_group) VALUES (?, ?, ?, ?, ?, ?)", 
                                             (acc_name.text(), acc_id.text(), egg_name.text(), personality.text(), decibel.text(), egg_group.text())).connection.commit(),
            dialog.accept(), self.refresh_all_tables()
        ))
        layout.addWidget(btn)
        dialog.exec()

    # ====== 页面 3：已售出/补发 ======
    def setup_sold(self):
        layout = QVBoxLayout(self.tab_sold)
        
        self.table_sold = QTableWidget()
        cols = ["序号", "所属账号", "精灵蛋名", "性格", "重量", "定价", "状态", "买家平台", "买家名称", "买家ID", "操作"]
        self.table_sold.setColumnCount(len(cols))
        self.table_sold.setHorizontalHeaderLabels(cols)
        self.table_sold.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_sold)

    def load_sold_data(self):
        self.table_sold.setRowCount(0)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM eggs WHERE status IN ('已售出', '补发蛋')")
        for idx, row in enumerate(cursor.fetchall()):
            self.table_sold.insertRow(idx)
            # 已售出数据锁定，不可编辑，只能改状态
            self.table_sold.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.table_sold.setItem(idx, 1, QTableWidgetItem(row[1]))
            self.table_sold.setItem(idx, 2, QTableWidgetItem(row[2]))
            self.table_sold.setItem(idx, 3, QTableWidgetItem(row[3]))
            self.table_sold.setItem(idx, 5, QTableWidgetItem(row[5]))
            self.table_sold.setItem(idx, 6, QTableWidgetItem(row[7]))
            
            # 状态可编辑
            status_combo = QComboBox()
            status_combo.addItems(["已售出", "补发蛋", "需售后"])
            status_combo.setCurrentText(row[8])
            status_combo.currentTextChanged.connect(lambda text, r_id=row[0]: self.update_status(r_id, text))
            self.table_sold.setCellWidget(idx, 6, status_combo)
            
            # 买家信息输入框
            buyer_platform = QLineEdit(row[14])
            buyer_name = QLineEdit(row[15])
            buyer_id = QLineEdit(row[16])
            self.table_sold.setCellWidget(idx, 7, buyer_platform)
            self.table_sold.setCellWidget(idx, 8, buyer_name)
            self.table_sold.setCellWidget(idx, 9, buyer_id)
            
            # 保存买家信息按钮
            btn_save_buyer = QPushButton("保存买家")
            btn_save_buyer.clicked.connect(lambda checked, r_id=row[0], bp=buyer_platform, bn=buyer_name, bi=buyer_id: self.save_buyer_info(r_id, bp, bn, bi))
            self.table_sold.setCellWidget(idx, 10, btn_save_buyer)
        conn.close()

    def save_buyer_info(self, r_id, bp, bn, bi):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE eggs SET buyer_platform=?, buyer_name=?, buyer_id=? WHERE id=?", (bp.text(), bn.text(), bi.text(), r_id))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "成功", "买家信息已保存")

    def update_status(self, r_id, text):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE eggs SET status=? WHERE id=?", (text, r_id))
        conn.commit()
        conn.close()
        self.refresh_all_tables()

    # ====== 页面 4：售后蛋 ======
    def setup_aftersales(self):
        layout = QVBoxLayout(self.tab_aftersales)
        
        self.table_aftersales = QTableWidget()
        cols = ["序号", "所属账号", "精灵蛋名", "重量", "状态", "买家平台", "买家名称", "买家ID", "操作"]
        self.table_aftersales.setColumnCount(len(cols))
        self.table_aftersales.setHorizontalHeaderLabels(cols)
        self.table_aftersales.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table_aftersales)

    def load_aftersales_data(self):
        self.table_aftersales.setRowCount(0)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM eggs WHERE status IN ('需售后', '已售后')")
        for idx, row in enumerate(cursor.fetchall()):
            self.table_aftersales.insertRow(idx)
            self.table_aftersales.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.table_aftersales.setItem(idx, 1, QTableWidgetItem(row[1]))
            self.table_aftersales.setItem(idx, 2, QTableWidgetItem(row[2]))
            self.table_aftersales.setItem(idx, 4, QTableWidgetItem(row[5]))
            self.table_aftersales.setItem(idx, 5, QTableWidgetItem(row[14]))
            self.table_aftersales.setItem(idx, 6, QTableWidgetItem(row[15]))
            self.table_aftersales.setItem(idx, 7, QTableWidgetItem(row[16]))
            
            # 状态选择 (需售后 / 已售后)
            status_combo = QComboBox()
            status_combo.addItems(["需售后", "已售后"])
            status_combo.setCurrentText(row[8])
            status_combo.currentTextChanged.connect(lambda text, r_id=row[0], r=idx: self.update_aftersales_status(r_id, text, r))
            self.table_aftersales.setCellWidget(idx, 4, status_combo)
            
            # 底色处理
            if row[8] == "需售后":
                for col in range(8): self.table_aftersales.item(idx, col).setBackground(Qt.red)
                self.table_aftersales.item(idx, 0).setBackground(Qt.red)
            elif row[8] == "已售后":
                for col in range(8): 
                    if self.table_aftersales.item(idx, col):
                        self.table_aftersales.item(idx, col).setBackground(Qt.green)
        conn.close()

    def update_aftersales_status(self, r_id, text, row_idx):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE eggs SET status=? WHERE id=?", (text, r_id))
        conn.commit()
        conn.close()
        self.refresh_all_tables()

    # ====== 全局刷新 ======
    def refresh_all_tables(self):
        self.load_warehouse_data()
        self.load_production_data()
        self.load_sold_data()
        self.load_aftersales_data()

if __name__ == "__main__":
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

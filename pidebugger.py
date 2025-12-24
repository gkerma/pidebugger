#!/usr/bin/env python3
"""
PiDebugger v5.1 Modular - VSCode Style + Système Modulaire
Interface professionnelle avec détection contexte et modules dynamiques
"""

import sys
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QComboBox, QLabel,
    QListWidget, QSplitter, QStatusBar, QFrame, QListWidgetItem
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QTextCursor, QTextCharFormat
from PyQt6.QtWidgets import QStyleFactory

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("⚠️  pyserial non installé")

try:
    from core.context_detector import ContextDetector, ContextType
    from core.module_manager import ModuleManager
    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    print("⚠️  Modules core/ non trouvés")


class SerialReader(QThread):
    """Thread lecture série"""
    data_received = pyqtSignal(str, float)
    
    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self.running = True
    
    def run(self):
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    text = data.decode('utf-8', errors='replace')
                    self.data_received.emit(text, time.time())
                time.sleep(0.01)
            except Exception as e:
                print(f"Erreur: {e}")
                break
    
    def stop(self):
        self.running = False


class VSCodeSidebar(QWidget):
    """Sidebar VSCode avec icônes"""
    button_clicked = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setFixedWidth(50)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 10, 0, 10)
        
        buttons = [
            ("🏠", "home", "Home"),
            ("📊", "status", "Boot Status"),
            ("💾", "modules", "Modules"),
            ("💡", "suggestions", "Suggestions"),
            ("⚙️", "settings", "Settings"),
        ]
        
        for icon, name, tooltip in buttons:
            btn = QPushButton(icon)
            btn.setObjectName(name)
            btn.setToolTip(tooltip)
            btn.setFixedSize(45, 45)
            btn.clicked.connect(lambda checked, n=name: self.button_clicked.emit(n))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    font-size: 20pt;
                }
                QPushButton:hover {
                    background-color: #2a2a2a;
                }
                QPushButton:pressed {
                    background-color: #007acc;
                }
            """)
            layout.addWidget(btn)
        
        layout.addStretch()


class ModulePanel(QWidget):
    """Panel d'affichage des modules actifs"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        
        title = QLabel("📦 Active Modules")
        title.setStyleSheet("""
            font-size: 15pt;
            font-weight: bold;
            color: #007acc;
            padding: 6px;
        """)
        
        self.modules_list = QListWidget()
        self.modules_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                color: #d4d4d4;
                font-size: 13pt;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #3e3e42;
            }
            QListWidget::item:selected {
                background-color: #007acc;
            }
        """)
        
        layout.addWidget(title)
        layout.addWidget(self.modules_list)
    
    def update_modules(self, modules: list):
        """Met à jour la liste des modules"""
        self.modules_list.clear()
        for module in modules:
            item = QListWidgetItem(f"✅ {module}")
            self.modules_list.addItem(item)


class SuggestionsPanel(QWidget):
    """Panel de suggestions contextuelles"""
    
    command_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        
        title = QLabel("💡 Suggestions")
        title.setStyleSheet("""
            font-size: 15pt;
            font-weight: bold;
            color: #007acc;
            padding: 6px;
        """)
        
        self.suggestions_list = QListWidget()
        self.suggestions_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                color: #89d185;
                font-size: 13pt;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #3e3e42;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: #ffffff;
            }
        """)
        self.suggestions_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        layout.addWidget(title)
        layout.addWidget(self.suggestions_list)
    
    def update_suggestions(self, suggestions: list):
        """Met à jour les suggestions"""
        self.suggestions_list.clear()
        for cmd in suggestions[:10]:
            item = QListWidgetItem(f"• {cmd}")
            self.suggestions_list.addItem(item)
    
    def on_item_double_clicked(self, item):
        """Double-clic sur suggestion"""
        cmd = item.text().replace("• ", "")
        self.command_selected.emit(cmd)


class PiDebuggerV51(QMainWindow):
    """PiDebugger v5.1 Modular"""
    
    def __init__(self):
        super().__init__()
        self.serial = None
        self.reader_thread = None
        self.start_time = None
        self.rx_bytes = 0
        self.tx_bytes = 0
        
        # Core components
        if CORE_AVAILABLE:
            self.context_detector = ContextDetector()
            self.module_manager = ModuleManager()
            # Découvrir et charger modules
            modules = self.module_manager.discover_modules()
            for module in modules:
                self.module_manager.load_module(module)
        else:
            self.context_detector = None
            self.module_manager = None
        
        self.init_ui()
        self.apply_vscode_theme()
        
        # Timer status bar
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(1000)
        
        # Timer port refresh
        self.port_timer = QTimer()
        self.port_timer.timeout.connect(self.refresh_ports)
        self.port_timer.start(2000)
    
    def init_ui(self):
        """Interface"""
        self.setWindowTitle('⚙️ PiDebugger v5.1 Modular - VSCode Style')
        self.setGeometry(100, 100, 1800, 900)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = VSCodeSidebar()
        self.sidebar.button_clicked.connect(self.on_sidebar_clicked)
        
        # Splitter 3 colonnes
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel gauche: Modules + Suggestions
        left_panel = self.create_left_panel()
        
        # Panel centre: Terminal
        center_panel = self.create_center_panel()
        
        # Panel droit: Hardware + Timeline
        right_panel = self.create_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 900, 300])
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(splitter)
        
        # Status bar
        self.create_status_bar()
    
    def create_left_panel(self):
        """Panel gauche: Modules + Suggestions"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.module_panel = ModulePanel()
        self.suggestions_panel = SuggestionsPanel()
        self.suggestions_panel.command_selected.connect(self.on_suggestion_selected)
        
        layout.addWidget(self.module_panel, stretch=1)
        layout.addWidget(self.suggestions_panel, stretch=2)
        
        return widget
    
    def create_center_panel(self):
        """Panel centre: Terminal"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Connection
        conn_layout = QHBoxLayout()
        conn_layout.setSpacing(8)
        
        conn_label = QLabel("🔌")
        conn_label.setStyleSheet("font-size: 16pt;")
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(250)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedWidth(40)
        self.refresh_btn.clicked.connect(self.refresh_ports)
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setFixedWidth(100)
        
        conn_layout.addWidget(conn_label)
        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(self.refresh_btn)
        conn_layout.addWidget(self.connect_btn)
        conn_layout.addStretch()
        
        # Terminal
        term_label = QLabel("💻 Terminal")
        term_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #007acc;")
        
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14pt;
                border: 1px solid #3e3e42;
                padding: 8px;
            }
        """)
        
        # Input
        input_layout = QHBoxLayout()
        input_layout.setSpacing(4)
        
        prompt = QLabel(">")
        prompt.setStyleSheet("font-size: 16pt; color: #007acc; font-weight: bold;")
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Type command...")
        self.command_input.returnPressed.connect(self.send_command)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self.send_command)
        
        self.enter_btn = QPushButton("↵")
        self.enter_btn.setFixedWidth(50)
        self.enter_btn.setToolTip("Send Enter")
        self.enter_btn.clicked.connect(self.send_enter)
        
        self.interrupt_btn = QPushButton("^C")
        self.interrupt_btn.setFixedWidth(50)
        self.interrupt_btn.clicked.connect(self.send_interrupt)
        
        input_layout.addWidget(prompt)
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.enter_btn)
        input_layout.addWidget(self.interrupt_btn)
        
        layout.addLayout(conn_layout)
        layout.addWidget(term_label)
        layout.addWidget(self.terminal)
        layout.addLayout(input_layout)
        
        return widget
    
    def create_right_panel(self):
        """Panel droit: Hardware + Timeline"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Context
        context_label = QLabel("🎯 Context")
        context_label.setStyleSheet("font-size: 15pt; font-weight: bold; color: #007acc;")
        
        self.context_text = QLabel("Disconnected")
        self.context_text.setStyleSheet("""
            background-color: #2d2d30;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            padding: 12px;
            font-size: 13pt;
            color: #569cd6;
        """)
        self.context_text.setWordWrap(True)
        
        # Hardware
        hw_label = QLabel("🔧 Hardware")
        hw_label.setStyleSheet("font-size: 15pt; font-weight: bold; color: #007acc;")
        
        self.hardware_text = QLabel("No hardware detected")
        self.hardware_text.setStyleSheet("""
            background-color: #2d2d30;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            padding: 12px;
            font-size: 13pt;
            color: #ce9178;
        """)
        self.hardware_text.setWordWrap(True)
        
        # Timeline
        timeline_label = QLabel("📈 Timeline")
        timeline_label.setStyleSheet("font-size: 15pt; font-weight: bold; color: #007acc;")
        
        self.timeline_list = QListWidget()
        self.timeline_list.setStyleSheet("""
            QListWidget {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                color: #d4d4d4;
                font-size: 12pt;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px;
            }
        """)
        
        layout.addWidget(context_label)
        layout.addWidget(self.context_text)
        layout.addWidget(hw_label)
        layout.addWidget(self.hardware_text)
        layout.addWidget(timeline_label)
        layout.addWidget(self.timeline_list, stretch=1)
        
        return widget
    
    def create_status_bar(self):
        """Status bar"""
        status = self.statusBar()
        status.setStyleSheet("""
            QStatusBar {
                background-color: #007acc;
                color: #ffffff;
                font-size: 12pt;
                padding: 4px 8px;
            }
        """)
        
        self.status_context = QLabel("Context: —")
        self.status_port = QLabel("Port: —")
        self.status_uptime = QLabel("Uptime: —")
        self.status_stats = QLabel("RX: 0 | TX: 0")
        
        status.addWidget(self.status_context)
        status.addWidget(QLabel(" │ "))
        status.addWidget(self.status_port)
        status.addWidget(QLabel(" │ "))
        status.addWidget(self.status_uptime)
        status.addPermanentWidget(self.status_stats)
    
    def apply_vscode_theme(self):
        """Thème VSCode"""
        self.setStyle(QStyleFactory.create('Fusion'))
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#d4d4d4"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#d4d4d4"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#2d2d30"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#d4d4d4"))
        
        self.setPalette(palette)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 13pt;
                color: #d4d4d4;
            }
            QPushButton:hover {
                background-color: #3e3e42;
                border-color: #007acc;
            }
            QPushButton:pressed {
                background-color: #007acc;
            }
            QComboBox {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 13pt;
                color: #d4d4d4;
            }
            QLineEdit {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                padding: 6px 12px;
                font-size: 13pt;
                color: #d4d4d4;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """)
    
    def refresh_ports(self):
        """Rafraîchit les ports"""
        if not SERIAL_AVAILABLE:
            return
        
        current = self.port_combo.currentText()
        self.port_combo.clear()
        
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")
        
        idx = self.port_combo.findText(current)
        if idx >= 0:
            self.port_combo.setCurrentIndex(idx)
    
    def toggle_connection(self):
        """Toggle connexion"""
        if self.serial and self.serial.is_open:
            self.disconnect()
        else:
            self.connect()
    
    def connect(self):
        """Connexion"""
        if not SERIAL_AVAILABLE:
            return
        
        port_text = self.port_combo.currentText()
        if not port_text:
            return
        
        port = port_text.split(' - ')[0]
        
        try:
            self.serial = serial.Serial(port, 115200, timeout=0.1)
            self.reader_thread = SerialReader(self.serial)
            self.reader_thread.data_received.connect(self.on_data_received)
            self.reader_thread.start()
            
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setStyleSheet("background-color: #f48771;")
            self.start_time = time.time()
            
            if self.context_detector:
                self.context_detector.current_context.type = ContextType.UNKNOWN
            
            self.append_terminal(f"✅ Connected to {port}\n", "#89d185")
            
        except Exception as e:
            self.append_terminal(f"❌ Error: {e}\n", "#f48771")
    
    def disconnect(self):
        """Déconnexion"""
        if self.reader_thread:
            self.reader_thread.stop()
            self.reader_thread.wait()
        
        if self.serial:
            self.serial.close()
            self.serial = None
        
        self.connect_btn.setText("Connect")
        self.connect_btn.setStyleSheet("")
        self.start_time = None
        
        self.append_terminal("❌ Disconnected\n", "#f48771")
    
    def send_command(self):
        """Envoie commande"""
        cmd = self.command_input.text()
        if not cmd or not self.serial or not self.serial.is_open:
            return
        
        try:
            self.serial.write((cmd + '\n').encode('utf-8'))
            self.serial.flush()
            self.tx_bytes += len(cmd) + 1
            self.append_terminal(f"{cmd}\n", "#569cd6")
            self.command_input.clear()
        except Exception as e:
            self.append_terminal(f"❌ {e}\n", "#f48771")
    
    def send_enter(self):
        """Envoie Enter"""
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(b'\n')
                self.serial.flush()
                self.tx_bytes += 1
                self.append_terminal("↵\n", "#cca700")
            except:
                pass
    
    def send_interrupt(self):
        """Envoie Ctrl-C"""
        if self.serial and self.serial.is_open:
            try:
                self.serial.write(b'\x03')
                self.serial.flush()
                self.tx_bytes += 1
                self.append_terminal("^C\n", "#f48771")
            except:
                pass
    
    def on_data_received(self, text, timestamp):
        """Données reçues"""
        self.rx_bytes += len(text)
        self.append_terminal(text, "#d4d4d4")
        
        # Traitement avec core
        if self.context_detector and self.module_manager:
            for line in text.split('\n'):
                if not line.strip():
                    continue
                
                # Détection contexte
                if self.context_detector.update(line):
                    context = self.context_detector.get_context()
                    self.update_context(context)
                    
                    # Activer modules pour ce contexte
                    self.activate_modules_for_context(context.type.value)
                
                # Traiter avec modules
                result = self.module_manager.process_line(
                    line,
                    self.context_detector.current_context.type.value
                )
                
                if result:
                    if result['hardware']:
                        self.update_hardware(result['hardware'])
    
    def activate_modules_for_context(self, context_type: str):
        """Active les modules pour un contexte"""
        # Mapping contexte → modules
        context_modules = {
            'uboot_spl': ['uboot_module'],
            'uboot_main': ['uboot_module'],
            'linux_kernel': ['linux_module'],
            'linux_init': ['linux_module'],
            'linux_shell': ['linux_module'],
            'atf_bl1': ['atf_module'],
            'atf_bl2': ['atf_module'],
            'atf_bl31': ['atf_module'],
        }
        
        modules = context_modules.get(context_type, [])
        
        # Désactiver tous puis activer ceux du contexte
        for mod in self.module_manager.get_active_modules():
            self.module_manager.deactivate_module(mod)
        
        for mod in modules:
            self.module_manager.activate_module(mod)
        
        # Update UI
        self.module_panel.update_modules(self.module_manager.get_active_modules())
        
        # Update suggestions
        suggestions = self.module_manager.get_suggestions(context_type)
        self.suggestions_panel.update_suggestions(suggestions)
    
    def update_context(self, context):
        """Met à jour le contexte"""
        ctx_type = context.type.value.replace('_', ' ').title()
        
        text = f"{ctx_type}"
        if context.prompt:
            text += f"\nPrompt: {context.prompt}"
        if context.version:
            text += f"\nVersion: {context.version}"
        
        self.context_text.setText(text)
        
        # Timeline
        ts = time.strftime('%H:%M:%S')
        self.timeline_list.insertItem(0, f"{ts} - {ctx_type}")
    
    def update_hardware(self, hardware: dict):
        """Met à jour hardware"""
        lines = []
        for key, value in hardware.items():
            lines.append(f"{key}: {value}")
        
        if lines:
            self.hardware_text.setText('\n'.join(lines[:6]))
    
    def append_terminal(self, text, color="#d4d4d4"):
        """Ajoute au terminal"""
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        
        cursor.insertText(text, fmt)
        self.terminal.setTextCursor(cursor)
        self.terminal.ensureCursorVisible()
    
    def update_status_bar(self):
        """Met à jour status bar"""
        if self.context_detector:
            ctx = self.context_detector.current_context.type.value
            self.status_context.setText(f"Context: {ctx}")
        
        if self.serial and self.serial.is_open:
            self.status_port.setText(f"Port: {self.serial.port}")
        else:
            self.status_port.setText("Port: —")
        
        if self.start_time:
            uptime = int(time.time() - self.start_time)
            h = uptime // 3600
            m = (uptime % 3600) // 60
            s = uptime % 60
            self.status_uptime.setText(f"Uptime: {h:02d}:{m:02d}:{s:02d}")
        
        rx_k = self.rx_bytes / 1024
        tx_k = self.tx_bytes / 1024
        self.status_stats.setText(f"RX: {rx_k:.1f}K | TX: {tx_k:.1f}K")
    
    def on_sidebar_clicked(self, name):
        """Clic sidebar"""
        print(f"Sidebar: {name}")
    
    def on_suggestion_selected(self, cmd):
        """Suggestion sélectionnée"""
        self.command_input.setText(cmd)
        self.command_input.setFocus()
    
    def closeEvent(self, event):
        """Fermeture"""
        self.disconnect()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 13))
    
    window = PiDebuggerV51()
    window.show()
    window.refresh_ports()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

"""
view/login_dialog.py
Tela de autenticação (login) simples e funcional (sem dependências externas).
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt


class LoginDialog(QDialog):
    """
    Diálogo de login simples.
    Credenciais fixas: admin / admin
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acesso ao Sistema - C213")
        self.setModal(True)
        self.setFixedSize(400, 180)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Título
        title = QLabel("🔐 Autenticação Necessária")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Campos de entrada
        form_layout = QVBoxLayout()

        self.edit_user = QLineEdit()
        self.edit_user.setPlaceholderText("Usuário")

        self.edit_pass = QLineEdit()
        self.edit_pass.setPlaceholderText("Senha")
        self.edit_pass.setEchoMode(QLineEdit.Password)

        form_layout.addWidget(self.edit_user)
        form_layout.addWidget(self.edit_pass)
        layout.addLayout(form_layout)

        # Botões
        btn_layout = QHBoxLayout()

        self.btn_login = QPushButton("Entrar")
        self.btn_login.clicked.connect(self._on_login)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def _on_login(self):
        user_input = self.edit_user.text().strip()
        password_input = self.edit_pass.text().strip()

        # Verifica campos vazios
        if not user_input or not password_input:
            QMessageBox.warning(self, "Campos vazios", "Preencha usuário e senha.")
            return

        # 🔥 LOGIN SIMPLES (SEM ENV, SEM BANCO)
        if user_input == "admin" and password_input == "admin":
            self.accept()
        else:
            QMessageBox.critical(self, "Acesso negado", "Usuário ou senha incorretos.")
            self.edit_pass.clear()
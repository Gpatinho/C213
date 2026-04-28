"""
Projeto C213 - Identificação de Sistemas e Controle PID
Grupo 2: Ziegler-Nichols + ITAE
"""

import sys
from PyQt5.QtWidgets import QApplication
from view.main_window import MainWindow
from controller.app_controller import AppController


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("C213 - Controle PID | Grupo 2")

    controller = AppController()
    window = MainWindow(controller)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
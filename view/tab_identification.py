"""
view/tab_identification.py
Aba de Identificação de Sistemas.
"""

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QFileDialog, QGridLayout, QLineEdit,
    QSizePolicy, QMessageBox
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg


class TabIdentification(QWidget):
    """
    Aba 1: Carrega dataset .mat, exibe dados e executa identificação de Smith.
    """

    def __init__(self, controller, main_window):
        super().__init__()
        self.controller  = controller
        self.main_window = main_window
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Painel esquerdo — controles
        left = self._build_left_panel()
        layout.addWidget(left, stretch=1)

        # Painel direito — gráfico
        right = self._build_right_panel()
        layout.addWidget(right, stretch=3)

    def _build_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(12)

        # ── Carregamento ──────────────────────────────────────
        grp_load = QGroupBox("Dataset")
        g_layout = QVBoxLayout(grp_load)

        self.lbl_file = QLabel("Nenhum arquivo carregado.")
        self.lbl_file.setWordWrap(True)
        self.lbl_file.setStyleSheet("color: #a6adc8; font-size: 11px;")

        btn_load = QPushButton("📂  Carregar .mat")
        btn_load.clicked.connect(self._on_load)

        g_layout.addWidget(btn_load)
        g_layout.addWidget(self.lbl_file)
        layout.addWidget(grp_load)

        # ── Resumo dos dados ──────────────────────────────────
        grp_info = QGroupBox("Informações do Dataset")
        g_info = QGridLayout(grp_info)
        g_info.setSpacing(6)

        labels = ["Amostras:", "t inicial (s):", "t final (s):", "y mín:", "y máx:", "Degrau:"]
        self._info_fields = {}
        for i, lbl in enumerate(labels):
            key = lbl.replace(":", "").strip()
            g_info.addWidget(QLabel(lbl), i, 0)
            field = QLineEdit("—")
            field.setReadOnly(True)
            field.setStyleSheet("background-color: #11111b; color: #a6adc8;")
            g_info.addWidget(field, i, 1)
            self._info_fields[key] = field

        layout.addWidget(grp_info)

        # ── Identificação ─────────────────────────────────────
        grp_id = QGroupBox("Método de Smith")
        g_id = QVBoxLayout(grp_id)

        self.btn_identify = QPushButton("🔍  Identificar")
        self.btn_identify.setEnabled(False)
        self.btn_identify.clicked.connect(self._on_identify)

        g_id.addWidget(self.btn_identify)

        # Campos de resultado
        params = [("K (ganho):", "K"), ("τ (tau, s):", "tau"), ("θ (theta, s):", "theta"), ("EQM:", "eqm")]
        self._param_fields = {}
        param_grid = QGridLayout()
        for i, (lbl, key) in enumerate(params):
            param_grid.addWidget(QLabel(lbl), i, 0)
            field = QLineEdit("—")
            field.setReadOnly(True)
            field.setStyleSheet("background-color: #11111b; color: #a6e3a1; font-weight: bold;")
            param_grid.addWidget(field, i, 1)
            self._param_fields[key] = field

        g_id.addLayout(param_grid)
        layout.addWidget(grp_id)

        # ── Exportar ──────────────────────────────────────────
        self.btn_export = QPushButton("💾  Exportar Gráfico")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._on_export)
        layout.addWidget(self.btn_export)

        layout.addStretch()
        return panel

    def _build_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Configura estilo do PyQtGraph
        pg.setConfigOption("background", "#11111b")
        pg.setConfigOption("foreground", "#cdd6f4")

        self.plot_widget = pg.PlotWidget(title="Resposta ao Degrau — Malha Aberta")
        self.plot_widget.setLabel("left", "Saída y(t)")
        self.plot_widget.setLabel("bottom", "Tempo (s)")
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(self.plot_widget)
        return panel

    # ── Slots (callbacks) ─────────────────────────────────────

    def _on_load(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Dataset", "", "MATLAB Files (*.mat)"
        )
        if not filepath:
            return

        try:
            summary = self.controller.load_dataset(filepath)
            self._update_info(summary, filepath)
            self._plot_raw_data()
            self.btn_identify.setEnabled(True)
            self.main_window.set_status(f"Dataset carregado: {filepath.split('/')[-1]}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar", str(e))

    def _on_identify(self):
        try:
            model = self.controller.run_identification()
            self._update_params(model)

            # Plota a curva do modelo sobreposta aos dados reais
            t_model, y_model = self.controller.get_model_curve()
            self.plot_widget.plot(
                t_model, y_model,
                pen=pg.mkPen("#f38ba8", width=2, style=Qt.DashLine),
                name="Modelo FOPDT (Smith)",
            )

            self.btn_export.setEnabled(True)
            self.main_window.unlock_pid_tab()

        except Exception as e:
            QMessageBox.critical(self, "Erro na Identificação", str(e))

    def _on_export(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Gráfico", "identificacao.png", "PNG (*.png)"
        )
        if filepath:
            exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
            exporter.export(filepath)
            self.main_window.set_status(f"Gráfico exportado: {filepath}")

    # ── Helpers de UI ─────────────────────────────────────────

    def _plot_raw_data(self):
        self.plot_widget.clear()
        t = self.controller.time_data
        y = self.controller.output_data
        self.plot_widget.plot(t, y, pen=pg.mkPen("#89b4fa", width=2), name="Dados Reais")

    def _update_info(self, summary: dict, filepath: str):
        self.lbl_file.setText(filepath.split("/")[-1])
        mapping = {
            "Amostras": str(summary.get("n_amostras", "—")),
            "t inicial (s)": f"{summary.get('t_inicial', 0):.3f}",
            "t final (s)": f"{summary.get('t_final', 0):.3f}",
            "y mín": f"{summary.get('y_min', 0):.4f}",
            "y máx": f"{summary.get('y_max', 0):.4f}",
            "Degrau": f"{summary.get('amplitude_degrau', 1):.4f}",
        }
        for key, val in mapping.items():
            if key in self._info_fields:
                self._info_fields[key].setText(val)

    def _update_params(self, model):
        self._param_fields["K"].setText(f"{model.K:.4f}")
        self._param_fields["tau"].setText(f"{model.tau:.4f}")
        self._param_fields["theta"].setText(f"{model.theta:.4f}")
        self._param_fields["eqm"].setText(f"{model.eqm:.6f}")
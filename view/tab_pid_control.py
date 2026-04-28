"""
view/tab_pid_control.py
Aba de Controle PID — sintonia, simulação e métricas de desempenho.
"""

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QGridLayout, QLineEdit,
    QComboBox, QDoubleSpinBox, QSizePolicy,
    QMessageBox, QFileDialog, QRadioButton, QButtonGroup,
    QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg

from model.pid_tuning import TuningMethod


class TabPIDControl(QWidget):
    """
    Aba 2: Sintonia do controlador PID e visualização em malha fechada.

    Permite:
    - Selecionar método automático (Ziegler-Nichols ou ITAE)
    - Inserir parâmetros manualmente
    - Definir SetPoint com entrada do tipo degrau
    - Visualizar resposta em malha fechada no gráfico
    - Exibir métricas: tr, ts, Mp, ess
    - Exportar o gráfico como imagem
    """

    def __init__(self, controller, main_window):
        super().__init__()
        self.controller  = controller
        self.main_window = main_window

        # Curvas atualmente plotadas (para limpar seletivamente)
        self._curve_sp   = None   # linha do setpoint
        self._curve_cl   = None   # curva de malha fechada atual
        self._markers    = []     # marcadores de pontos (tr, ts, pico)

        self._build_ui()

    # ══════════════════════════════════════════════════════════════
    #  CONSTRUÇÃO DA INTERFACE
    # ══════════════════════════════════════════════════════════════

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        layout.addWidget(self._build_left_panel(), stretch=1)
        layout.addWidget(self._build_right_panel(), stretch=3)

    # ── Painel esquerdo ───────────────────────────────────────────

    def _build_left_panel(self):
        panel = QWidget()
        vlay  = QVBoxLayout(panel)
        vlay.setSpacing(12)

        vlay.addWidget(self._build_model_info())
        vlay.addWidget(self._build_tuning_group())
        vlay.addWidget(self._build_setpoint_group())
        vlay.addWidget(self._build_metrics_group())
        vlay.addWidget(self._build_action_buttons())
        vlay.addStretch()
        return panel

    def _build_model_info(self):
        """Exibe os parâmetros FOPDT identificados (somente leitura)."""
        grp    = QGroupBox("Modelo Identificado (FOPDT)")
        g      = QGridLayout(grp)
        g.setSpacing(6)

        params = [("K (ganho):", "K"), ("τ (s):", "tau"), ("θ (s):", "theta"), ("EQM:", "eqm")]
        self._model_fields = {}
        for i, (lbl, key) in enumerate(params):
            g.addWidget(QLabel(lbl), i, 0)
            f = QLineEdit("—")
            f.setReadOnly(True)
            f.setStyleSheet("background-color:#11111b; color:#a6e3a1; font-weight:bold;")
            g.addWidget(f, i, 1)
            self._model_fields[key] = f

        return grp

    def _build_tuning_group(self):
        """Grupo com seleção de método e campos Kp/Ti/Td."""
        grp  = QGroupBox("Sintonia do Controlador PID")
        vlay = QVBoxLayout(grp)
        vlay.setSpacing(8)

        # ── Seleção de modo ───────────────────────────────────────
        mode_row = QHBoxLayout()
        self._rb_method = QRadioButton("Método")
        self._rb_manual = QRadioButton("Manual")
        self._rb_method.setChecked(True)
        self._rb_method.toggled.connect(self._on_mode_changed)

        btn_group = QButtonGroup(self)
        btn_group.addButton(self._rb_method)
        btn_group.addButton(self._rb_manual)

        mode_row.addWidget(self._rb_method)
        mode_row.addWidget(self._rb_manual)
        mode_row.addStretch()
        vlay.addLayout(mode_row)

        # ── Seleção de método ─────────────────────────────────────
        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Método:"))
        self._combo_method = QComboBox()
        self._combo_method.addItem("Ziegler-Nichols", TuningMethod.ZIEGLER_NICHOLS)
        self._combo_method.addItem("ITAE",            TuningMethod.ITAE)
        self._combo_method.currentIndexChanged.connect(self._on_method_changed)
        method_row.addWidget(self._combo_method)
        vlay.addLayout(method_row)

        # ── Linha separadora ──────────────────────────────────────
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #313244;")
        vlay.addWidget(line)

        # ── Campos Kp / Ti / Td ───────────────────────────────────
        pid_grid = QGridLayout()
        pid_grid.setSpacing(6)

        pid_labels = [("Kp:", "Kp"), ("Ti (s):", "Ti"), ("Td (s):", "Td")]
        self._pid_fields = {}
        for i, (lbl, key) in enumerate(pid_labels):
            pid_grid.addWidget(QLabel(lbl), i, 0)
            spin = QDoubleSpinBox()
            spin.setDecimals(4)
            spin.setRange(0.0, 9999.0)
            spin.setSingleStep(0.1)
            spin.setValue(0.0)
            pid_grid.addWidget(spin, i, 1)
            self._pid_fields[key] = spin

        # Botão limpar (modo manual)
        self._btn_clear = QPushButton("✕ Limpar")
        self._btn_clear.setStyleSheet(
            "background-color:#313244; color:#cdd6f4; font-size:11px; padding:4px 10px;"
        )
        self._btn_clear.clicked.connect(self._on_clear_pid)
        pid_grid.addWidget(self._btn_clear, 3, 1)

        vlay.addLayout(pid_grid)
        self._set_manual_mode(False)  # começa no modo automático

        return grp

    def _build_setpoint_group(self):
        """Campo de setpoint e comparação entre métodos."""
        grp  = QGroupBox("Controle — SetPoint")
        g    = QGridLayout(grp)
        g.setSpacing(6)

        g.addWidget(QLabel("SetPoint:"), 0, 0)
        self._spin_sp = QDoubleSpinBox()
        self._spin_sp.setDecimals(2)
        self._spin_sp.setRange(-9999.0, 9999.0)
        self._spin_sp.setValue(1.0)
        g.addWidget(self._spin_sp, 0, 1)

        g.addWidget(QLabel("t final (s):"), 1, 0)
        self._spin_tend = QDoubleSpinBox()
        self._spin_tend.setDecimals(1)
        self._spin_tend.setRange(10.0, 9999.0)
        self._spin_tend.setValue(300.0)
        g.addWidget(self._spin_tend, 1, 1)

        return grp

    def _build_metrics_group(self):
        """Painel de métricas de resposta (tr, ts, Mp, ess)."""
        grp  = QGroupBox("Métricas de Resposta")
        g    = QGridLayout(grp)
        g.setSpacing(6)

        metrics = [
            ("tr (subida, s):",   "tr"),
            ("ts (acomod., s):",  "ts"),
            ("Mp (sobressinal):", "Mp"),
            ("ess (erro regime):", "ess"),
            ("Pico:",              "peak"),
        ]
        self._metric_fields = {}
        for i, (lbl, key) in enumerate(metrics):
            g.addWidget(QLabel(lbl), i, 0)
            f = QLineEdit("—")
            f.setReadOnly(True)
            f.setStyleSheet("background-color:#11111b; color:#89dceb; font-weight:bold;")
            g.addWidget(f, i, 1)
            self._metric_fields[key] = f

        return grp

    def _build_action_buttons(self):
        """Botões Sintonizar e Exportar."""
        w    = QWidget()
        vlay = QVBoxLayout(w)
        vlay.setSpacing(8)
        vlay.setContentsMargins(0, 0, 0, 0)

        self._btn_tune = QPushButton("⚙️  Sintonizar")
        self._btn_tune.clicked.connect(self._on_tune)

        self._btn_export = QPushButton("💾  Exportar Gráfico")
        self._btn_export.setEnabled(False)
        self._btn_export.setStyleSheet(
            "background-color:#313244; color:#cdd6f4;"
        )
        self._btn_export.clicked.connect(self._on_export)

        vlay.addWidget(self._btn_tune)
        vlay.addWidget(self._btn_export)
        return w

    # ── Painel direito (gráfico) ──────────────────────────────────

    def _build_right_panel(self):
        panel = QWidget()
        vlay  = QVBoxLayout(panel)

        self._plot = pg.PlotWidget(title="Resposta ao Degrau — Malha Fechada")
        self._plot.setLabel("left",   "Saída y(t)")
        self._plot.setLabel("bottom", "Tempo (s)")
        self._plot.addLegend()
        self._plot.showGrid(x=True, y=True, alpha=0.2)
        self._plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        vlay.addWidget(self._plot)
        return panel

    # ══════════════════════════════════════════════════════════════
    #  SLOTS (CALLBACKS)
    # ══════════════════════════════════════════════════════════════

    def _on_mode_changed(self):
        manual = self._rb_manual.isChecked()
        self._set_manual_mode(manual)

    def _on_method_changed(self):
        """Ao trocar método, limpa os campos para evitar confusão."""
        if self._rb_method.isChecked():
            for f in self._pid_fields.values():
                f.setValue(0.0)

    def _on_clear_pid(self):
        for f in self._pid_fields.values():
            f.setValue(0.0)

    def _on_tune(self):
        """Executa a sintonia e a simulação em malha fechada."""
        try:
            # ── 1. Sintonia ───────────────────────────────────────
            if self._rb_manual.isChecked():
                pid = self.controller.tune_pid(
                    method=TuningMethod.MANUAL,
                    Kp_manual=self._pid_fields["Kp"].value(),
                    Ti_manual=self._pid_fields["Ti"].value(),
                    Td_manual=self._pid_fields["Td"].value(),
                )
            else:
                method = self._combo_method.currentData()
                pid    = self.controller.tune_pid(method=method)
                # Mostra os parâmetros calculados
                self._pid_fields["Kp"].setValue(pid.Kp)
                self._pid_fields["Ti"].setValue(pid.Ti)
                self._pid_fields["Td"].setValue(pid.Td)

            # ── 2. Simulação ──────────────────────────────────────
            sp    = self._spin_sp.value()
            t_end = self._spin_tend.value()
            time, output, metrics = self.controller.simulate_closed_loop(
                setpoint=sp, t_end=t_end
            )

            # ── 3. Atualiza gráfico e métricas ────────────────────
            self._plot_response(time, output, sp, metrics, pid.method)
            self._update_metrics(metrics)

            self._btn_export.setEnabled(True)
            self._btn_export.setStyleSheet("")   # restaura estilo padrão

            self.main_window.set_status(
                f"✅ [{pid.method}] Kp={pid.Kp:.4f}  Ti={pid.Ti:.4f}  Td={pid.Td:.4f}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro na Sintonia", str(e))

    def _on_export(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Gráfico", "controle_pid.png", "PNG (*.png)"
        )
        if filepath:
            exporter = pg.exporters.ImageExporter(self._plot.plotItem)
            exporter.export(filepath)
            self.main_window.set_status(f"Gráfico exportado: {filepath}")

    # ══════════════════════════════════════════════════════════════
    #  HELPERS DE UI
    # ══════════════════════════════════════════════════════════════

    def _set_manual_mode(self, manual: bool):
        """Habilita/desabilita campos conforme o modo selecionado."""
        self._combo_method.setEnabled(not manual)
        self._btn_clear.setVisible(manual)
        for f in self._pid_fields.values():
            f.setReadOnly(not manual)
            style = "" if manual else "background-color:#11111b; color:#a6e3a1;"
            f.setStyleSheet(style)

    def _plot_response(self, time, output, setpoint, metrics, method_name):
        """Plota a curva de malha fechada com linha de setpoint e marcadores."""
        self._plot.clear()
        self._markers.clear()

        colors = {
            "Ziegler-Nichols": "#f38ba8",
            "ITAE":            "#a6e3a1",
            "Manual":          "#89b4fa",
        }
        color = colors.get(method_name, "#cdd6f4")

        # Linha do setpoint
        sp_line = pg.InfiniteLine(
            pos=setpoint, angle=0,
            pen=pg.mkPen("#fab387", width=1, style=Qt.DashLine),
            label=f"SP={setpoint:.2f}",
            labelOpts={"color": "#fab387", "position": 0.05},
        )
        self._plot.addItem(sp_line)

        # Curva principal
        self._plot.plot(
            time, output,
            pen=pg.mkPen(color, width=2),
            name=f"Malha Fechada ({method_name})",
        )

        # Marcador de pico (se houver sobressinal)
        if metrics.overshoot > 0.5 and metrics.peak_time is not None:
            self._add_marker(
                metrics.peak_time, metrics.peak_value,
                f"Mp={metrics.overshoot:.1f}%",
                "#f38ba8",
            )

        # Marcador de tempo de subida
        if metrics.rise_time is not None:
            t90 = self._find_t90(time, output, setpoint)
            if t90 is not None:
                self._add_marker(
                    t90, 0.90 * setpoint,
                    f"tr={metrics.rise_time:.1f}s",
                    "#89dceb",
                )

        # Marcador de acomodação
        if metrics.settling_time is not None:
            y_at_ts = float(np.interp(metrics.settling_time, time, output))
            self._add_marker(
                metrics.settling_time, y_at_ts,
                f"ts={metrics.settling_time:.1f}s",
                "#a6e3a1",
            )

    def _add_marker(self, t, y, label, color):
        """Adiciona um ponto marcado no gráfico."""
        scatter = pg.ScatterPlotItem(
            x=[t], y=[y],
            symbol="o", size=10,
            pen=pg.mkPen(color, width=1.5),
            brush=pg.mkBrush(color + "88"),
        )
        text = pg.TextItem(label, color=color, anchor=(0, 1))
        text.setPos(t, y)
        self._plot.addItem(scatter)
        self._plot.addItem(text)
        self._markers.extend([scatter, text])

    def _find_t90(self, time, output, setpoint):
        """Encontra o instante em que a saída atinge 90% do setpoint."""
        level = 0.90 * setpoint
        idx   = np.where(output >= level)[0]
        if len(idx) == 0:
            return None
        i = int(idx[0])
        if i > 0:
            y0, y1 = float(output[i-1]), float(output[i])
            t0, t1 = float(time[i-1]),   float(time[i])
            if y1 != y0:
                return t0 + (level - y0) * (t1 - t0) / (y1 - y0)
        return float(time[i])

    def _update_metrics(self, metrics):
        """Atualiza os campos de métricas na interface."""
        tr  = f"{metrics.rise_time:.3f} s"    if metrics.rise_time    is not None else "—"
        ts  = f"{metrics.settling_time:.3f} s" if metrics.settling_time is not None else "—"
        Mp  = f"{metrics.overshoot:.2f} %"     if metrics.overshoot    is not None else "—"
        ess = f"{metrics.steady_state_error:.4f}"
        pk  = f"{metrics.peak_value:.4f}"

        self._metric_fields["tr"].setText(tr)
        self._metric_fields["ts"].setText(ts)
        self._metric_fields["Mp"].setText(Mp)
        self._metric_fields["ess"].setText(ess)
        self._metric_fields["peak"].setText(pk)

    def refresh_model_fields(self):
        """
        Chamado pela MainWindow quando a identificação é concluída.
        Popula os campos do modelo e define o setpoint inicial.
        """
        m = self.controller.fopdt_model
        if m is None:
            return

        self._model_fields["K"].setText(f"{m.K:.4f}")
        self._model_fields["tau"].setText(f"{m.tau:.4f}")
        self._model_fields["theta"].setText(f"{m.theta:.4f}")
        self._model_fields["eqm"].setText(f"{m.eqm:.6f}")

        # Setpoint inicial = valor final do processo (saída em regime)
        if self.controller.output_data is not None:
            sp = float(self.controller.output_data[-1])
            self._spin_sp.setValue(round(sp, 2))
"""
view/tab_pid_control.py
Aba de Controle PID — sintonia, simulação, comparação e métricas de desempenho.
"""

import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QGroupBox, QGridLayout, QLineEdit,
    QComboBox, QDoubleSpinBox, QSizePolicy,
    QMessageBox, QFileDialog, QRadioButton, QButtonGroup,
    QFrame, QScrollArea
)
from PyQt5.QtCore import Qt
import pyqtgraph as pg

from model.pid_tuning import TuningMethod


class TabPIDControl(QWidget):

    def __init__(self, controller, main_window):
        super().__init__()
        self.controller  = controller
        self.main_window = main_window
        self._markers    = []
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

    def _build_left_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        inner = QWidget()
        vlay  = QVBoxLayout(inner)
        vlay.setSpacing(12)
        vlay.setContentsMargins(4, 4, 8, 4)

        vlay.addWidget(self._build_model_info())
        vlay.addWidget(self._build_tuning_group())
        vlay.addWidget(self._build_setpoint_group())
        vlay.addWidget(self._build_metrics_group())
        vlay.addWidget(self._build_action_buttons())
        vlay.addStretch()

        scroll.setWidget(inner)
        return scroll

    def _build_model_info(self):
        grp = QGroupBox("Modelo Identificado (FOPDT)")
        g   = QGridLayout(grp)
        g.setSpacing(6)

        self._model_fields = {}
        for i, (lbl, key) in enumerate([
            ("K (ganho):", "K"), ("τ (s):", "tau"),
            ("θ (s):", "theta"), ("EQM:", "eqm")
        ]):
            g.addWidget(QLabel(lbl), i, 0)
            f = QLineEdit("—")
            f.setReadOnly(True)
            f.setStyleSheet("background:#11111b; color:#a6e3a1; font-weight:bold;")
            g.addWidget(f, i, 1)
            self._model_fields[key] = f
        return grp

    def _build_tuning_group(self):
        grp  = QGroupBox("Sintonia do Controlador PID")
        vlay = QVBoxLayout(grp)
        vlay.setSpacing(8)

        # Modo: Método ou Manual
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

        # ComboBox de método
        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Método:"))
        self._combo_method = QComboBox()
        self._combo_method.addItem("Ziegler-Nichols", TuningMethod.ZIEGLER_NICHOLS)
        self._combo_method.addItem("ITAE",            TuningMethod.ITAE)
        self._combo_method.currentIndexChanged.connect(self._on_method_changed)
        method_row.addWidget(self._combo_method)
        vlay.addLayout(method_row)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color:#313244;")
        vlay.addWidget(line)

        # Campos Kp / Ti / Td
        pid_grid = QGridLayout()
        pid_grid.setSpacing(6)
        self._pid_fields = {}
        for i, (lbl, key) in enumerate([("Kp:", "Kp"), ("Ti (s):", "Ti"), ("Td (s):", "Td")]):
            pid_grid.addWidget(QLabel(lbl), i, 0)
            spin = QDoubleSpinBox()
            spin.setDecimals(4)
            spin.setRange(0.0, 9999.0)
            spin.setSingleStep(0.1)
            spin.setValue(0.0)
            pid_grid.addWidget(spin, i, 1)
            self._pid_fields[key] = spin

        self._btn_clear = QPushButton("✕ Limpar")
        self._btn_clear.setStyleSheet(
            "background-color:#313244; color:#cdd6f4; font-size:11px; padding:4px 10px;"
        )
        self._btn_clear.clicked.connect(self._on_clear_pid)
        pid_grid.addWidget(self._btn_clear, 3, 1)
        vlay.addLayout(pid_grid)

        self._set_manual_mode(False)
        return grp

    def _build_setpoint_group(self):
        grp = QGroupBox("Controle — SetPoint")
        g   = QGridLayout(grp)
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
        """
        Painel de métricas com duas colunas: ZN e ITAE lado a lado
        para facilitar a comparação.
        """
        grp = QGroupBox("Métricas de Resposta")
        g   = QGridLayout(grp)
        g.setSpacing(5)

        # Cabeçalhos
        g.addWidget(QLabel(""), 0, 0)
        lbl_zn = QLabel("ZN")
        lbl_zn.setAlignment(Qt.AlignCenter)
        lbl_zn.setStyleSheet("color:#f38ba8; font-weight:bold;")
        g.addWidget(lbl_zn, 0, 1)

        lbl_it = QLabel("ITAE")
        lbl_it.setAlignment(Qt.AlignCenter)
        lbl_it.setStyleSheet("color:#a6e3a1; font-weight:bold;")
        g.addWidget(lbl_it, 0, 2)

        rows = [
            ("tr (s):",  "tr"),
            ("ts (s):",  "ts"),
            ("Mp (%):",  "Mp"),
            ("ess:",     "ess"),
            ("Pico:",    "peak"),
        ]
        self._metric_fields = {"ZN": {}, "ITAE": {}}
        for i, (lbl, key) in enumerate(rows, start=1):
            g.addWidget(QLabel(lbl), i, 0)
            for col, method in enumerate(["ZN", "ITAE"], start=1):
                color = "#f38ba8" if method == "ZN" else "#a6e3a1"
                f = QLineEdit("—")
                f.setReadOnly(True)
                f.setStyleSheet(
                    f"background:#11111b; color:{color}; font-weight:bold; font-size:11px;"
                )
                g.addWidget(f, i, col)
                self._metric_fields[method][key] = f

        return grp

    def _build_action_buttons(self):
        w    = QWidget()
        vlay = QVBoxLayout(w)
        vlay.setSpacing(8)
        vlay.setContentsMargins(0, 0, 0, 0)

        # Sintonizar método individual
        self._btn_tune = QPushButton("⚙️  Sintonizar")
        self._btn_tune.clicked.connect(self._on_tune)

        # Comparar ZN vs ITAE no mesmo gráfico
        self._btn_compare = QPushButton("📊  Comparar ZN vs ITAE")
        self._btn_compare.setStyleSheet(
            "background-color:#cba6f7; color:#1e1e2e;"
        )
        self._btn_compare.clicked.connect(self._on_compare)

        # Exportar
        self._btn_export = QPushButton("💾  Exportar Gráfico")
        self._btn_export.setEnabled(False)
        self._btn_export.setStyleSheet("background-color:#313244; color:#cdd6f4;")
        self._btn_export.clicked.connect(self._on_export)

        vlay.addWidget(self._btn_tune)
        vlay.addWidget(self._btn_compare)
        vlay.addWidget(self._btn_export)
        return w

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
    #  SLOTS
    # ══════════════════════════════════════════════════════════════

    def _on_mode_changed(self):
        self._set_manual_mode(self._rb_manual.isChecked())

    def _on_method_changed(self):
        if self._rb_method.isChecked():
            for f in self._pid_fields.values():
                f.setValue(0.0)

    def _on_clear_pid(self):
        for f in self._pid_fields.values():
            f.setValue(0.0)

    def _on_tune(self):
        """Sintoniza e plota um único método."""
        try:
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
                self._pid_fields["Kp"].setValue(pid.Kp)
                self._pid_fields["Ti"].setValue(pid.Ti)
                self._pid_fields["Td"].setValue(pid.Td)

            sp    = self._spin_sp.value()
            t_end = self._spin_tend.value()
            time, output, metrics = self.controller.simulate_closed_loop(
                setpoint=sp, t_end=t_end
            )

            self._plot.clear()
            self._markers.clear()
            self._add_setpoint_line(sp)
            self._plot_curve(time, output, pid.method, metrics)

            # Preenche métricas na coluna correta
            col = "ZN" if pid.method == "Ziegler-Nichols" else (
                  "ITAE" if pid.method == "ITAE" else None)
            if col:
                self._fill_metrics(col, metrics)

            self._btn_export.setEnabled(True)
            self._btn_export.setStyleSheet("")
            self.main_window.set_status(
                f"✅ [{pid.method}]  Kp={pid.Kp:.4f}  Ti={pid.Ti:.4f}  Td={pid.Td:.4f}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Erro na Sintonia", str(e))

    def _on_compare(self):
        """Plota ZN e ITAE no mesmo gráfico e preenche as duas colunas de métricas."""
        try:
            sp    = self._spin_sp.value()
            t_end = self._spin_tend.value()

            self._plot.clear()
            self._markers.clear()
            self._add_setpoint_line(sp)

            for method, col in [
                (TuningMethod.ZIEGLER_NICHOLS, "ZN"),
                (TuningMethod.ITAE,            "ITAE"),
            ]:
                pid = self.controller.tune_pid(method=method)
                time, output, metrics = self.controller.simulate_closed_loop(
                    setpoint=sp, t_end=t_end
                )
                self._plot_curve(time, output, pid.method, metrics)
                self._fill_metrics(col, metrics)

            self._plot.setTitle("Comparação ZN vs ITAE — Malha Fechada")
            self._btn_export.setEnabled(True)
            self._btn_export.setStyleSheet("")
            self.main_window.set_status("📊 Comparação ZN vs ITAE gerada com sucesso!")

        except Exception as e:
            QMessageBox.critical(self, "Erro na Comparação", str(e))

    def _on_export(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Gráfico", "controle_pid.png", "PNG (*.png)"
        )
        if filepath:
            exporter = pg.exporters.ImageExporter(self._plot.plotItem)
            exporter.export(filepath)
            self.main_window.set_status(f"Gráfico exportado: {filepath}")

    # ══════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════

    def _set_manual_mode(self, manual: bool):
        self._combo_method.setEnabled(not manual)
        self._btn_clear.setVisible(manual)
        for f in self._pid_fields.values():
            f.setReadOnly(not manual)
            f.setStyleSheet("" if manual else "background:#11111b; color:#a6e3a1;")

    def _add_setpoint_line(self, sp):
        line = pg.InfiniteLine(
            pos=sp, angle=0,
            pen=pg.mkPen("#fab387", width=1, style=Qt.DashLine),
            label=f"SP={sp:.2f}",
            labelOpts={"color": "#fab387", "position": 0.05},
        )
        self._plot.addItem(line)

    def _plot_curve(self, time, output, method_name, metrics):
        """Plota uma curva de resposta com seus marcadores."""
        colors = {
            "Ziegler-Nichols": "#f38ba8",
            "ITAE":            "#a6e3a1",
            "Manual":          "#89b4fa",
        }
        color = colors.get(method_name, "#cdd6f4")

        self._plot.plot(
            time, output,
            pen=pg.mkPen(color, width=2),
            name=method_name,
        )

        # Marcador de pico
        if metrics.overshoot > 0.5 and metrics.peak_time is not None:
            self._add_marker(
                metrics.peak_time, metrics.peak_value,
                f"Mp={metrics.overshoot:.1f}%", color,
            )

        # Marcador de tr (ponto de 90%)
        if metrics.rise_time is not None:
            t90 = self._find_crossing(time, output, 0.90 * self._spin_sp.value())
            if t90 is not None:
                self._add_marker(
                    t90, 0.90 * self._spin_sp.value(),
                    f"tr={metrics.rise_time:.1f}s", color,
                )

        # Marcador de ts
        if metrics.settling_time is not None:
            y_ts = float(np.interp(metrics.settling_time, time, output))
            self._add_marker(
                metrics.settling_time, y_ts,
                f"ts={metrics.settling_time:.1f}s", color,
            )

    def _add_marker(self, t, y, label, color):
        scatter = pg.ScatterPlotItem(
            x=[t], y=[y], symbol="o", size=10,
            pen=pg.mkPen(color, width=1.5),
            brush=pg.mkBrush(color + "88"),
        )
        text = pg.TextItem(label, color=color, anchor=(0, 1))
        text.setPos(t, y)
        self._plot.addItem(scatter)
        self._plot.addItem(text)
        self._markers.extend([scatter, text])

    def _find_crossing(self, time, output, level):
        idx = np.where(output >= level)[0]
        if len(idx) == 0:
            return None
        i = int(idx[0])
        if i > 0:
            y0, y1 = float(output[i-1]), float(output[i])
            t0, t1 = float(time[i-1]),   float(time[i])
            if y1 != y0:
                return t0 + (level - y0) * (t1 - t0) / (y1 - y0)
        return float(time[i])

    def _fill_metrics(self, col: str, metrics):
        """Preenche a coluna ZN ou ITAE no painel de métricas."""
        f = self._metric_fields[col]
        f["tr"].setText(f"{metrics.rise_time:.2f} s"      if metrics.rise_time    is not None else "—")
        f["ts"].setText(f"{metrics.settling_time:.2f} s"  if metrics.settling_time is not None else "—")
        f["Mp"].setText(f"{metrics.overshoot:.2f} %"      if metrics.overshoot    is not None else "—")
        f["ess"].setText(f"{metrics.steady_state_error:.4f}")
        f["peak"].setText(f"{metrics.peak_value:.4f}")

    def refresh_model_fields(self):
        m = self.controller.fopdt_model
        if m is None:
            return
        self._model_fields["K"].setText(f"{m.K:.4f}")
        self._model_fields["tau"].setText(f"{m.tau:.4f}")
        self._model_fields["theta"].setText(f"{m.theta:.4f}")
        self._model_fields["eqm"].setText(f"{m.eqm:.6f}")

        if self.controller.output_data is not None:
            sp = float(self.controller.output_data[-1])
            self._spin_sp.setValue(round(sp, 2))
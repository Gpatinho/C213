"""
controller/app_controller.py
Controlador principal da aplicação (camada C do MVC).
"""

import numpy as np
from model.data_loader import DataLoader
from model.identification import SmithIdentification, SundaresanIdentification, FOPDTModel
from model.pid_tuning import PIDTuner, PIDParameters, TuningMethod
from model.simulator import ClosedLoopSimulator, ResponseMetrics


class AppController:
    """
    Orquestra o fluxo completo:
    1. Carregamento de dados
    2. Identificação (Smith e Sundaresan)
    3. Sintonia PID
    4. Simulação em malha fechada
    """

    def __init__(self):
        self._loader    = DataLoader()
        self._smith     = SmithIdentification()
        self._sundar    = SundaresanIdentification()
        self._tuner     = PIDTuner()
        self._simulator = ClosedLoopSimulator()

        # Modelos identificados (ambos os métodos)
        self.model_smith:    FOPDTModel = None
        self.model_sundar:   FOPDTModel = None
        self.fopdt_model:    FOPDTModel = None   # modelo ativo (escolhido pelo usuário)

        self.pid_params:     PIDParameters  = None
        self.last_metrics:   ResponseMetrics = None

        self.time_data   = None
        self.output_data = None
        self.input_data  = None

    # ── ABA 1: IDENTIFICAÇÃO ──────────────────────────────────────────────

    def load_dataset(self, filepath: str) -> dict:
        self._loader.load(filepath)
        self.time_data   = self._loader.time
        self.output_data = self._loader.output_signal
        self.input_data  = self._loader.input_signal
        return self._loader.summary()

    def run_identification(self) -> tuple:
        """
        Executa Smith e Sundaresan.
        Retorna (model_smith, model_sundaresan).
        Define automaticamente o modelo ativo como o de menor EQM.
        """
        if self.time_data is None:
            raise RuntimeError("Carregue um dataset antes de identificar.")

        step = self._loader.get_step_amplitude()

        self.model_smith  = self._smith.identify(self.time_data, self.output_data, step)
        self.model_sundar = self._sundar.identify(self.time_data, self.output_data, step)

        # Seleciona automaticamente o de menor EQM
        if self.model_smith.eqm <= self.model_sundar.eqm:
            self.fopdt_model = self.model_smith
        else:
            self.fopdt_model = self.model_sundar

        return self.model_smith, self.model_sundar

    def select_model(self, method: str):
        """Permite ao usuário escolher qual modelo usar ('Smith' ou 'Sundaresan')."""
        if method == "Smith":
            self.fopdt_model = self.model_smith
        elif method == "Sundaresan":
            self.fopdt_model = self.model_sundar
        else:
            raise ValueError(f"Método desconhecido: {method}")

    def get_model_curve(self, method: str = None):
        """Retorna (time, y_model) para o método especificado (ou o ativo)."""
        if method == "Smith":
            model = self.model_smith
        elif method == "Sundaresan":
            model = self.model_sundar
        else:
            model = self.fopdt_model

        if model is None:
            raise RuntimeError("Execute a identificação primeiro.")

        y0   = float(self.output_data[0])
        step = self._loader.get_step_amplitude()

        identifier = self._smith if model.method == "Smith" else self._sundar
        y_model = identifier.get_model_response(self.time_data, model, step, y0)
        return self.time_data, y_model

    # ── ABA 2: CONTROLE PID ───────────────────────────────────────────────

    def tune_pid(self, method: TuningMethod, Kp_manual=1.0, Ti_manual=1.0, Td_manual=0.0):
        if self.fopdt_model is None:
            raise RuntimeError("Execute a identificação antes de sintonizar o PID.")
        self.pid_params = self._tuner.tune(
            method=method,
            K=self.fopdt_model.K,
            tau=self.fopdt_model.tau,
            theta=self.fopdt_model.theta,
            Kp_manual=Kp_manual,
            Ti_manual=Ti_manual,
            Td_manual=Td_manual,
        )
        return self.pid_params

    def simulate_closed_loop(self, setpoint=1.0, t_end=None):
        if self.fopdt_model is None:
            raise RuntimeError("Execute a identificação primeiro.")
        if self.pid_params is None:
            raise RuntimeError("Sintonize o PID primeiro.")
        time, output = self._simulator.simulate(
            model=self.fopdt_model,
            pid=self.pid_params,
            setpoint=setpoint,
            t_end=t_end,
        )
        self.last_metrics = self._simulator.compute_metrics(time, output, setpoint)
        return time, output, self.last_metrics

    def get_available_methods(self):
        return self._tuner.available_methods()

    def is_dataset_loaded(self):
        return self._loader.is_loaded()

    def is_identified(self):
        return self.fopdt_model is not None

    def is_tuned(self):
        return self.pid_params is not None
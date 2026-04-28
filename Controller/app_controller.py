"""
controller/app_controller.py
Controlador principal da aplicação (camada C do MVC).

Liga a View (interface) com o Model (lógica de negócio),
sem que nenhum dos dois precise conhecer o outro diretamente.
"""

import numpy as np
from model.data_loader import DataLoader
from model.identification import SmithIdentification, FOPDTModel
from model.pid_tuning import PIDTuner, PIDParameters, TuningMethod
from model.simulator import ClosedLoopSimulator, ResponseMetrics


class AppController:
    """
    Responsável por orquestrar o fluxo da aplicação:
    1. Carregamento de dados
    2. Identificação do modelo FOPDT
    3. Sintonia do PID
    4. Simulação em malha fechada
    5. Entrega dos resultados à View
    """

    def __init__(self):
        # Camada Model
        self._loader     = DataLoader()
        self._smith      = SmithIdentification()
        self._tuner      = PIDTuner()
        self._simulator  = ClosedLoopSimulator()

        # Estado interno
        self.fopdt_model: FOPDTModel    = None
        self.pid_params:  PIDParameters = None
        self.last_metrics: ResponseMetrics = None

        # Dados brutos
        self.time_data   = None
        self.output_data = None
        self.input_data  = None

    # ──────────────────────────────────────────────────────────
    #  ABA 1 — IDENTIFICAÇÃO
    # ──────────────────────────────────────────────────────────

    def load_dataset(self, filepath: str) -> dict:
        """
        Carrega um arquivo .mat e retorna um resumo dos dados.
        Lança exceção em caso de falha.
        """
        self._loader.load(filepath)

        self.time_data   = self._loader.time
        self.output_data = self._loader.output_signal
        self.input_data  = self._loader.input_signal

        return self._loader.summary()

    def run_identification(self) -> FOPDTModel:
        """
        Executa a identificação pelo Método de Smith.
        Requer que um dataset tenha sido carregado antes.
        """
        if self.time_data is None or self.output_data is None:
            raise RuntimeError("Carregue um dataset antes de identificar.")

        step_amp = self._loader.get_step_amplitude()
        self.fopdt_model = self._smith.identify(
            self.time_data, self.output_data, step_amp
        )
        return self.fopdt_model

    def get_model_curve(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Retorna (time, y_model) para plotar a curva do modelo identificado
        junto com os dados reais.
        """
        if self.fopdt_model is None:
            raise RuntimeError("Execute a identificação primeiro.")

        y0       = float(self.output_data[0])
        step_amp = self._loader.get_step_amplitude()
        y_model  = self._smith.get_model_response(
            self.time_data, self.fopdt_model, step_amp, y0
        )
        return self.time_data, y_model

    # ──────────────────────────────────────────────────────────
    #  ABA 2 — CONTROLE PID
    # ──────────────────────────────────────────────────────────

    def tune_pid(
        self,
        method: TuningMethod,
        Kp_manual: float = 1.0,
        Ti_manual: float = 1.0,
        Td_manual: float = 0.0,
    ) -> PIDParameters:
        """
        Sintoniza o controlador PID usando o método especificado.
        Requer identificação prévia.
        """
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

    def simulate_closed_loop(
        self,
        setpoint: float = 1.0,
        t_end: float = None,
    ) -> tuple[np.ndarray, np.ndarray, ResponseMetrics]:
        """
        Simula o sistema em malha fechada e retorna (time, output, metrics).
        Requer identificação e sintonia prévias.
        """
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

    def get_available_methods(self) -> list:
        """Retorna os métodos de sintonia disponíveis para o Grupo 2."""
        return self._tuner.available_methods()

    def is_dataset_loaded(self) -> bool:
        return self._loader.is_loaded()

    def is_identified(self) -> bool:
        return self.fopdt_model is not None

    def is_tuned(self) -> bool:
        return self.pid_params is not None
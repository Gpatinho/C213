"""
model/identification.py
Identificação do modelo FOPDT pelo Método de Smith.

Modelo FOPDT:
    G(s) = K * exp(-theta * s) / (tau * s + 1)
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class FOPDTModel:
    """Representa os parâmetros identificados do modelo FOPDT."""
    K: float
    tau: float
    theta: float
    eqm: float = 0.0

    def __str__(self):
        return (
            f"FOPDT → K={self.K:.4f}  τ={self.tau:.4f}s  θ={self.theta:.4f}s  "
            f"EQM={self.eqm:.6f}"
        )


class SmithIdentification:
    """
    Método de Smith para identificação de sistemas FOPDT
    """

    def identify(
        self,
        time: np.ndarray,
        output: np.ndarray,
        step_amplitude: float = 1.0,
    ) -> FOPDTModel:

        # 🔹 Valor inicial
        y0 = float(output[0])

        # 🔹 Valor em regime (média dos últimos pontos → mais robusto)
        y_ss = float(np.mean(output[-10:]))

        delta_y = y_ss - y0
        if abs(delta_y) < 1e-10:
            raise ValueError("Variação de saída muito pequena.")

        # 🔹 Ganho
        K = delta_y / step_amplitude

        # 🔹 Normalização
        y_norm = (output - y0) / delta_y

        # 🔹 Pontos de Smith
        t1 = self._time_at_fraction(time, y_norm, 0.283)
        t2 = self._time_at_fraction(time, y_norm, 0.632)

        if t1 is None or t2 is None:
            raise ValueError("Não foi possível encontrar os pontos 28.3% e 63.2%.")

        # 🔥 Fórmulas CORRETAS
        tau = 1.5 * (t2 - t1)
        theta = t1 - 0.5 * tau

        # 🔹 Garantir valores físicos
        tau = max(tau, 1e-6)
        theta = max(theta, 0.0)

        # 🔹 Simulação do modelo
        y_model = self._simulate_fopdt(time, K, tau, theta, step_amplitude, y0)

        # 🔹 Erro quadrático médio
        eqm = float(np.mean((output - y_model) ** 2))

        return FOPDTModel(K=K, tau=tau, theta=theta, eqm=eqm)

    def _time_at_fraction(self, time, y_norm, fraction):
        """Retorna o tempo onde a saída atinge determinada fração."""
        indices = np.where(y_norm >= fraction)[0]
        if len(indices) == 0:
            return None

        idx = indices[0]

        # 🔹 Interpolação linear
        if idx > 0:
            y_prev, y_curr = y_norm[idx - 1], y_norm[idx]
            t_prev, t_curr = time[idx - 1], time[idx]

            if y_curr != y_prev:
                return t_prev + (fraction - y_prev) * (t_curr - t_prev) / (y_curr - y_prev)

        return float(time[idx])

    def _simulate_fopdt(
        self,
        time,
        K,
        tau,
        theta,
        step_amplitude,
        y0,
    ):
        """Simula resposta do modelo FOPDT"""
        y = np.full_like(time, y0, dtype=float)

        mask = time >= theta
        y[mask] = y0 + K * step_amplitude * (
            1 - np.exp(-(time[mask] - theta) / tau)
        )

        return y

    def get_model_response(
        self,
        time,
        model: FOPDTModel,
        step_amplitude=1.0,
        y0=0.0,
    ):
        """Retorna curva do modelo identificado"""
        return self._simulate_fopdt(
            time, model.K, model.tau, model.theta, step_amplitude, y0
        )
"""
model/pid_tuning.py
Métodos de sintonia PID para o Grupo 2: Ziegler-Nichols e ITAE.

Todos os métodos recebem os parâmetros FOPDT (K, tau, theta)
e retornam (Kp, Ti, Td).
"""

from dataclasses import dataclass
from enum import Enum
import numpy as np


class TuningMethod(Enum):
    ZIEGLER_NICHOLS = "Ziegler-Nichols"
    ITAE            = "ITAE"
    MANUAL          = "Manual"


@dataclass
class PIDParameters:
    """Parâmetros do controlador PID."""
    Kp: float
    Ti: float   # Tempo integral (s)
    Td: float   # Tempo derivativo (s)
    method: str = ""

    @property
    def Ki(self) -> float:
        """Ganho integral: Ki = Kp / Ti"""
        return self.Kp / self.Ti if self.Ti > 0 else 0.0

    @property
    def Kd(self) -> float:
        """Ganho derivativo: Kd = Kp * Td"""
        return self.Kp * self.Td

    def __str__(self):
        return (
            f"[{self.method}]  Kp={self.Kp:.4f}  Ti={self.Ti:.4f}s  Td={self.Td:.4f}s  "
            f"(Ki={self.Ki:.4f}  Kd={self.Kd:.4f})"
        )


class ZieglerNicholsTuning:
    """
    Sintonia PID pelo Método de Ziegler-Nichols (Curva de Reação).

    Aplicável a sistemas FOPDT com resposta em malha aberta.

    Fórmulas para controlador PID:
        Kp = 1.2 * tau / (K * theta)
        Ti = 2.0 * theta
        Td = 0.5 * theta

    Referência:
        Ziegler & Nichols, ASME Transactions, 1942.
    """

    def tune(self, K: float, tau: float, theta: float) -> PIDParameters:
        """
        Calcula os parâmetros PID pelo método de Ziegler-Nichols.

        Parâmetros
        ----------
        K     : ganho estático do processo
        tau   : constante de tempo (s)
        theta : atraso (dead time) (s)
        """
        if theta <= 0:
            raise ValueError("θ (theta) deve ser maior que zero para Ziegler-Nichols.")
        if K <= 0 or tau <= 0:
            raise ValueError("K e τ devem ser positivos.")

        Kp = 1.2 * tau / (K * theta)
        Ti = 2.0 * theta
        Td = 0.5 * theta

        return PIDParameters(Kp=Kp, Ti=Ti, Td=Td, method="Ziegler-Nichols")


class ITAETuning:
    """
    Sintonia PID pelo Critério ITAE (Integral of Time-weighted Absolute Error)
    para rejeição a perturbações em sistemas FOPDT.

    Fórmulas baseadas na razão de atraso: phi = theta / tau

    Kp = (A/K) * (theta/tau)^B
    Ti = tau / (C + D * (theta/tau))
    Td = E * tau * (theta/tau)^F

    Coeficientes para controlador PID (sintonia para set-point):
        A=0.965, B=-0.855, C=0.796, D=-0.1465, E=0.308, F=0.929

    Referência:
        Chien & Fruehauf (1990), adaptado por Seborg et al. (2016).
    """

    # Coeficientes ITAE para PID (rastreamento de set-point)
    # Fonte: Seborg, Edgar & Mellichamp (2016)
    _A = 0.965
    _B = -0.855
    _C = 0.796
    _D = -0.1465
    _E = 0.308
    _F = 0.929

    def tune(self, K: float, tau: float, theta: float) -> PIDParameters:
        """
        Calcula os parâmetros PID pelo critério ITAE.

        Parâmetros
        ----------
        K     : ganho estático do processo
        tau   : constante de tempo (s)
        theta : atraso (dead time) (s)
        """
        if theta <= 0 or tau <= 0 or K <= 0:
            raise ValueError("K, τ e θ devem ser positivos para o método ITAE.")

        phi = theta / tau  # razão de atraso normalizada

        Kp = (self._A / K) * (phi ** self._B)
        Ti = tau / (self._C + self._D * phi)
        Td = self._E * tau * (phi ** self._F)

        # Garante valores físicos
        Ti = max(Ti, 1e-6)
        Td = max(Td, 0.0)

        return PIDParameters(Kp=Kp, Ti=Ti, Td=Td, method="ITAE")


class PIDTuner:
    """
    Fachada (Facade) que centraliza o acesso aos métodos de sintonia.
    Adicione novos métodos aqui sem alterar o controller.
    """

    def __init__(self):
        self._zn   = ZieglerNicholsTuning()
        self._itae = ITAETuning()

    def tune(
        self,
        method: TuningMethod,
        K: float,
        tau: float,
        theta: float,
        Kp_manual: float = 1.0,
        Ti_manual: float = 1.0,
        Td_manual: float = 0.0,
    ) -> PIDParameters:
        """
        Chama o método de sintonia correspondente e retorna os parâmetros PID.
        """
        if method == TuningMethod.ZIEGLER_NICHOLS:
            return self._zn.tune(K, tau, theta)

        elif method == TuningMethod.ITAE:
            return self._itae.tune(K, tau, theta)

        elif method == TuningMethod.MANUAL:
            return PIDParameters(
                Kp=Kp_manual,
                Ti=Ti_manual,
                Td=Td_manual,
                method="Manual",
            )

        else:
            raise ValueError(f"Método desconhecido: {method}")

    def available_methods(self) -> list:
        """Retorna os métodos disponíveis para o Grupo 2."""
        return [TuningMethod.ZIEGLER_NICHOLS, TuningMethod.ITAE, TuningMethod.MANUAL]
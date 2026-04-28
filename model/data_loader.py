"""
model/data_loader.py
Responsável por carregar e validar arquivos .mat com dados experimentais.
"""

import numpy as np
import scipy.io as sio


class DataLoader:
    """
    Carrega datasets no formato .mat e extrai os vetores de tempo,
    entrada (u) e saída (y) do processo.
    """

    def __init__(self):
        self.time = None
        self.input_signal = None
        self.output_signal = None
        self.metadata = {}
        self.filepath = None

    def load(self, filepath: str) -> bool:
        """
        Carrega o arquivo .mat e identifica automaticamente as variáveis.
        """
        try:
            raw = sio.loadmat(filepath)

            # Remove chaves internas do scipy
            data = {k: v for k, v in raw.items() if not k.startswith("__")}

            self.filepath = filepath
            self._parse_variables(data)
            self._extract_metadata(data)

            return True

        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
        except Exception as e:
            raise ValueError(f"Erro ao carregar .mat: {str(e)}")

    def _parse_variables(self, data: dict):
        """
        Identifica automaticamente tempo, entrada e saída.
        """
        keys = list(data.keys())

        # 🔹 Possíveis nomes (compatível com seu dataset)
        time_keys    = ["t", "time", "tempo", "tiempo", "T"]
        input_keys   = ["u", "input", "entrada", "dados_entrada", "U"]
        output_keys  = ["y", "output", "saida", "dados_saida", "Y", "ySP"]

        # 🔥 Função correta para extrair dados
        def find_key(candidates):
            for c in candidates:
                if c in data:
                    val = data[c]

                    # 🔥 Se vier como matriz (ex: Nx2), pega só a primeira coluna
                    if isinstance(val, np.ndarray) and val.ndim > 1:
                        val = val[:, 0]

                    return val.flatten()
            return None

        # 🔹 Encontrar sinais
        self.time = find_key(time_keys)
        self.input_signal = find_key(input_keys)
        self.output_signal = find_key(output_keys)

        # 🔹 Caso os dados venham como matriz única
        if self.time is None and len(keys) == 1:
            matrix = data[keys[0]]

            if isinstance(matrix, np.ndarray) and matrix.ndim == 2:
                self.time = matrix[:, 0]
                self.output_signal = matrix[:, 1]

                if matrix.shape[1] >= 3:
                    self.input_signal = matrix[:, 2]

        # 🔴 Validação obrigatória
        if self.time is None or self.output_signal is None:
            raise ValueError(
                "Não foi possível identificar tempo e saída no arquivo.\n"
                f"Colunas encontradas: {keys}"
            )

        # 🔥 Garantir mesmo tamanho (resolve erro 802 vs 401)
        min_len = min(len(self.time), len(self.output_signal))

        self.time = self.time[:min_len]
        self.output_signal = self.output_signal[:min_len]

        if self.input_signal is not None:
            self.input_signal = self.input_signal[:min_len]

    def _extract_metadata(self, data: dict):
        """Extrai metadados opcionais."""
        self.metadata = {}

        for key in ["unit_time", "unit_output", "unit_input", "descricao"]:
            if key in data:
                self.metadata[key] = str(data[key])

    def get_step_amplitude(self) -> float:
        """Retorna amplitude do degrau."""
        if self.input_signal is not None:
            return float(np.max(self.input_signal) - np.min(self.input_signal))
        return 1.0

    def is_loaded(self) -> bool:
        return self.time is not None and self.output_signal is not None

    def summary(self) -> dict:
        """Resumo dos dados carregados."""
        if not self.is_loaded():
            return {}

        return {
            "n_amostras": len(self.time),
            "t_inicial": float(self.time[0]),
            "t_final": float(self.time[-1]),
            "y_min": float(np.min(self.output_signal)),
            "y_max": float(np.max(self.output_signal)),
            "amplitude_degrau": self.get_step_amplitude(),
            "metadata": self.metadata,
        }
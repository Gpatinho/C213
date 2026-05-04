"""
utils/report_generator.py
Geração de Laudo Técnico Profissional focado em Engenharia de Controle Clássico.
"""
from fpdf import FPDF


class ReportGenerator(FPDF):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    def header(self):
        self.set_fill_color(30, 70, 110)
        self.rect(0, 0, 210, 25, 'F')
        self.set_font('Arial', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, 'LAUDO TECNICO DE ENGENHARIA - CONTROLE PID', ln=True, align='C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Disciplina C213 - Sistemas Embarcados - Inatel 2026', ln=True, align='C')
        self.ln(15)

    def _escrever_fundamentacao_teorica(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, '3. Fundamentacao Teorica da Aplicacao', ln=True)
        self.set_font('Arial', '', 10)

        texto = (
            "O sistema opera em malha fechada utilizando o erro (SP-PV) para correcao. "
            "A Acao Proporcional (Kp) reduz o erro e acelera a subida, mas aumenta o sobressinal. "
            "A Acao Integral (Ti) elimina o erro estacionario, mas pode instabilizar se for excessiva. "
            "A Acao Derivativa (Td) amortece as oscilacoes, atuando como um freio preditivo."
        )

        self.multi_cell(0, 5, texto)
        self.ln(5)

    def _escrever_nota_tecnica_local(self):
        self.ln(10)
        self.set_font('Arial', 'B', 11)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, 'Apendice: Logica de Diagnostico do Relatorio Local', ln=True)

        self.set_font('Arial', 'I', 9)
        self.set_text_color(100, 100, 100)

        regras = (
            "* Regra de Sobressinal (Mp): Agressivo se Mp > 20%; Moderado entre 0.5% e 20%; Conservador se ~0%.\n"
            "* Regra de Estabilidade (ts): Se ts for N/A, sistema instavel.\n"
            "* Regra de Erro Estatico (ess): Se ess > 0.05, acao integral ineficaz."
        )

        self.multi_cell(0, 4, regras)

    def _gerar_analise_estatica(self, historico):
        if not historico:
            return "Nenhuma simulacao foi realizada."

        txt = ""

        for nome, dados in historico.items():
            met = dados['metrics']
            txt += f"[{nome}]: "

            # Overshoot
            if met.overshoot is not None:
                if met.overshoot > 20:
                    txt += f"Agressivo (Mp={met.overshoot:.1f}%). "
                elif met.overshoot > 0.5:
                    txt += f"Moderado (Mp={met.overshoot:.1f}%). "
                else:
                    txt += "Suave. "
            else:
                txt += "Instavel. "

            # Settling time
            if met.settling_time is not None:
                txt += f"ts={met.settling_time:.1f}s. "
            else:
                txt += "Nao estabilizou. "

            # Erro estacionário
            if met.steady_state_error is not None and met.steady_state_error > 0.05:
                txt += "Erro elevado."

            txt += "\n\n"

        return txt

    def obter_analise_ia(self, simulacoes, K, tau, theta):
        """
        🔥 SUBSTITUÍDO: Agora sempre usa análise local (sem API externa)
        """
        return self._gerar_analise_estatica(simulacoes)

    def generate(self, output_path, use_ai=True):
        self.add_page()
        self.set_text_color(0, 0, 0)

        melhor_id = "Sundaresan" if self.controller.dados_identificacao['Sundaresan']['eqm'] < self.controller.dados_identificacao['Smith']['eqm'] else "Smith"

        K = self.controller.dados_identificacao[melhor_id]['K']
        tau = self.controller.dados_identificacao[melhor_id]['tau']
        theta = self.controller.dados_identificacao[melhor_id]['theta']

        # 1. Função de Transferência
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, '1. Funcao de Transferencia Identificada (FOPDT)', ln=True)

        self.set_font('Arial', '', 11)
        self.cell(0, 6, f"Modelo: '{melhor_id}'", ln=True)

        self.set_font('Courier', 'B', 11)
        self.cell(0, 8, f"          {K:.4f} * e^(-{theta:.2f}s)", ln=True)
        self.cell(0, 8, f"  G(s) = --------------------", ln=True)
        self.cell(0, 8, f"             {tau:.2f}s + 1", ln=True)

        # 2. Tabela
        self.ln(5)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, '2. Tabela de Desempenho', ln=True)

        self.set_font('Courier', 'B', 8)
        self.cell(0, 6, f"{'Metodo':20} | {'Kp':6} | {'Ti':6} | {'Td':6} || {'ts':6} | {'Mp':6}", ln=True)
        self.cell(0, 2, "-"*70, ln=True)

        self.set_font('Courier', '', 8)

        for nome, dados in self.controller.historico_simulacoes.items():
            pid = dados['pid']
            met = dados['metrics']

            ts = f"{met.settling_time:.2f}" if met.settling_time else "N/A"
            mp = f"{met.overshoot:.2f}" if met.overshoot else "N/A"

            self.cell(0, 6,
                f"{nome:20} | {pid.Kp:6.2f} | {pid.Ti:6.2f} | {pid.Td:6.2f} || {ts:6} | {mp:6}",
                ln=True
            )

        # 3. Fundamentação
        self.ln(5)
        self._escrever_fundamentacao_teorica()

        # 4. Análise
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, '4. Avaliacao Analitica', ln=True)

        self.set_font('Arial', '', 10)
        analise = self._gerar_analise_estatica(self.controller.historico_simulacoes)
        self.multi_cell(0, 5, analise)

        # 5. Apêndice
        self._escrever_nota_tecnica_local()

        self.output(output_path)
        return True
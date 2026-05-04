README ATUALIZADO (PRONTO PRA COLAR)
# C213 — Identificação de Sistemas e Controle PID
### Grupo 2 | Disciplina: Sistemas de Controle Automático

> Aplicação desktop para identificação de modelos FOPDT e projeto de controladores PID com interface gráfica interativa.

---

## 📌 Visão Geral

Este projeto permite:

- Identificar modelos FOPDT a partir de dados experimentais
- Comparar métodos clássicos de identificação
- Projetar controladores PID automaticamente ou manualmente
- Simular respostas em malha fechada
- Gerar relatórios técnicos em PDF

---

## 👥 Integrantes

| Nome | GitHub |
|------|--------|
| Guilherme Felipe | [@Gpatinho](https://github.com/Gpatinho) |
| Clara de Lima Azevedo | [@claralimaze](https://github.com/claralimaze) |
| Tiago Rodrigues Gregório | [@tiagogregorio](https://github.com/tiagogregorio) |

---

## ⚙️ Funcionalidades

### 🔹 Identificação de Sistemas
- Método de **Smith**
- Método de **Sundaresan**
- Cálculo automático do **EQM**
- Seleção do melhor modelo

### 🔹 Controle PID
- Ziegler-Nichols (rápido, com sobressinal)
- ITAE (resposta suave)
- Modo manual (Kp, Ti, Td)

### 🔹 Simulação
- Resposta ao degrau
- Métricas:
  - Tempo de subida (tr)
  - Tempo de acomodação (ts)
  - Sobressinal (Mp)
  - Erro estacionário (ess)

### 🔹 Relatórios
- Geração de PDF técnico
- Análise baseada em regras (sem uso de IA externa)

---

## 🧠 Modelo FOPDT

     K · e^(-θs)

G(s) = ─────────────
τs + 1


Onde:
- **K** — ganho do sistema  
- **τ** — constante de tempo  
- **θ** — atraso (dead time)  

---

## 🗂 Estrutura do Projeto


C213/
│
├── main.py
├── requirements.txt
│
├── model/
├── view/
├── controller/
├── utils/
│
└── data/


---

## 🚀 Instalação e Execução

### 📌 Pré-requisitos
- Python 3.9+
- pip

---

### 🔧 Passo a passo

#### 1. Clone o repositório
```bash
git clone https://github.com/Gpatinho/C213.git
cd C213
2. (Opcional) Ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
3. Instale as dependências
pip install -r requirements.txt
4. Execute o projeto
python main.py
🔐 Login

O sistema utiliza um login simples e local para garantir execução estável:

Usuário: admin
Senha: admin

⚠️ Observação: O login foi simplificado para evitar dependências externas e garantir funcionamento em qualquer ambiente.

🖥 Como Usar
🔹 Aba Identificação
Carregue o arquivo .mat
Clique em Identificar
Compare os métodos
Escolha o modelo para controle
🔹 Aba Controle PID
Escolha modo automático ou manual
Defina o SetPoint
Clique em Sintonizar
Analise os gráficos e métricas
📊 Resultados

O sistema permite comparar:

Precisão dos modelos (EQM)
Desempenho dos controladores
Estabilidade e tempo de resposta
📦 Dependências
PyQt5
pyqtgraph
numpy
scipy
control
matplotlib
fpdf
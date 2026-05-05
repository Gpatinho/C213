# C213 — Identificação de Sistemas e Controle PID
### Grupo 2 | Disciplina: Sistemas de Controle Automático — Inatel 2026

> Aplicação desktop para identificação de modelos FOPDT e projeto de controladores PID com interface gráfica interativa, tela de login, geração de relatório PDF e análise por IA.

---

## Integrantes

| Nome | GitHub |
|------|--------|
| Guilherme Felipe | 
| Thiago Rodrigues Gregorio | 
| Clara de Lima azevedo | 

---

## Como Rodar o Projeto — Passo a Passo

### Pré-requisitos

- **Python 3.9 ou superior** — [download aqui](https://www.python.org/downloads/)
- **Git** — [download aqui](https://git-scm.com/downloads)
- Conexão com internet (para instalar dependências)

Para verificar se você já tem o Python instalado, abra o terminal e rode:
```bash
python --version
```

---

### 1. Clonar o Repositório

```bash
git clone https://github.com/Gpatinho/C213.git
cd C213
```

---

### 2. Criar Ambiente Virtual (recomendado)

Evita conflitos com outras versões de bibliotecas instaladas no sistema.

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux / Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> Quando o ambiente estiver ativo, você verá `(venv)` no início do terminal.

---

### 3. Instalar as Dependências

```bash
pip install -r requirements.txt
```

Isso instala automaticamente todas as bibliotecas necessárias:

| Biblioteca | Para que serve |
|-----------|----------------|
| `PyQt5` | Interface gráfica |
| `pyqtgraph` | Gráficos interativos |
| `numpy` | Cálculos numéricos |
| `scipy` | Carregamento de arquivos `.mat` |
| `control` | Simulação de sistemas de controle |
| `matplotlib` | Plotagem auxiliar |
| `fpdf2` | Geração de relatório PDF |
| `google-generativeai` | Análise por IA no relatório (opcional) |
| `python-dotenv` | Carregamento de variáveis de ambiente |

---

### 4. Configurar o Arquivo `.env`

O projeto usa um arquivo `.env` para as credenciais de login. Crie o arquivo copiando o exemplo:

**Windows:**
```powershell
copy .env.example .env
```

**Linux / Mac:**
```bash
cp .env.example .env
```

O arquivo `.env` já vem com as credenciais padrão prontas para uso:
```
APP_USER=admin
APP_PASS=admin123
```

> ⚠️ **Nunca commite o arquivo `.env` no GitHub** — ele contém senhas e chaves de API.

#### (Opcional) Habilitar análise por IA no relatório

Se quiser usar o Google Gemini para gerar análises automáticas no relatório PDF, obtenha uma chave em [aistudio.google.com](https://aistudio.google.com/app/apikey) e adicione no `.env`:
```
GEMINI_API_KEY=sua_chave_aqui
```
Se deixar em branco, o relatório será gerado com análise por regras locais, sem necessidade de internet.

---

### 5. Executar o Projeto

```bash
python main.py
```

A aplicação vai abrir com uma **tela de login**. Use as credenciais do arquivo `.env`:
- **Usuário:** `admin`
- **Senha:** `admin123`

---

## Como Usar a Aplicação

### Aba 1 — Identificação

1. Clique em **Carregar .mat** e selecione o dataset do seu grupo na pasta `data/`
2. Clique em **Identificar** — o sistema roda Smith e Sundaresan automaticamente
3. Compare os resultados: o método com **menor EQM** é destacado automaticamente
4. Use o menu suspenso **"Usar para sintonia"** para escolher qual modelo usar na sintonia PID
5. O gráfico superior mostra a **saída y(t)** com as curvas dos dois modelos sobrepostas
6. O gráfico inferior mostra o **sinal de entrada u(t)**
7. Clique em **Exportar Gráfico** para salvar a imagem

### Aba 2 — Controle PID

1. Escolha o modo de sintonia:
   - **Método** → selecione Ziegler-Nichols ou ITAE (parâmetros calculados automaticamente)
   - **Manual** → insira Kp, Ti e Td manualmente
2. No modo **Manual**, ao clicar em Sintonizar o sistema **verifica a estabilidade automaticamente** antes de simular. Se o sistema for instável, um aviso aparece com a opção de continuar ou cancelar
3. Defina o **SetPoint** desejado
4. Clique em **Sintonizar** para simular um método individualmente
5. Clique em **Comparar ZN vs ITAE** para ver os dois métodos no mesmo gráfico com métricas lado a lado
6. Analise as métricas: **tr** (tempo de subida), **ts** (tempo de acomodação), **Mp** (sobressinal) e **ess** (erro em regime permanente)
7. Clique em **Exportar Gráfico** para salvar

---

## Datasets Disponíveis

| Arquivo | Grupo |
|---------|-------|
| `Dataset_Grupo1_c213.mat` | Grupo 1 |
| `Dataset_Grupo2_c213.mat` | Grupo 2 ← **(seu grupo)** |
| `Dataset_Grupo3_c213.mat` | Grupo 3 |
| `Dataset_Grupo4_c213.mat` | Grupo 4 |
| `Dataset_Grupo5_c213.mat` | Grupo 5 |
| `Dataset_Grupo6_c213.mat` | Grupo 6 |
| `Dataset_Grupo7_c213.mat` | Grupo 7 |
| `Dataset_Grupo8_c213.mat` | Grupo 8 |
| `Dataset_Grupo9_c213.mat` | Grupo 9 |

---

## Estrutura do Projeto

```
C213/
│
├── main.py                     # Ponto de entrada (login + janela principal)
├── requirements.txt            # Dependências do projeto
├── .env.example                # Exemplo de configuração (copiar para .env)
│
├── model/                      # Camada Model (MVC)
│   ├── data_loader.py          # Carregamento de arquivos .mat
│   ├── identification.py       # Métodos Smith e Sundaresan
│   ├── pid_tuning.py           # Sintonia PID (ZN, ITAE, Manual)
│   └── simulator.py            # Simulação em malha fechada + métricas
│
├── view/                       # Camada View (MVC)
│   ├── login_dialog.py         # Tela de login
│   ├── main_window.py          # Janela principal com abas
│   ├── tab_identification.py   # Aba de Identificação
│   └── tab_pid_control.py      # Aba de Controle PID
│
├── controller/                 # Camada Controller (MVC)
│   └── app_controller.py       # Orquestra Model e View
│
├── utils/
│   └── report_generator.py     # Geração de relatório PDF com IA
│
└── data/
    └── Dataset_Grupo*_c213.mat # Datasets experimentais (todos os grupos)
```

---

## Métodos Implementados

### Identificação — Modelo FOPDT

```
         K · e^(-θs)
G(s) = ─────────────
           τs + 1
```

| Método | Pontos Utilizados | Referência |
|--------|-------------------|------------|
| **Smith** | 28.3% e 63.2% da resposta normalizada | Smith (1972) |
| **Sundaresan** | 35.3% e 85.3% da resposta normalizada | Sundaresan & Krishnaswamy (1978) |

### Sintonia PID — Grupo 2

| Método | Característica |
|--------|---------------|
| **Ziegler-Nichols** | Resposta rápida, maior sobressinal |
| **ITAE** | Minimiza erro ponderado no tempo, resposta mais suave |
| **Manual** | Ajuste livre com verificação automática de estabilidade |

---

## Resultados — Dataset Grupo 2

### Identificação

| Parâmetro | Smith | Sundaresan | Valor Real |
|-----------|-------|------------|------------|
| K | 0.8789 | 0.8789 | 0.88 |
| τ (s) | 30.92 | 30.66 | 31.0 |
| θ (s) | 5.80 | 11.47 | 6.0 |
| **EQM** | **7.788** | **0.047** | — |

### Sintonia PID

| Métrica | Ziegler-Nichols | ITAE |
|---------|----------------|------|
| Kp | 7.2737 | 4.5894 |
| Ti (s) | 11.6092 | 40.2364 |
| Td (s) | 2.9023 | 2.0133 |
| **tr (s)** | **7.1** | **11.8** |
| **ts (s)** | **34.9** | **47.1** |
| **Mp (%)** | **58.6** | **0.0** |
| **ess** | **≈ 0** | **≈ 0** |

> O **ITAE** elimina o sobressinal ao custo de uma resposta mais lenta — ideal para plantas térmicas onde oscilações são indesejadas.

---

## Solução de Problemas

**Erro: `No module named 'fpdf'`**
```bash
pip install fpdf2
```

**Erro: `No module named 'PyQt5'`**
```bash
pip install PyQt5
```

**Erro: `No module named 'control'`**
```bash
pip install control
```

**Erro: `No module named 'dotenv'`**
```bash
pip install python-dotenv
```

**Arquivo `.env` não encontrado**
```powershell
copy .env.example .env
```

---

## Referências

- Smith, C. L. (1972). *Digital Computer Process Control*. Intext Educational Publishers.
- Sundaresan, K. R., Krishnaswamy, P. R. (1978). *Estimation of time delay parameters in linear systems*. Ind. Eng. Chem. Process Des. Dev.
- Ziegler, J. G., Nichols, N. B. (1942). *Optimum settings for automatic controllers*. ASME Transactions.
- Ogata, K. (2010). *Engenharia de Controle Moderno*. 5ª Edição.
- Seborg, D. E., Edgar, T. F., Mellichamp, D. A. (2016). *Dinâmica e Controle de Processos*. 4ª Edição.

---

## Licença

Projeto acadêmico desenvolvido para a disciplina C213 — Sistemas de Controle Automático.
Instituto Nacional de Telecomunicações — Inatel, 2026.
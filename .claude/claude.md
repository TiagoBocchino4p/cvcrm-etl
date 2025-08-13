# 🤖 claude.md - Guia de Referência para Claude

> **IMPORTANTE:** Este arquivo serve como contexto essencial para o Claude ao analisar este projeto no VS Code. Leia SEMPRE antes de fazer alterações no código.

---

## 🎯 CONTEXTO DO PROJETO

**NOME:** CVCRM ETL Pipeline  
**CLIENTE:** BP Incorporadora  
**DEV:** Tiago Bocchino (tiago.bocchino@4pcapital.com.br)  
**OBJETIVO:** Automatizar sincronização CVCRM → PostgreSQL com dashboard

---

## 🔐 AUTENTICAÇÃO - REGRAS CRÍTICAS

### ⚠️ MÉTODO CORRETO DESCOBERTO (Agosto 2025)
```python
# ✅ USAR SEMPRE (testado e funcionando)
headers = {
    'email': os.getenv('CVCRM_API_EMAIL'),
    'token': os.getenv('CVCRM_API_TOKEN'),
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# ❌ NUNCA USAR (já testado - não funciona)
# Bearer Token, Basic Auth, X-API-*, Query Params
```

### 🌐 URL BASE ESPECÍFICA
```python
# ✅ URL CORRETA (específica da BP Incorporadora)
base_url = 'https://bpincorporadora.cvcrm.com.br/api/v1/cvdw'

# ❌ URLS INCORRETAS
# 'https://api.cvcrm.com.br/v1'
# 'https://cvcrm.com.br/api/v1'
```

### ⏱️ RATE LIMITING OBRIGATÓRIO
```python
import time
time.sleep(3)  # SEMPRE 3+ segundos entre requests
# Limite: 20 requests/minuto
# Erro 429 = aguardar 60 segundos
```

---

## 📊 ESTRUTURA DE DADOS CVDW

### 🎯 ENDPOINTS FUNCIONAIS
```python
ENDPOINTS_STATUS = {
    'reservas': 'FUNCIONA',           # ✅ Testado OK
    'reservas/valores': 'RATE_LIMIT', # ⚠️ Funciona com delay
    'vendas': 'RATE_LIMIT',          # ⚠️ Funciona com delay  
    'empreendimentos': 'ERROR_405',   # ❌ Método não permitido
    'unidades': 'ERROR_401'           # ❌ Sem permissão
}
```

### 📋 PARÂMETROS PADRÃO
```python
default_params = {
    'page': 1,
    'registros_por_pagina': 500,  # MAX permitido
    'a_partir_data_referencia': None  # Para sync incremental
}
```

---

## 🗄️ PADRÕES DE BANCO DE DADOS

### 🏗️ TABELAS PRINCIPAIS (9 tabelas)
```python
CORE_TABLES = [
    'empreendimentos',  # Cadastro empreendimentos
    'vendas',          # Transações vendas
    'unidades',        # Unidades imóveis
    'prosoluto',       # Sistema ProSoluto
    'contratos',       # Contratos firmados
    'clientes',        # Cadastro clientes
    'repasses',        # Repasses financeiros
    'tabela_preco',    # Tabelas preços
    'leads'            # Leads vendas
]
```

### 📈 VIEWS ANALÍTICAS
```sql
-- ⚠️ ATENÇÃO: Views com GROUP BY
-- SEMPRE incluir campos não-agregados no GROUP BY
-- Especialmente EXTRACT(), DATE_PART(), etc.

-- ✅ CORRETO
CREATE VIEW view_vendas_anuais AS
SELECT 
    empreendimento_id,
    EXTRACT(YEAR FROM data_venda) as ano,
    COUNT(*) as total_vendas
FROM vendas
GROUP BY empreendimento_id, EXTRACT(YEAR FROM data_venda);

-- ❌ ERRO COMUM (já ocorreu)
-- GROUP BY empreendimento_id; -- Falta o EXTRACT!
```

---

## 🔧 FUNÇÕES PRINCIPAIS DO SISTEMA

### 1️⃣ CloudDatabaseManager (main.py)
```python
class CloudDatabaseManager:
    def __init__(self):
        # Conecta PostgreSQL via DATABASE_URL
        
    def create_tables(self):
        # ⚠️ Local do erro SQL GROUP BY
        # Sempre verificar sintaxe das Views
        
    def get_connection(self):
        # Context manager para conexões
```

### 2️⃣ ETLProcessor (main.py)
```python
class ETLProcessor:
    def __init__(self):
        # Inicializa com headers corretos
        self.headers = {
            'email': os.getenv('CVCRM_API_EMAIL'),
            'token': os.getenv('CVCRM_API_TOKEN'),
            'Accept': 'application/json'
        }
        
    def fetch_data_from_api(self, endpoint, params=None):
        # SEMPRE usar time.sleep(3) antes do request
        # SEMPRE verificar status_code
        
    def sync_empreendimentos(self):
    def sync_vendas(self):
    def sync_unidades(self):
    # etc... uma função por endpoint
```

### 3️⃣ Dashboard (monitoring.py)
```python
# Flask app para monitoramento
# Plotly para gráficos
# KPIs em tempo real
```

---

## 🐛 PROBLEMAS CONHECIDOS E SOLUÇÕES

### ❌ Erro SQL GROUP BY
```
ERRO: column "vendas.data_venda" must appear in the GROUP BY clause
LOCAL: main.py linha ~487 (create_tables)
CAUSA: VIEW usando EXTRACT() sem incluir no GROUP BY
```

### ❌ UnicodeEncodeError (Windows)
```python
# PROBLEMA: Emojis no logging (❌ ✅ 🎯)
# SOLUÇÃO: Usar print() ou configurar encoding UTF-8
```

### ❌ Rate Limit 429
```python
# SOLUÇÃO OBRIGATÓRIA:
if response.status_code == 429:
    print("Rate limit atingido, aguardando 60s...")
    time.sleep(60)
    # Retry request
```

---

## 📁 ARQUIVOS E RESPONSABILIDADES

### 🎯 ARQUIVOS PRINCIPAIS
```
main.py           # ETL principal + classes core
monitoring.py     # Dashboard Flask + KPIs
requirements.txt  # Dependências (28 packages)
.env             # Credenciais (EMAIL + TOKEN + DB)
runtime.txt      # Python 3.13.5
```

### 🧪 ARQUIVOS DE TESTE
```
test_api_cvcrm.py     # Teste autenticação (MÉTODO 2 funciona)
test_database.py      # Teste PostgreSQL
test_tables.py        # Teste criação estrutura
test_sync.py         # Teste sincronização individual
```

---

## 🔄 FLUXO DE DESENVOLVIMENTO

### 📋 STATUS ATUAL (Agosto 2025)
```
✅ CONCLUÍDO:
- Passo 1: Ambiente Python configurado
- Passo 2: Sintaxe validada (MimeText→MIMEText)
- Passo 3: Variáveis ambiente funcionais
- Passo 4: API CVCRM conectada (headers corretos)
- Passo 5: PostgreSQL conectado

🔄 EM ANDAMENTO:
- Passo 6: Criação tabelas (erro SQL GROUP BY)

⏳ PENDENTE:
- Passo 7: Sincronização individual
- Passo 8: Dashboard funcional
- Passo 9: ETL completo
- Passo 10: Automação
```

### 🎯 PRÓXIMA AÇÃO OBRIGATÓRIA
1. Corrigir erro SQL no main.py (~linha 487)
2. Adicionar EXTRACT(YEAR FROM data_venda) no GROUP BY
3. Executar `py test_tables.py`

---

## 🔍 COMANDOS DE DIAGNÓSTICO

### 🧪 Testes Rápidos
```bash
# Teste API
py -c "import requests, os; from dotenv import load_dotenv; load_dotenv(); r=requests.get('https://bpincorporadora.cvcrm.com.br/api/v1/cvdw/reservas', headers={'email':os.getenv('CVCRM_API_EMAIL'),'token':os.getenv('CVCRM_API_TOKEN')}); print(f'Status: {r.status_code}')"

# Teste Banco
py test_database.py

# Teste Estrutura
py test_tables.py
```

### 🔍 Debug SQL
```bash
# Encontrar problema GROUP BY
findstr /n "EXTRACT.*data_venda" main.py
findstr /n "GROUP BY" main.py
```

---

## ⚙️ VARIÁVEIS DE AMBIENTE (.env)

```env
# API CVCRM (OBRIGATÓRIO)
CVCRM_API_TOKEN=3b10d578dcafe9a...
CVCRM_API_EMAIL=tiago.bocchino@4pcapital.com.br

# PostgreSQL (OBRIGATÓRIO)  
DATABASE_URL=postgresql://user:pass@host:port/db

# Opcionais
RAILWAY_ENVIRONMENT=production
PORT=5000
ALERT_EMAIL_USER=email@gmail.com
```

---

## 🚨 REGRAS DE OURO PARA CLAUDE

### 1️⃣ SEMPRE VERIFICAR AUTENTICAÇÃO
```python
# Se vir código com Bearer Token = ESTÁ ERRADO
# Se vir código sem time.sleep() = ADICIONAR
# Se vir URL genérica = CORRIGIR para BP específica
```

### 2️⃣ SEMPRE VALIDAR SQL
```sql
-- Se vir EXTRACT(), DATE_PART(), etc. no SELECT
-- VERIFICAR se está no GROUP BY também
```

### 3️⃣ SEMPRE PRESERVAR FUNCIONALIDADES
```python
# Não alterar headers que funcionam
# Não remover time.sleep()
# Não mudar URL base sem testar
```

### 4️⃣ SEMPRE DOCUMENTAR MUDANÇAS
```python
# Atualizar este claude.md se algo mudar
# Manter histórico de tentativas
# Explicar por que algo funciona/não funciona
```

---

## 🎯 PONTOS DE ATENÇÃO ESPECÍFICOS

### 🔴 NUNCA ALTERAR SEM TESTAR:
- Headers de autenticação API
- URL base da CVCRM  
- Rate limiting (time.sleep)
- Estrutura do banco (sem backup)

### 🟡 SEMPRE VERIFICAR:
- Encoding UTF-8 em arquivos
- GROUP BY em queries com funções
- Status codes das APIs (200, 401, 429)
- Logs de erro específicos

### 🟢 PRIORIDADES:
1. Corrigir erro SQL atual
2. Completar sincronização
3. Dashboard funcional
4. Testes automatizados

---

## 📞 CONTATO E CONTEXTO

**DESENVOLVEDOR:** Tiago Bocchino  
**EMAIL:** tiago.bocchino@4pcapital.com.br  
**EMPRESA:** 4P Capital  
**CLIENTE:** BP Incorporadora  

**CLAUDE:** Use este arquivo como referência SEMPRE que trabalhar neste projeto. Ele contém todo o contexto necessário para não precisarmos repetir descobertas já feitas.

---

*🤖 Este arquivo deve ser lido pelo Claude antes de qualquer alteração no código*
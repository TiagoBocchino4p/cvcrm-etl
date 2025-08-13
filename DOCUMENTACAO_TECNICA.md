# DOCUMENTAÇÃO TÉCNICA - CVCRM ETL

## Status Atual - Agosto 2025
**SISTEMA CORRIGIDO E ALINHADO COM ESTRUTURA REAL CVDW**

### Situação
- ✅ **Infraestrutura**: 100% funcional (DB + Dashboard + Deploy)
- ✅ **Código ETL**: Corrigido para estrutura real CVDW
- ✅ **Endpoints corretos**: /reservas, /comissoes, /reservas/condicoes
- ✅ **Tabelas reestruturadas**: Campos conforme documentação CVDW
- ✅ **Views corrigidas**: Filtros Ativo='S' + data_venda IS NOT NULL

## Arquitetura do Sistema

### Visão Geral
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CVCRM API     │───▶│   Railway ETL   │───▶│ Neon PostgreSQL │
│   (CVDW v2)     │    │   (Python)      │    │   (Cloud DB)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Flask Dashboard │
                       │   (Plotly)      │
                       └─────────────────┘
```

### Componentes Principais

#### 1. ETL Processor (main.py)

**CVCRMAPIClient**: Cliente API otimizado
- Base URL: `https://bpincorporadora.cvcrm.com.br/api/v1/cvdw`
- Authentication: headers com email + token
- Rate limiting: 1 segundo entre requests
- Retry automático: 3 tentativas com backoff exponencial

**Endpoints CVDW Corrigidos**:
```python
# Endpoints corretos conforme documentação CVDW
/reservas                    # Vendas reais (Ativo='S' + data_venda)
/comissoes                   # Comissões dos corretores  
/reservas/condicoes          # Condições das reservas
/empreendimentos             # Projetos imobiliários
/unidades                    # Unidades dos empreendimentos
```

**CloudDatabaseManager**: Gerenciador PostgreSQL
- SSL obrigatório (sslmode=require)
- Pool de conexões otimizado
- Transações automáticas
- Error handling robusto

#### 2. Dashboard Web (monitoring.py)

**Flask Application**: Interface web responsiva
- Auto-refresh a cada 30 segundos
- Charts interativos Plotly
- APIs REST para integração BI
- Health checks automáticos

**Endpoints Dashboard**:
```
GET /                    # Dashboard principal
GET /health             # Health check
GET /api/kpis           # KPIs JSON
GET /api/sales          # Dados vendas
```

## Estrutura do Banco de Dados

### Tabelas Principais - Estrutura CVDW Corrigida

#### vendas (Vendas Reais)
```sql
CREATE TABLE IF NOT EXISTS vendas (
    id SERIAL PRIMARY KEY,
    cvcrm_id INTEGER UNIQUE NOT NULL,
    reserva_id INTEGER,
    empreendimento VARCHAR(255),
    corretor VARCHAR(255),
    time_corretor VARCHAR(100),
    cliente VARCHAR(255),
    cliente_email VARCHAR(255),
    valor DECIMAL(15,2),
    data_venda DATE,
    data_registro TIMESTAMP,
    ativo VARCHAR(1),
    comissao_valor DECIMAL(15,2),
    comissao_percentual DECIMAL(5,2),
    forma_pagamento VARCHAR(100),
    origem_lead VARCHAR(100),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### empreendimentos
```sql
CREATE TABLE IF NOT EXISTS empreendimentos (
    id SERIAL PRIMARY KEY,
    cvcrm_id INTEGER UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    endereco VARCHAR(500),
    cidade VARCHAR(100),
    estado VARCHAR(50),
    cep VARCHAR(20),
    status VARCHAR(50),
    data_lancamento DATE,
    valor_m2 DECIMAL(10,2),
    total_unidades INTEGER,
    unidades_vendidas INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### unidades
```sql
CREATE TABLE IF NOT EXISTS unidades (
    id SERIAL PRIMARY KEY,
    cvcrm_id INTEGER UNIQUE NOT NULL,
    empreendimento_id INTEGER,
    numero VARCHAR(50),
    bloco VARCHAR(50),
    andar INTEGER,
    tipologia VARCHAR(100),
    metragem DECIMAL(8,2),
    quartos INTEGER,
    suites INTEGER,
    banheiros INTEGER,
    vagas_garagem INTEGER,
    valor DECIMAL(15,2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (empreendimento_id) REFERENCES empreendimentos(cvcrm_id)
);
```

### Views Otimizadas - Filtros CVDW Corretos

#### vw_vendas_ativas (Vendas Válidas)
```sql
CREATE OR REPLACE VIEW vw_vendas_ativas AS
SELECT 
    v.*,
    e.nome as empreendimento_nome,
    e.cidade as empreendimento_cidade
FROM vendas v
LEFT JOIN empreendimentos e ON v.empreendimento = e.nome
WHERE v.ativo = 'S' 
  AND v.data_venda IS NOT NULL
  AND v.valor > 0;
```

#### vw_kpis_vendas (KPIs Dashboard)
```sql
CREATE OR REPLACE VIEW vw_kpis_vendas AS
SELECT 
    COUNT(*) as total_vendas,
    COALESCE(SUM(valor), 0) as valor_total,
    COALESCE(AVG(valor), 0) as ticket_medio,
    COALESCE(SUM(comissao_valor), 0) as comissao_total,
    COUNT(DISTINCT corretor) as total_corretores,
    COUNT(DISTINCT empreendimento) as total_empreendimentos
FROM vw_vendas_ativas;
```

#### vw_vendas_mes_atual
```sql
CREATE OR REPLACE VIEW vw_vendas_mes_atual AS
SELECT 
    DATE_TRUNC('month', data_venda) as mes,
    COUNT(*) as vendas,
    SUM(valor) as receita,
    AVG(valor) as ticket_medio
FROM vw_vendas_ativas
WHERE data_venda >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY DATE_TRUNC('month', data_venda);
```

## API Integration - Estrutura CVDW

### Authentication
```python
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'email': CVCRM_API_EMAIL,
    'token': CVCRM_API_TOKEN
}
```

### Rate Limiting
```python
# Rate limiting inteligente
time.sleep(1.0)  # 1 segundo entre requests
retry_count = 0
max_retries = 3
```

### Pagination
```python
# Paginação otimizada para cloud gratuito
params = {
    'page': page_num,
    'per_page': 25  # Reduzido para evitar timeouts
}
```

### Error Handling
```python
def api_request_with_retry(url, params=None):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)
```

## Deployment Configuration

### Railway (Cloud Platform)

**Procfile**:
```
web: gunicorn monitoring:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
worker: python main.py
```

**runtime.txt**:
```
python-3.11.5
```

**railway.json**:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "always"
  }
}
```

### Environment Variables
```env
# CVCRM API
CVCRM_API_TOKEN=your_token_here
CVCRM_API_EMAIL=your.email@company.com

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:port/db?sslmode=require

# Environment
RAILWAY_ENVIRONMENT=production
PORT=5000

# Email Alerts (Optional)
ALERT_EMAIL_USER=alerts@company.com
ALERT_EMAIL_PASSWORD=app_password
ALERT_EMAIL_TO=admin@company.com
```

### Neon PostgreSQL Setup
```sql
-- Connection string format
postgresql://username:password@hostname.neon.tech/database?sslmode=require&channel_binding=require

-- SSL Configuration (obrigatório)
sslmode=require
channel_binding=require
```

## Performance Optimizations

### Cloud-Friendly Limits
```python
# Otimizações para tier gratuito
BATCH_SIZE = 25                    # Reduzido de 100
MAX_RECORDS_PER_SYNC = 1000        # Limite por sincronização
REQUEST_TIMEOUT = 30               # Timeout adequado
CONNECTION_POOL_SIZE = 5           # Pool pequeno mas eficiente
```

### Scheduling Otimizado
```python
# Sync apenas em horário comercial (economia de recursos)
@scheduler.add_job('cron', hour='6-22', minute=0, second=0, step=4)
def scheduled_sync():
    if os.getenv('RAILWAY_ENVIRONMENT') == 'production':
        # Executa apenas em produção no horário comercial
        sync_all_data()
```

### Database Optimizations
```sql
-- Índices para performance
CREATE INDEX idx_vendas_data_venda ON vendas(data_venda);
CREATE INDEX idx_vendas_ativo ON vendas(ativo);
CREATE INDEX idx_vendas_corretor ON vendas(corretor);
CREATE INDEX idx_vendas_empreendimento ON vendas(empreendimento);

-- Particionamento por data (para grandes volumes)
CREATE TABLE vendas_2024 PARTITION OF vendas 
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

## Monitoring e Observability

### Health Checks
```python
@app.route('/health')
def health_check():
    try:
        # Test database connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        # Test API connectivity
        api_status = test_cvcrm_api()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'api': 'accessible' if api_status else 'unavailable',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
```

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cvcrm_etl.log'),
        logging.StreamHandler()
    ]
)
```

### Metrics Collection
```python
# Métricas customizadas para monitoramento
metrics = {
    'sync_duration': time.time() - start_time,
    'records_processed': total_records,
    'errors_count': error_count,
    'api_requests': request_count,
    'memory_usage': psutil.virtual_memory().percent
}
```

## Security Configuration

### SSL/TLS
- Database: SSL obrigatório (sslmode=require)
- API calls: HTTPS obrigatório
- Dashboard: HTTPS em produção

### Credential Management
- Environment variables apenas
- Nunca hardcode credentials
- .env.example para template seguro
- .gitignore protege arquivos sensíveis

### Data Privacy (LGPD Compliance)
- Dados pessoais protegidos
- Logs sem informações sensíveis
- Backup seguro
- Acesso controlado

## Troubleshooting Técnico

### Erro: SSL Connection Failed
```bash
# Verificar certificados SSL
openssl s_client -connect hostname:5432 -verify_return_error

# Testar conexão com SSL
psql "postgresql://user:pass@host/db?sslmode=require" -c "SELECT version();"
```

### Erro: API Rate Limited (429)
```python
# Implementar backoff exponencial
import time
import random

def exponential_backoff(attempt):
    base_delay = 2 ** attempt
    jitter = random.uniform(0, 1)
    return base_delay + jitter
```

### Erro: Out of Memory
```python
# Reduzir batch size
BATCH_SIZE = 10  # Para ambientes com pouca RAM

# Liberar memória explicitamente
import gc
gc.collect()
```

### Erro: Database Connection Pool Exhausted
```sql
-- Verificar conexões ativas
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Finalizar conexões antigas
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'neondb' AND pid <> pg_backend_pid();
```

## Testing Strategy

### Unit Tests
```python
# Testes individuais por componente
python test_conexao_simples.py    # API + DB básico
python test_database.py           # PostgreSQL completo
python test_tables.py             # Estrutura banco
```

### Integration Tests
```python
# Testes de integração completa
python test_sync_individual.py    # Sincronização ETL
python test_production.py         # Validação deploy
python verificar_dados.py         # Dados pós-ETL
```

### Load Testing
```python
# Teste de carga para produção
python populate_mock_data.py      # Mock data CVDW
```

## API Documentation

### Endpoints Dashboard

#### GET /api/kpis
```json
{
  "total_vendas": 150,
  "valor_total": 45000000.00,
  "ticket_medio": 300000.00,
  "comissao_total": 1350000.00,
  "total_corretores": 25,
  "total_empreendimentos": 8
}
```

#### GET /api/sales?periodo=30
```json
{
  "vendas": [
    {
      "cvcrm_id": 12345,
      "cliente": "João Silva",
      "corretor": "Maria Santos",
      "empreendimento": "Residencial Sunset",
      "valor": 350000.00,
      "data_venda": "2024-08-10",
      "comissao_valor": 10500.00
    }
  ],
  "total": 45,
  "periodo": "últimos 30 dias"
}
```

## Maintenance Tasks

### Daily
- Verificar health checks
- Monitorar logs de erro
- Validar sincronização dados

### Weekly  
- Analisar métricas performance
- Verificar uso recursos cloud
- Backup configurações

### Monthly
- Revisar e otimizar queries
- Atualizar dependências
- Análise capacidade sistema

## Backup e Recovery

### Database Backup
```bash
# Backup automático Neon
# Configurado no painel Neon.tech
# Retention: 7 dias (tier gratuito)

# Backup manual
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Configuration Backup
```bash
# Backup configurações
cp .env .env.backup.$(date +%Y%m%d)
cp railway.json railway.json.backup
```

### Recovery Procedures
```bash
# Restore database
psql $DATABASE_URL < backup_20240815.sql

# Restore configuration
cp .env.backup.20240815 .env
```
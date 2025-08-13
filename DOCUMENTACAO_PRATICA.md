# DOCUMENTAÇÃO PRÁTICA - CVCRM ETL

## Guia de Uso Diário

### Comandos Essenciais

#### Desenvolvimento Local
```bash
# Executar ETL Worker
python main.py

# Executar Dashboard Web  
python monitoring.py

# Instalar dependências
pip install -r requirements.txt

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

#### Testes e Validação
```bash
# Teste conexão básica (API + DB)
python test_conexao_simples.py

# Teste completo do banco
python test_database.py

# Teste estrutura das tabelas
python test_tables.py

# Teste sincronização individual
python test_sync_individual.py

# Teste configuração de produção
python test_production.py

# Verificar dados após ETL
python verificar_dados.py

# Popular dados de teste CVDW
python populate_mock_data.py
```

#### Produção (Railway)
```bash
# Processo Web (Dashboard)
gunicorn monitoring:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120

# Processo Worker (ETL)
python main.py

# Ver logs em tempo real
railway logs

# Deploy manual
railway up
```

### URLs Importantes

#### Ambiente de Desenvolvimento
- **Dashboard Local**: http://localhost:5000
- **Health Check**: http://localhost:5000/health
- **API KPIs**: http://localhost:5000/api/kpis
- **API Vendas**: http://localhost:5000/api/sales

#### Ambiente de Produção
- **Dashboard**: https://seu-app.railway.app
- **Health Check**: https://seu-app.railway.app/health
- **API KPIs**: https://seu-app.railway.app/api/kpis
- **API Vendas**: https://seu-app.railway.app/api/sales

## Configuração Passo-a-Passo

### 1. Setup Inicial

#### Clonar Repositório
```bash
git clone <seu-repositorio>
cd cvcrm-etl
```

#### Configurar Ambiente
```bash
# Copiar template de configuração
cp .env.example .env

# Editar com seus dados reais
notepad .env  # Windows
nano .env     # Linux/Mac
```

#### Exemplo .env
```env
# CVCRM API Credentials
CVCRM_API_TOKEN=seu_token_real_aqui
CVCRM_API_EMAIL=seu.email@empresa.com

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@host.neon.tech/db?sslmode=require

# Environment
RAILWAY_ENVIRONMENT=development
PORT=5000

# Email Alerts (Opcional)
ALERT_EMAIL_USER=alertas@empresa.com
ALERT_EMAIL_PASSWORD=senha_app_especifica
ALERT_EMAIL_TO=admin@empresa.com
```

### 2. Setup Banco Neon PostgreSQL

#### Criar Conta Neon
1. Acesse https://neon.tech
2. Cadastre-se gratuitamente
3. Crie um novo projeto
4. Anote as credenciais de conexão

#### Configurar SSL
```sql
-- Verificar SSL está ativo
SHOW ssl;

-- Testar conexão
SELECT version();
```

#### Obter String de Conexão
```bash
# Formato Neon
postgresql://username:password@hostname.neon.tech/database?sslmode=require&channel_binding=require
```

### 3. Setup Railway Deploy

#### Criar Conta Railway
1. Acesse https://railway.app
2. Conecte sua conta GitHub
3. Importe este repositório

#### Configurar Variáveis
```env
CVCRM_API_TOKEN=seu_token_aqui
CVCRM_API_EMAIL=seu.email@empresa.com
DATABASE_URL=postgresql://...neon.tech/...
RAILWAY_ENVIRONMENT=production
```

#### Configurar Serviços
- **Web Service**: Dashboard Flask
- **Worker Service**: ETL Process

## Interpretação de Dados e KPIs

### Dashboard Principal

#### KPIs Essenciais
- **Total de Vendas**: Número total de vendas válidas (Ativo='S' + data_venda)
- **Valor Total**: Soma de todas as vendas em reais
- **Ticket Médio**: Valor médio por venda
- **Comissão Total**: Soma das comissões dos corretores
- **Total Corretores**: Número de corretores ativos
- **Total Empreendimentos**: Projetos com vendas

#### Gráficos de Análise
- **Evolução Vendas**: Tendência de vendas ao longo do tempo
- **Top 10 Corretores**: Ranking por comissão
- **Vendas por Empreendimento**: Distribuição por projeto
- **Performance Mensal**: Comparativo mês a mês

### Como Interpretar os Dados

#### Vendas Válidas (Filtros CVDW)
```sql
-- Critérios para venda válida
ativo = 'S'              -- Reserva ativa
AND data_venda IS NOT NULL  -- Data de venda confirmada
AND valor > 0               -- Valor positivo
```

#### Estados da Reserva
- **Ativo='S'**: Venda confirmada e válida
- **Ativo='N'**: Venda cancelada ou inválida
- **data_venda NULL**: Reserva sem venda confirmada

#### Campos Importantes
- **reserva_id**: ID único da reserva no CVCRM
- **cvcrm_id**: ID da venda na tabela de vendas
- **empreendimento**: Nome do projeto imobiliário
- **corretor**: Nome do corretor responsável
- **valor**: Valor da venda em reais
- **comissao_valor**: Valor da comissão em reais

## Solução de Problemas Comuns

### Problemas de Conexão

#### Erro: "Connection refused"
```bash
# Verificar se o banco está acessível
telnet hostname.neon.tech 5432

# Testar conexão com psql
psql "postgresql://user:pass@host/db?sslmode=require" -c "SELECT 1;"
```

#### Erro: "SSL required"
```bash
# Garantir SSL na string de conexão
DATABASE_URL=postgresql://...?sslmode=require

# Verificar certificados
openssl s_client -connect hostname.neon.tech:5432
```

### Problemas de API

#### Erro: "401 Unauthorized"
```bash
# Verificar credenciais no .env
echo $CVCRM_API_TOKEN
echo $CVCRM_API_EMAIL

# Testar manualmente
curl -H "email: seu@email.com" -H "token: seu_token" \
     https://bpincorporadora.cvcrm.com.br/api/v1/cvdw/reservas
```

#### Erro: "429 Rate Limited"
```python
# Aumentar delay entre requests
time.sleep(2.0)  # Aumentar de 1 para 2 segundos

# Reduzir batch size
per_page = 10  # Reduzir de 25 para 10
```

### Problemas de Deploy

#### Erro: "Build Failed"
```bash
# Verificar requirements.txt
pip install -r requirements.txt

# Verificar Python version
python --version  # Deve ser 3.11.5

# Testar localmente primeiro
python main.py
python monitoring.py
```

#### Erro: "Out of Memory"
```python
# Reduzir batch size no código
BATCH_SIZE = 10
MAX_RECORDS_PER_SYNC = 500

# Otimizar queries
SELECT * FROM vendas LIMIT 100;  # Adicionar LIMIT
```

## Manutenção e Monitoramento

### Checklist Diário

#### Verificações Essenciais
- [ ] Dashboard acessível (https://seu-app.railway.app)
- [ ] Health check retornando "healthy"
- [ ] Logs sem erros críticos
- [ ] Sincronização funcionando (últimas 4 horas)
- [ ] KPIs atualizados

#### Comandos de Verificação
```bash
# Health check
curl https://seu-app.railway.app/health

# Verificar logs
railway logs --tail

# Testar API local
python test_conexao_simples.py
```

### Checklist Semanal

#### Análise de Performance
- [ ] Tempo de sincronização < 5 minutos
- [ ] Uso de memória < 80%
- [ ] Uso de CPU < 70%
- [ ] Espaço em disco < 80%

#### Validação de Dados
```sql
-- Verificar dados recentes
SELECT COUNT(*) FROM vendas 
WHERE created_at >= NOW() - INTERVAL '7 days';

-- Verificar vendas válidas
SELECT COUNT(*) FROM vw_vendas_ativas;

-- Verificar consistência
SELECT COUNT(*) FROM vendas WHERE ativo = 'S' AND data_venda IS NULL;
```

### Checklist Mensal

#### Otimização de Performance
- [ ] Analisar queries lentas
- [ ] Verificar índices necessários
- [ ] Limpar logs antigos
- [ ] Atualizar dependências

#### Backup e Segurança
```bash
# Backup configuração
cp .env .env.backup.$(date +%Y%m%d)

# Verificar certificados SSL
openssl s_client -connect hostname.neon.tech:5432 | grep -i "expire"

# Rodar todos os testes
python test_database.py
python test_production.py
```

## Casos de Uso Práticos

### Cenário 1: Nova Sincronização

#### Objetivo
Executar uma sincronização manual completa dos dados.

#### Passos
```bash
# 1. Verificar conexões
python test_conexao_simples.py

# 2. Executar ETL
python main.py

# 3. Verificar resultados
python verificar_dados.py

# 4. Acessar dashboard
# Abrir http://localhost:5000
```

### Cenário 2: Análise de Vendas

#### Objetivo
Analisar performance de vendas do último mês.

#### Passos
```sql
-- 1. Vendas do mês atual
SELECT 
    corretor,
    COUNT(*) as vendas,
    SUM(valor) as receita,
    AVG(valor) as ticket_medio
FROM vw_vendas_ativas 
WHERE data_venda >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY corretor
ORDER BY receita DESC;

-- 2. Evolução por dia
SELECT 
    data_venda,
    COUNT(*) as vendas,
    SUM(valor) as receita
FROM vw_vendas_ativas 
WHERE data_venda >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY data_venda
ORDER BY data_venda;
```

### Cenário 3: Troubleshooting Erro

#### Objetivo
Resolver erro de sincronização da API.

#### Passos
```bash
# 1. Verificar logs
tail -f cvcrm_etl.log

# 2. Testar API manualmente
curl -H "email: $CVCRM_API_EMAIL" \
     -H "token: $CVCRM_API_TOKEN" \
     "https://bpincorporadora.cvcrm.com.br/api/v1/cvdw/reservas?page=1&per_page=5"

# 3. Verificar banco
python test_database.py

# 4. Executar sync individual
python test_sync_individual.py
```

### Cenário 4: Deploy Nova Versão

#### Objetivo
Fazer deploy de uma nova versão no Railway.

#### Passos
```bash
# 1. Testar localmente
python main.py
python monitoring.py

# 2. Executar todos os testes
python test_production.py

# 3. Commit mudanças
git add .
git commit -m "Update: nova feature"
git push

# 4. Verificar deploy no Railway
# Dashboard Railway > Deployments

# 5. Testar produção
curl https://seu-app.railway.app/health
```

## Integração com Ferramentas BI

### Power BI

#### Configuração
1. **Get Data** > **PostgreSQL**
2. **Server**: `hostname.neon.tech:5432`
3. **Database**: `neondb`
4. **Username/Password**: credenciais Neon

#### Views Recomendadas
```sql
-- Use estas views para melhor performance
SELECT * FROM vw_vendas_ativas;
SELECT * FROM vw_kpis_vendas;
SELECT * FROM vw_vendas_mes_atual;
```

### Google Looker Studio

#### Configuração
1. **Add Data** > **PostgreSQL**
2. **Hostname**: `hostname.neon.tech`
3. **Port**: `5432`
4. **Database**: `neondb`
5. **SSL**: **Required**

#### Queries Otimizadas
```sql
-- Dashboard principal
SELECT 
    corretor,
    empreendimento,
    SUM(valor) as receita,
    COUNT(*) as vendas,
    AVG(valor) as ticket_medio
FROM vw_vendas_ativas
GROUP BY corretor, empreendimento;
```

### Excel / Google Sheets

#### Conexão ODBC
1. **Instalar driver PostgreSQL ODBC**
2. **Configurar DSN**:
   - Server: `hostname.neon.tech`
   - Port: `5432`
   - Database: `neondb`
   - SSL Mode: `require`

#### Fórmulas Úteis
```excel
# Conectar dados
=IMPORTDATA("https://seu-app.railway.app/api/kpis")

# Atualizar automático
=IMPORTXML("https://seu-app.railway.app/api/sales","//vendas")
```

## FAQ - Perguntas Frequentes

### Como verificar se o sistema está funcionando?
```bash
# Health check
curl https://seu-app.railway.app/health

# Resposta esperada
{"status": "healthy", "database": "connected", "api": "accessible"}
```

### Como forçar uma sincronização manual?
```bash
# Local
python main.py

# Produção (Railway CLI)
railway run python main.py
```

### Como verificar os últimos dados sincronizados?
```sql
SELECT 
    MAX(created_at) as ultima_sincronizacao,
    COUNT(*) as total_registros
FROM vendas;
```

### Como resolver erro de "SSL connection required"?
```env
# Adicionar SSL na string de conexão
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

### Como aumentar performance da sincronização?
```python
# Reduzir batch size
BATCH_SIZE = 10

# Aumentar timeout
REQUEST_TIMEOUT = 60

# Adicionar índices
CREATE INDEX idx_vendas_data ON vendas(data_venda);
```

### Como configurar alertas por email?
```env
# Configurar no .env
ALERT_EMAIL_USER=alertas@empresa.com
ALERT_EMAIL_PASSWORD=senha_app_especifica
ALERT_EMAIL_TO=admin@empresa.com
```

### Como acessar dados via API?
```bash
# KPIs gerais
curl https://seu-app.railway.app/api/kpis

# Vendas dos últimos 30 dias
curl https://seu-app.railway.app/api/sales?periodo=30

# Health check
curl https://seu-app.railway.app/health
```

### Como fazer backup dos dados?
```bash
# Backup completo
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Backup apenas vendas
pg_dump $DATABASE_URL -t vendas > vendas_backup.sql
```

### Como restaurar backup?
```bash
# Restaurar completo
psql $DATABASE_URL < backup_20240815.sql

# Restaurar apenas vendas
psql $DATABASE_URL < vendas_backup.sql
```

### Como monitorar uso de recursos?
```bash
# Railway dashboard
railway status

# Logs em tempo real
railway logs --tail

# Métricas CPU/RAM
railway metrics
```
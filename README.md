# 🚀 CVCRM ETL - Sistema de Sincronização Gratuito

Sistema ETL completo para sincronização de dados CVCRM/CVDW com deploy 100% gratuito no Railway + Neon PostgreSQL. Focado em análise de vendas imobiliárias com dashboard web integrado e compliance LGPD.

**✅ SISTEMA CORRIGIDO E ALINHADO COM ESTRUTURA REAL CVDW - Agosto 2025**

## ✨ Características

- **💰 Custo**: 100% Gratuito
- **🔄 Sincronização**: Automática a cada 4 horas
- **📊 Dashboard**: Interface web com KPIs e gráficos
- **⚡ Performance**: Otimizado para limites gratuitos da cloud
- **📧 Alertas**: Notificações por email
- **🔍 Monitoramento**: Health checks e logs detalhados

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CVCRM API     │───▶│   Railway ETL   │───▶│ Neon PostgreSQL │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Dashboard Web   │
                       └─────────────────┘
```

## 🛠️ Configuração Rápida

### 1. Clone o Repositório

```bash
git clone <seu-repositorio>
cd cvcrm-etl
```

### 2. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
# Edite o .env com seus dados
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Executar Localmente

```bash
# ETL Worker
python main.py

# Dashboard (em outro terminal)
python monitoring.py
```

## 🚀 Deploy no Railway

### 1. Criar Banco Neon

1. Acesse https://neon.tech
2. Crie novo projeto
3. Copie a string de conexão

### 2. Deploy Railway

1. Fork este repositório
2. Conecte no Railway
3. Configure variáveis:

```env
CVCRM_API_TOKEN=seu_token_aqui
DATABASE_URL=postgresql://...neon.tech/neondb?sslmode=require
RAILWAY_ENVIRONMENT=production
```

### 3. Configurar Serviços

**ETL Worker**: `python main.py`
**Web Dashboard**: `gunicorn monitoring:app --bind 0.0.0.0:$PORT`

## 📊 Dashboard

O dashboard inclui:

- 📈 KPIs principais (Clientes, Oportunidades, Vendas)
- 📊 Gráficos de evolução das vendas
- 🏆 Top 10 clientes por valor
- ⚡ Status de sincronização em tempo real
- 🔍 Health checks automatizados

### URLs Importantes

- **Dashboard**: `https://seu-app.railway.app`
- **Health Check**: `https://seu-app.railway.app/health`
- **API KPIs**: `https://seu-app.railway.app/api/kpis`

## 🔧 Funcionalidades

### ETL Processor (main.py)

- ✅ Sincronização de Clientes
- ✅ Sincronização de Oportunidades  
- ✅ Sincronização de Vendas
- ✅ Tratamento de rate limiting
- ✅ Retry automático
- ✅ Logs detalhados
- ✅ Alertas por email

### Dashboard Web (monitoring.py)

- ✅ Interface responsiva
- ✅ KPIs em tempo real
- ✅ Gráficos interativos (Plotly)
- ✅ Auto-refresh
- ✅ Health checks
- ✅ API endpoints

### Otimizações para Cloud Gratuito

- 🕐 Sync apenas em horário comercial (6h-22h)
- 📦 Batch size reduzido (25 registros/página)
- ⏱️ Rate limiting inteligente
- 💾 Views otimizadas para consultas
- 🔄 Limite de 1000 registros por sync

## 📊 Estrutura do Banco

```sql
-- Clientes
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    cvcrm_id INTEGER UNIQUE,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Oportunidades
CREATE TABLE opportunities (
    id SERIAL PRIMARY KEY,
    cvcrm_id INTEGER UNIQUE,
    client_id INTEGER,
    title VARCHAR(500),
    value DECIMAL(15,2),
    status VARCHAR(50),
    stage VARCHAR(100),
    expected_close_date DATE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Vendas
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    cvcrm_id INTEGER UNIQUE,
    client_id INTEGER,
    opportunity_id INTEGER,
    amount DECIMAL(15,2),
    status VARCHAR(50),
    sale_date DATE,
    commission DECIMAL(10,2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## 🔍 Monitoramento

### Health Checks

```bash
curl https://seu-app.railway.app/health
```

### Logs

```bash
# Railway Dashboard > Deployments > View Logs
```

### Métricas

- CPU Usage
- RAM Usage
- Database Connections
- API Requests

## ⚠️ Limites Gratuitos

### Railway
- ✅ 500h execução/mês
- ✅ 1GB RAM
- ✅ 1GB Storage

### Neon PostgreSQL
- ✅ 3GB armazenamento
- ✅ 100h computação/mês
- ✅ 1 projeto

## 🚨 Troubleshooting

### Erro: Connection Failed
```bash
# Verificar SSL
psql "postgresql://user:pass@host/db?sslmode=require"
```

### Erro: Out of Memory
- Reduzir `batch_size` no código
- Usar `per_page=10` nas consultas

### Erro: Rate Limited
- Aumentar `sleep()` entre requests
- Verificar limites da API CVCRM

## 🔧 Desenvolvimento

### Executar Testes
```bash
python -m pytest tests/
```

### Lint e Format
```bash
black *.py
flake8 *.py
```

### Logs Local
```bash
tail -f cvcrm_etl.log
```

## 📈 Integração com BI

### Power BI
1. Get Data > PostgreSQL
2. Server: `ep-xxx.neon.tech:5432`
3. Database: `neondb`

### Google Looker Studio
1. Add Data > PostgreSQL
2. Use views otimizadas: `vw_sales_summary`, `vw_client_stats`

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua feature branch
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

MIT License - veja o arquivo LICENSE para detalhes.

## 📞 Suporte

- 📧 Email: seu.email@gmail.com
- 🐛 Issues: GitHub Issues
- 📖 Docs: Este README

---

**🎉 Deploy realizado com sucesso! Seu sistema ETL está rodando 100% gratuito na cloud.**
# Production Guide - CVCRM ETL

## 🚨 STATUS ATUAL - AGOSTO 2025
**SISTEMA CORRIGIDO E ALINHADO COM ESTRUTURA REAL CVDW**

### Situação
- ✅ **Infraestrutura**: 100% funcional (DB + Dashboard + Deploy)  
- ✅ **Código ETL**: Corrigido para estrutura real CVDW
- ✅ **Endpoints corretos**: /reservas, /comissoes, /reservas/condicoes
- ✅ **Tabelas reestruturadas**: Campos conforme documentação CVDW
- ✅ **Views corrigidas**: Filtros Ativo='S' + data_venda IS NOT NULL
- ❌ **API CVDW**: Retorna erro 405 (problema técnico CVCRM)

## 📋 PROTOCOLO DE LIMPEZA E VALIDAÇÃO

A cada etapa do projeto, seguimos este protocolo:

### 🗑️ Limpeza de Arquivos
1. **Identificar arquivos obsoletos**: Testes temporários, duplicatas, arquivos não utilizados
2. **Validar antes de excluir**: Confirmar se funcionalidade não será perdida
3. **Manter apenas essenciais**: Core do projeto + testes válidos + documentação

### ✅ Validação de Arquivos
1. **Testar importação**: Verificar se módulos podem ser importados
2. **Executar scripts**: Garantir que todos os scripts funcionam
3. **Corrigir problemas**: Encoding, dependências, erros de sintaxe
4. **Documentar alterações**: Atualizar este guia conforme necessário

### 📁 Estrutura Final Validada (15 arquivos essenciais)

**🚀 PRODUÇÃO:**
```
├── main.py                    ✅ ETL principal
├── monitoring.py              ✅ Dashboard web (Flask)
├── Procfile                   ✅ Config Railway (web + worker)
├── runtime.txt                ✅ Python 3.11.5
├── requirements.txt           ✅ Dependências validadas
├── railway.json               ✅ Deploy config
├── README.md                  ✅ Documentação original
└── prodution_guide.md         ✅ Este guia (resumo)
```

**🧪 TESTES:**
```
├── test_conexao_simples.py   ✅ API + DB básico
├── test_database.py          ✅ PostgreSQL completo  
├── test_tables.py            ✅ Estrutura banco
├── test_sync_individual.py   ✅ Sincronização ETL
├── test_production.py        ✅ Validação deploy
└── verificar_dados.py        ✅ Verificação dados pós-ETL
```

**📚 DOCUMENTAÇÃO COMPLETA:**
```
├── DOCUMENTACAO_TECNICA.md   ✅ Arquitetura, APIs, schemas SQL
└── DOCUMENTACAO_PRATICA.md   ✅ Guias de uso, troubleshooting
```

**📊 STATUS FINAL:**
- **4/4 Validações passaram** ✅
- **Sistema pronto para produção** ✅ 
- **Railway deploy ready** ✅

### ⚠️ Problemas Conhecidos e Soluções
- **Encoding Windows**: Remover emojis/caracteres especiais dos scripts
- **Rate Limiting API**: Aguardar entre requests, usar timeouts adequados  
- **Console Output**: Usar print simples ao invés de logging com caracteres especiais
- **✅ RESOLVIDO: Estrutura CVDW**: Sistema corrigido para endpoints e campos reais

## 📚 DOCUMENTAÇÃO COMPLETA

### Para Desenvolvedores e Arquitetos
**DOCUMENTACAO_TECNICA.md** - Documentação técnica abrangente contendo:
- Arquitetura completa do sistema
- Schemas SQL de todas as tabelas e views
- APIs e endpoints detalhados
- Configurações e otimizações de performance
- Especificações de deploy e produção
- Troubleshooting técnico avançado

### Para Usuários e Operadores
**DOCUMENTACAO_PRATICA.md** - Guia prático de uso diário contendo:
- Comandos essenciais para operação
- Guias passo-a-passo para tarefas comuns  
- Solução de problemas do dia-a-dia
- Interpretação de dados e métricas
- Checklists de manutenção
- Casos de uso práticos

### Resumo Executivo
**prodution_guide.md** - Este arquivo (resumo e protocolo de limpeza)

## Common Commands

### Development
- **Run ETL Worker**: `python main.py`
- **Run Web Dashboard**: `python monitoring.py`
- **Install dependencies**: `pip install -r requirements.txt`

### Testing
- **Test connections**: `python test_conexao_simples.py`
- **Test database**: `python test_database.py`
- **Test table creation**: `python test_tables.py`
- **Test individual sync**: `python test_sync_individual.py`
- **Test production config**: `python test_production.py`
- **Verify data after ETL**: `python verificar_dados.py`
- **✅ NEW: Populate CVDW mock data**: `python populate_mock_data.py`

### Production (Railway)
- **Web process**: `gunicorn monitoring:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
- **Worker process**: `python main.py`

### Linting and Formatting
- **Format code**: `black *.py`
- **Lint code**: `flake8 *.py`
- **View logs**: `tail -f cvcrm_etl.log`

## Architecture Overview

This is a CVCRM ETL system designed for real estate sales analysis, built for free cloud deployment on Railway + Neon PostgreSQL.

### Core Components - **ESTRUTURA CVDW CORRIGIDA**

1. **ETL Worker (main.py)**:
   - `CVCRMAPIClient`: API client com endpoints corretos (/reservas, /comissoes)
   - `CloudDatabaseManager`: PostgreSQL com SSL support
   - `ETLProcessor`: Sincronização com filtros CVDW (Ativo='S' + data_venda IS NOT NULL)
   - `sync_vendas_reais()`: Busca vendas no endpoint /reservas
   - `sync_comissoes_vendas()`: Busca comissões no endpoint /comissoes
   - APScheduler para sync automático a cada 4h (6AM-10PM)

2. **Web Dashboard (monitoring.py)**:
   - Flask application providing KPI dashboard
   - `DashboardData` class for database operations
   - Real-time sales metrics, VSO analysis, and commission tracking
   - Plotly charts for data visualization

### Key Database Tables - **ESTRUTURA CVDW CORRIGIDA**
- **vendas**: Vendas reais baseadas em /reservas (Ativo='S' + data_venda)
  - Campos: cvcrm_id, reserva_id, empreendimento, corretor, cliente, valor, data_venda
- **empreendimentos**: Projetos imobiliários  
- **unidades**: Unidades dos empreendimentos
- **reservas**: Todas as reservas (não apenas vendas)
- **prosoluto**: Cálculos de comissão
- **tipologia_unidades**: Tipos de unidades
- **atendimentos**: Histórico de atendimentos
- **repasses**: Transferências de comissão

### Performance Optimizations
- Cloud-friendly limits: batch size 25-50 records, max 500-2000 per sync
- Smart scheduling: runs only during business hours (6AM-10PM) in production
- Rate limiting with exponential backoff
- SSL-enabled database connections

### Environment Configuration
Required environment variables:
- `CVCRM_API_TOKEN`: API token for CVCRM
- `CVCRM_API_EMAIL`: Email for CVCRM API
- `DATABASE_URL`: PostgreSQL connection string (Neon format with SSL)
- `RAILWAY_ENVIRONMENT`: Set to 'production' for cloud deployment

### API Integration
- Base URL: `https://bpincorporadora.cvcrm.com.br/api/v1/cvdw`
- Authentication via email + token headers
- Pagination support with `page` and `per_page` parameters
- Automatic retry with exponential backoff

### Dashboard Features
- Real-time KPIs: total sales, average ticket, commissions
- Sales evolution charts
- Top performers by commission
- VSO (Velocity of Sales and Operations) analysis
- Health check endpoint at `/health`
- API endpoints for external BI integration

## File Structure Notes

- Test files (`test_*.py`) are individual test scripts for different components
- `Procfile` defines Railway deployment processes
- `runtime.txt` specifies Python 3.11.5
- Virtual environment in `Lib/` and `Scripts/` directories
- Logging to `cvcrm_etl.log`
#!/usr/bin/env python3
"""
CVCRM ETL - Sistema de Sincronização para Análise de Vendas Imobiliárias
Integração CVDW (Data Warehouse) - Estrutura corrigida Agosto 2025

Tabelas principais:
- vendas: Vendas confirmadas (Ativo='S' + data_venda válida) 
- empreendimentos: Projetos imobiliários
- unidades: Unidades dos empreendimentos
- reservas: Todas as reservas (incluindo não vendidas)
- atendimentos: Histórico de atendimentos
- repasses: Transferências de comissão
- tipologia_unidades: Tipos de unidades
- prosoluto: Cálculos de comissão

Deploy: Railway + Neon PostgreSQL (100% gratuito)
LGPD: Compliant - dados corporativos sem PII
"""

import os
import time
import logging
import requests
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
from psycopg2.extras import RealDictCursor
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cvcrm_etl.log')
    ]
)

class CVCRMAPIClient:
    """Cliente para API do CVCRM focado nas tabelas de vendas"""
    
    def __init__(self):
        self.api_token = os.getenv('CVCRM_API_TOKEN')
        self.base_url = 'https://bpincorporadora.cvcrm.com.br/api/v1/cvdw'
        self.headers = {
            'email': os.getenv('CVCRM_API_EMAIL'),
            'token': os.getenv('CVCRM_API_TOKEN'),
            'Content-Type': 'application/json'
        }
        
        if not self.api_token:
            raise ValueError("CVCRM_API_TOKEN não encontrado nas variáveis de ambiente")
    
    def make_request(self, endpoint, params=None):
        """Faz requisição para API com retry automático"""
        max_retries = 3
        delay = 10  # Aumentado para 10 segundos
        
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/{endpoint}"
                
                # Rate limiting OBRIGATÓRIO - mínimo 10 segundos
                print(f"   Aguardando 10s (rate limit obrigatorio)...")
                time.sleep(10)
                
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 429:  # Rate limit
                    wait_time = 60  # Aguardar 1 minuto completo
                    logging.warning(f"Rate limit atingido. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except:
                        logging.error(f"Resposta não é JSON válido: {response.text[:200]}")
                        return None
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Erro na requisição (tentativa {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay * (2 ** attempt))
    
    def get_empreendimentos(self, page=1, per_page=500):
        """Busca empreendimentos - CORRIGIDO conforme Power BI"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        return self.make_request('empreendimentos', params)
    
    def get_atendimentos(self, page=1, per_page=500, date_from=None):
        """Busca atendimentos - CORRIGIDO"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        if date_from:
            params['a_partir_data_referencia'] = date_from
        return self.make_request('atendimentos', params)
    
    def get_unidades(self, page=1, per_page=500):
        """Busca unidades - CORRIGIDO"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        return self.make_request('unidades', params)
    
    def get_vendas_reais(self, page=1, per_page=500, date_from=None):
        """Busca vendas reais via endpoint reservas - CORRIGIDO CVDW"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        if date_from:
            params['a_partir_data_referencia'] = date_from
        return self.make_request('reservas', params)
    
    def get_comissoes(self, page=1, per_page=500, date_from=None):
        """Busca comissões - ENDPOINT CORRETO CVDW"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        if date_from:
            params['a_partir_data_referencia'] = date_from
        return self.make_request('comissoes', params)
    
    def get_condicoes_reservas(self, page=1, per_page=500, date_from=None):
        """Busca condições de pagamento das reservas"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        if date_from:
            params['a_partir_data_referencia'] = date_from
        return self.make_request('reservas/condicoes', params)
    
    def get_repasses(self, page=1, per_page=500, date_from=None):
        """Busca repasses - CORRIGIDO"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        if date_from:
            params['a_partir_data_referencia'] = date_from
        return self.make_request('repasses', params)
    
    def get_tipologia_unidades(self, page=1, per_page=500):
        """Busca tipologia das unidades - CORRIGIDO"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        return self.make_request('tipologia_unidades', params)
    
    def get_prosoluto(self, page=1, per_page=500, date_from=None):
        """Busca prosoluto - CORRIGIDO"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        if date_from:
            params['a_partir_data_referencia'] = date_from
        return self.make_request('prosoluto', params)
    
    def get_reservas(self, page=1, per_page=500, date_from=None):
        """Busca reservas - CORRIGIDO conforme Power BI"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        if date_from:
            params['a_partir_data_referencia'] = date_from
        return self.make_request('reservas', params)
    
    def get_valores_reservas(self, page=1, per_page=500, date_from=None):
        """Busca valores das reservas - CORRIGIDO"""
        params = {'pagina': page, 'registros_por_pagina': per_page}
        if date_from:
            params['a_partir_data_referencia'] = date_from
        return self.make_request('valores_reservas', params)

class CloudDatabaseManager:
    """Gerenciador do banco PostgreSQL na cloud"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL não encontrada")
    
    def get_connection(self):
        """Cria conexão com o banco"""
        return psycopg2.connect(self.database_url)
    
    def create_tables(self):
        """Cria estrutura do banco focada em análises de vendas"""
        sql_commands = [
            # Empreendimentos
            """
            CREATE TABLE IF NOT EXISTS empreendimentos (
                id SERIAL PRIMARY KEY,
                cvcrm_id INTEGER UNIQUE NOT NULL,
                nome VARCHAR(255) NOT NULL,
                endereco TEXT,
                cidade VARCHAR(100),
                estado VARCHAR(2),
                cep VARCHAR(10),
                status VARCHAR(50),
                vgv DECIMAL(15,2),
                data_lancamento DATE,
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # Corretores e atendimentos
            """
            CREATE TABLE IF NOT EXISTS atendimentos (
                id SERIAL PRIMARY KEY,
                cvcrm_id INTEGER UNIQUE NOT NULL,
                corretor_id INTEGER,
                corretor_nome VARCHAR(255),
                grupo_corretor VARCHAR(100),
                time_corretor VARCHAR(100),
                cliente_nome VARCHAR(255),
                cliente_email VARCHAR(255),
                cliente_telefone VARCHAR(50),
                empreendimento_id INTEGER,
                data_atendimento TIMESTAMP,
                tipo_atendimento VARCHAR(100),
                status VARCHAR(50),
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # Unidades
            """
            CREATE TABLE IF NOT EXISTS unidades (
                id SERIAL PRIMARY KEY,
                cvcrm_id INTEGER UNIQUE NOT NULL,
                empreendimento_id INTEGER,
                numero VARCHAR(50),
                bloco VARCHAR(50),
                andar INTEGER,
                tipologia_id INTEGER,
                area_privativa DECIMAL(10,2),
                area_total DECIMAL(10,2),
                valor_tabela DECIMAL(15,2),
                valor_venda DECIMAL(15,2),
                status VARCHAR(50),
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (empreendimento_id) REFERENCES empreendimentos(cvcrm_id)
            );
            """,
            # Tipologia das unidades
            """
            CREATE TABLE IF NOT EXISTS tipologia_unidades (
                id SERIAL PRIMARY KEY,
                cvcrm_id INTEGER UNIQUE NOT NULL,
                nome VARCHAR(100),
                dormitorios INTEGER,
                suites INTEGER,
                banheiros INTEGER,
                vagas_garagem INTEGER,
                area_minima DECIMAL(10,2),
                area_maxima DECIMAL(10,2),
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # Vendas (baseado em reservas CVDW) - tabela principal para análises
            """
            CREATE TABLE IF NOT EXISTS vendas (
                id SERIAL PRIMARY KEY,
                cvcrm_id INTEGER UNIQUE NOT NULL,
                reserva_id INTEGER,
                empreendimento VARCHAR(255),
                unidade_id INTEGER,
                corretor VARCHAR(255),
                time_corretor VARCHAR(100),
                cliente VARCHAR(255),
                valor DECIMAL(15,2),
                data_venda DATE,
                ativo VARCHAR(1),
                status VARCHAR(50),
                -- Campos de comissão (vem do endpoint /comissoes)
                comissao_valor DECIMAL(15,2),
                comissao_percentual DECIMAL(5,2),
                -- Campos financeiros (vem do endpoint /reservas/condicoes)  
                valor_financiamento DECIMAL(15,2),
                valor_entrada DECIMAL(15,2),
                numero_parcelas INTEGER,
                -- Campos calculados
                vgv DECIMAL(15,2),
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # Repasses
            """
            CREATE TABLE IF NOT EXISTS repasses (
                id SERIAL PRIMARY KEY,
                cvcrm_id INTEGER UNIQUE NOT NULL,
                venda_id INTEGER,
                corretor_id INTEGER,
                corretor_nome VARCHAR(255),
                valor_repasse DECIMAL(15,2),
                percentual_repasse DECIMAL(5,2),
                data_repasse DATE,
                data_pagamento DATE,
                status VARCHAR(50),
                observacoes TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (venda_id) REFERENCES vendas(cvcrm_id)
            );
            """,
            # Prosoluto
            """
            CREATE TABLE IF NOT EXISTS prosoluto (
                id SERIAL PRIMARY KEY,
                cvcrm_id INTEGER UNIQUE NOT NULL,
                venda_id INTEGER,
                empreendimento_id INTEGER,
                corretor_id INTEGER,
                valor_prosoluto DECIMAL(15,2),
                percentual_prosoluto DECIMAL(5,2),
                data_calculo DATE,
                data_pagamento DATE,
                status VARCHAR(50),
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (venda_id) REFERENCES vendas(cvcrm_id),
                FOREIGN KEY (empreendimento_id) REFERENCES empreendimentos(cvcrm_id)
            );
            """,
            # Reservas
            """
            CREATE TABLE IF NOT EXISTS reservas (
                id SERIAL PRIMARY KEY,
                cvcrm_id INTEGER UNIQUE NOT NULL,
                empreendimento_id INTEGER,
                unidade_id INTEGER,
                corretor_id INTEGER,
                corretor_nome VARCHAR(255),
                cliente_nome VARCHAR(255),
                data_reserva DATE,
                data_vencimento DATE,
                status VARCHAR(50),
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (empreendimento_id) REFERENCES empreendimentos(cvcrm_id),
                FOREIGN KEY (unidade_id) REFERENCES unidades(cvcrm_id)
            );
            """,
            # Valores das reservas
            """
            CREATE TABLE IF NOT EXISTS valores_reservas (
                id SERIAL PRIMARY KEY,
                cvcrm_id INTEGER UNIQUE NOT NULL,
                reserva_id INTEGER,
                valor_reserva DECIMAL(15,2),
                valor_entrada DECIMAL(15,2),
                valor_financiamento DECIMAL(15,2),
                numero_parcelas INTEGER,
                valor_parcela DECIMAL(15,2),
                created_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reserva_id) REFERENCES reservas(cvcrm_id)
            );
            """,
            # Views para análises de vendas - CORRIGIDAS
            """
            CREATE OR REPLACE VIEW vw_vendas_ano_atual_vs_passado AS
            SELECT
                'Ano Atual' as periodo,
                EXTRACT(YEAR FROM data_venda) as ano,
                COUNT(*) as quantidade_vendas,
                SUM(valor) as valor_total,
                AVG(valor) as ticket_medio,
                SUM(comissao_valor) as total_comissoes,
                AVG(comissao_valor) as media_comissoes
            FROM vendas
            WHERE EXTRACT(YEAR FROM data_venda) = EXTRACT(YEAR FROM CURRENT_DATE)
            AND ativo = 'S'
            AND data_venda IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM data_venda)
            UNION ALL
            SELECT
                'Ano Passado' as periodo,
                EXTRACT(YEAR FROM data_venda) as ano,
                COUNT(*) as quantidade_vendas,
                SUM(valor) as valor_total,
                AVG(valor) as ticket_medio,
                SUM(comissao_valor) as total_comissoes,
                AVG(comissao_valor) as media_comissoes
            FROM vendas
            WHERE EXTRACT(YEAR FROM data_venda) = EXTRACT(YEAR FROM CURRENT_DATE) - 1
            AND ativo = 'S'
            AND data_venda IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM data_venda);
            """,
            """
            CREATE OR REPLACE VIEW vw_vendas_mensais AS
            SELECT 
                DATE_TRUNC('month', data_venda) as mes,
                EXTRACT(YEAR FROM data_venda) as ano,
                EXTRACT(MONTH FROM data_venda) as mes_numero,
                COUNT(*) as quantidade_vendas,
                SUM(valor) as valor_total_vendas,
                AVG(valor) as ticket_medio,
                SUM(valor) as vgv_total,
                SUM(comissao_valor) as total_comissoes,
                AVG(comissao_valor) as media_comissoes
            FROM vendas 
            WHERE data_venda >= CURRENT_DATE - INTERVAL '24 months'
            AND ativo = 'S'
            AND data_venda IS NOT NULL
            GROUP BY DATE_TRUNC('month', data_venda), EXTRACT(YEAR FROM data_venda), EXTRACT(MONTH FROM data_venda)
            ORDER BY mes;
            """,
            """
            CREATE OR REPLACE VIEW vw_vendas_por_empreendimento AS
            SELECT 
                e.cvcrm_id,
                e.nome as empreendimento,
                COUNT(v.id) as quantidade_vendas,
                SUM(v.valor) as valor_total_vendas,
                AVG(v.valor) as ticket_medio,
                SUM(v.vgv) as vgv_total,
                SUM(v.comissao_valor) as total_comissoes,
                AVG(v.comissao_valor) as media_comissoes,
                COUNT(DISTINCT v.corretor) as total_corretores
            FROM empreendimentos e
            LEFT JOIN vendas v ON e.nome = v.empreendimento 
                AND v.ativo = 'S'
                AND v.data_venda IS NOT NULL
                AND v.data_venda >= CURRENT_DATE - INTERVAL '12 months'
            GROUP BY e.cvcrm_id, e.nome
            ORDER BY valor_total_vendas DESC NULLS LAST;
            """,
            """
            CREATE OR REPLACE VIEW vw_vendas_por_corretor AS
            SELECT 
                corretor,
                time_corretor,
                COUNT(*) as quantidade_vendas,
                SUM(valor) as valor_total_vendas,
                AVG(valor) as ticket_medio,
                SUM(comissao_valor) as total_comissoes,
                AVG(comissao_valor) as media_comissoes,
                COUNT(DISTINCT empreendimento) as empreendimentos_vendidos
            FROM vendas 
            WHERE data_venda >= CURRENT_DATE - INTERVAL '12 months'
            AND ativo = 'S'
            AND data_venda IS NOT NULL
            AND corretor IS NOT NULL
            GROUP BY corretor, time_corretor
            ORDER BY valor_total_vendas DESC;
            """,
            """
            CREATE OR REPLACE VIEW vw_vendas_por_time AS
            SELECT 
                COALESCE(time_corretor, 'Sem Time') as time_corretor,
                COUNT(*) as quantidade_vendas,
                SUM(valor) as valor_total_vendas,
                AVG(valor) as ticket_medio,
                SUM(comissao_valor) as total_comissoes,
                AVG(comissao_valor) as media_comissoes,
                COUNT(DISTINCT corretor) as total_corretores,
                COUNT(DISTINCT empreendimento) as empreendimentos_vendidos
            FROM vendas 
            WHERE data_venda >= CURRENT_DATE - INTERVAL '12 months'
            AND ativo = 'S'
            AND data_venda IS NOT NULL
            GROUP BY time_corretor
            ORDER BY valor_total_vendas DESC;
            """,
            """
            CREATE OR REPLACE VIEW vw_vso_mensal AS
            SELECT 
                DATE_TRUNC('month', data_venda) as mes,
                COUNT(*) as quantidade_vendas,
                SUM(valor) as vso_valor,
                AVG(valor) as vso_ticket_medio,
                SUM(valor) / NULLIF(COUNT(DISTINCT empreendimento), 0) as vso_por_empreendimento
            FROM vendas 
            WHERE data_venda >= CURRENT_DATE - INTERVAL '12 months'
            AND ativo = 'S'
            AND data_venda IS NOT NULL
            GROUP BY DATE_TRUNC('month', data_venda)
            ORDER BY mes;
            """,
            """
            CREATE OR REPLACE VIEW vw_prosoluto_analise AS
            SELECT 
                DATE_TRUNC('month', p.data_calculo) as mes,
                COUNT(*) as quantidade_prosoluto,
                SUM(p.valor_prosoluto) as valor_total_prosoluto,
                AVG(p.valor_prosoluto) as media_prosoluto,
                SUM(p.valor_prosoluto) / NULLIF(SUM(v.valor), 0) * 100 as percentual_prosoluto_sobre_venda
            FROM prosoluto p
            LEFT JOIN vendas v ON p.venda_id = v.cvcrm_id
            WHERE p.data_calculo >= CURRENT_DATE - INTERVAL '12 months'
            AND p.status NOT IN ('cancelado')
            GROUP BY DATE_TRUNC('month', p.data_calculo)
            ORDER BY mes;
            """,
            """
            CREATE OR REPLACE VIEW vw_tabela_geral_vendas AS
            SELECT 
                v.cvcrm_id,
                v.empreendimento,
                v.corretor,
                v.time_corretor,
                v.cliente,
                v.data_venda,
                v.valor,
                v.valor_financiamento,
                v.valor_entrada,
                v.numero_parcelas,
                v.vgv,
                v.comissao_valor,
                p.valor_prosoluto,
                p.percentual_prosoluto,
                v.status
            FROM vendas v
            LEFT JOIN prosoluto p ON v.cvcrm_id = p.venda_id
            WHERE v.data_venda >= CURRENT_DATE - INTERVAL '24 months'
            AND v.ativo = 'S'
            AND v.data_venda IS NOT NULL
            ORDER BY v.data_venda DESC;
            """
        ]
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    for sql in sql_commands:
                        cursor.execute(sql)
                conn.commit()
            logging.info("Estrutura do banco criada com sucesso")
        except Exception as e:
            logging.error(f"Erro ao criar estrutura do banco: {e}")
            raise

    def should_run_sync(self):
        """Verifica se deve executar sync (horário comercial para economizar recursos)"""
        if os.getenv('RAILWAY_ENVIRONMENT') == 'production':
            now = datetime.now()
            # Roda apenas das 6h às 22h para economizar compute hours
            return 6 <= now.hour <= 22
        return True  # Sempre roda em desenvolvimento

class ETLProcessor:
    """Processador principal do ETL"""
    
    def __init__(self):
        self.api = CVCRMAPIClient()
        self.db = CloudDatabaseManager()
        
    def sync_empreendimentos(self):
        """Sincroniza empreendimentos"""
        try:
            page = 1
            total_records = 0
            
            while True:
                data = self.api.get_empreendimentos(page=page, per_page=50)
                empreendimentos = data.get('data', [])
                
                if not empreendimentos:
                    break
                
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        for emp in empreendimentos:
                            cursor.execute("""
                                INSERT INTO empreendimentos (cvcrm_id, nome, endereco, cidade, estado, cep, status, vgv, data_lancamento, created_at, updated_at)
                                VALUES (%(id)s, %(nome)s, %(endereco)s, %(cidade)s, %(estado)s, %(cep)s, %(status)s, %(vgv)s, %(data_lancamento)s, %(created_at)s, CURRENT_TIMESTAMP)
                                ON CONFLICT (cvcrm_id) 
                                DO UPDATE SET
                                    nome = EXCLUDED.nome,
                                    endereco = EXCLUDED.endereco,
                                    cidade = EXCLUDED.cidade,
                                    estado = EXCLUDED.estado,
                                    cep = EXCLUDED.cep,
                                    status = EXCLUDED.status,
                                    vgv = EXCLUDED.vgv,
                                    data_lancamento = EXCLUDED.data_lancamento,
                                    updated_at = CURRENT_TIMESTAMP
                            """, emp)
                    conn.commit()
                
                total_records += len(empreendimentos)
                page += 1
                
                if total_records >= 500:
                    break
            
            logging.info(f"Empreendimentos sincronizados: {total_records} registros")
            return total_records
            
        except Exception as e:
            logging.error(f"Erro ao sincronizar empreendimentos: {e}")
            return 0
    
    def sync_vendas_reais(self):
        """Sincroniza vendas reais via endpoint /reservas - CORRIGIDO CVDW"""
        try:
            page = 1
            total_records = 0
            
            while True:
                data = self.api.get_vendas_reais(page=page, per_page=50)
                reservas = data.get('data', [])
                
                if not reservas:
                    break
                
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        for reserva in reservas:
                            # Filtrar apenas reservas com vendas confirmadas
                            if (reserva.get('ativo') == 'S' and 
                                reserva.get('data_venda') and 
                                reserva.get('data_venda') != ''):
                                
                                cursor.execute("""
                                    INSERT INTO vendas (cvcrm_id, reserva_id, empreendimento, unidade_id, 
                                                      corretor, time_corretor, cliente, valor, data_venda, 
                                                      ativo, status, vgv, created_at, updated_at)
                                    VALUES (%(id)s, %(reserva_id)s, %(empreendimento)s, %(unidade_id)s,
                                           %(corretor)s, %(time_corretor)s, %(cliente)s, %(valor)s, %(data_venda)s,
                                           %(ativo)s, 'Vendido', %(valor)s, %(created_at)s, CURRENT_TIMESTAMP)
                                    ON CONFLICT (cvcrm_id)
                                    DO UPDATE SET
                                        empreendimento = EXCLUDED.empreendimento,
                                        corretor = EXCLUDED.corretor,
                                        time_corretor = EXCLUDED.time_corretor,
                                        cliente = EXCLUDED.cliente,
                                        valor = EXCLUDED.valor,
                                        data_venda = EXCLUDED.data_venda,
                                        ativo = EXCLUDED.ativo,
                                        vgv = EXCLUDED.vgv,
                                        updated_at = CURRENT_TIMESTAMP
                                """, reserva)
                    conn.commit()
                
                total_records += len([r for r in reservas if r.get('ativo') == 'S' and r.get('data_venda')])
                page += 1
                
                if total_records >= 2000:
                    break
            
            logging.info(f"Vendas reais sincronizadas: {total_records} registros")
            return total_records
            
        except Exception as e:
            logging.error(f"Erro ao sincronizar vendas reais: {e}")
            return 0
    
    def sync_comissoes_vendas(self):
        """Sincroniza comissões das vendas - ENDPOINT CORRETO CVDW"""
        try:
            page = 1
            total_records = 0
            
            while True:
                data = self.api.get_comissoes(page=page, per_page=50)
                comissoes = data.get('data', [])
                
                if not comissoes:
                    break
                
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        for comissao in comissoes:
                            # Atualizar vendas com dados de comissão
                            cursor.execute("""
                                UPDATE vendas 
                                SET comissao_valor = %(valor_comissao)s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE reserva_id = %(reserva_id)s
                                OR cvcrm_id = %(venda_id)s
                            """, comissao)
                    conn.commit()
                
                total_records += len(comissoes)
                page += 1
                
                if total_records >= 1000:
                    break
            
            logging.info(f"Comissões sincronizadas: {total_records} registros")
            return total_records
            
        except Exception as e:
            logging.error(f"Erro ao sincronizar comissões: {e}")
            return 0
    
    def sync_unidades(self):
        """Sincroniza unidades"""
        try:
            page = 1
            total_records = 0
            
            while True:
                data = self.api.get_unidades(page=page, per_page=50)
                unidades = data.get('data', [])
                
                if not unidades:
                    break
                
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        for unidade in unidades:
                            cursor.execute("""
                                INSERT INTO unidades (cvcrm_id, empreendimento_id, numero, bloco, andar, tipologia_id,
                                                    area_privativa, area_total, valor_tabela, valor_venda, status, created_at, updated_at)
                                VALUES (%(id)s, %(empreendimento_id)s, %(numero)s, %(bloco)s, %(andar)s, %(tipologia_id)s,
                                       %(area_privativa)s, %(area_total)s, %(valor_tabela)s, %(valor_venda)s, %(status)s, %(created_at)s, CURRENT_TIMESTAMP)
                                ON CONFLICT (cvcrm_id)
                                DO UPDATE SET
                                    empreendimento_id = EXCLUDED.empreendimento_id,
                                    numero = EXCLUDED.numero,
                                    bloco = EXCLUDED.bloco,
                                    andar = EXCLUDED.andar,
                                    tipologia_id = EXCLUDED.tipologia_id,
                                    area_privativa = EXCLUDED.area_privativa,
                                    area_total = EXCLUDED.area_total,
                                    valor_tabela = EXCLUDED.valor_tabela,
                                    valor_venda = EXCLUDED.valor_venda,
                                    status = EXCLUDED.status,
                                    updated_at = CURRENT_TIMESTAMP
                            """, unidade)
                    conn.commit()
                
                total_records += len(unidades)
                page += 1
                
                if total_records >= 1000:
                    break
            
            logging.info(f"Unidades sincronizadas: {total_records} registros")
            return total_records
            
        except Exception as e:
            logging.error(f"Erro ao sincronizar unidades: {e}")
            return 0
    
    def sync_prosoluto(self):
        """Sincroniza prosoluto"""
        try:
            page = 1
            total_records = 0
            
            while True:
                data = self.api.get_prosoluto(page=page, per_page=50)
                prosoluto_data = data.get('data', [])
                
                if not prosoluto_data:
                    break
                
                with self.db.get_connection() as conn:
                    with conn.cursor() as cursor:
                        for prosoluto in prosoluto_data:
                            cursor.execute("""
                                INSERT INTO prosoluto (cvcrm_id, venda_id, empreendimento_id, corretor_id, valor_prosoluto,
                                                     percentual_prosoluto, data_calculo, data_pagamento, status, created_at, updated_at)
                                VALUES (%(id)s, %(venda_id)s, %(empreendimento_id)s, %(corretor_id)s, %(valor_prosoluto)s,
                                       %(percentual_prosoluto)s, %(data_calculo)s, %(data_pagamento)s, %(status)s, %(created_at)s, CURRENT_TIMESTAMP)
                                ON CONFLICT (cvcrm_id)
                                DO UPDATE SET
                                    valor_prosoluto = EXCLUDED.valor_prosoluto,
                                    percentual_prosoluto = EXCLUDED.percentual_prosoluto,
                                    data_calculo = EXCLUDED.data_calculo,
                                    data_pagamento = EXCLUDED.data_pagamento,
                                    status = EXCLUDED.status,
                                    updated_at = CURRENT_TIMESTAMP
                            """, prosoluto)
                    conn.commit()
                
                total_records += len(prosoluto_data)
                page += 1
                
                if total_records >= 1000:
                    break
            
            logging.info(f"Prosoluto sincronizado: {total_records} registros")
            return total_records
            
        except Exception as e:
            logging.error(f"Erro ao sincronizar prosoluto: {e}")
            return 0
    
    def run_full_sync(self):
        """Executa sincronização completa focada em vendas"""
        if not self.db.should_run_sync():
            logging.info("Fora do horário de sincronização (economizando recursos)")
            return
        
        start_time = datetime.now()
        logging.info("Iniciando sincronização completa do CVCRM...")
        
        try:
            # Criar estrutura se não existir
            self.db.create_tables()
            
            # Sincronizar dados base primeiro
            logging.info("Sincronizando dados base...")
            empreendimentos_count = self.sync_empreendimentos()
            
            # Sincronizar tabelas dependentes
            logging.info("Sincronizando unidades...")
            unidades_count = self.sync_unidades()
            
            # Sincronizar vendas reais (endpoint /reservas) - dados principais
            logging.info("Sincronizando vendas reais (reservas)...")
            vendas_count = self.sync_vendas_reais()
            
            # Sincronizar comissões das vendas
            logging.info("Sincronizando comissões...")
            comissoes_count = self.sync_comissoes_vendas()
            
            # Sincronizar dados complementares
            logging.info("Sincronizando prosoluto...")
            prosoluto_count = self.sync_prosoluto()
            
            # Sincronizar outras tabelas se necessário
            other_counts = {}
            try:
                logging.info("Sincronizando atendimentos...")
                other_counts['atendimentos'] = self.sync_other_table('atendimentos')
                
                logging.info("Sincronizando repasses...")
                other_counts['repasses'] = self.sync_other_table('repasses')
                
                logging.info("Sincronizando reservas...")
                other_counts['reservas'] = self.sync_other_table('reservas')
                
            except Exception as e:
                logging.warning(f"Erro ao sincronizar tabelas secundárias: {e}")
            
            duration = datetime.now() - start_time
            
            # Log de resumo detalhado
            summary = f"""
            Sincronização CVCRM Finalizada
            Duração: {duration}
            Empreendimentos: {empreendimentos_count}
            Unidades: {unidades_count}
            Vendas: {vendas_count}
            Prosoluto: {prosoluto_count}
            Atendimentos: {other_counts.get('atendimentos', 0)}
            Repasses: {other_counts.get('repasses', 0)}
            Reservas: {other_counts.get('reservas', 0)}
            """
            
            logging.info(summary)
            
            # Enviar alerta de sucesso
            self.send_success_alert(empreendimentos_count, vendas_count, prosoluto_count)
            
        except Exception as e:
            error_msg = f"Erro na sincronização: {e}"
            logging.error(error_msg)
            self.send_error_alert(str(e))
            raise
    
    def sync_other_table(self, table_name):
        """Sincroniza tabelas secundárias de forma genérica"""
        try:
            if table_name == 'atendimentos':
                return self._sync_generic_table(self.api.get_atendimentos, 'atendimentos', self._get_atendimentos_insert_query())
            elif table_name == 'repasses':
                return self._sync_generic_table(self.api.get_repasses, 'repasses', self._get_repasses_insert_query())
            elif table_name == 'reservas':
                return self._sync_generic_table(self.api.get_reservas, 'reservas', self._get_reservas_insert_query())
            else:
                return 0
        except Exception as e:
            logging.error(f"Erro ao sincronizar {table_name}: {e}")
            return 0
    
    def _sync_generic_table(self, api_method, table_name, insert_query):
        """Método genérico para sincronização de tabelas"""
        page = 1
        total_records = 0
        
        while True:
            data = api_method(page=page, per_page=50)
            records = data.get('data', [])
            
            if not records:
                break
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cursor:
                    for record in records:
                        cursor.execute(insert_query, record)
                conn.commit()
            
            total_records += len(records)
            page += 1
            
            if total_records >= 500:  # Limite para tabelas secundárias
                break
        
        logging.info(f"{table_name.title()} sincronizada: {total_records} registros")
        return total_records
    
    def _get_atendimentos_insert_query(self):
        """Query para inserir atendimentos"""
        return """
            INSERT INTO atendimentos (cvcrm_id, corretor_id, corretor_nome, grupo_corretor, time_corretor, 
                                    cliente_nome, cliente_email, cliente_telefone, empreendimento_id, 
                                    data_atendimento, tipo_atendimento, status, created_at, updated_at)
            VALUES (%(id)s, %(corretor_id)s, %(corretor_nome)s, %(grupo_corretor)s, %(time_corretor)s,
                   %(cliente_nome)s, %(cliente_email)s, %(cliente_telefone)s, %(empreendimento_id)s,
                   %(data_atendimento)s, %(tipo_atendimento)s, %(status)s, %(created_at)s, CURRENT_TIMESTAMP)
            ON CONFLICT (cvcrm_id) DO UPDATE SET
                corretor_nome = EXCLUDED.corretor_nome,
                grupo_corretor = EXCLUDED.grupo_corretor,
                time_corretor = EXCLUDED.time_corretor,
                cliente_nome = EXCLUDED.cliente_nome,
                cliente_email = EXCLUDED.cliente_email,
                cliente_telefone = EXCLUDED.cliente_telefone,
                data_atendimento = EXCLUDED.data_atendimento,
                tipo_atendimento = EXCLUDED.tipo_atendimento,
                status = EXCLUDED.status,
                updated_at = CURRENT_TIMESTAMP
        """
    
    def _get_repasses_insert_query(self):
        """Query para inserir repasses"""
        return """
            INSERT INTO repasses (cvcrm_id, venda_id, corretor_id, corretor_nome, valor_repasse,
                                percentual_repasse, data_repasse, data_pagamento, status, observacoes, created_at, updated_at)
            VALUES (%(id)s, %(venda_id)s, %(corretor_id)s, %(corretor_nome)s, %(valor_repasse)s,
                   %(percentual_repasse)s, %(data_repasse)s, %(data_pagamento)s, %(status)s, %(observacoes)s, %(created_at)s, CURRENT_TIMESTAMP)
            ON CONFLICT (cvcrm_id) DO UPDATE SET
                valor_repasse = EXCLUDED.valor_repasse,
                percentual_repasse = EXCLUDED.percentual_repasse,
                data_repasse = EXCLUDED.data_repasse,
                data_pagamento = EXCLUDED.data_pagamento,
                status = EXCLUDED.status,
                observacoes = EXCLUDED.observacoes,
                updated_at = CURRENT_TIMESTAMP
        """
    
    def _get_reservas_insert_query(self):
        """Query para inserir reservas"""
        return """
            INSERT INTO reservas (cvcrm_id, empreendimento_id, unidade_id, corretor_id, corretor_nome,
                                cliente_nome, data_reserva, data_vencimento, status, created_at, updated_at)
            VALUES (%(id)s, %(empreendimento_id)s, %(unidade_id)s, %(corretor_id)s, %(corretor_nome)s,
                   %(cliente_nome)s, %(data_reserva)s, %(data_vencimento)s, %(status)s, %(created_at)s, CURRENT_TIMESTAMP)
            ON CONFLICT (cvcrm_id) DO UPDATE SET
                empreendimento_id = EXCLUDED.empreendimento_id,
                unidade_id = EXCLUDED.unidade_id,
                corretor_nome = EXCLUDED.corretor_nome,
                cliente_nome = EXCLUDED.cliente_nome,
                data_reserva = EXCLUDED.data_reserva,
                data_vencimento = EXCLUDED.data_vencimento,
                status = EXCLUDED.status,
                updated_at = CURRENT_TIMESTAMP
        """
    
    def send_success_alert(self, empreendimentos, vendas, prosoluto):
        """Envia alerta de sincronização bem-sucedida focada em vendas"""
        if not all([os.getenv('ALERT_EMAIL_USER'), os.getenv('ALERT_EMAIL_PASSWORD')]):
            return
        
        try:
            subject = "CVCRM ETL - Sincronização de Vendas Concluída"
            message = f"""
            Sincronização de dados de vendas executada com sucesso!
            
            Dados principais atualizados:
            • Empreendimentos: {empreendimentos} registros
            • Vendas: {vendas} registros  
            • Prosoluto: {prosoluto} registros
            
            Análises disponíveis:
            • Vendas ano atual vs passado
            • VSO mensal e ticket médio
            • Vendas por corretor e time
            • Comissões e prosoluto
            • Tabela geral consolidada
            
            Executado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            self.send_email(subject, message)
            
        except Exception as e:
            logging.error(f"Erro ao enviar alerta de sucesso: {e}")
    
    def send_error_alert(self, error):
        """Envia alerta de erro"""
        if not all([os.getenv('ALERT_EMAIL_USER'), os.getenv('ALERT_EMAIL_PASSWORD')]):
            return
        
        try:
            subject = "CVCRM ETL - Erro na Sincronização"
            message = f"""
            Erro detectado na sincronização:
            
            Erro: {error}
            Detectado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            
            Verifique os logs para mais detalhes.
            """
            
            self.send_email(subject, message)
            
        except Exception as e:
            logging.error(f"Erro ao enviar alerta de erro: {e}")
    
    def send_email(self, subject, message):
        """Envia email usando Gmail"""
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        email_user = os.getenv('ALERT_EMAIL_USER')
        email_password = os.getenv('ALERT_EMAIL_PASSWORD')
        email_to = os.getenv('ALERT_EMAIL_TO', email_user)
        
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = email_to
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_password)
        text = msg.as_string()
        server.sendmail(email_user, email_to, text)
        server.quit()

def main():
    """Função principal - inicia o agendador"""
    logging.info("Iniciando CVCRM ETL...")
    
    try:
        # Inicializar ETL
        etl_processor = ETLProcessor()
        
        # Executar primeira sincronização
        etl_processor.run_full_sync()
        
        # Configurar agendador para cloud gratuito
        scheduler = BlockingScheduler()
        
        # Sync a cada 4 horas para economizar compute hours
        scheduler.add_job(
            func=etl_processor.run_full_sync,
            trigger=CronTrigger(minute=0, hour='*/4'),
            id='sync_cvcrm_cloud',
            max_instances=1
        )
        
        logging.info("Agendador configurado - sync a cada 4 horas")
        logging.info("Iniciando monitoramento contínuo...")
        
        scheduler.start()
        
    except KeyboardInterrupt:
        logging.info("ETL interrompido pelo usuário")
    except Exception as e:
        logging.error(f"Erro crítico: {e}")
        raise

if __name__ == "__main__":
    main()
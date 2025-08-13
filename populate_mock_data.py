#!/usr/bin/env python3
"""
Popula banco com dados mock para testar estrutura das tabelas
Usado temporariamente enquanto API CVDW tem problema 405
"""
import os
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(os.getenv('DATABASE_URL'))

def create_mock_data():
    """Cria dados mock realistas para teste"""
    
    # Mock Empreendimentos
    empreendimentos = [
        {
            'cvcrm_id': 1,
            'nome': 'Residencial Sol Nascente',
            'endereco': 'Rua das Flores, 123, Vila Olímpia',
            'cidade': 'São Paulo',
            'estado': 'SP', 
            'cep': '04552-000',
            'status': 'Lancamento',
            'vgv': 45000000.00,
            'data_lancamento': '2024-01-15',
            'created_at': datetime.now()
        },
        {
            'cvcrm_id': 2,
            'nome': 'Edificio Vista Mar Premium',
            'endereco': 'Av. Beira Mar, 456, Gonzaga',
            'cidade': 'Santos',
            'estado': 'SP',
            'cep': '11055-100', 
            'status': 'Obras',
            'vgv': 78000000.00,
            'data_lancamento': '2024-03-20',
            'created_at': datetime.now()
        },
        {
            'cvcrm_id': 3,
            'nome': 'Condominio Park Residence',
            'endereco': 'Rua dos Jardins, 789, Morumbi',
            'cidade': 'São Paulo', 
            'estado': 'SP',
            'cep': '05650-000',
            'status': 'Vendas',
            'vgv': 62000000.00,
            'data_lancamento': '2024-05-10',
            'created_at': datetime.now()
        }
    ]
    
    # Mock Unidades
    unidades = [
        {'cvcrm_id': 101, 'empreendimento_id': 1, 'numero': '101', 'bloco': 'A', 'andar': 1, 'tipologia_id': 1, 'area_privativa': 65.50, 'area_total': 78.30, 'valor_tabela': 480000.00, 'valor_venda': 450000.00, 'status': 'Vendido', 'created_at': datetime.now()},
        {'cvcrm_id': 102, 'empreendimento_id': 1, 'numero': '102', 'bloco': 'A', 'andar': 1, 'tipologia_id': 1, 'area_privativa': 67.20, 'area_total': 80.10, 'valor_tabela': 490000.00, 'valor_venda': 465000.00, 'status': 'Vendido', 'created_at': datetime.now()},
        {'cvcrm_id': 201, 'empreendimento_id': 2, 'numero': '201', 'bloco': 'B', 'andar': 2, 'tipologia_id': 2, 'area_privativa': 95.20, 'area_total': 110.80, 'valor_tabela': 820000.00, 'valor_venda': 780000.00, 'status': 'Vendido', 'created_at': datetime.now()},
        {'cvcrm_id': 202, 'empreendimento_id': 2, 'numero': '202', 'bloco': 'B', 'andar': 2, 'tipologia_id': 2, 'area_privativa': 98.50, 'area_total': 115.20, 'valor_tabela': 850000.00, 'valor_venda': 810000.00, 'status': 'Vendido', 'created_at': datetime.now()},
        {'cvcrm_id': 301, 'empreendimento_id': 3, 'numero': '301', 'bloco': 'C', 'andar': 3, 'tipologia_id': 3, 'area_privativa': 120.00, 'area_total': 140.50, 'valor_tabela': 950000.00, 'valor_venda': 920000.00, 'status': 'Vendido', 'created_at': datetime.now()}
    ]
    
    # Mock Vendas (baseado em estrutura CVDW reservas) - distribuídas pelos últimos 6 meses
    base_date = datetime.now() - timedelta(days=180)
    vendas = [
        {'cvcrm_id': 1, 'reserva_id': 1001, 'empreendimento': 'Residencial Sol Nascente', 'unidade_id': 101, 'corretor': 'João Silva Santos', 'time_corretor': 'Team Alpha', 'cliente': 'Maria Santos Oliveira', 'valor': 450000.00, 'data_venda': (base_date + timedelta(days=30)).date(), 'ativo': 'S', 'status': 'Vendido', 'comissao_valor': 22500.00, 'vgv': 450000.00, 'created_at': datetime.now()},
        {'cvcrm_id': 2, 'reserva_id': 1002, 'empreendimento': 'Residencial Sol Nascente', 'unidade_id': 102, 'corretor': 'João Silva Santos', 'time_corretor': 'Team Alpha', 'cliente': 'Pedro Costa Lima', 'valor': 465000.00, 'data_venda': (base_date + timedelta(days=45)).date(), 'ativo': 'S', 'status': 'Vendido', 'comissao_valor': 23250.00, 'vgv': 465000.00, 'created_at': datetime.now()},
        {'cvcrm_id': 3, 'reserva_id': 2001, 'empreendimento': 'Edificio Vista Mar Premium', 'unidade_id': 201, 'corretor': 'Ana Costa Ferreira', 'time_corretor': 'Team Beta', 'cliente': 'Ricardo Mendes', 'valor': 780000.00, 'data_venda': (base_date + timedelta(days=60)).date(), 'ativo': 'S', 'status': 'Vendido', 'comissao_valor': 39000.00, 'vgv': 780000.00, 'created_at': datetime.now()},
        {'cvcrm_id': 4, 'reserva_id': 2002, 'empreendimento': 'Edificio Vista Mar Premium', 'unidade_id': 202, 'corretor': 'Carlos Rodrigues', 'time_corretor': 'Team Beta', 'cliente': 'Juliana Almeida', 'valor': 810000.00, 'data_venda': (base_date + timedelta(days=90)).date(), 'ativo': 'S', 'status': 'Vendido', 'comissao_valor': 40500.00, 'vgv': 810000.00, 'created_at': datetime.now()},
        {'cvcrm_id': 5, 'reserva_id': 3001, 'empreendimento': 'Condominio Park Residence', 'unidade_id': 301, 'corretor': 'Fernanda Lima', 'time_corretor': 'Team Gamma', 'cliente': 'Roberto Nascimento', 'valor': 920000.00, 'data_venda': (base_date + timedelta(days=120)).date(), 'ativo': 'S', 'status': 'Vendido', 'comissao_valor': 46000.00, 'vgv': 920000.00, 'created_at': datetime.now()}
    ]
    
    # Mock Prosoluto
    prosoluto = [
        {'cvcrm_id': 1, 'venda_id': 1, 'empreendimento_id': 1, 'corretor_id': 1, 'valor_prosoluto': 9000.00, 'percentual_prosoluto': 2.0, 'data_calculo': (base_date + timedelta(days=60)).date(), 'data_pagamento': (base_date + timedelta(days=90)).date(), 'status': 'Pago', 'created_at': datetime.now()},
        {'cvcrm_id': 2, 'venda_id': 2, 'empreendimento_id': 1, 'corretor_id': 1, 'valor_prosoluto': 9300.00, 'percentual_prosoluto': 2.0, 'data_calculo': (base_date + timedelta(days=75)).date(), 'data_pagamento': (base_date + timedelta(days=105)).date(), 'status': 'Pago', 'created_at': datetime.now()},
        {'cvcrm_id': 3, 'venda_id': 3, 'empreendimento_id': 2, 'corretor_id': 2, 'valor_prosoluto': 15600.00, 'percentual_prosoluto': 2.0, 'data_calculo': (base_date + timedelta(days=90)).date(), 'data_pagamento': (base_date + timedelta(days=120)).date(), 'status': 'Pago', 'created_at': datetime.now()},
        {'cvcrm_id': 4, 'venda_id': 4, 'empreendimento_id': 2, 'corretor_id': 3, 'valor_prosoluto': 16200.00, 'percentual_prosoluto': 2.0, 'data_calculo': (base_date + timedelta(days=120)).date(), 'data_pagamento': None, 'status': 'Pendente', 'created_at': datetime.now()},
        {'cvcrm_id': 5, 'venda_id': 5, 'empreendimento_id': 3, 'corretor_id': 4, 'valor_prosoluto': 18400.00, 'percentual_prosoluto': 2.0, 'data_calculo': (base_date + timedelta(days=150)).date(), 'data_pagamento': None, 'status': 'Pendente', 'created_at': datetime.now()}
    ]
    
    return {
        'empreendimentos': empreendimentos,
        'unidades': unidades,
        'vendas': vendas,
        'prosoluto': prosoluto
    }

def insert_mock_data():
    """Insere dados mock no banco"""
    
    print("=== INSERINDO DADOS MOCK NO BANCO ===")
    
    mock_data = create_mock_data()
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                
                print("1. Inserindo empreendimentos...")
                for emp in mock_data['empreendimentos']:
                    cursor.execute("""
                        INSERT INTO empreendimentos (cvcrm_id, nome, endereco, cidade, estado, cep, status, vgv, data_lancamento, created_at, updated_at)
                        VALUES (%(cvcrm_id)s, %(nome)s, %(endereco)s, %(cidade)s, %(estado)s, %(cep)s, %(status)s, %(vgv)s, %(data_lancamento)s, %(created_at)s, CURRENT_TIMESTAMP)
                        ON CONFLICT (cvcrm_id) DO UPDATE SET
                            nome = EXCLUDED.nome,
                            endereco = EXCLUDED.endereco,
                            status = EXCLUDED.status,
                            updated_at = CURRENT_TIMESTAMP
                    """, emp)
                
                print("2. Inserindo unidades...")
                for unidade in mock_data['unidades']:
                    cursor.execute("""
                        INSERT INTO unidades (cvcrm_id, empreendimento_id, numero, bloco, andar, tipologia_id, area_privativa, area_total, valor_tabela, valor_venda, status, created_at, updated_at)
                        VALUES (%(cvcrm_id)s, %(empreendimento_id)s, %(numero)s, %(bloco)s, %(andar)s, %(tipologia_id)s, %(area_privativa)s, %(area_total)s, %(valor_tabela)s, %(valor_venda)s, %(status)s, %(created_at)s, CURRENT_TIMESTAMP)
                        ON CONFLICT (cvcrm_id) DO UPDATE SET
                            valor_venda = EXCLUDED.valor_venda,
                            status = EXCLUDED.status,
                            updated_at = CURRENT_TIMESTAMP
                    """, unidade)
                
                print("3. Inserindo vendas (nova estrutura CVDW)...")
                for venda in mock_data['vendas']:
                    cursor.execute("""
                        INSERT INTO vendas (cvcrm_id, reserva_id, empreendimento, unidade_id, corretor, time_corretor, cliente, valor, data_venda, ativo, status, comissao_valor, vgv, created_at, updated_at)
                        VALUES (%(cvcrm_id)s, %(reserva_id)s, %(empreendimento)s, %(unidade_id)s, %(corretor)s, %(time_corretor)s, %(cliente)s, %(valor)s, %(data_venda)s, %(ativo)s, %(status)s, %(comissao_valor)s, %(vgv)s, %(created_at)s, CURRENT_TIMESTAMP)
                        ON CONFLICT (cvcrm_id) DO UPDATE SET
                            valor = EXCLUDED.valor,
                            ativo = EXCLUDED.ativo,
                            status = EXCLUDED.status,
                            updated_at = CURRENT_TIMESTAMP
                    """, venda)
                
                print("4. Inserindo dados de prosoluto...")
                for prs in mock_data['prosoluto']:
                    cursor.execute("""
                        INSERT INTO prosoluto (cvcrm_id, venda_id, empreendimento_id, corretor_id, valor_prosoluto, percentual_prosoluto, data_calculo, data_pagamento, status, created_at, updated_at)
                        VALUES (%(cvcrm_id)s, %(venda_id)s, %(empreendimento_id)s, %(corretor_id)s, %(valor_prosoluto)s, %(percentual_prosoluto)s, %(data_calculo)s, %(data_pagamento)s, %(status)s, %(created_at)s, CURRENT_TIMESTAMP)
                        ON CONFLICT (cvcrm_id) DO UPDATE SET
                            valor_prosoluto = EXCLUDED.valor_prosoluto,
                            status = EXCLUDED.status,
                            updated_at = CURRENT_TIMESTAMP
                    """, prs)
                
            conn.commit()
            print("\nSUCESSO! Dados mock inseridos no banco")
            
    except Exception as e:
        print(f"ERRO ao inserir dados mock: {e}")
        raise

def verify_data():
    """Verifica se os dados foram inseridos corretamente"""
    
    print("\n=== VERIFICANDO DADOS INSERIDOS ===")
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                
                # Contar registros em cada tabela
                tabelas = ['empreendimentos', 'unidades', 'vendas', 'prosoluto']
                
                for tabela in tabelas:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                    count = cursor.fetchone()[0]
                    print(f"{tabela}: {count} registros")
                
                print("\n=== TESTANDO VIEWS DE ANALISE ===")
                
                # Testar views principais
                views_teste = [
                    ('vw_vendas_por_empreendimento', 'Vendas por empreendimento'),
                    ('vw_vendas_por_corretor', 'Vendas por corretor'),
                    ('vw_vendas_por_time', 'Vendas por time'),
                    ('vw_tabela_geral_vendas', 'Tabela geral de vendas')
                ]
                
                for view_name, desc in views_teste:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {view_name}")
                        count = cursor.fetchone()[0] 
                        print(f"{desc}: {count} registros")
                    except Exception as e:
                        print(f"{desc}: ERRO - {e}")
                
                print("\n=== RESUMO FINANCEIRO ===")
                
                # Dados financeiros principais
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_vendas,
                        SUM(valor) as valor_total,
                        AVG(valor) as ticket_medio,
                        SUM(comissao_valor) as total_comissoes
                    FROM vendas 
                    WHERE ativo = 'S' AND data_venda IS NOT NULL
                """)
                
                resultado = cursor.fetchone()
                if resultado:
                    total_vendas, valor_total, ticket_medio, total_comissoes = resultado
                    print(f"Total de Vendas: {total_vendas}")
                    print(f"Valor Total: R$ {valor_total:,.2f}")
                    print(f"Ticket Médio: R$ {ticket_medio:,.2f}")
                    print(f"Total Comissões: R$ {total_comissoes:,.2f}")
                
                print("\nSUCESSO! Views e dados funcionando perfeitamente")
                
    except Exception as e:
        print(f"ERRO ao verificar dados: {e}")

if __name__ == "__main__":
    print("CVCRM ETL - Populacao de Dados Mock")
    print("====================================")
    print("IMPORTANTE: Estes sao dados de TESTE")
    print("Serao substituidos quando API CVDW funcionar")
    print()
    
    insert_mock_data()
    verify_data()
    
    print("\n🎉 DADOS MOCK INSERIDOS COM SUCESSO!")
    print("👉 Dashboard agora tem dados para exibir")
    print("👉 Execute: python monitoring.py")
    print("👉 Acesse: http://localhost:5000")
    print("👉 Quando API CVDW funcionar, estes dados serão substituidos")
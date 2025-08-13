import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def verificar_dados():
    print("=== VERIFICACAO DE DADOS APOS ETL ===")
    
    database_url = os.getenv('DATABASE_URL')
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Tabelas principais para verificar
        tabelas = [
            'empreendimentos',
            'vendas', 
            'unidades',
            'prosoluto',
            'atendimentos',
            'repasses',
            'reservas'
        ]
        
        print("\n--- Contagem de registros por tabela ---")
        total_registros = 0
        
        for tabela in tabelas:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {tabela};")
                count = cursor.fetchone()[0]
                print(f"{tabela:15}: {count:6} registros")
                total_registros += count
            except Exception as e:
                print(f"{tabela:15}: ERRO - {e}")
        
        print(f"{'TOTAL':15}: {total_registros:6} registros")
        
        # Verificar se há alguma tabela com dados para mostrar exemplo
        print("\n--- Exemplos de dados (se existirem) ---")
        for tabela in tabelas:
            try:
                cursor.execute(f"SELECT * FROM {tabela} LIMIT 3;")
                rows = cursor.fetchall()
                if rows:
                    print(f"\n{tabela.upper()} (primeiros {len(rows)} registros):")
                    for i, row in enumerate(rows, 1):
                        print(f"  Registro {i}: {row[:5]}...")  # Mostrar só os primeiros 5 campos
            except Exception as e:
                pass  # Não mostrar erros aqui
        
        # Verificar views também
        print("\n--- Views analiticas ---")
        views = [
            'vw_vendas_mensais',
            'vw_vendas_por_empreendimento', 
            'vw_prosoluto_analise'
        ]
        
        for view in views:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {view};")
                count = cursor.fetchone()[0]
                print(f"{view:25}: {count:6} registros")
            except Exception as e:
                print(f"{view:25}: ERRO - {e}")
        
        cursor.close()
        conn.close()
        
        if total_registros > 0:
            print(f"\n=== SUCESSO ===")
            print(f"Base de dados contem {total_registros} registros!")
            print(f"ETL funcionou e trouxe dados reais!")
        else:
            print(f"\n=== ATENCAO ===") 
            print(f"ETL executou mas nao trouxe dados.")
            print(f"Possíveis causas:")
            print(f"  - API sem dados no período")
            print(f"  - Filtros muito restritivos")
            print(f"  - Endpoints com restrições")
            print(f"  - Rate limiting impediu requests")
        
        return total_registros
        
    except Exception as e:
        print(f"\nErro ao verificar dados: {e}")
        return 0

if __name__ == "__main__":
    verificar_dados()
import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
from utils.db_utils import conectar_postgres, configurar_logger, carregar_env

env = carregar_env([
    "psql_local_host", "psql_local_port", "psql_local_user", 
    "psql_local_password", "psql_local_dbname_fin"
])
configurar_logger("analise_fpd", "INFO")

RECRIAR_ESTRUTURA = False  # Se True, recria as tabelas no Postgres antes de popular
NOVOS_CLIENTES = 2000  # Quantidade de clientes a serem gerados

fake = Faker(['pt_BR'])
conn, cursor, engine = conectar_postgres(
    host = env["psql_local_host"],
    port = env["psql_local_port"],
    username = env["psql_local_user"],
    password = env["psql_local_password"],
    database = env["psql_local_dbname_fin"]
)


def obter_max_id(tabela, coluna):
    """Obtem o valor máximo de uma coluna na tabela especificada"""
    if RECRIAR_ESTRUTURA:
        return 0 
    try:
        query = f"SELECT MAX({coluna}) FROM {tabela};"
        df = pd.read_sql(query, engine)
        max_id = df.iloc[0, 0]
        return max_id if max_id is not None else 0
    except Exception as e:
        print(f"Erro ao obter max_id de {tabela}: {e}")
        return 0

# --- 1. GERAR CLIENTES ---
def generate_clients(n, start_id):
    clients = []
    for i in range(start_id + 1, start_id + n + 1):
        clients.append({
            'id_cliente': i,
            'nome': fake.name(),
            'segmento': random.choice(['Corporate', 'Varejo', 'Agro', 'PME']),
            'uf': fake.state_abbr(),
            'data_cadastro': fake.date_between(start_date='-1y', end_date='today')
        })
    return pd.DataFrame(clients)


# --- 2. GERAR CONTRATOS ---
def generate_contracts(df_clients, start_id):
    contracts = []
    contract_id = start_id + 1
    for _, client in df_clients.iterrows():
        # Simulando que alguns clientes têm mais de um contrato (recompra)
        num_contracts = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
        
        last_date = client['data_cadastro']
        for _ in range(num_contracts):
            start_date = last_date + timedelta(days=random.randint(30, 200))
            if start_date > datetime.now().date(): break
            
            contracts.append({
                'id_contrato': contract_id,
                'id_cliente': client['id_cliente'],
                'data_emissao': start_date,
                'valor_total': round(random.uniform(1000, 50000), 2),
                'parcelas': random.choice([6, 12, 24])
            })
            last_date = start_date
            contract_id += 1
    return pd.DataFrame(contracts)


# --- 3. GERAR FATURAS (Onde mora a inadimplência) ---
def generate_invoices(df_contracts, start_id):
    invoices = []
    invoice_id = start_id +1
    for _, contract in df_contracts.iterrows():
        parcela_val = round(contract['valor_total'] / contract['parcelas'], 2)
        
        for n in range(1, contract['parcelas'] + 1):
            due_date = contract['data_emissao'] + timedelta(days=30 * n)
            
            # Lógica de Status:
            # 10% de chance de ser Inadimplente se já venceu
            status = 'Paid'
            payment_date = due_date + timedelta(days=random.randint(-5, 2))
            
            if due_date < datetime.now().date():
                if random.random() < 0.15: # 15% de inadimplência simulada
                    status = 'Overdue'
                    payment_date = None
            else:
                status = 'Open'
                payment_date = None

            invoices.append({
                'id_fatura': invoice_id,
                'id_contrato': contract['id_contrato'],
                'num_parcela': n,
                'data_vcto': due_date,
                'vlr_parcela': parcela_val,
                'status': status,
                'data_pgto': payment_date
            })
            invoice_id += 1
    return pd.DataFrame(invoices)


def generate_debt_collection(df_invoices, start_id):
    collections = []
    collection_id = start_id + 1
    df_overdue = df_invoices[df_invoices['status'] == 'Overdue']

    for _, invoice in df_overdue.iterrows():
        qtde_acionamentos = random.randint(1, 4)
        data_base = invoice['data_vcto']
        
        for _ in range(qtde_acionamentos):
            dias_atraso = (datetime.now().date() - data_base).days
            data_acionamento = data_base + timedelta(days=random.randint(1, 30))

            if data_acionamento > datetime.now().date():
                break  # Não gerar acionamentos no futuro
    
            collections.append({
                'id_debt_collection': collection_id,
                'id_contrato': invoice['id_contrato'],
                'num_fatura': invoice['id_fatura'],
                'data_acionamento': data_acionamento,
                'forma_acionamento': random.choice(['sms', 'email', 'ligação']),
                'resultado': random.choice(['Contato', 'Sem Contato', 'Promessa de Pagamento', 'Renegociação', 'Desconhece Dívida']),
                'cpc': random.choice([0, 1])
            })
            collection_id += 1
            data_base = data_acionamento  # Atualiza a data base para o próximo acionamento
    return pd.DataFrame(collections)


max_cliente = obter_max_id('clients', 'id_cliente')
max_contrato = obter_max_id('contracts', 'id_contrato')
max_fatura = obter_max_id('invoices', 'id_fatura')
max_collection = obter_max_id('debt_collection', 'id_debt_collection')

# 2. Gerar Dados Incrementalmente
df_c = generate_clients(NOVOS_CLIENTES, max_cliente)
df_con = generate_contracts(df_c, max_contrato)
df_inv = generate_invoices(df_con, max_fatura)
df_debt = generate_debt_collection(df_inv, max_collection)

# 3. Salvar no Banco
acao_banco = 'replace' if RECRIAR_ESTRUTURA else 'append'

df_c.to_sql('clients', engine, if_exists=acao_banco, index=False)
df_con.to_sql('contracts', engine, if_exists=acao_banco, index=False)
df_inv.to_sql('invoices', engine, if_exists=acao_banco, index=False)
df_debt.to_sql('debt_collection', engine, if_exists=acao_banco, index=False)


print(f"--- Processo Concluído (Modo: {acao_banco.upper()}) ---")
print(f"Novos Clientes: {len(df_c)}")
print(f"Novos Contratos: {len(df_con)}")
print(f"Novas Faturas: {len(df_inv)}")
print(f"Novos Acionamentos (Cobrança): {len(df_debt)}")

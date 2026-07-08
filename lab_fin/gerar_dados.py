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

fake = Faker(['pt_BR'])
conn, cursor, engine = conectar_postgres(
    host = env["psql_local_host"],
    port = env["psql_local_port"],
    username = env["psql_local_user"],
    password = env["psql_local_password"],
    database = env["psql_local_dbname_fin"]
)

# --- 1. GERAR CLIENTES ---
def generate_clients(n=100):
    clients = []
    for i in range(1, n + 1):
        clients.append({
            'id_cliente': i,
            'nome': fake.name(),
            'segmento': random.choice(['Corporate', 'Varejo', 'Agro', 'PME']),
            'uf': fake.state_abbr(),
            'data_cadastro': fake.date_between(start_date='-1y', end_date='today')
        })
    return pd.DataFrame(clients)


# --- 2. GERAR CONTRATOS ---
def generate_contracts(df_clients):
    contracts = []
    contract_id = 1
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
def generate_invoices(df_contracts):
    invoices = []
    invoice_id = 1
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

# Execução
df_c = generate_clients(2000)
df_con = generate_contracts(df_c)
df_inv = generate_invoices(df_con)

# Salvar no Banco
df_c.to_sql('clients', engine, if_exists='append', index=False)
df_con.to_sql('contracts', engine, if_exists='append', index=False)
df_inv.to_sql('invoices', engine, if_exists='append', index=False)

print(f"Sandbox Criada! {len(df_inv)} faturas geradas para análise.")


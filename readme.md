# Sandbox de Análise Financeira e Risco de Crédito

Este repositório contém uma infraestrutura completa para simulação e análise de dados financeiros, com foco em métricas de risco de crédito como **FPD (First Payment Default)** e **SPD (Second Payment Default)**. O projeto integra a geração de dados sintéticos em Python com modelagem estruturada e consultas avançadas em PostgreSQL.

## 📂 Estrutura de Arquivos

### 1. `utils/db_utils.py`
**Finalidade:** Arquivo de funções comuns para operações de ETL e gestão de banco de dados.
- Gerencia a conexão com múltiplos bancos de dados (PostgreSQL, SQL Server) usando `psycopg2`, `pyodbc` e `SQLAlchemy`.
- Faz o carregamento e validação de variáveis de ambiente (`.env`).


### 2. `sql/create_tables.sql`
**Finalidade:** Script DDL (Data Definition Language) para estruturar o banco de dados PostgreSQL.
- Cria as tabelas `clients` (clientes), `contracts` (contratos) e `invoices` (faturas).
- Estabelece a integridade referencial com chaves estrangeiras (Foreign Keys) e restrições (Check Constraints).
- Prepara o banco com tipos de dados adequados para garantir a precisão dos cálculos financeiros.

### 3. `gerar_dados.py`
**Finalidade:** Motor de geração de dados sintéticos realistas.
- Utiliza a biblioteca `Faker` para gerar perfis demográficos de clientes.
- Cria regras lógicas para vincular múltiplos contratos por cliente (simulando retenção/recompra).
- Gera faturas com comportamentos de pagamento simulados (incluindo taxas controladas de inadimplência).
- Popula as tabelas do PostgreSQL automaticamente via `pandas.to_sql`.

### 4. `sql/queries.sql`
**Finalidade:** Consultas SQL analíticas de alto desempenho.
- Calcula os indicadores de risco **FPD** e **SPD** por contrato.
- Utiliza CTEs (Common Table Expressions) para separar vencimentos teóricos de pagamentos reais.
- Emprega cláusulas avançadas como `FILTER` e `DATE_TRUNC` para comparar datas de pagamento com precisão mensal, evitando distorções causadas por pagamentos antecipados de parcelas futuras.

## 🚀 Como Utilizar

1. **Preparar o Banco de Dados:** Execute o arquivo `create_tables.sql` no seu ambiente PostgreSQL para criar a estrutura das tabelas.
2. **Instalação das dependências:** Costumo usar o pipenv para gerenciar pacotes: `pip install pipenv`. Basta navegar até o caminho onde está o Pipfile e digitar `pipenv install`. Ele criará o venv e instalará os pacotes necessários para esse lab.
3. **Gerar os Dados:** Para essa lab, as senhas estão salvas em um arquivo fora do projeto (`~/secure/env/.env`) e o `db_utils.py` está configurado para, dinamicamente, fazer o import das bibliotecas e retornar as senhas para uso posterior no código. Na prática, basta executar o `gerar_dados.py` para popular as tabelas.
4. **Analisar:** Utilize as queries do arquivo `queries.sql` para extrair os indicadores financeiros do banco populado.
-- =========================================================================
-- MODELO DE DADOS: SANDBOX DE ANÁLISE FINANCEIRA E RISCO (POSTGRESQL)
-- Autor: Engenharia de Dados / Sandbox de Testes Financeiros
-- Objetivo: Definição de Esquema (DDL) com Integridade Referencial e Índices
-- =========================================================================

DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS contracts CASCADE;
DROP TABLE IF EXISTS clients CASCADE;

-- 1. TABELA DE CLIENTES
-- Armazena os perfis demográficos e segmentações do Faker
CREATE TABLE clients (
    id_cliente INT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    segmento VARCHAR(50) NOT NULL,       -- Ex: 'Corporate', 'Varejo', 'Agro', 'PME'
    uf CHAR(2) NOT NULL,                 -- Estado (ex: 'SP', 'RJ')
    data_cadastro DATE NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABELA DE CONTRATOS
-- Registra as operações de crédito originadas
CREATE TABLE contracts (
    id_contrato INT PRIMARY KEY,
    id_cliente INT NOT NULL,
    data_emissao DATE NOT NULL,
    valor_total DECIMAL(14, 2) NOT NULL, 
    parcelas INT NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Restrições de Integridade
    CONSTRAINT fk_contracts_client FOREIGN KEY (id_cliente) REFERENCES clients(id_cliente) ON DELETE CASCADE
);

-- 3. TABELA DE FATURAS (INVOICES)
-- Granularidade máxima: essencial para cálculos de safras, FPD, SPD e Aging de parcelas
CREATE TABLE invoices (
    id_fatura INT PRIMARY KEY,
    id_contrato INT NOT NULL,
    num_parcela INT NOT NULL,
    data_vcto DATE NOT NULL,               -- Data de Vencimento
    vlr_parcela DECIMAL(14, 2) NOT NULL,       -- Valor da Parcela daquele mês
    status VARCHAR(20) NOT NULL,          -- 'Paid' (Pago), 'Overdue' (Vencido/Atraso), 'Open' (Aberto)
    data_pgto DATE,                    -- Data real de pagamento (NULL se não pago)
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Restrições de Integridade e Regras de Negócio
    CONSTRAINT fk_invoices_contract FOREIGN KEY (id_contrato) REFERENCES contracts(id_contrato) ON DELETE CASCADE,
    CONSTRAINT chk_invoice_status CHECK (status IN ('Paid', 'Overdue', 'Open'))
);

/*
COMMENT ON TABLE clients IS 'Tabela contendo os dados demográficos e segmentação de clientes.';
COMMENT ON TABLE contracts IS 'Tabela contendo os cabeçalhos de contratos financeiros criados.';
COMMENT ON TABLE invoices IS 'Tabela granular contendo o fluxo de parcelas e status de pagamento para controle de risco (FPD/SPD).';

-- Índice para acelerar agrupamentos por mercado/segmento 
CREATE INDEX idx_clients_segmento ON clients(segmento);

-- Índice na FK para otimizar os JOINs entre Clientes e Contratos
CREATE INDEX idx_contracts_id_cliente ON contracts(id_cliente);

-- Índices compostos de alta performance para buscas temporais de risco e Window Functions
CREATE INDEX idx_invoices_contract_due ON invoices(id_contrato, due_date);
CREATE INDEX idx_invoices_status ON invoices(status);
*/
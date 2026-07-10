-- Active: 1783513857725@@127.0.0.1@5432@lab_fin@public
-- ============================================================
-- Indicadores FPD e SPD por contrato
--
-- FPD (First Payment Default):
--   'Sim' se o 1º pagamento já realizado no contrato (qualquer
--   parcela) NÃO caiu dentro do mês de vencimento da parcela 1,
--   ou se nenhum pagamento foi feito ainda.
--
-- SPD (Second Payment Default):
--   Mesma lógica aplicada ao 2º pagamento x vencimento da parcela 2.
--   Se o contrato já é FPD = 'Sim', o SPD é marcado como 'N/A'
--   (a régua de 2º pagamento só faz sentido se o cliente passou
--   pela 1ª régua).
-- ============================================================

WITH parcelas_referencia AS (
    -- Data de vencimento da 1ª e da 2ª parcela de cada contrato
    SELECT
        id_contrato,
        MAX(data_vcto) FILTER (WHERE num_parcela = 1) AS vencimento_parcela_1,
        MAX(data_vcto) FILTER (WHERE num_parcela = 2) AS vencimento_parcela_2
    FROM invoices
    GROUP BY id_contrato
),

pagamentos_ordenados AS (
    -- Apenas faturas efetivamente pagas, ordenadas cronologicamente
    SELECT
        id_contrato,
        data_pgto,
        ROW_NUMBER() OVER (PARTITION BY id_contrato ORDER BY data_pgto) AS ordem_pagamento
    FROM invoices
    WHERE status = 'Paid'
      AND data_pgto IS NOT NULL
),

pagamentos_referencia AS (
    -- 1º e 2º pagamento realizados no contrato, independente de qual parcela
    SELECT
        id_contrato,
        MAX(data_pgto) FILTER (WHERE ordem_pagamento = 1) AS primeiro_pagamento,
        MAX(data_pgto) FILTER (WHERE ordem_pagamento = 2) AS segundo_pagamento
    FROM pagamentos_ordenados
    GROUP BY id_contrato
),

indicadores AS (
    SELECT
        parcelas_referencia.id_contrato,
        parcelas_referencia.vencimento_parcela_1,
        pagamentos_referencia.primeiro_pagamento,
        parcelas_referencia.vencimento_parcela_2,
        pagamentos_referencia.segundo_pagamento,
        pagamentos_referencia.primeiro_pagamento >= DATE_TRUNC('month', parcelas_referencia.vencimento_parcela_1)
            AND pagamentos_referencia.primeiro_pagamento <  DATE_TRUNC('month', parcelas_referencia.vencimento_parcela_1) + INTERVAL '1 month'
            AS pagou_dentro_mes_p1,
        pagamentos_referencia.segundo_pagamento >= DATE_TRUNC('month', parcelas_referencia.vencimento_parcela_2)
            AND pagamentos_referencia.segundo_pagamento <  DATE_TRUNC('month', parcelas_referencia.vencimento_parcela_2) + INTERVAL '1 month'
            AS pagou_dentro_mes_p2
    FROM parcelas_referencia
    LEFT JOIN pagamentos_referencia
        ON pagamentos_referencia.id_contrato = parcelas_referencia.id_contrato
)

SELECT
    id_contrato,
    vencimento_parcela_1,
    primeiro_pagamento,
    CASE WHEN pagou_dentro_mes_p1 THEN 'Não' ELSE 'Sim' END AS indicador_fpd,
    vencimento_parcela_2,
    segundo_pagamento,
    CASE
        WHEN NOT pagou_dentro_mes_p1 THEN 'N/A'
        WHEN pagou_dentro_mes_p2 THEN 'Não'
        ELSE 'Sim'
    END AS indicador_spd
FROM indicadores
ORDER BY id_contrato;


-- CREATE INDEX idx_invoices_contrato_parcela ON invoices (id_contrato, num_parcela);
-- CREATE INDEX idx_invoices_contrato_pago    ON invoices (id_contrato, data_pgto) WHERE status = 'Paid';

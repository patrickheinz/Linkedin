WITH parcelas_pagas
AS (
	SELECT contracts.id_cliente
		,invoices.id_fatura
		,invoices.id_contrato
		,invoices.num_parcela
		,invoices.data_vcto
		,invoices.data_pgto
		,(invoices.data_pgto - invoices.data_vcto) AS dias_atraso
	FROM invoices
	JOIN contracts ON contracts.id_contrato = invoices.id_contrato
	WHERE invoices.STATUS = 'Paid'
	)
	,com_baseline_historica
AS (
	SELECT *
		,ROW_NUMBER() OVER (
			PARTITION BY id_cliente ORDER BY data_vcto
			) AS ordem_parcela
		,AVG(dias_atraso) OVER (
			PARTITION BY id_cliente ORDER BY data_vcto ROWS BETWEEN UNBOUNDED PRECEDING
					AND 1 PRECEDING
			) AS media_atraso_ate_aqui
		,STDDEV(dias_atraso) OVER (
			PARTITION BY id_cliente ORDER BY data_vcto ROWS BETWEEN UNBOUNDED PRECEDING
					AND 1 PRECEDING
			) AS desvio_atraso_ate_aqui
	FROM parcelas_pagas
	)
SELECT id_cliente
	,id_contrato
	,num_parcela
	,data_vcto
	,dias_atraso
	,ROUND(media_atraso_ate_aqui::NUMERIC, 1) AS media_historica
	,ROUND(desvio_atraso_ate_aqui::NUMERIC, 1) AS desvio_historico
	,CASE 
		WHEN ordem_parcela = 1
			THEN 'Sem histórico anterior'
		WHEN dias_atraso > media_atraso_ate_aqui + COALESCE(desvio_atraso_ate_aqui, 0) + 3
			THEN 'Piora pontual (acima do histórico dele)'
		WHEN dias_atraso < media_atraso_ate_aqui - COALESCE(desvio_atraso_ate_aqui, 0) - 3
			THEN 'Melhora pontual (abaixo do histórico dele)'
		ELSE 'Dentro do histórico'
		END AS classificacao_pontual
FROM com_baseline_historica
ORDER BY id_cliente
	,ordem_parcela;

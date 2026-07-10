WITH parcelas_pagas
AS (
	SELECT contracts.id_cliente
		,invoices.data_vcto
		,(invoices.data_pgto - invoices.data_vcto) AS dias_atraso
		,ROW_NUMBER() OVER (
			PARTITION BY contracts.id_cliente ORDER BY invoices.data_vcto
			) AS ordem_parcela
	FROM invoices
	JOIN contracts ON contracts.id_contrato = invoices.id_contrato
	WHERE invoices.STATUS = 'Paid'
	)
	,tendencia_cliente
AS (
	SELECT id_cliente
		,COUNT(*) AS qtd_parcelas_pagas
		,ROUND(AVG(dias_atraso), 1) AS media_atraso
		,ROUND(REGR_SLOPE(dias_atraso, ordem_parcela)::NUMERIC, 2) AS slope -- inclinação da reta de regressão
		,ROUND(CORR(dias_atraso, ordem_parcela)::NUMERIC, 2) AS correlacao -- força da relação linear
	FROM parcelas_pagas
	GROUP BY id_cliente
	)
SELECT clients.id_cliente
	,clients.nome
	,tendencia_cliente.qtd_parcelas_pagas
	,tendencia_cliente.media_atraso
	,tendencia_cliente.slope
	,tendencia_cliente.correlacao
	,CASE 
		WHEN tendencia_cliente.qtd_parcelas_pagas < 4
			THEN 'Dados insuficientes'
		WHEN tendencia_cliente.correlacao >= 0.5
			AND tendencia_cliente.slope > 0.3
			    THEN 'Piorando'
		WHEN tendencia_cliente.correlacao <= - 0.5
			AND tendencia_cliente.slope < - 0.3
			    THEN 'Melhorando'
		ELSE 'Mantendo'
		END AS tendencia_comportamento
FROM tendencia_cliente
JOIN clients ON clients.id_cliente = tendencia_cliente.id_cliente
ORDER BY tendencia_cliente.id_cliente;
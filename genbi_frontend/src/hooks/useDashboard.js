import { useState, useEffect, useCallback } from 'react'
import { chatApi } from '../services/api'

function useQuery(sql) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const run = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await chatApi.executeSQL(sql.trim(), 50, 0)
      setData(res)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [sql])

  useEffect(() => { run() }, [run])

  return { data, loading, error, refetch: run }
}

export function useDashboard() {
  const [period, setPeriod] = useState('all') // 'all' | '30j' | '7j'

  const pw = period === '7j'
    ? `AND sale_date >= CURRENT_DATE - INTERVAL '7 days'`
    : period === '30j'
    ? `AND sale_date >= CURRENT_DATE - INTERVAL '30 days'`
    : ''

  const pws = period === '7j'
    ? `AND s.sale_date >= CURRENT_DATE - INTERVAL '7 days'`
    : period === '30j'
    ? `AND s.sale_date >= CURRENT_DATE - INTERVAL '30 days'`
    : ''

  const caTotal = useQuery(
    `SELECT SUM(total_amount_fcfa) AS ca_total FROM marts.fct_sales WHERE TRUE ${pw}`
  )

  const caMensuel = useQuery(
    `SELECT sale_month AS mois, SUM(total_amount_fcfa) AS ca_total
     FROM marts.fct_sales WHERE TRUE ${pw}
     GROUP BY sale_month ORDER BY sale_month`
  )

  const topProduits = useQuery(
    `SELECT pd.commercial_name AS produit, SUM(sd.quantity) AS quantite_vendue
     FROM marts.fct_sales s
     JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id
     JOIN marts.dim_products pd ON sd.product_id = pd.product_id
     WHERE TRUE ${pws}
     GROUP BY pd.commercial_name ORDER BY quantite_vendue DESC LIMIT 5`
  )

  const genericsSplit = useQuery(
    `SELECT pd.is_generic, SUM(sd.quantity) AS total_vendu
     FROM marts.fct_sales s
     JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id
     JOIN marts.dim_products pd ON sd.product_id = pd.product_id
     WHERE TRUE ${pws}
     GROUP BY pd.is_generic ORDER BY pd.is_generic DESC`
  )

  const stocksAlerte = useQuery(
    `SELECT commercial_name AS produit,
            quantity_in_stock AS stock_actuel,
            safety_stock_threshold AS seuil
     FROM marts.dim_stocks
     WHERE is_below_safety_threshold = TRUE
     ORDER BY quantity_in_stock ASC`
  )

  const lotsPerimables = useQuery(
    `SELECT commercial_name AS produit,
            batch_number AS lot,
            expiration_date AS expiration,
            days_until_expiry AS jours_restants
     FROM marts.dim_stocks
     WHERE days_until_expiry >= 0 AND days_until_expiry <= 30
     ORDER BY days_until_expiry ASC`
  )

  const ruptures = useQuery(
    `SELECT COUNT(*) AS total_ruptures FROM marts.fct_missed_sales`
  )

  const isLoading = [caTotal, caMensuel, topProduits, genericsSplit, stocksAlerte, lotsPerimables, ruptures]
    .some(q => q.loading)

  function refetchAll() {
    caTotal.refetch()
    caMensuel.refetch()
    topProduits.refetch()
    genericsSplit.refetch()
    stocksAlerte.refetch()
    lotsPerimables.refetch()
    ruptures.refetch()
  }

  return {
    caTotal, caMensuel, topProduits, genericsSplit,
    stocksAlerte, lotsPerimables, ruptures,
    isLoading, refetchAll,
    period, setPeriod,
  }
}

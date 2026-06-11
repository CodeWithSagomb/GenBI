import { useState, useEffect, useCallback } from 'react'
import { chatApi } from '../services/api'

const SQL = {
  caTotal: `
    SELECT SUM(total_amount_fcfa) AS ca_total
    FROM marts.fct_sales`,

  caMensuel: `
    SELECT sale_month AS mois, SUM(total_amount_fcfa) AS ca_total
    FROM marts.fct_sales
    GROUP BY sale_month
    ORDER BY sale_month`,

  topProduits: `
    SELECT pd.commercial_name AS produit, SUM(sd.quantity) AS quantite_vendue
    FROM marts.fct_sales s
    JOIN staging.stg_raw__sale_details sd ON s.sale_id = sd.sale_id
    JOIN marts.dim_products pd ON sd.product_id = pd.product_id
    GROUP BY pd.commercial_name
    ORDER BY quantite_vendue DESC
    LIMIT 5`,

  stocksAlerte: `
    SELECT commercial_name AS produit,
           quantity_in_stock AS stock_actuel,
           safety_stock_threshold AS seuil
    FROM marts.dim_stocks
    WHERE is_below_safety_threshold = TRUE
    ORDER BY quantity_in_stock ASC`,

  lotsPerimables: `
    SELECT commercial_name AS produit,
           batch_number AS lot,
           expiration_date AS expiration,
           days_until_expiry AS jours_restants
    FROM marts.dim_stocks
    WHERE days_until_expiry >= 0 AND days_until_expiry <= 30
    ORDER BY days_until_expiry ASC`,

  ruptures: `
    SELECT COUNT(*) AS total_ruptures
    FROM marts.fct_missed_sales`,
}

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
  const caTotal      = useQuery(SQL.caTotal)
  const caMensuel    = useQuery(SQL.caMensuel)
  const topProduits  = useQuery(SQL.topProduits)
  const stocksAlerte = useQuery(SQL.stocksAlerte)
  const lotsPerimables = useQuery(SQL.lotsPerimables)
  const ruptures     = useQuery(SQL.ruptures)

  const isLoading = [caTotal, caMensuel, topProduits, stocksAlerte, lotsPerimables, ruptures]
    .some(q => q.loading)

  function refetchAll() {
    caTotal.refetch()
    caMensuel.refetch()
    topProduits.refetch()
    stocksAlerte.refetch()
    lotsPerimables.refetch()
    ruptures.refetch()
  }

  return { caTotal, caMensuel, topProduits, stocksAlerte, lotsPerimables, ruptures, isLoading, refetchAll }
}

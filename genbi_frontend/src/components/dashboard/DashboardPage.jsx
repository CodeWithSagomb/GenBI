import { RefreshCw, DollarSign, TrendingUp, Package, AlertTriangle, Clock, ShoppingCart, Zap } from 'lucide-react'
import { useDashboard } from '../../hooks/useDashboard'
import { useAlerts } from '../../hooks/useAlerts'
import { KPICard } from './KPICard'
import { AlertTable } from './AlertTable'
import { RankingBarChart } from '../visualizations/RankingBarChart'
import { SalesLineChart } from '../visualizations/SalesLineChart'

function buildChartData(columns, rows) {
  if (!rows || !columns) return []
  return rows.map(row => {
    const obj = {}
    columns.forEach((col, i) => { obj[col] = row[i] })
    return obj
  })
}

const SEVERITY_LABEL = { danger: 'Critique', warning: 'Attention', info: 'Info' }

const MONTHS_SHORT = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc']

function derivePeriod(rows) {
  if (!rows || rows.length === 0) return null
  const first = rows[0][0]
  const last  = rows[rows.length - 1][0]
  if (!first || !last) return null
  const a = MONTHS_SHORT[first - 1]
  const b = MONTHS_SHORT[last  - 1]
  return a === b ? a : `${a}–${b}`
}

function AlertInsightCard({ alert }) {
  const color = alert.severity === 'danger' ? 'var(--danger)'
    : alert.severity === 'warning' ? 'var(--warning)'
    : 'var(--secondary)'
  return (
    <div className="alert-insight-card" style={{ borderLeft: `3px solid ${color}` }}>
      <div className="alert-insight-card__header">
        <span className="alert-insight-card__badge" style={{ background: color }}>
          {SEVERITY_LABEL[alert.severity] ?? alert.severity}
        </span>
        <span className="alert-insight-card__title">{alert.title}</span>
        <span className="alert-insight-card__count">{alert.row_count} résultat{alert.row_count > 1 ? 's' : ''}</span>
      </div>
      {alert.row_count === 0 ? (
        <p className="alert-insight-card__empty">Aucune alerte active.</p>
      ) : (
        <p className="alert-insight-card__insight">{alert.insight}</p>
      )}
    </div>
  )
}

export function DashboardPage() {
  const {
    caTotal, caMensuel, topProduits,
    stocksAlerte, lotsPerimables, ruptures,
    isLoading, refetchAll,
  } = useDashboard()
  const { alerts, loading: alertsLoading, refetch: refetchAlerts } = useAlerts()

  const caValue = caTotal.data?.rows?.[0]?.[0] ?? null
  const rupturesValue = ruptures.data?.rows?.[0]?.[0] ?? null

  const caMensuelData = buildChartData(caMensuel.data?.columns, caMensuel.data?.rows)
  const topProduitsData = buildChartData(topProduits.data?.columns, topProduits.data?.rows)

  return (
    <div className="dashboard">

      {/* En-tête */}
      <div className="dashboard__header">
        <div>
          <h1 className="dashboard__title">Tableau de bord</h1>
          <p className="dashboard__subtitle">
            Vue d'ensemble{derivePeriod(caMensuel.data?.rows) ? ` — données ${derivePeriod(caMensuel.data?.rows)}` : ''}
          </p>
        </div>
        <button
          className="dashboard__refresh"
          onClick={() => { refetchAll(); refetchAlerts() }}
          disabled={isLoading || alertsLoading}
          title="Actualiser"
        >
          <RefreshCw size={15} className={(isLoading || alertsLoading) ? 'spin' : ''} />
          Actualiser
        </button>
      </div>

      {/* KPI Cards */}
      <div className="dashboard__kpis">
        <KPICard
          title="Chiffre d'affaires total"
          value={caValue}
          unit="FCFA"
          icon={DollarSign}
          color="primary"
          loading={caTotal.loading}
          error={caTotal.error}
        />
        <KPICard
          title="Stocks sous seuil"
          value={stocksAlerte.data?.rows?.length ?? null}
          unit="produits"
          icon={AlertTriangle}
          color={stocksAlerte.data?.rows?.length > 0 ? 'danger' : 'ok'}
          loading={stocksAlerte.loading}
          error={stocksAlerte.error}
        />
        <KPICard
          title="Lots expirant < 30j"
          value={lotsPerimables.data?.rows?.length ?? null}
          unit="lots"
          icon={Clock}
          color={lotsPerimables.data?.rows?.length > 0 ? 'warning' : 'ok'}
          loading={lotsPerimables.loading}
          error={lotsPerimables.error}
        />
        <KPICard
          title="Ruptures de stock"
          value={rupturesValue}
          unit="total"
          icon={ShoppingCart}
          color="secondary"
          loading={ruptures.loading}
          error={ruptures.error}
        />
      </div>

      {/* Graphiques */}
      <div className="dashboard__charts">
        <div className="chart-card">
          <h2 className="chart-card__title">
            <TrendingUp size={16} /> Évolution CA par mois
          </h2>
          <div className="chart-card__body">
            {caMensuel.loading && <p className="chart-card__state">Chargement…</p>}
            {caMensuel.error   && <p className="chart-card__state">Erreur</p>}
            {!caMensuel.loading && caMensuelData.length > 0 && (
              <SalesLineChart data={caMensuelData} xKey="mois" yKey="ca_total" />
            )}
          </div>
        </div>

        <div className="chart-card">
          <h2 className="chart-card__title">
            <Package size={16} /> Top 5 produits vendus
          </h2>
          <div className="chart-card__body">
            {topProduits.loading && <p className="chart-card__state">Chargement…</p>}
            {topProduits.error   && <p className="chart-card__state">Erreur</p>}
            {!topProduits.loading && topProduitsData.length > 0 && (
              <RankingBarChart data={topProduitsData} xKey="produit" yKey="quantite_vendue" />
            )}
          </div>
        </div>
      </div>

      {/* Alertes */}
      <div className="dashboard__alerts">
        <AlertTable
          title="Stocks sous seuil de sécurité"
          columns={stocksAlerte.data?.columns ?? []}
          rows={stocksAlerte.data?.rows ?? null}
          loading={stocksAlerte.loading}
          error={stocksAlerte.error}
          severity="danger"
        />
        <AlertTable
          title="Lots expirant dans 30 jours"
          columns={lotsPerimables.data?.columns ?? []}
          rows={lotsPerimables.data?.rows ?? null}
          loading={lotsPerimables.loading}
          error={lotsPerimables.error}
          severity="warning"
        />
      </div>

      {/* Alertes intelligentes — narration LLM */}
      <div className="dashboard__section">
        <h2 className="dashboard__section-title">
          <Zap size={16} /> Alertes intelligentes
        </h2>
        {alertsLoading ? (
          <p className="chart-card__state">Analyse en cours…</p>
        ) : (
          <div className="alert-insights">
            {alerts.map(alert => (
              <AlertInsightCard key={alert.id} alert={alert} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

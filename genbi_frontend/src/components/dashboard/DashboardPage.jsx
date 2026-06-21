import { useState } from 'react'
import { RefreshCw, DollarSign, TrendingUp, Package, AlertTriangle, Clock, ShoppingCart, Zap, Maximize2, X, PieChart } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useDashboard } from '../../hooks/useDashboard'
import { useAlerts } from '../../hooks/useAlerts'
import { KPICard } from './KPICard'
import { AlertTable } from './AlertTable'
import { RankingBarChart } from '../visualizations/RankingBarChart'
import { SalesLineChart } from '../visualizations/SalesLineChart'
import { GenericsPieChart } from '../visualizations/GenericsPieChart'

function buildChartData(columns, rows) {
  if (!rows || !columns) return []
  return rows.map(row => {
    const obj = {}
    columns.forEach((col, i) => { obj[col] = row[i] })
    return obj
  })
}

function derivePeriod(rows, monthsShort) {
  if (!rows || rows.length === 0) return null
  const first = rows[0][0]
  const last  = rows[rows.length - 1][0]
  if (!first || !last) return null
  const a = monthsShort[first - 1]
  const b = monthsShort[last  - 1]
  return a === b ? a : `${a}–${b}`
}

function AlertInsightCard({ alert }) {
  const { t } = useTranslation()
  const SEVERITY_LABEL = {
    danger:  t('dashboard.alert_severity_danger'),
    warning: t('dashboard.alert_severity_warning'),
    info:    t('dashboard.alert_severity_info'),
  }
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
        <span className="alert-insight-card__count">
          {t(alert.row_count === 1 ? 'dashboard.alert_results_one' : 'dashboard.alert_results_other', { count: alert.row_count })}
        </span>
      </div>
      {alert.row_count === 0 ? (
        <p className="alert-insight-card__empty">{t('dashboard.alert_none')}</p>
      ) : (
        <p className="alert-insight-card__insight">{alert.insight}</p>
      )}
    </div>
  )
}

function FullscreenOverlay({ title, children, onClose }) {
  return (
    <div className="fullscreen-overlay" onClick={onClose}>
      <div className="fullscreen-overlay__content" onClick={e => e.stopPropagation()}>
        <div className="fullscreen-overlay__header">
          <span className="fullscreen-overlay__title">{title}</span>
          <button className="fullscreen-overlay__close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <div className="fullscreen-overlay__body">{children}</div>
      </div>
    </div>
  )
}

export function DashboardPage() {
  const { t } = useTranslation()
  const monthsShort = t('months.short', { returnObjects: true })
  const {
    caTotal, caMensuel, topProduits, genericsSplit,
    stocksAlerte, lotsPerimables, ruptures,
    isLoading, refetchAll,
    period, setPeriod,
  } = useDashboard()
  const { alerts, loading: alertsLoading, refetch: refetchAlerts } = useAlerts()
  const [fullscreen, setFullscreen] = useState(null)

  const caValue = caTotal.data?.rows?.[0]?.[0] ?? null
  const rupturesValue = ruptures.data?.rows?.[0]?.[0] ?? null

  const caMensuelData   = buildChartData(caMensuel.data?.columns,  caMensuel.data?.rows)
  const topProduitsData = buildChartData(topProduits.data?.columns, topProduits.data?.rows)
  const sparklineData   = caMensuel.data?.rows?.map(r => ({ v: Number(r[1]) })) ?? []

  const PERIOD_OPTIONS = [
    { key: 'all', label: t('dashboard.period_all') },
    { key: '30j', label: t('dashboard.period_30d') },
    { key: '7j',  label: t('dashboard.period_7d') },
  ]

  const period_str = derivePeriod(caMensuel.data?.rows, monthsShort)

  return (
    <div className="dashboard">

      {/* En-tête */}
      <div className="dashboard__header">
        <div>
          <h1 className="dashboard__title">{t('dashboard.title')}</h1>
          <p className="dashboard__subtitle">
            {t('dashboard.subtitle')}{period_str ? ` — ${t('dashboard.subtitle_period', { period: period_str })}` : ''}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div className="period-filter">
            {PERIOD_OPTIONS.map(opt => (
              <button
                key={opt.key}
                className={`period-filter__btn${period === opt.key ? ' period-filter__btn--active' : ''}`}
                onClick={() => setPeriod(opt.key)}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <button
            className="dashboard__refresh"
            onClick={() => { refetchAll(); refetchAlerts() }}
            disabled={isLoading || alertsLoading}
            title={t('dashboard.refresh')}
          >
            <RefreshCw size={15} className={(isLoading || alertsLoading) ? 'spin' : ''} />
            {t('dashboard.refresh')}
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="dashboard__kpis">
        <KPICard
          title={t('dashboard.kpi_ca_total')}
          value={caValue}
          unit="FCFA"
          icon={DollarSign}
          color="primary"
          loading={caTotal.loading}
          error={caTotal.error}
          sparklineData={sparklineData}
        />
        <KPICard
          title={t('dashboard.kpi_stocks')}
          value={stocksAlerte.data?.rows?.length ?? null}
          unit={t('dashboard.kpi_unit_products')}
          icon={AlertTriangle}
          color={stocksAlerte.data?.rows?.length > 0 ? 'danger' : 'ok'}
          loading={stocksAlerte.loading}
          error={stocksAlerte.error}
        />
        <KPICard
          title={t('dashboard.kpi_lots')}
          value={lotsPerimables.data?.rows?.length ?? null}
          unit="lots"
          icon={Clock}
          color={lotsPerimables.data?.rows?.length > 0 ? 'warning' : 'ok'}
          loading={lotsPerimables.loading}
          error={lotsPerimables.error}
        />
        <KPICard
          title={t('dashboard.kpi_ruptures')}
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
          <div className="chart-card__header">
            <h2 className="chart-card__title">
              <TrendingUp size={16} /> {t('dashboard.chart_ca_monthly')}
            </h2>
            <button className="chart-card__fullscreen-btn" onClick={() => setFullscreen('line')} title="Plein écran">
              <Maximize2 size={13} />
            </button>
          </div>
          <div className="chart-card__body">
            {caMensuel.loading && <p className="chart-card__state">{t('dashboard.loading')}</p>}
            {caMensuel.error   && <p className="chart-card__state">{t('dashboard.kpi_error')}</p>}
            {!caMensuel.loading && caMensuelData.length > 0 && (
              <SalesLineChart data={caMensuelData} xKey="mois" yKey="ca_total" months={monthsShort} />
            )}
            {!caMensuel.loading && !caMensuel.error && caMensuelData.length === 0 && (
              <p className="chart-card__state">{t('dashboard.chart_ca_empty')}</p>
            )}
          </div>
        </div>

        <div className="chart-card">
          <div className="chart-card__header">
            <h2 className="chart-card__title">
              <Package size={16} /> {t('dashboard.chart_top5')}
            </h2>
            <button className="chart-card__fullscreen-btn" onClick={() => setFullscreen('bar')} title="Plein écran">
              <Maximize2 size={13} />
            </button>
          </div>
          <div className="chart-card__body">
            {topProduits.loading && <p className="chart-card__state">{t('dashboard.loading')}</p>}
            {topProduits.error   && <p className="chart-card__state">{t('dashboard.kpi_error')}</p>}
            {!topProduits.loading && topProduitsData.length > 0 && (
              <RankingBarChart data={topProduitsData} xKey="produit" yKey="quantite_vendue" />
            )}
          </div>
        </div>

        <div className="chart-card">
          <div className="chart-card__header">
            <h2 className="chart-card__title">
              <PieChart size={16} /> {t('dashboard.chart_generics')}
            </h2>
            <button className="chart-card__fullscreen-btn" onClick={() => setFullscreen('pie')} title="Plein écran">
              <Maximize2 size={13} />
            </button>
          </div>
          <div className="chart-card__body">
            {genericsSplit.loading && <p className="chart-card__state">{t('dashboard.loading')}</p>}
            {genericsSplit.error   && <p className="chart-card__state">{t('dashboard.kpi_error')}</p>}
            {!genericsSplit.loading && genericsSplit.data?.rows?.length > 0 && (
              <GenericsPieChart rows={genericsSplit.data.rows} />
            )}
          </div>
        </div>
      </div>

      {/* Alertes */}
      <div className="dashboard__alerts">
        <AlertTable
          title={t('dashboard.alert_stocks_title')}
          columns={stocksAlerte.data?.columns ?? []}
          rows={stocksAlerte.data?.rows ?? null}
          loading={stocksAlerte.loading}
          error={stocksAlerte.error}
          severity="danger"
        />
        <AlertTable
          title={t('dashboard.alert_lots_title')}
          columns={lotsPerimables.data?.columns ?? []}
          rows={lotsPerimables.data?.rows ?? null}
          loading={lotsPerimables.loading}
          error={lotsPerimables.error}
          severity="warning"
        />
      </div>

      {/* Alertes intelligentes */}
      <div className="dashboard__section">
        <h2 className="dashboard__section-title">
          <Zap size={16} /> {t('dashboard.alerts_title')}
        </h2>
        {alertsLoading ? (
          <p className="chart-card__state">{t('dashboard.loading')}</p>
        ) : (
          <div className="alert-insights">
            {alerts.map(alert => (
              <AlertInsightCard key={alert.id} alert={alert} />
            ))}
          </div>
        )}
      </div>

      {/* Plein écran overlay */}
      {fullscreen === 'line' && (
        <FullscreenOverlay title={t('dashboard.chart_ca_monthly')} onClose={() => setFullscreen(null)}>
          {caMensuelData.length > 0
            ? <SalesLineChart data={caMensuelData} xKey="mois" yKey="ca_total" months={monthsShort} />
            : <p className="chart-card__state">{t('dashboard.chart_ca_empty')}</p>}
        </FullscreenOverlay>
      )}
      {fullscreen === 'bar' && (
        <FullscreenOverlay title={t('dashboard.chart_top5')} onClose={() => setFullscreen(null)}>
          {topProduitsData.length > 0
            ? <RankingBarChart data={topProduitsData} xKey="produit" yKey="quantite_vendue" />
            : <p className="chart-card__state">{t('dashboard.chart_ca_empty')}</p>}
        </FullscreenOverlay>
      )}
      {fullscreen === 'pie' && (
        <FullscreenOverlay title={t('dashboard.chart_generics')} onClose={() => setFullscreen(null)}>
          {genericsSplit.data?.rows?.length > 0
            ? <GenericsPieChart rows={genericsSplit.data.rows} />
            : <p className="chart-card__state">{t('dashboard.chart_ca_empty')}</p>}
        </FullscreenOverlay>
      )}
    </div>
  )
}

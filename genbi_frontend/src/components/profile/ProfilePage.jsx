import { useState, useEffect } from 'react'
import { User, MapPin, Building2, TrendingUp, Package, ShoppingCart, LogOut } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { authApi, chatApi } from '../../services/api'

function formatNumber(val) {
  if (val === null || val === undefined) return '—'
  return new Intl.NumberFormat('fr-FR').format(Math.round(Number(val)))
}

function StatItem({ icon: Icon, label, value, unit }) {
  return (
    <div className="profile-stat">
      <div className="profile-stat__icon"><Icon size={16} /></div>
      <div className="profile-stat__info">
        <span className="profile-stat__label">{label}</span>
        <span className="profile-stat__value">{formatNumber(value)}<span className="profile-stat__unit"> {unit}</span></span>
      </div>
    </div>
  )
}

export function ProfilePage({ onLogout }) {
  const { t } = useTranslation()
  const [user, setUser] = useState(null)
  const [pharmacy, setPharmacy] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const u = await authApi.me()
        setUser(u)

        const pharmRes = await chatApi.executeSQL(
          `SELECT pharmacy_name, city, district FROM marts.dim_pharmacies WHERE pharmacy_id = current_setting('app.current_pharmacy_id', true)::int LIMIT 1`,
          1
        )
        if (pharmRes?.rows?.length) {
          const [name, city, district] = pharmRes.rows[0]
          setPharmacy({ name, city, district })
        }

        const statsRes = await chatApi.executeSQL(
          `SELECT
            SUM(total_amount_fcfa) AS ca_total,
            COUNT(*) AS total_ventes,
            (SELECT COUNT(*) FROM marts.fct_missed_sales) AS ruptures
          FROM marts.fct_sales`,
          1
        )
        if (statsRes?.rows?.length) {
          const [ca, ventes, rups] = statsRes.rows[0]
          setStats({ ca, ventes, ruptures: rups })
        }
      } catch (_) {}
      finally { setLoading(false) }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="profile-page">
        <div className="profile-loading">{t('profile.loading')}</div>
      </div>
    )
  }

  return (
    <div className="profile-page">
      <div className="profile-header">
        <div className="profile-avatar">
          <User size={32} />
        </div>
        <div className="profile-identity">
          <h1 className="profile-name">{pharmacy?.name ?? `Pharmacie #${user?.pharmacy_id}`}</h1>
          <p className="profile-email">{user?.email}</p>
          <span className="profile-role">
            {user?.role === 'admin' ? t('profile.role_admin') : t('profile.role_pharmacist')}
          </span>
        </div>
        <button className="profile-logout" onClick={onLogout} title={t('app.logout')}>
          <LogOut size={15} />
          <span>{t('profile.logout')}</span>
        </button>
      </div>

      <div className="profile-cards">
        <div className="profile-card">
          <h2 className="profile-card__title">{t('profile.section_info')}</h2>
          <div className="profile-info-list">
            {pharmacy?.city && (
              <div className="profile-info-item">
                <Building2 size={14} className="profile-info-item__icon" />
                <span>{pharmacy.city}</span>
              </div>
            )}
            {pharmacy?.district && (
              <div className="profile-info-item">
                <MapPin size={14} className="profile-info-item__icon" />
                <span>{t('profile.district')} {pharmacy.district}</span>
              </div>
            )}
            <div className="profile-info-item">
              <User size={14} className="profile-info-item__icon" />
              <span>{t('profile.pharmacy_id')}{user?.pharmacy_id}</span>
            </div>
          </div>
        </div>

        {stats && (
          <div className="profile-card">
            <h2 className="profile-card__title">{t('profile.section_stats')}</h2>
            <div className="profile-stats-grid">
              <StatItem icon={TrendingUp} label={t('profile.stat_ca')} value={stats.ca} unit="FCFA" />
              <StatItem icon={Package} label={t('profile.stat_sales')} value={stats.ventes} unit="transactions" />
              <StatItem icon={ShoppingCart} label={t('profile.stat_ruptures')} value={stats.ruptures} unit="enregistrées" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

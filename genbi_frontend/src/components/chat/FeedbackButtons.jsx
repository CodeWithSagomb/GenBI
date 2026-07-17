import { useTranslation } from 'react-i18next'

export function FeedbackButtons({ onFeedback, feedback }) {
  const { t } = useTranslation()
  const voted = feedback !== null && feedback !== undefined

  return (
    <div className="feedback-buttons">
      {voted ? (
        <span className="feedback-buttons__confirmation">{t('chat.feedback_thanks')}</span>
      ) : null}
      <button
        className={`feedback-btn ${feedback === 'good' ? 'feedback-btn--active' : ''}`}
        onClick={() => onFeedback('good')}
        disabled={voted}
        aria-label={`👍 ${t('chat.feedback_good')}`}
      >
        👍
      </button>
      <button
        className={`feedback-btn ${feedback === 'bad' ? 'feedback-btn--active' : ''}`}
        onClick={() => onFeedback('bad')}
        disabled={voted}
        aria-label={`👎 ${t('chat.feedback_bad')}`}
      >
        👎
      </button>
    </div>
  )
}

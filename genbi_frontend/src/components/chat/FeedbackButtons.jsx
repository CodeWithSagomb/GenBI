export function FeedbackButtons({ onFeedback, feedback }) {
  const voted = feedback !== null && feedback !== undefined

  return (
    <div className="feedback-buttons">
      {voted ? (
        <span className="feedback-buttons__confirmation">Merci pour votre retour</span>
      ) : null}
      <button
        className={`feedback-btn ${feedback === 'good' ? 'feedback-btn--active' : ''}`}
        onClick={() => onFeedback('good')}
        disabled={voted}
        aria-label="👍 Bonne réponse"
      >
        👍
      </button>
      <button
        className={`feedback-btn ${feedback === 'bad' ? 'feedback-btn--active' : ''}`}
        onClick={() => onFeedback('bad')}
        disabled={voted}
        aria-label="👎 Mauvaise réponse"
      >
        👎
      </button>
    </div>
  )
}

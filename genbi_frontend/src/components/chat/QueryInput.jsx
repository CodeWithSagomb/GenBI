import { useState } from 'react'
import { useTranslation } from 'react-i18next'

export function QueryInput({ onSubmit, disabled }) {
  const { t } = useTranslation()
  const [value, setValue] = useState('')

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function submit() {
    if (!value.trim() || disabled) return
    onSubmit(value.trim())
    setValue('')
  }

  return (
    <div className="query-input-wrapper">
      <input
        data-testid="query-input"
        className="query-input"
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={t('chat.placeholder')}
        disabled={disabled}
        autoComplete="off"
      />
      <button
        data-testid="send-button"
        className="send-button"
        onClick={submit}
        disabled={disabled || !value.trim()}
      >
        {t('chat.send')}
      </button>
    </div>
  )
}

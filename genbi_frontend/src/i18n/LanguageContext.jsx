import { createContext, useContext, useState } from 'react'
import i18n from './index'

const LanguageContext = createContext(null)

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('genbi_lang') || 'fr')

  function toggleLang() {
    const next = lang === 'fr' ? 'en' : 'fr'
    localStorage.setItem('genbi_lang', next)
    i18n.changeLanguage(next)
    setLang(next)
  }

  return (
    <LanguageContext.Provider value={{ lang, toggleLang }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLang() {
  return useContext(LanguageContext)
}

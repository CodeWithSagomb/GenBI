import '@testing-library/jest-dom'
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import fr from '../src/i18n/fr.json'
import en from '../src/i18n/en.json'

// JSDOM n'implémente pas scrollIntoView — mock global pour tous les tests
window.HTMLElement.prototype.scrollIntoView = function () {}

// Vitest 4.x + jsdom : localStorage n'est pas auto-attaché au global avant le premier test
if (!globalThis.localStorage) {
  const _store = {}
  Object.defineProperty(globalThis, 'localStorage', {
    value: {
      getItem:    (k)    => Object.prototype.hasOwnProperty.call(_store, k) ? _store[k] : null,
      setItem:    (k, v) => { _store[k] = String(v) },
      removeItem: (k)    => { delete _store[k] },
      clear:      ()     => { Object.keys(_store).forEach(k => delete _store[k]) },
    },
    writable: true,
  })
}

// Initialiser i18n en français pour tous les tests
if (!i18n.isInitialized) {
  i18n.use(initReactI18next).init({
    resources: { fr: { translation: fr }, en: { translation: en } },
    lng: 'fr',
    fallbackLng: 'fr',
    interpolation: { escapeValue: false },
  })
}

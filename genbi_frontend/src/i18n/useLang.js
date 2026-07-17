import { useContext } from 'react'
import { LanguageContext } from './LanguageContext'

export function useLang() {
  return useContext(LanguageContext)
}

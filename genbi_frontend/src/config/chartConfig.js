// Règles de visualisation frontend — modifier ici pour changer le comportement des charts.
// ChartRouter.jsx importe ce fichier : zéro regex hardcodée dans les composants.

export const CHART_CONFIG = {
  // Colonnes temporelles → line chart (col[0] est une date/période)
  dateColumnPattern: /date|jour|semaine|mois|month/i,

  // Colonnes catégorielles → éligibles au pie chart
  pieColumnPattern: /généri|generic|princep|type|mode|assur|insur|payment|catég|categ|répart|segment|classe|form|thérap|origin|wholesaler|fournis|laborat|labo\b|pays\b|country|sexe|gender/i,

  // Colonnes exclues de la détection pie (faux positifs : insurer_id, insurer_share_fcfa)
  excludeColumnPattern: /_id$|_fcfa$/i,

  // Colonnes ID — exclues des axes de valeur dans pickChartKeys / pickComboKeys
  idColumnPattern: /_id$/i,

  // Nombre maximum de lignes pour afficher un pie chart
  pieMaxRows: 10,
}

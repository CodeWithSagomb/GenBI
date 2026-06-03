import '@testing-library/jest-dom'

// JSDOM n'implémente pas scrollIntoView — mock global pour tous les tests
window.HTMLElement.prototype.scrollIntoView = function () {}

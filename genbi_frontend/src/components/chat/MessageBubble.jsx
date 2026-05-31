export function MessageBubble({ role, children }) {
  return (
    <div className={`message-bubble message-bubble--${role}`}>
      {children}
    </div>
  )
}

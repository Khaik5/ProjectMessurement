export default function Toast({ message, type = 'info', onClose }) {
  if (!message) return null;
  return (
    <div className={`toast toast-${type}`}>
      <span>{message}</span>
      <button onClick={onClose}>x</button>
    </div>
  );
}

export default function Button({ children, variant = 'primary', loading = false, className = '', ...props }) {
  return (
    <button {...props} className={`btn btn-${variant} ${loading ? 'is-loading' : ''} ${className}`} disabled={loading || props.disabled}>
      {loading ? <span className="btn-spinner" aria-hidden="true" /> : null}
      {children}
    </button>
  );
}

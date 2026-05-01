export default function SectionHeader({ eyebrow, title, description, actions, compact = false }) {
  return (
    <div className={`section-header ${compact ? 'section-header-compact' : ''}`}>
      <div>
        {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
        <h2>{title}</h2>
        {description ? <p className="muted">{description}</p> : null}
      </div>
      {actions ? <div className="button-row">{actions}</div> : null}
    </div>
  );
}

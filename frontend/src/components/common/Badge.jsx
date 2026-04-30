import { riskClass } from '../../utils/riskUtils.js';

export default function Badge({ children, level }) {
  return <span className={`badge ${level ? riskClass(level) : ''}`}>{children || level}</span>;
}

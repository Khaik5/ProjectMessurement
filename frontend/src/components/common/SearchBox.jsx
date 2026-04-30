import { Search } from 'lucide-react';

export default function SearchBox({ value, onChange, placeholder = 'Search modules...' }) {
  return (
    <label className="search-box">
      <Search size={18} />
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} />
    </label>
  );
}

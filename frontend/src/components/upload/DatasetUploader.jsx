import { useState } from 'react';
import { UploadCloud } from 'lucide-react';

const allowed = ['csv', 'json'];

export default function DatasetUploader({ onUpload, disabled }) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');

  function submit(file) {
    if (!file || disabled) return;
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!allowed.includes(ext)) {
      setError('Use CSV or JSON.');
      return;
    }
    setError('');
    onUpload(file);
  }

  return (
    <label
      className={`upload-box ${dragging ? 'is-dragging' : ''}`}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        submit(event.dataTransfer.files?.[0]);
      }}
    >
      <input type="file" accept=".csv,.json" disabled={disabled} onChange={(event) => {
        submit(event.target.files?.[0]);
        event.target.value = '';
      }} />
      <UploadCloud size={34} />
      <strong>Drop metrics file</strong>
      <span>CSV or JSON</span>
      {error ? <small className="field-error">{error}</small> : null}
    </label>
  );
}

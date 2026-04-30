import { UploadCloud } from 'lucide-react';

export default function DatasetUploader({ onUpload, disabled }) {
  return (
    <label className="upload-box">
      <input type="file" accept=".csv,.json" disabled={disabled} onChange={(event) => {
        const file = event.target.files?.[0];
        if (file) onUpload(file);
        event.target.value = '';
      }} />
      <UploadCloud size={36} />
      <strong>Drag and drop your metrics here</strong>
      <span>or click to browse CSV/JSON files</span>
    </label>
  );
}

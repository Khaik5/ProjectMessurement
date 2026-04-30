export default function TrainingGuide({ guide }) {
  const steps = guide?.steps || [
    'Upload a dataset containing module_name, loc, complexity, coupling, code_churn, defect_label.',
    'defect_label must use 0 for No Defect and 1 for Defect.',
    'Train the production model to compare Logistic Regression, Random Forest, and Neural Network.',
    'The best model is selected by F1-score, then ROC-AUC.',
    'Return to Metrics Explorer and analyze the target dataset.'
  ];
  return (
    <div className="warning-panel">
      <strong>{guide?.title || 'Training guide'}</strong>
      <ol style={{ margin: '10px 0 0 18px', padding: 0 }}>
        {steps.map((step) => <li key={step}>{step}</li>)}
      </ol>
    </div>
  );
}

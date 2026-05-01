export default function TrainingGuide() {
  const steps = [
    'Use a labeled dataset.',
    'Train all algorithms.',
    'Activate the best model.',
    'Run analysis.'
  ];
  return (
    <div className="metric-panel">
      <strong>Training workflow</strong>
      <div className="model-score">
        {steps.map((step, index) => <span className="badge" key={step}>{index + 1}. {step}</span>)}
      </div>
    </div>
  );
}

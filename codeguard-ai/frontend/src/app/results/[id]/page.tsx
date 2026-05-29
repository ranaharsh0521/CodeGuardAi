import ResultsClient from './ResultsClient';

export function generateStaticParams() {
  return [{ id: 'demo' }];
}

export default function ScanResultsPage() {
  return <ResultsClient />;
}

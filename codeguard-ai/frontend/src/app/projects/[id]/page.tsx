import ProjectClient from './ProjectClient';

export function generateStaticParams() {
  return [{ id: 'demo' }];
}

export default function ProjectDetailPage() {
  return <ProjectClient />;
}

import { artifactColors } from '../theme';

// A use case (left) linked to a class (right) – the core idea of the tool.
export default function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#0f172a" />
      <path d="M11 11 C 17 11, 15 21, 21 21" stroke="#38bdf8" strokeWidth="2.2" fill="none" strokeLinecap="round" />
      <rect x="5" y="7.5" width="8" height="7" rx="2" fill={artifactColors.useCase} />
      <rect x="19" y="17.5" width="8" height="7" rx="2" fill={artifactColors.javaClass} />
    </svg>
  );
}

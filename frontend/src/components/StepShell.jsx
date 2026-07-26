export default function StepShell({ eyebrow, title, description, children, onBack, onNext, nextLabel = '下一步', nextDisabled = false }) {
  return (
    <div className="w-full max-w-lg mx-auto">
      <p className="font-display text-sm font-bold tracking-wide text-amber-700 mb-2" style={{ color: 'var(--color-amber)' }}>
        {eyebrow}
      </p>
      <h2 className="font-display text-2xl font-extrabold mb-2" style={{ color: 'var(--color-teal)' }}>
        {title}
      </h2>
      {description && <p className="text-base text-ink/70 mb-6 leading-relaxed">{description}</p>}

      <div className="space-y-3 mb-8">{children}</div>

      <div className="flex items-center gap-3">
        {onBack && (
          <button
            onClick={onBack}
            className="px-5 py-3 rounded-xl font-medium text-base border-2 transition-colors"
            style={{ borderColor: 'var(--color-sage)', color: 'var(--color-teal)' }}
          >
            上一步
          </button>
        )}
        {onNext && (
          <button
            onClick={onNext}
            disabled={nextDisabled}
            className="flex-1 px-5 py-3 rounded-xl font-bold text-base text-white transition-opacity disabled:opacity-40"
            style={{ backgroundColor: 'var(--color-teal)' }}
          >
            {nextLabel}
          </button>
        )}
      </div>
    </div>
  );
}

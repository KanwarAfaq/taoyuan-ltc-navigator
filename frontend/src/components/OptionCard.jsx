export default function OptionCard({ label, sublabel, selected, onClick }) {
  return (
    <button
      onClick={onClick}
      aria-pressed={selected}
      className="w-full text-left px-5 py-4 rounded-xl border-2 transition-colors flex items-center justify-between gap-4"
      style={{
        borderColor: selected ? 'var(--color-teal)' : 'var(--color-sage)',
        backgroundColor: selected ? 'var(--color-sage-light)' : 'white',
      }}
    >
      <span>
        <span className="block font-semibold text-base" style={{ color: 'var(--color-ink)' }}>{label}</span>
        {sublabel && <span className="block text-sm text-ink/60 mt-0.5">{sublabel}</span>}
      </span>
      <span
        className="shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center"
        style={{ borderColor: selected ? 'var(--color-teal)' : 'var(--color-sage)' }}
      >
        {selected && <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: 'var(--color-teal)' }} />}
      </span>
    </button>
  );
}

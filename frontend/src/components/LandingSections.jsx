import content from '../seo/content.json';

/** Crawlable content under the wizard. Copy lives in src/seo/content.json (shared with the build-time head + fallback HTML). */
export default function LandingSections() {
  const c = content;
  return (
    <div className="w-full max-w-3xl mx-auto space-y-10 px-1">
      <img src="/hero.svg" alt={c.heroAlt} width="640" height="400" className="w-full max-w-md mx-auto rounded-2xl" loading="lazy" />
      {c.sections.map((s) => (
        <section key={s.id} id={s.id} className="scroll-mt-4">
          <h2 className="font-display text-xl font-extrabold mb-3" style={{ color: 'var(--color-teal)' }}>{s.h2}</h2>
          <ul className="grid gap-3 sm:grid-cols-2">
            {s.items.map((i) => (
              <li key={i.t} className="rounded-xl border-2 p-4 bg-white" style={{ borderColor: 'var(--color-sage)' }}>
                <h3 className="font-semibold">{i.t}</h3>
                <p className="text-sm text-ink/70 mt-1 leading-relaxed">{i.d}</p>
              </li>
            ))}
          </ul>
        </section>
      ))}
      <section id="faq" className="scroll-mt-4">
        <h2 className="font-display text-xl font-extrabold mb-3" style={{ color: 'var(--color-teal)' }}>{c.faqTitle}</h2>
        <div className="space-y-2">
          {c.faq.map((f) => (
            <details key={f.q} className="rounded-xl border-2 p-4 bg-white" style={{ borderColor: 'var(--color-sage)' }}>
              <summary className="cursor-pointer font-medium">{f.q}</summary>
              <p className="mt-2 text-sm text-ink/70 leading-relaxed">{f.a}</p>
            </details>
          ))}
        </div>
      </section>
      <section id="resources" className="scroll-mt-4 pb-10">
        <h2 className="font-display text-xl font-extrabold mb-3" style={{ color: 'var(--color-teal)' }}>{c.refsTitle}</h2>
        <ul className="space-y-2 text-sm">
          {[...c.refs, ...c.related].map((r) => (
            <li key={r.href}>
              <a href={r.href} target="_blank" rel="noopener noreferrer" className="underline" style={{ color: 'var(--color-teal-light)' }}>{r.label} ↗</a>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

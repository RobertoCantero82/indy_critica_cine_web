import { useEffect, useRef } from 'react'

function useReveal() {
  const ref = useRef(null)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { el.classList.add('revealed'); obs.unobserve(el) } },
      { threshold: 0.1 }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])
  return ref
}

function Reveal({ children }) {
  const ref = useReveal()
  return <div ref={ref} className="reveal-block">{children}</div>
}

export default function Informe({ informe, videoId, onVolver }) {
  const cvp        = informe.critica_vs_publico || {}
  const bs         = informe.banda_sonora || {}
  const snack      = informe.snack || {}
  const plataformas  = informe.streaming_espana || []
  const alternativas = informe.alternativas || []

  return (
    <div style={{ paddingBottom: 80 }}>

      {/* ── TÍTULO ── */}
      <div className="up" style={{ padding: '72px 0 48px', borderBottom: '1px solid var(--border)' }}>
        <span className="inf-label">Análisis · Indy</span>
        <h2 style={{
          fontFamily: 'var(--font-title)',
          fontSize: 'clamp(40px,7vw,80px)',
          color: 'var(--text)',
          letterSpacing: 5, lineHeight: 1, marginBottom: 16,
        }}>
          {informe.titulo_anio}
        </h2>
        <div style={{ width: 80, height: 3, background: 'var(--gold)', marginTop: 24 }} />
      </div>

      {/* ── VEREDICTO ── */}
      <Reveal>
        <div className="inf-section">
          <span className="inf-label">Veredicto</span>

          {/* Pastilla SÍ / NO */}
          {informe.veredicto_recomendacion && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 20 }}>
              <div style={{
                fontFamily: 'var(--font-title)',
                fontSize: 52,
                letterSpacing: 4,
                lineHeight: 1,
                color: informe.veredicto_recomendacion === 'SÍ' ? '#4caf50' : '#e53935',
                border: `3px solid ${informe.veredicto_recomendacion === 'SÍ' ? '#4caf50' : '#e53935'}`,
                padding: '6px 24px',
                boxShadow: `4px 4px 0 ${informe.veredicto_recomendacion === 'SÍ' ? '#2e7d32' : '#b71c1c'}`,
              }}>
                {informe.veredicto_recomendacion === 'SÍ' ? '✓ SÍ' : '✗ NO'}
              </div>
              {informe.veredicto_razon && (
                <p style={{
                  fontFamily: 'var(--font-title)',
                  fontSize: 22,
                  letterSpacing: 2,
                  color: 'var(--text)',
                  lineHeight: 1.3,
                }}>
                  {informe.veredicto_razon}
                </p>
              )}
            </div>
          )}

          {/* Párrafo */}
          <p className="veredicto">{informe.veredicto}</p>
        </div>
      </Reveal>

      {/* ── PUNTUACIONES ── */}
      <Reveal>
        <div className="inf-section">
          <span className="inf-label">Crítica vs Público</span>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, marginBottom: 20 }}>
            {[
              { n: cvp.puntuacion_critica ?? '—', suf: cvp.puntuacion_critica ? '/10' : '', l: 'Crítica' },
              { n: cvp.puntuacion_publico ?? '—', suf: cvp.puntuacion_publico ? '/10' : '', l: 'Público' },
              { n: cvp.quien_gana === 'publico' ? 'Público' : cvp.quien_gana === 'critica' ? 'Crítica' : 'Empate', suf: '', l: 'Gana' },
            ].map((s, i) => (
              <div key={i} className="score-block">
                <div className="score-n">
                  {s.n}{s.suf && <span style={{ fontSize: 20, color: 'var(--gold-dim)' }}>{s.suf}</span>}
                </div>
                <div className="score-l">{s.l}</div>
              </div>
            ))}
          </div>
          {cvp.comentario && (
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 18, color: 'var(--text-2)', fontStyle: 'italic' }}>
              {cvp.comentario}
            </p>
          )}
        </div>
      </Reveal>

      {/* ── GIROS + POST-CRÉDITOS ── */}
      <Reveal>
        <div className="inf-section" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {[
            { label: 'Índice de giros', value: informe.indice_giros },
            { label: 'Post-créditos',   value: informe.post_creditos === 'sí' ? '✅ Quédate' : informe.post_creditos === 'no' ? '❌ Puedes salir' : '— Sin datos' },
          ].map((d, i) => (
            <div key={i} style={{ background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border)', padding: '28px 24px' }}>
              <span className="inf-label">{d.label}</span>
              <p style={{ fontFamily: 'var(--font-body)', fontSize: 20, color: 'var(--text)' }}>{d.value}</p>
            </div>
          ))}
        </div>
      </Reveal>

      {/* ── STREAMING ── */}
      <Reveal>
        <div className="inf-section">
          <span className="inf-label">Disponible en España</span>
          {plataformas.length > 0 ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {plataformas.map(p => <span key={p} className="tag">{p}</span>)}
            </div>
          ) : (
            <p style={{ fontFamily: 'var(--font-body)', color: 'var(--text-3)', fontStyle: 'italic' }}>
              No disponible en streaming actualmente.
            </p>
          )}
        </div>
      </Reveal>

      {/* ── BANDA SONORA ── */}
      <Reveal>
        <div className="inf-section">
          <span className="inf-label">Banda Sonora</span>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 20, marginBottom: videoId ? 20 : 0, color: 'var(--text)' }}>
            <strong>{bs.compositor || 'Desconocido'}</strong>
            {bs.album && <span style={{ color: 'var(--text-2)' }}> — {bs.album}</span>}
          </p>
          {videoId && (
            <div style={{ border: '1px solid var(--border)' }}>
              <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10, background: 'rgba(0,0,0,0.6)' }}>
                <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--gold)', animation: 'pulse 2s infinite' }} />
                <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.2}}`}</style>
                <span style={{ fontFamily: 'var(--font-ui)', fontSize: 10, color: 'var(--gold)', letterSpacing: 2, textTransform: 'uppercase' }}>Reproduciendo</span>
              </div>
              <iframe width="100%" height="80"
                src={`https://www.youtube.com/embed/${videoId}?autoplay=1&controls=1`}
                allow="autoplay; encrypted-media" allowFullScreen style={{ display: 'block' }} />
            </div>
          )}
        </div>
      </Reveal>

      {/* ── SNACK ── */}
      <Reveal>
        <div className="inf-section">
          <span className="inf-label">Snack Recomendado</span>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: 20, color: 'var(--text)' }}>
            <strong>{snack.snack}</strong>
            {snack.justificacion && <span style={{ color: 'var(--text-2)' }}> — {snack.justificacion}</span>}
          </p>
        </div>
      </Reveal>

      {/* ── ALERTA INDY ── */}
      {informe.alerta_indy && (
        <Reveal>
          <div className="inf-section" style={{ borderLeft: '3px solid var(--gold)', paddingLeft: 24 }}>
            <span className="inf-label">🐾 Alerta Indy</span>
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 19, lineHeight: 1.75, color: 'var(--text)' }}>
              {informe.alerta_indy}
            </p>
          </div>
        </Reveal>
      )}

      {/* ── ALTERNATIVAS ── */}
      {alternativas.length > 0 && (
        <Reveal>
          <div className="inf-section">
            <span className="inf-label">Si no te convence, prueba esto</span>
            {alternativas.map((peli, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'baseline', gap: 20,
                padding: '14px 0',
                borderBottom: i < alternativas.length - 1 ? '1px solid var(--border)' : 'none',
              }}>
                <span style={{ fontFamily: 'var(--font-title)', fontSize: 16, color: 'var(--gold)', letterSpacing: 2, flexShrink: 0 }}>
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span style={{ fontFamily: 'var(--font-body)', fontSize: 20, color: 'var(--text)' }}>{peli}</span>
              </div>
            ))}
          </div>
        </Reveal>
      )}

      {/* ── THE END ── */}
      <Reveal>
        <div style={{ paddingTop: 56, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontFamily: 'var(--font-title)', fontSize: 32, color: 'var(--text-3)', letterSpacing: 4 }}>
            — FIN —
          </span>
          <button className="btn-secondary" onClick={onVolver}>← Nueva búsqueda</button>
        </div>
      </Reveal>

    </div>
  )
}

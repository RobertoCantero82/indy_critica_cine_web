import { useEffect, useRef, useState } from 'react'

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

function Reveal({ children, className = '', style }) {
  const ref = useReveal()
  return <div ref={ref} className={`reveal-block ${className}`} style={style}>{children}</div>
}

const GOLD   = '#c8a84b'
const TEXT   = '#f0ead8'
const TEXT2  = 'rgba(240,234,216,0.55)'
const BORDER = 'rgba(255,255,255,0.1)'

function Label({ children }) {
  return (
    <p style={{
      fontFamily: 'var(--font-ui)', fontSize: 10, fontWeight: 700,
      letterSpacing: 3, textTransform: 'uppercase',
      color: GOLD, marginBottom: 14,
    }}>✦ {children}</p>
  )
}

function GirosDots({ n, total = 4 }) {
  return (
    <span style={{ display: 'flex', gap: 4 }}>
      {Array.from({ length: total }, (_, i) => (
        <span key={i} style={{
          width: 10, height: 10, borderRadius: '50%',
          background: i < n ? GOLD : 'rgba(255,255,255,0.15)',
          display: 'inline-block',
        }} />
      ))}
    </span>
  )
}

function Dato({ label, value, valueStyle }) {
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '10px 0', borderBottom: `1px solid ${BORDER}`,
    }}>
      <span style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color: TEXT2, letterSpacing: 0.5 }}>{label}</span>
      <span style={{ fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 600, color: TEXT, ...valueStyle }}>{value}</span>
    </div>
  )
}

function Punt({ fuente, valor, sufijo, sub }) {
  return (
    <div className="score-item">
      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 10, color: TEXT2, letterSpacing: 2, textTransform: 'uppercase', marginBottom: 4 }}>{fuente}</p>
      <p style={{ fontFamily: 'var(--font-title)', fontSize: 32, color: TEXT, lineHeight: 1, margin: '6px 0' }}>
        {valor}{sufijo && <span style={{ fontSize: 12, color: GOLD }}>{sufijo}</span>}
      </p>
      <p style={{ fontFamily: 'var(--font-ui)', fontSize: 10, color: TEXT2, letterSpacing: 1 }}>{sub}</p>
    </div>
  )
}

function extraerVideoId(url) {
  if (!url) return ''
  const m = url.match(/(?:v=|youtu\.be\/|embed\/)([A-Za-z0-9_-]{11})/)
  return m ? m[1] : url
}

function girosANumero(texto) {
  if (!texto) return 0
  if (texto.includes('No te fíes')) return 4
  if (texto.includes('Bastantes'))  return 3
  if (texto.includes('Alguna'))     return 2
  return 1
}

function nivelDrama(indice, cvp) {
  if (cvp?.diferencia != null && Math.abs(cvp.diferencia) > 3) return 'Alto'
  if (indice.includes('No te fíes') || indice.includes('Bastantes')) return 'Alto'
  if (indice.includes('Alguna')) return 'Medio'
  return 'Bajo'
}

const PLATFORM_URLS = {
  'netflix': 'https://www.netflix.com/',
  'prime video': 'https://www.primevideo.com/',
  'disney+': 'https://www.disneyplus.com/',
  'hbo max': 'https://www.hbomax.com/',
  'max': 'https://www.max.com/',
  'skyshowtime': 'https://www.skyshowtime.com/',
  'movistar plus+': 'https://www.movistarplus.es/',
  'movistar+': 'https://www.movistarplus.es/',
  'filmin': 'https://www.filmin.es/',
  'apple tv': 'https://tv.apple.com/',
  'apple tv+': 'https://tv.apple.com/',
  'rtve play': 'https://www.rtve.es/play/',
  'atresplayer': 'https://www.atresplayer.com/',
  'mitele': 'https://www.mitele.es/',
  'rakuten tv': 'https://rakuten.tv/',
  'pluto tv': 'https://pluto.tv/',
}

function getPlatformUrl(p) {
  const name = (typeof p === 'object' ? p.nombre : p || '').toLowerCase().trim();
  for (const key in PLATFORM_URLS) {
    if (name.includes(key) || key.includes(name)) {
      return PLATFORM_URLS[key];
    }
  }
  return `https://www.google.com/search?q=${encodeURIComponent(name + ' streaming')}`;
}

export default function Informe({ informe, videoId, esLofi, posterUrl, onVolver, esSuerte }) {
  const [masAbierto, setMasAbierto] = useState(false)

  const [textoVeredicto, setTextoVeredicto] = useState('')

  useEffect(() => {
    if (!informe) return;
    const FRASES_SI = [
      "¡No te la puedes perder! 🍿",
      "¡Dale al play y disfruta! 🎬",
      "¡Una apuesta segura! 🚀",
      "¡Cine en estado puro! ✨",
      "¡Prepara las palomitas! 🍿"
    ];
    const FRASES_NO = [
      "¡No pierdas el tiempo! 🛑",
      "¡Apaga la tele! 📺",
      "¡Huye mientras puedas! 🏃",
      "¡Mejor busca otra cosa! 🔍",
      "¡Una pérdida de tiempo! ⏳"
    ];

    // Selección determinista según el título para mantener consistencia
    const titleStr = informe.titulo_anio || '';
    let charCodeSum = 0;
    for (let i = 0; i < titleStr.length; i++) {
      charCodeSum += titleStr.charCodeAt(i);
    }

    if (informe.veredicto_recomendacion === 'SÍ') {
      setTextoVeredicto(FRASES_SI[charCodeSum % FRASES_SI.length]);
    } else {
      setTextoVeredicto(FRASES_NO[charCodeSum % FRASES_NO.length]);
    }
  }, [informe])

  const cvp        = informe.critica_vs_publico || {}
  const bs         = informe.banda_sonora || {}
  const snack      = informe.snack || {}
  const plataformas  = informe.streaming_espana || []
  const alternativas = informe.alternativas || []
  const giros      = girosANumero(informe.indice_giros)
  const bsVideoId      = videoId
  const trailerVideoId = bs.url_youtube ? extraerVideoId(bs.url_youtube) : null

  if (esSuerte) {
    return (
      <div style={{ padding: '40px 40px 80px', fontFamily: 'var(--font-body)', color: TEXT, maxWidth: 1000, margin: '0 auto' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 32,
          alignItems: 'start'
        }}>
          {/* Módulo 1: Póster de la película */}
          <Reveal className="report-card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{
              aspectRatio: '2/3', background: 'rgba(0,0,0,0.5)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 40, color: 'rgba(255,255,255,0.08)',
            }}>
              {posterUrl
                ? <img src={posterUrl} alt={informe.titulo_anio}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                    onError={e => { e.target.style.display = 'none' }} />
                : '🎬'}
            </div>
            <div style={{ padding: '20px 24px' }}>
              <p style={{ fontFamily: 'var(--font-title)', fontSize: 24, color: TEXT, letterSpacing: 2, lineHeight: 1.3, marginBottom: 8 }}>
                {informe.titulo_anio}
              </p>
              {informe.veredicto_recomendacion && (
                <div>
                  <span className={informe.veredicto_recomendacion === 'SÍ' ? 'badge-si' : 'badge-no'} style={{ fontSize: 18, padding: '4px 16px' }}>
                    {textoVeredicto}
                  </span>
                </div>
              )}
            </div>
          </Reveal>

          {/* Columna Derecha: Sinopsis y Banda Sonora */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
            {/* Módulo 2: Sinopsis */}
            <Reveal className="report-card" style={{ minHeight: 200 }}>
              <Label>De qué va</Label>
              <p style={{ fontSize: 18, color: TEXT, lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                {informe.de_que_va || "No hay sinopsis disponible para esta película."}
              </p>
            </Reveal>

            {/* Módulo 3: Banda Sonora */}
            {(bs.compositor || bs.album || bsVideoId) && (
              <Reveal className="report-card">
                <Label>{esLofi ? '🎵 Lofi — sin banda sonora' : 'Banda Sonora'}</Label>
                {!esLofi && (bs.compositor || bs.album) && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
                    <span style={{ fontSize: 32 }}>🎵</span>
                    <div>
                      <p style={{ fontFamily: 'var(--font-ui)', fontWeight: 700, fontSize: 16, color: TEXT, letterSpacing: 0.5 }}>
                        {bs.compositor || 'Compositor desconocido'}
                      </p>
                      {bs.album && <p style={{ fontSize: 13, color: TEXT2, marginTop: 4 }}>{bs.album}</p>}
                    </div>
                  </div>
                )}
                {bsVideoId && (
                  <iframe width="100%" height="160"
                    src={`https://www.youtube.com/embed/${bsVideoId}?autoplay=1&controls=1`}
                    allow="autoplay; encrypted-media" allowFullScreen
                    style={{ display: 'block', border: 'none', borderRadius: 12, boxShadow: '0 4px 20px rgba(0,0,0,0.4)' }} title="Banda sonora" />
                )}
              </Reveal>
            )}
          </div>
        </div>

        {/* Acciones */}
        <div style={{
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          paddingTop: 40, marginTop: 40, borderTop: `1px solid ${BORDER}`,
        }}>
          <button onClick={onVolver} className="btn-main" style={{
            padding: '12px 28px', fontSize: 16, borderRadius: 12, textShadow: 'none'
          }}>
            ← Otra recomendación
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: '32px 40px 80px', fontFamily: 'var(--font-body)', color: TEXT }}>

      <div className="informe-grid">

        {/* ════ COL IZQUIERDA: póster + banda sonora ════ */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          <Reveal className="report-card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{
              aspectRatio: '2/3', background: 'rgba(0,0,0,0.5)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 40, color: 'rgba(255,255,255,0.08)',
            }}>
              {posterUrl
                ? <img src={posterUrl} alt={informe.titulo_anio}
                    style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                    onError={e => { e.target.style.display = 'none' }} />
                : '🎬'}
            </div>
            <div style={{ padding: '12px 16px' }}>
              <p style={{ fontFamily: 'var(--font-title)', fontSize: 14, color: TEXT, letterSpacing: 1.5, lineHeight: 1.3 }}>
                {informe.titulo_anio}
              </p>
            </div>
          </Reveal>


          {(bs.compositor || bs.album || bsVideoId) && (
            <Reveal className="report-card">
              <Label>{esLofi ? '🎵 Lofi — sin banda sonora' : 'Banda Sonora'}</Label>
              {!esLofi && (bs.compositor || bs.album) && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <span style={{ fontSize: 20 }}>🎵</span>
                  <div>
                    <p style={{ fontFamily: 'var(--font-ui)', fontWeight: 700, fontSize: 13, color: TEXT }}>
                      {bs.compositor || 'Compositor desconocido'}
                    </p>
                    {bs.album && <p style={{ fontSize: 12, color: TEXT2, marginTop: 2 }}>{bs.album}</p>}
                  </div>
                </div>
              )}
              {bsVideoId && (
                <iframe width="100%" height="80"
                  src={`https://www.youtube.com/embed/${bsVideoId}?autoplay=1&controls=1`}
                  allow="autoplay; encrypted-media" allowFullScreen
                  style={{ display: 'block', border: 'none', borderRadius: 6 }} title="Banda sonora" />
              )}
            </Reveal>
          )}

        </div>

        {/* ════ COL CENTRAL: veredicto + snack + dónde verla + alerta + alternativas ════ */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          <Reveal className="report-card">
            <Label>Veredicto de Indy</Label>
            {informe.veredicto_recomendacion && (
              <div style={{ marginBottom: 18 }}>
                <span className={informe.veredicto_recomendacion === 'SÍ' ? 'badge-si' : 'badge-no'}>
                  {textoVeredicto}
                </span>
              </div>
            )}
            <p style={{ fontSize: 16, color: TEXT, fontWeight: 'bold', marginBottom: 14, lineHeight: 1.5 }}>
              {informe.veredicto_razon}
            </p>
            {informe.veredicto && informe.veredicto !== informe.veredicto_razon && (
              <p style={{ fontSize: 14, color: TEXT2, lineHeight: 1.8, borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 14, fontStyle: 'italic' }}>
                {informe.veredicto}
              </p>
            )}
          </Reveal>

          {(snack.snack || snack.comida) && (
            <Reveal className="report-card">
              <Label>Snack de Indy</Label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 8, rowGap: 8 }}>
                  {snack.comida ? (
                    <>
                      {snack.bebida && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 24 }}>🥤</span>
                          <span style={{ fontFamily: 'var(--font-ui)', fontWeight: 700, fontSize: 15, color: TEXT }}>
                            {snack.bebida}
                          </span>
                        </div>
                      )}
                      {snack.bebida && snack.comida && (
                        <span style={{ color: 'var(--gold)', fontWeight: 'bold', fontSize: 18, margin: '0 4px' }}>+</span>
                      )}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 24 }}>🍿</span>
                        <span style={{ fontFamily: 'var(--font-ui)', fontWeight: 700, fontSize: 15, color: TEXT }}>
                          {snack.comida}
                        </span>
                      </div>
                    </>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 24 }}>🍿</span>
                      <span style={{ fontFamily: 'var(--font-ui)', fontWeight: 700, fontSize: 15, color: TEXT }}>
                        {snack.snack}
                      </span>
                    </div>
                  )}
                </div>
                {snack.justificacion && (
                  <p style={{ fontSize: 13, color: TEXT2, fontStyle: 'italic', lineHeight: 1.6, borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 10 }}>
                    {snack.justificacion}
                  </p>
                )}
              </div>
            </Reveal>
          )}

          <Reveal className="report-card">
            <Label>Dónde verla</Label>
            {plataformas.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                {plataformas.map((p, i) => {
                  const nombre = typeof p === 'object' ? p.nombre : p;
                  const url = getPlatformUrl(p);
                  return (
                    <a key={i} href={url} target="_blank" rel="noopener noreferrer" style={{
                      textDecoration: 'none',
                      display: 'inline-block',
                      padding: '6px 16px', borderRadius: 20,
                      fontFamily: 'var(--font-ui)', fontSize: 12, fontWeight: 600, letterSpacing: 1,
                      background: i === 0 ? 'rgba(240, 192, 64, 0.25)' : 'rgba(255, 255, 255, 0.05)',
                      color: i === 0 ? 'var(--gold)' : TEXT2,
                      border: `1.5px solid ${i === 0 ? 'rgba(240, 192, 64, 0.4)' : BORDER}`,
                      transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = i === 0 ? 'rgba(240, 192, 64, 0.35)' : 'rgba(255, 255, 255, 0.1)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.borderColor = i === 0 ? 'rgba(240, 192, 64, 0.6)' : 'rgba(255, 255, 255, 0.15)';
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = i === 0 ? 'rgba(240, 192, 64, 0.25)' : 'rgba(255, 255, 255, 0.05)';
                      e.currentTarget.style.transform = 'none';
                      e.currentTarget.style.borderColor = i === 0 ? 'rgba(240, 192, 64, 0.4)' : BORDER;
                    }}
                    >
                      {i === 0 && '✓ '}{nombre} ↗
                    </a>
                  );
                })}
              </div>
            ) : (
              <p style={{ fontSize: 14, color: TEXT2, fontStyle: 'italic' }}>No disponible en streaming.</p>
            )}
          </Reveal>

          {informe.alerta_indy && (
            <Reveal className="report-card indy-alert-banner">
              <Label>🐾 Alerta Indy</Label>
              <p style={{ fontSize: 14, color: TEXT2, lineHeight: 1.8 }}>{informe.alerta_indy}</p>
            </Reveal>
          )}

          {alternativas.length > 0 && (
            <Reveal className="report-card">
              <Label>Si no te convence, prueba esto</Label>
              {alternativas.map((peli, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'baseline', gap: 16,
                  padding: '11px 0',
                  borderBottom: i < alternativas.length - 1 ? `1px solid ${BORDER}` : 'none',
                }}>
                  <span style={{ fontFamily: 'var(--font-title)', fontSize: 13, color: GOLD, letterSpacing: 2, flexShrink: 0 }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span style={{ fontSize: 15, color: TEXT }}>{peli}</span>
                </div>
              ))}
            </Reveal>
          )}
        </div>

        {/* ════ COL DERECHA: datos + tráiler + banda sonora ════ */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          <Reveal className="report-card">
            <Label>Puntuaciones</Label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 8, marginBottom: 14 }}>
              <Punt fuente="Crítica"
                valor={cvp.puntuacion_critica != null ? `${cvp.puntuacion_critica}` : '—'}
                sufijo={cvp.puntuacion_critica != null ? '/10' : ''} sub="crítica" />
              <Punt fuente="Público"
                valor={cvp.puntuacion_publico != null ? `${cvp.puntuacion_publico}` : '—'}
                sufijo={cvp.puntuacion_publico != null ? '/10' : ''} sub="audiencia" />
              <Punt fuente="Gana"
                valor={cvp.quien_gana === 'publico' ? 'Público' : cvp.quien_gana === 'critica' ? 'Crítica' : 'Empate'}
                sufijo="" sub="¿quién?" />
            </div>
            <button onClick={() => setMasAbierto(v => !v)} style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontFamily: 'var(--font-ui)', fontSize: 11, color: GOLD,
              letterSpacing: 1, padding: 0, display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <span style={{ fontSize: 9 }}>{masAbierto ? '▲' : '▼'}</span>
              {masAbierto ? 'Menos datos' : 'Más datos'}
            </button>
            {masAbierto && cvp.comentario && (
              <p style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${BORDER}`, fontSize: 13, color: TEXT2, fontStyle: 'italic', lineHeight: 1.7 }}>
                {cvp.comentario}
              </p>
            )}
          </Reveal>

          <Reveal className="report-card">
            <Label>Datos curiosos</Label>
            <Dato label="Giros de guión" value={<GirosDots n={giros} />} />
            <Dato label="Postcréditos"
              value={informe.post_creditos === 'sí' ? 'Quédate' : informe.post_creditos === 'no' ? 'No' : '—'} />
            {informe.indice_giros && <Dato label="Nivel drama" value={nivelDrama(informe.indice_giros, cvp)} />}
            {informe.alerta_indy && <Dato label="El perro" value="Aparece 🐾" valueStyle={{ color: GOLD }} />}
          </Reveal>

          <Reveal className="report-card">
            <Label>Tráiler</Label>
            {trailerVideoId ? (
              <div style={{ borderRadius: 8, overflow: 'hidden', aspectRatio: '16/9' }}>
                <iframe width="100%" height="100%"
                  src={`https://www.youtube.com/embed/${trailerVideoId}`}
                  allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen style={{ display: 'block', border: 'none' }} title="Tráiler" />
              </div>
            ) : (
              <div style={{
                aspectRatio: '16/9', background: 'rgba(255,255,255,0.04)', borderRadius: 8,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: TEXT2, fontFamily: 'var(--font-ui)', fontSize: 11, letterSpacing: 2,
              }}>NO DISPONIBLE</div>
            )}
          </Reveal>

        </div>
      </div>

      {/* ── Acciones ── */}
      <div style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center',
        paddingTop: 32, marginTop: 32, borderTop: `1px solid ${BORDER}`,
      }}>
        <button onClick={onVolver} style={{
          background: 'transparent', border: `1.5px solid ${BORDER}`, color: TEXT2,
          fontFamily: 'var(--font-ui)', fontSize: 11, fontWeight: 600,
          letterSpacing: 2, textTransform: 'uppercase', padding: '10px 20px', cursor: 'pointer', borderRadius: 6,
        }}>← Nueva búsqueda</button>
      </div>

    </div>
  )
}

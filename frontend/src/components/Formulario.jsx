import { useState, useRef, useEffect } from 'react'

const PERFILES = [
  { key: 'palomitero',    label: 'El Palomitero',    img: '/palomitero.png' },
  { key: 'independiente', label: 'El Independiente',  img: '/independiente.png' },
  { key: 'fantastico',    label: 'El Fantástico',     img: '/fantastico.png' },
  { key: 'dramatico',     label: 'El Dramático',      img: '/dramatico.png' },
  { key: 'curioso',       label: 'El Curioso',        img: '/curioso.png' },
]

export default function Formulario({ onBuscar, onVolver, onComprobarTitulo, startAtStep2, tituloInicial, anioInicial }) {
  const [step, setStep]     = useState(startAtStep2 ? 2 : 1)
  const [titulo, setTitulo] = useState(tituloInicial || '')
  const [anio, setAnio]     = useState(anioInicial ? String(anioInicial) : '')
  const [perfil, setPerfil] = useState(null)
  const [comprobandoCache, setComprobandoCache] = useState(false)
  const inputRef = useRef(null)

  useEffect(() => { setTimeout(() => inputRef.current?.focus(), 100) }, [step])

  const submit = (perfilKey) => {
    if (!titulo.trim() || !perfilKey) return
    onBuscar({
      titulo: titulo.trim(),
      perfil_usuario: perfilKey,
      anio: anio ? parseInt(anio) : null,
      nombre_usuario: null,
    })
  }

  // antes de pasar al paso del perfil compruebo si la película ya tiene caché
  const irAlPaso2 = async () => {
    if (!titulo.trim() || comprobandoCache) return
    setComprobandoCache(true)
    const tieneCache = await onComprobarTitulo(titulo.trim(), anio ? parseInt(anio) : null)
    setComprobandoCache(false)
    if (!tieneCache) setStep(2)
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', padding: '40px 24px',
      backgroundImage: 'linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)), url(/fondo.jpg)',
      backgroundSize: 'cover', backgroundPosition: 'center',
      backgroundAttachment: 'fixed',
    }}>
      {/* Progreso */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 48 }}>
        {[1, 2].map(n => (
          <div key={n} style={{
            width: n <= step ? 40 : 10, height: 8,
            background: n <= step ? 'var(--gold)' : 'rgba(255,255,255,0.15)',
            transition: 'all 0.3s ease',
          }} />
        ))}
      </div>

      <div className="up glass-panel" key={step} style={{
        width: '100%',
        maxWidth: step === 2 ? 1200 : 520,
        padding: step === 2 ? '40px 48px' : '40px 36px',
        transition: 'max-width 0.4s cubic-bezier(0.4, 0, 0.2, 1), padding 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
      }}>

        {/* ── PASO 1: Película ── */}
        {step === 1 && (
          <div style={{ textAlign: 'center' }}>
            <p className="label" style={{ marginBottom: 12 }}>Paso 1 de 2</p>
            <h2 style={{
              fontFamily: 'var(--font-ui)', fontWeight: 800, fontSize: 'clamp(28px,4.5vw,42px)',
              color: 'var(--text)', letterSpacing: 0.5, marginBottom: 36, lineHeight: 1.15,
            }}>
              ¿Qué peli quieres que analice?
            </h2>

            <input ref={inputRef} className="inp" value={titulo}
              onChange={e => setTitulo(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && irAlPaso2()}
              placeholder="El Padrino, Dune, Barbie…"
              style={{ marginBottom: 12, borderRadius: 12 }}
            />
            <input className="inp no-spinner" type="number" value={anio}
              onChange={e => setAnio(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && irAlPaso2()}
              placeholder="Año (opcional)"
              min="1900" max="2030"
              style={{ marginBottom: 36, fontSize: 16, padding: '10px 18px', borderRadius: 12 }}
            />

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, width: '100%' }}>
              <button className="btn-secondary" onClick={onVolver}
                style={{ width: 160, padding: '16px 0', fontSize: 14, fontFamily: 'var(--font-ui)', fontWeight: 700, textAlign: 'center' }}>
                ← Atrás
              </button>
              <button className="btn-secondary"
                disabled={!titulo.trim() || comprobandoCache}
                onClick={irAlPaso2}
                style={{
                  width: 160, padding: '16px 0', fontSize: 14, fontFamily: 'var(--font-ui)', fontWeight: 700,
                  textAlign: 'center', opacity: titulo.trim() && !comprobandoCache ? 1 : 0.4,
                  cursor: titulo.trim() && !comprobandoCache ? 'pointer' : 'not-allowed',
                }}>
                {comprobandoCache ? 'Comprobando…' : 'Siguiente →'}
              </button>
            </div>
          </div>
        )}

        {/* ── PASO 2: Perfil ── */}
        {step === 2 && (
          <div>
            <p className="label" style={{ marginBottom: 12 }}>Paso 2 de 2</p>
            <h2 style={{
              fontFamily: 'var(--font-title)', fontSize: 'clamp(36px,6vw,48px)',
              color: 'var(--text)', letterSpacing: 4, marginBottom: 36,
              textAlign: 'center'
            }}>
              ¿Qué tipo de espectador eres?
            </h2>

            <div className="no-scrollbar" style={{ display: 'flex', flexDirection: 'row', flexWrap: 'nowrap', gap: 12, justifyContent: 'center', marginBottom: 36, width: '100%', overflowX: 'auto' }}>
              {PERFILES.map(p => (
                <button key={p.key} type="button"
                  onClick={() => { setPerfil(p.key); setTimeout(() => submit(p.key), 220) }}
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    cursor: 'pointer',
                    outline: 'none',
                    transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                    flex: '1 1 200px',
                    maxWidth: 230,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    transform: perfil === p.key ? 'scale(1.06)' : 'scale(1)',
                  }}
                >
                  <img 
                    src={p.img} 
                    alt={p.label}
                    style={{
                      width: '100%',
                      height: 'auto',
                      objectFit: 'contain',
                      transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                      filter: perfil === p.key 
                        ? 'drop-shadow(0 0 15px rgba(240, 192, 64, 0.8))' 
                        : 'drop-shadow(0 6px 12px rgba(0, 0, 0, 0.5))',
                    }}
                    onMouseEnter={e => {
                      if (perfil !== p.key) {
                        e.currentTarget.style.filter = 'drop-shadow(0 0 12px rgba(240, 192, 64, 0.45)) drop-shadow(0 8px 16px rgba(0,0,0,0.6))';
                        e.currentTarget.parentElement.style.transform = 'scale(1.04)';
                      }
                    }}
                    onMouseLeave={e => {
                      if (perfil !== p.key) {
                        e.currentTarget.style.filter = 'drop-shadow(0 6px 12px rgba(0, 0, 0, 0.5))';
                        e.currentTarget.parentElement.style.transform = 'scale(1)';
                      }
                    }}
                  />
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <button className="btn-secondary" onClick={() => setStep(1)} style={{ width: '100%', maxWidth: 200 }}>
                ← Atrás
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  )
}

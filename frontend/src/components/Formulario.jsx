import { useState, useRef, useEffect } from 'react'

const PERFILES = [
  { key: 'palomitero',    label: 'El Palomitero',    emoji: '🍿' },
  { key: 'independiente', label: 'El Independiente',  emoji: '🎬' },
  { key: 'fantastico',    label: 'El Fantástico',     emoji: '🚀' },
  { key: 'dramatico',     label: 'El Dramático',      emoji: '🎭' },
  { key: 'curioso',       label: 'El Curioso',        emoji: '🎲' },
]

export default function Formulario({ onBuscar, onVolver }) {
  const [step, setStep]     = useState(1)
  const [titulo, setTitulo] = useState('')
  const [anio, setAnio]     = useState('')
  const [perfil, setPerfil] = useState(null)
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

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', padding: '40px 24px',
      background: 'rgba(0,0,0,0.78)',
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

      <div className="up" key={step} style={{ width: '100%', maxWidth: 520 }}>

        {/* ── PASO 1: Película ── */}
        {step === 1 && (
          <div>
            <p className="label" style={{ marginBottom: 12 }}>Paso 1 de 2</p>
            <h2 style={{
              fontFamily: 'var(--font-title)', fontSize: 'clamp(36px,6vw,56px)',
              color: 'var(--text)', letterSpacing: 4, marginBottom: 36,
            }}>
              ¿Qué película?
            </h2>

            <input ref={inputRef} className="inp" value={titulo}
              onChange={e => setTitulo(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && titulo.trim() && setStep(2)}
              placeholder="El Padrino, Dune, Barbie…"
              style={{ marginBottom: 12 }}
            />
            <input className="inp" type="number" value={anio}
              onChange={e => setAnio(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && titulo.trim() && setStep(2)}
              placeholder="Año (opcional)"
              min="1900" max="2030"
              style={{ marginBottom: 36, fontSize: 16, padding: '10px 18px' }}
            />

            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <button className="btn-main"
                disabled={!titulo.trim()}
                onClick={() => setStep(2)}
                style={{ opacity: titulo.trim() ? 1 : 0.4 }}>
                Siguiente →
              </button>
              <button className="btn-secondary" onClick={onVolver}>← Atrás</button>
            </div>
          </div>
        )}

        {/* ── PASO 2: Perfil ── */}
        {step === 2 && (
          <div>
            <p className="label" style={{ marginBottom: 12 }}>Paso 2 de 2</p>
            <h2 style={{
              fontFamily: 'var(--font-title)', fontSize: 'clamp(36px,6vw,56px)',
              color: 'var(--text)', letterSpacing: 4, marginBottom: 36,
            }}>
              ¿Cómo ves las pelis?
            </h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 36 }}>
              {PERFILES.map(p => (
                <button key={p.key} type="button"
                  onClick={() => { setPerfil(p.key); setTimeout(() => submit(p.key), 180) }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 16,
                    padding: '16px 20px',
                    background: perfil === p.key ? 'rgba(240,192,64,0.15)' : 'rgba(0,0,0,0.5)',
                    border: `2px solid ${perfil === p.key ? 'var(--gold)' : 'rgba(255,255,255,0.1)'}`,
                    color: 'var(--text)', cursor: 'pointer', textAlign: 'left',
                    transition: 'all 0.12s',
                  }}
                  onMouseEnter={e => { if (perfil !== p.key) e.currentTarget.style.borderColor = 'rgba(255,255,255,0.3)' }}
                  onMouseLeave={e => { if (perfil !== p.key) e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)' }}
                >
                  <span style={{ fontSize: 24 }}>{p.emoji}</span>
                  <span style={{ fontFamily: 'var(--font-title)', fontSize: 22, letterSpacing: 2 }}>{p.label}</span>
                </button>
              ))}
            </div>

            <button className="btn-secondary" onClick={() => setStep(1)}>← Atrás</button>
          </div>
        )}

      </div>
    </div>
  )
}

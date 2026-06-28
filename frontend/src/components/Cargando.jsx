import { useState, useEffect } from 'react'

const FRASES = [
  'Indy está en misión…',
  'Consultando las fuentes…',
  'Analizando crítica y público…',
  'Rastreando plataformas…',
  'Preparando el veredicto…',
]

export default function Cargando() {
  const [i, setI] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setI(n => (n + 1) % FRASES.length), 2800)
    return () => clearInterval(t)
  }, [])

  return (
    <div style={{
      minHeight: '100vh', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
      background: 'rgba(0,0,0,0.78)',
    }}>
      <p key={i} style={{
        fontFamily: 'var(--font-title)',
        fontSize: 'clamp(24px,4vw,36px)',
        color: 'var(--gold)',
        letterSpacing: 4,
        textTransform: 'uppercase',
        textAlign: 'center',
        animation: 'fade-phrase 0.4s ease',
      }}>
        {FRASES[i]}
      </p>
      <style>{`
        @keyframes fade-phrase {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}

import { useState } from 'react'
import Formulario from './components/Formulario'
import Informe from './components/Informe'
import Cargando from './components/Cargando'

const API = 'http://localhost:8000'

export default function App() {
  const [estado, setEstado]       = useState('intro')   // intro | form | cargando | cache | informe
  const [informe, setInforme]     = useState(null)
  const [cacheInfo, setCacheInfo] = useState(null)
  const [formData, setFormData]   = useState(null)
  const [videoId, setVideoId]     = useState(null)

  const handleBuscar = async (datos) => {
    setFormData(datos)
    setEstado('cargando')
    try {
      const res   = await fetch(`${API}/cache`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ titulo: datos.titulo }) })
      const cache = await res.json()
      if (cache.cache) { setCacheInfo(cache); setEstado('cache'); return }
    } catch (e) { console.error(e) }
    await ejecutarAgente(datos, false)
  }

  const ejecutarAgente = async (datos, forzar_nuevo) => {
    setEstado('cargando')
    try {
      const res = await fetch(`${API}/analizar`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...datos, forzar_nuevo }) })
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail) }
      const r = await res.json()
      setInforme(r.informe); setVideoId(r.youtube_video_id || null); setEstado('informe')
    } catch (e) { setEstado('form'); alert('Error: ' + e.message) }
  }

  const handleVolver = () => { setEstado('intro'); setInforme(null); setVideoId(null) }

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg)',
      backgroundImage: 'url(/fondo.jpg)',
      backgroundSize: 'cover', backgroundPosition: 'center',
      backgroundAttachment: 'fixed',
    }}>

      {/* ── INTRO ── */}
      {estado === 'intro' && (
        <div style={{
          minHeight: '100vh',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          padding: 32,
          backgroundImage: 'url(/fondo.jpg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
        }}>
          {/*
            El usuario se encarga del logo/título (coloca /indy-titulo.png en /public)
            o edita directamente este bloque.
          */}
          <img src="/indy-titulo.png" alt="INDY"
            style={{ maxWidth: 480, width: '90%', marginBottom: 40 }}
            onError={e => { e.target.style.display = 'none' }}
          />

          <button onClick={() => setEstado('form')} className="btn-main">
            ANALIZAR UNA PELÍCULA
          </button>

          <p style={{
            marginTop: 20, fontSize: 14, color: 'rgba(255,255,255,0.85)',
            fontFamily: 'var(--font-body)', letterSpacing: 1,
            textShadow: '0 1px 4px rgba(0,0,0,0.9), 0 0 12px rgba(0,0,0,0.8)',
          }}>
            *puede que te arruine la noche. o que te salve el fin de semana.
          </p>
        </div>
      )}

      {/* ── FORMULARIO ── */}
      {estado === 'form' && (
        <Formulario onBuscar={handleBuscar} onVolver={() => setEstado('intro')} />
      )}

      {/* ── CARGANDO ── */}
      {estado === 'cargando' && <Cargando />}

      {/* ── CACHÉ ── */}
      {estado === 'cache' && cacheInfo && (
        <div style={{
          minHeight: '100vh', background: 'var(--bg)',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', padding: 40,
        }}>
          <div style={{ maxWidth: 520, width: '100%', textAlign: 'center' }}>
            <p style={{
              fontFamily: 'monospace', fontSize: 13, color: 'var(--text-2)',
              marginBottom: 12, letterSpacing: 1,
            }}>
              Indy ya analizó esta película el <strong style={{ color: 'var(--gold)' }}>{cacheInfo.fecha_consulta}</strong>
            </p>
            <p style={{ fontFamily: 'monospace', fontSize: 11, color: 'var(--text-3)', marginBottom: 36 }}>
              ¿Usamos el análisis guardado o repetimos la misión?
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              <button className="btn-main" style={{ fontSize: 13, padding: '14px 28px' }}
                onClick={() => { setInforme(cacheInfo.informe); setEstado('informe') }}>
                USAR GUARDADO
              </button>
              <button className="btn-secondary"
                onClick={() => ejecutarAgente(formData, true)}>
                ANALIZAR DE NUEVO
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── INFORME ── */}
      {estado === 'informe' && informe && (
        <div style={{
          minHeight: '100vh',
          background: 'rgba(8,7,6,0.84)',
        }}>
          {/* Header sticky */}
          <header style={{
            borderBottom: '1px solid rgba(255,255,255,0.08)',
            padding: '14px 32px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            background: 'rgba(8,7,6,0.95)',
            position: 'sticky', top: 0, zIndex: 100,
          }}>
            <span style={{ fontFamily: 'var(--font-title)', fontSize: 28, color: 'var(--text)', letterSpacing: 6 }}>INDY</span>
            <button className="btn-secondary" onClick={handleVolver}>← volver</button>
          </header>

          {/* Contenido */}
          <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 40px' }}>
            <Informe informe={informe} videoId={videoId} onVolver={handleVolver} />
          </div>

          <footer style={{ borderTop: '1px solid rgba(255,255,255,0.06)', padding: '16px 32px', fontFamily: 'var(--font-ui)', fontSize: 11, color: 'var(--text-3)', letterSpacing: 2, textTransform: 'uppercase' }}>
            Indy · En memoria de un schnauzer con criterio propio
          </footer>
        </div>
      )}

    </div>
  )
}

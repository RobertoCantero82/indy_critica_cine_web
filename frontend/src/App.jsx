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
  const [esLofi, setEsLofi]       = useState(false)
  const [posterUrl, setPosterUrl] = useState(null)
  const [mostrarModal, setMostrarModal] = useState(false)
  const [mostrarSuerteModal, setMostrarSuerteModal] = useState(false)
  const [suerteGenero, setSuerteGenero] = useState('Acción')
  const [suertePlataforma, setSuertePlataforma] = useState('Netflix')
  const [suertePerfil, setSuertePerfil] = useState('palomitero')
  const [suertePrompt, setSuertePrompt] = useState('')
  const [suerteCargando, setSuerteCargando] = useState(false)
  const [esSuerte, setEsSuerte] = useState(false)
  const [suerteResultado, setSuerteResultado] = useState(null)
  const [suerteError, setSuerteError] = useState(null)
 
  const handleSuerteRecomendar = async () => {
    setSuerteCargando(true)
    setSuerteResultado(null)
    setSuerteError(null)
    try {
      const horaActual = new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
      const res = await fetch(`${API}/recomendar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plataforma: suertePlataforma,
          prompt_personalizado: suertePrompt.trim() || undefined,
          hora_actual: horaActual
        })
      })
      if (!res.ok) throw new Error('Error en recomendar')
      const data = await res.json()
      setSuerteResultado(data)
      setSuerteCargando(false)
    } catch (e) {
      console.error(e)
      setSuerteCargando(false)
      setSuerteError("Error al obtener recomendación de Indy. Revisa la conexión con el servidor.")
    }
  }

  const closeSuerteModal = () => {
    setMostrarSuerteModal(false)
    setSuerteResultado(null)
    setSuerteError(null)
    setSuertePrompt('')
    setSuerteCargando(false)
  }

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
      setInforme(r.informe); setVideoId(r.youtube_video_id || null); setEsLofi(r.youtube_es_lofi || false); setPosterUrl(r.informe?.poster_url || null); setEstado('informe')
    } catch (e) { setEstado('form'); alert('Error: ' + e.message) }
  }

  const handleVolver = () => { setEstado('intro'); setInforme(null); setVideoId(null); setEsLofi(false); setPosterUrl(null); setEsSuerte(false) }

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
          padding: 24,
          backgroundImage: 'linear-gradient(rgba(0, 0, 0, 0.72), rgba(0, 0, 0, 0.72)), url(/fondo.jpg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
          overflow: 'hidden',
        }}>
          {/* Logo de título */}
          <img src="/indy-titulo.png" alt="INDY"
            style={{ maxWidth: 440, width: '90%', marginBottom: 12 }}
            onError={e => { e.target.style.display = 'none' }}
          />

          {/* Subtítulo / Descripción arriba */}
          <p style={{
            marginBottom: 32, fontSize: 13, color: 'rgba(255,255,255,0.85)',
            fontFamily: 'var(--font-body)', letterSpacing: 1,
            textShadow: '0 1px 4px rgba(0,0,0,0.9), 0 0 12px rgba(0,0,0,0.8)',
            textAlign: 'center', maxWidth: 380, lineHeight: 1.5
          }}>
            El agente de IA que te ayuda a elegir película antes de que se te enfríen las palomitas buscando.
          </p>

          {/* Pegatina interactiva de Indy para empezar la experiencia (Más grande!) */}
          <button 
            onClick={() => setEstado('form')} 
            style={{ 
              background: 'none', 
              border: 'none', 
              cursor: 'pointer', 
              outline: 'none',
              padding: 0,
              marginBottom: 36,
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              width: '100%',
              display: 'flex',
              justifyContent: 'center'
            }}
            onMouseEnter={e => {
              e.currentTarget.style.transform = 'scale(1.05)';
              const img = e.currentTarget.querySelector('img');
              if (img) {
                img.style.filter = 'grayscale(0%) sepia(0%) drop-shadow(0 0 24px rgba(240, 192, 64, 0.95))';
              }
            }}
            onMouseLeave={e => {
              e.currentTarget.style.transform = 'scale(1)';
              const img = e.currentTarget.querySelector('img');
              if (img) {
                img.style.filter = 'grayscale(25%) sepia(15%) drop-shadow(0 8px 16px rgba(0, 0, 0, 0.6))';
              }
            }}
          >
            <img 
              src="/indy_start.png" 
              alt="Comenzar Misión Indy"
              style={{ 
                maxWidth: 320,
                width: '75%',
                height: 'auto', 
                objectFit: 'contain',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                filter: 'grayscale(25%) sepia(15%) drop-shadow(0 8px 16px rgba(0, 0, 0, 0.6))'
              }}
            />
          </button>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center', width: '90%', maxWidth: 320 }}>
            <button onClick={() => setMostrarSuerteModal(true)} className="btn-main" style={{
              width: '100%',
              padding: '12px 24px',
              fontSize: '18px',
              background: 'linear-gradient(180deg, rgba(74, 222, 128, 0.16) 0%, rgba(74, 222, 128, 0.05) 100%)',
              borderColor: 'rgba(74, 222, 128, 0.4)',
              color: '#4ade80',
              boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.2), 0 4px 16px rgba(74, 222, 128, 0.1)',
              letterSpacing: '2px',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'linear-gradient(180deg, rgba(74, 222, 128, 0.24) 0%, rgba(74, 222, 128, 0.10) 100%)';
              e.currentTarget.style.borderColor = 'rgba(74, 222, 128, 0.65)';
              e.currentTarget.style.boxShadow = 'inset 0 1px 2px rgba(255,255,255,0.35), 0 12px 40px rgba(74, 222, 128, 0.18)';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'linear-gradient(180deg, rgba(74, 222, 128, 0.16) 0%, rgba(74, 222, 128, 0.05) 100%)';
              e.currentTarget.style.borderColor = 'rgba(74, 222, 128, 0.4)';
              e.currentTarget.style.boxShadow = 'inset 0 1px 1px rgba(255,255,255,0.2), 0 4px 16px rgba(74, 222, 128, 0.1)';
              e.currentTarget.style.transform = 'none';
            }}
            >
              CHAT CON INDY 💬
            </button>
            <button onClick={() => setMostrarModal(true)} className="btn-secondary" style={{ width: '100%', padding: '10px 20px', fontSize: 13 }}>
              ¿Por qué me llamo Indy? 🐾
            </button>
          </div>
        </div>
      )}

      {/* ── FORMULARIO ── */}
      {estado === 'form' && (
        <Formulario onBuscar={(datos) => { setEsSuerte(false); handleBuscar(datos) }} onVolver={() => setEstado('intro')} />
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
                onClick={() => { setInforme(cacheInfo.informe); setPosterUrl(cacheInfo.informe?.poster_url || null); setEstado('informe') }}>
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
          background: 'rgba(13,11,10,0.92)',
          backdropFilter: 'blur(8px)',
          WebkitBackdropFilter: 'blur(8px)',
        }}>


          {/* Contenido */}
          <Informe 
            informe={informe} 
            videoId={videoId} 
            esLofi={esLofi} 
            posterUrl={posterUrl} 
            onVolver={handleVolver} 
            esSuerte={esSuerte} 
          />
        </div>
      )}

      {/* ── MODAL HISTORIA DE INDY ── */}
      {mostrarModal && (
        <div className="modal-overlay" onClick={() => setMostrarModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <button onClick={() => setMostrarModal(false)} style={{
              position: 'absolute', top: 20, right: 20,
              background: 'none', border: 'none', color: 'var(--text-2)',
              fontSize: 22, cursor: 'pointer', fontFamily: 'monospace',
              lineHeight: 1
            }}>
              ✕
            </button>
            
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
              <img src="/indy_real.jpg" alt="Indy el Schnauzer Real" style={{
                width: 160, height: 160, borderRadius: '50%',
                objectFit: 'cover', border: '3px solid var(--gold)',
                boxShadow: '0 8px 24px rgba(240, 192, 64, 0.25)',
                marginBottom: 24
              }} />
              
              <h3 style={{
                fontFamily: 'var(--font-title)', fontSize: 30,
                color: 'var(--gold)', letterSpacing: 2, marginBottom: 16
              }}>
                Déjame que te cuente su historia...
              </h3>
              
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 14,
                color: 'var(--text)', lineHeight: 1.7, marginBottom: 20,
                textAlign: 'justify'
              }}>
                Este agente de IA se llama Indy en honor a un entrañable perro de raza <strong>Schnauzer miniatura</strong> que tenía un fuerte carácter y, sin duda, un criterio muy propio. Indy no se conformaba con cualquier cosa: si algo no le gustaba, te lo hacía saber de inmediato.
              </p>
              
              <p style={{
                fontFamily: 'var(--font-body)', fontSize: 14,
                color: 'var(--text-2)', lineHeight: 1.7, marginBottom: 28,
                textAlign: 'justify'
              }}>
                Nuestra IA hereda su exigencia, honestidad brutal y amor por el buen cine (o al menos por lo que a él le convencía) para decirte si una película realmente merece tu tiempo. Su veredicto no se anda con rodeos.
              </p>
              
              <button className="btn-secondary" onClick={() => setMostrarModal(false)} style={{ padding: '10px 24px' }}>
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL VOY A TENER SUERTE ── */}
      {mostrarSuerteModal && (
        <div className="modal-overlay" onClick={() => !suerteCargando && closeSuerteModal()}>
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 550, padding: '36px 32px' }}>
            <button onClick={() => !suerteCargando && closeSuerteModal()} style={{
              position: 'absolute', top: 20, right: 20,
              background: 'none', border: 'none', color: 'var(--text-2)',
              fontSize: 22, cursor: 'pointer', fontFamily: 'monospace',
              lineHeight: 1
            }} disabled={suerteCargando}>
              ✕
            </button>

            {suerteCargando ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', padding: '40px 0' }}>
                <span style={{ fontSize: 48, animation: 'pulse 1.5s infinite' }}>🐾</span>
                <p style={{ fontFamily: 'var(--font-title)', fontSize: 24, color: '#4ade80', marginTop: 16 }}>
                  Indy está escribiendo...
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--text-2)', marginTop: 8, fontStyle: 'italic' }}>
                  Olfateando la cartelera y rascándose la oreja mientras lo piensa...
                </p>
                <style>{`
                  @keyframes pulse {
                    0% { transform: scale(1); opacity: 0.6; }
                    50% { transform: scale(1.15); opacity: 1; }
                    100% { transform: scale(1); opacity: 0.6; }
                  }
                `}</style>
              </div>
            ) : suerteError ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', padding: '20px 0' }}>
                <span style={{ fontSize: 44, marginBottom: 12 }}>⚠️</span>
                <p style={{ fontFamily: 'var(--font-title)', fontSize: 22, color: '#ef5350', marginBottom: 12 }}>
                  Error de conexión
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--text-2)', textAlign: 'center', marginBottom: 24, lineHeight: 1.5 }}>
                  {suerteError}
                </p>
                <div style={{ display: 'flex', gap: 12, width: '100%', justifyContent: 'center' }}>
                  <button className="btn-main" onClick={handleSuerteRecomendar} style={{ width: '55%', padding: '10px 20px', fontSize: 14 }}>
                    Reintentar 🐾
                  </button>
                  <button className="btn-secondary" onClick={() => setSuerteError(null)} style={{ width: '40%', padding: '10px 20px', fontSize: 14 }}>
                    Escribir otro plan
                  </button>
                </div>
              </div>
            ) : suerteResultado ? (
              <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                {/* Cabecera del chat */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: 16, marginBottom: 20 }}>
                  <img src="/indy_real.jpg" alt="Indy" style={{ width: 44, height: 44, borderRadius: '50%', border: '2px solid var(--gold)', objectFit: 'cover' }} onError={e => { e.target.src = "/icono_indy.png" }} />
                  <div style={{ textAlign: 'left' }}>
                    <h4 style={{ fontFamily: 'var(--font-title)', fontSize: 18, color: 'var(--gold)', margin: 0, letterSpacing: 1 }}>Indy el Crítico</h4>
                    <span style={{ fontFamily: 'var(--font-ui)', fontSize: 10, color: '#4ade80', textTransform: 'uppercase', letterSpacing: 1, display: 'block' }}>En Línea 🐾</span>
                  </div>
                </div>

                {/* Burbuja del mensaje del usuario (Derecha) */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
                  <div style={{
                    maxWidth: '85%',
                    background: 'rgba(255, 255, 255, 0.08)',
                    borderRadius: '16px 16px 2px 16px',
                    padding: '12px 16px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                  }}>
                    <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--text)', margin: 0, lineHeight: 1.4, textAlign: 'left' }}>
                      {suertePrompt}
                    </p>
                  </div>
                </div>

                {/* Burbuja del mensaje de Indy (Izquierda) */}
                <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 24 }}>
                  <div style={{
                    maxWidth: '85%',
                    background: 'linear-gradient(135deg, rgba(74, 222, 128, 0.15) 0%, rgba(74, 222, 128, 0.05) 100%)',
                    border: '1px solid rgba(74, 222, 128, 0.35)',
                    borderRadius: '16px 16px 16px 2px',
                    padding: '16px',
                    boxShadow: '0 4px 16px rgba(74, 222, 128, 0.08)',
                    textAlign: 'left'
                  }}>
                    <p style={{ fontFamily: 'var(--font-body)', fontSize: 14, color: 'var(--text)', margin: 0, lineHeight: 1.5 }}>
                      Te recomiendo ver: <strong style={{ color: '#4ade80', fontSize: 16 }}>{suerteResultado.titulo}</strong> {suerteResultado.anio ? `(${suerteResultado.anio})` : ''}
                    </p>
                    <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--text-2)', margin: '12px 0 0 0', lineHeight: 1.5, fontStyle: 'italic', borderTop: '1px solid rgba(74,222,128,0.2)', paddingTop: 10 }}>
                      🐾 "{suerteResultado.justificacion_eleccion}"
                    </p>
                  </div>
                </div>

                {/* Botones de acción */}
                <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                  <button 
                    className="btn-main" 
                    onClick={() => { setSuerteResultado(null); setSuertePrompt('') }}
                    style={{
                      width: '60%', padding: '10px 20px', fontSize: 14,
                      background: 'linear-gradient(180deg, rgba(240, 192, 64, 0.16) 0%, rgba(240, 192, 64, 0.05) 100%)',
                      borderColor: 'rgba(240, 192, 64, 0.45)',
                      color: 'var(--gold)',
                      boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.2), 0 4px 16px rgba(0,0,0,0.3)',
                      textShadow: 'none'
                    }}
                  >
                    Preguntar otra cosa 🐾
                  </button>
                  <button className="btn-secondary" onClick={closeSuerteModal} style={{ width: '35%', padding: '10px 16px', fontSize: 14 }}>
                    Cerrar chat
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
                <span style={{ fontSize: 44, marginBottom: 12 }}>💬</span>
                <h3 style={{
                  fontFamily: 'var(--font-title)', fontSize: 28,
                  color: '#4ade80', letterSpacing: 2, marginBottom: 8
                }}>
                  Habla con Indy
                </h3>
                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 13,
                  color: 'var(--text-2)', lineHeight: 1.5, marginBottom: 24, textAlign: 'center'
                }}>
                  Cuéntale tu situación, estado de ánimo o el plan que tienes, e Indy elegirá la película ideal para ti.
                </p>

                {/* Selector de Plataforma (Compacto) */}
                <div style={{ width: '100%', textAlign: 'left', marginBottom: 18 }}>
                  <label style={{ fontFamily: 'var(--font-ui)', fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 6 }}>
                    Plataforma de streaming:
                  </label>
                  <select value={suertePlataforma} onChange={e => setSuertePlataforma(e.target.value)} disabled={suerteCargando} style={{
                    width: '100%', background: 'rgba(0,0,0,0.5)', border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 12, padding: '10px 14px', color: 'var(--text)', fontFamily: 'var(--font-body)', fontSize: 13, outline: 'none'
                  }}>
                    <option value="Netflix" style={{ background: '#111' }}>Netflix</option>
                    <option value="Prime Video" style={{ background: '#111' }}>Prime Video</option>
                    <option value="Disney+" style={{ background: '#111' }}>Disney+</option>
                    <option value="Max" style={{ background: '#111' }}>Max</option>
                    <option value="Movistar+" style={{ background: '#111' }}>Movistar+</option>
                    <option value="Apple TV+" style={{ background: '#111' }}>Apple TV+</option>
                    <option value="Filmin" style={{ background: '#111' }}>Filmin</option>
                  </select>
                </div>

                {/* Caja de chat (Textarea) */}
                <div style={{ width: '100%', textAlign: 'left', marginBottom: 24 }}>
                  <label style={{ fontFamily: 'var(--font-ui)', fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 6 }}>
                    Tu mensaje para Indy:
                  </label>
                  <textarea
                    value={suertePrompt}
                    onChange={e => setSuertePrompt(e.target.value)}
                    onKeyDown={e => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if (suertePrompt.trim() && !suerteCargando) {
                          handleSuerteRecomendar();
                        }
                      }
                    }}
                    placeholder="Ej: Recomiéndame una peli para ver un domingo a la tarde de lluvia con la familia si hay 40º en la calle..."
                    disabled={suerteCargando}
                    style={{
                      width: '100%', height: 110, background: 'rgba(0,0,0,0.4)', border: '2px solid rgba(255,255,255,0.12)',
                      borderRadius: 12, padding: '12px 16px', color: 'var(--text)', fontFamily: 'var(--font-body)', fontSize: 14,
                      outline: 'none', resize: 'none', transition: 'all 0.2s', lineHeight: 1.5
                    }}
                    onFocus={e => e.currentTarget.style.borderColor = '#4ade80'}
                    onBlur={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)'}
                    autoFocus
                  />
                </div>

                <div style={{ display: 'flex', gap: 12, width: '100%', justifyContent: 'center' }}>
                  <button 
                    className="btn-main" 
                    onClick={handleSuerteRecomendar} 
                    disabled={suerteCargando || !suertePrompt.trim()} 
                    style={{
                      width: '65%', padding: '12px 24px', fontSize: 15,
                      background: 'linear-gradient(180deg, rgba(74, 222, 128, 0.16) 0%, rgba(74, 222, 128, 0.05) 100%)',
                      borderColor: suertePrompt.trim() ? 'rgba(74, 222, 128, 0.4)' : 'rgba(255,255,255,0.08)',
                      color: suertePrompt.trim() ? '#4ade80' : 'var(--text-3)',
                      boxShadow: suertePrompt.trim() ? 'inset 0 1px 1px rgba(255,255,255,0.2), 0 4px 16px rgba(74, 222, 128, 0.1)' : 'none',
                      opacity: suertePrompt.trim() ? 1 : 0.5,
                      cursor: suertePrompt.trim() ? 'pointer' : 'not-allowed'
                    }}
                  >
                    {suerteCargando ? 'Indy pensando...' : 'Enviar a Indy 🐾'}
                  </button>
                  <button className="btn-secondary" onClick={closeSuerteModal} disabled={suerteCargando} style={{ width: '30%', padding: '12px 16px', fontSize: 15 }}>
                    Cerrar
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  )
}

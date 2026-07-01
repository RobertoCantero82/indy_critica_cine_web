import { useState } from 'react'
import Formulario from './components/Formulario'
import Informe from './components/Informe'
import Cargando from './components/Cargando'

const API = 'http://localhost:8000'

const URLS_PLATAFORMA = {
  'Netflix':     titulo => `https://www.netflix.com/search?q=${encodeURIComponent(titulo)}`,
  'Prime Video': titulo => `https://www.amazon.com/s?k=${encodeURIComponent(titulo)}&i=instant-video`,
  'Disney+':     titulo => `https://www.google.com/search?q=${encodeURIComponent(`${titulo} site:disneyplus.com`)}`,
  'Max':         titulo => `https://play.max.com/search?q=${encodeURIComponent(titulo)}`,
  'Movistar+':   titulo => `https://ver.movistarplus.es/buscador/${encodeURIComponent(titulo)}`,
  'Apple TV+':   titulo => `https://tv.apple.com/search?term=${encodeURIComponent(titulo)}`,
  'Filmin':      titulo => `https://www.filmin.es/buscar?q=${encodeURIComponent(titulo)}`,
}

const urlPlataforma = (plataforma, titulo) =>
  (URLS_PLATAFORMA[plataforma] || (t => `https://www.google.com/search?q=${encodeURIComponent(`${t} ${plataforma}`)}`))(titulo)

const urlImdb         = titulo => `https://www.imdb.com/find?q=${encodeURIComponent(titulo)}`
const urlFilmaffinity = titulo => `https://www.filmaffinity.com/es/search.php?stext=${encodeURIComponent(titulo)}`
const urlLetterboxd   = titulo => `https://letterboxd.com/search/${encodeURIComponent(titulo)}/`

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
  const [suertePlataforma, setSuertePlataforma] = useState('Netflix')
  const [suertePrompt, setSuertePrompt] = useState('')
  const [suerteCargando, setSuerteCargando] = useState(false)
  const [esSuerte, setEsSuerte] = useState(false)
  const [suerteResultado, setSuerteResultado] = useState(null)
  const [suerteError, setSuerteError] = useState(null)
  const [forzarNuevo, setForzarNuevo] = useState(false)
  const [tituloAnioPendiente, setTituloAnioPendiente] = useState({ titulo: '', anio: null, tmdb_id: null })
  const [easterEggActivo, setEasterEggActivo] = useState(false)

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
    // si venimos de "analizar de nuevo" en la pantalla de caché, ya sabemos que hay que forzar
    if (forzarNuevo) {
      setForzarNuevo(false)
      await ejecutarAgente(datos, true)
      return
    }
    setEstado('cargando')
    try {
      const res   = await fetch(`${API}/cache`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ titulo: datos.titulo }) })
      const cache = await res.json()
      if (cache.cache) { setCacheInfo(cache); setEstado('cache'); return }
    } catch (e) { console.error(e) }
    await ejecutarAgente(datos, false)
  }

  // compruebo si ya existe caché justo al confirmar el título, antes de preguntar el perfil
  const comprobarTitulo = async (titulo, anio, tmdb_id) => {
    try {
      const res   = await fetch(`${API}/cache`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ titulo }) })
      const cache = await res.json()
      if (cache.cache) {
        setCacheInfo(cache)
        setTituloAnioPendiente({ titulo, anio, tmdb_id: tmdb_id || null })
        setEstado('cache')
        return true
      }
    } catch (e) { console.error(e) }
    return false
  }

  // autocompleta coincidencias con póster mientras el usuario escribe el título — con debounce en el propio formulario
  const buscarCandidatos = async (titulo, signal) => {
    const res = await fetch(`${API}/buscar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ titulo }),
      signal,
    })
    if (!res.ok) throw new Error('error buscando coincidencias')
    const data = await res.json()
    return data.candidatos || []
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

  const handleVolver = () => { setEstado('intro'); setInforme(null); setVideoId(null); setEsLofi(false); setPosterUrl(null); setEsSuerte(false); setTituloAnioPendiente({ titulo: '', anio: null, tmdb_id: null }); setForzarNuevo(false) }

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
          {/* Logo de título — easter egg: un clic activa la música oculta */}
          <img src="/indy-titulo.png" alt="INDY"
            style={{ maxWidth: 220, width: '55%', marginBottom: 12, cursor: 'pointer' }}
            onError={e => { e.target.style.display = 'none' }}
            onClick={() => setEasterEggActivo(true)}
          />
          {easterEggActivo && (
            <iframe
              title="easter-egg-audio"
              src="https://www.youtube.com/embed/ojZ0k9ymdU0?autoplay=1"
              allow="autoplay"
              style={{ width: 0, height: 0, border: 'none', position: 'absolute' }}
            />
          )}

          {/* Pegatina interactiva de Indy para empezar la experiencia (Más grande!) */}
          <button
            onClick={() => setEstado('form')}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              outline: 'none',
              padding: 0,
              marginBottom: 14,
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
                maxWidth: 460,
                width: '100%',
                height: 'auto',
                objectFit: 'contain',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                filter: 'grayscale(25%) sepia(15%) drop-shadow(0 8px 16px rgba(0, 0, 0, 0.6))'
              }}
            />
          </button>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, alignItems: 'center', width: '90%', maxWidth: 320 }}>
            <button onClick={() => setMostrarSuerteModal(true)} className="btn-secondary" style={{ width: '100%', padding: '14px 20px', fontSize: 14 }}
              onMouseEnter={e => { e.currentTarget.style.boxShadow = 'inset 0 1px 0 rgba(255,255,255,0.2), 0 0 24px rgba(240, 192, 64, 0.45)' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = '' }}
            >
              CHAT CON INDY
            </button>
            <button onClick={() => setMostrarModal(true)} className="btn-secondary" style={{ width: '100%', padding: '10px 20px', fontSize: 13 }}
              onMouseEnter={e => { e.currentTarget.style.boxShadow = 'inset 0 1px 0 rgba(255,255,255,0.2), 0 0 24px rgba(240, 192, 64, 0.45)' }}
              onMouseLeave={e => { e.currentTarget.style.boxShadow = '' }}
            >
              ¿Por qué me llamo Indy?
            </button>
          </div>
        </div>
      )}

      {/* ── FORMULARIO ── */}
      {estado === 'form' && (
        <Formulario
          onBuscar={(datos) => { setEsSuerte(false); handleBuscar(datos) }}
          onVolver={() => { setEstado('intro'); setTituloAnioPendiente({ titulo: '', anio: null, tmdb_id: null }); setForzarNuevo(false) }}
          onComprobarTitulo={comprobarTitulo}
          onBuscarCandidatos={buscarCandidatos}
          startAtStep2={forzarNuevo}
          tituloInicial={tituloAnioPendiente.titulo}
          anioInicial={tituloAnioPendiente.anio}
          tmdbIdInicial={tituloAnioPendiente.tmdb_id}
        />
      )}

      {/* ── CARGANDO ── */}
      {estado === 'cargando' && <Cargando />}

      {/* ── CACHÉ ── */}
      {estado === 'cache' && cacheInfo && (
        <div style={{
          minHeight: '100vh', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', padding: '40px 24px',
          backgroundImage: 'linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)), url(/fondo.jpg)',
          backgroundSize: 'cover', backgroundPosition: 'center', backgroundAttachment: 'fixed',
        }}>
          <div className="glass-panel" style={{ maxWidth: 520, width: '100%', padding: '40px 36px', textAlign: 'center' }}>
            <h3 style={{
              fontFamily: 'var(--font-title)', fontSize: 26,
              color: 'var(--gold)', letterSpacing: 1.5, marginBottom: 20,
            }}>
              Ya analicé esta película
            </h3>
            <p style={{
              fontFamily: 'var(--font-body)', fontSize: 14, color: 'var(--text-2)', marginBottom: 8,
            }}>
              Indy ya analizó esta película el <strong style={{ color: 'var(--gold)' }}>{cacheInfo.fecha_consulta}</strong>
            </p>
            <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--text-3)', marginBottom: 36 }}>
              ¿Usamos el análisis guardado o repetimos la misión?
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              <button className="btn-main" style={{ fontSize: 13, padding: '14px 28px' }}
                onClick={() => { setInforme(cacheInfo.informe); setPosterUrl(cacheInfo.informe?.poster_url || null); setEstado('informe') }}>
                USAR GUARDADO
              </button>
              <button className="btn-secondary"
                onClick={() => { setForzarNuevo(true); setEstado('form') }}>
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
          backgroundImage: 'linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url(/fondo.jpg)',
          backgroundSize: 'cover', backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
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
          <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: 880, padding: '40px 44px' }}>
            <button onClick={() => setMostrarModal(false)} style={{
              position: 'absolute', top: 20, right: 20,
              background: 'none', border: 'none', color: 'var(--text-2)',
              fontSize: 22, cursor: 'pointer', fontFamily: 'monospace',
              lineHeight: 1
            }}>
              ✕
            </button>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 32, alignItems: 'stretch' }}>

              {/* Columna izquierda: foto grande */}
              <div style={{ flex: '1 1 220px', maxWidth: 280 }}>
                <img src="/indy_real.jpg" alt="Indy el Schnauzer Real" style={{
                  width: '100%', height: '100%', minHeight: 260,
                  borderRadius: 18, objectFit: 'cover',
                  border: '2px solid var(--gold)',
                  boxShadow: '0 8px 24px rgba(240, 192, 64, 0.2), inset 0 1px 0 rgba(255,255,255,0.1)',
                  display: 'block',
                }} />
              </div>

              {/* Columna derecha: historia, dos tercios del módulo */}
              <div style={{ flex: '2 1 360px', textAlign: 'left' }}>
                <h3 style={{
                  fontFamily: 'var(--font-title)', fontSize: 28,
                  color: 'var(--gold)', letterSpacing: 2, marginBottom: 18
                }}>
                  Déjame que te cuente su historia...
                </h3>

                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 14,
                  color: 'var(--text)', lineHeight: 1.75, marginBottom: 16,
                }}>
                  Indy era mi perro, adoptado en 2012 y procedente de Badajoz. Un schnauzer de carácter, con esas cejas pobladas que le daban siempre cara de estar juzgándote en silencio. Su nombre procede, evidentemente, de Indiana Jones. Pero, ¿por qué Indiana Jones?
                </p>

                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 14,
                  color: 'var(--text-2)', lineHeight: 1.75, marginBottom: 16,
                }}>
                  Resulta que, como se explica en <em>"Indiana Jones y la última cruzada"</em>, Indy en realidad se llama Henry Jones Jr. Entonces, ¿por qué ese famoso nombre? Curiosamente, poca gente recuerda que su nombre procede de un perro de su infancia, llamado Indiana.
                </p>

                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 14,
                  color: 'var(--text-2)', lineHeight: 1.75, marginBottom: 16,
                }}>
                  Así que este agente, Indy, debe su nombre a mi perro de toda la vida, quien a su vez recibió su nombre por el famoso arqueólogo encarnado por Harrison Ford.
                </p>

                <p style={{
                  fontFamily: 'var(--font-body)', fontSize: 14,
                  color: 'var(--text-2)', lineHeight: 1.75, marginBottom: 28,
                }}>
                  Y si el agente tiene tanto carácter al opinar sobre cine, es por algo: los schnauzer son así, tercos, curiosos y con un olfato infalible para detectar cuándo algo no merece la pena. Indy nunca se conformaba con cualquier paseo, y este Indy tampoco se conforma con cualquier película.
                </p>

                <button className="btn-secondary" onClick={() => setMostrarModal(false)} style={{ padding: '10px 24px' }}>
                  Cerrar
                </button>
              </div>
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
                <p style={{ fontFamily: 'var(--font-title)', fontSize: 26, letterSpacing: 1.5, color: 'var(--gold)', marginTop: 16 }}>
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
                <p style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 20, color: '#ef5350', marginBottom: 12 }}>
                  Error de conexión
                </p>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--text-2)', textAlign: 'center', marginBottom: 24, lineHeight: 1.5 }}>
                  {suerteError}
                </p>
                <div style={{ display: 'flex', gap: 12, width: '100%', justifyContent: 'center' }}>
                  <button className="btn-secondary" onClick={handleSuerteRecomendar} style={{ width: '55%', padding: '10px 20px', fontSize: 14 }}>
                    Reintentar
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
                    <h4 style={{ fontFamily: 'var(--font-title)', fontSize: 22, color: 'var(--gold)', margin: 0, letterSpacing: 1 }}>Indy</h4>
                    <span style={{ fontFamily: 'var(--font-body)', fontWeight: 700, fontSize: 10, color: 'var(--gold)', textTransform: 'uppercase', letterSpacing: 1, display: 'block' }}>En línea</span>
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
                    background: 'linear-gradient(135deg, rgba(240, 192, 64, 0.12) 0%, rgba(240, 192, 64, 0.03) 100%)',
                    border: '1px solid rgba(240, 192, 64, 0.3)',
                    borderRadius: '16px 16px 16px 2px',
                    padding: '16px',
                    boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
                    textAlign: 'left'
                  }}>
                    <p style={{ fontFamily: 'var(--font-body)', fontSize: 14, color: 'var(--text)', margin: 0, lineHeight: 1.5 }}>
                      Te recomiendo ver:{' '}
                      <a
                        href={urlPlataforma(suertePlataforma, suerteResultado.titulo)}
                        target="_blank" rel="noopener noreferrer"
                        style={{ color: 'var(--gold)', fontSize: 16, fontWeight: 700, textDecoration: 'underline', textUnderlineOffset: 3 }}
                      >
                        {suerteResultado.titulo}
                      </a>{' '}
                      {suerteResultado.anio ? `(${suerteResultado.anio})` : ''}
                    </p>
                    <p style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--text-2)', margin: '12px 0 0 0', lineHeight: 1.5, fontStyle: 'italic', borderTop: '1px solid rgba(240,192,64,0.18)', paddingTop: 10 }}>
                      "{suerteResultado.justificacion_eleccion}"
                    </p>
                    <div style={{ display: 'flex', gap: 12, marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(240,192,64,0.18)' }}>
                      <a href={urlImdb(suerteResultado.titulo)} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--text-3)', letterSpacing: 0.5 }}>IMDb ↗</a>
                      <a href={urlFilmaffinity(suerteResultado.titulo)} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--text-3)', letterSpacing: 0.5 }}>FilmAffinity ↗</a>
                      <a href={urlLetterboxd(suerteResultado.titulo)} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--text-3)', letterSpacing: 0.5 }}>Letterboxd ↗</a>
                    </div>
                  </div>
                </div>

                {/* Botones de acción */}
                <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                  <button
                    className="btn-secondary"
                    onClick={() => { setSuerteResultado(null); setSuertePrompt('') }}
                    style={{ width: '60%', padding: '10px 20px', fontSize: 14 }}
                  >
                    Preguntar otra cosa
                  </button>
                  <button className="btn-secondary" onClick={closeSuerteModal} style={{ width: '35%', padding: '10px 16px', fontSize: 14 }}>
                    Cerrar chat
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
                <h3 style={{
                  fontFamily: 'var(--font-title)', fontSize: 28,
                  color: 'var(--gold)', letterSpacing: 2, marginBottom: 8
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
                  <p style={{ fontFamily: 'var(--font-body)', fontSize: 10, fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase', color: 'var(--gold)', marginBottom: 8 }}>
                    ✦ Plataforma de streaming
                  </p>
                  <select className="inp" value={suertePlataforma} onChange={e => setSuertePlataforma(e.target.value)} disabled={suerteCargando} style={{
                    fontSize: 14, padding: '10px 14px'
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
                  <p style={{ fontFamily: 'var(--font-body)', fontSize: 10, fontWeight: 700, letterSpacing: 3, textTransform: 'uppercase', color: 'var(--gold)', marginBottom: 8 }}>
                    ✦ Tu mensaje para Indy
                  </p>
                  <textarea
                    className="inp"
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
                    style={{ height: 110, fontSize: 14, resize: 'none', lineHeight: 1.5 }}
                    autoFocus
                  />
                </div>

                <div style={{ display: 'flex', gap: 12, width: '100%', justifyContent: 'center' }}>
                  <button
                    className="btn-secondary"
                    onClick={handleSuerteRecomendar}
                    disabled={suerteCargando || !suertePrompt.trim()}
                    style={{
                      width: '65%', padding: '12px 24px', fontSize: 15,
                      opacity: suertePrompt.trim() ? 1 : 0.5,
                      cursor: suertePrompt.trim() ? 'pointer' : 'not-allowed'
                    }}
                  >
                    {suerteCargando ? 'Indy pensando...' : 'Enviar a Indy'}
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

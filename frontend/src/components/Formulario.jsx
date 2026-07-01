import { useState, useRef, useEffect } from 'react'

// cada png trae un margen transparente distinto alrededor del dibujo, así que con objectFit
// contain el dibujo real se ve más grande o más pequeño según la imagen aunque la caja mida igual.
// compenso ese margen con una escala calculada a partir del recuadro real de cada dibujo,
// sin recortar los png originales para no arriesgarme a cortar los bordes decorativos.
const PERFILES = [
  { key: 'palomitero',    label: 'El Palomitero',    img: '/palomitero.png',    escala: 1.00 },
  { key: 'independiente', label: 'El Independiente',  img: '/independiente.png', escala: 1.03 },
  { key: 'fantastico',    label: 'El Fantástico',     img: '/fantastico.png',    escala: 1.01 },
  { key: 'dramatico',     label: 'El Dramático',      img: '/dramatico.png',     escala: 1.20 },
  { key: 'curioso',       label: 'El Curioso',        img: '/curioso.png',       escala: 1.21 },
]

// espera tras la última pulsación de tecla antes de consultar la api — evita saturarla en cada letra
const DEBOUNCE_MS = 350
// longitud mínima del texto para empezar a buscar coincidencias
const MIN_CARACTERES = 2
// referencia al filtro de grano que aplico a los pósters de perfil, para que combinen con la pegatina de inicio
const FILTRO_GRANO = 'url(#grano-perfiles) '

export default function Formulario({ onBuscar, onVolver, onComprobarTitulo, onBuscarCandidatos, startAtStep2, tituloInicial, anioInicial, tmdbIdInicial }) {
  const [step, setStep]     = useState(startAtStep2 ? 2 : 1)
  const [titulo, setTitulo] = useState(tituloInicial || '')
  const [anio, setAnio]     = useState(anioInicial ? String(anioInicial) : '')
  const [tmdbId, setTmdbId] = useState(tmdbIdInicial || null)
  const [perfil, setPerfil] = useState(null)
  const [comprobandoCache, setComprobandoCache] = useState(false)
  const [seleccion, setSeleccion]   = useState(null)
  const [candidatos, setCandidatos] = useState([])
  const [buscando, setBuscando]     = useState(false)
  const inputRef      = useRef(null)
  const debounceRef   = useRef(null)
  const abortRef       = useRef(null)
  const cacheBusquedas = useRef({}) // memoiza resultados ya consultados para no repetir peticiones
  const carruselRef    = useRef(null) // referencia a la tira de candidatos para poder desplazarla con flechas
  // guardo si puedo desplazar la tira de candidatos hacia la izquierda o hacia la derecha
  const [puedeIzq, setPuedeIzq] = useState(false)
  const [puedeDer, setPuedeDer] = useState(false)

  // reviso cuánto se puede desplazar la tira de candidatos y actualizo las flechas visibles
  const actualizarFlechas = () => {
    const el = carruselRef.current
    if (!el) { setPuedeIzq(false); setPuedeDer(false); return }
    setPuedeIzq(el.scrollLeft > 4)
    setPuedeDer(el.scrollLeft + el.clientWidth < el.scrollWidth - 4)
  }

  // recalculo las flechas cada vez que cambia la lista de candidatos mostrada
  useEffect(() => { actualizarFlechas() }, [candidatos])

  // desplazo la tira de candidatos hacia el lado indicado al pulsar una flecha
  const desplazarCarrusel = (direccion) => {
    const el = carruselRef.current
    if (!el) return
    // uso instant en vez de smooth porque el desplazamiento animado no avanza en algunos navegadores sin pestaña visible
    el.scrollBy({ left: direccion * 200, behavior: 'instant' })
    // recalculo las flechas justo después del desplazamiento, sin esperar al evento scroll
    setTimeout(actualizarFlechas, 0)
  }

  useEffect(() => { setTimeout(() => inputRef.current?.focus(), 100) }, [step])

  // cancelo cualquier timer o petición en vuelo si el componente se desmonta
  useEffect(() => () => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (abortRef.current) abortRef.current.abort()
  }, [])

  const buscarCandidatos = async (texto) => {
    if (cacheBusquedas.current[texto]) {
      setCandidatos(cacheBusquedas.current[texto])
      setBuscando(false)
      return
    }
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller
    try {
      const lista = await onBuscarCandidatos(texto, controller.signal)
      cacheBusquedas.current[texto] = lista
      setCandidatos(lista)
    } catch (e) {
      if (e.name !== 'AbortError') setCandidatos([])
    } finally {
      setBuscando(false)
    }
  }

  const onChangeTitulo = (valor) => {
    setTitulo(valor)
    setSeleccion(null)
    setTmdbId(null)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    const texto = valor.trim()
    if (texto.length < MIN_CARACTERES) {
      if (abortRef.current) abortRef.current.abort()
      setCandidatos([])
      setBuscando(false)
      return
    }
    setBuscando(true)
    debounceRef.current = setTimeout(() => buscarCandidatos(texto), DEBOUNCE_MS)
  }

  // avanza al paso del perfil (o a la pantalla de caché) usando el candidato elegido o el texto libre
  const avanzar = async (candidato) => {
    const tituloFinal = candidato?.titulo || titulo.trim()
    if (!tituloFinal || comprobandoCache) return
    const anioFinal   = candidato?.anio ? parseInt(candidato.anio) : (anio ? parseInt(anio) : null)
    const tmdbIdFinal = candidato?.tmdb_id || tmdbId || null
    setComprobandoCache(true)
    const tieneCache = await onComprobarTitulo(tituloFinal, anioFinal, tmdbIdFinal)
    setComprobandoCache(false)
    if (!tieneCache) setStep(2)
  }

  const seleccionar = (c) => {
    setSeleccion(c)
    setTitulo(c.titulo)
    setTmdbId(c.tmdb_id)
    setCandidatos([])
    avanzar(c)
  }

  const submit = (perfilKey) => {
    if (!titulo.trim() || !perfilKey) return
    onBuscar({
      titulo: seleccion?.titulo || titulo.trim(),
      perfil_usuario: perfilKey,
      anio: seleccion?.anio ? parseInt(seleccion.anio) : (anio ? parseInt(anio) : null),
      tmdb_id: seleccion?.tmdb_id || tmdbId || null,
      nombre_usuario: null,
    })
  }

  const mostrarResultados = step === 1 && !seleccion && titulo.trim().length >= MIN_CARACTERES

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', padding: '40px 24px',
      backgroundImage: 'linear-gradient(rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0.65)), url(/fondo.jpg)',
      backgroundSize: 'cover', backgroundPosition: 'center',
      backgroundAttachment: 'fixed',
    }}>
      {/* defino aquí el filtro de grano, oculto, para que los pósters de perfil combinen con la pegatina de inicio */}
      <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true">
        <filter id="grano-perfiles">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" result="ruido" />
          <feColorMatrix type="saturate" values="0" in="ruido" result="ruidoGris" />
          {/* comprimo el ruido a un rango estrecho para que oscurezca poco y el grano quede sutil */}
          <feComponentTransfer in="ruidoGris" result="ruidoSuave">
            <feFuncR type="linear" slope="0.15" intercept="0.85" />
            <feFuncG type="linear" slope="0.15" intercept="0.85" />
            <feFuncB type="linear" slope="0.15" intercept="0.85" />
          </feComponentTransfer>
          {/* recorto el ruido a la silueta real del png para que no se vea como un bloque gris fuera del dibujo */}
          <feComposite in="ruidoSuave" in2="SourceGraphic" operator="in" result="ruidoRecortado" />
          <feBlend in="SourceGraphic" in2="ruidoRecortado" mode="multiply" />
        </filter>
      </svg>

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
              onChange={e => onChangeTitulo(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && avanzar(seleccion)}
              placeholder="El Padrino, Dune, Barbie…"
              style={{ marginBottom: seleccion ? 12 : 8, borderRadius: 12 }}
            />

            {/* Confirmación de la película elegida en la lista de candidatos */}
            {seleccion && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 10, justifyContent: 'center',
                marginBottom: 24, padding: '8px 14px', borderRadius: 12,
                background: 'rgba(240, 192, 64, 0.08)', border: '1px solid rgba(240, 192, 64, 0.25)',
              }}>
                {seleccion.poster_url && (
                  <img src={seleccion.poster_url} alt={seleccion.titulo}
                    style={{ width: 34, height: 50, objectFit: 'cover', borderRadius: 4 }} />
                )}
                <span style={{ fontFamily: 'var(--font-body)', fontSize: 13, color: 'var(--gold)', fontWeight: 700 }}>
                  {seleccion.titulo}{seleccion.anio ? ` (${seleccion.anio})` : ''}
                </span>
                <button type="button" onClick={() => { setSeleccion(null); setTmdbId(null); inputRef.current?.focus() }}
                  style={{ background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer', fontSize: 12, textDecoration: 'underline' }}>
                  cambiar
                </button>
              </div>
            )}

            {/* Resultados en vivo con póster mientras se escribe */}
            {mostrarResultados && (
              <div style={{ marginBottom: 28, minHeight: 24, textAlign: 'left' }}>
                {buscando && (
                  <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--text-3)', textAlign: 'center' }}>
                    Buscando coincidencias…
                  </p>
                )}
                {!buscando && candidatos.length > 0 && (
                  <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                    {/* flecha izquierda — la mantengo siempre montada y solo cambio su visibilidad,
                        para que la tira de candidatos no cambie de posición entre hermanos y pierda el scroll */}
                    <button type="button" onClick={() => desplazarCarrusel(-1)}
                      style={{
                        position: 'absolute', left: -4, zIndex: 1, width: 28, height: 28, borderRadius: '50%',
                        background: 'rgba(0,0,0,0.55)', border: '1px solid rgba(255,255,255,0.25)',
                        color: 'var(--text)', cursor: puedeIzq ? 'pointer' : 'default', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        opacity: puedeIzq ? 1 : 0, pointerEvents: puedeIzq ? 'auto' : 'none',
                        transition: 'opacity 0.15s ease',
                      }}
                      aria-hidden={!puedeIzq}
                      aria-label="Ver coincidencias anteriores"
                    >
                      ‹
                    </button>
                    <div ref={carruselRef} className="no-scrollbar" onScroll={actualizarFlechas}
                      style={{ display: 'flex', gap: 10, overflowX: 'auto', paddingBottom: 4, justifyContent: candidatos.length < 4 ? 'center' : 'flex-start' }}>
                      {candidatos.map(c => (
                        <button key={c.tmdb_id} type="button" onClick={() => seleccionar(c)}
                          style={{
                            display: 'flex', flexDirection: 'column', alignItems: 'center',
                            width: 92, flexShrink: 0, background: 'rgba(255,255,255,0.03)',
                            border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10,
                            padding: 6, cursor: 'pointer', transition: 'border-color 0.2s ease',
                          }}
                          onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(240, 192, 64, 0.6)' }}
                          onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)' }}
                        >
                          {c.poster_url ? (
                            <img src={c.poster_url} alt={c.titulo}
                              style={{ width: 78, height: 112, objectFit: 'cover', borderRadius: 6, marginBottom: 6 }} />
                          ) : (
                            <div style={{
                              width: 78, height: 112, borderRadius: 6, marginBottom: 6,
                              background: 'rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center',
                              justifyContent: 'center', textAlign: 'center', fontSize: 10, color: 'var(--text-3)', padding: 4,
                            }}>
                              Sin póster
                            </div>
                          )}
                          <span style={{ fontFamily: 'var(--font-body)', fontSize: 11, color: 'var(--text)', lineHeight: 1.25, textAlign: 'center' }}>
                            {c.titulo}
                          </span>
                          <span style={{ fontFamily: 'var(--font-body)', fontSize: 10, color: 'var(--text-3)' }}>
                            {c.anio || '—'}
                          </span>
                        </button>
                      ))}
                    </div>
                    {/* flecha derecha — igual que la izquierda, siempre montada y con visibilidad por css */}
                    <button type="button" onClick={() => desplazarCarrusel(1)}
                      style={{
                        position: 'absolute', right: -4, zIndex: 1, width: 28, height: 28, borderRadius: '50%',
                        background: 'rgba(0,0,0,0.55)', border: '1px solid rgba(255,255,255,0.25)',
                        color: 'var(--text)', cursor: puedeDer ? 'pointer' : 'default', display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        opacity: puedeDer ? 1 : 0, pointerEvents: puedeDer ? 'auto' : 'none',
                        transition: 'opacity 0.15s ease',
                      }}
                      aria-hidden={!puedeDer}
                      aria-label="Ver más coincidencias"
                    >
                      ›
                    </button>
                  </div>
                )}
                {!buscando && candidatos.length === 0 && (
                  <p style={{ fontFamily: 'var(--font-body)', fontSize: 12, color: 'var(--text-3)', textAlign: 'center' }}>
                    Sin coincidencias — puedes continuar igualmente con "Siguiente".
                  </p>
                )}
              </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, width: '100%', marginTop: seleccion || mostrarResultados ? 0 : 24 }}>
              <button className="btn-secondary" onClick={onVolver}
                style={{ width: 160, padding: '16px 0', fontSize: 14, fontFamily: 'var(--font-ui)', fontWeight: 700, textAlign: 'center' }}>
                ← Atrás
              </button>
              <button className="btn-secondary"
                disabled={!titulo.trim() || comprobandoCache}
                onClick={() => avanzar(seleccion)}
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

            <div className="no-scrollbar" style={{ display: 'flex', flexDirection: 'row', flexWrap: 'nowrap', gap: 14, justifyContent: 'center', marginBottom: 36, width: '100%', overflowX: 'auto' }}>
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
                    // fijo un tamaño igual para las cinco, sin que crezcan ni encojan con el ancho de la pantalla
                    flex: '0 0 auto',
                    width: 220,
                    height: 220,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    // recorto aquí el margen transparente sobrante tras compensar el tamaño,
                    // así nunca se cuela sobre la pegatina de al lado
                    overflow: 'hidden',
                    transform: perfil === p.key ? 'scale(1.06)' : 'scale(1)',
                  }}
                >
                  <img
                    src={p.img}
                    alt={p.label}
                    style={{
                      // ancho y alto fijos con objectFit contain para que todas las pegatinas midan igual
                      // aunque el png de origen tenga una proporción distinta
                      width: '100%',
                      height: '100%',
                      objectFit: 'contain',
                      // compenso aquí el margen transparente propio de este png para igualar el tamaño visible
                      transform: `scale(${p.escala})`,
                      transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                      filter: perfil === p.key
                        ? FILTRO_GRANO + 'drop-shadow(0 0 15px rgba(240, 192, 64, 0.8))'
                        : FILTRO_GRANO + 'drop-shadow(0 6px 12px rgba(0, 0, 0, 0.5))',
                    }}
                    onMouseEnter={e => {
                      if (perfil !== p.key) {
                        e.currentTarget.style.filter = FILTRO_GRANO + 'drop-shadow(0 0 12px rgba(240, 192, 64, 0.45)) drop-shadow(0 8px 16px rgba(0,0,0,0.6))';
                        e.currentTarget.parentElement.style.transform = 'scale(1.04)';
                      }
                    }}
                    onMouseLeave={e => {
                      if (perfil !== p.key) {
                        e.currentTarget.style.filter = FILTRO_GRANO + 'drop-shadow(0 6px 12px rgba(0, 0, 0, 0.5))';
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

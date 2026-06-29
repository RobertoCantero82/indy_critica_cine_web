export default function PegatinaSVG({ titulo, anio, genero, recomendacion }) {
  const esPositivo = recomendacion === 'SÍ'
  const stamp      = esPositivo ? '¡SÍ!' : '¡NO!'
  const stampColor = esPositivo ? '#2d7a2d' : '#c0392b'
  const gen        = (genero || 'CINE').toUpperCase().slice(0, 12)

  // Limitar título para que quepa
  const tituloCorto = titulo && titulo.length > 18 ? titulo.slice(0, 17) + '…' : titulo || ''

  return (
    <svg
      viewBox="0 0 260 300"
      xmlns="http://www.w3.org/2000/svg"
      style={{ width: '100%', filter: 'drop-shadow(0 6px 20px rgba(0,0,0,0.5))' }}
    >
      <defs>
        {/* Textura de grano */}
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" result="noise" />
          <feColorMatrix type="saturate" values="0" in="noise" result="grayNoise" />
          <feBlend in="SourceGraphic" in2="grayNoise" mode="multiply" result="blend" />
          <feComponentTransfer in="blend">
            <feFuncA type="linear" slope="1" />
          </feComponentTransfer>
        </filter>
        {/* Borde desgastado */}
        <filter id="rough">
          <feTurbulence type="turbulence" baseFrequency="0.04" numOctaves="2" seed="3" result="turb" />
          <feDisplacementMap in="SourceGraphic" in2="turb" scale="3" xChannelSelector="R" yChannelSelector="G" />
        </filter>
      </defs>

      {/* ── Fondo negro de la pegatina ── */}
      <rect x="8" y="8" width="244" height="284" rx="18" ry="18"
        fill="#111" filter="url(#rough)" />

      {/* ── Borde blanco grueso ── */}
      <rect x="8" y="8" width="244" height="284" rx="18" ry="18"
        fill="none" stroke="white" strokeWidth="6" filter="url(#rough)" />

      {/* ── Borde interior fino ── */}
      <rect x="18" y="18" width="224" height="264" rx="12" ry="12"
        fill="none" stroke="white" strokeWidth="1.5" strokeDasharray="4 3" opacity="0.4" />

      {/* ── Género arriba ── */}
      <text x="130" y="48"
        fontFamily="'Courier New', monospace" fontSize="11" fontWeight="700"
        fill="white" textAnchor="middle" letterSpacing="4" opacity="0.7">
        {gen}
      </text>

      {/* ── Línea decorativa ── */}
      <line x1="40" y1="56" x2="220" y2="56" stroke="white" strokeWidth="1" opacity="0.3" />

      {/* ── Icono central: proyector retro en SVG ── */}
      <g transform="translate(130,150)" opacity="0.9">
        {/* Cuerpo del proyector */}
        <rect x="-38" y="-28" width="76" height="50" rx="6" fill="none" stroke="white" strokeWidth="2.5" />
        {/* Lente */}
        <circle cx="0" cy="-4" r="16" fill="none" stroke="white" strokeWidth="2.5" />
        <circle cx="0" cy="-4" r="9" fill="none" stroke="white" strokeWidth="1.5" opacity="0.5" />
        {/* Bobinas */}
        <circle cx="-26" cy="-18" r="8" fill="none" stroke="white" strokeWidth="2" />
        <circle cx="26" cy="-18" r="8" fill="none" stroke="white" strokeWidth="2" />
        {/* Rayo de luz */}
        <polygon points="-6,12 6,12 18,40 -18,40" fill="white" opacity="0.12" />
        {/* Patas */}
        <line x1="-20" y1="22" x2="-24" y2="38" stroke="white" strokeWidth="2" />
        <line x1="20" y1="22" x2="24" y2="38" stroke="white" strokeWidth="2" />
        <line x1="-28" y1="38" x2="28" y2="38" stroke="white" strokeWidth="2" />
      </g>

      {/* ── Estrellas decorativas ── */}
      {[40, 220].map((x, i) => (
        <text key={i} x={x} y="155"
          fontFamily="serif" fontSize="14" fill="white" textAnchor="middle" opacity="0.5">★</text>
      ))}

      {/* ── Línea separadora ── */}
      <line x1="30" y1="210" x2="230" y2="210" stroke="white" strokeWidth="1" opacity="0.3" />

      {/* ── Título ── */}
      <text x="130" y="238"
        fontFamily="'Georgia', serif" fontSize="22" fontWeight="700"
        fill="white" textAnchor="middle" letterSpacing="1">
        {tituloCorto}
      </text>

      {/* ── Año ── */}
      <text x="130" y="256"
        fontFamily="'Courier New', monospace" fontSize="11"
        fill="white" textAnchor="middle" opacity="0.55" letterSpacing="2">
        {anio || ''}
      </text>

      {/* ── Stamp de veredicto ── */}
      <g transform="translate(200, 82)">
        <circle cx="0" cy="0" r="26" fill="none" stroke={stampColor} strokeWidth="3" opacity="0.9" />
        <circle cx="0" cy="0" r="22" fill="none" stroke={stampColor} strokeWidth="1" opacity="0.5" />
        <text x="0" y="6"
          fontFamily="'Georgia', serif" fontSize="15" fontWeight="700"
          fill={stampColor} textAnchor="middle" opacity="0.9">
          {stamp}
        </text>
      </g>

      {/* ── Textura de grano encima ── */}
      <rect x="8" y="8" width="244" height="284" rx="18" ry="18"
        fill="url(#grain)" opacity="0.08" />
    </svg>
  )
}

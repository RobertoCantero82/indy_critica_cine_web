import { useState, useEffect } from 'react'

const FRASES = [
  "Espera, que la peli es tan intensa que me está erizando las cejas de schnauzer mientras la analizo...",
  "Buscando el Santo Grial del cine en la base de datos (o al menos algo que no te dé ganas de dormir la siesta)...",
  "Intercambiando la película por un saco de arena en el servidor a ver si no se activa la trampa...",
  "Comprobando si los primeros diez minutos duelen más que caer en una trampa de un templo maldito...",
  "Cruzando desiertos y esquivando dardos venenosos para traerte el informe...",
  "Peinándome la barba de schnauzer mientras decido si esto es cine o tortura...",
  "Estudiando los datos con esa mirada juiciosa que solo un schnauzer y un arqueólogo pueden poner...",
  "Evaluando los primeros minutos (mi nivel de escepticismo ahora mismo es proporcional al tamaño de mis cejas)...",
  "¡Esquivando una roca gigante de clichés cinematográficos! Casi no lo cuento...",
  "Dándole golpes al teclado con las almohadillas de las patas porque esto no carga lo suficientemente rápido...",
  "Sacudiéndome el polvo de tres tumbas egipcias de la barba mientras analizo la película...",
  "Dando tres vueltas sobre mí mismo antes de tumbarme a redactar el veredicto definitivo...",
  "Desplegando un mapa gigante sobre la mesa para ver por dónde se ha perdido el guion de esta peli...",
  "Enterrando los peores giros cinematográficos en el jardín para que nadie los sufra...",
  "Esperando a que termine de explotar el maíz en el microondas mientras se procesa el informe...",
  "Abriéndome paso a machetazos entre la maleza de los diálogos pretenciosos...",
  "Desenrollando un papiro de críticas tan largo que ya me llega a las patas traseras...",
  "Se me está quedando la barba tiesa con el giro de guion que acabo de procesar...",
  "Ladrándole al router a ver si así los bytes corren más rápido...",
  "Pisando con cuidado las baldosas del servidor para no activar la trampa de los spoilers...",
  "Midiendo la comodidad del sofá (si la peli es mala, al menos que la siesta sea arqueológica)...",
  "Oliendo el ambiente a ver si detecto aroma a peliculón o a tostón infumable..."
]

export default function Cargando() {
  const [frase, setFrase] = useState('')

  useEffect(() => {
    const obtenerAleatoria = (excluir = '') => {
      const disponibles = FRASES.filter(f => f !== excluir)
      return disponibles[Math.floor(Math.random() * disponibles.length)]
    }

    setFrase(obtenerAleatoria())

    const t = setInterval(() => {
      setFrase(current => obtenerAleatoria(current))
    }, 8500)

    return () => clearInterval(t)
  }, [])

  const fraseSinPuntos = frase.endsWith('...') ? frase.slice(0, -3) : frase

  return (
    <div style={{
      minHeight: '100vh', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
      background: 'rgba(13,11,10,0.84)',
      backdropFilter: 'blur(8px)',
      WebkitBackdropFilter: 'blur(8px)',
      padding: 32,
    }}>
      <p key={frase} style={{
        fontFamily: 'var(--font-body)',
        fontSize: 'clamp(18px, 3vw, 24px)',
        color: 'var(--gold)',
        letterSpacing: 0.5,
        textAlign: 'center',
        maxWidth: 700,
        lineHeight: 1.6,
        animation: 'fade-phrase 0.5s ease',
      }}>
        {fraseSinPuntos}
        <span className="loading-dots">
          <span>.</span><span>.</span><span>.</span>
        </span>
      </p>
      <style>{`
        @keyframes fade-phrase {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .loading-dots span {
          animation: loading-dot-blink 1.4s infinite both;
          display: inline-block;
        }
        .loading-dots span:nth-child(2) {
          animation-delay: .2s;
        }
        .loading-dots span:nth-child(3) {
          animation-delay: .4s;
        }
        @keyframes loading-dot-blink {
          0% { opacity: .2; transform: translateY(0); }
          50% { opacity: 1; transform: translateY(-3px); }
          100% { opacity: .2; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}

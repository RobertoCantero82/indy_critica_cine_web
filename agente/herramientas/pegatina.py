# pegatina.py — herramienta 4: genera la url de la pegatina coleccionable via pollinations.ai

from urllib.parse import quote


class Pegatina:
    """
    genera una url de imagen en pollinations.ai con estilo pegatina retro
    basada en los datos de la película.
    sin api key, sin coste, sin registro.
    """

    def _construir_prompt(self, titulo: str, generos: list, director: str) -> str:
        genero = generos[0] if generos else "film"

        return (
            f"cuphead game art style sticker, cartoon character from '{titulo}' {genero} movie, "
            f"1930s fleischer studios rubber hose animation, bold expressive action pose, "
            f"thick black ink outlines, pure black and white grayscale, "
            f"die-cut sticker badge shape, thick white border all around, "
            f"vintage worn texture, halftone dots, retro cartoon poster aesthetic, "
            f"no color, no gradients, high contrast black and white illustration only"
        )

    def ejecutar(self, titulo: str, generos: list, director: str = None) -> dict:
        try:
            prompt = self._construir_prompt(titulo, generos, director)
            encoded = quote(prompt)
            # seed fijo por título para que la misma peli siempre genere la misma pegatina
            seed = abs(hash(titulo)) % 9999
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed={seed}"
            return {"ok": True, "pegatina_url": url}
        except Exception as e:
            return {"ok": False, "error": str(e)}

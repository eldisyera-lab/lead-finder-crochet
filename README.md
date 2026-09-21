# 🧶 Lead Finder Ético para Crochet

Herramienta de **web scraping ético** para encontrar personas interesadas en aprender crochet (leads calificados) y promocionar cursos del canal **"Crochet para Aprender"**.

## ✨ ¿Qué hace?

Analiza comentarios públicos de videos de YouTube y páginas web autorizadas para detectar **intención de compra/aprendizaje** en el nicho del crochet:

- *"quiero aprender"*, *"¿cuánto cuesta?"*, *"soy principiante"*, *"¿algún curso?"*...

Los resultados se guardan en `leads_crochet.json` listos para tu estrategia de ventas.

## ⚖️ Principios éticos y legales

Esta herramienta fue diseñada bajo reglas estrictas de responsabilidad:

| ✅ Buenas prácticas implementadas | 🛑 Lo que NUNCA hace |
|---|---|
| Revisa `robots.txt` automáticamente | No extrae correos, teléfonos ni datos sensibles |
| Pausas de 5–10 s entre solicitudes (anti-DoS) | No bombardea servidores |
| User-Agent transparente con contacto | No raspa datos privados |
| Solo sitios propios o con permiso explícito | No ignora términos de servicio |

## 🔧 Requisitos

- Python 3.8 o superior
- Sin API keys, sin cuentas de Google — funciona en cualquier país

```bash
pip install -r requirements.txt
```

## 🚀 Uso

1. Edita el archivo `scraper_crochet_sin_api.py` y pon tu correo en `USER_AGENT`:
   ```python
   USER_AGENT = "CrochetParaAprenderBot/1.0 (contacto: tuemail@ejemplo.com)"
   ```
2. Agrega URLs de videos de crochet en la lista `VIDEOS` (idealmente de tu propio canal):
   ```python
   VIDEOS = [
       "https://www.youtube.com/watch?v=XXXXXXXXXXX",
   ]
   ```
3. Ejecuta:
   ```bash
   python scraper_crochet_sin_api.py
   ```
4. Revisa `leads_crochet.json` con los leads encontrados.

## 📁 Estructura

```
scraper-crochet/
├── scraper_crochet_sin_api.py   # Script principal (sin API key)
├── requirements.txt             # Dependencias
└── README.md                    # Este archivo
```

## ⚠️ Aviso legal

Este proyecto es **solo para fines educativos y de aprendizaje**. Usa la herramienta únicamente en sitios web que poseas o con permiso adecuado, siempre respetando `robots.txt`, los términos de servicio y las leyes de privacidad vigentes. El autor no se hace responsable del uso indebido.

## 🤝 Contacto

Canal: **Crochet para Aprender** 🧶

---

⭐ Si te sirvió, deja una estrella al repo.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
SCRAPER ETICO SIN API - "Crochet para Aprender"
=============================================================
Busca leads (personas con intencion de aprender crochet) en los
comentarios PUBLICOS de videos de YouTube, SIN necesidad de API key.

COMO FUNCIONA:
  1. Descarga el HTML publico de cada video (con pausas de cortesia).
  2. Extrae el JSON embebido (ytInitialData) donde YouTube guarda
     los comentarios visibles.
  3. Filtra los comentarios que muestran intencion de aprender/comprar.
  4. Guarda los leads en leads_crochet.json

NOTA: YouTube solo incluye los primeros comentarios en el HTML inicial.
Este script carga hasta 2 paginas adicionales de comentarios mediante
el token de continuacion. Para volumen alto, usa la API oficial v3.

REGLAS DE ORO IMPLEMENTADAS:
  - Pausas de 6-12 s entre solicitudes (cortesia / anti-sobrecarga)
  - User-Agent transparente con TU correo de contacto
  - Solo comentarios PUBLICOS; nunca datos privados
  - NO extrae correos, telefonos ni datos sensibles

Requisitos:
    pip install -r requirements.txt
"""

import json
import random
import re
import time
import unicodedata

import requests

# ============================================================
# CONFIGURACION — EDITA ESTO
# ============================================================
USER_AGENT = "CrochetParaAprenderBot/1.0 (contacto: eldisyerar@gmail.com)"
# IMPORTANTE: cambia 'eldisyerar@gmail.com' por TU correo real.

PAUSA_MIN = 6        # segundos minimos entre solicitudes
PAUSA_MAX = 12       # segundos maximos (aleatorio, comportamiento humano)
PAGINAS_EXTRA = 2    # paginas de comentarios adicionales por video

# Agrega aqui los URLs de videos de crochet (idealmente de tu propio canal)
VIDEOS = [
    "https://www.youtube.com/watch?v=XXXXXXXXXXX",
    # "https://www.youtube.com/watch?v=YYYYYYYYYYY",
]

PALABRAS_CLAVE_INTENCION = [
    "quiero aprender", "como aprendo", "me interesa",
    "donde compro", "cuanto cuesta", "cuanto vale",
    "necesito un curso", "recomiendan curso", "recomiendan algun curso",
    "soy principiante", "recien empiezo", "quiero empezar",
    "algun curso", "venden el curso", "tienen curso",
    "como me inscribo", "donde lo consigo", "haces algun curso",
]

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "es-419,es;q=0.9",
}

# Pre-calcular las palabras clave sin acentos para comparar
_CLAVES = None


def _claves_normalizadas():
    global _CLAVES
    if _CLAVES is None:
        _CLAVES = [normalizar(k) for k in PALABRAS_CLAVE_INTENCION]
    return _CLAVES


def normalizar(texto):
    """Minusculas y sin acentos, para comparar 'cuanto' == 'cuánto'."""
    texto = texto.lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def es_intencion(texto):
    t = normalizar(texto)
    return any(clave in t for clave in _claves_normalizadas())


# ============================================================
# UTILIDADES DE RED (con cortesia)
# ============================================================

def id_de_video(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w\-]{11})", url)
    return m.group(1) if m else None


def obtener_html(session, url, intentos=3):
    for i in range(intentos):
        try:
            r = session.get(url, headers=HEADERS, timeout=20)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            print("    reintento " + str(i + 1) + ": " + str(e))
            time.sleep(random.uniform(5, 10))
    return None


def extraer_titulo(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if m:
        return m.group(1).replace(" - YouTube", "").strip()
    return None


# ============================================================
# PARSEO DEL JSON EMBEBIDO DE YOUTUBE
# ============================================================

def extraer_yt_initial_data(html):
    """Localiza 'var ytInitialData = {...};' y decodifica el JSON."""
    idx = html.find("ytInitialData")
    while idx != -1:
        resto = html[idx:]
        m = re.match(r'ytInitialData["\']?\s*(?:\]\s*)?=\s*', resto)
        if m:
            inicio = idx + m.end()
            try:
                obj, _ = json.JSONDecoder().raw_decode(html[inicio:])
                return obj
            except json.JSONDecodeError:
                pass
        idx = html.find("ytInitialData", idx + 1)
    return None


def extraer_innertube(html):
    """Saca la API key interna y el contexto para paginar comentarios."""
    m = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', html)
    api_key = m.group(1) if m else None
    idx = html.find('"INNERTUBE_CONTEXT":')
    contexto = None
    if idx != -1:
        inicio = html.find("{", idx)
        try:
            contexto, _ = json.JSONDecoder().raw_decode(html[inicio:])
        except json.JSONDecodeError:
            contexto = None
    return api_key, contexto


def recoger_tokens(o, tokens):
    """Recolecta tokens de continuacion ('ver mas comentarios')."""
    if isinstance(o, dict):
        cc = o.get("continuationCommand")
        if isinstance(cc, dict) and isinstance(cc.get("token"), str):
            tokens.append(cc["token"])
        for v in o.values():
            recoger_tokens(v, tokens)
    elif isinstance(o, list):
        for v in o:
            recoger_tokens(v, tokens)


def tokens_seccion_comentarios(data):
    """Tokens de la seccion de comentarios en la pagina inicial."""
    tokens = []

    def rec(o):
        if isinstance(o, dict):
            sec = o.get("itemSectionRenderer")
            if isinstance(sec, dict) and sec.get("sectionIdentifier") == "comment-item-section":
                recoger_tokens(sec, tokens)
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)

    rec(data)
    return tokens


def acumular_comentarios(data, acum, vistos):
    """Recorre el JSON y guarda cada comentario visible (sin duplicados)."""
    def rec(o):
        if isinstance(o, dict):
            cr = o.get("commentRenderer")
            if isinstance(cr, dict):
                try:
                    autor = cr["authorText"]["simpleText"]
                    texto = "".join(
                        r.get("text", "") for r in cr["contentText"]["runs"]
                    ).strip()
                    clave = (autor, texto)
                    if texto and clave not in vistos:
                        vistos.add(clave)
                        acum.append({"autor": autor, "comentario": texto})
                except (KeyError, TypeError):
                    pass
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)

    rec(data)


def cargar_continuacion(session, api_key, contexto, token):
    url = "https://www.youtube.com/youtubei/v1/next?key=" + api_key
    payload = {"context": contexto, "continuation": token}
    r = session.post(url, json=payload, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


# ============================================================
# ANALISIS POR VIDEO
# ============================================================

def analizar_video(session, url, paginas_extra=PAGINAS_EXTRA):
    vid = id_de_video(url)
    if not vid:
        print("  URL no valida: " + url)
        return vid, None, []

    print("  Descargando: " + url)
    watch = "https://www.youtube.com/watch?v=" + vid + "&hl=es"
    html = obtener_html(session, watch)
    if not html:
        return vid, None, []

    titulo = extraer_titulo(html) or vid
    data = extraer_yt_initial_data(html)
    if data is None:
        print("    No se encontro ytInitialData (bloqueo o cambio de YouTube).")
        return vid, titulo, []

    comentarios, vistos = [], set()
    acumular_comentarios(data, comentarios, vistos)
    print("    Comentarios visibles en pagina inicial: " + str(len(comentarios)))

    # Paginacion de comentarios (boton 'ver mas')
    tokens = tokens_seccion_comentarios(data)
    api_key, contexto = extraer_innertube(html)
    pagina = 0
    while pagina < paginas_extra and tokens and api_key and contexto:
        token = tokens.pop(0)
        time.sleep(random.uniform(PAUSA_MIN, PAUSA_MAX))  # cortesia
        try:
            resp = cargar_continuacion(session, api_key, contexto, token)
        except requests.RequestException as e:
            print("    Error paginando comentarios: " + str(e))
            break
        acumular_comentarios(resp, comentarios, vistos)
        tokens = []
        recoger_tokens(resp, tokens)
        pagina += 1
        print("    Pagina extra " + str(pagina) + ": total " + str(len(comentarios)))

    return vid, titulo, comentarios


# ============================================================
# EJECUCION PRINCIPAL
# ============================================================

def main():
    print("=" * 55)
    print("LEAD FINDER ETICO (sin API) - Crochet para Aprender")
    print("=" * 55)

    if USER_AGENT.find("eldisyerar@gmail.com") != -1:
        print("\nAVISO: pon TU correo en USER_AGENT antes de ejecutar.\n")

    session = requests.Session()
    leads = []
    vistos_autores = set()

    for url in VIDEOS:
        vid, titulo, comentarios = analizar_video(session, url)
        if not titulo:
            continue
        print("  Video: " + titulo)
        nuevos = 0
        for c in comentarios:
            if es_intencion(c["comentario"]) and c["autor"] not in vistos_autores:
                vistos_autores.add(c["autor"])
                leads.append({
                    "autor": c["autor"],
                    "video": titulo,
                    "video_id": vid,
                    "comentario": c["comentario"][:200],
                    "tipo_lead": "alta_intencion",
                })
                nuevos += 1
        print("    -> Leads con intencion: " + str(nuevos))
        time.sleep(random.uniform(PAUSA_MIN, PAUSA_MAX))  # cortesia entre videos

    print("\nTotal de leads calificados: " + str(len(leads)))
    for i, lead in enumerate(leads[:10], 1):
        print("\n  " + str(i) + ". @" + lead["autor"])
        print("     Video: " + lead["video"])
        print("     Dice: " + lead["comentario"])

    with open("leads_crochet.json", "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)
    print("\nGuardado en leads_crochet.json")
    print("Proceso finalizado con pausas de cortesia.")


if __name__ == "__main__":
    main()

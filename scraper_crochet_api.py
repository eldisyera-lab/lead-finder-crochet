#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
SCRAPER ETICO PARA NICHO CROCHET - "Crochet para Aprender"
=============================================================
Objetivo: Encontrar personas interesadas en aprender crochet
(leads calificados) de forma 100% legal y etica.

METODO 1 (RECOMENDADO): YouTube Data API v3 (oficial y legal)
   - Extrae comentarios de videos de crochet con intencion de compra
     ("quiero aprender", "donde compro el curso?", "me interesa")
   - Requiere API key gratuita de Google Cloud

METODO 2: Scraper web generico CON PERMISO (blogs/propios sitios)
   - Respeta robots.txt automaticamente
   - Pausas obligatorias entre solicitudes
   - User-Agent identificable

REGLAS DE ORO IMPLEMENTADAS EN EL CODIGO:
   - Revision automatica de robots.txt
   - Pausas de cortesia (5-10 segundos entre solicitudes)
   - Solo datos publicos y no sensibles
   - User-Agent transparente (identifica tu bot)
   - NO extrae correos, telefonos ni datos personales sensibles
   - NO sobrecarga servidores

Requisitos:
    pip install requests beautifulsoup4 google-api-python-client
"""

import time
import random
import json
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ============================================================
# CONFIGURACION
# ============================================================
PAUSA_MIN = 5       # segundos minimos entre solicitudes (cortesia)
PAUSA_MAX = 10      # segundos maximos (aleatorio para parecer humano)
USER_AGENT = "CrochetParaAprenderBot/1.0 (contacto: tucorreo@ejemplo.com)"
# IMPORTANTE: Pon TU correo real. Un bot identificable = respetuoso.

PALABRAS_CLAVE_INTENCION = [
    "quiero aprender", "como aprendo", "como aprendo", "me interesa",
    "donde compro", "donde compro", "cuanto cuesta", "cuanto cuesta",
    "necesito un curso", "recomiendan curso", "soy principiante",
    "recien empiezo", "quiero empezar", "algun curso", "algun curso"
]

# ============================================================
# METODO 1: YOUTUBE DATA API v3 (LEGAL - API OFICIAL)
# ============================================================

def buscar_leads_youtube(api_key, max_videos=5, max_comentarios=50):
    """
    Busca videos de crochet y extrae comentarios con intencion de compra.
    Usa la API OFICIAL de YouTube (cumple Terminos de Servicio).

    Como obtener tu API key GRATIS (5 minutos):
    1. Ve a https://console.cloud.google.com
    2. Crea un proyecto nuevo (ej: "crochet-leads")
    3. Activa "YouTube Data API v3"
    4. Credenciales -> Crear clave API
    5. Listo! Copiala y pegala abajo.
    """
    from googleapiclient.discovery import build

    youtube = build("youtube", "v3", developerKey=api_key)

    # 1. Buscar videos populares de crochet
    print("\nBuscando videos de crochet...")
    busqueda = youtube.search().list(
        q="aprender crochet principiantes",
        part="snippet",
        type="video",
        maxResults=max_videos,
        order="viewCount"
    ).execute()

    leads = []

    for item in busqueda.get("items", []):
        video_id = item["id"]["videoId"]
        titulo = item["snippet"]["title"]
        print("  Analizando: " + titulo)

        # Pausa de cortesia (aunque la API lo permita, seamos gentiles)
        time.sleep(random.uniform(2, 4))

        # 2. Extraer comentarios del video
        try:
            comentarios = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_comentarios,
                order="relevance"
            ).execute()

            for c in comentarios.get("items", []):
                autor = c["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
                texto = c["snippet"]["topLevelComment"]["snippet"]["textDisplay"].lower()

                # 3. Filtrar solo comentarios con intencion de aprender/comprar
                if any(p in texto for p in PALABRAS_CLAVE_INTENCION):
                    leads.append({
                        "autor": autor,
                        "video": titulo,
                        "comentario": texto[:200],
                        "tipo_lead": "alta_intencion"
                    })
        except Exception as e:
            # Algunos videos tienen comentarios desactivados, es normal
            print("     (comentarios desactivados o error: " + str(e) + ")")

        time.sleep(random.uniform(PAUSA_MIN, PAUSA_MAX))

    return leads


# ============================================================
# METODO 2: SCRAPER WEB GENERICO (SOLO CON PERMISO / SITIOS PROPIOS)
# ============================================================

class ScraperEtico:
    """
    Scraper generico que CUMPLE automaticamente las buenas practicas:
    - Verifica robots.txt ANTES de cada dominio
    - Pausas aleatorias entre solicitudes
    - User-Agent transparente
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._robots_cache = {}

    def respeta_robots(self, url):
        """Devuelve True si robots.txt permite rastrear esa URL."""
        dominio = urlparse(url).scheme + "://" + urlparse(url).netloc
        if dominio not in self._robots_cache:
            rp = robotparser.RobotFileParser()
            rp.set_url(urljoin(dominio, "/robots.txt"))
            try:
                rp.read()
                self._robots_cache[dominio] = rp
            except Exception:
                # Si no hay robots.txt, asumimos permitido pero con cautela
                print("  ADVERTENCIA: No se pudo leer robots.txt de " + dominio)
                return True
        return self._robots_cache[dominio].can_fetch(USER_AGENT, url)

    def obtener(self, url):
        """Obtiene una pagina SOLO si robots.txt lo permite."""
        if not self.respeta_robots(url):
            print("  robots.txt PROHIBE: " + url + " -> se respeta y se omite.")
            return None

        print("  robots.txt permite: " + url)
        time.sleep(random.uniform(PAUSA_MIN, PAUSA_MAX))  # pausa de cortesia
        respuesta = self.session.get(url, timeout=15)
        respuesta.raise_for_status()
        return respuesta.text

    def extraer_texto(self, html, selector="p"):
        """Extrae texto de parrafos (ej: foros de crochet, blogs con permiso)."""
        sopa = BeautifulSoup(html, "html.parser")
        return [p.get_text(strip=True) for p in sopa.select(selector)
                if len(p.get_text(strip=True)) > 30]


# ============================================================
# EJEMPLO DE USO COMPLETO
# ============================================================

if __name__ == "__main__":

    print("=" * 55)
    print("LEAD FINDER ETICO - Crochet para Aprender")
    print("=" * 55)

    # ---- METODO 1: YouTube API ----
    API_KEY = "PEGA_AQUI_TU_API_KEY_DE_GOOGLE"
    # Obtén tu key gratis en: https://console.cloud.google.com

    if API_KEY != "PEGA_AQUI_TU_API_KEY_DE_GOOGLE":
        leads = buscar_leads_youtube(API_KEY)
        print("\nSe encontraron " + str(len(leads)) + " leads calificados:")
        for i, lead in enumerate(leads[:10], 1):
            print("\n  " + str(i) + ". @" + lead["autor"])
            print("     Video: " + lead["video"])
            print("     Dice: " + lead["comentario"])
        # Guardar resultados
        with open("leads_crochet.json", "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=2)
        print("\nGuardado en leads_crochet.json")
    else:
        print("\nConfigura tu API key de YouTube para el Metodo 1.")

    # ---- METODO 2: Ejemplo de scraping con permiso ----
    print("\n" + "-" * 55)
    print("METODO 2 - Scraper web (solo sitios propios o con permiso)")
    print("-" * 55)
    scraper = ScraperEtico()
    # Ejemplo: tu propio sitio web o un blog que te autorizo
    # url = "https://tusitio-web-crochet.com/blog"
    # html = scraper.obtener(url)
    # if html:
    #     parrafos = scraper.extraer_texto(html)
    #     print("Extraidos " + str(len(parrafos)) + " parrafos")

    print("\nProceso finalizado respetando robots.txt y pausas de cortesia.")
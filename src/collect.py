import csv
import os
import sys
import time
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import requests

URL = "https://trends.google.com/trending/rss?geo=BR"
ARQUIVO = "data/snapshots.csv"
CAMPOS = ["coletado_em", "posicao", "termo", "volume_aprox",
          "publicado_em", "noticia_titulo", "noticia_fonte"]


def nome_local(tag):
    return tag.split("}")[-1]


def buscar_rss():
    for tentativa in range(3):
        try:
            r = requests.get(URL, timeout=30,
                             headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            return r.content
        except requests.RequestException as e:
            print(f"Tentativa {tentativa + 1} falhou: {e}")
            time.sleep(5 * (tentativa + 1))
    return None


def parsear(conteudo, agora):
    raiz = ET.fromstring(conteudo)
    linhas = []
    for pos, item in enumerate(raiz.iter("item"), start=1):
        dados = {}
        noticia_titulo, noticia_fonte = "", ""
        for filho in item:
            nome = nome_local(filho.tag)
            if nome == "news_item":
                if not noticia_titulo:
                    for n in filho:
                        sub = nome_local(n.tag)
                        if sub == "news_item_title":
                            noticia_titulo = (n.text or "").strip()
                        elif sub == "news_item_source":
                            noticia_fonte = (n.text or "").strip()
            else:
                dados[nome] = (filho.text or "").strip()
        linhas.append({
            "coletado_em": agora,
            "posicao": pos,
            "termo": dados.get("title", ""),
            "volume_aprox": dados.get("approx_traffic", ""),
            "publicado_em": dados.get("pubDate", ""),
            "noticia_titulo": noticia_titulo,
            "noticia_fonte": noticia_fonte,
        })
    return linhas


def salvar(linhas):
    os.makedirs("data", exist_ok=True)
    novo = not os.path.exists(ARQUIVO)
    with open(ARQUIVO, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if novo:
            w.writeheader()
        w.writerows(linhas)


def main():
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    conteudo = buscar_rss()
    if conteudo is None:
        print("Não foi possível baixar o feed.")
        sys.exit(1)
    linhas = parsear(conteudo, agora)
    if not linhas:
        print("Feed sem itens. O formato pode ter mudado.")
        sys.exit(1)
    salvar(linhas)
    print(f"{len(linhas)} trends salvos.")


if __name__ == "__main__":
    main()

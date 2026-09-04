#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Só Vibrar · medição das alturas de seção.

Gera build/alturas-secoes.json, consumido pelo build para reservar a altura
certa de cada seção adiada. Sem esses números o navegador usa uma estimativa
única e a barra de rolagem salta enquanto a pessoa desce a página.

Rode este script quando a copy mudar o suficiente para alterar a altura das
seções. Ele exige Playwright, que o build normal não exige.

    python3 build/build.py && python3 build/medir_secoes.py && python3 build/build.py
"""

import json
import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(RAIZ, "dist")
SAIDA = os.path.join(RAIZ, "build", "alturas-secoes.json")
PORTA = 8137
LARGURA = 414


def main():
    if not os.path.isdir(DIST):
        sys.exit("Rode python3 build/build.py antes de medir.")

    from playwright.sync_api import sync_playwright

    servidor = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORTA), "--bind", "127.0.0.1"],
        cwd=DIST, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    chrome = os.environ.get("CHROME_PATH",
                            "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
    medidas = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"])
            for v in ("a", "b", "c", "d"):
                pg = b.new_page(viewport={"width": LARGURA, "height": 896})
                pg.goto("http://127.0.0.1:%d/%s/" % (PORTA, v), wait_until="load")
                pg.wait_for_timeout(1200)
                pg.add_style_tag(content="section.sv-adiada{content-visibility:visible!important}")
                pg.wait_for_timeout(800)
                alturas = pg.evaluate(
                    "() => Array.from(document.querySelectorAll('section'))"
                    ".map(s => Math.round(s.getBoundingClientRect().height))")
                medidas[v] = alturas
                print("  %s: %d seções  %s" % (v.upper(), len(alturas), alturas))
                pg.close()
            b.close()
    finally:
        servidor.terminate()

    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump({"largura_de_referencia": LARGURA, "alturas": medidas},
                  f, indent=2, ensure_ascii=False)
    print("\nGravado em build/alturas-secoes.json")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Só Vibrar · fontes próprias.

Substitui a Montserrat servida pelo Google por arquivos hospedados no mesmo
domínio das páginas, reduzidos aos caracteres que a copy realmente usa.

Por que isso importa mais do que parece em 4G:

- O `<link>` para fonts.googleapis.com **bloqueia a renderização**. A página
  não pinta nada enquanto ele não volta.
- São dois domínios novos, fonts.googleapis.com e fonts.gstatic.com, cada um
  com DNS, TCP e TLS próprios antes do primeiro byte útil.
- Servindo do próprio domínio, a conexão já está aberta e o arquivo pode ser
  pedido com `preload` no primeiro instante.

O subconjunto de caracteres é calculado a partir do texto das páginas, mais uma
margem de segurança com todo o alfabeto acentuado do português, dígitos e
pontuação. Pequenas edições de copy não quebram nada, e o build recalcula tudo
a cada execução.

Se a rede não estiver disponível e não houver cache, o módulo devolve a página
sem alteração, mantendo o Google Fonts. O build não quebra por causa disso.
"""

import os
import re
import unicodedata
import urllib.request

try:
    from fontTools import subset as ft_subset
    from fontTools.ttLib import TTFont
    FONTTOOLS = True
except ImportError:
    FONTTOOLS = False

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0.0.0 Safari/537.36")

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache-fontes")

# Margem de segurança: o que precisa existir na fonte mesmo que a copy mude.
BASE = (
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " .,;:!?()[]{}/\\-–—_'\"“”‘’«»…·•*&%#@+=<>|~^"
    "áàâãäéèêëíìîïóòôõöúùûüçñýÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑÝ"
    "ºª°§¹²³¼½¾±×÷€$£¥R"
)


def _baixar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        dados = r.read()
    with open(destino, "wb") as f:
        f.write(dados)
    return dados


def _origem_woff2(peso, italico):
    """Devolve o woff2 do subconjunto latino da Montserrat, do cache ou da rede."""
    os.makedirs(CACHE, exist_ok=True)
    nome = "montserrat-%d%s.woff2" % (peso, "-italic" if italico else "")
    caminho = os.path.join(CACHE, nome)
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            return f.read()

    if italico:
        familia = "family=Montserrat:ital,wght@1,%d" % peso
    else:
        familia = "family=Montserrat:wght@%d" % peso
    css_url = "https://fonts.googleapis.com/css2?%s&display=swap" % familia

    req = urllib.request.Request(css_url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        css = r.read().decode("utf-8")

    # Os blocos vêm rotulados por comentário. Queremos o latino.
    blocos = re.findall(r'/\*\s*([a-z-]+)\s*\*/\s*@font-face\s*\{(.*?)\}', css, re.S)
    alvo = None
    for rotulo, corpo in blocos:
        if rotulo == "latin":
            m = re.search(r'url\((https://fonts\.gstatic\.com[^)]+)\)', corpo)
            if m:
                alvo = m.group(1)
                break
    if not alvo:
        raise RuntimeError("subconjunto latino não encontrado para peso %d" % peso)

    return _baixar(alvo, caminho)


def _reduzir(dados_woff2, caracteres, saida):
    """Reduz a fonte aos caracteres pedidos e grava em woff2."""
    bruto = os.path.join(CACHE, "tmp-entrada.woff2")
    with open(bruto, "wb") as f:
        f.write(dados_woff2)

    fonte = TTFont(bruto)
    s = ft_subset.Subsetter(ft_subset.Options(
        layout_features=["kern", "liga", "clig", "calt", "ccmp", "locl"],
        notdef_outline=True,
        recalc_bounds=True,
        drop_tables=["DSIG"],
    ))
    s.populate(text="".join(sorted(caracteres)))
    s.subset(fonte)
    fonte.flavor = "woff2"
    fonte.save(saida)
    fonte.close()

    with TTFont(saida) as conferencia:
        cobertos = set()
        for tabela in conferencia["cmap"].tables:
            cobertos |= set(tabela.cmap.keys())
    faltando = {c for c in caracteres if ord(c) not in cobertos}
    return faltando


def caracteres_da_pagina(html):
    """Caracteres visíveis da página, sem marcação, sem CSS e sem script."""
    corpo = html.split("<body>", 1)[-1]
    corpo = re.sub(r'<(script|style)\b.*?</\1>', " ", corpo, flags=re.S | re.I)
    corpo = re.sub(r'<[^>]+>', " ", corpo)
    corpo = corpo.replace("&nbsp;", " ").replace("&amp;", "&")
    usados = {c for c in corpo if not c.isspace()}
    # Emoji e símbolos fora do latino não vêm da Montserrat.
    return {c for c in usados
            if ord(c) < 0x2200 and unicodedata.category(c)[0] != "C"}


def aplicar(html, pesos, italico, pasta_assets, catalogo, preload_pesos=None):
    """Troca o Google Fonts por arquivos próprios. Devolve (html, relatorio)."""
    if not FONTTOOLS:
        return html, {"ok": False, "motivo": "fonttools ausente"}

    pasta = os.path.join(pasta_assets, "fonts")
    os.makedirs(pasta, exist_ok=True)

    precisa = caracteres_da_pagina(html) | set(BASE)
    variantes = [(p, False) for p in pesos] + ([(400, True)] if italico else [])

    regras, arquivos, faltas = [], {}, set()
    for peso, ital in variantes:
        chave = (peso, ital)
        nome = "montserrat-%d%s.woff2" % (peso, "i" if ital else "")
        destino = os.path.join(pasta, nome)

        if chave in catalogo:
            # Já gerada por outra página. Confere se cobre esta copy também.
            faltando = catalogo[chave]["faltando"] & precisa
            if faltando:
                # Copy desta página exige caracteres novos: regera com a união.
                catalogo[chave]["chars"] |= precisa
                faltando = _reduzir(_origem_woff2(peso, ital),
                                    catalogo[chave]["chars"], destino)
                catalogo[chave]["faltando"] = faltando
        else:
            try:
                faltando = _reduzir(_origem_woff2(peso, ital), precisa, destino)
            except Exception as e:
                return html, {"ok": False, "motivo": str(e)}
            catalogo[chave] = {"chars": set(precisa), "faltando": faltando}

        faltas |= catalogo[chave]["faltando"]
        arquivos[chave] = "/assets/fonts/" + nome
        regras.append(
            "@font-face{font-family:'Montserrat';font-style:%s;font-weight:%d;"
            "font-display:swap;src:url('%s') format('woff2')}"
            % ("italic" if ital else "normal", peso, arquivos[chave])
        )

    if faltas:
        return html, {"ok": False,
                      "motivo": "caracteres fora do subconjunto latino: %s"
                                % "".join(sorted(faltas))[:40]}

    # Fora o Google Fonts, incluindo os preconnect que só serviam a ele.
    html = re.sub(r'\s*<link rel="preconnect" href="https://fonts\.[^"]*"[^>]*>', "", html)
    html = re.sub(r'\s*<link href="https://fonts\.googleapis\.com[^"]*" rel="stylesheet">', "", html)

    # Preconnect para os terceiros que continuam existindo.
    preconnect = (
        '<link rel="preconnect" href="https://scripts.converteai.net" crossorigin>\n'
        '<link rel="preconnect" href="https://www.googletagmanager.com">\n'
    )

    # Preload só dos pesos que aparecem acima da dobra. Pré-carregar todos
    # competiria com a imagem do topo pela mesma banda.
    alvo = preload_pesos or [400, max(pesos)]
    pre = "".join(
        '<link rel="preload" as="font" type="font/woff2" href="%s" crossorigin>\n'
        % arquivos[(p, False)]
        for p in alvo if (p, False) in arquivos
    )

    html = html.replace("</head>", preconnect + pre + "</head>", 1)
    html = html.replace("<style>", "<style>\n" + "\n".join(regras) + "\n", 1)

    tamanho = sum(os.path.getsize(os.path.join(pasta, os.path.basename(v)))
                  for v in arquivos.values())
    return html, {"ok": True, "arquivos": len(arquivos), "bytes": tamanho,
                  "glifos": len(precisa)}

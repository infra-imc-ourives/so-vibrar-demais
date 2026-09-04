#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Só Vibrar · otimizações de carregamento.

Módulo usado por build.py. Nada aqui altera copy: mexe apenas em como os
recursos da página são entregues ao navegador.

O que faz:

1. Tira as imagens de dentro do HTML. Elas estavam em base64, o que
   representava 98% do peso da versão A e 93% da B. Em base64 a imagem
   precisa ser baixada junto com o HTML, antes de o navegador pintar
   qualquer coisa, e não pode ser cacheada nem reaproveitada entre as
   quatro páginas.
2. Converte para WebP quando o arquivo fica menor, e reaproveita a mesma
   imagem quando ela se repete entre páginas.
3. Escreve width e height em cada <img>. Sem isso, imagem externa provoca
   deslocamento de layout, que era zero enquanto tudo era base64.
4. Pede prioridade alta para a imagem do topo e adia o carregamento das
   que estão abaixo da dobra.
5. Reduz os pesos de fonte pedidos ao Google Fonts para os que a página
   realmente usa. Cada peso é um arquivo separado.

Pillow é opcional. Sem ele, as imagens saem no formato original e sem
width e height.
"""

import base64
import hashlib
import os
import re

try:
    from PIL import Image
    import io as _io
    PILLOW = True
except ImportError:
    PILLOW = False


PADRAO_IMG = re.compile(r'data:image/([a-zA-Z+]+);base64,([A-Za-z0-9+/=]+)')

EXTENSAO = {"jpeg": "jpg", "jpg": "jpg", "png": "png", "gif": "gif",
            "webp": "webp", "svg+xml": "svg"}


def _dimensoes(dados):
    if not PILLOW:
        return None
    try:
        with Image.open(_io.BytesIO(dados)) as im:
            return im.size
    except Exception:
        return None


def _para_webp(dados, formato):
    """Converte para WebP. Devolve None se não compensar ou não der."""
    if not PILLOW or formato == "svg+xml" or formato == "gif":
        return None
    try:
        with Image.open(_io.BytesIO(dados)) as im:
            tem_alfa = im.mode in ("RGBA", "LA") or (
                im.mode == "P" and "transparency" in im.info)
            im = im.convert("RGBA" if tem_alfa else "RGB")
            buf = _io.BytesIO()
            im.save(buf, "WEBP", quality=82, method=6)
            saida = buf.getvalue()
    except Exception:
        return None
    return saida if len(saida) < len(dados) * 0.95 else None


def extrair_imagens(html, pasta_assets, catalogo):
    """Troca cada data URI por um arquivo em /assets. `catalogo` é um dict
    compartilhado entre as páginas, para a mesma imagem virar um arquivo só."""
    os.makedirs(pasta_assets, exist_ok=True)
    tamanhos = {}

    def trocar(m):
        formato = m.group(1).lower()
        dados = base64.b64decode(m.group(2))
        chave = hashlib.sha1(dados).hexdigest()[:12]

        if chave in catalogo:
            caminho, dim = catalogo[chave]
            tamanhos[caminho] = dim
            return caminho

        ext = EXTENSAO.get(formato, "bin")
        dim = _dimensoes(dados)

        webp = _para_webp(dados, formato)
        if webp is not None:
            dados, ext = webp, "webp"

        nome = "img-%s.%s" % (chave, ext)
        with open(os.path.join(pasta_assets, nome), "wb") as f:
            f.write(dados)

        caminho = "/assets/" + nome
        catalogo[chave] = (caminho, dim)
        tamanhos[caminho] = dim
        return caminho

    return PADRAO_IMG.sub(trocar, html), tamanhos


def anotar_imagens(html, tamanhos):
    """Escreve width, height e prioridade de carregamento em cada <img>.

    A primeira imagem da página fica com prioridade alta, porque costuma ser
    o elemento que define o LCP. As demais carregam sob demanda."""
    indice = [0]

    def trocar(m):
        tag = m.group(0)
        indice[0] += 1
        primeira = indice[0] == 1

        src = re.search(r'src="([^"]+)"', tag)
        if src and src.group(1) in tamanhos:
            dim = tamanhos[src.group(1)]
            if dim and "width=" not in tag:
                tag = tag[:-1] + ' width="%d" height="%d">' % dim

        if "decoding=" not in tag:
            tag = tag[:-1] + ' decoding="async">'
        if primeira:
            if "fetchpriority=" not in tag:
                tag = tag[:-1] + ' fetchpriority="high">'
        elif "loading=" not in tag:
            tag = tag[:-1] + ' loading="lazy">'
        return tag

    return re.sub(r'<img\b[^>]*>', trocar, html)


def preload_do_topo(html):
    """Preload da imagem de fundo do topo. Ela é pedida pelo CSS, então o
    navegador só descobre que precisa dela depois de montar o CSSOM."""
    m = re.search(r"url\('(/assets/[^']+)'\)", html)
    if not m:
        return html
    link = ('<link rel="preload" as="image" href="%s" fetchpriority="high">\n'
            % m.group(1))
    return html.replace("</head>", link + "</head>", 1)


def ajustar_fontes(html, pesos, italico):
    """Reduz a lista de pesos pedida ao Google Fonts.

    Cada peso é um arquivo woff2 próprio. As páginas pediam sete ou oito
    variações e usavam de três a cinco."""
    if italico:
        lista = ";".join("0,%d" % p for p in pesos) + ";1,400"
        familia = "family=Montserrat:ital,wght@" + lista
    else:
        familia = "family=Montserrat:wght@" + ";".join(str(p) for p in pesos)

    return re.sub(
        r'family=Montserrat:[^"&]+',
        familia,
        html,
    )


SCRIPT_PLAYER_ADIADO = """
<script>
/* === Player da VSL · carregamento fora do caminho crítico ===
   O script do player responde por praticamente todo o tempo de bloqueio da
   página. Aqui ele passa a ser pedido depois que a página já pintou e o
   navegador está ocioso, com um teto de 3 segundos para o caso de a
   ociosidade não chegar. O vídeo continua na mesma posição e ninguém
   precisa clicar em nada a mais para assistir. */
(function () {
  var pedido = false;
  function carregar() {
    if (pedido) return;
    pedido = true;
    var s = document.createElement('script');
    s.src = '__PLAYER_SRC__';
    s.async = true;
    document.head.appendChild(s);
  }
  function agendar() {
    if (window.requestIdleCallback) {
      window.requestIdleCallback(carregar, { timeout: 3000 });
    } else {
      setTimeout(carregar, 1200);
    }
  }
  if (document.readyState === 'complete') agendar();
  else window.addEventListener('load', agendar);

  /* Se a pessoa tocar no vídeo antes disso, carrega na hora. */
  document.addEventListener('DOMContentLoaded', function () {
    var wrap = document.querySelector('.vsl-wrap, .vslbox');
    if (wrap) ['click', 'touchstart'].forEach(function (ev) {
      wrap.addEventListener(ev, carregar, { once: true });
    });
  });
})();
</script>
"""


def adiar_player(html):
    """Substitui a injeção imediata do player pela versão adiada."""
    m = re.search(
        r'<script type="text/javascript">\s*var s=document\.createElement\("script"\);'
        r'\s*s\.src="([^"]+)".*?</script>',
        html, re.S)
    if not m:
        return html, False
    novo = SCRIPT_PLAYER_ADIADO.replace("__PLAYER_SRC__", m.group(1))
    return html[:m.start()] + novo + html[m.end():], True

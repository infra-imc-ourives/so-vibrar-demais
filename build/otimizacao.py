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


# ---------------------------------------------------- vídeos do YouTube

FACADE_CSS = """
.yt-facade{position:relative;display:block;width:100%;height:100%;border:0;
border-radius:inherit;overflow:hidden;cursor:pointer;background:#000}
.yt-facade img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.yt-facade .yt-play{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
width:64px;height:46px;border-radius:12px;background:rgba(0,0,0,0.72);
display:flex;align-items:center;justify-content:center;transition:background .18s ease}
.yt-facade:hover .yt-play,.yt-facade:focus-visible .yt-play{background:#FF0000}
.yt-facade .yt-play::after{content:"";border-style:solid;border-width:11px 0 11px 19px;
border-color:transparent transparent transparent #fff;margin-left:4px}
.yt-facade iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
"""

FACADE_JS = """
<script>
/* === Depoimentos do YouTube · carregamento sob demanda ===
   Cada player do YouTube custa mais de um megabyte de JavaScript e disputa a
   linha principal do navegador. Aqui a página mostra a capa do vídeo, que pesa
   alguns kilobytes, e só monta o player quando a pessoa toca para assistir.
   O vídeo abre já tocando, então o toque continua sendo um só. */
document.addEventListener('click', function (e) {
  var alvo = e.target.closest ? e.target.closest('.yt-facade') : null;
  if (!alvo || alvo.dataset.pronto) return;
  alvo.dataset.pronto = '1';
  var f = document.createElement('iframe');
  f.src = 'https://www.youtube.com/embed/' + alvo.dataset.video +
          '?autoplay=1&rel=0&modestbranding=1';
  f.title = alvo.dataset.titulo || 'Depoimento';
  f.allow = 'accelerometer; autoplay; encrypted-media; picture-in-picture';
  f.setAttribute('allowfullscreen', '');
  alvo.innerHTML = '';
  alvo.appendChild(f);
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ event: 'sv_depoimento_play', sv_video: alvo.dataset.video });
}, true);

/* Teclado: o card é um botão, então espaço e enter também abrem o vídeo. */
document.addEventListener('keydown', function (e) {
  if (e.key !== 'Enter' && e.key !== ' ') return;
  var alvo = e.target.classList && e.target.classList.contains('yt-facade') ? e.target : null;
  if (!alvo) return;
  e.preventDefault();
  alvo.click();
});

/* Se a capa não vier (bloqueador, rede), some com ela em vez de mostrar o
   ícone de imagem quebrada. O fundo preto com o botão continua legível. */
document.addEventListener('error', function (e) {
  var img = e.target;
  if (img.tagName === 'IMG' && img.parentElement &&
      img.parentElement.classList.contains('yt-facade')) {
    img.style.display = 'none';
  }
}, true);
</script>
"""


def facade_youtube(html):
    """Troca cada iframe do YouTube por uma capa clicável."""
    achados = [0]

    def trocar(m):
        tag = m.group(0)
        vid = re.search(r'youtube\.com/embed/([A-Za-z0-9_-]+)', tag)
        if not vid:
            return tag
        achados[0] += 1
        titulo = re.search(r'title="([^"]*)"', tag)
        return (
            '<div class="yt-facade" data-video="%s" data-titulo="%s" '
            'role="button" tabindex="0" aria-label="Assistir ao depoimento">'
            '<img src="https://i.ytimg.com/vi/%s/hqdefault.jpg" alt="" '
            'loading="lazy" decoding="async" width="480" height="360">'
            '<span class="yt-play" aria-hidden="true"></span></div>'
            % (vid.group(1), titulo.group(1) if titulo else "Depoimento", vid.group(1))
        )

    novo = re.sub(r'<iframe\b[^>]*youtube\.com/embed/[^>]*>\s*</iframe>', trocar, html)
    if not achados[0]:
        novo = re.sub(r'<iframe\b[^>]*youtube\.com/embed/[^>]*>', trocar, html)
    if not achados[0]:
        return html, 0

    novo = novo.replace("<style>", "<style>" + FACADE_CSS, 1)
    novo = novo.replace("</body>", FACADE_JS + "</body>", 1)
    return novo, achados[0]


# ------------------------------------------- seções fora da tela

def pular_render_fora_da_tela(html, alturas=None, a_partir_de=2, minimo_total=6000):
    """Deixa o navegador adiar o trabalho de layout das seções longe da dobra.

    Só faz sentido em página muito longa: a versão B tem 18.554 px em celular,
    cerca de 21 telas. Sem isso, o navegador calcula o layout e a pintura das
    21 telas antes de mostrar a primeira.

    `contain-intrinsic-size` reserva a altura de cada seção enquanto ela não é
    renderizada. As alturas vêm medidas de build/alturas-secoes.json: com uma
    estimativa única, uma seção de 4.304 px reservaria 900 px e a barra de
    rolagem saltaria enquanto a pessoa desce. Sem as medidas, a função não faz
    nada, porque o salto custa mais do que o ganho."""
    if not alturas:
        return html, 0
    if sum(alturas) < minimo_total:
        return html, 0

    contador = [0]
    usadas = []

    def trocar(m):
        i = contador[0]
        contador[0] += 1
        if i < a_partir_de or i >= len(alturas):
            return m.group(0)
        usadas.append((i, alturas[i]))
        tag = m.group(0)
        classes = "sv-adiada sv-s%d" % i
        if 'class="' in tag:
            return tag.replace('class="', 'class="%s ' % classes, 1)
        return tag[:-1] + ' class="%s">' % classes

    novo_html = re.sub(r'<section\b[^>]*>', trocar, html)
    if not usadas:
        return html, 0

    regras = ["\nsection.sv-adiada{content-visibility:auto}"]
    for i, h in usadas:
        regras.append("section.sv-s%d{contain-intrinsic-size:auto %dpx}" % (i, h))
    regras.append("")

    novo_html = novo_html.replace("<style>", "<style>" + "\n".join(regras), 1)
    return novo_html, len(usadas)

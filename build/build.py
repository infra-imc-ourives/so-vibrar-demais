#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Só Vibrar · build das páginas de teste A/B/C/D.

Lê os arquivos aprovados em baseline/ e gera dist/, aplicando as correções
técnicas necessárias para que o teste possa ser medido e para que a versão A
revele o botão no momento certo.

A copy nunca é alterada por este script. Ele só mexe em <head>, em atributos
href de checkout e no script de revelação do CTA da versão A.

Uso:  python3 build/build.py
"""

import os
import re
import shutil

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(RAIZ, "baseline")
DIST = os.path.join(RAIZ, "dist")

DOMINIO = "https://sovibrar.elainneourives.com.br"

# Imagem de compartilhamento. PRECISA ser enviada para a raiz do domínio.
# Enquanto o arquivo não existir, o link compartilhado no WhatsApp aparece sem capa.
OG_IMAGE = DOMINIO + "/og-so-vibrar.jpg"

# Container do Google Tag Manager do Instituto. Todo o tracking (Pixel da Meta,
# GA4, conversões) deve ser disparado por dentro dele, nunca colado direto na
# página, para não duplicar evento com o container global.
GTM_ID = "GTM-PX6PZLNQ"

# Segundo do vídeo em que a Elainne inicia a oferta na VSL.
# Valor a confirmar com a Jacky. 840 = 14min00s.
PITCH_SECONDS = 840

VARIANTES = {
    "a": {
        "arquivo": "a-vsl-pura.html",
        "titulo": "Só Vibrar | Elainne Ourives",
        "descricao": (
            "Existe um cadeado invisível travando a sua vida, e não é falta de "
            "esforço. Assista ao vídeo e descubra os 5 cadeados emocionais."
        ),
    },
    "b": {
        "arquivo": "b-escada-completa.html",
        "titulo": "Só Vibrar | Elainne Ourives",
        "descricao": (
            "10 minutos por dia é o que você precisa para transformar sua vida. "
            "Destrave os poderes ocultos da sua mente com o Só Vibrar."
        ),
    },
    "c": {
        "arquivo": "c-hibrida.html",
        "titulo": "Só Vibrar | Elainne Ourives",
        "descricao": (
            "Elainne Ourives revela os 5 cadeados emocionais que mantêm você no "
            "mesmo lugar e a chave de 10 minutos por dia que abre cada um deles."
        ),
    },
    "d": {
        "arquivo": "d-advertorial.html",
        "titulo": "Os 5 cadeados invisíveis | Instituto Elainne Ourives",
        "descricao": (
            "Por que algumas pessoas fazem de tudo e não saem do lugar? A resposta "
            "pode estar em 5 cadeados emocionais que operam no inconsciente."
        ),
    },
}

# Variante servida na raiz do domínio até o teste apontar a vencedora.
VARIANTE_RAIZ = "b"


# ------------------------------------------------------------------ GTM

GTM_HEAD = """<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','__GTM_ID__');</script>
<!-- End Google Tag Manager -->
"""

GTM_BODY = """<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=__GTM_ID__"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager -->
"""


def aplicar_gtm(html):
    """GTM o mais alto possível no <head>, logo após charset e viewport, e o
    noscript imediatamente após a abertura do <body>."""
    marcador = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
    if marcador not in html:
        raise SystemExit("ERRO: meta viewport não encontrada; GTM não foi aplicado.")
    html = html.replace(
        marcador,
        marcador + "\n" + GTM_HEAD.replace("__GTM_ID__", GTM_ID),
        1,
    )
    if "<body>" not in html:
        raise SystemExit("ERRO: tag <body> não encontrada; noscript do GTM não aplicado.")
    return html.replace(
        "<body>",
        "<body>\n" + GTM_BODY.replace("__GTM_ID__", GTM_ID),
        1,
    )


# ---------------------------------------------------------------- head

def montar_head(variante, dados):
    """Meta description, Open Graph, Twitter Card e canonical."""
    url = "%s/%s/" % (DOMINIO, variante)
    return """<meta name="description" content="{descricao}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#050508">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Instituto Elainne Ourives">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{descricao}">
<meta property="og:image" content="{imagem}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{titulo}">
<meta name="twitter:description" content="{descricao}">
<meta name="twitter:image" content="{imagem}">
""".format(
        descricao=dados["descricao"],
        titulo=dados["titulo"],
        url=url,
        imagem=OG_IMAGE,
    )


def aplicar_head(html, variante, dados):
    # Remove a description existente para não duplicar (só a versão B tem uma).
    html = re.sub(r'\s*<meta name="description"[^>]*>\s*', "\n", html, flags=re.I)

    bloco = montar_head(variante, dados)
    marcador = '<link rel="preconnect" href="https://fonts.googleapis.com">'
    if marcador in html:
        return html.replace(marcador, bloco + marcador, 1)
    return html.replace("</head>", bloco + "</head>", 1)


# ---------------------------------------------------------- atribuição

SCRIPT_ATRIBUICAO = """
<script>
/* === Só Vibrar · atribuição de variante e eventos de checkout ===
   Encaminha para o checkout os parâmetros que vieram do anúncio e carimba a
   variante do teste. Sem isso, as vendas das quatro versões chegam
   indistinguíveis na Hubla e o teste não pode ser lido. */
(function () {
  var VARIANTE = '__VARIANTE__';

  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({ event: 'sv_page_view', sv_variante: VARIANTE });

  var params = new URLSearchParams(window.location.search);
  params.set('sv_var', VARIANTE);
  if (!params.get('utm_campaign')) params.set('utm_campaign', 'so-vibrar');
  if (!params.get('utm_content')) params.set('utm_content', 'variante-' + VARIANTE);
  var query = params.toString();

  function carimbar() {
    var links = document.querySelectorAll('a[href*="pay.hub.la"]');
    Array.prototype.forEach.call(links, function (link, i) {
      var posicao = i + 1;
      var base = link.getAttribute('href').split('?')[0];
      link.setAttribute('href', base + '?' + query + '&sv_cta=' + posicao);
      link.addEventListener('click', function () {
        window.dataLayer.push({
          event: 'sv_checkout_click',
          sv_variante: VARIANTE,
          sv_cta: posicao,
          sv_cta_texto: (link.textContent || '').trim()
        });
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', carimbar);
  } else {
    carimbar();
  }
})();
</script>
"""


def aplicar_atribuicao(html, variante):
    script = SCRIPT_ATRIBUICAO.replace("__VARIANTE__", variante)
    return html.replace("</body>", script + "</body>", 1)


# ------------------------------------------------------- CTA da versão A

SCRIPT_CTA_A = """
<script>
/* === Versão A · revelação do botão de compra ===
   O baseline revelava o CTA por setTimeout contado a partir do carregamento
   da página. Quem abria a página e não dava play recebia o botão do mesmo
   jeito, e quem dava play atrasado recebia o botão antes do pitch.

   Aqui a contagem é do vídeo, não da página:
   1. tenta acompanhar o relógio do player;
   2. se o player não expuser a API, conta a partir do play da pessoa. */
var PITCH_SECONDS = __PITCH__;

(function () {
  var area = document.getElementById('cta-area');
  if (!area) return;

  var revelado = false;
  function revelar(motivo) {
    if (revelado) return;
    revelado = true;
    area.classList.add('show');
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({ event: 'sv_cta_revelado', sv_motivo: motivo });
  }

  /* 1. Relógio do player. O smartplayer da Vturb muda de API entre versões,
     por isso testamos antes de usar e mantemos o caminho 2 como garantia. */
  function ligarNoPlayer() {
    var p = window.smartplayer;
    if (p && p.instances && p.instances.length) p = p.instances[0];
    if (!p || typeof p.on !== 'function') return false;
    p.on('timeupdate', function () {
      var t = (p.video && p.video.currentTime) || p.currentTime || 0;
      if (t >= PITCH_SECONDS) revelar('tempo-de-video');
    });
    return true;
  }

  var tentativas = 0;
  var sonda = setInterval(function () {
    if (ligarNoPlayer() || ++tentativas > 60) clearInterval(sonda);
  }, 500);

  /* 2. Contagem iniciada pela interação com o player, nunca pelo load. */
  var wrap = document.querySelector('.vsl-wrap');
  if (wrap) {
    var eventos = ['click', 'touchstart', 'keydown'];
    var iniciar = function () {
      eventos.forEach(function (ev) { wrap.removeEventListener(ev, iniciar); });
      setTimeout(function () { revelar('tempo-decorrido'); }, PITCH_SECONDS * 1000);
    };
    eventos.forEach(function (ev) { wrap.addEventListener(ev, iniciar); });
  }
})();
</script>
"""


def aplicar_cta_a(html):
    """Substitui o bloco de revelação do baseline pela versão corrigida."""
    padrao = re.compile(
        r"<script>\s*/\* CONFIG: segundo em que o botão aparece.*?</script>",
        re.S,
    )
    novo = SCRIPT_CTA_A.replace("__PITCH__", str(PITCH_SECONDS))
    html, trocas = padrao.subn(novo, html)
    if trocas != 1:
        raise SystemExit(
            "ERRO: bloco de revelação do CTA não encontrado em a-vsl-pura.html. "
            "O baseline mudou; revise build/build.py antes de publicar."
        )
    return html


# ------------------------------------------------------------------ main

def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    for variante, dados in VARIANTES.items():
        origem = os.path.join(BASELINE, dados["arquivo"])
        with open(origem, encoding="utf-8") as f:
            html = f.read()

        html = aplicar_gtm(html)
        html = aplicar_head(html, variante, dados)
        html = aplicar_atribuicao(html, variante)
        if variante == "a":
            html = aplicar_cta_a(html)

        destino = os.path.join(DIST, variante)
        os.makedirs(destino)
        caminho = os.path.join(destino, "index.html")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)

        kb = os.path.getsize(caminho) / 1024
        print("  dist/%s/index.html  (%.0f KB)" % (variante, kb))

    # Raiz do domínio serve a mesma página da variante escolhida.
    shutil.copyfile(
        os.path.join(DIST, VARIANTE_RAIZ, "index.html"),
        os.path.join(DIST, "index.html"),
    )
    print("  dist/index.html      (cópia da variante %s)" % VARIANTE_RAIZ.upper())
    print("\nBuild concluído. Confirme PITCH_SECONDS antes de liberar tráfego.")


if __name__ == "__main__":
    main()

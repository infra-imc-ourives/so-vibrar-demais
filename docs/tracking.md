# Tracking · Só Vibrar

O que está instalado nas cinco páginas geradas, onde fica e como conferir.

## O que está no ar

| Ferramenta | Identificador | Onde | Arquivos pedidos |
|---|---|---|---|
| Google Tag Manager | `GTM-PX6PZLNQ` | topo do `<head>`, `noscript` após `<body>` | `gtm.js` |
| VK Digital | `QPCsaqlFossljbjphJFJ` | `<head>`, logo abaixo do GTM | `sales_pixel.js?v=56`, `event_pageview.js`, `pixel.js?v=55` |

Os dois blocos da VK estão palavra por palavra como a VK enviou. Quando eles
mandarem versão nova, troque em `build/build.py` (constante `PIXEIS_VK`) e rode
o build. **Nunca edite `dist/` direto:** a alteração some na próxima geração.

## Por que a VK fica no `<head>` e não no fim do `<body>`

Pixel de atribuição precisa disparar cedo. Se a pessoa clicar no botão de
checkout antes de ele carregar, a venda chega na VK sem origem, e o teste A/B/C/D
perde justamente o dado que ele existe para produzir.

Os três arquivos são pedidos de forma assíncrona pelo próprio código da VK,
então estar no `<head>` não bloqueia a renderização. Foi acrescentado também um
`preconnect` para `cf.vkdigital.com.br`, que abre DNS, TCP e TLS no primeiro
instante e reduz a espera quando os scripts forem pedidos de fato.

## Proteção contra instalação dupla

O build interrompe com erro se encontrar `vkdigital` já presente no arquivo de
origem. Instalar o mesmo pixel duas vezes dobra `page_view` e dobra venda no
relatório, e é um erro que só aparece semanas depois, quando os números não
fecham com a plataforma.

O mesmo vale para o GTM: ele já estava instalado desde a primeira versão destas
páginas. Colar o container de novo criaria disparo duplo de tudo.

## Eventos próprios no dataLayer

Além do que GTM e VK medem sozinhos, as páginas publicam estes eventos para você
criar gatilhos dentro do GTM:

| Evento | Quando dispara | Variáveis |
|---|---|---|
| `sv_page_view` | carregamento da página | `sv_variante` |
| `sv_checkout_click` | clique em qualquer botão de checkout | `sv_variante`, `sv_cta`, `sv_cta_texto` |
| `sv_cta_revelado` | versão A, quando o botão aparece | `sv_motivo` |
| `sv_depoimento_play` | versão B, toque em um depoimento | `sv_video` |

## Conferência depois de publicar

Abra qualquer versão com o inspetor do navegador na aba Rede e filtre por
`vkdigital`. O esperado:

```
sales_pixel.js?v=56     200
event_pageview.js       200
pixel.js?v=55           200
```

**Três requisições, uma de cada. Se alguma aparecer duas vezes, há instalação
duplicada em outro ponto**, provavelmente no tema do WordPress ou em uma tag
dentro do próprio GTM.

E no console, os três objetos precisam existir:

```js
window.vkPixel && window.vkPixelSales && window.vkPageViewPixel
```

## Um ponto para confirmar com a VK

Os dois blocos enviados iniciam **três** produtos com a mesma conta:
`vkPixelSales` (venda), `vkPageViewPixel` (page_view explícito) e `vkPixel`
(pixel geral).

Vale perguntar ao suporte da VK se o `pixel.js` já dispara `page_view` por conta
própria. Se disparar, o `event_pageview.js` estaria contando a mesma visita duas
vezes, e todo o cálculo de conversão do teste sairia pela metade do valor real.

Não dá para responder isso lendo o código: os arquivos são servidos pela VK e
mudam sem aviso. **A conferência é de trinta segundos:** publique, abra o
inspetor na aba Rede, filtre por `vkdigital` e veja se sai mais de uma chamada
de registro de visita. Se sair, remova o `event_pageview.js` do bloco em
`build/build.py`.

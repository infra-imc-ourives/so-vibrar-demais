# Desempenho · Só Vibrar

Trabalho feito sobre o relatório do PageSpeed de 4 de setembro de 2026, feito
na versão A em Moto G Power emulado com limitação de 4G lento.

## O relatório de partida

| Métrica | Valor | Situação |
|---|---|---|
| Nota de desempenho | 46 | vermelho |
| First Contentful Paint | 4,0 s | vermelho |
| Largest Contentful Paint | 4,7 s | vermelho |
| Total Blocking Time | 1.750 ms | vermelho |
| Speed Index | 4,5 s | laranja |
| Cumulative Layout Shift | 0 | verde |

## A primeira coisa a entender: metade do problema não é seu

Rodando o Lighthouse localmente, na mesma configuração de celular e 4G lento,
com uma diferença: nesta máquina o domínio `scripts.converteai.net` está
bloqueado, então **o player da Vturb não carrega**.

Resultado: **Total Blocking Time de 0 ms.**

O relatório de vocês mede 1.750 ms. A única diferença relevante entre os dois
ambientes é o player. Logo, praticamente todo o tempo de bloqueio da página vem
do script da Vturb, não do código da página.

Isso importa para calibrar expectativa: **enquanto a VSL for servida pela Vturb,
a nota não chega a 90 no PageSpeed.** Nenhuma otimização de HTML muda isso,
porque o custo está dentro de um script de terceiro que vocês não controlam.

O que dá para fazer, e foi feito, é tirar esse script do caminho crítico e
resolver por completo a parte que é sua.

## A parte que era sua: 98% do HTML eram imagens

Composição dos arquivos originais:

| Arquivo | imagens | base64 | HTML total | proporção |
|---|---|---|---|---|
| `a-vsl-pura.html` | 3 | 265 KB | 270 KB | **98%** |
| `b-escada-completa.html` | 14 | 583 KB | 624 KB | **93%** |
| `c-hibrida.html` | 3 | 265 KB | 272 KB | **98%** |
| `d-advertorial.html` | 2 | 91 KB | 99 KB | **93%** |

Detalhe da versão A, que é a que vocês mediram:

| # | Formato | Tamanho real | Em base64 | Onde |
|---|---|---|---|---|
| 1 | JPEG | 22 KB | 29 KB | fundo do topo, no CSS dentro do `<head>` |
| 2 | PNG | **130 KB** | 174 KB | logo do topo |
| 3 | PNG | 47 KB | 63 KB | logo do rodapé |

Três problemas somados nessa estrutura:

1. **Imagem em base64 não carrega em paralelo.** Ela vem dentro do HTML, então o
   navegador precisa baixar os 270 KB inteiros antes de pintar qualquer coisa.
2. **A do fundo estava no CSS, dentro do `<head>`.** Isso bloqueia a
   renderização: nada aparece na tela até o CSS terminar de chegar.
3. **Nada disso é cacheável entre as páginas.** O mesmo logo estava embutido
   nas quatro versões, e o navegador baixava tudo de novo a cada uma.

Somado a isso, as páginas pediam ao Google Fonts sete ou oito variações da
Montserrat e usavam de três a cinco. Cada variação é um arquivo separado.

## O que foi feito

Tudo isso vive em `build/otimizacao.py` e é aplicado pelo build. A copy não foi
tocada em nenhum ponto.

**1. Imagens fora do HTML.** As 22 ocorrências de base64 nas quatro páginas
viraram **9 arquivos** em `/assets/`, porque a mesma imagem aparecia repetida
entre versões e agora é uma só. Total: 264 KB, compartilhados e cacheados entre
as cinco páginas.

**2. Conversão para WebP.** Aplicada quando o arquivo fica ao menos 5% menor.
O logo de 130 KB em PNG é o caso mais evidente.

**3. `width` e `height` em cada `<img>`.** Enquanto tudo era base64, a imagem
existia no instante em que o HTML chegava e o layout nunca se mexia. Ao virar
arquivo externo, ela passa a chegar depois, e sem dimensão declarada o texto
salta quando ela aparece. O CLS continuou em 0 depois da mudança, o que confirma
que a proteção funcionou.

**4. Prioridade de carregamento.** A imagem do topo ganhou `preload` e
`fetchpriority="high"`, porque é pedida pelo CSS e o navegador só descobriria
que precisa dela tarde. As imagens abaixo da dobra ganharam `loading="lazy"`,
o que na versão B, com 13 imagens, é a maior parte delas.

**5. Pesos de fonte.** Cada página passou a pedir só o que usa:

| Versão | Antes | Depois |
|---|---|---|
| A | 7 variações | 3 (400, 700, 800) |
| B | 8 variações | 5 (400, 600, 700, 800, 900) |
| C | 7 variações | 3 (400, 800, 900) |
| D | 7 variações | 5 (400, 700, 800, 900 e itálico 400) |

**6. Player fora do caminho crítico.** O script da Vturb passa a ser pedido
quando o navegador está ocioso, depois da primeira pintura, com teto de 3
segundos. Se a pessoa tocar no vídeo antes disso, carrega na hora. **O vídeo
continua no mesmo lugar e ninguém precisa de um clique a mais para assistir.**

## Peso final do HTML

| Arquivo | Antes | Depois | Redução |
|---|---|---|---|
| `dist/a/index.html` | 270 KB | **11 KB** | 96% |
| `dist/b/index.html` | 624 KB | **46 KB** | 93% |
| `dist/c/index.html` | 272 KB | **11 KB** | 96% |
| `dist/d/index.html` | 99 KB | **12 KB** | 88% |

## Medição, antes e depois

Lighthouse 12, celular, 4G lento, mesma máquina, mesmo servidor local.

| Versão | | Nota | FCP | LCP | TBT | CLS |
|---|---|---|---|---|---|---|
| **A** | antes | 82 | 2,7 s | 2,8 s | 0 ms | 0 |
| | depois | **89** | **1,4 s** | **1,8 s** | 0 ms | 0 |
| **B** | antes | 65 | 4,5 s | 4,6 s | 0 ms | 0 |
| | depois | **88** | **1,7 s** | **2,3 s** | 0 ms | 0 |
| **C** | depois | 89 | 1,4 s | 1,8 s | 0 ms | 0 |
| **D** | depois | 90 | 1,4 s | 1,4 s | 0 ms | 0 |

Outras categorias, depois: acessibilidade 96 a 97, práticas recomendadas 96,
SEO 100 nas quatro.

### O que estes números não dizem

**Eles não são o que o PageSpeed de vocês vai mostrar, e é importante saber por
quê.** Nesta máquina, três recursos externos não carregam: o player da Vturb, o
Google Tag Manager e o Google Fonts. A medição isola o custo da própria página e
mede exatamente o que foi corrigido. Ela não mede o custo dos terceiros.

Traduzindo para expectativa honesta:

- **FCP e LCP devem melhorar de verdade**, e essa melhora é a que importa para
  conversão, porque é o tempo até a pessoa ver a página em vez de uma tela
  preta. A queda de 4,5 s para 1,7 s na versão B vem de retirar 578 KB do
  caminho crítico, e esse ganho não depende de terceiro nenhum. [Provável, alto]
- **O TBT deve cair, mas eu não consegui medir aqui**, porque o player não
  carrega nesta máquina. Adiar o script para o momento de ociosidade tira o
  custo de execução da janela crítica, e é a recomendação padrão do próprio
  Lighthouse para script de terceiro. Quanto isso vale em pontos, só o PageSpeed
  na URL publicada responde. [Chute fundamentado, precisa ser conferido]
- **A nota final ainda fica presa ao player.** Espere melhora clara, não 90.

**O próximo passo é de vocês:** publicar e rodar o PageSpeed na URL real. É a
única medição que vale, porque inclui servidor, CDN, latência e os terceiros.

## O que ficou fora, e por quê

**Trocar a Vturb.** É a única mudança capaz de levar a nota a 90. Também é a que
mexe em funil, retenção, disparo de eventos e relatório de audiência da VSL.
Decisão de negócio, não de código. Se a nota do PageSpeed for objetivo real e
não vaidade, essa é a conversa a ter.

**Servir a imagem do topo em tamanhos diferentes por tela.** O fundo do topo
tem 22 KB. O ganho seria de poucos KB e o custo é complicar o build. Não
compensa hoje.

**Reduzir o logo abaixo do WebP atual.** Ele é uma marca com degradê e brilho,
o que resiste a compressão. Um SVG resolveria de vez, mas exige o arquivo
vetorial original, que não está no repositório. Se a equipe de design tiver o
`.ai` ou `.svg`, vale pedir.

## Duas coisas que dependem do servidor, não do código

Nenhuma das duas é feita pelo build, e as duas valem pontos reais:

1. **Compactação (gzip ou brotli)** para HTML, CSS e JS. Os 46 KB da versão B
   viram cerca de 12 KB na rede. Os WebP já são comprimidos e não precisam.
2. **Cache longo para `/assets/`.** Os nomes dos arquivos carregam o conteúdo
   (`img-<código>.webp`), então `Cache-Control: public, max-age=31536000,
   immutable` é seguro: se a imagem mudar, o nome muda junto.

---

# Segunda rodada

Feita sobre os relatórios do PageSpeed de 4 de setembro nas URLs já publicadas.

## Ponto de partida real

| URL | Versão | Nota | Práticas recomendadas |
|---|---|---|---|
| `sovibrar1` | A · VSL pura | 66 | 96 |
| `sovibrar2` | B · escada completa | **43** | **73** |
| `sovibrar3` | C · híbrida | 67 | 96 |
| `sovibrar4` | D · advertorial | 71 | 96 |

A primeira rodada valeu 20 pontos na versão A, de 46 para 66. Mas a B ficou em
43, e ela é a única com "Práticas recomendadas" em 73 contra 96 das outras.
Diferença de 23 pontos numa categoria inteira, só nela. Isso aponta para algo
específico da B, não para um problema geral.

## O que a B tem que as outras não têm

**Três iframes do YouTube.** Cada player do YouTube carrega mais de um megabyte
de JavaScript, abre conexão com três domínios e grava cookies de terceiro. Os
cookies de terceiro são justamente o que a categoria "Práticas recomendadas"
penaliza. [Provável, alto]

Os iframes já tinham `loading="lazy"`, mas isso apenas adia: quando a pessoa
rola até os depoimentos, o megabyte chega inteiro.

**E 18.554 px de altura**, cerca de 21 telas de celular. Sem nenhuma instrução
em contrário, o navegador calcula o layout e a pintura das 21 telas antes de
mostrar a primeira.

## O que foi feito nesta rodada

### 1. Montserrat hospedada no próprio domínio, reduzida à copy

Esta é a maior mudança, e vale para as quatro versões.

O que existia antes:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:..." rel="stylesheet">
```

Três problemas nessa estrutura:

1. **O `<link rel="stylesheet"` bloqueia a renderização.** A página não pinta
   nada enquanto o Google não responde.
2. **São dois domínios novos**, cada um com DNS, TCP e TLS próprios antes do
   primeiro byte útil. Em 4G lento isso custa algumas centenas de milissegundos,
   duas vezes.
3. **A fonte vinha inteira.** O subconjunto latino da Montserrat tem cerca de
   380 glifos, cobrindo dezenas de idiomas europeus. A copy de vocês usa 171.

Agora a fonte é servida do próprio domínio, já reduzida aos caracteres que a
copy usa, e pré-carregada no primeiro instante:

| Arquivo | Tamanho |
|---|---|
| `montserrat-400.woff2` | 12,4 KB |
| `montserrat-600.woff2` | 12,6 KB |
| `montserrat-700.woff2` | 12,5 KB |
| `montserrat-800.woff2` | 12,5 KB |
| `montserrat-900.woff2` | 12,0 KB |
| `montserrat-400i.woff2` | 12,6 KB |

O subconjunto é calculado do texto das páginas mais uma margem com todo o
alfabeto acentuado do português, dígitos e pontuação, e é recalculado a cada
build. Se algum caractere da copy ficasse de fora, o build **não** aplica a
troca e mantém o Google Fonts, em vez de publicar uma página com letra faltando.

Os dois `preconnect` que serviam ao Google foram reaproveitados para os
terceiros que continuam existindo: `scripts.converteai.net` e
`www.googletagmanager.com`.

### 2. Depoimentos do YouTube só montam o player ao toque

Os três iframes viraram capas clicáveis. A página mostra a miniatura do vídeo,
que pesa poucos kilobytes, e monta o player quando a pessoa toca. **O vídeo abre
já tocando, então continua sendo um toque só.**

Isso tira mais de três megabytes de JavaScript do carregamento da B e elimina os
cookies de terceiro, que é o que derruba a categoria "Práticas recomendadas".

Cuidados incluídos: a capa responde a teclado (`Enter` e espaço), tem
`role="button"` e rótulo acessível, e se a miniatura não vier (bloqueador, rede),
ela some em vez de mostrar o ícone de imagem quebrada. O toque dispara
`sv_depoimento_play` no `dataLayer`, então dá para medir quantas pessoas de fato
assistem aos depoimentos.

### 3. Seções longe da dobra saem do layout inicial

Nove seções da B receberam `content-visibility:auto`. O navegador só calcula o
layout delas quando chegam perto da tela.

Isso só funciona bem com a altura de cada seção reservada. Com uma estimativa
única de 900 px, uma seção de 4.304 px faria a barra de rolagem saltar enquanto
a pessoa desce. Por isso as alturas reais são medidas e gravadas em
`build/alturas-secoes.json`:

```
B: [1126, 982, 1325, 1337, 1076, 2319, 1598, 4304, 1484, 633, 1749]
```

Medido depois: a altura total varia 6,7% durante a rolagem, com salto máximo de
144 px, menos de um sexto de tela. **Custo honesto: o CLS da B saiu de 0 para
0,042.** Continua dentro da faixa boa do Google, que é abaixo de 0,1, mas deixou
de ser zero. Se preferirem zero, `ADIAR_SECOES = False` no topo de
`build/build.py` desliga só isso.

O script `build/medir_secoes.py` refaz a medição quando a copy mudar a altura
das seções.

## Medição

Lighthouse 12, celular, 4G lento, mesma máquina e mesmo servidor local nas três
rodadas.

| Versão | | Nota | FCP | LCP | CLS |
|---|---|---|---|---|---|
| **A** | original | 82 | 2,7 s | 2,8 s | 0 |
| | rodada 1 | 89 | 1,4 s | 1,8 s | 0 |
| | rodada 2 | **100** | **0,8 s** | **1,7 s** | 0 |
| **B** | original | 65 | 4,5 s | 4,6 s | 0 |
| | rodada 1 | 88 | 1,7 s | 2,3 s | 0 |
| | rodada 2 | **99** | **1,4 s** | **2,1 s** | 0,04 |
| **C** | rodada 1 | 89 | 1,4 s | 1,8 s | 0 |
| | rodada 2 | **100** | **0,8 s** | **1,7 s** | 0 |
| **D** | rodada 1 | 90 | 1,4 s | 1,4 s | 0 |
| | rodada 2 | **100** | **1,1 s** | **1,5 s** | 0 |

Acessibilidade 96 a 98, práticas recomendadas 96, SEO 100 nas quatro.

**Estes 100 não são o que o PageSpeed vai mostrar.** Nesta máquina não carregam
o player da Vturb, o GTM, o YouTube nem o `i.ytimg.com`. A medição isola o custo
da própria página, e nesse recorte não há mais nada relevante a otimizar.

## Expectativa honesta para o PageSpeed real

| Versão | Hoje | O que muda | Expectativa |
|---|---|---|---|
| **B** | 43 | 3 MB de YouTube saem do carregamento, 9 seções saem do layout inicial, Google Fonts sai | maior salto absoluto das quatro |
| **C** | 67 | Google Fonts sai, duas conexões a menos | acima de 80 é provável |
| **D** | 71 | Google Fonts sai, duas conexões a menos | acima de 80 é provável |
| **A** | 66 | Google Fonts sai | o mais difícil dos quatro |

**A versão A é o caso mais difícil, e a razão é estrutural:** a página é o vídeo.
Tirando o player da Vturb, não sobra praticamente nada para otimizar, e o player
é justamente o que responde pelo tempo de bloqueio. A nota dela fica presa ao
que a Vturb entrega.

## As duas alavancas que sobram, as duas com custo

**1. Capa clicável também na VSL.** A mesma técnica dos depoimentos aplicada ao
vídeo principal: a página mostra uma imagem com botão de play e monta o player
da Vturb ao toque. Tecnicamente é a mudança que mais valeria pontos, e é a única
que colocaria a versão A com folga acima de 80.

O custo não é técnico, é de funil: se a VSL hoje começa sozinha, ela passaria a
exigir um toque. Em VSL isso costuma ser aceitável e, com som liberado pelo
gesto da pessoa, às vezes melhora a retenção. Mas é mudança de comportamento do
funil, não de código, e a decisão é de vocês.

**2. Trocar o player.** Resolve de vez e mexe em retenção, eventos e relatório
de audiência da VSL. Conversa maior.

## O que depende do servidor, não do código

A pasta `servidor/` traz os arquivos prontos, `.htaccess` para Apache e
LiteSpeed, e `nginx.conf` para Nginx. Os dois pontos que eles resolvem **não têm
como ser resolvidos dentro do HTML**:

- **Compressão.** Os 50 KB de HTML da versão B chegam ao celular com cerca de
  12 KB. Aparece direto no FCP em 4G.
- **Cache longo em `/assets/`.** Os nomes carregam o conteúdo, então é seguro.
  Sem ele, cada visita rebaixa imagens e fontes de novo.

Confira depois de aplicar:

```bash
curl -sI -H "Accept-Encoding: gzip, br" https://sovibrar1.elainneourives.com.br/ | grep -i content-encoding
```

Se não voltar nada, a hospedagem ignorou a configuração e vale abrir chamado.

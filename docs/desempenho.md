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

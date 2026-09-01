# Auditoria técnica · páginas Só Vibrar

Auditoria dos quatro arquivos entregues em `baseline/`, feita antes de qualquer
alteração. Cada achado abaixo foi verificado no arquivo, não presumido.

## 1. Corrigido pelo build

### 1.1 O teste não podia ser medido

**O achado.** As quatro versões apontavam para o mesmo link de checkout, sem um
único parâmetro que as diferenciasse:

```
a-vsl-pura.html         1x  https://pay.hub.la/hBZXUS60oESBNuUxf9pH
b-escada-completa.html  5x  https://pay.hub.la/hBZXUS60oESBNuUxf9pH
c-hibrida.html          2x  https://pay.hub.la/hBZXUS60oESBNuUxf9pH
d-advertorial.html      2x  https://pay.hub.la/hBZXUS60oESBNuUxf9pH
```

Nenhuma das páginas tinha pixel, GTM ou `dataLayer`. Ou seja: as vendas das
quatro versões chegariam à Hubla indistinguíveis, e não haveria como responder a
pergunta que motiva o teste.

**A correção.** O build injeta um script que, no carregamento:

- lê a query string com que a pessoa chegou (as UTMs e o `fbclid` do anúncio);
- acrescenta `sv_var` com a letra da versão;
- preenche `utm_content` com `variante-a`, `variante-b` e assim por diante,
  apenas quando o anúncio não mandou um `utm_content` próprio;
- preenche `utm_campaign` com `so-vibrar` quando o anúncio não mandou nenhum;
- reescreve todos os botões de checkout com essa query, mais `sv_cta` com a
  posição do botão na página.

Resultado verificado em navegador, chegando com
`?utm_source=meta&utm_medium=cpc&utm_campaign=teste-cadeados&fbclid=ABC123`:

```
https://pay.hub.la/hBZXUS60oESBNuUxf9pH?utm_source=meta&utm_medium=cpc
&utm_campaign=teste-cadeados&fbclid=ABC123&sv_var=b&utm_content=variante-b&sv_cta=3
```

O `sv_cta` responde de quebra qual botão da página longa realmente vende, que é
a informação que decide onde cortar e onde reforçar a versão B.

### 1.2 Sem tracking

**A correção.** GTM `GTM-PX6PZLNQ` no topo do `<head>` das cinco páginas
geradas, com o `noscript` logo após a abertura do `<body>`. Nenhum pixel foi
colado direto na página, para não duplicar disparo com o container global.

Eventos publicados no `dataLayer` para você criar os gatilhos dentro do GTM:

| Evento | Quando dispara | Variáveis |
|---|---|---|
| `sv_page_view` | carregamento da página | `sv_variante` |
| `sv_checkout_click` | clique em qualquer botão de checkout | `sv_variante`, `sv_cta`, `sv_cta_texto` |
| `sv_cta_revelado` | versão A, quando o botão aparece | `sv_motivo` |

### 1.3 Versão A revelava o botão na hora errada

**O achado.** O baseline terminava assim:

```js
var PITCH_SECONDS = 840;
setTimeout(function() {
  document.getElementById('cta-area').classList.add('show');
}, PITCH_SECONDS * 1000);
```

A contagem partia do carregamento da página, não do vídeo. Duas consequências,
as duas ruins:

- quem abrisse a página e não desse play recebia o botão aos 14 minutos do
  mesmo jeito, sem ter ouvido a oferta;
- quem desse play aos 6 minutos de página recebia o botão aos 14 minutos de
  página, ou seja, aos 8 minutos de vídeo, bem antes do pitch.

Em tráfego mobile, onde o autoplay é bloqueado por padrão e a pessoa precisa
tocar para começar, o segundo caso é o comportamento normal, não a exceção.

**A correção.** A revelação agora tem dois caminhos:

1. acompanha o relógio do próprio player quando ele expõe a API;
2. se o player não expuser, conta a partir da primeira interação da pessoa com
   a área do vídeo, nunca a partir do load.

**Ponto que exige confirmação:** a API do smartplayer da Vturb varia entre
versões, então o caminho 1 é tentado com verificação de tipo e o caminho 2
sustenta o comportamento se ele não existir. Vale confirmar com o time da Vturb
qual evento a conta de vocês expõe e ajustar `ligarNoPlayer` em
`build/build.py`. Enquanto isso o caminho 2 já entrega o comportamento correto.

### 1.4 Sem meta description e sem Open Graph

**O achado.** Só a versão B tinha `meta description`. Nenhuma das quatro tinha
Open Graph.

Isso importa mais do que parece nesse público: link do Instituto compartilhado
em grupo de WhatsApp sem Open Graph aparece como URL crua, sem capa e sem
título. O compartilhamento orgânico é tráfego de graça e estava sendo jogado
fora.

**A correção.** `description`, `og:*`, `twitter:*`, `canonical` e `theme-color`
por versão.

**Pendência que só você resolve:** a imagem de compartilhamento aponta para
`https://sovibrar.elainneourives.com.br/og-so-vibrar.jpg`, que **ainda não
existe**. Enquanto o arquivo não subir, o link compartilhado continua sem capa.
Formato: 1200x630 px, JPG, abaixo de 300 KB.

## 2. Não corrigido, por ser decisão sua

### 2.1 Peso das páginas

A versão B tem 627 KB de HTML porque todas as imagens estão em base64 dentro do
próprio arquivo, e parte delas dentro da tag `<style>` no `<head>`. Imagem em
base64 no CSS do head bloqueia a renderização: o navegador precisa baixar o
arquivo inteiro antes de pintar o primeiro pixel.

Extrair as imagens para `/assets` faria elas carregarem em paralelo, com cache
entre as quatro versões e sem bloquear o primeiro paint. O custo é perder a
propriedade de arquivo único autossuficiente, que é justamente o que torna a
publicação simples via FTP ou bloco HTML do WordPress.

Não mexi porque a decisão é de operação, não de código. Se a publicação for por
FTP em pasta própria, como recomenda o LEIA-ME original, extrair vale a pena e o
build faz isso em uma passada.

### 2.2 C e D mandam para o checkout sem falar de preço

Nem a versão C nem a D citam valor, parcelamento, bônus ou o que está incluso.
A pessoa clica em "Quero destravar minha vida" e cai direto no checkout da
Hubla, onde vê o preço pela primeira vez.

Na versão A isso é aceitável, porque a VSL faz o pitch inteiro antes do botão
aparecer. Em C e D não há nada fazendo esse trabalho.

O efeito previsível é que B ganhe o teste por um motivo que não é o formato: B é
a única versão que apresenta a oferta. O teste passa a comparar "página com
oferta" contra "página sem oferta", que é uma pergunta já respondida, em vez de
comparar formatos, que é a pergunta que interessa.

Se a intenção for testar formato, C e D precisam de um bloco de oferta antes do
CTA final. Não escrevi esse bloco porque copy nova precisa passar pela Jacky.

### 2.3 Oscilação de gênero na copy

A copy alterna entre feminino e masculino dentro da mesma peça:

| Trecho | Arquivo |
|---|---|
| "os 5 cadeados emocionais que mantêm você **presa** no mesmo lugar" | C |
| "quanto já te custou permanecer **travada**" | B |
| "é onde a maioria **das alunas** sente a primeira virada real" | B |
| "Episódio 02 · Você Realmente Está **Comprometido**" | B |
| "assumir o papel de **protagonista**" | B |

Se o público é majoritariamente feminino, e a escolha de "presa", "travada" e
"alunas" indica que sim, então a correção é padronizar tudo no feminino, não
alternar. A alternância dentro da mesma página quebra a sensação de que o texto
está falando com a leitora, que é exatamente o efeito que a peça depende.

Não corrigi porque isso é copy aprovada e a chamada é da Jacky.

## 3. Verificação executada

Teste em navegador (Chromium, viewport 390x844, chegando com UTMs de anúncio):

| Verificação | A | B | C | D |
|---|---|---|---|---|
| Erros de JavaScript | nenhum | nenhum | nenhum | nenhum |
| `gtm.js` no dataLayer | sim | sim | sim | sim |
| `sv_page_view` no dataLayer | sim | sim | sim | sim |
| Botões de checkout carimbados | 1/1 | 5/5 | 2/2 | 2/2 |
| CTA oculto no load | sim | n/a | n/a | n/a |
| CTA segue oculto logo após o play | sim | n/a | n/a | n/a |

Sintaxe de todos os blocos de script validada com `node --check`.

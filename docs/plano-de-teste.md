# Plano do teste · Só Vibrar

## A conclusão primeiro

**Quatro versões simultâneas provavelmente não fecham o teste.** Com quatro
variantes você precisa de mais que o dobro do tráfego que precisaria com duas, e
ainda assim tem mais chance de declarar vencedora uma versão que só teve sorte.

Recomendação: rodar **duas versões por vez, em duas rodadas**.

## Por que duas e não quatro

Dois efeitos se somam contra o teste de quatro braços.

**O tráfego se divide.** Cada versão recebe 25% em vez de 50%, então cada uma
demora o dobro para acumular o volume necessário.

**As comparações se multiplicam.** Com quatro versões você faz três comparações
contra o controle. Ao nível usual de 95% por comparação, a chance de pelo menos
um falso positivo sobe de 5% para cerca de 14%. Corrigir isso (Bonferroni, 95%
dividido por três comparações) exige mais amostra por versão, não menos.

Volume necessário por versão, poder de 80%:

| CVR base | uplift a detectar | 2 versões | 4 versões (corrigido) |
|---|---|---|---|
| 1,0% | 20% | 42.694 | 56.947 |
| 1,0% | 30% | 19.828 | 26.447 |
| 1,0% | 50% | 7.751 | 10.338 |
| 1,5% | 20% | 28.304 | 37.753 |
| 1,5% | 30% | 13.141 | 17.529 |
| 1,5% | 50% | 5.134 | 6.849 |
| 2,0% | 20% | 21.110 | 28.157 |
| 2,0% | 30% | 9.798 | 13.070 |
| 2,0% | 50% | 3.826 | 5.104 |

Em total de visitantes, assumindo CVR base de 1,5% e uplift de 30%:

- duas versões: **26.283 visitantes**
- quatro versões: **70.114 visitantes**

Você compra 2,7 vezes mais tráfego para responder a mesma pergunta.

**A premissa que precisa ser trocada por dado real:** a CVR base de 1,5% é
estimativa minha, não medição. Substitua pela conversão histórica de página de
venda de front-end do Instituto em tráfego frio da Meta e a tabela se recalcula
sozinha. Se a CVR real for muito diferente, o plano muda.

## O desenho recomendado

**Rodada 1: B contra D.**
Testa a hipótese que mais separa as peças: página de venda declarada contra
formato editorial. São os dois extremos de temperatura de tráfego frio, e é a
comparação de maior valor informativo.

**Rodada 2: a vencedora da rodada 1 contra A ou C.**
Testa o papel da VSL contra o texto, já sabendo qual abordagem de entrada
funciona.

Antes de rodar C ou D contra B, resolva o que está no item 2.2 da auditoria: C e
D não apresentam preço nenhum. Do jeito que estão, elas perdem para B por
ausência de oferta, não por formato, e o teste não responde nada.

## Como dividir o tráfego

**Use o teste A/B nativo do Gerenciador de Anúncios da Meta**, com uma URL por
variante. É a opção correta aqui.

Não use redirecionamento por JavaScript na raiz do domínio. Um splitter em JS
custa um salto extra antes do primeiro paint, atrasa a página em tráfego mobile
e embaralha a atribuição, porque a Meta registra a visita na URL de entrada e a
pessoa termina em outra.

Enquanto o teste roda, a raiz (`sovibrar.elainneourives.com.br/`) serve a
variante B, conforme definido em `VARIANTE_RAIZ` no build. Ela existe para
tráfego direto, orgânico e compartilhamento, não para o teste.

## O que medir

O carimbo de variante já chega no checkout, então a leitura pode ser feita
direto na Hubla pelo parâmetro `sv_var`, sem depender do GTM.

Métrica de decisão, nessa ordem:

1. **Venda por visitante** (`sv_var` na Hubla dividido por `sv_page_view` no
   GTM). É a única métrica que decide.
2. **Clique no checkout por visitante** (`sv_checkout_click` / `sv_page_view`).
   Diagnóstico: separa problema de página de problema de checkout.
3. **Checkout para venda.** Se cair muito em uma versão específica, o problema é
   descompasso entre a promessa da página e o que aparece no checkout. É
   exatamente o que se espera de C e D no estado atual.
4. **Qual botão vende** (`sv_cta`). Só na versão B, que tem cinco. Diz onde
   cortar e onde reforçar.

## Regras de decisão, definidas antes de começar

Combine estas três regras agora, antes de ver qualquer número. Definir critério
depois de olhar o resultado é como o teste vira justificativa da opinião de
quem olha primeiro.

1. **Não olhar antes do volume.** Espiar o resultado todo dia e parar quando
   fica bonito infla o falso positivo muito acima dos 5% nominais. Defina o
   volume pela tabela e só leia no fim.
2. **Ciclos inteiros de sete dias.** Terça converte diferente de domingo.
   Parar na quinta-feira mede o dia da semana, não a página.
3. **Empate é resultado.** Se a diferença não passar o corte, fique com a mais
   simples de manter. Empate não é convite para rodar mais uma semana até o
   número virar.

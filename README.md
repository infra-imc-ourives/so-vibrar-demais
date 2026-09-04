# Só Vibrar · páginas de venda

Páginas de venda do **Só Vibrar** (Instituto Elainne Ourives) em quatro versões,
para teste de conversão no domínio `sovibrar.elainneourives.com.br`.

Checkout: `https://pay.hub.la/hBZXUS60oESBNuUxf9pH`
Container GTM: `GTM-PX6PZLNQ`

---

## Estrutura

| Pasta | O que é |
|---|---|
| `baseline/` | Os quatro HTML exatamente como foram aprovados. **Nunca editar direto.** |
| `build/build.py` | Aplica as correções técnicas sobre o baseline. Não toca em copy. |
| `build/otimizacao.py` | Otimizações de carregamento usadas pelo build. |
| `dist/` | O que vai para o servidor. Gerado pelo build, versionado para conferência. |
| `dist/assets/` | Imagens extraídas do HTML. **Sobe junto, na raiz do domínio.** |
| `docs/` | Plano do teste, auditoria técnica e instruções de publicação. |

## As quatro versões

| Versão | Formato | CTAs | Preço na página |
|---|---|---|---|
| **A** | VSL pura, botão revelado no pitch | 1 | não |
| **B** | Página longa completa, escada de valor e bônus | 5 | sim |
| **C** | Híbrida, VSL com prova social curta | 2 | não |
| **D** | Advertorial em formato editorial | 2 | não |

## Como gerar as páginas

```bash
python3 build/build.py
```

Lê `baseline/`, escreve `dist/`. Usa Pillow para converter imagens e ler
dimensões (`pip install pillow`). Sem Pillow o build roda igual, só que as
imagens saem no formato original e sem `width`/`height`.

O que o build aplica em cada arquivo:

**Correção**

1. **GTM** `GTM-PX6PZLNQ` no topo do `<head>` e o `noscript` logo após o `<body>`.
2. **Meta description, Open Graph e Twitter Card** por versão, mais `canonical`.
3. **Atribuição de variante:** um script que repassa ao checkout as UTMs que
   vieram do anúncio e carimba `sv_var`, `utm_content` e `sv_cta` em todos os
   botões. Dispara `sv_page_view` e `sv_checkout_click` no `dataLayer`.
4. **Versão A:** substitui a revelação do botão por uma que conta o tempo do
   vídeo, não o tempo de página.

**Desempenho** (detalhado em `docs/desempenho.md`)

5. **Imagens fora do HTML.** Eram base64 e representavam 98% do peso da versão
   A. Saem para `/assets/`, viram WebP e são reaproveitadas entre as páginas.
6. **`width`, `height`, `fetchpriority` e `loading`** em cada `<img>`, mais
   `preload` da imagem do topo.
7. **Pesos de fonte** reduzidos aos que cada página usa. Pediam sete ou oito,
   usam de três a cinco.
8. **Player da VSL** pedido fora do caminho crítico, sem mudar onde o vídeo
   aparece nem exigir clique a mais.

As três otimizações têm interruptor no topo de `build/build.py`:
`EXTRAIR_IMAGENS`, `ADIAR_PLAYER` e `AJUSTAR_FONTES`.

## Antes de mexer

Qualquer alteração de copy entra em `baseline/` e depois roda o build. Editar
`dist/` direto faz a mudança sumir na próxima geração.

O único valor que precisa de confirmação humana antes de liberar tráfego é
`PITCH_SECONDS` em `build/build.py`, hoje em `840` (14min00s). É o segundo da
VSL em que a Elainne inicia a oferta.

## Leia antes de publicar

- `docs/auditoria-tecnica.md`: o que estava quebrado, o que foi corrigido e o
  que segue em aberto.
- `docs/plano-de-teste.md`: quanto tráfego o teste exige e por que quatro
  versões simultâneas provavelmente não fecham.
- `docs/publicacao.md`: passo a passo do deploy e checklist de liberação.
- `docs/desempenho.md`: o que estava pesando, o que foi feito e os números
  antes e depois.

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
| `dist/` | O que vai para o servidor. Gerado pelo build, versionado para conferência. |
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

Sem dependências. Lê `baseline/`, escreve `dist/`.

O que o build aplica em cada arquivo:

1. **GTM** `GTM-PX6PZLNQ` no topo do `<head>` e o `noscript` logo após o `<body>`.
2. **Meta description, Open Graph e Twitter Card** por versão, mais `canonical`.
3. **Atribuição de variante:** um script que repassa ao checkout as UTMs que
   vieram do anúncio e carimba `sv_var`, `utm_content` e `sv_cta` em todos os
   botões. Dispara `sv_page_view` e `sv_checkout_click` no `dataLayer`.
4. **Versão A:** substitui a revelação do botão por uma que conta o tempo do
   vídeo, não o tempo de página.

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

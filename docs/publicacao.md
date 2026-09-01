# Publicação · Só Vibrar

Substitui o `LEIA-ME_instrucoes_publicacao.txt` original, que fica preservado
nesta pasta como registro do que foi entregue.

Domínio: `sovibrar.elainneourives.com.br`

## O que subir

Suba o conteúdo de `dist/`, não o de `baseline/`. Os arquivos em `baseline/`
são os originais aprovados, sem GTM e sem carimbo de variante.

| Arquivo local | Caminho no servidor | URL |
|---|---|---|
| `dist/index.html` | `/index.html` | `sovibrar.elainneourives.com.br/` |
| `dist/a/index.html` | `/a/index.html` | `.../a/` |
| `dist/b/index.html` | `/b/index.html` | `.../b/` |
| `dist/c/index.html` | `/c/index.html` | `.../c/` |
| `dist/d/index.html` | `/d/index.html` | `.../d/` |

A raiz é uma cópia da variante B, até o teste apontar a vencedora. Para trocar,
altere `VARIANTE_RAIZ` em `build/build.py` e rode o build de novo.

Cada arquivo continua autossuficiente: CSS, imagens em base64 e scripts estão
dentro dele. Não há pasta de imagens para subir junto.

## Como publicar

**Recomendado: FTP ou gerenciador de arquivos**, cada arquivo em sua pasta,
renomeado para `index.html`. É o caminho mais direto e o único que preserva o
arquivo exatamente como foi gerado e testado.

**Alternativa no WordPress:** página em branco com template sem cabeçalho e
rodapé (canvas ou blank) e o conteúdo colado em bloco HTML personalizado.
Nessa opção é preciso remover `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>` e
`</html>`, e mover o conteúdo de `<style>` para o CSS adicional do tema.

Atenção nessa alternativa: ao remover o `<head>` você remove também o GTM e as
tags Open Graph. O GTM precisa ser garantido pelo container global do tema, e o
Open Graph pelo plugin de SEO, página por página. Se nenhum dos dois estiver
resolvido, o FTP é o caminho.

## Antes de liberar tráfego

- [ ] `PITCH_SECONDS` confirmado com a Jacky e o build rodado de novo.
      Hoje está em `840` (14min00s), valor herdado do arquivo original.
- [ ] `og-so-vibrar.jpg` (1200x630 px, JPG, abaixo de 300 KB) enviado para a
      raiz do domínio. Sem ele, o link compartilhado aparece sem capa.
- [ ] As cinco URLs abrindo com HTTPS válido.
- [ ] VSL carregando e reproduzindo em `/a/`, `/b/` e `/c/`.
- [ ] GTM disparando nas cinco URLs, verificado no modo de visualização do
      Tag Manager (container `GTM-PX6PZLNQ`).
- [ ] Pixel da Meta disparando, configurado **por dentro do GTM**, nunca colado
      direto na página, para não duplicar evento com o container global.
- [ ] Clique em um botão de cada versão levando ao checkout **com o `sv_var`
      correto na URL**. Este item é o que torna o teste legível: se o parâmetro
      não chegar, não suba tráfego.
- [ ] Teste em celular real, não só no emulador do navegador. A maioria do
      tráfego é mobile.
- [ ] Na versão A, confirmar que o botão não aparece antes do pitch. Dê play,
      pule para perto de `PITCH_SECONDS` e verifique.

## Checagem rápida do carimbo de variante

Abra qualquer versão acrescentando parâmetros de teste na URL:

```
https://sovibrar.elainneourives.com.br/d/?utm_source=meta&utm_medium=cpc&fbclid=TESTE
```

Passe o mouse sobre o botão e confira que o destino traz `sv_var=d`,
`utm_content=variante-d`, `sv_cta=1` e as UTMs originais preservadas.

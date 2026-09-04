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
| `dist/assets/` (pasta inteira) | `/assets/` | `.../assets/` |
| `servidor/.htaccess` (Apache/LiteSpeed) | `/.htaccess` | não é URL |

A raiz é uma cópia da variante B, até o teste apontar a vencedora. Para trocar,
altere `VARIANTE_RAIZ` em `build/build.py` e rode o build de novo.

## Mudou: agora existe uma pasta de imagens

Até a otimização de desempenho, cada HTML era autossuficiente, com as imagens
em base64 dentro dele. **Isso mudou.** As imagens saíram do HTML e vivem em
`dist/assets/`, e é por isso que a versão A caiu de 270 KB para 11 KB.

Consequências práticas:

- **A pasta `assets/` precisa subir junto, na raiz do domínio**, não dentro de
  `/a/` ou `/b/`. Os caminhos no HTML são absolutos (`/assets/img-....webp`),
  então uma única pasta serve as cinco páginas e o navegador reaproveita o
  cache entre elas.
- Se você subir só os HTML e esquecer a pasta, **as páginas abrem sem nenhuma
  imagem**. Logo, fundo, mockups, tudo. Suba `assets/` primeiro.
- Os nomes dos arquivos têm o conteúdo embutido (`img-<código>.webp`). Trocar
  uma imagem gera um nome novo, então não existe problema de cache antigo.

## Como publicar

**Recomendado: FTP ou gerenciador de arquivos**, cada arquivo em sua pasta,
renomeado para `index.html`. É o caminho mais direto e o único que preserva o
arquivo exatamente como foi gerado e testado.

**Alternativa no WordPress:** página em branco com template sem cabeçalho e
rodapé (canvas ou blank) e o conteúdo colado em bloco HTML personalizado.
Nessa opção é preciso remover `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>` e
`</html>`, e mover o conteúdo de `<style>` para o CSS adicional do tema.

Atenção nessa alternativa: ao remover o `<head>` você remove também o GTM, as
tags Open Graph e o `preload` da imagem do topo. O GTM precisa ser garantido
pelo container global do tema, e o Open Graph pelo plugin de SEO, página por
página. Se nenhum dos dois estiver resolvido, o FTP é o caminho.

E a pasta `assets/` continua sendo obrigatória nessa alternativa também.

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
- [ ] Pasta `assets/` no ar. Abra `sovibrar.elainneourives.com.br/assets/` e
      confirme que o servidor entrega os arquivos. Sem ela, as páginas ficam
      sem imagem nenhuma.
- [ ] Configuração do servidor aplicada. Use `servidor/.htaccess` (Apache,
      LiteSpeed, cPanel) ou `servidor/nginx.conf`. Confira depois com
      `curl -sI -H "Accept-Encoding: gzip, br" <url> | grep -i content-encoding`.
- [ ] Fontes servindo de `/assets/fonts/`. Abra uma página e confirme no
      inspetor que a Montserrat carrega do seu domínio, não do Google.
- [ ] Na versão B, tocar em um depoimento abre o vídeo já tocando.
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

# Publicação · Só Vibrar

Substitui o `LEIA-ME_instrucoes_publicacao.txt` original, que fica preservado
nesta pasta como registro do que foi entregue.

Domínio: `sovibrar.elainneourives.com.br`

## O que subir

**Cada pasta em `dist/` é autossuficiente.** Ela leva o `index.html` e a sua
própria pasta `assets`, com as imagens e as fontes daquela página. Nada é
buscado de fora da pasta.

Vocês publicaram em quatro subdomínios. O mapeamento:

| Pasta local | Versão | Vai para a raiz de |
|---|---|---|
| `dist/a/` | A · VSL pura | `sovibrar1.elainneourives.com.br` |
| `dist/b/` | B · escada completa | `sovibrar2.elainneourives.com.br` |
| `dist/c/` | C · híbrida | `sovibrar3.elainneourives.com.br` |
| `dist/d/` | D · advertorial | `sovibrar4.elainneourives.com.br` |
| `dist/raiz/` | cópia da B | domínio principal, quando existir |

Suba **o conteúdo** de cada pasta, não a pasta em si. No subdomínio 1 deve
ficar assim:

```
sovibrar1.elainneourives.com.br/
├── index.html
└── assets/
    ├── img-4fdf662fd6e2.webp
    ├── img-5f062199f58b.webp
    └── fonts/
        ├── montserrat-400.woff2
        ├── montserrat-700.woff2
        └── montserrat-800.woff2
```

A regra que evita o problema: **`assets` sempre ao lado do `index.html`**, nunca
um nível acima, nunca em outro subdomínio.

## Por que os caminhos são relativos

Até a correção de setembro, o HTML pedia `/assets/img-....webp`, com barra na
frente. Barra na frente significa "a partir da raiz do domínio", e isso só
funciona quando a página está exatamente na raiz e a pasta `assets` também.

Publicando em quatro subdomínios, cada um precisaria da sua própria `/assets/`
na raiz. Qualquer desencontro deixava a página sem imagem nenhuma, e sem fonte
também, já que as fontes vivem em `assets/fonts/`.

Agora o HTML pede `assets/img-....webp`, sem barra. Isso significa "ao lado do
arquivo", e funciona em qualquer arranjo:

| Arranjo | Funciona |
|---|---|
| Pasta na raiz de um subdomínio | sim |
| Páginas em subpasta de um domínio único (`/a/`, `/b/`) | sim |
| Arquivo aberto direto do disco, com duplo clique | sim |

Os três casos foram testados em navegador antes de publicar esta versão.

## Faixa de urgência no topo

As quatro páginas trazem a faixa vermelha com "Assista antes que saia do ar"
como primeiro elemento visível. Ela tem altura fixa declarada em CSS, então não
empurra o conteúdo depois que a página já pintou.

O vermelho é `#E3161F`, não o vermelho puro. Contra branco, `#FF0000` dá
contraste de 4,00 e reprova no mínimo de 4,5 exigido para texto; `#E3161F` dá
4,77 e passa. A diferença visual entre os dois é imperceptível, e a nota de
acessibilidade continua onde estava.

Para tirar a faixa de uma versão, mude a linha correspondente em
`build/build.py` e rode o build:

```python
FAIXA_TOPO = {"a": True, "b": True, "c": True, "d": False}
```

Para mudar o texto, altere `FAIXA_TEXTO` no mesmo arquivo.

## Se uma imagem não aparecer

A página passou a esconder imagem que não carrega, em vez de mostrar o ícone de
imagem quebrada. **Mas ela avisa no console**, para o problema não virar
silêncio. Abra o inspetor, aba Console, e procure:

```
[Só Vibrar] imagem não carregou: assets/img-....webp
```

Se aparecer, a pasta `assets` não subiu junto ou não está ao lado do
`index.html`. Confirme abrindo o arquivo direto no navegador:

```
https://sovibrar1.elainneourives.com.br/assets/img-4fdf662fd6e2.webp
```

- **Abre a imagem:** o arquivo está lá, e o problema é outro.
- **404:** a pasta não subiu, ou subiu no lugar errado.
- **Baixa em vez de mostrar:** o servidor não conhece WebP. Aplique o
  `servidor/.htaccess`, que declara o tipo.

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
- [ ] VK Digital disparando. Inspetor, aba Rede, filtro `vkdigital`: devem
      aparecer **três** requisições, uma de cada arquivo. Se alguma repetir, há
      instalação duplicada em outro ponto. Ver `docs/tracking.md`.
- [ ] Clique em um botão de cada versão levando ao checkout **com o `sv_var`
      correto na URL**. Este item é o que torna o teste legível: se o parâmetro
      não chegar, não suba tráfego.
- [ ] Pasta `assets/` ao lado do `index.html` em **cada** subdomínio. Abra uma
      imagem direto pela URL para confirmar. Sem ela, a página fica sem imagem
      e sem a fonte Montserrat.
- [ ] Console do navegador sem nenhuma linha `[Só Vibrar] imagem não carregou`.
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

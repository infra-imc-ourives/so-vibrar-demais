# Configuração do servidor

Dois arquivos, escolha o que corresponde à hospedagem:

| Arquivo | Quando usar |
|---|---|
| `.htaccess` | Apache, LiteSpeed, hospedagem com cPanel. Sobe para a raiz do domínio. |
| `nginx.conf` | Nginx. O conteúdo é colado dentro do bloco `server` do domínio. |

## Por que isso importa

Os dois pontos que estes arquivos resolvem, compressão e cache, **não têm como
ser resolvidos dentro do HTML**. São instruções que o servidor dá ao navegador.

- **Compressão:** a versão B tem cerca de 50 KB de HTML. Comprimida, chega ao
  celular com aproximadamente 12 KB. É uma diferença que aparece direto no
  First Contentful Paint em 4G.
- **Cache:** sem ele, quem volta à página baixa as imagens e as fontes de novo.
  Com ele, a segunda visita e a navegação entre as versões do teste custam
  quase nada de rede.

## Uma conferência que vale fazer

Depois de aplicar, confirme que a compressão está mesmo ativa:

```bash
curl -sI -H "Accept-Encoding: gzip, br" https://sovibrar1.elainneourives.com.br/ | grep -i content-encoding
```

Se a resposta trouxer `content-encoding: br` ou `gzip`, está funcionando. Se não
trouxer nada, a hospedagem ignorou a configuração e vale abrir chamado com o
suporte, porque o ganho é real e não custa nada.

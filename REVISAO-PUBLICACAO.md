# Revisão de publicação — 16/11/2026

Arquitetura preservada: Python, Flask, SQLAlchemy, templates Jinja, HTML/CSS/JavaScript e SQLite. Os blueprints e modelos de clientes, ordens, itens e usuários foram mantidos.

## Verificações executadas

- Ambiente virtual novo com Python 3.13; instalação de `requirements.txt` concluída. As versões completas foram registradas em `requirements.lock.txt`.
- `python -m pip check` — nenhuma dependência incompatível.
- `python -m unittest discover -s tests -v` — **13 testes aprovados** no ambiente novo.
- `node --check static/app.js` e `node --check static/security.js` — sem erro de sintaxe.
- Navegador: login, cadastro de cliente sem placa/telefone, busca de cliente, criação de OS com item e PIX, histórico, edição do valor de R$ 45,50 para R$ 60,00 e atualização do faturamento — conferidos com dados fictícios em banco separado.
- Após a correção do script compartilhado, as telas de histórico/edição/faturamento foram verificadas sem novos erros JavaScript.

Os testes cobrem bloqueio anônimo em páginas/APIs/PDFs, CSRF, login incorreto, primeiro usuário pela CLI, cadastro autenticado, logout, favicon sem invalidar a sessão, renderização das telas, clientes sem campos opcionais, duplicatas, normalização, busca/edição/exclusão, ordens com totais, pendência/cancelamento fora da receita, rejeição de entradas inválidas sem destruir itens anteriores, filtros, PDF com nome de cliente contendo barra e persistência após reinicialização.

## Correções

1. APIs e páginas operacionais agora exigem sessão autenticada.
2. Chave de sessão fixa substituída por segredo local aleatório ou variável de ambiente; debug desativado e servidor limitado ao loopback.
3. Primeiro usuário pode ser criado por CLI sem senha padrão; senhas curtas/vazias de novos cadastros são rejeitadas.
4. Formulários e chamadas JSON protegidos por token CSRF; logout por POST.
5. Campos únicos opcionais vazios são armazenados como NULL, permitindo mais de um cliente sem telefone/placa.
6. Itens, números finitos, quantidades, valores, status e datas são validados antes de alterar a OS. Filtros inválidos retornam erro tratado.
7. Faturamento do mês não inclui meses futuros; somente OS finalizadas contam na receita.
8. PDF usa nome baseado no ID, sem incorporar o nome do cliente ao caminho; arquivos gerados ficam na pasta local de dados.
9. Textos dinâmicos das listagens são escapados. A busca usa elementos DOM e só inicializa onde seus campos existem; uma seleção anterior é descartada ao alterar a busca.
10. Requisição de recurso inexistente (favicon) não limpa o token do formulário de login.

## Limites

Validação realizada com SQLite em Windows e Python 3.13. MySQL não foi executado; a consulta mensal preservada usa `strftime`, específico do SQLite. O servidor Flask fornecido atende ao uso local; hospedagem pública exige configuração própria de produção. Há avisos de APIs legadas de SQLAlchemy, datetime e fpdf2 que não impediram a execução. Nenhum banco ou recibo real foi enviado ao repositório. O banco original permanece no diretório de origem, sem migração automática.

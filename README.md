# Conecta Comunidade

Protótipo acadêmico de gerenciamento de campanhas e inscrições em ações sociais. Disciplina **Projetos e Práticas de Extensão IV**, Unidade 4.

## Funcionalidades implementadas
- Cadastrar e listar campanhas com descrição, data, local e limite de vagas.
- Registrar voluntários e realizar inscrições, evitando duplicidades.
- Exibir indicadores de campanhas, voluntários e inscrições.
- Interface responsiva, consumindo API REST simples.

## Tecnologias
Python 3.10+ (bibliotecas padrão `http.server` e `sqlite3`), SQLite, HTML, CSS e JavaScript. **Sem dependências externas**.

## Como executar
1. Instale o Python 3.10 ou superior.
2. Clone este repositório: `git clone URL_DO_SEU_REPOSITORIO`.
3. Entre na pasta: `cd conecta-comunidade`.
4. Execute: `python app.py` (no Windows também pode ser `py app.py`).
5. Acesse http://localhost:8000.

O arquivo `conecta.db` é gerado automaticamente na primeira execução.

## Endpoints
- `GET /api/campanhas` — lista campanhas e número de inscrições.
- `GET /api/indicadores` — totais do sistema.
- `POST /api/campanhas` — cria campanha; campos `titulo`, `descricao`, `local`, `data` (AAAA-MM-DD), `vagas`.
- `POST /api/inscricoes` — cadastra voluntário e inscrição; campos `campanha_id`, `nome`, `email`.

## Estrutura de dados
`campanhas (id, titulo, descricao, local, data, vagas)`; `voluntarios (id, nome, email UNIQUE)`; `inscricoes (id, campanha_id FK, voluntario_id FK, UNIQUE(campanha_id, voluntario_id))`.

## Limitações / segurança
**Este é um protótipo para execução local, não uma aplicação de produção.** Não tem autenticação, autorização, proteção contra abuso ou HTTPS próprios; qualquer pessoa com acesso ao servidor pode cadastrar campanhas. Evite cadastrar dados reais de terceiros. Para publicar na internet, implemente autenticação, proteção de dados pessoais, logs, backups e hospedagem segura.

## GitHub
Crie um repositório novo, faça o commit dos arquivos e compartilhe o link com a professora. Não inclua `conecta.db` no repositório. Veja `DOCUMENTACAO.md`.

## Testes automatizados
Execute `python -m unittest discover -s tests -v`. São 6 testes de integração HTTP; consulte `RESULTADOS_TESTES.txt`.

## Entrega acadêmica
Veja `GUIA_ENTREGA_PROFESSORA.md` e `Documentacao_Final_Conecta_Comunidade_PRONTA.docx`.

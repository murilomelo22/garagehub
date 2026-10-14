# GarageHub · V0.1

Rede social automotiva com garagem digital, acompanhamento de evolução e personalização de um carro genérico em 3D. Nome provisório. Interface em português, tema escuro com acento azul escuro, fundo `#101114` e assinatura de cultura de garagem e navegação adaptada ao celular.

## Rodar localmente

Requisitos: **Python 3.10+**, `pip`, navegador moderno. Não é necessário Node.js, Docker ou banco externo. Three.js, OrbitControls e Chart.js são carregados por HTTPS de `cdn.jsdelivr.net`; o 3D também requer WebGL habilitado no navegador.

```bash
git clone https://github.com/murilomelo22/garagehub.git
cd garagehub
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Prompt de Comando)
.venv\Scripts\activate.bat
```

Instale e inicie:

```bash
python -m pip install -r requirements.txt
python run.py
```

No seu computador, abra `http://127.0.0.1:5000`. Encerre com `Ctrl+C`. O banco SQLite e as tabelas são criados automaticamente na primeira execução. O servidor inicia sem debug e escuta apenas a máquina local. Para desenvolvimento com recarga automática, use `python -m flask --app run run --debug`.

Esse endereço funciona na máquina que executa o servidor. Em um ambiente remoto, ele não abre a aplicação no seu computador. Para acessar de outros dispositivos, publique o site usando as instruções abaixo.

## Acessar pela internet

A prévia em **GitHub Pages** permite navegar pelo GarageHub com dados de exemplo. A aplicação completa pode ser hospedada com **Gunicorn**, HTTPS e um disco persistente para SQLite e uploads.

### Prévia no GitHub Pages

1. Abra [Settings → Pages do repositório](https://github.com/murilomelo22/garagehub/settings/pages).
2. Em **Build and deployment → Source**, selecione **Deploy from a branch**.
3. Escolha a branch **main**, a pasta **/docs** e clique em **Save**.
4. Aguarde a publicação do GitHub e abra [GarageHub](https://murilomelo22.github.io/garagehub/).

O endereço fica disponível após a ativação. A pasta `docs/` contém 18 páginas, incluindo a demonstração e o modelo para carros criados no navegador. Clique em **Entrar como visitante** para usar o perfil de `lucas_gti`. Os botões Adicionar veículo, Editar carro, Registrar evolução e Novo projeto abrem formulários acessíveis, com salvamento local.

A prévia usa `localStorage` na chave `garagehub:preview:v0.1`. Carros, medições, modificações, perfil de exemplo, posts com foto, curtidas, comentários, seguidores e configurações 3D sobrevivem à recarga no mesmo navegador. Não há autenticação real no Pages. Os dados não são enviados ao Flask, não são sincronizados entre dispositivos e deixam de existir se o armazenamento do site for apagado. As fotos são reduzidas a até 1200 px e 800 KB codificados; se faltar espaço, a interface informa a falha e mantém os dados anteriores.

Os modais suportam teclado, Escape e devolução de foco. Os textos criados pelo visitante são escapados antes de entrar no HTML. A exportação usa somente registros fictícios; não publica e-mails, hashes de senha, sessões ou fotos reais.

Para atualizar a prévia depois de alterar a interface, execute e publique a pasta gerada:

```bash
python scripts/build_pages.py
```

A exportação usa um banco temporário e **não lê nem publica o banco real, sessões ou uploads de usuários**. Somente ilustrações e registros de demonstração entram na prévia.

### Publicar no Render

Para disponibilizar a aplicação completa, siga estes passos. Nenhuma conta de demonstração é criada automaticamente na hospedagem: use **Começar minha garagem** para cadastrar sua conta.

1. Entre no [painel do Render](https://dashboard.render.com/) e conecte sua conta do GitHub.
2. Selecione **New → Blueprint**, escolha o repositório `murilomelo22/garagehub` e a branch que contém `render.yaml`, `Dockerfile` e o código da aplicação.
3. Confira o serviço e o disco e confirme a instalação. O plano `starter` com disco persistente **é pago**; o Render mostra o custo antes de confirmar. O plano gratuito sem disco não preserva contas e fotos entre recriações do serviço.
4. Aguarde o serviço ficar **Live** e abra a URL HTTPS fornecida pelo Render. Esse será o endereço para acessar pelo computador ou celular.

O arquivo `render.yaml` gera `SECRET_KEY`, configura o proxy HTTPS, conecta um disco de 1 GB em `/var/data` e verifica `/health`. Banco e fotos ficam em `/var/data/garagehub`. Não substitua o segredo em cada publicação: ele mantém as sessões válidas. Faça backups do diretório de dados. Esta configuração atende a uma única instância; para múltiplas instâncias, migre o banco e os uploads para serviços externos.

### Outra hospedagem com Python ou Docker

Os nomes das variáveis estão em `.env.example`; configure-as diretamente no painel da hospedagem. Defina `GARAGEHUB_ENV=production`, uma `SECRET_KEY` aleatória com pelo menos 32 caracteres e `GARAGEHUB_DATA_DIR` apontando para um volume persistente. A aplicação não carrega `.env` automaticamente.

Sem Docker, instale `requirements-production.txt` e use este comando de inicialização:

```bash
gunicorn --config gunicorn.conf.py run:app
```

O servidor escuta `0.0.0.0` na porta indicada por `PORT` (padrão: `10000`). A hospedagem deve oferecer HTTPS. Ative `GARAGEHUB_TRUST_PROXY=1` apenas quando ela fornece um proxy confiável que substitui os cabeçalhos `X-Forwarded-*`; mantenha a porta do Gunicorn protegida de conexões diretas.

Para executar a imagem Docker no seu computador, gere a chave no próprio terminal e mantenha o volume entre reinícios:

```bash
docker build -t garagehub .
docker volume create garagehub-data
docker run --rm -p 10000:10000 \
  --mount source=garagehub-data,target=/var/data \
  -e SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')" \
  -e GARAGEHUB_ENV=development \
  garagehub
```

Abra `http://localhost:10000`. O exemplo usa cookies HTTP para a execução local; em produção mantenha `GARAGEHUB_ENV=production` e HTTPS. Gere e armazene um segredo fixo na hospedagem, em vez de usar o exemplo de chave nova a cada execução.

Se a porta estiver ocupada, use `PORT=5001 python run.py` no Linux/macOS ou defina `$env:PORT="5001"` antes de `python run.py` no PowerShell. Também é possível usar `python -m flask --app run run --port 5001`.

### Dados de exemplo (opcional)

Com o ambiente virtual ativo:

```bash
python seed.py
# Alternativa equivalente:
python -m flask --app run seed
```

Cria **3 usuários e 9 carros**, fotos ilustrativas geradas localmente, medições, modificações, relações sociais e posts. Pode ser executado novamente sem duplicar os mesmos exemplos. Preserva os registros existentes. As medições reconhecidas como os números repetidos do seed antigo são corrigidas; históricos personalizados são preservados.

| Usuário | E-mail | Cidade | Carros |
| --- | --- | --- | --- |
| `lucas_gti` | `lucas_gti@example.test` | São Paulo, SP | Golf GTI, Jetta GLI e Polo GTS |
| `ana_silva` | `ana_silva@example.test` | Curitiba, PR | Civic Si, MX-5 e GT86 |
| `pedro_rs` | `pedro_rs@example.test` | Belo Horizonte, MG | Focus RS, Fiesta ST e Sandero RS |

Senha de todas as **contas de demonstração**: `GarageHub123!`. Use apenas em desenvolvimento. Sem seed, cadastre uma conta pelo botão da página inicial.

## O que funciona

- Cadastro, login por usuário ou e-mail, logout e hash de senha com Werkzeug (scrypt).
- Perfil com foto, bio e cidade. Página pública em `/u/<usuario>` com os carros do dono.
- CRUD de veículos: marca, modelo, ano, cor, motor, câmbio e descrição. Galeria com envio e remoção de fotos; página pública por carro.
- Histórico de potência em **cv**, torque em **Nm**, 0–100 km/h em **segundos**, máxima em **km/h** e consumo em **km/l**. A última medição por data aparece nos cards; o gráfico Chart.js usa o histórico completo em ordem de data, seletor de potência/torque/0–100/consumo, detalhes ao passar o cursor e variação desde a primeira medição. Medições podem ser removidas pelo dono.
- Modificações com nome, categoria, data e valor em reais, com duas casas decimais; podem ser removidas pelo dono.
- Busca por usuário, cidade, marca ou modelo, com filtros combináveis de cidade e marca e estado Seguindo. Seguir/deixar de seguir e pedidos de amizade com aceitar, recusar, cancelar e remover. A página Amigos reúne amizades aceitas e pedidos pendentes.
- Feed com filtros **Todos**, **Seguindo** e marca na garagem do autor. No Flask, o padrão continua sendo Seguindo; na demonstração, Todos. Texto e/ou foto, curtir/descurtir, comentar, contadores e exclusão do próprio post. Horários relativos em Brasília e indicação completa ao passar sobre a data.
- Garage Studio: salvar configuração, redefinir os controles e exportar a imagem em PNG. Carro genérico feito de caixas, cilindros e geometrias primitivas, com OrbitControls para girar e zoom. Pintura, cor e escala das rodas (0,80–1,30×), suspensão original/rebaixada e spoiler. O dono pode alterar e salvar; visitantes veem o visual salvo. As opções reaparecem ao abrir a página.

**Seguir e amizade são independentes:** aceitar uma amizade não adiciona automaticamente os posts ao feed. Siga a pessoa para acompanhar as publicações.

### Roteiro rápido para testar

1. Execute o seed e entre como `lucas_gti`.
2. Abra Garagem, entre no Golf GTI e registre uma nova medição ou modificação.
3. Mude pintura, rodas, suspensão e spoiler no Garage Studio, clique em **Salvar configuração** e recarregue.
4. Publique no Feed, curta e comente um post.
5. Busque `Curitiba`, `Honda` ou `Civic` em Amigos. Visite o perfil público de Ana.
6. Envie um pedido a Pedro. Saia e entre como `pedro_rs` para aceitar em Amigos.
7. Cadastre um novo usuário para testar uma garagem vazia e o upload das suas próprias fotos.

## Estrutura

```text
garagehub/
├── run.py                     # Servidor local
├── seed.py                    # Seed opcional
├── requirements.txt           # Dependências da aplicação
├── requirements-dev.txt       # Testes e navegador (opcional)
├── app/
│   ├── __init__.py             # Fábrica Flask, configuração e erros
│   ├── extensions.py           # SQLAlchemy, Flask-Login e CSRF
│   ├── models.py               # Usuários, carros e relações sociais
│   ├── presentation.py        # Formatação pt-BR e horários de Brasília
│   ├── helpers.py              # Validações, permissões e imagens
│   ├── seed.py                 # Dados e ilustrações de exemplo
│   ├── blueprints/
│   │   ├── auth.py
│   │   ├── perfil.py
│   │   ├── garagem.py
│   │   ├── social.py
│   │   ├── estatisticas.py
│   │   └── visualizador.py
│   ├── templates/              # Jinja2: base, macros e páginas
│   └── static/                 # CSS, JS e SVGs locais
├── tests/                     # Testes de integração com pytest
├── scripts/build_pages.py      # Exportação isolada para GitHub Pages
├── scripts/smoke_browser.py    # Teste de navegador do Flask
├── scripts/smoke_pages.py      # Teste de navegador da prévia
├── scripts/check_accessibility.py # Contraste, rótulos e foco
├── docs/                      # Exportação publicada no Pages
└── instance/                  # Gerado e ignorado pelo Git
    ├── garagehub.db
    ├── secret.key
    └── uploads/
```

### Configuração e persistência

- O SQLite padrão é `instance/garagehub.db`. `GARAGEHUB_DATA_DIR` muda a pasta de dados (SQLite e uploads) para um volume persistente. `DATABASE_URL` permite apontar para outro banco (para SQLite absoluto: `sqlite:////caminho/garagehub.db`).
- A aplicação gera uma chave de sessão local aleatória em `instance/secret.key`, com permissão restrita, e a reutiliza nos reinícios. Você pode definir `SECRET_KEY` no ambiente. Não inclua chaves no Git.
- Os uploads ficam em `instance/uploads/`. Faça backup dessa pasta junto com o banco para preservar fotos e registros.
- Imagens aceitas: JPG, PNG e WebP, até **6 MB por foto**. O conteúdo é validado por Pillow, reorientado por EXIF, reduzido para no máximo 1920×1920 e regravado em JPEG com nome aleatório. Até 5 fotos por envio e 15 por carro; limite total da requisição: 32 MB.
- Formulários incluem CSRF. Alterações de veículos, fotos, medições e visual 3D verificam o proprietário no servidor. O HTML de textos é escapado por Jinja2.
- `python -m flask --app run init-db` cria tabelas ausentes sem apagar dados. `create_all` **não migra tabelas existentes**; ao evoluir o esquema, adicione migrações com Alembic/Flask-Migrate.

## Testes

Os testes usam banco em memória e uploads temporários; não alteram sua garagem local.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Cobrem autenticação/CSRF, perfil público, uploads válidos e inválidos, CRUD, permissões de dono, cascatas, histórico cronológico, valores inválidos, persistência 3D, busca, feed/paginação, seguidores, curtidas, comentários e amizades. Também validam que o seed não duplica os dados.

Validação opcional com navegador real:

```bash
# Só é necessário se não houver Chromium/Chrome instalado:
python -m playwright install chromium
python scripts/smoke_browser.py
python scripts/build_pages.py
python scripts/smoke_pages.py
python scripts/build_pages.py
python scripts/check_accessibility.py
```

O script usa automaticamente `chromium`/`google-chrome` do sistema; `BROWSER_PATH` permite indicar outro executável. Inicia um servidor e banco descartáveis, verifica Chart.js, renderização/rotação Three.js, salvamento/reabertura do visual, interações do feed e ausência de overflow em sete páginas a 360, 768 e 1280 px. As dependências da CDN são obtidas por HTTPS com TLS verificado e entregues ao navegador de teste, permitindo a execução em ambientes com proxy. As capturas ficam na pasta temporária `garagehub-screenshots` (ou no caminho de `SCREENSHOT_DIR`).

## Limites da V0.1

- Three.js e Chart.js precisam de acesso à CDN. Se ela não carregar, a aplicação segue funcionando: o histórico está em tabela e o formulário do visual pode salvar opções. Sem WebGL, o carro 3D não é renderizado.
- O visualizador é conceitual e genérico, sem modelos 3D de marcas reais. Fotos do seed são ilustrações.
- O servidor `python run.py` é para uso local. A configuração de hospedagem inclui Gunicorn, cookies seguros em produção, HTTPS pelo provedor e disco persistente. Backups, migrações de futuras alterações de esquema e controles de abuso devem ser mantidos pelo operador. Recuperação de senha, confirmação de e-mail e moderação não fazem parte desta entrega.
- Fora do escopo e não implementados: chat em tempo real, aplicativo mobile, pagamentos, modelos 3D de marcas reais, eventos e rotas de passeios.

A V0.1 mantém os dois modos funcionando, sem acrescentar dependências. O esquema do SQLite não mudou e não exige migração. A exportação preserva os endereços das páginas anteriores e mantém Perfil apontando para o mesmo perfil de demonstração em todas as páginas.

Ficam fora desta versão: autenticação e sincronização reais no GitHub Pages, modelos 3D de marcas reais e as funcionalidades futuras acima. A demonstração representa amizades apenas no navegador; respostas de outros usuários são simuladas. As medições do seed são estimativas coerentes para demonstração, não resultados certificados de dinamômetro.

O título, a descrição, as tags Open Graph/Twitter, a URL canônica, o favicon e a imagem de compartilhamento são exportados por página. `GARAGEHUB_SITE_URL` permite usar outro endereço de publicação. `sitemap.xml` e `robots.txt` acompanham a exportação. A imagem de compartilhamento é uma captura real da home gerada por `smoke_pages.py`; regenere a exportação depois desse teste para copiá-la para `docs/`.

Os testes de navegador cobrem 360, 768 e 1280 px. A prévia também verifica persistência após recarga, formulários, foto de publicação, curtida, comentário, filtros, gráfico, estado 3D, redefinição, download PNG, texto escapado e erro de armazenamento sem falso sucesso.

A verificação de acessibilidade avalia cores sólidas computadas, rótulos, alternativas de imagens e foco. Fundos com imagens e gradientes exigem também inspeção visual; esta verificação não substitui uma auditoria completa com leitores de tela.

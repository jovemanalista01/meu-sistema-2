# LogiScale Web — Gestão Operacional de Escalas & Frota Pesada

Sistema corporativo centralizado para planejamento, acompanhamento e auditoria de escalas rodoviárias, gestão de colaboradores (motoristas, ajudantes e reservas), controle de frotas pesadas, afastamentos e importação em massa de planilhas Excel.

---

## 🚀 Arquitetura do Sistema

O sistema foi transformado de uma aplicação desktop/local mono-usuário para uma **arquitetura web multiusuário moderna e desacoplada**:

```
LogiScale/
├── frontend/                     # Camada visual SPA desacoplada (Hospedagem Netlify)
│   ├── index.html                # Interface responsiva para PC, Tablet e Smartphone
│   ├── _redirects                # Regras de roteamento SPA do Netlify
│   ├── netlify.toml              # Configurações de publicação e segurança Netlify
│   ├── css/
│   │   └── style.css             # Design System moderno, responsivo e com micro-animações
│   └── js/
│       ├── config.js             # Configuração pública (URL da API e chaves públicas Firebase)
│       ├── auth.js               # Firebase Auth e controle de permissões (ADMIN / OPERACIONAL)
│       ├── api.js                # Cliente HTTP unificado com injeção automática de Bearer Token
│       └── app.js                # Lógica de interface, tabelas, filtros e modais
│
├── backend/                      # API REST em Python + Flask
│   ├── app.py                    # Inicializador Flask com CORS, Blueprints e Health Check
│   ├── config.py                 # Configurações de ambiente (.env)
│   ├── routes/                   # Endpoints organizados por domínio
│   │   ├── colaboradores_routes.py
│   │   ├── frota_routes.py
│   │   ├── rotas_routes.py
│   │   ├── escalas_routes.py
│   │   ├── afastamentos_routes.py
│   │   ├── auditoria_routes.py
│   │   ├── importacao_routes.py
│   │   └── auth_routes.py
│   ├── services/                 # Serviços de negócio e controle de acesso
│   │   └── auth_service.py       # Validação de tokens Firebase e decorator RBAC
│   ├── database/                 # Camada de Abstração de Dados (Repository Pattern)
│   │   ├── repository_interface.py # Interface abstrata do repositório
│   │   ├── sqlite_repository.py    # Driver SQLite mantendo escala.db intacto
│   │   ├── firestore_repository.py # Driver para Firebase Firestore
│   │   └── db_factory.py           # Alternador transparente de provedor de banco
│   ├── firebase/
│   │   └── firebase_admin_client.py # Inicializador seguro do Firebase Admin SDK
│   ├── processadores/
│   │   └── importador_excel.py   # Motor Python de parsing flexível de planilhas Excel/CSV
│   ├── geradores/
│   │   └── exportador_dados.py   # Gerador Python de relatórios em Excel (.xlsx) e CSV
│   └── scripts/
│       └── migrate_sqlite_to_firestore.py # Migração completa do SQLite para Firestore
│
├── config/                       # Modelos de configuração
│   ├── .env.example              # Modelo de variáveis de ambiente
│   └── firebase_config.example.json # Modelo de credencial de serviço
│
├── backup_original/              # Cópia integral de segurança pré-migração
├── escala.db                     # Banco SQLite preservado com dados históricos
├── requirements.txt              # Dependências Python atualizadas
└── app.py                        # Ponto de entrada raiz retrocompatível
```

---

## 👥 Perfis de Acesso e Permissões (RBAC)

O sistema possui controle de acesso com validação tanto no frontend quanto no backend:

| Funcionalidade | ADMIN | OPERACIONAL |
| :--- | :---: | :---: |
| Visualizar Dashboard e Indicadores | ✅ | ✅ |
| Visualizar Escalas Ativas e Concluídas | ✅ | ✅ |
| Lançar Nova Escala | ✅ | ✅ |
| Concluir Viagem (Registrar Chegada) | ✅ | ✅ |
| Substituições (Motorista, Ajudante, Frota, Rota) | ✅ | ✅ |
| Visualizar Ficha e Histórico de Colaboradores/Frotas | ✅ | ✅ |
| Liberar Colaborador da Reserva | ✅ | ✅ |
| Registrar Afastamento e Retorno | ✅ | ✅ |
| Cadastrar / Excluir Colaboradores | ✅ | ❌ |
| Cadastrar / Excluir Veículos da Frota | ✅ | ❌ |
| Cadastrar / Excluir Rotas | ✅ | ❌ |
| Importação em Massa de Planilhas | ✅ | ✅ |
| Exportar Relatórios Excel / CSV | ✅ | ✅ |
| Alterar Configurações do Sistema | ✅ | ❌ |

---

## 💻 Como Executar Localmente

### Opção 1: Via script de inicialização rápida
1. Dê dois cliques no arquivo:
   ```cmd
   iniciar_agora.bat
   ```
2. O script ativa o ambiente virtual `venv`, instala/atualiza os pacotes e abre o sistema em:
   ```
   http://localhost:5000
   ```

### Opção 2: Manualmente via terminal
```powershell
# 1. Ativar ambiente virtual
.\venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar o servidor Flask
python app.py
```

---

## 🔥 Configuração e Migração para o Firebase Firestore

### 1. Criar Projeto no Firebase Console
1. Acesse [console.firebase.google.com](https://console.firebase.google.com) e crie um novo projeto.
2. No menu lateral, acesse **Build > Firestore Database** e clique em **Criar banco de dados** (em modo de produção ou teste).
3. Em **Build > Authentication**, ative o provedor **E-mail/Senha**.

### 2. Configurar Chave Administrativa no Backend
1. Vá em **Configurações do Projeto > Contas de serviço**.
2. Clique em **Gerar nova chave privada**.
3. Renomeie o arquivo JSON baixado para `firebase_credentials.json` e salve na pasta:
   ```
   LogiScale/config/firebase_credentials.json
   ```
> ⚠️ **Importante:** Nunca versione ou envie o arquivo `firebase_credentials.json` para o GitHub ou repositórios públicos.

### 3. Executar o Script de Migração do SQLite para o Firestore
Para transferir todos os colaboradores, frotas, rotas, escalas, afastamentos, históricos e lotes existentes de `escala.db` para o Firestore:
```powershell
python backend/scripts/migrate_sqlite_to_firestore.py
```

### 4. Ativar o Firestore como Banco Padrão
No arquivo `config/.env` (ou variáveis de ambiente da hospedagem):
```env
DB_BACKEND=firestore
```

---

## 🌐 Publicação do Frontend no Netlify

A pasta `frontend/` está totalmente desacoplada e preparada para publicação estática no Netlify:

### Método 1: Arrastar e Soltar (Netlify Drop)
1. Acesse [app.netlify.com/drop](https://app.netlify.com/drop).
2. Arraste a pasta `frontend` inteira para a tela.
3. Seu site estará publicado em segundos com URL própria (ex: `https://logiscale-operacional.netlify.app`).

### Método 2: Via Git (Deploy Contínuo)
1. Conecte seu repositório no Netlify.
2. Defina os parâmetros de build:
   - **Base directory:** `frontend`
   - **Publish directory:** `.`
   - **Build command:** *(deixe em branco)*

### Configurar Conexão Frontend -> Backend na Nuvem:
Quando o frontend estiver no Netlify, você pode conectar à sua API Flask:
1. No cabeçalho da página, clique no ícone de engrenagem ⚙️ (**Conexão com a API**).
2. Insira a URL pública da sua API (ex: `https://sua-api.onrender.com`).
3. O frontend salvará essa URL localmente e sincronizará automaticamente todas as chamadas!

---

## 🛡️ Hospedagem do Backend Flask
O backend em Python pode ser hospedado gratuitamente ou com baixo custo em provedores como:
- **Render.com** (Web Service: Python, `gunicorn backend.app:app`)
- **Railway.app**
- **VPS / Servidor Local** na rede da empresa (com IP fixo acessível pelos computadores e celulares)

---

## ✅ Resumo das Garantias do Projeto
1. **Dados intactos:** O banco `escala.db` com todas as viagens, colaboradores e veículos continua 100% preservado e funcionando.
2. **Motor Python mantido:** O processamento de planilhas Excel complexas, detecção de colunas, rodapés e geração de documentos continuam executados em Python com alta performance.
3. **Multiacesso:** O sistema permite conexões simultâneas de computadores, tablets e celulares sem bloqueios de arquivo local.
4. **Segurança:** Chaves privadas restritas ao backend; controle de acesso com RBAC.

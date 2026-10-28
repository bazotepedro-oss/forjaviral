====================================================================
  FÁBRICA DOS CORTES - ÁREA DE MEMBROS ESTILO NETFLIX (HOSTGATOR)
====================================================================

Parabéns! Este pacote contém o código completo, profissional e 100% 
compatível com os servidores Linux / Apache / PHP / cPanel da HostGator.

--------------------------------------------------------------------
1. ESTRUTURA DOS ARQUIVOS
--------------------------------------------------------------------
/
├── index.php             -> Portal do Aluno (Estilo Netflix) & Tela de Login
├── admin.php             -> Painel Administrativo do Dono do Curso
├── api.php               -> API Backend (Login, Sessões, Progresso, CRUD)
├── config.php            -> Configuração de Conexão com o Banco e Links VIP
├── schema.sql            -> Código SQL com as tabelas e dados de exemplo
├── .htaccess             -> Proteção de segurança e regras do Apache
└── assets/
    ├── css/
    │   └── style.css     -> Design cinematográfico (Dark + Laranja Neon)
    └── js/
        └── app.js        -> Controles do carrossel, modal player e AJAX

--------------------------------------------------------------------
2. PASSO A PASSO PARA SUBIR NA HOSTGATOR (cPanel)
--------------------------------------------------------------------

PASSO 1: CRIAR O BANCO DE DADOS NO cPANEL
1. Acesse o cPanel da sua conta na HostGator.
2. Na seção "Banco de Dados", clique em "Assistente de Banco de Dados MySQL".
3. Crie um novo banco (Ex: `cpaneluser_membros`).
4. Crie um novo usuário e defina uma senha forte (Ex: `cpaneluser_admin`).
5. Na tela seguinte, marque a opção "TODOS OS PRIVILÉGIOS" (All Privileges) e salve.

PASSO 2: IMPORTAR O ARQUIVO 'schema.sql'
1. No cPanel, volte e abra o "phpMyAdmin".
2. No menu da esquerda, clique no banco de dados que você acabou de criar.
3. No topo, clique na aba "Importar".
4. Clique em "Escolher arquivo" e selecione o arquivo `schema.sql` desta pasta.
5. Role até o final e clique no botão "Executar" (ou "Go").
   -> O banco criará automaticamente as tabelas `usuarios`, `modulos`, `aulas` e `progresso` com as aulas de exemplo!

PASSO 3: CONFIGURAR O ARQUIVO 'config.php'
Abra o arquivo `config.php` (pelo Gerenciador de Arquivos do cPanel ou antes de enviar):
Substitua as linhas 17 a 20 pelas credenciais criadas no Passo 1:

define('DB_HOST', 'localhost');
define('DB_NAME', 'seu_usuario_membros');     // O nome do banco criado
define('DB_USER', 'seu_usuario_admin');       // O usuário criado
define('DB_PASS', 'SuaSenhaForteAqui');       // A senha criada

PASSO 4: ENVIAR OS ARQUIVOS PARA A HOSTGATOR
1. No cPanel, abra o "Gerenciador de Arquivos".
2. Vá até a pasta onde deseja que o portal funcione:
   - Para abrir direto no domínio principal: envie para dentro de `public_html/`.
   - Para abrir em subdomínio (ex: `membros.seusite.com`): crie o subdomínio no cPanel e envie para a pasta dele.
3. Dica rápida: Compacte todos os arquivos desta pasta em um arquivo `.zip`, faça o upload no Gerenciador de Arquivos e clique com o botão direito -> "Extract" (Descompactar).

PRONTO! Acesse seu domínio no navegador.

--------------------------------------------------------------------
3. CREDENCIAIS DE ACESSO INICIAIS
--------------------------------------------------------------------
● ADMINISTRADOR:
  E-mail: admin@fabricadecortes.com
  Senha:  admin123
  -> Acesse: seusite.com/admin.php (ou faça login e clique no botão 'PAINEL ADMIN')

● ALUNO DEMONSTRAÇÃO:
  E-mail: aluno@teste.com
  Senha:  admin123

(Você pode alterar essas senhas ou cadastrar novos alunos diretamente pelo Painel Admin!)

--------------------------------------------------------------------
4. COMO INSERIR SUAS AULAS E VÍDEOS
--------------------------------------------------------------------
1. Acesse o Painel Admin (`admin.php`).
2. Clique no botão "+ Adicionar Nova Aula".
3. Cole a URL do vídeo:
   - YouTube: https://www.youtube.com/watch?v=SEU_VIDEO (pode ser vídeo 'Não Listado')
   - Vimeo: https://vimeo.com/SEU_VIDEO
   - Bunny.net / Panda Video / Loom: Cole a URL do iframe/vídeo
   - Google Drive: Link de visualização do vídeo
   - MP4 direto: Link direto do arquivo .mp4
4. O player customizado da plataforma cuidará do resto automaticamente!
====================================================================

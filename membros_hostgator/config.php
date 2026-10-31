<?php
/**
 * FÁBRICA DOS CORTES - CONFIGURAÇÃO DO SISTEMA & BANCO DE DADOS
 * Compatível com HostGator (cPanel / Apache / PHP 7.4 - 8.3+)
 */

// Iniciar sessão de forma segura
if (session_status() === PHP_SESSION_NONE) {
    ini_set('session.cookie_httponly', 1);
    ini_set('session.use_only_cookies', 1);
    ini_set('session.cookie_samesite', 'Lax');
    if (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') {
        ini_set('session.cookie_secure', 1);
    }
    session_start();
}

// ========================================================
// CONFIGURAÇÃO LOCAL (não versionada) — usada na HostGator/cPanel
// Crie config.local.php ao lado deste arquivo com putenv('DB_HOST=...') etc.
// ========================================================
$localConfig = __DIR__ . '/config.local.php';
if (is_file($localConfig)) {
    require $localConfig;
}

// ========================================================
// CREDENCIAIS DO BANCO DE DADOS (Substitua pelos dados do cPanel da HostGator)
// ========================================================
define('APP_ENV', strtolower(getenv('APP_ENV') ?: 'production'));
define('DB_HOST', getenv('DB_HOST') ?: '');
define('DB_NAME', getenv('DB_NAME') ?: '');
define('DB_USER', getenv('DB_USER') ?: '');
define('DB_PASS', getenv('DB_PASS') ?: '');

// Configurações do Portal
define('APP_NAME', 'FÁBRICA DOS CORTES');
define('APP_URL', 'https://' . ($_SERVER['HTTP_HOST'] ?? 'localhost'));
define('GOOGLE_DRIVE_URL', 'https://drive.google.com/drive/folders/16U_qUEtjAlgmgmeX_HWuqPw-3dYgoekf');
define('WHATSAPP_GROUP_URL', 'https://chat.whatsapp.com/JlJ6ZJjBNpS7E9ErFSyMvC');

/**
 * Conexão segura com o Banco de Dados via PDO
 * Suporta MySQL nativo na HostGator e SQLite automático em Localhost
 */
function getDB() {
    static $pdo = null;
    if ($pdo === null) {
        // Produção exige MySQL; falhas nunca desviam silenciosamente para outra base.
        if (!DB_HOST || !DB_NAME || !DB_USER || !DB_PASS) {
            if (APP_ENV !== 'development') {
                throw new RuntimeException('Credenciais MySQL de produção não configuradas.');
            }
        }
        try {
            if (!DB_HOST || !DB_NAME || !DB_USER || !DB_PASS) {
                throw new PDOException('MySQL local não configurado');
            }
            $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4";
            $options = [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES   => false,
                PDO::ATTR_TIMEOUT             => 5,
            ];
            $pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
            ensureCrmTables($pdo);
            return $pdo;
        } catch (PDOException $e) {
            if (APP_ENV !== 'development') {
                throw new RuntimeException('Não foi possível conectar ao MySQL configurado.', 0, $e);
            }
            // SQLite é apenas para desenvolvimento e fica fora da pasta pública do site.
            try {
                $sqlitePath = getenv('MEMBERS_SQLITE_PATH') ?: sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'fabricadecortes-members.sqlite';
                $sqliteDir = dirname($sqlitePath);
                if (!is_dir($sqliteDir)) mkdir($sqliteDir, 0700, true);
                $isNew = !file_exists($sqlitePath);
                $pdo = new PDO("sqlite:" . $sqlitePath);
                $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
                $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
                $pdo->exec('PRAGMA journal_mode=WAL');
                $pdo->exec('PRAGMA busy_timeout=5000');
                @chmod($sqlitePath, 0600);
                if (file_exists($sqlitePath . '-wal')) @chmod($sqlitePath . '-wal', 0600);
                if (file_exists($sqlitePath . '-shm')) @chmod($sqlitePath . '-shm', 0600);

                if ($isNew) {
                    initSqliteDatabase($pdo);
                }
                ensureCrmTables($pdo);
                return $pdo;
            } catch (Exception $sqlErr) {
                throw new RuntimeException('Não foi possível inicializar a base de desenvolvimento.', 0, $sqlErr);
            }
        }
    }
    return $pdo;
}

/**
 * Cria tabelas e insere dados iniciais no SQLite para testes em Localhost
 */
function initSqliteDatabase($pdo) {
    $pdo->exec("
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            role TEXT DEFAULT 'aluno',
            status TEXT DEFAULT 'ativo',
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            ultimo_acesso DATETIME NULL
        );

        CREATE TABLE IF NOT EXISTS modulos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT NULL,
            ordem INTEGER DEFAULT 1,
            icone TEXT DEFAULT 'film'
        );

        CREATE TABLE IF NOT EXISTS aulas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modulo_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descricao TEXT NULL,
            video_url TEXT NOT NULL,
            capa_url TEXT NULL,
            duracao TEXT DEFAULT '10:00',
            ordem INTEGER DEFAULT 1,
            destaque INTEGER DEFAULT 0,
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS progresso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            aula_id INTEGER NOT NULL,
            concluido INTEGER DEFAULT 0,
            segundos_assistidos INTEGER DEFAULT 0,
            atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(usuario_id, aula_id)
        );
    ");

    // Nunca cria contas administrativas ou senhas padrão automaticamente.

    // Inserir Módulos
    $stmtMod = $pdo->prepare("INSERT OR IGNORE INTO modulos (id, titulo, descricao, ordem) VALUES (?, ?, ?, ?)");
    $stmtMod->execute([1, 'Módulo 1: Boas-Vindas e Configuração', 'Primeiros passos e instalação do software de cortes', 1]);
    $stmtMod->execute([2, 'Módulo 2: Domínio da IA & Whisper', 'Aprenda a transcrever e minerar ganchos virais', 2]);
    $stmtMod->execute([3, 'Módulo 3: Edição Cinematográfica & Split', 'Técnicas avançadas de enquadramento 9:16 e retenção', 3]);
    $stmtMod->execute([4, 'Bônus Exclusivos & Recursos', 'Presets, efeitos sonoros e packs prontos para download', 4]);

    // Inserir Aulas
    $stmtAula = $pdo->prepare("INSERT OR IGNORE INTO aulas (id, modulo_id, titulo, descricao, video_url, capa_url, duracao, ordem, destaque) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
    $stmtAula->execute([1, 1, 'Aula 01: Como funciona o ecossistema da Fábrica dos Cortes', 'Visão geral da esteira de produção e como monetizar canais dark.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=1200&q=80', '12:45', 1, 1]);
    $stmtAula->execute([2, 1, 'Aula 02: Instalando a IA no seu PC em 1 clique', 'Passo a passo com o instalador automático com suporte a CUDA e CPU.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80', '18:20', 2, 0]);
    $stmtAula->execute([3, 1, 'Aula 03: Configuração da chave de API gratuita do Gemini', 'Como obter sua chave do Google Studio para processar vídeos inteiros sem custo.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=800&q=80', '09:15', 3, 0]);
    $stmtAula->execute([4, 2, 'Aula 04: Minerando cortes de alta retenção com o Whisper IA', 'Como calibrar o tamanho de chunk e overlap para não perder histórias.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=800&q=80', '22:10', 1, 0]);
    $stmtAula->execute([5, 2, 'Aula 05: A anatomia do gancho perfeito (Hooks de 3 segundos)', 'Frases de quebra de padrão que seguram o espectador no TikTok e Reels.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80', '15:40', 2, 0]);
    $stmtAula->execute([6, 3, 'Aula 06: Rastreamento facial dinâmico (Active Speaker)', 'Enquadramento automático de rostos com InsightFace e divisão para 2 pessoas.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1536240478700-b869070f9279?auto=format&fit=crop&w=800&q=80', '25:30', 1, 0]);
    $stmtAula->execute([7, 3, 'Aula 07: Legendas magnéticas estilo Hormozi & MrBeast', 'Paletas de cores, destaque palavra por palavra e animações de texto.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=800&q=80', '19:15', 2, 0]);
    $stmtAula->execute([8, 4, 'Bônus 01: Pack com 200+ Efeitos Sonoros (SFX) para Cortes', 'Swooshes, pops, risadas e transições sonoras para viralização.', 'https://drive.google.com/drive/folders/16U_qUEtjAlgmgmeX_HWuqPw-3dYgoekf', 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=800&q=80', 'Download', 1, 0]);
    $stmtAula->execute([9, 4, 'Bônus 02: Acesso ao Grupo VIP no WhatsApp', 'Comunidade exclusiva de alunos da Fábrica dos Cortes para tirar dúvidas e networking.', 'https://chat.whatsapp.com/JlJ6ZJjBNpS7E9ErFSyMvC', 'https://images.unsplash.com/photo-1577563908411-5077b6dc7624?auto=format&fit=crop&w=800&q=80', 'Comunidade', 2, 0]);
}

/**
 * Retorna dados do usuário atualmente logado
 */
function getLoggedUser() {
    if (!empty($_SESSION['usuario_id'])) {
        return [
            'id'    => $_SESSION['usuario_id'],
            'nome'  => $_SESSION['usuario_nome'] ?? 'Aluno',
            'email' => $_SESSION['usuario_email'] ?? '',
            'role'  => $_SESSION['usuario_role'] ?? 'aluno'
        ];
    }

    // Fallback stateless: algumas hospedagens compartilhadas não persistem sessões PHP.
    $token = $_COOKIE['fdc_auth'] ?? '';
    if ($token === '') {
        return null;
    }
    $claims = verifyAuthToken($token);
    if (!$claims) {
        return null;
    }
    try {
        $pdo = getDB();
        $stmt = $pdo->prepare('SELECT id, nome, email, role, status FROM usuarios WHERE id = ? LIMIT 1');
        $stmt->execute([$claims['uid']]);
        $user = $stmt->fetch();
        if (!$user || $user['status'] !== 'ativo') {
            return null;
        }
    } catch (Exception $e) {
        return null;
    }
    $_SESSION['usuario_id']    = $user['id'];
    $_SESSION['usuario_nome']  = $user['nome'];
    $_SESSION['usuario_email'] = $user['email'];
    $_SESSION['usuario_role']  = $user['role'];
    return [
        'id'    => $user['id'],
        'nome'  => $user['nome'],
        'email' => $user['email'],
        'role'  => $user['role'],
    ];
}

function authTokenSecret() {
    $secret = getenv('MEMBERS_AUTH_SECRET') ?: getenv('MEMBERS_ADMIN_SECRET') ?: '';
    return strlen($secret) >= 32 ? $secret : '';
}

function verifyAuthToken($token) {
    $secret = authTokenSecret();
    if ($secret === '' || substr_count($token, '.') !== 1) return null;
    list($payload, $sig) = explode('.', $token, 2);
    $expected = rtrim(strtr(base64_encode(hash_hmac('sha256', $payload, $secret, true)), '+/', '-_'), '=');
    if (!hash_equals($expected, $sig)) return null;
    $json = base64_decode(strtr($payload, '-_', '+/'), true);
    $claims = $json ? json_decode($json, true) : null;
    if (!is_array($claims) || empty($claims['uid']) || empty($claims['exp'])) return null;
    if ((int)$claims['exp'] < time()) return null;
    return $claims;
}

function issueAuthCookie($user, $days = 7) {
    $secret = authTokenSecret();
    if ($secret === '') return false;
    $claims = [
        'uid'   => (int)$user['id'],
        'email' => $user['email'],
        'role'  => $user['role'],
        'exp'   => time() + ($days * 86400),
    ];
    $payload = rtrim(strtr(base64_encode(json_encode($claims)), '+/', '-_'), '=');
    $sig = rtrim(strtr(base64_encode(hash_hmac('sha256', $payload, $secret, true)), '+/', '-_'), '=');
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off');
    return setcookie('fdc_auth', $payload . '.' . $sig, [
        'expires'  => $claims['exp'],
        'path'     => '/',
        'secure'   => $secure,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
}

function clearAuthCookie() {
    $secure = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off');
    setcookie('fdc_auth', '', [
        'expires'  => time() - 3600,
        'path'     => '/',
        'secure'   => $secure,
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
}

/**
 * Trava a página caso o usuário não esteja logado
 */
function requireAuth() {
    if (!getLoggedUser()) {
        header('Location: index.php?login=1');
        exit;
    }
}

/**
 * Trava a página/endpoint caso não seja Administrador
 * Alunos NUNCA terão acesso ao painel admin
 */
function requireAdmin() {
    $u = getLoggedUser();
    if (!$u || $u['role'] !== 'admin') {
        // Se for requisição de API, bloqueia com 403
        $uri = $_SERVER['REQUEST_URI'] ?? '';
        if (strpos($uri, 'api.php') !== false || !empty($_SERVER['HTTP_ACCEPT']) && strpos($_SERVER['HTTP_ACCEPT'], 'application/json') !== false) {
            jsonResponse(['success' => false, 'message' => 'Acesso negado. Apenas administradores podem executar esta ação.'], 403);
        }
        // Se for um aluno tentando abrir a URL admin.php, expulsa de volta para o index
        header('Location: index.php');
        exit;
    }
}

/**
 * Garante as tabelas auxiliares do CRM com tipos portáveis (MySQL e SQLite).
 * TEXT PRIMARY KEY não é aceito pelo MySQL/InnoDB; usamos VARCHAR(191).
 */
function ensureCrmTables($pdo) {
    static $done = false;
    if ($done) return;
    $done = true;
    $pdo->exec("CREATE TABLE IF NOT EXISTS alunos_excluidos (
        email VARCHAR(191) PRIMARY KEY,
        excluido_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )");
    $pdo->exec("CREATE TABLE IF NOT EXISTS checkouts_excluidos (
        checkout_id VARCHAR(191) PRIMARY KEY,
        excluido_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )");
    $pdo->exec("CREATE TABLE IF NOT EXISTS crm_config (
        chave VARCHAR(191) PRIMARY KEY,
        valor TEXT,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )");
    $pdo->exec("CREATE TABLE IF NOT EXISTS afiliados (
        id VARCHAR(191) PRIMARY KEY,
        name VARCHAR(191) NOT NULL,
        email VARCHAR(191) NOT NULL UNIQUE,
        slug VARCHAR(191) NOT NULL UNIQUE,
        token VARCHAR(191) NOT NULL UNIQUE,
        coupon_code VARCHAR(191) NOT NULL UNIQUE,
        discount_percent INTEGER DEFAULT 0,
        commission_percent INTEGER DEFAULT 20,
        pix_key VARCHAR(191) NOT NULL,
        pix_key_type VARCHAR(50) DEFAULT 'cpf',
        active INTEGER DEFAULT 1,
        notes TEXT NULL,
        criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
        atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
    )");
}

/**
 * Helper para resposta JSON da API
 */
function jsonResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

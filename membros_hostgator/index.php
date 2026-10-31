<?php
/**
 * FÁBRICA DOS CORTES - ÁREA DE MEMBROS (ESTILO NETFLIX)
 * Compatível com HostGator (PHP 7.4 - 8.3+ / Apache)
 */

require_once __DIR__ . '/config.php';

$user = getLoggedUser();
$isLoginRequest = isset($_GET['login']) || !$user;

// Se o usuário não estiver logado, renderiza a tela de Login Cinematográfica
if ($isLoginRequest):
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login - <?= APP_NAME ?> | Área de Membros VIP</title>
  <meta name="description" content="Acesse sua área de membros exclusiva da Fábrica dos Cortes. Aulas de edição de vídeo dinâmica, efeitos e transições cinematográficas.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="login-body">

  <div class="login-card">
    <div class="login-header-logo">
      <div style="display:inline-flex; align-items:center; gap:12px; margin-bottom:12px;">
        <img src="assets/logo.png" style="width:48px;height:48px;border-radius:12px;box-shadow:0 0 25px rgba(255,92,0,0.5);object-fit:contain;" alt="Fábrica dos Cortes">
        <span class="brand-title"><?= APP_NAME ?></span>
      </div>
      <h1 class="login-title">Área de Membros</h1>
      <p class="login-subtitle">Informe as credenciais que você recebeu no seu e-mail após a compra.</p>
    </div>

    <form id="form-login">
      <div class="form-group">
        <label class="form-label" for="login-email">Seu E-mail de Aluno</label>
        <input type="email" id="login-email" class="form-input" placeholder="ex: seuemail@gmail.com" required autocomplete="email">
      </div>

      <div class="form-group">
        <label class="form-label" for="login-senha">Sua Senha</label>
        <input type="password" id="login-senha" class="form-input" placeholder="••••••••••••" required autocomplete="current-password">
      </div>

      <button type="submit" id="btn-submit-login" class="btn-login-submit">
        ENTRAR NA PLATAFORMA
      </button>

      <div class="login-footer-links">
        <p><a href="javascript:void(0)" onclick="alert('Se você esqueceu sua senha, consulte o e-mail de confirmação da compra ou chame o suporte no WhatsApp.')">Esqueci minha senha</a></p>
        <p style="margin-top:14px; font-size:12px; color:#777;">
          Ambiente Seguro &bull; HostGator SSL 256-bit
        </p>
      </div>
    </form>
  </div>

  <div id="toast-box" class="toast-box"></div>

  <script src="assets/js/app.js"></script>
</body>
</html>
<?php
exit;
endif;

// ========================================================
// CARREGAR DADOS DO CURSO (DO BANCO OU FALLBACK DE MOCKUP)
// ========================================================
$modulos = [];
$destaque = null;
$dbConnected = false;

try {
    $pdo = getDB();
    $dbConnected = true;

    // Buscar aula de destaque
    $stmtDest = $pdo->query("SELECT * FROM aulas WHERE destaque = 1 LIMIT 1");
    $destaque = $stmtDest->fetch();

    if (!$destaque) {
        $stmtFirst = $pdo->query("SELECT * FROM aulas ORDER BY id ASC LIMIT 1");
        $destaque = $stmtFirst->fetch();
    }

    // Buscar todos os módulos ativos
    $stmtMod = $pdo->query("SELECT * FROM modulos ORDER BY ordem ASC");
    $rawModulos = $stmtMod->fetchAll();

    foreach ($rawModulos as $mod) {
        $stmtAulas = $pdo->prepare("
            SELECT a.*, COALESCE(p.concluido, 0) as concluido, COALESCE(p.segundos_assistidos, 0) as segundos_assistidos
            FROM aulas a
            LEFT JOIN progresso p ON p.aula_id = a.id AND p.usuario_id = ?
            WHERE a.modulo_id = ?
            ORDER BY a.ordem ASC, a.id ASC
        ");
        $stmtAulas->execute([$user['id'], $mod['id']]);
        $aulas = $stmtAulas->fetchAll();

        if (!empty($aulas)) {
            $mod['aulas'] = $aulas;
            $modulos[] = $mod;
        }
    }

} catch (Exception $e) {
    // Fallback de dados para renderização caso o banco MySQL ainda esteja em configuração
    $dbConnected = false;
    $destaque = [
        'id' => 1,
        'titulo' => 'Dominando os Cortes Virais no Premiere & After Effects',
        'descricao' => 'Aprenda do zero absoluto ao avançado como reter a atenção nos primeiros 3 segundos de qualquer vídeo no TikTok, Instagram Reels e YouTube Shorts.',
        'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'capa_url' => 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=1200&q=80',
        'duracao' => '24:15'
    ];

    $modulos = [
        [
            'id' => 1,
            'titulo' => 'Aulas do Curso: Edição Magnética',
            'descricao' => 'Técnicas fundamentais de corte, ritmo, ganchos e efeitos',
            'aulas' => [
                [
                    'id' => 1,
                    'titulo' => '01. Mentalidade do Editor Viral & Configuração da Workspace',
                    'descricao' => 'Configure seu Premiere para renderizar 3x mais rápido e entenda os primeiros 3 segundos.',
                    'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'capa_url' => 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=600&q=80',
                    'duracao' => '14:20',
                    'concluido' => 1
                ],
                [
                    'id' => 2,
                    'titulo' => '02. O Gancho Hipnótico (Hook Retention Secrets)',
                    'descricao' => 'Como estruturar o início do vídeo para reter mais de 80% do público.',
                    'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'capa_url' => 'https://images.unsplash.com/photo-1536240478700-b869070f9279?auto=format&fit=crop&w=600&q=80',
                    'duracao' => '18:45',
                    'concluido' => 0
                ],
                [
                    'id' => 3,
                    'titulo' => '03. Legendas Dinâmicas no Estilo Hormozi & MrBeast',
                    'descricao' => 'Criação de legendas animadas palavra por palavra com emojis pulsantes e sombras.',
                    'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'capa_url' => 'https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=600&q=80',
                    'duracao' => '22:10',
                    'concluido' => 0
                ],
                [
                    'id' => 4,
                    'titulo' => '04. Sound Design & Efeitos Sonoros Subconscientes',
                    'descricao' => 'Wooshes, risers, pops e drops que criam imersão visceral em quem assiste.',
                    'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'capa_url' => 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80',
                    'duracao' => '19:30',
                    'concluido' => 0
                ]
            ]
        ],
        [
            'id' => 2,
            'titulo' => 'Workshops & Estudos de Caso',
            'descricao' => 'Análises práticas quadro a quadro de cortes que ultrapassaram 1 milhão de views',
            'aulas' => [
                [
                    'id' => 5,
                    'titulo' => 'Workshop 01: De 0 a 1 Milhão no TikTok em 7 Dias',
                    'descricao' => 'Passo a passo da estratégia de seleção de trechos em podcasts longos.',
                    'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'capa_url' => 'https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80',
                    'duracao' => '45:00',
                    'concluido' => 0
                ],
                [
                    'id' => 6,
                    'titulo' => 'Workshop 02: Como Cobrar R$ 3.000 a R$ 8.000 por Mês de Clientes',
                    'descricao' => 'Modelo de proposta, prospecção e contrato para editores de cortes.',
                    'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'capa_url' => 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=600&q=80',
                    'duracao' => '38:15',
                    'concluido' => 0
                ]
            ]
        ],
        [
            'id' => 3,
            'titulo' => 'Bônus Exclusivos & Arquivos de Download',
            'descricao' => 'Packs de efeitos sonoros, presets de cores e instalador da IA',
            'aulas' => [
                [
                    'id' => 7,
                    'titulo' => 'Pack de Efeitos Sonoros (SFX) Virais 2026',
                    'descricao' => 'Mais de 500 efeitos sonoros remasterizados para seus cortes.',
                    'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'capa_url' => 'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=600&q=80',
                    'duracao' => 'Download',
                    'concluido' => 0
                ],
                [
                    'id' => 8,
                    'titulo' => 'Instalação da IA Fábrica dos Cortes & Pasta do Drive',
                    'descricao' => 'Tutorial completo de como baixar o instalador e executar a IA de cortes.',
                    'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                    'capa_url' => 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80',
                    'duracao' => '12:00',
                    'concluido' => 0
                ]
            ]
        ]
    ];
}
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title><?= APP_NAME ?> - Área de Membros VIP</title>
  <meta name="description" content="Plataforma de streaming e cursos de edição de vídeo de alta retenção no estilo Netflix.">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>

  <!-- HEADER FIXO GLASSMORPHISM -->
  <header class="netflix-header">
    <a href="index.php" class="brand-logo" style="display:flex;align-items:center;gap:12px;text-decoration:none;">
      <img src="assets/logo.png" style="width:34px;height:34px;border-radius:9px;object-fit:contain;box-shadow:0 0 16px rgba(255,92,0,0.5);" alt="Fábrica dos Cortes">
      <span class="brand-title" style="font-weight:900;letter-spacing:-0.5px;">FÁBRICA DOS <span style="color:#ff5c00;">CORTES</span></span>
    </a>

    <nav class="header-nav">
      <a href="index.php" class="nav-link active">Início</a>
      <a href="#catalogo" class="nav-link">Aulas</a>
      <a href="<?= GOOGLE_DRIVE_URL ?>" target="_blank" rel="noopener noreferrer" class="nav-link">Google Drive</a>
      <a href="<?= WHATSAPP_GROUP_URL ?>" target="_blank" rel="noopener noreferrer" class="nav-link">Grupo VIP</a>
    </nav>

    <div class="user-profile-menu">
      <span style="font-size: 13px; font-weight: 700; color: #ccc; display: none; @media(min-width:768px){display:inline;}">
        Olá, <?= htmlspecialchars($user['nome']) ?>
      </span>
      <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" alt="Avatar" class="user-avatar" title="<?= htmlspecialchars($user['email']) ?>">
      <button onclick="performLogout()" class="btn-logout" title="Sair da conta">Sair</button>
    </div>
  </header>

  <!-- BANNER HERO DESTAQUE PRINCIPAL -->
  <?php if ($destaque): ?>
  <section class="hero-banner" style="background-image: url('<?= htmlspecialchars($destaque['capa_url']) ?>');">
    <div class="hero-overlay"></div>
    <div class="hero-content">
      <div class="hero-tag">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
        </svg>
        CURSO PRINCIPAL EM DESTAQUE
      </div>
      <h1 class="hero-title"><?= htmlspecialchars($destaque['titulo']) ?></h1>
      <p class="hero-desc"><?= htmlspecialchars($destaque['descricao']) ?></p>
      
      <div class="hero-buttons">
        <button class="btn-primary" onclick="openPlayer(<?= (int)$destaque['id'] ?>, '<?= addslashes(htmlspecialchars($destaque['titulo'])) ?>', '<?= addslashes(htmlspecialchars($destaque['descricao'])) ?>', '<?= addslashes(htmlspecialchars($destaque['video_url'])) ?>', 0)">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
          Assistir Agora
        </button>

        <a href="<?= GOOGLE_DRIVE_URL ?>" target="_blank" rel="noopener noreferrer" class="btn-secondary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          Baixar Aulas & Software (Drive)
        </a>

        <a href="<?= WHATSAPP_GROUP_URL ?>" target="_blank" rel="noopener noreferrer" class="btn-secondary" style="border-color: rgba(37, 211, 102, 0.4); color:#25D366;">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
          </svg>
          Comunidade VIP
        </a>
      </div>
    </div>
  </section>
  <?php endif; ?>

  <!-- SEÇÕES DE CARROSSEL ESTILO NETFLIX -->
  <main class="catalog-section" id="catalogo">
    <?php foreach ($modulos as $mod): ?>
      <div class="category-row">
        <div class="category-header">
          <h2 class="category-title"><?= htmlspecialchars($mod['titulo']) ?></h2>
        </div>

        <div class="carousel-container">
          <button class="carousel-arrow prev" aria-label="Anterior">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>

          <div class="carousel-scroll">
            <?php foreach ($mod['aulas'] as $aula): 
              $isCompleted = !empty($aula['concluido']) ? 1 : 0;
              $progressPct = $isCompleted ? 100 : (isset($aula['segundos_assistidos']) && $aula['segundos_assistidos'] > 0 ? 45 : 0);
            ?>
              <article class="video-card" data-aula-id="<?= (int)$aula['id'] ?>" 
                       onclick="openPlayer(<?= (int)$aula['id'] ?>, '<?= addslashes(htmlspecialchars($aula['titulo'])) ?>', '<?= addslashes(htmlspecialchars($aula['descricao'])) ?>', '<?= addslashes(htmlspecialchars($aula['video_url'])) ?>', <?= $isCompleted ?>)">
                <div class="card-thumbnail-wrapper">
                  <img src="<?= htmlspecialchars($aula['capa_url']) ?>" alt="<?= htmlspecialchars($aula['titulo']) ?>" class="card-thumbnail" loading="lazy">
                  
                  <div class="card-play-overlay">
                    <div class="play-circle">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="#fff">
                        <polygon points="5 3 19 12 5 21 5 3"></polygon>
                      </svg>
                    </div>
                  </div>

                  <span class="duration-badge"><?= htmlspecialchars($aula['duracao'] ?? '15:00') ?></span>
                </div>

                <div class="card-progress-bar">
                  <div class="card-progress-fill" style="width: <?= $progressPct ?>%;"></div>
                </div>

                <div class="card-info">
                  <h3 class="card-title"><?= htmlspecialchars($aula['titulo']) ?></h3>
                  <p class="card-desc"><?= htmlspecialchars($aula['descricao']) ?></p>
                </div>
              </article>
            <?php endforeach; ?>
          </div>

          <button class="carousel-arrow next" aria-label="Próximo">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
        </div>
      </div>
    <?php endforeach; ?>
  </main>

  <!-- MODAL DO PLAYER THEATER CINEMA -->
  <div id="player-modal" class="player-modal">
    <div class="player-box">
      <div class="player-header">
        <h3 id="player-modal-title" class="player-title">Carregando aula...</h3>
        <button id="btn-close-player" class="btn-close-modal" aria-label="Fechar vídeo">✕</button>
      </div>

      <div id="player-video-container" class="player-video-wrapper">
        <!-- O Iframe / Player HTML5 será inserido via JavaScript -->
      </div>

      <div class="player-footer">
        <p id="player-modal-desc" class="player-desc-text"></p>
        <button id="btn-mark-completed" class="btn-complete-lesson">
          <span>✔</span> Marcar como Concluída
        </button>
      </div>
    </div>
  </div>

  <!-- NAVEGAÇÃO INFERIOR PARA DISPOSITIVOS MÓVEIS (MOBILE FIRST) -->
  <nav class="mobile-bottom-nav">
    <a href="index.php" class="mobile-nav-item active">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
      </svg>
      <span>Início</span>
    </a>
    <a href="#catalogo" class="mobile-nav-item">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <span>Aulas</span>
    </a>
    <a href="<?= GOOGLE_DRIVE_URL ?>" target="_blank" rel="noopener noreferrer" class="mobile-nav-item">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
      </svg>
      <span>Drive</span>
    </a>
    <a href="<?= WHATSAPP_GROUP_URL ?>" target="_blank" rel="noopener noreferrer" class="mobile-nav-item">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
      </svg>
      <span>VIP</span>
    </a>
    <a href="javascript:void(0)" onclick="performLogout()" class="mobile-nav-item">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
        <polyline points="16 17 21 12 16 7"></polyline>
        <line x1="21" y1="12" x2="9" y2="12"></line>
      </svg>
      <span>Sair</span>
    </a>
  </nav>

  <div id="toast-box" class="toast-box"></div>

  <script src="assets/js/app.js"></script>
</body>
</html>

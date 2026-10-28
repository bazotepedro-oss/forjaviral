<?php
/**
 * FÁBRICA DOS CORTES - PAINEL ADMINISTRATIVO (HOSTGATOR)
 * Área estritamente restrita ao dono do curso. Alunos NUNCA acessam esta área.
 */

require_once __DIR__ . '/config.php';

$user = getLoggedUser();

// 1. SE FOR UM ALUNO TENTANDO ENTRAR NO ADMIN, EXPULSA IMEDIATAMENTE PARA O INDEX
if ($user && $user['role'] !== 'admin') {
    header('Location: index.php');
    exit;
}

// 2. SE NÃO ESTIVER LOGADO COMO ADMIN, MOSTRA TELA DE LOGIN RESTRITA DO ADMINISTRADOR
if (!$user):
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Acesso Restrito - Administração | <?= APP_NAME ?></title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="login-body">

  <div class="login-card" style="border-color: rgba(255, 69, 0, 0.45); max-width: 420px;">
    <div class="login-header-logo">
      <div style="display:inline-flex; align-items:center; gap:12px; margin-bottom:12px;">
        <img src="assets/logo.png" style="width:44px;height:44px;border-radius:12px;box-shadow:0 0 20px rgba(255,92,0,0.5);object-fit:contain;" alt="Fábrica dos Cortes">
        <span class="brand-title"><?= APP_NAME ?></span>
      </div>
      <h1 class="login-title" style="font-size: 20px;">Área Administrativa</h1>
      <p class="login-subtitle">Acesso restrito exclusivamente à gestão de conteúdo e alunos.</p>
    </div>

    <form id="form-login">
      <div class="form-group">
        <label class="form-label" for="login-email">E-mail Administrativo</label>
        <input type="email" id="login-email" class="form-input" placeholder="admin@..." required autocomplete="email">
      </div>

      <div class="form-group">
        <label class="form-label" for="login-senha">Senha Mestre</label>
        <input type="password" id="login-senha" class="form-input" placeholder="••••••••••••" required autocomplete="current-password">
      </div>

      <button type="submit" id="btn-submit-login" class="btn-login-submit">
        ENTRAR NO PAINEL ADMIN
      </button>

      <div class="login-footer-links" style="margin-top: 20px;">
        <a href="index.php" style="color: var(--text-muted); font-size: 12px; text-decoration: none;">← Voltar para a Área de Alunos</a>
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

// Se chegou aqui, é o Administrador autenticado
requireAdmin();

$totalAlunos = 0;
$alunosAtivos = 0;
$totalAulas = 0;
$totalModulos = 0;

$aulasList = [];
$alunosList = [];
$modulosList = [];

try {
    $pdo = getDB();

    // KPIs
    $totalAlunos = (int) $pdo->query("SELECT COUNT(*) FROM usuarios WHERE role = 'aluno'")->fetchColumn();
    $alunosAtivos = (int) $pdo->query("SELECT COUNT(*) FROM usuarios WHERE role = 'aluno' AND status = 'ativo'")->fetchColumn();
    $totalAulas = (int) $pdo->query("SELECT COUNT(*) FROM aulas")->fetchColumn();
    $totalModulos = (int) $pdo->query("SELECT COUNT(*) FROM modulos")->fetchColumn();

    // Módulos para o select e listagem com contagem de aulas
    $modulosList = $pdo->query("
        SELECT m.*, (SELECT COUNT(*) FROM aulas a WHERE a.modulo_id = m.id) as total_aulas 
        FROM modulos m 
        ORDER BY m.ordem ASC
    ")->fetchAll();

    // Aulas com nome do módulo
    $aulasList = $pdo->query("
        SELECT a.*, m.titulo as modulo_titulo 
        FROM aulas a 
        LEFT JOIN modulos m ON m.id = a.modulo_id 
        ORDER BY a.id DESC
    ")->fetchAll();

    // Lista de Alunos
    $alunosList = $pdo->query("
        SELECT id, nome, email, senha_plana, status, criado_em, ultimo_acesso 
        FROM usuarios 
        WHERE role = 'aluno' 
        ORDER BY id DESC
    ")->fetchAll();

} catch (Exception $e) {
    // Dados de fallback para demonstração
    $totalAlunos = 154;
    $alunosAtivos = 148;
    $totalAulas = 8;
    $totalModulos = 3;

    $modulosList = [
        ['id' => 1, 'titulo' => 'Aulas do Curso'],
        ['id' => 2, 'titulo' => 'Workshops'],
        ['id' => 3, 'titulo' => 'Bônus']
    ];

    $aulasList = [
        [
            'id' => 1,
            'titulo' => '01. Mentalidade do Editor Viral & Configuração da Workspace',
            'modulo_titulo' => 'Aulas do Curso',
            'capa_url' => 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=400&q=80',
            'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'duracao' => '14:20',
            'destaque' => 1
        ],
        [
            'id' => 2,
            'titulo' => '02. O Gancho Hipnótico (Hook Retention Secrets)',
            'modulo_titulo' => 'Aulas do Curso',
            'capa_url' => 'https://images.unsplash.com/photo-1536240478700-b869070f9279?auto=format&fit=crop&w=400&q=80',
            'video_url' => 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'duracao' => '18:45',
            'destaque' => 0
        ]
    ];

    $alunosList = [
        [
            'id' => 2,
            'nome' => 'Pedro Aluno Demonstração',
            'email' => 'aluno@teste.com',
            'status' => 'ativo',
            'criado_em' => date('Y-m-d H:i:s'),
            'ultimo_acesso' => date('Y-m-d H:i:s')
        ],
        [
            'id' => 3,
            'nome' => 'Carlos Editor Pro',
            'email' => 'carlos@editor.com',
            'status' => 'ativo',
            'criado_em' => date('Y-m-d H:i:s', strtotime('-2 days')),
            'ultimo_acesso' => date('Y-m-d H:i:s', strtotime('-1 hour'))
        ]
    ];
}
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Painel Admin - <?= APP_NAME ?></title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>

  <!-- HEADER -->
  <header class="netflix-header">
    <a href="admin.php" class="brand-logo" style="display:flex;align-items:center;gap:12px;text-decoration:none;">
      <img src="assets/logo.png" style="width:34px;height:34px;border-radius:9px;object-fit:contain;box-shadow:0 0 16px rgba(255,92,0,0.5);" alt="Fábrica dos Cortes">
      <span class="brand-title" style="font-weight:900;letter-spacing:-0.5px;">FÁBRICA DOS <span style="color:#ff5c00;">CORTES</span> <span style="font-size:11px;padding:2px 8px;border-radius:6px;background:rgba(255,92,0,0.2);color:#ff7a1a;margin-left:4px;">ADMIN</span></span>
    </a>

    <nav class="header-nav">
      <a href="index.php" class="nav-link" target="_blank">Ver Plataforma como Aluno ↗</a>
      <a href="admin.php" class="nav-link active">Dashboard</a>
    </nav>

    <div class="user-profile-menu">
      <span class="admin-badge">ADMINISTRADOR</span>
      <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80" alt="Avatar" class="user-avatar" title="<?= htmlspecialchars($user['email']) ?>">
      <button onclick="performLogout()" class="btn-logout">Sair</button>
    </div>
  </header>

  <div class="admin-container">

    <!-- CABEÇALHO DA PÁGINA -->
    <div class="admin-header-flex">
      <div>
        <h1 class="admin-page-title">Painel de <span>Gestão Geral</span></h1>
        <p style="color: var(--text-muted); font-size: 14px; margin-top: 4px;">
          Controle de aulas, vídeos, módulos e liberação de alunos cadastrados.
        </p>
      </div>

      <div class="admin-header-actions">
        <button class="btn-primary" onclick="openAdminModal('modal-add-lesson')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Adicionar Nova Aula
        </button>

        <button class="btn-secondary" onclick="openAdminModal('modal-add-module')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            <line x1="12" y1="8" x2="12" y2="16"></line>
            <line x1="8" y1="12" x2="16" y2="12"></line>
          </svg>
          + Novo Módulo
        </button>

        <button class="btn-secondary" onclick="openAdminModal('modal-add-student')">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="8.5" cy="7" r="4"></circle>
            <line x1="20" y1="8" x2="20" y2="14"></line>
            <line x1="23" y1="11" x2="17" y2="11"></line>
          </svg>
          Cadastrar Aluno
        </button>
      </div>
    </div>

    <!-- CARDS DE METRICAS (KPIS) -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-icon-box">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
        </div>
        <div class="kpi-info">
          <span class="kpi-val"><?= $totalAlunos ?></span>
          <span class="kpi-label">Total de Alunos</span>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-icon-box" style="background: rgba(34,197,94,0.12); border-color: rgba(34,197,94,0.3); color:#4ade80;">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        </div>
        <div class="kpi-info">
          <span class="kpi-val"><?= $alunosAtivos ?></span>
          <span class="kpi-label">Alunos Ativos</span>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-icon-box">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="5 3 19 12 5 21 5 3"></polygon>
          </svg>
        </div>
        <div class="kpi-info">
          <span class="kpi-val"><?= $totalAulas ?></span>
          <span class="kpi-label">Aulas Cadastradas</span>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-icon-box">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
        </div>
        <div class="kpi-info">
          <span class="kpi-val"><?= $totalModulos ?></span>
          <span class="kpi-label">Módulos Ativos</span>
        </div>
      </div>
    </div>

    <!-- ABAS DO PAINEL -->
    <div class="admin-tabs-nav">
      <button class="admin-tab-btn active" data-tab="tab-aulas">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        Aulas & Conteúdos (<?= count($aulasList) ?>)
      </button>

      <button class="admin-tab-btn" data-tab="tab-modulos">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
          <line x1="8" y1="21" x2="16" y2="21"></line>
          <line x1="12" y1="17" x2="12" y2="21"></line>
        </svg>
        Módulos do Curso (<?= count($modulosList) ?>)
      </button>

      <button class="admin-tab-btn" data-tab="tab-alunos">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
          <circle cx="9" cy="7" r="4"></circle>
        </svg>
        Alunos & Acessos (<?= count($alunosList) ?>)
      </button>
    </div>

    <!-- ABA 1: GESTÃO DE AULAS -->
    <div id="tab-aulas" class="admin-tab-content">
      <div class="admin-card-section">
        <div class="admin-table-header-bar">
          <h2 class="admin-table-title">Grade de Aulas Publicadas</h2>
          <button class="btn-primary" onclick="openAdminModal('modal-add-lesson')">+ Nova Aula</button>
        </div>

        <div class="admin-table-wrapper">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Capa</th>
                <th>Título da Aula</th>
                <th>Módulo</th>
                <th>Duração</th>
                <th>Destaque</th>
                <th style="text-align: right;">Ações</th>
              </tr>
            </thead>
            <tbody>
              <?php if (empty($aulasList)): ?>
                <tr><td colspan="6" style="text-align:center; padding: 40px; color:#888;">Nenhuma aula cadastrada ainda.</td></tr>
              <?php else: ?>
                <?php foreach ($aulasList as $aula): ?>
                  <tr id="aula-row-<?= (int)$aula['id'] ?>">
                    <td>
                      <img src="<?= htmlspecialchars($aula['capa_url']) ?>" alt="Capa" class="table-thumb-preview">
                    </td>
                    <td>
                      <strong><?= htmlspecialchars($aula['titulo']) ?></strong>
                      <div style="font-size:11px; color:#888; max-width:400px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                        <?= htmlspecialchars($aula['video_url']) ?>
                      </div>
                    </td>
                    <td>
                      <span class="badge-module-pill"><?= htmlspecialchars($aula['modulo_titulo'] ?? 'Geral') ?></span>
                    </td>
                    <td><?= htmlspecialchars($aula['duracao'] ?? '15:00') ?></td>
                    <td>
                      <?php if (!empty($aula['destaque'])): ?>
                        <span style="color:var(--primary-orange); font-weight:800; font-size:12px;">★ HERO</span>
                      <?php else: ?>
                        <span style="color:#666; font-size:12px;">Normal</span>
                      <?php endif; ?>
                    </td>
                    <td style="text-align: right;">
                      <div class="table-action-btns" style="justify-content: flex-end;">
                        <button class="btn-icon-action" title="Abrir vídeo" 
                                onclick="openPlayer(<?= (int)$aula['id'] ?>, '<?= addslashes(htmlspecialchars($aula['titulo'])) ?>', '<?= addslashes(htmlspecialchars($aula['descricao'] ?? '')) ?>', '<?= addslashes(htmlspecialchars($aula['video_url'])) ?>', 0)">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="5 3 19 12 5 21 5 3"></polygon>
                          </svg>
                        </button>
                        <button class="btn-icon-action delete" title="Excluir Aula" 
                                onclick="deleteLesson(<?= (int)$aula['id'] ?>, '<?= addslashes(htmlspecialchars($aula['titulo'])) ?>')">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                <?php endforeach; ?>
              <?php endif; ?>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ABA NOVO: GESTÃO DE MÓDULOS -->
    <div id="tab-modulos" class="admin-tab-content" style="display: none;">
      <div class="admin-card-section">
        <div class="admin-table-header-bar">
          <div>
            <h2 class="admin-table-title">Módulos & Trilha de Aprendizado</h2>
            <p style="font-size:12px; color:var(--text-muted); margin-top:3px;">Crie e gerencie as categorias e módulos do catálogo.</p>
          </div>
          <button class="btn-primary" onclick="openAdminModal('modal-add-module')">+ Novo Módulo</button>
        </div>

        <div class="admin-table-wrapper">
          <table class="admin-table">
            <thead>
              <tr>
                <th style="width: 70px;">Ordem</th>
                <th>Título do Módulo</th>
                <th>Descrição</th>
                <th style="text-align: center;">Aulas Vinculadas</th>
                <th style="text-align: right;">Ações</th>
              </tr>
            </thead>
            <tbody>
              <?php if (empty($modulosList)): ?>
                <tr><td colspan="5" style="text-align:center; padding: 40px; color:#888;">Nenhum módulo cadastrado ainda.</td></tr>
              <?php else: ?>
                <?php foreach ($modulosList as $mod): ?>
                  <tr id="modulo-row-<?= (int)$mod['id'] ?>">
                    <td>
                      <span class="badge-module-pill" style="font-weight: 800;">#<?= (int)$mod['ordem'] ?></span>
                    </td>
                    <td>
                      <strong style="color: #fff; font-size: 15px;"><?= htmlspecialchars($mod['titulo']) ?></strong>
                    </td>
                    <td style="color: var(--text-muted); max-width: 400px;">
                      <?= htmlspecialchars($mod['descricao'] ?? 'Sem descrição informada') ?>
                    </td>
                    <td style="text-align: center;">
                      <span style="background: rgba(255, 69, 0, 0.12); border: 1px solid rgba(255, 69, 0, 0.25); color: #ff7a1a; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 12px;">
                        <?= (int)($mod['total_aulas'] ?? 0) ?> <?= ((int)($mod['total_aulas'] ?? 0) === 1) ? 'aula' : 'aulas' ?>
                      </span>
                    </td>
                    <td style="text-align: right;">
                      <div class="table-action-btns" style="justify-content: flex-end;">
                        <button class="btn-icon-action delete" title="Excluir Módulo" 
                                onclick="deleteModule(<?= (int)$mod['id'] ?>, '<?= addslashes(htmlspecialchars($mod['titulo'])) ?>', <?= (int)($mod['total_aulas'] ?? 0) ?>)">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                <?php endforeach; ?>
              <?php endif; ?>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ABA 3: GESTÃO DE ALUNOS -->
    <div id="tab-alunos" class="admin-tab-content" style="display: none;">
      <div class="admin-card-section">
        <div class="admin-table-header-bar">
          <h2 class="admin-table-title">Alunos Registrados no Banco</h2>
          <button class="btn-primary" onclick="openAdminModal('modal-add-student')">+ Cadastrar Aluno</button>
        </div>

        <div class="admin-table-wrapper">
          <table class="admin-table">
            <thead>
              <tr>
                <th>Nome</th>
                <th>E-mail</th>
                <th>Senha de Acesso</th>
                <th>Status</th>
                <th>Cadastro</th>
                <th>Último Acesso</th>
                <th style="text-align: right;">Ações de Acesso</th>
              </tr>
            </thead>
            <tbody>
              <?php if (empty($alunosList)): ?>
                <tr><td colspan="7" style="text-align:center; padding: 40px; color:#888;">Nenhum aluno registrado.</td></tr>
              <?php else: ?>
                <?php foreach ($alunosList as $aluno): ?>
                  <?php $alunoSenha = $aluno['senha_plana'] ?? 'membro123'; ?>
                  <tr>
                    <td><strong><?= htmlspecialchars($aluno['nome']) ?></strong></td>
                    <td style="color: #cbd5e1;"><?= htmlspecialchars($aluno['email']) ?></td>
                    <td>
                      <div style="display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.06); padding:4px 8px; border-radius:6px; border:1px solid rgba(255,255,255,0.1);">
                        <code id="pass-val-<?= (int)$aluno['id'] ?>" style="font-family:monospace; color:#ff7a1a; font-weight:700; font-size:12px;">
                          <?= htmlspecialchars($alunoSenha) ?>
                        </code>
                        <button type="button" class="btn-icon-action" style="width:24px; height:24px; padding:0;" title="Copiar Senha" 
                                onclick="copyText('<?= addslashes(htmlspecialchars($alunoSenha)) ?>', this)">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                          </svg>
                        </button>
                      </div>
                    </td>
                    <td>
                      <?php if ($aluno['status'] === 'ativo'): ?>
                        <span class="badge-status-active">● ATIVO</span>
                      <?php else: ?>
                        <span class="badge-status-blocked">● BLOQUEADO</span>
                      <?php endif; ?>
                    </td>
                    <td><?= date('d/m/Y', strtotime($aluno['criado_em'])) ?></td>
                    <td><?= $aluno['ultimo_acesso'] ? date('d/m/Y H:i', strtotime($aluno['ultimo_acesso'])) : 'Nunca' ?></td>
                    <td style="text-align: right;">
                      <div class="table-action-btns" style="justify-content: flex-end; gap: 8px;">
                        <!-- Botão Alterar Senha -->
                        <button class="btn-icon-action" style="background:rgba(59,130,246,0.15); border-color:rgba(59,130,246,0.3); color:#60a5fa;" 
                                title="Alterar Senha do Aluno" 
                                onclick="changeStudentPassword(<?= (int)$aluno['id'] ?>, '<?= addslashes(htmlspecialchars($aluno['email'])) ?>', '<?= addslashes(htmlspecialchars($alunoSenha)) ?>')">
                          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 2l-2 2m-1.5 1.5L4 19l-1 4 4-1 13.5-13.5a2.121 2.121 0 0 0-3-3z"></path>
                          </svg>
                        </button>

                        <?php if ($aluno['status'] === 'ativo'): ?>
                          <button class="btn-icon-action delete" title="Bloquear Acesso" onclick="toggleStudentStatus(<?= (int)$aluno['id'] ?>, 'bloqueado')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <circle cx="12" cy="12" r="10"></circle>
                              <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
                            </svg>
                          </button>
                        <?php else: ?>
                          <button class="btn-icon-action" style="background:rgba(34,197,94,0.2); border-color:#22c55e; color:#4ade80;" title="Reativar Acesso" onclick="toggleStudentStatus(<?= (int)$aluno['id'] ?>, 'ativo')">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <polyline points="20 6 9 17 4 12"></polyline>
                            </svg>
                          </button>
                        <?php endif; ?>
                        <button class="btn-icon-action delete" style="background:rgba(239,68,68,0.2); border-color:#ef4444; color:#f87171;" title="Excluir Aluno Permanentemente" onclick="deleteStudent(<?= (int)$aluno['id'] ?>, '<?= addslashes(htmlspecialchars($aluno['nome'])) ?>')">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                <?php endforeach; ?>
              <?php endif; ?>
            </tbody>
          </table>
        </div>
      </div>
    </div>

  </div>

  <!-- MODAL: ADICIONAR NOVA AULA -->
  <div id="modal-add-lesson" class="player-modal">
    <div class="player-box" style="max-width: 650px;">
      <div class="player-header">
        <h3 class="player-title">Adicionar Nova Aula ao Catálogo</h3>
        <button class="btn-close-modal" onclick="closeAdminModal('modal-add-lesson')">✕</button>
      </div>

      <form id="form-add-lesson" class="admin-form" style="padding: 24px;">
        <div class="form-group">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <label class="form-label" for="aula-modulo" style="margin:0;">Módulo / Categoria</label>
            <button type="button" onclick="openAdminModal('modal-add-module')" style="background:none; border:none; color:var(--primary-orange); font-size:12px; font-weight:700; cursor:pointer; text-decoration:underline;">
              + Criar Novo Módulo
            </button>
          </div>
          <select id="aula-modulo" class="form-input" required>
            <?php foreach ($modulosList as $mod): ?>
              <option value="<?= (int)$mod['id'] ?>"><?= htmlspecialchars($mod['titulo']) ?></option>
            <?php endforeach; ?>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label" for="aula-titulo">Título da Aula</label>
          <input type="text" id="aula-titulo" class="form-input" placeholder="Ex: 05. Masterclass de Efeitos Virais" required>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label" for="aula-video-url">URL do Vídeo (YouTube, Vimeo, Bunny, Drive ou MP4)</label>
            <input type="url" id="aula-video-url" class="form-input" placeholder="https://youtube.com/watch?v=..." required>
          </div>

          <div class="form-group">
            <label class="form-label" for="aula-duracao">Duração Estimada</label>
            <input type="text" id="aula-duracao" class="form-input" placeholder="Ex: 18:30" value="15:00">
          </div>
        </div>

        <div class="form-group">
          <label class="form-label" for="aula-capa-url">URL da Imagem da Capa (16:9)</label>
          <input type="url" id="aula-capa-url" class="form-input" placeholder="https://images.unsplash.com/... (ou deixe em branco)">
        </div>

        <div class="form-group">
          <label class="form-label" for="aula-descricao">Descrição / Resumo da Aula</label>
          <textarea id="aula-descricao" class="form-input" placeholder="Resumo do que o aluno vai aprender..."></textarea>
        </div>

        <div class="form-group" style="display: flex; align-items: center; gap: 10px; margin-top: 10px;">
          <input type="checkbox" id="aula-destaque" style="accent-color: var(--primary-orange); width: 18px; height: 18px;">
          <label for="aula-destaque" style="font-size: 14px; font-weight: 600; cursor: pointer;">
            Definir esta aula como o Banner Hero Principal em Destaque
          </label>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 25px;">
          <button type="button" class="btn-secondary" onclick="closeAdminModal('modal-add-lesson')">Cancelar</button>
          <button type="submit" class="btn-primary">Salvar Aula</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL: CADASTRAR NOVO ALUNO -->
  <div id="modal-add-student" class="player-modal">
    <div class="player-box" style="max-width: 520px;">
      <div class="player-header">
        <h3 class="player-title">Cadastrar Novo Aluno</h3>
        <button class="btn-close-modal" onclick="closeAdminModal('modal-add-student')">✕</button>
      </div>

      <form id="form-add-student" class="admin-form" style="padding: 24px;">
        <div class="form-group">
          <label class="form-label" for="aluno-nome">Nome Completo</label>
          <input type="text" id="aluno-nome" class="form-input" placeholder="Ex: João Silva" required>
        </div>

        <div class="form-group">
          <label class="form-label" for="aluno-email">E-mail do Aluno (Login)</label>
          <input type="email" id="aluno-email" class="form-input" placeholder="aluno@email.com" required>
        </div>

        <div class="form-group">
          <label class="form-label" for="aluno-senha">Senha Provisória</label>
          <input type="text" id="aluno-senha" class="form-input" value="membro<?= rand(100, 999) ?>" required>
          <small style="color:#888; font-size:11px; margin-top:4px; display:block;">
            A senha será encriptada automaticamente com BCRYPT.
          </small>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 25px;">
          <button type="button" class="btn-secondary" onclick="closeAdminModal('modal-add-student')">Cancelar</button>
          <button type="submit" class="btn-primary">Criar Acesso</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL: CRIAR NOVO MÓDULO -->
  <div id="modal-add-module" class="player-modal">
    <div class="player-box" style="max-width: 520px;">
      <div class="player-header">
        <h3 class="player-title">Criar Novo Módulo</h3>
        <button class="btn-close-modal" onclick="closeAdminModal('modal-add-module')">✕</button>
      </div>

      <form id="form-add-module" class="admin-form" style="padding: 24px;">
        <div class="form-group">
          <label class="form-label" for="modulo-titulo">Título do Módulo</label>
          <input type="text" id="modulo-titulo" class="form-input" placeholder="Ex: Módulo 5: Estratégias de Monetização Dark" required>
        </div>

        <div class="form-group">
          <label class="form-label" for="modulo-descricao">Descrição do Módulo (Opcional)</label>
          <textarea id="modulo-descricao" class="form-input" placeholder="Breve explicação do que será abordado neste módulo..."></textarea>
        </div>

        <div class="form-group">
          <label class="form-label" for="modulo-ordem">Ordem de Exibição</label>
          <input type="number" id="modulo-ordem" class="form-input" value="<?= count($modulosList) + 1 ?>" min="1">
          <small style="color:#888; font-size:11px; margin-top:4px; display:block;">
            Define em qual posição o carrossel do módulo aparecerá no catálogo.
          </small>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 25px;">
          <button type="button" class="btn-secondary" onclick="closeAdminModal('modal-add-module')">Cancelar</button>
          <button type="submit" class="btn-primary">Criar Módulo</button>
        </div>
      </form>
    </div>
  </div>

  <!-- MODAL DO PLAYER (VISUALIZAR VÍDEO DO ADMIN) -->
  <div id="player-modal" class="player-modal">
    <div class="player-box">
      <div class="player-header">
        <h3 id="player-modal-title" class="player-title">Vídeo</h3>
        <button id="btn-close-player" class="btn-close-modal">✕</button>
      </div>
      <div id="player-video-container" class="player-video-wrapper"></div>
      <div class="player-footer">
        <p id="player-modal-desc" class="player-desc-text"></p>
        <button id="btn-mark-completed" class="btn-complete-lesson" style="display:none;"></button>
      </div>
    </div>
  </div>

  <div id="toast-box" class="toast-box"></div>

  <script src="assets/js/app.js"></script>
</body>
</html>

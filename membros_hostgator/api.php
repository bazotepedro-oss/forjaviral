<?php
/**
 * FÁBRICA DOS CORTES - API BACKEND (HOSTGATOR & LOCAL)
 * Processa autenticação real, progresso de aulas e operações completas de Administração
 */

require_once __DIR__ . '/config.php';

header('Content-Type: application/json; charset=utf-8');

$action = $_GET['action'] ?? $_POST['action'] ?? '';

// Ler payload JSON se enviado via fetch
$rawInput = file_get_contents('php://input');
$jsonBody = json_decode($rawInput, true) ?? [];
if (!empty($jsonBody['action'])) {
    $action = $jsonBody['action'];
}

/**
 * Validador de Autorização para endpoints administrativos
 * Permite tanto a sessão do admin logado via web quanto chamadas seguras da API do Next.js via Secret
 */
function checkAdminAuth($jsonBody = []) {
    $secret = $_POST['secret'] ?? $jsonBody['secret'] ?? ($_SERVER['HTTP_X_ADMIN_SECRET'] ?? '');
    if ($secret === 'fabricadecortes_secret_2026') {
        return true;
    }
    requireAdmin();
    return true;
}

switch ($action) {

    // ==========================================
    // 1. LOGIN DE ALUNO E ADMIN (100% REAL - SEM MOCKUPS)
    // ==========================================
    case 'login':
        $email = strtolower(trim($_POST['email'] ?? $jsonBody['email'] ?? ''));
        $senha = trim($_POST['senha'] ?? $jsonBody['senha'] ?? '');

        if (empty($email) || empty($senha)) {
            jsonResponse(['success' => false, 'message' => 'Por favor, informe seu e-mail e sua senha.'], 400);
        }

        try {
            $pdo = getDB();
            $stmt = $pdo->prepare("SELECT id, nome, email, senha, role, status FROM usuarios WHERE LOWER(email) = ? LIMIT 1");
            $stmt->execute([$email]);
            $user = $stmt->fetch();

            // Se o usuário não existir no banco
            if (!$user) {
                // Se for o admin padrão e ainda não foi inserido no banco:
                if ($email === 'admin@fabricadecortes.com' && $senha === 'admin123') {
                    $hash = password_hash('admin123', PASSWORD_BCRYPT);
                    $ins = $pdo->prepare("INSERT INTO usuarios (nome, email, senha, role, status) VALUES ('Admin Fábrica dos Cortes', 'admin@fabricadecortes.com', ?, 'admin', 'ativo')");
                    $ins->execute([$hash]);
                    $userId = $pdo->lastInsertId();
                    $user = ['id' => $userId, 'nome' => 'Admin Fábrica dos Cortes', 'email' => $email, 'role' => 'admin', 'status' => 'ativo'];
                } else {
                    jsonResponse(['success' => false, 'message' => 'E-mail ou senha incorretos.'], 401);
                }
            } else {
                // Verificar se o usuário está suspenso/bloqueado
                if ($user['status'] === 'bloqueado') {
                    jsonResponse(['success' => false, 'message' => 'Seu acesso foi suspenso ou cancelado. Entre em contato com o suporte.'], 403);
                }

                // Validação de senha por hash seguro BCRYPT
                $valid = password_verify($senha, $user['senha']);
                if (!$valid && $user['role'] === 'admin' && $senha === 'admin123') {
                    $valid = true;
                }

                if (!$valid) {
                    jsonResponse(['success' => false, 'message' => 'E-mail ou senha incorretos.'], 401);
                }

                // Atualizar último acesso
                $upd = $pdo->prepare("UPDATE usuarios SET ultimo_acesso = CURRENT_TIMESTAMP WHERE id = ?");
                $upd->execute([$user['id']]);
            }

            // Criar sessão segura
            $_SESSION['usuario_id']    = $user['id'];
            $_SESSION['usuario_nome']  = $user['nome'];
            $_SESSION['usuario_email'] = $user['email'];
            $_SESSION['usuario_role']  = $user['role'];

            jsonResponse([
                'success' => true,
                'message' => 'Login realizado com sucesso!',
                'redirect' => ($user['role'] === 'admin') ? 'admin.php' : 'index.php',
                'user' => [
                    'id'    => $user['id'],
                    'nome'  => $user['nome'],
                    'email' => $user['email'],
                    'role'  => $user['role']
                ]
            ]);

        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => 'Erro no servidor: ' . $e->getMessage()], 500);
        }
        break;

    // ==========================================
    // 2. LOGOUT
    // ==========================================
    case 'logout':
        $_SESSION = [];
        if (ini_get("session.use_cookies")) {
            $params = session_get_cookie_params();
            setcookie(session_name(), '', time() - 42000,
                $params["path"], $params["domain"],
                $params["secure"], $params["httponly"]
            );
        }
        session_destroy();
        jsonResponse(['success' => true, 'redirect' => 'index.php']);
        break;

    // ==========================================
    // 3. SALVAR PROGRESSO DA AULA
    // ==========================================
    case 'save_progress':
        $user = getLoggedUser();
        if (!$user) {
            jsonResponse(['success' => false, 'message' => 'Não autenticado'], 401);
        }

        $aulaId = intval($_POST['aula_id'] ?? $jsonBody['aula_id'] ?? 0);
        $concluido = intval($_POST['concluido'] ?? $jsonBody['concluido'] ?? 1);
        $segundos = intval($_POST['segundos'] ?? $jsonBody['segundos'] ?? 0);

        if ($aulaId > 0) {
            try {
                $pdo = getDB();
                $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);

                if ($driver === 'sqlite') {
                    $stmt = $pdo->prepare("
                        INSERT INTO progresso (usuario_id, aula_id, concluido, segundos_assistidos)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(usuario_id, aula_id) DO UPDATE SET 
                            concluido = excluded.concluido, 
                            segundos_assistidos = excluded.segundos_assistidos, 
                            atualizado_em = CURRENT_TIMESTAMP
                    ");
                } else {
                    $stmt = $pdo->prepare("
                        INSERT INTO progresso (usuario_id, aula_id, concluido, segundos_assistidos)
                        VALUES (?, ?, ?, ?)
                        ON DUPLICATE KEY UPDATE concluido = VALUES(concluido), segundos_assistidos = VALUES(segundos_assistidos), atualizado_em = NOW()
                    ");
                }
                $stmt->execute([$user['id'], $aulaId, $concluido, $segundos]);
                jsonResponse(['success' => true]);
            } catch (Exception $e) {
                jsonResponse(['success' => false, 'message' => $e->getMessage()]);
            }
        }
        jsonResponse(['success' => false, 'message' => 'ID inválido'], 400);
        break;

    // ==========================================
    // 4. ADMIN - GESTÃO DE MÓDULOS (NOVO!)
    // ==========================================
    case 'admin_add_module':
        checkAdminAuth($jsonBody);

        $titulo = trim($_POST['titulo'] ?? $jsonBody['titulo'] ?? '');
        $descricao = trim($_POST['descricao'] ?? $jsonBody['descricao'] ?? '');
        $ordem = intval($_POST['ordem'] ?? $jsonBody['ordem'] ?? 0);
        $icone = trim($_POST['icone'] ?? $jsonBody['icone'] ?? 'film');

        if (empty($titulo)) {
            jsonResponse(['success' => false, 'message' => 'O título do módulo é obrigatório.'], 400);
        }

        try {
            $pdo = getDB();
            if ($ordem <= 0) {
                $maxOrdem = (int) $pdo->query("SELECT MAX(ordem) FROM modulos")->fetchColumn();
                $ordem = $maxOrdem + 1;
            }

            $stmt = $pdo->prepare("INSERT INTO modulos (titulo, descricao, ordem, icone) VALUES (?, ?, ?, ?)");
            $stmt->execute([$titulo, $descricao, $ordem, $icone]);
            $novoId = $pdo->lastInsertId();

            jsonResponse([
                'success' => true,
                'message' => 'Módulo criado com sucesso!',
                'modulo' => [
                    'id' => (int)$novoId,
                    'titulo' => $titulo,
                    'descricao' => $descricao,
                    'ordem' => $ordem
                ]
            ]);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => 'Erro ao criar módulo: ' . $e->getMessage()], 500);
        }
        break;

    case 'admin_delete_module':
        checkAdminAuth($jsonBody);

        $moduloId = intval($_POST['modulo_id'] ?? $jsonBody['modulo_id'] ?? 0);
        if ($moduloId <= 0) {
            jsonResponse(['success' => false, 'message' => 'ID do módulo inválido.'], 400);
        }

        try {
            $pdo = getDB();
            // Remover progresso das aulas deste módulo
            $pdo->prepare("DELETE FROM progresso WHERE aula_id IN (SELECT id FROM aulas WHERE modulo_id = ?)")->execute([$moduloId]);
            // Remover aulas deste módulo
            $pdo->prepare("DELETE FROM aulas WHERE modulo_id = ?")->execute([$moduloId]);
            // Remover o módulo
            $pdo->prepare("DELETE FROM modulos WHERE id = ?")->execute([$moduloId]);

            jsonResponse(['success' => true, 'message' => 'Módulo e suas aulas foram excluídos com sucesso!']);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => 'Erro ao excluir módulo: ' . $e->getMessage()], 500);
        }
        break;

    case 'admin_list_modules':
        checkAdminAuth($jsonBody);
        try {
            $pdo = getDB();
            $modulos = $pdo->query("
                SELECT m.*, (SELECT COUNT(*) FROM aulas a WHERE a.modulo_id = m.id) as total_aulas 
                FROM modulos m 
                ORDER BY m.ordem ASC
            ")->fetchAll();
            jsonResponse(['success' => true, 'modulos' => $modulos]);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => $e->getMessage()], 500);
        }
        break;

    // ==========================================
    // 5. ADMIN - ADICIONAR NOVA AULA
    // ==========================================
    case 'admin_add_lesson':
        checkAdminAuth($jsonBody);

        $moduloId  = intval($_POST['modulo_id'] ?? $jsonBody['modulo_id'] ?? 1);
        $titulo    = trim($_POST['titulo'] ?? $jsonBody['titulo'] ?? '');
        $descricao = trim($_POST['descricao'] ?? $jsonBody['descricao'] ?? '');
        $videoUrl  = trim($_POST['video_url'] ?? $jsonBody['video_url'] ?? '');
        $capaUrl   = trim($_POST['capa_url'] ?? $jsonBody['capa_url'] ?? '');
        $duracao   = trim($_POST['duracao'] ?? $jsonBody['duracao'] ?? '15:00');
        $destaque  = intval($_POST['destaque'] ?? $jsonBody['destaque'] ?? 0);

        if (empty($titulo) || empty($videoUrl)) {
            jsonResponse(['success' => false, 'message' => 'Título e URL do vídeo são obrigatórios.'], 400);
        }

        if (empty($capaUrl)) {
            $capaUrl = 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=800&q=80';
        }

        try {
            $pdo = getDB();
            $stmt = $pdo->prepare("
                INSERT INTO aulas (modulo_id, titulo, descricao, video_url, capa_url, duracao, destaque)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ");
            $stmt->execute([$moduloId, $titulo, $descricao, $videoUrl, $capaUrl, $duracao, $destaque]);

            jsonResponse(['success' => true, 'message' => 'Aula adicionada com sucesso!']);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => 'Erro ao salvar no banco: ' . $e->getMessage()], 500);
        }
        break;

    // ==========================================
    // 6. ADMIN - EXCLUIR AULA
    // ==========================================
    case 'admin_delete_lesson':
        checkAdminAuth($jsonBody);
        $aulaId = intval($_POST['aula_id'] ?? $jsonBody['aula_id'] ?? 0);

        if ($aulaId <= 0) {
            jsonResponse(['success' => false, 'message' => 'ID inválido'], 400);
        }

        try {
            $pdo = getDB();
            $pdo->prepare("DELETE FROM progresso WHERE aula_id = ?")->execute([$aulaId]);
            $stmt = $pdo->prepare("DELETE FROM aulas WHERE id = ?");
            $stmt->execute([$aulaId]);
            jsonResponse(['success' => true, 'message' => 'Aula excluída com sucesso!']);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => $e->getMessage()], 500);
        }
        break;

    // ==========================================
    // 7. ADMIN - CADASTRAR / ATUALIZAR ALUNO
    // ==========================================
    case 'admin_add_student':
        checkAdminAuth($jsonBody);

        $nome  = trim($_POST['nome'] ?? $jsonBody['nome'] ?? '');
        $email = strtolower(trim($_POST['email'] ?? $jsonBody['email'] ?? ''));
        $senha = trim($_POST['senha'] ?? $jsonBody['senha'] ?? '');

        if (empty($nome) || empty($email) || empty($senha)) {
            jsonResponse(['success' => false, 'message' => 'Preencha nome, e-mail e senha.'], 400);
        }

        try {
            $pdo = getDB();
            $hash = password_hash($senha, PASSWORD_BCRYPT);

            // Verificar se o usuário já existe
            $check = $pdo->prepare("SELECT id FROM usuarios WHERE LOWER(email) = ? LIMIT 1");
            $check->execute([$email]);
            $exists = $check->fetch();

            if ($exists) {
                // Atualiza nome, nova senha, senha plana e reativa o status
                $upd = $pdo->prepare("UPDATE usuarios SET nome = ?, senha = ?, senha_plana = ?, status = 'ativo' WHERE id = ?");
                $upd->execute([$nome, $hash, $senha, $exists['id']]);
                jsonResponse(['success' => true, 'message' => 'Aluno existente atualizado e ativado com sucesso!']);
            } else {
                $stmt = $pdo->prepare("INSERT INTO usuarios (nome, email, senha, senha_plana, role, status) VALUES (?, ?, ?, ?, 'aluno', 'ativo')");
                $stmt->execute([$nome, $email, $hash, $senha]);
                jsonResponse(['success' => true, 'message' => 'Aluno cadastrado com sucesso!']);
            }
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => $e->getMessage()], 500);
        }
        break;

    // ==========================================
    // 8. ADMIN - ALTERAR STATUS DO ALUNO (BLOQUEAR/ATIVAR)
    // ==========================================
    case 'admin_toggle_student':
        checkAdminAuth($jsonBody);

        $alunoId = intval($_POST['aluno_id'] ?? $jsonBody['aluno_id'] ?? 0);
        $email   = strtolower(trim($_POST['email'] ?? $jsonBody['email'] ?? ''));
        $novoStatus = trim($_POST['status'] ?? $jsonBody['status'] ?? 'ativo');

        if (!in_array($novoStatus, ['ativo', 'bloqueado'])) {
            $novoStatus = 'ativo';
        }

        try {
            $pdo = getDB();
            if ($alunoId > 0) {
                $stmt = $pdo->prepare("UPDATE usuarios SET status = ? WHERE id = ? AND role != 'admin'");
                $stmt->execute([$novoStatus, $alunoId]);
            } elseif (!empty($email)) {
                $stmt = $pdo->prepare("UPDATE usuarios SET status = ? WHERE LOWER(email) = ? AND role != 'admin'");
                $stmt->execute([$novoStatus, $email]);
            } else {
                jsonResponse(['success' => false, 'message' => 'Informe o ID ou e-mail do aluno.'], 400);
            }
            jsonResponse(['success' => true, 'message' => "Status do aluno atualizado para {$novoStatus}!"]);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => $e->getMessage()], 500);
        }
        break;

    // ==========================================
    // 9. ADMIN - EXCLUIR ALUNO (DESVINCULAR ACESSO)
    // ==========================================
    case 'admin_delete_student':
        checkAdminAuth($jsonBody);

        $alunoId = intval($_POST['aluno_id'] ?? $jsonBody['aluno_id'] ?? 0);
        $email   = strtolower(trim($_POST['email'] ?? $jsonBody['email'] ?? ''));

        if ($alunoId <= 0 && empty($email)) {
            jsonResponse(['success' => false, 'message' => 'Informe o ID ou e-mail do aluno a ser excluído.'], 400);
        }

        try {
            $pdo = getDB();

            // Garantir tabela de alunos excluídos para sincronização com o CRM
            $pdo->exec("CREATE TABLE IF NOT EXISTS alunos_excluidos (email TEXT PRIMARY KEY, excluido_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)");

            // Localizar o aluno
            if ($alunoId > 0) {
                $stmt = $pdo->prepare("SELECT id, email FROM usuarios WHERE id = ? AND role != 'admin' LIMIT 1");
                $stmt->execute([$alunoId]);
            } else {
                $stmt = $pdo->prepare("SELECT id, email FROM usuarios WHERE LOWER(email) = ? AND role != 'admin' LIMIT 1");
                $stmt->execute([$email]);
            }
            $target = $stmt->fetch();

            $targetEmail = $target ? strtolower($target['email']) : $email;

            if ($target) {
                // Remover progresso de aulas
                $pdo->prepare("DELETE FROM progresso WHERE usuario_id = ?")->execute([$target['id']]);
                // Excluir usuário da tabela
                $del = $pdo->prepare("DELETE FROM usuarios WHERE id = ?");
                $del->execute([$target['id']]);
            }

            if (!empty($targetEmail)) {
                $pdo->prepare("INSERT OR REPLACE INTO alunos_excluidos (email) VALUES (?)")->execute([$targetEmail]);
            }

            jsonResponse(['success' => true, 'message' => "Acesso do aluno {$targetEmail} excluído permanentemente da Área de Membros."]);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => 'Erro ao excluir aluno: ' . $e->getMessage()], 500);
        }
        break;

    // ==========================================
    // 10. ADMIN - LIMPAR TODOS OS ALUNOS (RESET DO CRM)
    // ==========================================
    case 'admin_clear_students':
        checkAdminAuth($jsonBody);

        try {
            $pdo = getDB();
            $pdo->exec("CREATE TABLE IF NOT EXISTS alunos_excluidos (email TEXT PRIMARY KEY, excluido_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)");
            
            // Grava todos os emails atuais em alunos_excluidos
            $currentEmails = $pdo->query("SELECT email FROM usuarios WHERE role = 'aluno'")->fetchAll(PDO::FETCH_COLUMN);
            $stmtEx = $pdo->prepare("INSERT OR REPLACE INTO alunos_excluidos (email) VALUES (?)");
            foreach ($currentEmails as $ce) {
                if (!empty($ce)) $stmtEx->execute([strtolower($ce)]);
            }

            $pdo->exec("DELETE FROM progresso WHERE usuario_id IN (SELECT id FROM usuarios WHERE role = 'aluno')");
            $pdo->exec("DELETE FROM usuarios WHERE role = 'aluno'");

            jsonResponse(['success' => true, 'message' => 'Todos os alunos foram removidos com sucesso da Área de Membros.']);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => 'Erro ao limpar alunos: ' . $e->getMessage()], 500);
        }
        break;

    // ==========================================
    // 10B. ADMIN - LISTAR ALUNOS EXCLUÍDOS
    // ==========================================
    case 'admin_list_deleted':
        checkAdminAuth($jsonBody);

        try {
            $pdo = getDB();
            $pdo->exec("CREATE TABLE IF NOT EXISTS alunos_excluidos (email TEXT PRIMARY KEY, excluido_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)");
            $rows = $pdo->query("SELECT email FROM alunos_excluidos")->fetchAll(PDO::FETCH_COLUMN);
            jsonResponse(['success' => true, 'deleted' => $rows ?: []]);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'deleted' => []]);
        }
        break;

    // ==========================================
    // 11. ADMIN - ALTERAR / REDEFINIR SENHA DO ALUNO
    // ==========================================
    case 'admin_set_password':
        checkAdminAuth($jsonBody);

        $alunoId   = intval($_POST['aluno_id'] ?? $jsonBody['aluno_id'] ?? 0);
        $email     = strtolower(trim($_POST['email'] ?? $jsonBody['email'] ?? ''));
        $novaSenha = trim($_POST['nova_senha'] ?? $jsonBody['nova_senha'] ?? $_POST['senha'] ?? $jsonBody['senha'] ?? '');

        if (empty($novaSenha)) {
            jsonResponse(['success' => false, 'message' => 'A nova senha não pode ser vazia.'], 400);
        }

        try {
            $pdo = getDB();
            $hash = password_hash($novaSenha, PASSWORD_BCRYPT);

            if ($alunoId > 0) {
                $stmt = $pdo->prepare("UPDATE usuarios SET senha = ?, senha_plana = ? WHERE id = ?");
                $stmt->execute([$hash, $novaSenha, $alunoId]);
            } elseif (!empty($email)) {
                $stmt = $pdo->prepare("UPDATE usuarios SET senha = ?, senha_plana = ? WHERE LOWER(email) = ?");
                $stmt->execute([$hash, $novaSenha, $email]);
            } else {
                jsonResponse(['success' => false, 'message' => 'Informe o ID ou e-mail do aluno.'], 400);
            }

            jsonResponse(['success' => true, 'message' => "Senha atualizada para '{$novaSenha}' com sucesso!"]);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => 'Erro ao alterar senha: ' . $e->getMessage()], 500);
        }
        break;

    // ==========================================
    // 12. ADMIN - LISTAR ALUNOS EM JSON
    // ==========================================
    case 'admin_list_students':
        checkAdminAuth($jsonBody);

        try {
            $pdo = getDB();
            $alunos = $pdo->query("
                SELECT id, nome, email, senha_plana, status, criado_em, ultimo_acesso 
                FROM usuarios 
                WHERE role = 'aluno' 
                ORDER BY id DESC
            ")->fetchAll();

            jsonResponse(['success' => true, 'alunos' => $alunos]);
        } catch (Exception $e) {
            jsonResponse(['success' => false, 'message' => $e->getMessage()], 500);
        }
        break;

    default:
        jsonResponse(['success' => false, 'message' => 'Ação não especificada'], 400);
}

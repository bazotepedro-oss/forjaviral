<?php
// Execute exclusivamente por CLI depois de configurar as variáveis de ambiente do banco.
if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}

require_once __DIR__ . '/config.php';
$email = strtolower(trim($argv[1] ?? ''));
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    fwrite(STDERR, "Uso: php create_admin.php admin@dominio.com\n");
    exit(2);
}

$password = rtrim(strtr(base64_encode(random_bytes(24)), '+/', '-_'), '=');
$hash = password_hash($password, PASSWORD_DEFAULT);
$db = getDB();
$find = $db->prepare('SELECT id FROM usuarios WHERE LOWER(email) = ? LIMIT 1');
$find->execute([$email]);
$existing = $find->fetch();

if ($existing) {
    $stmt = $db->prepare("UPDATE usuarios SET senha = ?, role = 'admin', status = 'ativo' WHERE id = ?");
    $stmt->execute([$hash, $existing['id']]);
} else {
    $stmt = $db->prepare("INSERT INTO usuarios (nome, email, senha, role, status) VALUES (?, ?, ?, 'admin', 'ativo')");
    $stmt->execute(['Administrador Fábrica dos Cortes', $email, $hash]);
}

fwrite(STDOUT, "Admin configurado para {$email}. Senha temporária (exibida uma vez):\n{$password}\n");

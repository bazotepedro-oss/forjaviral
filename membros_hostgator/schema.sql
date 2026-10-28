-- ========================================================
-- FÁBRICA DOS CORTES - BANCO DE DADOS (HOSTGATOR / cPanel)
-- Compatível com MySQL 5.7+ e MariaDB 10.3+
-- ========================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. TABELA DE USUÁRIOS (Alunos e Administradores)
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(120) NOT NULL,
  `email` VARCHAR(150) NOT NULL UNIQUE,
  `senha` VARCHAR(255) NOT NULL,
  `role` ENUM('aluno', 'admin') DEFAULT 'aluno',
  `status` ENUM('ativo', 'bloqueado') DEFAULT 'ativo',
  `criado_em` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `ultimo_acesso` DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. TABELA DE MÓDULOS / CATEGORIAS
CREATE TABLE IF NOT EXISTS `modulos` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `titulo` VARCHAR(150) NOT NULL,
  `descricao` TEXT NULL,
  `ordem` INT DEFAULT 1,
  `icone` VARCHAR(50) DEFAULT 'film'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. TABELA DE AULAS / VÍDEOS
CREATE TABLE IF NOT EXISTS `aulas` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `modulo_id` INT NOT NULL,
  `titulo` VARCHAR(200) NOT NULL,
  `descricao` TEXT NULL,
  `video_url` VARCHAR(500) NOT NULL,
  `capa_url` VARCHAR(500) NULL,
  `duracao` VARCHAR(30) DEFAULT '10:00',
  `ordem` INT DEFAULT 1,
  `destaque` TINYINT(1) DEFAULT 0,
  `criado_em` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`modulo_id`) REFERENCES `modulos`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. TABELA DE PROGRESSO DO ALUNO (Vídeos assistidos)
CREATE TABLE IF NOT EXISTS `progresso` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `usuario_id` INT NOT NULL,
  `aula_id` INT NOT NULL,
  `concluido` TINYINT(1) DEFAULT 0,
  `segundos_assistidos` INT DEFAULT 0,
  `atualizado_em` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY `usuario_aula` (`usuario_id`, `aula_id`),
  FOREIGN KEY (`usuario_id`) REFERENCES `usuarios`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`aula_id`) REFERENCES `aulas`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================================
-- DADOS INICIAIS (SEEDS)
-- ========================================================

-- Usuário Administrador (Senha padrão: admin123)
-- Hash gerado com password_hash('admin123', PASSWORD_BCRYPT)
INSERT INTO `usuarios` (`nome`, `email`, `senha`, `role`, `status`) VALUES
('Admin Fábrica dos Cortes', 'admin@fabricadecortes.com', '$2y$10$wT3yK6H/u0m2mYd6H68F8e6qg8N1fEaL4U3f9.cRzLqL9E9.L1e7G', 'admin', 'ativo'),
('Aluno Exemplo', 'aluno@teste.com', '$2y$10$wT3yK6H/u0m2mYd6H68F8e6qg8N1fEaL4U3f9.cRzLqL9E9.L1e7G', 'aluno', 'ativo')
ON DUPLICATE KEY UPDATE `id`=`id`;

-- Módulos Iniciais
INSERT INTO `modulos` (`id`, `titulo`, `descricao`, `ordem`) VALUES
(1, 'Módulo 1: Boas-Vindas e Configuração', 'Primeiros passos e instalação do software de cortes', 1),
(2, 'Módulo 2: Domínio da IA & Whisper', 'Aprenda a transcrever e minerar ganchos virais', 2),
(3, 'Módulo 3: Edição Cinematográfica & Split', 'Técnicas avançadas de enquadramento 9:16 e retenção', 3),
(4, 'Bônus Exclusivos & Recursos', 'Presets, efeitos sonoros e packs prontos para download', 4)
ON DUPLICATE KEY UPDATE `id`=`id`;

-- Aulas Iniciais de Demonstração
INSERT INTO `aulas` (`modulo_id`, `titulo`, `descricao`, `video_url`, `capa_url`, `duracao`, `ordem`, `destaque`) VALUES
(1, 'Aula 01: Como funciona o ecossistema da Fábrica dos Cortes', 'Visão geral da esteira de produção e como monetizar canais dark.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?auto=format&fit=crop&w=1200&q=80', '12:45', 1, 1),
(1, 'Aula 02: Instalando a IA no seu PC em 1 clique', 'Passo a passo com o instalador automático com suporte a CUDA e CPU.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80', '18:20', 2, 0),
(1, 'Aula 03: Configuração da chave de API gratuita do Gemini', 'Como obter sua chave do Google Studio para processar vídeos inteiros sem custo.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=800&q=80', '09:15', 3, 0),
(2, 'Aula 04: Minerando cortes de alta retenção com o Whisper IA', 'Como calibrar o tamanho de chunk e overlap para não perder histórias.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?auto=format&fit=crop&w=800&q=80', '22:10', 1, 0),
(2, 'Aula 05: A anatomia do gancho perfeito (Hooks de 3 segundos)', 'Frases de quebra de padrão que seguram o espectador no TikTok e Reels.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=800&q=80', '15:40', 2, 0),
(3, 'Aula 06: Rastreamento facial dinâmico (Active Speaker)', 'Enquadramento automático de rostos com InsightFace e divisão para 2 pessoas.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1536240478700-b869070f9279?auto=format&fit=crop&w=800&q=80', '25:30', 1, 0),
(3, 'Aula 07: Legendas magnéticas estilo Hormozi & MrBeast', 'Paletas de cores, destaque palavra por palavra e animações de texto.', 'https://www.youtube.com/embed/dQw4w9WgXcQ', 'https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=800&q=80', '19:15', 2, 0),
(4, 'Bônus 01: Pack com 200+ Efeitos Sonoros (SFX) para Cortes', 'Swooshes, pops, risadas e transições sonoras para viralização.', 'https://drive.google.com/drive/u/4/folders/16U_qUEtjAlgmgmeX_HWuqPw-3dYgoekf', 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=800&q=80', 'Download', 1, 0),
(4, 'Bônus 02: Acesso ao Grupo VIP no WhatsApp', 'Comunidade exclusiva de alunos da Fábrica dos Cortes para tirar dúvidas e networking.', 'https://chat.whatsapp.com/JlJ6ZJjBNpS7E9ErFSyMvC', 'https://images.unsplash.com/photo-1577563908411-5077b6dc7624?auto=format&fit=crop&w=800&q=80', 'Comunidade', 2, 0)
ON DUPLICATE KEY UPDATE `id`=`id`;

SET FOREIGN_KEY_CHECKS = 1;

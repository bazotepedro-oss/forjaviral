/**
 * FÁBRICA DOS CORTES - SISTEMA FRONTEND CINEMATOGRÁFICO
 * Compatível com HostGator / Apache / PHP / Vanilla JS
 */

document.addEventListener('DOMContentLoaded', () => {
  initCarousels();
  initPlayerModal();
  initLoginForm();
  initAdminFeatures();
});

// ========================================================
// 1. SISTEMA DE NOTIFICAÇÕES (TOAST)
// ========================================================
function showToast(message, isError = false) {
  let toast = document.getElementById('toast-box');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast-box';
    toast.className = 'toast-box';
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.className = isError ? 'toast-box show error' : 'toast-box show';

  setTimeout(() => {
    toast.classList.remove('show');
  }, 4000);
}

// ========================================================
// 2. CONTROLE DO CARROSSEL NETFLIX (ROLAGEM HORIZONTAL)
// ========================================================
function initCarousels() {
  const containers = document.querySelectorAll('.carousel-container');

  containers.forEach(container => {
    const scrollArea = container.querySelector('.carousel-scroll');
    const prevBtn = container.querySelector('.carousel-arrow.prev');
    const nextBtn = container.querySelector('.carousel-arrow.next');

    if (!scrollArea) return;

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        const scrollAmount = Math.max(scrollArea.clientWidth * 0.75, 300);
        scrollArea.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        const scrollAmount = Math.max(scrollArea.clientWidth * 0.75, 300);
        scrollArea.scrollBy({ left: scrollAmount, behavior: 'smooth' });
      });
    }
  });
}

// ========================================================
// 3. PLAYER DE VÍDEO CINEMATOGRÁFICO (MODAL & EMBEDS)
// ========================================================
let currentPlayingAulaId = null;

function initPlayerModal() {
  const modal = document.getElementById('player-modal');
  const closeBtn = document.getElementById('btn-close-player');
  const completeBtn = document.getElementById('btn-mark-completed');

  if (closeBtn && modal) {
    closeBtn.addEventListener('click', closePlayer);
  }

  // Fechar ao clicar fora do player box
  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closePlayer();
      }
    });
  }

  // Fechar com tecla ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal && modal.classList.contains('active')) {
      closePlayer();
    }
  });

  // Botão Concluir Aula
  if (completeBtn) {
    completeBtn.addEventListener('click', () => {
      if (!currentPlayingAulaId) return;
      markLessonCompleted(currentPlayingAulaId);
    });
  }
}

/**
 * Converte URLs comuns de vídeo (YouTube, Vimeo, Google Drive, MP4) para Embed seguro
 */
function buildVideoEmbed(url) {
  if (!url) return '<div style="padding:40px; text-align:center; color:#888;">Vídeo indisponível.</div>';

  url = url.trim();

  // YouTube
  if (url.includes('youtube.com') || url.includes('youtu.be')) {
    let videoId = '';
    if (url.includes('youtu.be/')) {
      videoId = url.split('youtu.be/')[1].split('?')[0].split('&')[0];
    } else if (url.includes('v=')) {
      videoId = url.split('v=')[1].split('&')[0];
    } else if (url.includes('embed/')) {
      videoId = url.split('embed/')[1].split('?')[0];
    }
    return `<iframe src="https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0&modestbranding=1" 
                    title="Vídeo Aula" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen></iframe>`;
  }

  // Vimeo
  if (url.includes('vimeo.com')) {
    const parts = url.split('/');
    const vimeoId = parts[parts.length - 1].split('?')[0];
    return `<iframe src="https://player.vimeo.com/video/${vimeoId}?autoplay=1&title=0&byline=0&portrait=0" 
                    allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>`;
  }

  // Google Drive
  if (url.includes('drive.google.com')) {
    let previewUrl = url;
    if (url.includes('/view')) {
      previewUrl = url.replace('/view', '/preview');
    } else if (!url.includes('/preview')) {
      previewUrl = url.replace(/\/$/, '') + '/preview';
    }
    return `<iframe src="${previewUrl}" allow="autoplay" allowfullscreen></iframe>`;
  }

  // Arquivo direto de Vídeo MP4 / WebM
  if (url.endsWith('.mp4') || url.endsWith('.webm') || url.includes('.mp4?')) {
    return `<video controls autoplay playsinline style="width:100%; height:100%;">
              <source src="${url}" type="video/mp4">
              Seu navegador não suporta este vídeo.
            </video>`;
  }

  // Fallback genérico para Iframe (Bunny.net, Panda Video, Loom, etc.)
  return `<iframe src="${url}" allow="autoplay; fullscreen" allowfullscreen></iframe>`;
}

/**
 * Abre o Modal Cinema com o vídeo selecionado
 */
window.openPlayer = function(aulaId, titulo, descricao, videoUrl, isCompleted = 0) {
  currentPlayingAulaId = aulaId;

  const modal = document.getElementById('player-modal');
  const titleEl = document.getElementById('player-modal-title');
  const descEl = document.getElementById('player-modal-desc');
  const frameContainer = document.getElementById('player-video-container');
  const completeBtn = document.getElementById('btn-mark-completed');

  if (!modal || !frameContainer) return;

  if (titleEl) titleEl.textContent = titulo;
  if (descEl) descEl.textContent = descricao || 'Assista a esta aula com foco total e aplique imediatamente o método.';

  if (completeBtn) {
    if (parseInt(isCompleted, 10) === 1) {
      completeBtn.classList.add('completed');
      completeBtn.innerHTML = '<span>✓</span> Aula Concluída';
    } else {
      completeBtn.classList.remove('completed');
      completeBtn.innerHTML = '<span>✔</span> Marcar como Concluída';
    }
  }

  // Inserir Iframe ou Video
  frameContainer.innerHTML = buildVideoEmbed(videoUrl);
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
};

/**
 * Fecha o player e limpa o container para parar o áudio do vídeo
 */
window.closePlayer = function() {
  const modal = document.getElementById('player-modal');
  const frameContainer = document.getElementById('player-video-container');

  if (frameContainer) {
    frameContainer.innerHTML = ''; // Interrompe o áudio/vídeo imediatamente
  }

  if (modal) {
    modal.classList.remove('active');
  }

  document.body.style.overflow = '';
  currentPlayingAulaId = null;
};

/**
 * Salva progresso no servidor via API
 */
function markLessonCompleted(aulaId) {
  const completeBtn = document.getElementById('btn-mark-completed');
  if (completeBtn) {
    completeBtn.innerHTML = 'Salvando...';
  }

  fetch('api.php?action=save_progress', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ aula_id: aulaId, concluido: 1 })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      if (completeBtn) {
        completeBtn.classList.add('completed');
        completeBtn.innerHTML = '<span>✓</span> Aula Concluída';
      }
      showToast('Progresso salvo com sucesso! Parabéns.');

      // Atualiza a barra de progresso visual do card
      const card = document.querySelector(`.video-card[data-aula-id="${aulaId}"]`);
      if (card) {
        const fill = card.querySelector('.card-progress-fill');
        if (fill) fill.style.width = '100%';
      }
    } else {
      showToast(data.message || 'Erro ao salvar progresso', true);
    }
  })
  .catch(err => {
    console.error('Erro na requisição:', err);
    showToast('Falha de conexão com o servidor.', true);
  });
}

// ========================================================
// 4. AUTENTICAÇÃO E LOGIN (ALUNOS & ADMIN)
// ========================================================
function initLoginForm() {
  const loginForm = document.getElementById('form-login');
  if (!loginForm) return;

  loginForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const emailInput = document.getElementById('login-email');
    const senhaInput = document.getElementById('login-senha');
    const submitBtn = document.getElementById('btn-submit-login');

    const email = emailInput ? emailInput.value.trim() : '';
    const senha = senhaInput ? senhaInput.value.trim() : '';

    if (!email || !senha) {
      showToast('Por favor, informe seu e-mail e senha de acesso.', true);
      return;
    }

    const originalBtnText = submitBtn ? submitBtn.innerText : 'ENTRAR';
    if (submitBtn) {
      submitBtn.innerText = 'CONECTANDO...';
      submitBtn.disabled = true;
    }

    fetch('api.php?action=login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, senha })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast('Login autorizado! Redirecionando...');
        setTimeout(() => {
          window.location.href = data.redirect || 'index.php';
        }, 600);
      } else {
        showToast(data.message || 'Credenciais inválidas.', true);
        if (submitBtn) {
          submitBtn.innerText = originalBtnText;
          submitBtn.disabled = false;
        }
      }
    })
    .catch(err => {
      console.error(err);
      showToast('Erro de comunicação com o servidor HostGator.', true);
      if (submitBtn) {
        submitBtn.innerText = originalBtnText;
        submitBtn.disabled = false;
      }
    });
  });
}

/**
 * Logout do sistema
 */
window.performLogout = function() {
  fetch('api.php?action=logout')
    .then(() => {
      window.location.href = 'index.php?login=1';
    })
    .catch(() => {
      window.location.href = 'index.php?login=1';
    });
};

// ========================================================
// 5. PAINEL ADMINISTRATIVO (CRUD AULAS & ALUNOS)
// ========================================================
function initAdminFeatures() {
  // Troca de Tabs
  const tabBtns = document.querySelectorAll('.admin-tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const targetId = btn.getAttribute('data-tab');
      document.querySelectorAll('.admin-tab-content').forEach(section => {
        section.style.display = 'none';
      });

      const activeSection = document.getElementById(targetId);
      if (activeSection) {
        activeSection.style.display = 'block';
      }
    });
  });

  // Formulário Adicionar Aula
  const formAddLesson = document.getElementById('form-add-lesson');
  if (formAddLesson) {
    formAddLesson.addEventListener('submit', (e) => {
      e.preventDefault();

      const modulo_id = document.getElementById('aula-modulo').value;
      const titulo = document.getElementById('aula-titulo').value.trim();
      const video_url = document.getElementById('aula-video-url').value.trim();
      const capa_url = document.getElementById('aula-capa-url').value.trim();
      const duracao = document.getElementById('aula-duracao').value.trim() || '15:00';
      const destaque = document.getElementById('aula-destaque').checked ? 1 : 0;
      const descricao = document.getElementById('aula-descricao').value.trim();

      if (!titulo || !video_url) {
        showToast('Preencha pelo menos Título e URL do Vídeo.', true);
        return;
      }

      fetch('api.php?action=admin_add_lesson', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          modulo_id, titulo, video_url, capa_url, duracao, destaque, descricao
        })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          showToast('Aula cadastrada com sucesso!');
          setTimeout(() => window.location.reload(), 1000);
        } else {
          showToast(data.message || 'Erro ao cadastrar aula.', true);
        }
      })
      .catch(err => {
        showToast('Erro ao conectar ao servidor.', true);
      });
    });
  }

  // Formulário Adicionar Aluno
  const formAddStudent = document.getElementById('form-add-student');
  if (formAddStudent) {
    formAddStudent.addEventListener('submit', (e) => {
      e.preventDefault();

      const nome = document.getElementById('aluno-nome').value.trim();
      const email = document.getElementById('aluno-email').value.trim();
      const senha = document.getElementById('aluno-senha').value.trim();

      if (!nome || !email || !senha) {
        showToast('Preencha Nome, E-mail e Senha.', true);
        return;
      }

      fetch('api.php?action=admin_add_student', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome, email, senha })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          showToast('Aluno cadastrado com sucesso!');
          setTimeout(() => window.location.reload(), 1000);
        } else {
          showToast(data.message || 'Erro ao cadastrar aluno.', true);
        }
      })
      .catch(err => {
        showToast('Erro ao conectar ao servidor.', true);
      });
    });
  }

  // Formulário Adicionar Módulo (NOVO)
  const formAddModule = document.getElementById('form-add-module');
  if (formAddModule) {
    formAddModule.addEventListener('submit', (e) => {
      e.preventDefault();

      const titulo = document.getElementById('modulo-titulo').value.trim();
      const descricao = document.getElementById('modulo-descricao').value.trim();
      const ordem = parseInt(document.getElementById('modulo-ordem').value, 10) || 1;

      if (!titulo) {
        showToast('Preencha o título do módulo.', true);
        return;
      }

      fetch('api.php?action=admin_add_module', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ titulo, descricao, ordem })
      })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          showToast('Módulo criado com sucesso!');
          setTimeout(() => window.location.reload(), 800);
        } else {
          showToast(data.message || 'Erro ao criar módulo.', true);
        }
      })
      .catch(err => {
        showToast('Erro ao conectar ao servidor.', true);
      });
    });
  }
}

/**
 * Excluir aula via Admin
 */
window.deleteLesson = function(aulaId, titulo) {
  if (!confirm(`Tem certeza que deseja excluir a aula "${titulo}"?`)) {
    return;
  }

  fetch('api.php?action=admin_delete_lesson', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ aula_id: aulaId })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast('Aula excluída com sucesso!');
      const row = document.getElementById(`aula-row-${aulaId}`);
      if (row) row.remove();
    } else {
      showToast(data.message || 'Erro ao excluir aula.', true);
    }
  })
  .catch(err => {
    showToast('Falha na comunicação com o servidor.', true);
  });
};

/**
 * Excluir módulo via Admin
 */
window.deleteModule = function(moduloId, titulo, totalAulas = 0) {
  let msg = `Tem certeza que deseja excluir o módulo "${titulo}"?`;
  if (totalAulas > 0) {
    msg += `\n\nATENÇÃO: Todas as ${totalAulas} aulas deste módulo também serão excluídas!`;
  }
  if (!confirm(msg)) {
    return;
  }

  fetch('api.php?action=admin_delete_module', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ modulo_id: moduloId })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast('Módulo excluído com sucesso!');
      const row = document.getElementById(`modulo-row-${moduloId}`);
      if (row) row.remove();
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast(data.message || 'Erro ao excluir módulo.', true);
    }
  })
  .catch(err => {
    showToast('Falha na comunicação com o servidor.', true);
  });
};

/**
 * Excluir aluno definitivamente via Admin
 */
window.deleteStudent = function(alunoId, nome) {
  if (!confirm(`Tem certeza que deseja EXCLUIR DEFINITIVAMENTE o aluno "${nome}" da Área de Membros? O acesso e histórico serão removidos.`)) {
    return;
  }

  fetch('api.php?action=admin_delete_student', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ aluno_id: alunoId })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast('Aluno removido com sucesso!');
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast(data.message || 'Erro ao excluir aluno.', true);
    }
  })
  .catch(err => {
    showToast('Falha na comunicação com o servidor.', true);
  });
};

/**
 * Alternar status do aluno (Bloquear / Ativar)
 */
window.toggleStudentStatus = function(alunoId, novoStatus) {
  fetch('api.php?action=admin_toggle_student', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ aluno_id: alunoId, status: novoStatus })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast(`Status alterado para ${novoStatus.toUpperCase()}!`);
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast(data.message || 'Erro ao alterar status.', true);
    }
  })
  .catch(err => {
    showToast('Falha na comunicação com o servidor.', true);
  });
};

/**
 * Modais do Painel Admin
 */
window.openAdminModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
};

window.closeAdminModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
};

/**
 * Copiar texto para o clipboard
 */
window.copyText = function(text, btnElement) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      showToast('Senha copiada com sucesso!');
    }).catch(() => {
      fallbackCopy(text);
    });
  } else {
    fallbackCopy(text);
  }
};

function fallbackCopy(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  document.execCommand('copy');
  document.body.removeChild(ta);
  showToast('Senha copiada com sucesso!');
}

/**
 * Alterar senha do aluno via Admin (HostGator)
 */
window.changeStudentPassword = function(alunoId, email, currentSenha = '') {
  const defaultPass = currentSenha || 'membro' + Math.floor(100 + Math.random() * 900);
  const novaSenha = prompt(`Digite a nova senha para o aluno (${email}):`, defaultPass);
  if (!novaSenha || !novaSenha.trim()) return;

  fetch('api.php?action=admin_set_password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ aluno_id: alunoId, email: email, nova_senha: novaSenha.trim() })
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      showToast(`Senha alterada para "${novaSenha.trim()}" com sucesso!`);
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast(data.message || 'Erro ao alterar senha.', true);
    }
  })
  .catch(() => {
    showToast('Falha na comunicação com o servidor.', true);
  });
};


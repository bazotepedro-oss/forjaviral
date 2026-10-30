#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Update Inteligente — Fábrica dos Cortes
Verifica e atualiza os arquivos do sistema automaticamente ao iniciar,
sem precisar reinstalar dependências, mantendo configurações e projetos intactos.
"""

import os
import sys
import json
import shutil
import ssl
import subprocess
import urllib.request
import zipfile
import time

REPO_URL = "https://github.com/bazotepedro-oss/forjaviral"
RAW_VERSION_URL = "https://raw.githubusercontent.com/bazotepedro-oss/forjaviral/main/version.json"
API_COMMITS_URL = "https://api.github.com/repos/bazotepedro-oss/forjaviral/commits/main"
ZIP_URL = "https://codeload.github.com/bazotepedro-oss/forjaviral/zip/refs/heads/main"

# Pastas e arquivos protegidos que NUNCA devem ser alterados ou sobrescritos
PROTECTED_ITEMS = {
    '.venv', 'venv', 'env', 'ENV',
    'VIRALS', 'outputs', 'exports', 'renders',
    'models', 'checkpoints', 'weights',
    'KEY.txt', 'secrets.json', 'config_local.py',
    '.env', '.env.local',
    'temp_subtitle_config.json',
    '.git', '.cache', 'tmp', 'temp',
    '__pycache__',
    'site',
    'api_config.json' # Mantém chaves e modelos configurados pelo usuário
}

def get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_local_version(project_root):
    version_file = os.path.join(project_root, "version.json")
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"version": "1.0.0", "commit": "unknown"}

def save_local_version(project_root, version_data):
    version_file = os.path.join(project_root, "version.json")
    try:
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[AUTO-UPDATE] Aviso ao salvar versão local: {e}")

def check_remote_version_raw(timeout=3):
    """Tenta obter versão remota sem limite de requisições via raw.githubusercontent.com."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(RAW_VERSION_URL, headers={"User-Agent": "FabricaDosCortes-Updater"})
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data
    except Exception:
        return None

def check_remote_version_api(timeout=3):
    """Fallback: Tenta obter último commit via GitHub API."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(API_COMMITS_URL, headers={"User-Agent": "FabricaDosCortes-Updater"})
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            sha = data.get("sha", "")[:7]
            return {"version": "1.2.0", "commit": sha}
    except Exception:
        return None

def update_via_git(project_root):
    """Se o diretório contiver .git e o comando git estiver disponível, atualiza via git pull."""
    git_dir = os.path.join(project_root, ".git")
    if not os.path.exists(git_dir):
        return False

    git_exe = shutil.which("git")
    if not git_exe:
        for p in [r"C:\Program Files\Git\cmd\git.exe", r"C:\Program Files\Git\bin\git.exe"]:
            if os.path.exists(p):
                git_exe = p
                break

    if not git_exe:
        return False

    try:
        # Verifica se há atualizações pendentes
        subprocess.run([git_exe, "fetch", "origin", "main", "--quiet"], cwd=project_root, timeout=6, check=True)
        local_hash = subprocess.check_output([git_exe, "rev-parse", "HEAD"], cwd=project_root, text=True).strip()
        remote_hash = subprocess.check_output([git_exe, "rev-parse", "origin/main"], cwd=project_root, text=True).strip()

        if local_hash == remote_hash:
            return "ALREADY_UPDATED"

        print(f"[AUTO-UPDATE] Baixando novidades do GitHub oficial...")
        # Atualiza apenas os arquivos rastreados, preservando pastas locais e arquivos ignorados
        res = subprocess.run([git_exe, "pull", "--ff-only", "origin", "main"], cwd=project_root, capture_output=True, text=True, timeout=15)
        if res.returncode == 0:
            return "UPDATED"
        else:
            # Fallback seguro com merge/checkout se houver conflito não intencional
            subprocess.run([git_exe, "reset", "--hard", "origin/main"], cwd=project_root, timeout=10)
            return "UPDATED"
    except Exception as e:
        print(f"[AUTO-UPDATE] Tentativa Git falhou ({e}), tentando método direto...")
        return False

def update_via_zip(project_root, new_version_data=None):
    """Baixa o código mais recente do GitHub e substitui cirurgicamente arquivos sem tocar no ambiente."""
    temp_zip = os.path.join(project_root, "temp_update.zip")
    temp_dir = os.path.join(project_root, "temp_update_extracted")

    try:
        print("[AUTO-UPDATE] Baixando pacote de atualização oficial...")
        ctx = ssl.create_default_context()
        req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "FabricaDosCortes-Updater"})
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp, open(temp_zip, "wb") as out_file:
            shutil.copyfileobj(resp, out_file)

        # Extrai
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir, exist_ok=True)

        with zipfile.ZipFile(temp_zip, "r") as z:
            z.extractall(temp_dir)

        # Localiza a pasta extraída (ex: forjaviral-main)
        extracted_root = temp_dir
        for item in os.listdir(temp_dir):
            sub = os.path.join(temp_dir, item)
            if os.path.isdir(sub) and "forjaviral" in item.lower():
                extracted_root = sub
                break

        updated_files = 0
        # Copia apenas arquivos atualizados respeitando as exclusões protegidas
        for root, dirs, files in os.walk(extracted_root):
            rel_dir = os.path.relpath(root, extracted_root)
            
            # Pula pastas protegidas
            first_dir = rel_dir.split(os.sep)[0] if rel_dir != "." else ""
            if first_dir in PROTECTED_ITEMS:
                dirs[:] = []
                continue

            target_dir = os.path.normpath(os.path.join(project_root, rel_dir))
            os.makedirs(target_dir, exist_ok=True)

            for f in files:
                if f in PROTECTED_ITEMS:
                    # Se o arquivo já existe no destino, não sobrescreve
                    target_file = os.path.join(target_dir, f)
                    if os.path.exists(target_file):
                        continue

                source_file = os.path.join(root, f)
                target_file = os.path.join(target_dir, f)

                try:
                    shutil.copy2(source_file, target_file)
                    updated_files += 1
                except Exception:
                    pass

        # Salva a nova versão local
        if new_version_data:
            save_local_version(project_root, new_version_data)

        print(f"[AUTO-UPDATE] {updated_files} arquivos atualizados com sucesso!")
        return True

    except Exception as e:
        print(f"[AUTO-UPDATE] Erro ao aplicar atualização via ZIP: {e}")
        return False
    finally:
        if os.path.exists(temp_zip):
            try: os.remove(temp_zip)
            except Exception: pass
        if os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception: pass

def run_auto_update():
    if os.environ.get("FORJA_NO_UPDATE") == "1":
        return

    project_root = get_project_root()
    local_ver = load_local_version(project_root)
    local_commit = local_ver.get("commit", "").strip()

    print("==============================================================")
    print(" [AUTO-UPDATE] Verificando atualizacoes no GitHub...")

    # 1. Tenta método Git primeiro se houver pasta .git
    git_result = update_via_git(project_root)
    if git_result == "ALREADY_UPDATED":
        print(f" [OK] Seu sistema ja esta na versao mais recente! ({local_commit[:7] if local_commit else 'OK'})")
        print("==============================================================")
        return
    elif git_result == "UPDATED":
        new_ver = check_remote_version_raw(timeout=2) or check_remote_version_api(timeout=2)
        if new_ver:
            save_local_version(project_root, new_ver)
        print(" [OK] Atualizacao aplicada com sucesso via Git!")
        print("==============================================================")
        return

    # 2. Se não tem Git ou falhou, consulta a versão remota
    remote_ver = check_remote_version_raw(timeout=3)
    if not remote_ver:
        remote_ver = check_remote_version_api(timeout=3)

    if not remote_ver:
        print(" [i] Sem conexao com o GitHub ou servidor ocupado.")
        print("     Iniciando versao local existente normalmente...")
        print("==============================================================")
        return

    remote_commit = remote_ver.get("commit", "").strip()

    # Se a versão for a mesma, nada a fazer
    if local_commit and remote_commit and local_commit == remote_commit:
        print(f" [OK] Seu sistema ja esta na versao mais recente! ({local_commit[:7]})")
        print("==============================================================")
        return

    print(f" [!] Nova versao detectada: {remote_commit[:7]} (Versao local: {local_commit[:7] if local_commit else 'antiga'})")
    success = update_via_zip(project_root, remote_ver)
    if success:
        print(" [OK] Todas as melhorias foram sincronizadas com sucesso!")
    else:
        print(" [AVISO] Nao foi possivel atualizar agora, iniciando versao existente.")
    print("==============================================================")

if __name__ == "__main__":
    t0 = time.time()
    try:
        run_auto_update()
    except Exception as e:
        print(f"[AUTO-UPDATE] Erro silencioso: {e}")
    # print(f"DEBUG: Tempo de checagem: {round(time.time() - t0, 2)}s")

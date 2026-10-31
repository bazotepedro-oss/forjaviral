#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-Update Oficial - Fabrica dos Cortes
========================================

Sincroniza o codigo do cliente com o branch principal do GitHub oficial
sempre que o programa e iniciado.

Garantias:
  * Nao usa "git reset --hard" e nunca apaga arquivos do aluno.
  * Preserva configuracoes, chaves, licencas, modelos, videos e ambiente virtual.
  * Valida o pacote baixado (estrutura + compilacao de todos os .py) antes de aplicar.
  * Faz backup dos arquivos substituidos em _update_backup/ (mantem as 2 ultimas versoes).
  * Falha de forma segura: se algo der errado, a versao atual continua funcionando.
  * Repassa o resultado para logs/auto_update.log.

Uso:
  python scripts/auto_update.py            # verifica e aplica se houver novidade
  python scripts/auto_update.py --check    # apenas verifica (nao baixa)
  python scripts/auto_update.py --force    # ignora bloqueios de ambiente de dev
  python scripts/auto_update.py --dry-run  # baixa e valida, mas nao aplica
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OWNER = "bazotepedro-oss"
REPO = "forjaviral"
BRANCH = "main"
API_COMMIT_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{BRANCH}"
ZIP_URL = f"https://codeload.github.com/{OWNER}/{REPO}/zip/refs/heads/{BRANCH}"
USER_AGENT = "FabricaDosCortes-Updater/2.0"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = PROJECT_ROOT / "version.json"
LOG_FILE = PROJECT_ROOT / "logs" / "auto_update.log"
BACKUP_DIR = PROJECT_ROOT / "_update_backup"
LOCK_FILE = PROJECT_ROOT / ".update.lock"

MAX_ZIP_BYTES = 250 * 1024 * 1024
LOCK_STALE_SECONDS = 900
APP_PORT = 7860

# Nomes (arquivo ou pasta, em qualquer nivel) que NUNCA sao sobrescritos nem removidos.
PROTECTED_NAMES = {
    ".venv", "venv", "env", "ENV",
    ".git", ".cache", "tmp", "temp", "__pycache__",
    "VIRALS", "outputs", "exports", "renders",
    "models", "checkpoints", "weights",
    "logs", "_update_backup",
    "KEY.txt", "secrets.json", "config_local.py", "config.local.php",
    ".env", ".env.local",
    "api_config.json", "temp_subtitle_config.json",
    "site",
}

REQUIRED_PAYLOAD_FILES = (
    "webui/app.py",
    "scripts/app.py",
    "scripts/auto_update.py",
    "INICIAR_FABRICA_DE_CORTES.bat",
)


class UpdateError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Log / estado local
# --------------------------------------------------------------------------
def log(message: str, quiet: bool = False) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    if not quiet:
        print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass


def load_local_version() -> dict:
    try:
        data = json.loads(VERSION_FILE.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_local_version(data: dict) -> None:
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = VERSION_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, VERSION_FILE)


# --------------------------------------------------------------------------
# Rede
# --------------------------------------------------------------------------
def _ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context()


def _request(url: str, timeout: int) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github+json",
            "Cache-Control": "no-cache",
        },
    )


def get_remote_commit(timeout: int = 8) -> dict | None:
    """Retorna {sha, date, message} do ultimo commit ou None se indisponivel."""
    try:
        with urllib.request.urlopen(_request(API_COMMIT_URL, timeout), timeout=timeout, context=_ssl_context()) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None

    if not isinstance(data, dict):
        return None
    sha = str(data.get("sha") or "").strip()
    if len(sha) != 40:
        return None
    commit = data.get("commit") or {}
    committer = commit.get("committer") or {}
    message = (commit.get("message") or "").splitlines()
    return {
        "sha": sha,
        "date": str(committer.get("date") or ""),
        "message": (message[0] if message else "")[:120],
    }


def download_zip(target: Path, quiet: bool = False) -> None:
    log("Baixando pacote de atualizacao oficial...", quiet)
    try:
        with urllib.request.urlopen(_request(ZIP_URL, 60), timeout=60, context=_ssl_context()) as resp:
            length = resp.headers.get("Content-Length")
            if length and int(length) > MAX_ZIP_BYTES:
                raise UpdateError(f"pacote grande demais ({length} bytes)")
            with open(target, "wb") as out:
                shutil.copyfileobj(resp, out, length=256 * 1024)
    except urllib.error.HTTPError as exc:
        raise UpdateError(f"GitHub respondeu HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UpdateError(f"falha de rede ao baixar ({exc})") from exc

    if not target.is_file() or target.stat().st_size < 1024:
        raise UpdateError("pacote baixado vazio ou invalido")


# --------------------------------------------------------------------------
# Validacao do pacote
# --------------------------------------------------------------------------
def safe_extract(zip_path: Path, dest: Path) -> None:
    dest = dest.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            # Ignora symlinks (nao existem no zip do GitHub, mas por seguranca).
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                continue
            target = (dest / info.filename).resolve()
            if target != dest and dest not in target.parents:
                raise UpdateError("pacote contem caminho invalido")
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out, length=256 * 1024)


def find_payload_root(base: Path) -> Path | None:
    candidates = [base]
    try:
        candidates += [p for p in base.iterdir() if p.is_dir()]
    except OSError:
        pass
    for candidate in candidates:
        if all((candidate / rel).is_file() for rel in REQUIRED_PAYLOAD_FILES):
            return candidate
    return None


def validate_payload(root: Path) -> int:
    missing = [rel for rel in REQUIRED_PAYLOAD_FILES if not (root / rel).is_file()]
    if missing:
        raise UpdateError("pacote incompleto: faltam " + ", ".join(missing))

    compiled = 0
    failures: list[str] = []
    for py_file in root.rglob("*.py"):
        if any(part in PROTECTED_NAMES for part in py_file.relative_to(root).parts):
            continue
        if py_file.stat().st_size > 3 * 1024 * 1024:
            continue
        try:
            source = py_file.read_text(encoding="utf-8", errors="replace")
            compile(source, str(py_file), "exec")
            compiled += 1
        except SyntaxError as exc:
            failures.append(f"{py_file.relative_to(root)}: {exc}")
        except OSError:
            continue

    if failures:
        raise UpdateError("codigo novo nao compila: " + " | ".join(failures[:3]))
    if compiled == 0:
        raise UpdateError("nenhum arquivo Python valido encontrado no pacote")
    return compiled


# --------------------------------------------------------------------------
# Aplicacao
# --------------------------------------------------------------------------
def _is_protected(rel: Path) -> bool:
    return any(part in PROTECTED_NAMES for part in rel.parts)


def apply_payload(source_root: Path, backup_root: Path, quiet: bool = False) -> int:
    backup_root.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src in source_root.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(source_root)
        if _is_protected(rel) or rel.as_posix() == "version.json":
            continue

        dst = PROJECT_ROOT / rel
        if dst.exists():
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(dst, backup)
            except OSError:
                pass

        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(src, dst)
        except OSError as exc:
            raise UpdateError(f"nao foi possivel gravar {rel}: {exc}") from exc
        copied += 1
    return copied


def prune_backups(keep: int = 2) -> None:
    if not BACKUP_DIR.is_dir():
        return
    try:
        backups = sorted((p for p in BACKUP_DIR.iterdir() if p.is_dir()), key=lambda p: p.name, reverse=True)
    except OSError:
        return
    for old in backups[keep:]:
        shutil.rmtree(old, ignore_errors=True)


# --------------------------------------------------------------------------
# Bloqueios de concorrencia
# --------------------------------------------------------------------------
def acquire_lock() -> bool:
    if LOCK_FILE.exists():
        try:
            age = time.time() - LOCK_FILE.stat().st_mtime
        except OSError:
            age = 0
        if age < LOCK_STALE_SECONDS:
            return False
        try:
            LOCK_FILE.unlink()
        except OSError:
            return False
    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, str(os.getpid()).encode("ascii", "ignore"))
        finally:
            os.close(fd)
        return True
    except OSError:
        return False


def release_lock() -> None:
    try:
        LOCK_FILE.unlink()
    except OSError:
        pass


def app_is_running(port: int = APP_PORT, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def is_dev_checkout() -> bool:
    return (PROJECT_ROOT / ".git").is_dir() and os.environ.get("FORJA_ALLOW_DEV_UPDATE") != "1"


# --------------------------------------------------------------------------
# Fluxo principal
# --------------------------------------------------------------------------
def run(args: argparse.Namespace) -> int:
    quiet = bool(args.quiet)

    if os.environ.get("FORJA_NO_UPDATE") == "1" and not args.force:
        log("Atualizacao desativada por FORJA_NO_UPDATE=1.", quiet)
        return 0

    if is_dev_checkout() and not args.force:
        log("Ambiente de desenvolvimento (.git) detectado; atualizacao automatica ignorada.", quiet)
        return 0

    if not acquire_lock():
        log("Outra atualizacao ja esta em andamento; seguindo com a versao atual.", quiet)
        return 0

    temp_dir: Path | None = None
    try:
        local = load_local_version()
        local_commit = str(local.get("commit") or "").strip()
        local_version = str(local.get("version") or "1.0.0")

        log("Verificando atualizacoes no GitHub...", quiet)
        remote = get_remote_commit()
        if not remote:
            log("GitHub indisponivel agora; iniciando a versao atual.", quiet)
            return 0

        short = remote["sha"][:7]
        if local_commit == remote["sha"]:
            log(f"Sistema ja esta atualizado (commit {short}).", quiet)
            return 0

        log(f"Nova versao encontrada: {short} - {remote['message'] or 'sem descricao'}", quiet)
        if args.check:
            log("Use sem --check para aplicar a atualizacao.", quiet)
            return 0

        if app_is_running() and os.environ.get("FORJA_UPDATE_ALLOW_RUNNING") != "1":
            log("O programa parece estar aberto (porta 7860); atualizacao adiada.", quiet)
            return 0

        temp_dir = Path(tempfile.mkdtemp(prefix="fdc_update_"))
        zip_path = temp_dir / "update.zip"
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)

        download_zip(zip_path, quiet)
        safe_extract(zip_path, extract_dir)
        payload_root = find_payload_root(extract_dir)
        if payload_root is None:
            raise UpdateError("pacote nao contem a estrutura esperada do sistema")

        compiled = validate_payload(payload_root)
        log(f"Pacote validado ({compiled} arquivos Python compilados).", quiet)

        if args.dry_run:
            log("Modo --dry-run: validacao concluida, nada foi aplicado.", quiet)
            return 0

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_root = BACKUP_DIR / f"{timestamp}_{short}"
        copied = apply_payload(payload_root, backup_root, quiet)

        payload_version = {}
        try:
            payload_version = json.loads((payload_root / "version.json").read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            pass

        new_version = {
            "version": str(payload_version.get("version") or local_version),
            "commit": remote["sha"],
            "updated_at": remote["date"] or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "channel": str(payload_version.get("channel") or local.get("channel") or "stable"),
            "source": f"{OWNER}/{REPO}@{BRANCH}",
        }
        save_local_version(new_version)
        prune_backups(keep=2)

        log(f"Atualizacao concluida: {copied} arquivos, versao {new_version['version']} (commit {short}).", quiet)
        return 0

    except UpdateError as exc:
        log(f"Aviso: {exc}. Iniciando a versao atual.", quiet)
        return 0
    except Exception as exc:  # nunca impedir a abertura do programa
        log(f"Aviso inesperado na atualizacao ({exc!r}). Iniciando a versao atual.", quiet)
        return 0
    finally:
        release_lock()
        if temp_dir is not None:
            shutil.rmtree(temp_dir, ignore_errors=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Auto-update oficial da Fabrica dos Cortes")
    parser.add_argument("--check", action="store_true", help="apenas verificar se ha atualizacao")
    parser.add_argument("--dry-run", action="store_true", help="baixar e validar sem aplicar")
    parser.add_argument("--force", action="store_true", help="ignorar bloqueios (dev/porta/NO_UPDATE)")
    parser.add_argument("--quiet", action="store_true", help="nao imprimir no console")
    return parser


def main(argv: list[str] | None = None) -> int:
    return run(build_parser().parse_args(argv))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)

FORJA LICENSE (POSTGRES + CREDITOS)

Arquivos principais:
- license_server.py     -> FastAPI + PostgreSQL, débito/refund idempotente
- railway.toml          -> comando de deploy Railway
- start_server_pg.bat   -> inicia o servidor localmente
- requirements_license_pg.txt

Como rodar (local):
1) pip install -r requirements_license_pg.txt
2) Configure por secrets (nunca grave no BAT/Git):
   - DATABASE_URL (PostgreSQL persistente)
   - FORJA_PRIVATE_KEY_B64 (seed Ed25519 de 32 bytes)
   - ADMIN_TOKEN (aleatório, mínimo 32 caracteres)
   - DB_POOL_MAX (opcional, 2 a 30; compatibilize com o limite de conexões do PostgreSQL)
3) Execute start_server_pg.bat

Testes:
- http://127.0.0.1:8787/health
- O painel HTML antigo não aceita segredo na URL. Use a API administrativa com o header `x-admin-token`.
- O app valida em `/api/license/check`, consome em `/api/license/consume` com `operation_id` e liquida em `/api/license/refund`; o alias `/refund_n` permanece para testes locais.
- `/admin/api/credits/add` exige token e `operation_id`; repetir a mesma operação não duplica o crédito.

As tabelas de operações são criadas por migração idempotente no startup. Faça backup do PostgreSQL antes do primeiro deploy desta versão.

Teste de concorrência (apenas em servidor de teste local, nunca produção):
  set FORJA_TEST_SERVER_URL=http://127.0.0.1:8787
  set ALLOW_LICENSE_MUTATION_TESTS=YES
  set ADMIN_TOKEN=<token-local-forte>
  python tests/license_concurrency_smoke.py

Para o staging, gere um par separado com `python generate_keys.py`; guarde a chave privada somente em `.env.staging.local` e informe a chave pública para atualizar o cliente de teste. Não reutilize o par antigo que constava nos BATs.

**Rotação obrigatória:** tokens administrativos e duas chaves privadas de assinatura apareceram em BATs antigos deste repositório. Gere uma chave Ed25519 nova, atualize os clientes para confiar na nova chave pública, troque `FORJA_PRIVATE_KEY_B64` e `ADMIN_TOKEN` nos secrets do Railway e invalide os valores anteriores. Os valores antigos também continuam no histórico Git: remova-os do histórico após coordenar a rotação e force-push apenas com aprovação do mantenedor.

# PLAN — forjaviral-site (Next.js App Router)

## 1. Estado atual (explorado)
- `forjaviral-main` (raiz) é uma ferramenta Python: CLI (`main_improved.py`) + WebUI Gradio (`webui/app.py`) + scripts de processamento de vídeo.
- `license-server/` é FastAPI + SQLAlchemy (SQLite) com Stripe. serve como referência de padrão (models, webhooks, admin por header secret).
- Não há Next.js/React no repo. Node/npm não estão instalados nesta máquina (arquivos são deliverables).

## 2. Decisão de arquitetura
Criar `site/` como projeto Next.js separado, App Router, TypeScript strict, Tailwind, Prisma (SQLite por default, PostgreSQL opcional). Não toca no projeto Python existente.

## 3. Stack
- Next.js 14 App Router, TypeScript strict
- Tailwind CSS + custom design tokens (laranja/preto)
- Prisma ORM (SQLite default)
- React Hook Form + Zod
- Lucide React
- Sem NextAuth: auth mínima por cookie HTTP-only + HMAC para admin, com placeholder para clerk/next-auth depois.
- AbacatePay: abstração em `lib/integrations/abacatepay.ts` com tipos baseados em dados mínimos e comments indicando endpoints reais.
- E-mail: Resend/Nodemailer opcional (`lib/email.ts`), desativado se sem credenciais.

## 4. Páginas
`/`, `/precos`, `/checkout`, `/retorno`, `/acesso`, `/admin`, `/termos`, `/privacidade`, `/contato`, `/faq`

## 5. APIs
- GET /api/plans
- POST /api/checkout/create-session
- GET /api/orders/[id]/status
- GET /api/access/[token]
- POST /api/webhooks/abacatepay
- POST /api/admin/login
- GET /api/admin/orders, /subscriptions, /customers, /credentials, /webhooks
- POST /api/admin/orders/[id]/activate, /credentials/[id]/revoke, /credentials/[id]/regenerate

## 6. Banco (Prisma)
Planos, Customers, Orders, Subscriptions, AccessCredentials, WebhookEvents, AuditLogs.

## 7. Fluxo de compra
escolha plano -> dados -> order no banco -> checkout AbacatePay -> webhook -> ativa assinatura -> job gera credenciais -> /acesso mostra link/usuario/senha/token.

## 8. Provisionamento
`lib/provisioning.ts`: gera usuario, senha forte (hash argon2/bcrypt), access token one-time (hash, expiração), accessUrl = RAILWAY_APP_URL. Opcional `APP_PROVISION_URL` com HMAC para chamar API interna do app.

## 9. Segurança
HMAC webhook, idempotência por eventId, rate limiting, Zod em toda input, tokens one-time, hashes, rate limit, LGPD básico.

## 10. Testes
scripts node para mockar AbacatePay: criar order, webhook paid ativa, credencial única, token expirado bloqueia, cancelamento revoga.

## 11. Entrega
arquivos em `site/`, .env.example, README, seed de planos + admin.
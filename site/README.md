# forjaviral-site

Site de vendas e assinatura para **Forja Viral** — ferramenta de cortes com IA.

Stack: Next.js 14 (App Router) · TypeScript strict · Tailwind · Prisma · AbacatePay.

## Estrutura

```
site/
├── app/                  # Rotas (App Router)
│   ├── api/              # API routes
│   ├── (marketing)/      # Páginas públicas
│   ├── (auth)/           # Admin
│   └── globals.css
├── components/           # UI components
├── lib/                  # Camadas de domínio
│   ├── db.ts             # Prisma client
│   ├── auth.ts           # Admin auth
│   ├── abacatepay.ts     # Integração AbacatePay
│   ├── provisioning.ts   # Geração de credenciais
│   ├── railway.ts        # Integração Railway/app
│   ├── email.ts          # E-mail (Resend)
│   ├── ratelimit.ts      # Rate limiting
│   └── utils.ts          # Helpers
├── prisma/
│   └── schema.prisma     # Schema do banco
├── scripts/
│   └── seed.ts           # Seed de planos + admin
└── public/
```

## Setup local

```bash
cd site
cp .env.example .env
# Preencha .env com suas credenciais
npm install
npx prisma db push
npm run db:seed
npm run dev
# Acesse http://localhost:3000
```

## Configurar AbacatePay

1. Crie uma conta em [abacatepay.com](https://abacatepay.com).
2. Gere uma API Key no painel.
3. Cole em `ABACATEPAY_API_KEY`.
4. Copie o Webhook Secret em `ABACATEPAY_WEBHOOK_SECRET`.
5. Configure a URL de retorno em `ABACATEPAY_RETURN_URL`.
6. Mapeie os planos em `ABACATEPAY_PLAN_IDS` (JSON com slug -> planId).

## Configurar Railway

1. A ferramenta deve estar hospedada em `RAILWAY_APP_URL`.
2. Se a ferramenta tiver API de provisionamento, configure `APP_PROVISION_URL` e `APP_PROVISION_SECRET`.

## Testar webhook localmente

```bash
# Use o ngrok para expor localhost
ngrok http 3000

# No painel da AbacatePay, aponte o webhook para:
https://<ngrok-url>/api/webhooks/abacatepay

# Para testes manuais, use o script em scripts/test-webhook.ts
npm run test:webhook
```

## Admin

```bash
POST /api/admin/login
Body: {"email": "ADMIN_EMAIL", "password": "ADMIN_PASSWORD"}
# Use o cookie retornado para acessar /admin
```

## Seed

```bash
npm run db:seed
```

Cria planos (mensal, trimestral, anual) e o admin.

## Testes

```bash
npm test
```

## Deploy

```bash
npm run build
npm start
# ou use Railway/Vercel
```

## Variáveis de ambiente

Veja `.env.example` para a lista completa.
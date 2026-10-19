import { CheckCircle2, XCircle, Zap, TrendingDown } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

const COMPARISON_ROWS = [
  {
    feature: 'Preço por vídeo cortado',
    forja: 'A partir de R$ 0,55',
    opus: 'Aprox. R$ 3,80 a R$ 5,00',
    submagic: 'Aprox. R$ 6,00+',
    highlight: true,
  },
  {
    feature: 'Modelo de cobrança',
    forja: 'Créditos avulsos via Pix (Sem mensalidade)',
    opus: 'Assinatura mensal presa no cartão de crédito',
    submagic: 'Assinatura em dólar com IOF de 4,38%',
    highlight: true,
  },
  {
    feature: 'Se não usar no mês corrente?',
    forja: 'Seus créditos continuam válidos por 365 dias',
    opus: 'Seus minutos são apagados e você perde o dinheiro',
    submagic: 'Seus créditos expiram todo mês',
    highlight: true,
  },
  {
    feature: 'Legendas dinâmicas estilo Hormozi',
    forja: 'Calibradas em Português-BR com emojis e destaque',
    opus: 'Genéricas em inglês com tradução mecânica',
    submagic: 'Estilo próprio mas limitada em pacotes básicos',
    highlight: false,
  },
  {
    feature: 'Enquadramento automático Face Crop (9:16)',
    forja: 'Sim, rastreia e centraliza o rosto de quem fala',
    opus: 'Sim, mas corta partes de 2 convidados',
    submagic: 'Limitado dependendo do plano',
    highlight: false,
  },
  {
    feature: 'Onde você pode executar?',
    forja: 'No seu próprio PC com GPU ou no Google Colab Nuvem',
    opus: 'Apenas no navegador (fila de espera do servidor)',
    submagic: 'Apenas no navegador web',
    highlight: false,
  },
  {
    feature: 'Exportação XML (Premiere / DaVinci)',
    forja: 'Sim, exporta projeto aberto com áudio e cortes separados',
    opus: 'Não, só entrega vídeo MP4 já renderizado',
    submagic: 'Não, vídeo MP4 fechado',
    highlight: true,
  },
  {
    feature: 'Suporte e Atendimento',
    forja: 'WhatsApp direto em Português do Brasil',
    opus: 'Ticket por e-mail em inglês (dias de espera)',
    submagic: 'Chatbot em inglês',
    highlight: false,
  },
];

export function ComparativoSection() {
  return (
    <section className="border-b border-border py-20 relative overflow-hidden bg-surface/40">
      <div className="relative mx-auto w-full max-w-6xl px-4">
        <div className="text-center space-y-3 mb-14">
          <Badge variant="brand" className="mb-2">
            <TrendingDown className="h-3.5 w-3.5 mr-1" /> Comparativo Real de Mercado
          </Badge>
          <h2 className="font-display text-3xl sm:text-4xl lg:text-5xl font-extrabold text-text-primary">
            Por que a <span className="text-brand">Forja Viral</span> humilha as ferramentas gringas?
          </h2>
          <p className="text-text-secondary max-w-2xl mx-auto text-sm sm:text-base">
            Compare você mesmo: ferramentas como Opus Clip e Submagic cobram caro em dólar e apagam seus minutos se você não usar no mês.
          </p>
        </div>

        {/* Tabela Comparativa Desktop */}
        <div className="overflow-x-auto rounded-3xl border border-border/80 bg-surface/90 shadow-2xl backdrop-blur-md">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-surface-elevated/70 text-xs uppercase tracking-wider text-text-secondary">
                <th className="py-4 px-6 font-bold">Funcionalidade / Vantagem</th>
                <th className="py-4 px-6 font-extrabold text-brand bg-brand/10 border-x border-brand/20">
                  <div className="flex items-center gap-1.5">
                    <Zap className="h-4 w-4 text-brand" /> Forja Viral (Brasil)
                  </div>
                </th>
                <th className="py-4 px-6 font-semibold">Opus Clip (Gringo)</th>
                <th className="py-4 px-6 font-semibold">Submagic (Gringo)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {COMPARISON_ROWS.map((row, idx) => (
                <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                  <td className="py-4 px-6 font-medium text-text-primary">
                    {row.feature}
                  </td>
                  <td className="py-4 px-6 bg-brand/5 border-x border-brand/20 font-bold text-text-primary">
                    <div className="flex items-center gap-2 text-emerald-400">
                      <CheckCircle2 className="h-4 w-4 shrink-0 text-brand" />
                      <span className="text-text-primary">{row.forja}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-text-secondary">
                    <div className="flex items-center gap-2">
                      <XCircle className="h-4 w-4 shrink-0 text-error/70" />
                      <span>{row.opus}</span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-text-secondary">
                    <div className="flex items-center gap-2">
                      <XCircle className="h-4 w-4 shrink-0 text-error/70" />
                      <span>{row.submagic}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Banner Inferior */}
        <div className="mt-8 rounded-2xl border border-brand/30 bg-gradient-to-r from-brand/15 via-surface to-brand/15 p-5 text-center flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-left">
            <span className="text-xs uppercase tracking-wider font-bold text-brand block">Economia Comprovada</span>
            <p className="text-sm font-semibold text-text-primary">
              Com o valor de 1 único mês do Opus Clip (R$ 150), você compra mais de <strong>200 cortes na Forja Viral</strong> que duram 1 ano inteiro.
            </p>
          </div>
          <a href="#planos" className="shrink-0 inline-flex items-center justify-center rounded-xl bg-brand px-6 py-2.5 text-xs font-bold text-white shadow-lg shadow-brand/20 hover:bg-brand/90 transition-all">
            Ver Pacotes no Pix →
          </a>
        </div>
      </div>
    </section>
  );
}

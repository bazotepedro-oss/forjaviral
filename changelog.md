# Changelog

## 1.3.22 - atalho sem cmd

### Quantidade de cortes

- Pedir 10 cortes e receber 9 nao acontece mais. Quando a IA entrega menos do que o solicitado, o aplicativo pede os cortes que faltam automaticamente e junta com os ja aprovados.
- O prompt principal agora pede exatamente a quantidade solicitada, usando os proximos melhores momentos completos quando nao houver tantos picos.
- A cobranca continua sendo feita apenas sobre os cortes realmente entregues.



### Correcoes
- O atalho nao abre mais nenhuma janela de cmd. O Windows Terminal abria uma janela mesmo com o modo oculto quando o alvo era um arquivo .bat.
- O lancador oculto agora chama direto o pythonw (atualizacao) e o powershell oculto (bandeja), sem passar por cmd.exe.
- Se o aplicativo ainda nao estiver instalado, aparece uma caixa de aviso em vez de uma janela preta vazia.

## 1.3.21 - inicio 100% oculto

### Correcoes
- O atalho da Area de Trabalho nao abre mais janela de console nem item de PowerShell na barra. Ele inicia o aplicativo por um lancador oculto (wscript + VBS).
- O aviso de que o servidor nao iniciou aparecia cedo demais na primeira execucao. O tempo de espera subiu de 90 para 180 segundos, porque a primeira abertura carrega Gradio, CUDA e os modelos.
- Se a porta abrir depois do tempo, a bandeja reconhece o servidor em vez de mostrar erro.

## 1.3.20 — Diagnóstico e recuperação do servidor

### Correções
- O iniciador agora grava toda a saída do servidor em `logs\app.log`, inclusive falhas nativas.
- Cada geração também cria um log detalhado em `logs\render_*.log`, com a saída do FFmpeg e do processamento.
- Se o servidor encerrar inesperadamente, o iniciador reinicia automaticamente (até 3 tentativas) em vez de deixar o navegador sem conexão.
- Aviso na janela do terminal para não fechá-la durante a geração.
- O app bloqueia a geração quando há menos de 600 MB de memória livre e orienta fechar o navegador/outros programas.
- **Prompt do Melhores Momentos separado do prompt dos cortes**: agora existe um prompt próprio para compilados longos (`prompt_best_moments.txt`) e um prompt de resgate próprio. Os cortes curtos continuam usando o `prompt.txt` de sempre.
- **Bandeja do Windows**: o app inicia sem deixar o CMD aberto. O ícone fica na área de notificação (setinha) com menu para abrir, abrir logs, reiniciar o servidor ou sair. O servidor é reiniciado automaticamente se cair.

### Licença sem HWID

- As chaves deixaram de ficar presas a um computador. A validação de HWID foi removida do servidor de licenças: a mesma chave funciona em qualquer PC, sem pedir liberação.
- Nenhuma ação é necessária para as chaves já emitidas. Elas passam a funcionar em outra máquina automaticamente.
- O HWID continua aparecendo no painel apenas como informação histórica; ele não bloqueia mais nada.

### Correções no erro "sem segmentos virais"

- O prompt dos cortes deixou de exigir um pico de emoção em todo corte. Agora são aceitos quatro tipos de momento: emoção, conflito, insight e história completa. Explicações calmas e opiniões bem argumentadas passaram a valer.
- O prompt passou a instruir a IA a nunca devolver lista vazia quando existir pelo menos uma ideia completa na transcrição.
- O modo de resgate agora varre a transcrição inteira em janelas, em vez de olhar apenas os primeiros 180 mil caracteres. O final de podcasts longos passou a ser analisado.
- Criado um segundo nível de resgate, mais permissivo, usado quando o primeiro não encontra nada ou quando os candidatos não passam na validação.
- O resgate tem orçamento de tempo próprio e não é mais cancelado pelo limite global da análise.
- Todas as chamadas de resgate gravam prompt e resposta em `logs\ai_*.txt`, para diagnóstico.
- Corrigido um laço que podia travar a análise quando o tamanho de bloco era pequeno: o overlap agora nunca passa da metade do bloco.
- A mensagem final de erro agora mostra o motivo real da falha e indica a pasta de logs, em vez de apenas "nenhum segmento viral".
- Padronizado o limite de duração do compilado em 300 segundos entre o prompt e a validação (antes a validação usava 240).

## 1.3.19 — Marca d'água e vídeo da ferramenta

### Novidades
- **Marca d'água opcional** no canto superior direito dos cortes e dos Melhores Momentos.
- **Vídeo da ferramenta no final**: o encerramento de 11,8 s é anexado automaticamente ao fim de cada vídeo.
- As duas opções aparecem em **Criar Cortes** e em **Melhores Momentos**, ativadas por padrão e podem ser desligadas antes de gerar.
- Nos cortes verticais, a marca é aplicada antes da legenda queimada, então continua visível mesmo depois de editar o estilo da legenda na Biblioteca.
- Nos compilados 16:9, o encerramento vertical é centralizado sobre um fundo desfocado do próprio vídeo, sem barras pretas.
- O encerramento entra depois dos momentos e antes do fim do arquivo, com fade suave.

## 1.3.18 — Instalador corrigido em pastas do usuário

### Correções
- O instalador agora usa `requirements.txt` e `constraints.txt` **relativos à pasta do aplicativo**, com o Python do `.venv` informado explicitamente. Isso evita o erro `File not found: C:\Users\...` durante a instalação.
- Antes de instalar as dependências, o instalador confere se os dois arquivos existem e mostra o caminho completo se faltar algum.
- Se o `.venv` tiver sido copiado de outro PC ou estiver inválido, ele é recriado automaticamente em vez de reaproveitar um ambiente quebrado.
- O log do passo 6 mostra a pasta do app e os caminhos usados, facilitando o suporte.

## 1.3.17 — Pacote de fontes, instalador e feedback do compilado

### Novidades
- **Pacote com 44 fontes**: Montserrat, Poppins, Bebas Neue, Anton, Oswald, Barlow Condensed, Archivo Black, League Spartan, Teko, Kanit, Prompt, Exo 2, Orbitron, Righteous, Russo One, Black Ops One, Bungee, Bangers, Titan One, Passion One, Alfa Slab One, Inter, Roboto Condensed, Raleway, Rubik, Nunito, Lato, Open Sans, Source Sans 3, Manrope, Sora, Space Grotesk, Outfit, DM Sans, Work Sans, Plus Jakarta Sans, Urbanist, Figtree, Cabin, Caveat, Dancing Script, Great Vibes, Pacifico e Lobster.
- O instalador registra as fontes no Windows para o usuário atual, sem precisar de administrador. O atualizador e o iniciador também garantem o pacote.
- As fontes ficam disponíveis no seletor da Biblioteca e no preview, e o FFmpeg usa a pasta de fontes do app para queimar a legenda.
- O site oficial ganhou uma seção dedicada aos Melhores Momentos, com detalhes do compilado, preços e novas perguntas frequentes.

### Correções
- **Botão de compilado com feedback imediato**: ao clicar, aparece na hora um cartão de progresso com etapa, porcentagem e barra animada — sem textos duplicados sobre o player ou os metadados.
- O progresso agora acompanha de verdade a análise da IA e a renderização do FFmpeg, quadro a quadro, até 100%.
- Em caso de falha, o status mostra o erro e devolve os 10 créditos.
- Removida a cópia antiga `scripts/app.py`, que não era usada e continha o endereço interno do servidor.

## 1.3.16 — Fontes reais, contorno e molduras

### Interface
- **Fontes embutidas**: Montserrat, Poppins, Bebas Neue e Anton agora vão junto com o app, no preview e na renderização do vídeo. A fonte muda de verdade ao selecionar.
- **Espessura do contorno**: novo controle de 0 a 10 px, refletido no preview e na legenda queimada.
- **Moldura do estilo**: o seletor “Estilo de legenda” agora tem uma caixa visível, deixando claro que é clicável.
- **Previews sem borda preta**: o corte selecionado e a prévia de música ficaram em molduras escuras próprias, com o vídeo 9:16 enquadrado sem tarjas pretas.
- Player do corte selecionado um pouco maior, com a legenda aplicada mais visível.
- Fundo da prévia de música no mesmo tom dos cards, sem moldura preta.

## 1.3.15 — Biblioteca: ícones, prévia de legenda e música

### Interface
- **Ícones nos acordeões**: legenda, música, metadados e zona de risco agora têm ícone e título alinhado à esquerda.
- **Seletor de fonte**: o campo de texto "Montserrat-ExtraBold" virou uma seleção de fontes.
- **Prévia de legenda ao vivo**: mostra fonte, tamanho, cores, contorno, modo e maiúsculas antes de aplicar.
- **Espaçamento da legenda** ajustado: linhas, cores e botão de aplicar mais equilibrados.
- **Música repaginada**: player escuro próprio com play, barra de progresso, tempo e mute; volume e ducking alinhados.
- **Status de carregamento**: a prévia e a aplicação de música mostram uma barra animada com o que está sendo feito; o texto solto de "prévia pronta" foi removido.
- **Prévia de 30s** em card compacto, em vez do player preto gigante.

## 1.3.14 — Cortes longos, contexto completo e transições

### Mudanças
- **Cortes de 60 s a 5 min**: a IA agora é instruída a devolver poucos momentos longos e completos, com começo, explicação, exemplos e conclusão. Nada de fragmentos de 20–40 s.
- **Mesmo assunto = um corte**: partes próximas da mesma explicação são unidas em um único momento, em vez de vários cortes pequenos.
- **Transição em cada corte**: fade suave de 0,25 s para preto na saída e entrada do próximo corte, com áudio acompanhando.
- **Compilado de referência**: 17 cortes, de 1,9 a 5 min cada, total de **52,2 minutos**.
- O compilado anterior de cortes pequenos foi apagado e refeito.

## 1.3.13 — Compilado automático, cortes completos e link do podcast

### Novidades
- **Duração automática**: o campo de minutos começa em **0 = automático**, usando todos os melhores momentos que a IA encontrar. Acima de 0, o compilado tenta chegar à duração pedida.
- **Sempre abre com o melhor momento**: o botão de cold open foi removido; a melhor nota sempre abre o vídeo.
- **Baixar pelo link**: cole o link do YouTube na aba Melhores Momentos para baixar e transcrever o podcast sem passar pela aba Criar Cortes.
- **Extração máxima**: a IA agora é instruída a devolver o máximo de momentos completos, sem parar no meio de uma explicação, argumento ou história. Cada corte pode chegar a 4 minutos quando a ideia precisa.
- **Compilados longos**: a seleção automática usa todos os momentos com nota boa, sem o limite fixo de 5 ou 10 minutos.

### Correções
- Checagem de espaço em disco antes de renderizar compilações automáticas muito longas.
- O último compilado automático é carregado automaticamente na aba; se não houver, o último compilado fixo é usado.
- Links de download não passam pelo cache do Gradio, evitando cópias de centenas de MB.

## 1.3.12 — Melhores Momentos, licença discreta e correção da IA

### Novidades
- **Aba Melhores Momentos**: analisa o podcast inteiro, escolhe os melhores trechos e monta um compilado horizontal de **5 ou 10 minutos** para o YouTube.
- **Entrega completa**: MP4 em 1920×1080, 16:9, 30 FPS, H.264 e áudio AAC 192 kbps, com aceleração `h264_nvenc` e fallback automático para `libx264`.
- **Legendas e capítulos**: SRT sincronizado e descrição com capítulos prontos para colar no YouTube.
- **Custo fixo de 10 créditos**: o saldo é reservado antes, debitado só depois da entrega e devolvido integralmente em caso de falha.
- **Prévia e downloads** do MP4 e do SRT direto na aba.
- **Último compilado**: ao abrir a aba, o compilado de 10 min mais recente é carregado com player, capítulos e links de download.

### Correções
- **IA perdia dezenas de candidatos**: um tratamento de escapes corrompia JSON válido e reduzia 39 momentos a 3. O compilado agora aproveita todos os candidatos retornados.
- **Seleção sem repetição**: o compilador evita sobreposição de tempo e assuntos repetidos, prioriza picos de emoção e abre com o melhor momento.
- **Duração confiável**: a seleção é ajustada para perto de 5/10 minutos e o vídeo é validado em resolução, FPS e duração antes de confirmar a cobrança.
- **Licença sem servidor exposto**: a aba mostra apenas a chave e o botão de ativação; o endereço do serviço ficou interno.
- **Opções técnicas ocultas** para o cliente: backends, modelos, chunk size, configurações de rosto e logs não aparecem mais na interface.
- **Biblioteca mais equilibrada**: cards maiores, miniatura como poster do player, destaque do card selecionado e botões alinhados em duas colunas.
- **Música**: prévia de 30 s, volume, ducking e aplicação ao corte com backup automático; suporte a M4A.

## 1.3.11 — Biblioteca: cards, clique no corte e reload do player

### Correções
- **Vídeo não trocava ao mudar de corte**: o HTML atualizava a fonte, mas o `<video>` não recarregava. Um observador em JS chama `load()` quando a fonte muda.
- **Clique no card da galeria** seleciona o corte, atualiza o player e os metadados.
- **Parte de baixo repaginada**: legenda, música, metadados e zona de risco agora são cards com cabeçalho, no mesmo estilo do resto do app (sem accordions gigantes).
- **Seleção por dropdown** também recarrega o player e atualiza título/descrição/hashtags.

## 1.3.10 — Player da Biblioteca corrigido

### Correções
- **Vídeo não reproduzia (NaN:NaN)**: o componente de vídeo do Gradio falhava com os cortes verticais. O painel "Corte selecionado" agora usa um player HTML5 próprio, apontando para o mesmo arquivo da galeria.
- **Prévia de música** também usa o player próprio, com o mesmo comportamento.
- **Visual do player**: cantos arredondados, borda sutil, limite de altura e sombra no padrão dos cards.
- O título "Corte selecionado" ficou em caixa alta com espaçamento, como cabeçalho de seção.

## 1.3.9 — Biblioteca repaginada e música com prévia

### Interface
- **Biblioteca em duas colunas**: galeria à esquerda (3 cards por linha) e corte selecionado fixo à direita, com player e ações.
- **Seletor de cor corrigido**: o CSS sobrescrevia o fundo do seletor e ele ficava sempre branco. Agora mostra a cor real e aplica no vídeo.
- **Controles no padrão do menu**: swatches grandes (46px), sliders laranja, botões e dropdowns consistentes.

### Música
- **Lista de músicas** com player para ouvir a faixa escolhida.
- **Prévia de 30s mixada com o vídeo** antes de aplicar, com volume e ducking.
- **Upload** de mp3/wav/m4a direto na Biblioteca.
- **Aplicar música** re-mixa o corte com backup automático.

### Legenda
- **Aplicar em todos os cortes** de uma vez.
- Prévia do corte atualiza depois de aplicar (URL com cache-bust).

## 1.3.8 — Biblioteca de cortes

### Novidades
- **Aba Biblioteca**: galeria dos cortes prontos, com player, miniatura automática, título, nota e hashtags.
- **Ações por corte**: aprovar, reprovar (feedback salvo), renomear, apagar corte e baixar ZIP com vídeos, legendas e metadados.
- **Renomear/telemetria**: título atualizado no `viral_segments.txt`; feedback guardado em `feedback.json`.
- **Editar legenda depois de pronto**: presets e controles de fonte, tamanho, cores, contorno, posição e modo; re-queima só o corte, com backup automático do vídeo anterior.
- **Música**: catálogo em `music/`, upload do cliente, volume e ducking automático na voz (a música abaixa quando alguém fala).
- **Metadados**: título, descrição e hashtags prontos para colar no YouTube.

### Prompt
- **Pico de emoção obrigatório**: risada, choque, aplauso, confissão, reviravolta ou discordância dentro do corte, com payoff no final.
- **Campo `emotion`**: classifica o corte em laughter, shock, emotion, conflict, revelation ou inspiration.
- **Estrutura de referência**: hook (0-3s), setup, escalada e payoff nos últimos segundos, sem explicação depois.

## 1.3.7 — YouTube no Colab e cookies

### Correções
- **Bloqueio "Sign in to confirm you're not a bot"**: o download agora tenta os clientes alternativos do YouTube (`tv`, `android_vr`, `web_safari`, `mweb`) antes de desistir, em vez de procurar cookies de navegadores que não existem no Colab.
- **Cookies.txt no Colab**: nova célula 2B no notebook envia o `cookies.txt` exportado do navegador, salva no Drive e inicia o app com `--cookies-file`.
- **Mensagem clara**: quando o YouTube exige verificação, o log explica o que fazer em vez de terminar com erro de cookie do navegador.
- **Windows/macOS**: continua tentando os cookies dos navegadores locais automaticamente.

## 1.3.6 — PyTorch travado e GPU validada

### Correções
- **Stack do PyTorch travado**: `constraints.txt` agora fixa `torch/torchvision/torchaudio 2.5.1`, `pyannote-audio 3.4.0`, `transformers 4.48.0`, `whisperx 3.4.5` e `numpy 2.0.2`. Sem isso, o passo de dependências trocava o PyTorch CUDA pelo 2.14.1 CPU do PyPI e quebrava o `torchaudio` do pyannote.
- **Instalação das dependências com constraints**: o `INSTALADOR` passa `-c constraints.txt`, então o PyTorch escolhido (GPU ou CPU) não é substituído.
- **Verificação de GPU**: no modo GPU, o instalador confere `torch.cuda.is_available()`, reinstala o build CUDA se precisar e avisa para escolher o modo CPU em PCs sem placa NVIDIA.

## 1.3.5 — Dependências resolvidas de vez

### Correções
- **Transformers 4.48.0**: atende a exigência do WhisperX 3.4.5 (`>=4.48`) e continua funcionando com o PyTorch 2.5.1 CUDA 12.1. As versões 5.x desativavam o PyTorch e quebravam o alinhamento palavra por palavra.
- **Resolução completa validada**: o `requirements.txt` foi testado com o resolvedor antes da publicação; a única mudança é o CTranslate2 voltar para 4.4.0, e o instalador o atualiza para 4.8.4 logo depois com `--no-deps`.
- **Instalação limpa**: o passo 6.1 garante CTranslate2 4.5+ e a verificação final confere Gradio, WhisperX, PyTorch e CTranslate2.

## 1.3.4 — Instalação compatível e atualização pelo .bat

### Correções
- **Conflito de versões resolvido**: o instalador fixa WhisperX 3.4.5 e Transformers 4.46.3, que funcionam com o PyTorch 2.5.1 CUDA 12.1. O CTranslate2 4.8.4 é instalado num passo separado, sem conflitar com o WhisperX.
- **Alinhamento de legendas de volta**: o Transformers 5.x desativava o PyTorch e quebrava o alinhamento palavra por palavra; a versão fixada mantém o Wav2Vec2 funcionando.
- **Instalador rápido sempre baixa**: o `INSTALAR_FABRICA_DE_CORTES.bat` agora baixa a versão mais recente em toda execução e atualiza os arquivos, preservando `VIRALS`, modelos e a chave Gemini.
- **Verificação final** confere Gradio, WhisperX, PyTorch e CTranslate2 4.5+ antes de declarar sucesso.

## 1.3.3 — Instalação à prova de falha

### Correções
- **Instalador honesto**: agora ele para na primeira etapa que falhar e mostra o motivo, em vez de exibir "instalação concluída" mesmo com dependências faltando.
- **Verificação real no final**: só declara sucesso se `gradio`, `whisperx` e `torch` importarem de verdade dentro do `.venv`.
- **Reparo automático ao abrir**: o `INICIAR_FABRICA_DE_CORTES.bat` confere o Gradio antes de subir o app e chama o instalador sozinho quando a instalação estiver incompleta.

## 1.3.2 — Interface nova e cortes consistentes

### Interface
- **Nova interface no estilo Opus**: barra lateral com ícones, abas Licença/Criar Cortes, hero com a logo, cards escuros com detalhes laranja e botão grande de gerar.
- **Tela mais limpa**: Editor de Legendas e Biblioteca saíram da interface; o backend ficou fixo em Gemini e o Modo viral passou a ficar sempre ativo.
- **Console recolhido**: os logs ficam em "Detalhes técnicos" e a barra de progresso mostra a etapa e a porcentagem.

### Cortes
- **Candidatos extras**: a IA agora gera mais opções do que o pedido (pedir 4 gera 7, pedir 5 gera 9) e o app entrega apenas os melhores, evitando entregar menos cortes quando há sobreposição.
- **Fim do colapso dos cortes**: legendas automáticas sem pontuação faziam o vídeo inteiro virar um único bloco, e todos os cortes apontavam para 0 – duração total. Agora os blocos são limitados e cada corte fica no trecho certo.
- **Duração correta**: cortes com mais de 1000s não são mais tratados como milissegundos (um corte de 77s não vira 6s).
- **Timestamps flexíveis**: referências em `1:02:45` agora são interpretadas corretamente.
- **Hook de verdade**: o campo `hook` recebe a primeira frase falada no corte, não o título. O título fica separado e a nota é real, validada entre 0 e 100.

### IA, GPU e legendas
- **Gemini atualizado**: modelo padrão `gemini-2.5-flash`, com troca automática de modelo quando a API responde 404 ou 429 (em vez de esperar minutos no mesmo modelo).
- **Transcrição na GPU corrigida**: CTranslate2 4.8.4 com o cuDNN que acompanha o PyTorch, além de fallback automático para CPU.
- **Idioma da legenda**: a detecção não confunde mais nomes como "Inteligência" com inglês; vídeos em português são alinhados com o modelo em português.
- **Legendas completas**: como o corte começa em frase completa, a primeira legenda também começa inteira.

### Créditos
- **Devolução confirmada**: corrigido o erro de contexto do Gradio que impedia confirmar a devolução de créditos e derrubava a resposta final do processamento.

## 1.3.1 — Cortes completos e erro claro da IA

### Correções
- **Fim do modo de segurança aleatório**: quando a IA falhava, o app gerava cortes fixos com notas 95/92/89. Agora ele não gera vídeos desconexos; mostra o motivo e preserva os créditos.
- **Cortes em frases completas**: o início e o fim de cada corte são ajustados para limites de frase, evitando começar/terminar no meio do assunto.
- **Título completo no card**: o título não é mais cortado em duas linhas; as hashtags ficam separadas e o texto completo aparece.
- **Prompt mais rígido**: a IA agora precisa devolver `start_text`/`end_text` de frases completas, `end_time_ref`, título curto sem hashtags e campo `hashtags` separado.
- **Aviso de chave**: se a chave Gemini não estiver configurada, o app avisa claramente em vez de gerar cortes falsos.
- **Correção do `api_config.json`**: o arquivo agora é lido/gravado sem BOM, evitando o erro que impedia a chave Gemini de carregar.

## Fixes for Manual/Raw JSON Input

### Core Functionality
- **Raw Segment Repair**: Implemented automatic detection and repair of segments that lack timestamp information (e.g. manually crafted JSON with just reference tags). The system now recalculates start/end times using the transcript alignment logic.
- **Duration Constraint Hardening**: The timestamp alignment logic now strictly enforces the user-defined `min_duration`, effectively extending segments that the AI might have outputted as too short.

## Suporte a GGUF e Ajustes de Link

### Novidades
- **Suporte a GGUF**: colocado suporte a gguf para llm local.
- **Link Público**: ajustado diretórios de link público.

## Melhorias de Qualidade de Vídeo, Legendas e Processamento

### Novidades

- **Aprimoramento de prompt para LLM**: melhorias no prompt para permitir que o modelo de linguagem compreenda melhor o contexto do conteúdo.
- **Aprimoramento na detecção facial**: melhorias na identificação de rostos quando várias pessoas estão falando simultaneamente.
- **Seleção de Qualidade de Vídeo**: agora é possível escolher a qualidade desejada para download de vídeos (Melhor, 1080p, 720p, 480p) diretamente pela WebUI ou CLI, permitindo otimizar entre velocidade e uso de armazenamento.
- **Controle de Legendas do YouTube**: adicionada a opção de ignorar o download de legendas oficiais do YouTube, permitindo forçar uma nova transcrição via Whisper, se desejado.
- **Suporte a VTT**: o script de transcrição foi aprimorado para oferecer suporte a arquivos de legenda `.vtt` para alinhamento, garantindo maior compatibilidade.
- **Tradução de legendas em JSON com destaque palavra por palavra**: adicionada a tradução de legendas no formato JSON, permitindo highlight e sincronização word-by-word em outro idioma durante a exibição.

### Melhorias e Otimizações

- **yt-dlp mais robusto**: corrigidos problemas em que downloads de vídeo estavam sendo salvos como “Unknown_Video” e exibiam progresso incorreto. Também foram adicionados logs de progresso mais precisos e suporte aprimorado ao download de legendas.
- **Otimização de Legendas do YouTube**: quando legendas do YouTube estão disponíveis, o sistema agora faz o download automático e as utiliza apenas para alinhamento, pulando o processo pesado e demorado de transcrição. Isso acelera significativamente o processamento de vídeos que já possuem legendas.


## Active Speaker & Face Controls

### Controles Avançados de Face e Falante Ativo
- **Filtros de Face**: Controle granular para ignorar rostos pequenos, definir limite de confiança minimiza falsos positivos e "Zona Morta" para estabilizar a câmera.
- **Experimental: Active Speaker**: Novo modo experimental que tenta focar na pessoa que está falando (detecção de boca aberta e movimento), em vez de sempre dividir a tela.
- **Legendas**: Opção para remover pontuação automaticamente.

## Editor de Legenda JSON

### Funcionalidades
- **Editor de Legendas**: Adicionado um editor de legendas simples, dentro das limitações do Gradio, para corrigir erros de ortografia ocorridos durante o uso do WhisperX.

### Correções
- **Geral**: Alguns Fix Colab e melhorias na geração de viral segments.

## Gradio WebUI & UV Installation

### Nova Interface Web (Gradio)
- **OpusClip Inspired**: Nova interface gráfica construída com Gradio, inspirada no design do OpusClip, oferecendo uma experiência de usuário moderna e intuitiva.
- **Funcionalidades da UI**: Ajustes completos para garantir que todas as funcionalidades da ferramenta estejam acessíveis e operantes através da nova interface.

### Instalação e Infraestrutura
- **Instalação via UV**: Criação de script `.bat` para instalação otimizada de dependências utilizando o `uv`, acelerando o processo de setup.
- **Fixes Gerais**: Correções em diversos componentes que estavam quebrados ou instáveis, garantindo maior estabilidade na execução via UI.

## WebUI 2.0 & Enhanced Configuration

### WebUI Overhaul
- **Dark & Modern UI**: Interface completamente redesenhada com tema escuro e layout em grid responsivo (estilo Opus.pro) para a galeria de vídeos.
- **Dynamic Configuration**: Componentes da interface agora reagem dinamicamente à escolha do Backend de IA, atualizando automaticamente a lista de modelos disponíveis e o tamanho sugerido de chunk.
- **Improved Controls**: Controle granular sobre `Face Detect Interval`, `Skip Prompts`, e `Chunk Size` diretamente na interface web.
- **Refactoring**: Código da WebUI refatorado e modularizado (`library.py` separado do `app.py`) para melhor manutenção.

### Core & CLI
- **Arguments Expansion**: `main_improved.py` agora aceita argumentos de linha de comando para `--chunk-size` e `--ai-model-name`, permitindo override total da configuração.
- **Script Update**: `create_viral_segments.py` atualizado para respeitar os parâmetros passados via CLI, priorizando-os sobre o arquivo de configuração.

## Fix 2 faces

### Melhorias na Detecção Facial e Layout
- **Consistência Visual (2 Faces)**: Implementada lógica para "travar" a identidade dos rostos nas posições superior e inferior, impedindo que os participantes troquem de lugar durante o vídeo.
- **Lógica de Fallback Inteligente**: Caso o rosto não seja detectado no frame atual, o sistema agora tenta recuperar a posição baseada no frame anterior, posterior ou na última coordenada válida conhecida.
- **Intervalo de Detecção Personalizável**: Adicionada configuração para o usuário escolher a frequência da varredura facial, permitindo otimizar o tempo de renderização.

### Correções de Legendas
- **Correção de Sobreposição**: Resolvido bug onde legendas apareciam sobrepostas em momentos de fala rápida.
- **Refinamento de Centralização (2 Faces)**: Ajustes adicionais no cálculo de posição para garantir que a legenda fique perfeitamente centralizada no modo dividido.

## Atualizações Anteriores

### Refatoração e Melhorias de Código
- **Refatoração do Script Principal**: Criação e aprimoramento do `main_improved.py` para melhorar a estrutura e manutenibilidade do pipeline de processamento.
- **Padronização de Código (Inglês)**: Tradução completa de nomes de variáveis, funções e comentários internos para inglês, visando compatibilidade com padrões internacionais e colaboração open-source, mantendo logs de saída com suporte a i18n (`en_US`/`pt_BR`).
- **Ajuste de Diretórios**: Reorganização da estrutura de pastas e caminhos de saída para maior organização dos arquivos gerados.

### Configuração e IA
- **Integração Multi-LLM**: Implementação de suporte ao **g4f** (GPT-4 Free) e **Google Gemini**.
- **API Config**: Centralização das chaves e seleção de modelos no novo arquivo `api_config.json`, permitindo troca rápida de provedor de IA sem alterar o código.
- **Gerenciamento de Prompts**: Criação do arquivo `prompt.txt` para edição fácil do prompt do sistema.

### Legendas e Transcrição (Whisper)
- **Correções no Whisper**: Solução robusta para erros de `unpickling`, conflitos de DLLs (`libprotobuf`, `torchaudio`) e detecção de GPU.
- **Otimização do Fluxo (Slicing)**: O vídeo original é transcrito apenas uma vez. Os cortes reutilizam o JSON original, eliminando a re-transcrição e acelerando o processo.
- **Posicionamento de Legendas**: Correção da lógica de alinhamento para centralização no modo "2-face".

### Processamento de Vídeo e Detecção Facial
- **Novo Motor: InsightFace**: Adição da biblioteca `InsightFace` como motor de detecção facial de alta precisão.
- **MediaPipe**: Manutenção e correção de erros no fallback para o MediaPipe.
- **Limpeza de Logs**: Redução da verbosidade dos logs do FFmpeg no console.
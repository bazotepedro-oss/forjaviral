# Changelog

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
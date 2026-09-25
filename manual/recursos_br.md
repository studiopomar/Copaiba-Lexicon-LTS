# Catálogo de Recursos e Módulos — Copaiba Lexikon `e-LTS(se)`

Este guia detalha a arquitetura dos painéis da interface gráfica, configurações avançadas e a suíte completa de ferramentas integradas do **Copaiba Lexikon**.

---

## Arquitetura da Interface Gráfica

A interface do Copaiba Lexikon é baseada em **PySide6 (Qt6)** com suporte a acoplamento dinâmico de painéis (*Dock Widgets*).

### 1. Tabela Principal de Aliases
- **Campos:** Favorito, Status de Conclusão, Arquivo `.wav`, Nome do Alias, Offset, Overlap, Preutterance, Consonant e Cutoff.
- **Filtro em Tempo Real:** Campo de busca com suporte a correspondência instantânea e filtragem por prefixo/sufixo.
- **Edição em Linha:** Clique duplo sobre qualquer valor numérico ou alias para edição imediata.
- **Navegação com Teclado:** Suporte a atalhos de setas para seleção fluida.

### 2. Painel Central de Waveform
- **Visualização de Onda:** Traçado de alta densidade da forma de onda com cálculo dinâmico de pico/RMS.
- **Linhas de Parâmetros:**
  - **Offset (Início):** Delimita onde o fonema começa.
  - **Overlap (Sobreposição):** Define a zona de transição com a nota anterior.
  - **Preutterance (Pré-articulação):** Momento do tempo forte da nota.
  - **Consonant (Área Fixa):** Região não esticada temporalmente.
  - **Cutoff (Corte Final):** Ponto de término do fonema.
- **Mini-Mapa Panorâmico:** Barra compacta na base da waveform exibindo a totalidade do arquivo de áudio para salto e navegação instantânea.

### 3. Painel Lateral de Presets (Dock)
- Pré-configurações prontas para aplicar em um clique ou via atalhos (`Ctrl+1` a `Ctrl+5`):
  - **CV:** Padrão para fonemas Consoante-Vogal.
  - **VCV:** Configuração para bancos contínuos de múltiplas sílabas.
  - **VV:** Transições suaves entre vogais.
  - **VC:** Fechamento de sílabas e consoantes finais.
  - **-V:** Entradas e ataques vocálicos iniciais.
- **Criador de Presets Personalizados:** Permite cadastrar regras próprias baseadas na duração e estrutura dos fonemas.

---

## Configurações Globais e Ajustes Finos

### Configurações Gerais (`Ctrl + ,`)
- **Aparência & Tema:** Alternância entre temas escuros de alto contraste e estilos visuais ergonômicos.
- **Codificação de Arquivos:** Suporte a leitura/escrita em **UTF-8**, **Shift-JIS (cp932)** e **ANSI (mbcs)**.
- **Executáveis de Áudio:** Configuração dos caminhos do Resampler (ex: `TIPS`, `moresampler`, `resampler.exe`) e Wavtool.
- **Salvamento Automático & Backups:** Definição de intervalos e retenção de arquivos históricos de segurança.

### Configuração do Espectrograma e GPU
- **Aceleração por Hardware:** Suporte a **CUDA** (NVIDIA) e **OpenCL** (AMD / Intel / Apple) para cálculo ultrarrápido de FFTs.
- **Parâmetros Visuais:**
  - Ajuste de **Contraste**, **Gama** e **Ganho de Frequência**.
  - Tamanho da Janela FFT (128 a 4096 amostras).
  - Mapas de Cores especializados (Magma, Viridis, Plasma, Greyscale).

### Configuração de Áudio & Dispositivos
- Seleção de API de áudio (WASAPI, DirectSound, ALSA, PulseAudio, CoreAudio).
- Escolha da interface de som e taxa de amostragem.

---

## Suíte de Plugins Integrados (Pomar Tools)

### Colheita (*Pitch Analyzer*)
- **Função:** Extrai a frequência fundamental ($F_0$) do áudio e desenha uma linha tonal sobreposta à waveform.
- **Utilidade:** Permite identificar oscilações de pitch indesejadas, vibratos instáveis ou erros de afinação no voicebank gravado.

### Pomar Tuner (*Afinador em Tempo Real*)
- **Função:** Afinador cromático com leitura direta do microfone da máquina.
- **Utilidade:** O gravador (*recounter*) pode checar a nota e centavos de afinação antes de iniciar a captura de novos áudios.

### Maturação (*Detector VV / Crossfade*)
- **Função:** Algoritmo dedicado a identificar a região de transição harmônica entre duas vogais consecutivas.
- **Utilidade:** Automatiza o posicionamento de Preutterance e Overlap em bancos VCV e VV complexos.

### Enxertia (*Renomeação em Massa*)
- **Função:** Modificação de múltiplos aliases em lote usando regras de busca/substituição, prefixos, sufixos e **Expressões Regulares (Regex)**.
- **Utilidade:** Padronização de nomes de aliases em bancos multi-pitch (ex: adicionar `_A3`, `_C4` a centenas de arquivos de uma só vez).

### Polinizador (*Romaji ↔ Hiragana*)
- **Função:** Conversor fonético bidirecional entre escrita ocidental (Romaji) e silabário japonês (Hiragana).
- **Utilidade:** Adapta voicebanks estrangeiros para o padrão japonês e vice-versa instantaneamente.

### Podador (*Detector de Duplicatas*)
- **Função:** Varredura em busca de entradas conflitantes com o mesmo alias ou arquivos apontados indevidamente.
- **Utilidade:** Previne comportamentos anômalos no sintetizador gerados por duplicações acidentais no `oto.ini`.

### Inspetor (*Verificador de Consistência*)
- **Função:** Validação lógica e matemática de todos os parâmetros do voicebank.
- **Alertas Emitidos:**
  - Overlap maior ou igual ao Preutterance.
  - Consonant ultrapassando o limite físico do arquivo.
  - Cutoff negativo com corte incompatível.

### Geradores de Metadados
- **Gerador de README:** Gera documentação estruturada do voicebank para distribuição.
- **Gerador de `character.yaml`:** Cria o manifesto de configuração padronizado para uso direto no **OpenUtau**.

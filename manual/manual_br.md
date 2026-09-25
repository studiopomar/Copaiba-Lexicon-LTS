# Manual do Usuário — Copaiba Lexikon `e-LTS(se)`

Bem-vindo ao **Copaiba Lexikon**, a estação de trabalho integrada (IDE) de alta precisão desenvolvida para edição, configuração e calibração de arquivos `oto.ini` para [UTAU](https://utau.wiki/) e [OpenUtau](https://github.com/stakira/OpenUtau).

Este manual foi elaborado para orientar desde desenvolvedores iniciantes de voicebanks até otoers experientes na obtenção de resultados consistentes, estáveis e rápidos.

---

## Índice
1. [Conceitos Fundamentais do `oto.ini`](#1-conceitos-fundamentais-do-otoini)
2. [Interface Gráfica e Layout](#2-interface-gráfica-e-layout)
3. [Fluxo de Trabalho de Calibração (Otoing)](#3-fluxo-de-trabalho-de-calibração-otoing)
4. [Aceleração Gráfica e Espectrograma (GPU)](#4-aceleração-gráfica-e-espectrograma-gpu)
5. [Validação Auditiva: Teste de Síntese em Tempo Real](#5-validação-auditiva-teste-de-síntese-em-tempo-real)
6. [Suíte de Ferramentas Pomar (Plugins)](#6-suíte-de-ferramentas-pomar-plugins)
7. [Configurações do Projeto e Backups](#7-configurações-do-projeto-e-backups)
8. [Perguntas Frequentes e Resolução de Problemas](#8-perguntas-frequentes-e-resolução-de-problemas)

---

## 1. Conceitos Fundamentais do `oto.ini`

Cada entrada em um arquivo `oto.ini` descreve como o sintetizador vocal deve segmentar e esticar um arquivo `.wav` gravado. O formato básico é:

```text
arquivo.wav=alias,offset,consonant,cutoff,preutterance,overlap
```

### Os 5 Parâmetros de Tempo

```text
|--- (Offset) --->|================== [Áudio Utilizável] ==================| <--- (Cutoff) ---|
                  |--- [Overlap] --->|
                  |---------- [Preutterance] ---------->|
                  |----------------- [Consonant (Fixa)] ----------------->|
```

1. **Offset (Início / Azul):** Ponto inicial em milissegundos onde o áudio começa a ser considerado. Descarta ruídos e silêncios iniciais.
2. **Overlap (Sobreposição / Verde):** Ponto onde a nota anterior se funde com a nota atual (crossfade).
3. **Preutterance (Pré-articulação / Vermelho):** Momento em que a vogal ou centro fonético da nota realmente atinge o compasso musical.
4. **Consonant / Fixed (Região Consonantal Invariável / Rosa):** Trecho que **não** sofre alteração de tempo (time-stretching) pelo resampler. Preserva a naturalidade do ataque consonantal.
5. **Cutoff (Fim / Azul Direito):** Define o fim do áudio aproveitável. Quando negativo, mede a distância a partir do final do arquivo `.wav`.

---

## 2. Interface Gráfica e Layout

A interface do Copaiba Lexikon é modular e dividida em blocos focados em ergonomia:

```text
+-------------------------------------------------------------------------+
| Barra de Menus (Arquivo, Editar, Exibir, Ferramentas, Plugins, Ajuda)    |
| Barra de Ferramentas Rápida (Abrir, Salvar, Zoom, Presets, Síntese)     |
+-------------------------------------------------------------------------+
|                                                                         |
|  TABELA DE ALIASES (Lista com busca rápida, status e colunas de tempo)  |
|                                                                         |
+-------------------------------------------------------------------------+
|                                                                         |
|  PAINEL DE WAVEFORM & ESPECTROGRAMA                                    |
|  (Visualização de onda sonora, marcadores interativos e F0 de pitch)    |
|                                                                         |
|  MINI-MAPA DE NAVEGAÇÃO PANORÂMICA                                      |
+-------------------------------------------------------------------------+
| Barra de Status (Arquivo carregado, codificação, coordenadas e GPU)    |
+-------------------------------------------------------------------------+
```

- **Tabela de Aliases:** Permite ordenar por nome, arquivo `.wav`, parâmetros numéricos ou favoritos. Permite edição direta de células e seleção em massa.
- **Painel de Waveform:** Renderização de alta fidelidade da amplitude do áudio. Linhas verticais e regiões coloridas podem ser arrastadas diretamente.
- **Mini-Mapa:** Representação em miniatura do arquivo `.wav` completo, permitindo saltar rapidamente para qualquer seção de arquivos longos.
- **Painel Dock de Presets:** Acesso rápido às pré-configurações (CV, VCV, VV, VC, -V) com atalhos `Ctrl+1` a `Ctrl+5`.

---

## 3. Fluxo de Trabalho de Calibração (Otoing)

Para calibrar um voicebank com rapidez e precisão:

1. **Abrir o Voicebank:** Pressione `Ctrl + O` e selecione a pasta do voicebank. O arquivo `oto.ini` será detectado e carregado automaticamente.
2. **Navegar entre Fonemas:** Use as setas do teclado para cima e para baixo ou a roda do mouse sobre a waveform para alternar de alias.
3. **Marcar Pontos na Waveform:**
   - Posicione o mouse no início da consoante e pressione **`Q`** (Offset).
   - Posicione o mouse no ponto de crossfade e pressione **`W`** (Overlap).
   - Posicione o mouse no início da vogal estável e pressione **`E`** (Preutterance).
   - Posicione o mouse no final da consoante e pressione **`R`** (Consonant / Fixed).
   - Posicione o mouse onde a cauda da vogal termina e pressione **`T`** (Cutoff).
4. **Validar com Reprodução:**
   - `Espaço`: Ouve o segmento configurado.
   - `Ctrl + Shift + Espaço`: Executa o teste de síntese renderizado pelo resampler.
5. **Marcar Conclusão:** Pressione `Ctrl + M` para sinalizar o alias como calibrado.
6. **Salvar:** Pressione `Ctrl + S` para persistir no `oto.ini`.

---

## 4. Aceleração Gráfica e Espectrograma (GPU)

O Copaiba possui um motor de renderização de espectrogramas em tempo real via **PyOpenGL**, com processamento acelerado por hardware via **CUDA** (NVIDIA) e **OpenCL** (AMD / Intel / Apple Silicon).

### Como Ativar e Configurar:
1. Abra **Ferramentas > Configuração de Espectrograma**.
2. Ajuste:
   - **Contraste e Ganho:** Realça formantes vocálicos e ataques consonantais.
   - **Resolução FFT:** Maior precisão temporal (FFT menor) ou frequência (FFT maior).
   - **Aceleração de GPU:** Ative a opção para transferir os cálculos da CPU para a placa de vídeo.
   - **Paleta de Cores:** Selecione esquemas de alto contraste (Magma, Viridis, Inferno, Greyscale).

---

## 5. Validação Auditiva: Teste de Síntese em Tempo Real

Diferente de editores tradicionais onde o usuário precisa salvar, abrir o UTAU/OpenUtau e testar a voz, o Copaiba Lexikon possui um motor embutido de síntese imediata:

- Pressione **`Ctrl + Shift + Espaço`**.
- O áudio é processado pelo resampler configurado (ex: `TIPS.exe`, `moresampler.exe`, `resampler.exe`) e reproduzido instantaneamente.
- Nas **Configurações Gerais (`Ctrl + ,`)**, defina o caminho do executável do resampler de sua preferência.

---

## 6. Suíte de Ferramentas Pomar (Plugins)

O Copaiba integra ferramentas especializadas da iniciativa **Studio Pomar Yvyra**:

| Plugin | Finalidade | Como Usar |
| :--- | :--- | :--- |
| **Colheita** | Análise e sobreposição visual da curva de afinação ($F_0$). | Menu **Plugins > Análise > Colheita (Pitch)**. |
| **Pomar Tuner** | Afinador cromático via microfone para checar notas durante gravações. | Menu **Plugins > Análise > Pomar Tuner**. |
| **Maturação** | Detecção automática de pontos de transição de vogais em bancos VCV. | Menu **Plugins > Análise > Maturação (Detector VV)**. |
| **Enxertia** | Renomeação em massa com Expressões Regulares (Regex), prefixos e sufixos. | Menu **Plugins > Automação > Enxertia (Renomear)**. |
| **Polinizador** | Conversão bidirecional entre Romaji e Hiragana. | Menu **Plugins > Utilidades > Polinizador**. |
| **Podador** | Identificação e remoção de aliases duplicados ou redundantes. | Menu **Plugins > Validação > Podador (Duplicatas)**. |
| **Inspetor** | Verificação de inconsistências matemáticas (Overlap > Preutter, Cutoff inválido). | Menu **Plugins > Validação > Inspetor de Consistência**. |

---

## 7. Configurações do Projeto e Backups

- **Codificação de Arquivo:** Configure para UTF-8 (OpenUtau / UTAU Moderno) ou Shift-JIS / cp932 (UTAU Clássico japonês) em **Configurações (`Ctrl + ,`)**.
- **Salvamento Automático:** Defina intervalos de backup automático para garantir a persistência dos dados.
- **Discord Rich Presence:** Ative para exibir no seu perfil do Discord em qual banco e alias você está trabalhando.

---

## 8. Perguntas Frequentes e Resolução de Problemas

**P: A waveform não carrega o áudio.**  
R: Certifique-se de que o arquivo `.wav` está no formato PCM padrão (16-bit ou 24-bit, 44.1kHz ou 48kHz). Arquivos comprimidos em formatos incompatíveis devem ser convertidos.

**P: Os caracteres japoneses (Hiragana) aparecem corrompidos.**  
R: Altere o encoding de leitura em **Configurações Gerais > Codificação Padrão** para `Shift-JIS (cp932)`.

**P: Como redefinir o layout caso uma janela desapareça?**  
R: Pressione **`Ctrl + Shift + R`** para restaurar o layout padrão de todos os painéis.

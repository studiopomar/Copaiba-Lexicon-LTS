# Janelas e Recursos do Copaiba Lexikon

Este documento descreve as principais janelas, painéis e plugins disponíveis no Copaiba Lexikon.

## Interface Principal

A janela principal é dividida em três áreas principais:

### 1. Tabela de Aliases (Lista)
Localizada no topo (por padrão), exibe todos os aliases do arquivo `oto.ini`.
- **Colunas:** Favorito, Arquivo (.wav), Alias, Parâmetros (Offset, Overlap, Preutterance, Consonant, Cutoff).
- **Recursos:**
    - Filtro de busca rápida.
    - Ordenação por colunas.
    - Edição direta de valores (duplo clique).
    - Seleção múltipla para edição em lote.

### 2. Painel de Waveform (Forma de Onda)
Localizada na parte inferior (por padrão), mostra a visualização gráfica do áudio.
- **Visualização:** Mostra a onda sonora do arquivo selecionado.
- **Edição Visual:** Permite clicar e arrastar as linhas coloridas dos parâmetros.
    - **Azul:** Offset (início) e Cutoff (fim).
    - **Verde:** Overlap.
    - **Vermelho:** Preutterance.
    - **Rosa:** Consonant (área fixa).
- **Mini-Mapa:** Uma barra menor abaixo da waveform para navegação rápida em arquivos longos.

### 3. Painel de Presets (Lateral)
Painel acoplável (dock) que permite configurar e aplicar predefinições de parâmetros.
- Permite criar regras automáticas para tipos de aliases (CV, VCV, etc).

---

## Ferramentas e Diálogos

### Configurações Gerais (`Ctrl + ,`)
Janela global de preferências do software.
- **Geral:** Idioma, tema da interface.
- **Caminhos:** Localização de executáveis externos (Resamplers, Wavtool).
- **Backup:** Configuração de salvamento automático.

### Configuração de Espectrograma
Ajustes finos para a visualização do espectrograma na waveform.
- Contraste, gama de cores e resolução.
- Opção para ativar/desativar aceleração de hardware (GPU).

### Configuração de Teclas
Permite remapear as teclas de atalho usadas na edição da waveform (Padrão: Q, W, E, R, T).

### Dispositivo de Áudio
Seleciona a interface de áudio de saída (API e Dispositivo) para reprodução.

### Gerenciador de Plugins
Mostra os plugins instalados, suas versões e permite ativar/desativar extensões.

---

## Plugins Integrados

O Copaiba já vem com uma suíte de plugins poderosos instalados:

### Automação

**Enxertia - Renomear em Massa**
- Permite renomear múltiplos aliases usando padrões de substituição (Find & Replace), prefixos e sufixos.
- Suporta Expressões Regulares (Regex).

**Edição em Lote**
- Ferramenta nativa para aplicar valores numéricos de Offset, Overlap, etc., em todos os aliases selecionados de uma vez.

### Análise

**Colheita - Análise de Pitch**
- Analisa a frequência fundamental (F0) do áudio e exibe sobreposta à waveform.
- Útil para verificar a afinação das gravações.

**Maturação - Detector VV**
- Especializado em encontrar o ponto ideal de cruzamento (crossfade) entre vogais em bancos VCV/VC.

**Pomar - Afinador (Mic Tuner)**
- Um afinador cromático em tempo real que usa o microfone.
- Útil para o <i>recounter</i> (gravador) verificar a afinação antes de gravar.

### Utilidades

**Polinizador - Romaji ↔ Hiragana**
- Converte automaticamente os aliases de Romaji para Hiragana e vice-versa.
- Suporta diferentes padrões de romanização.

**Seleção - Ordenar Aliases**
- Ferramentas avançadas de ordenação da lista (por sufixo, pitch, duração, etc).

### Validação

**Podador - Detector de Duplicatas**
- Varre o voicebank em busca de aliases duplicados que podem causar conflitos.

**Inspetor - Verificador de Consistência**
- Verifica se há parâmetros inválidos (ex: Overlap maior que Preutterance, Cutoff inválido).

<div align="center">

<img width="100%" alt="Copaiba Lexikon Preview" src="https://github.com/user-attachments/assets/a18ad574-af82-4c55-9696-7e5372987eec" />

# Copaiba Lexikon `e-LTS(se)`

### *Estação de Trabalho para Configuração de Voicebanks e Edição de `oto.ini`*

[![Status](https://img.shields.io/badge/Release-e--LTS(se)-2ea44f.svg?style=for-the-badge&logo=shield)](https://github.com/studiopomar/Copaiba-Lexicon-LTS)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41CD52.svg?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PySide6/)
[![GPU Acceleration](https://img.shields.io/badge/GPU-CUDA%20%7C%20OpenCL%20%7C%20OpenGL-76B900.svg?style=for-the-badge&logo=nvidia&logoColor=white)](file:///Users/victor/copaiba-lexicon-lts/backend_gpu.py)
[![Platforms](https://img.shields.io/badge/Plataformas-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg?style=for-the-badge)](https://github.com/studiopomar/Copaiba-Lexicon-LTS)
[![i18n](https://img.shields.io/badge/Idiomas-14%20Locales-orange.svg?style=for-the-badge&logo=google-translate&logoColor=white)](file:///Users/victor/copaiba-lexicon-lts/translations)
[![Discord](https://img.shields.io/badge/Discord-Rich%20Presence-5865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](file:///Users/victor/copaiba-lexicon-lts/discord_rpc.py)

<br/>

[**Recursos Principais**](#principais-recursos) •
[**Suíte de Plugins Pomar**](#suíte-de-plugins-integrados-pomar-tools) •
[**Atalhos Rápidos**](#guia-rápido-de-atalhos) •
[**Instalação**](#instalação-e-execução) •
[**CI/CD & Compilação**](#cicd--builds-automatizados) •
[**Documentação**](#documentação-e-manuais)

</div>

---

## Visão Geral

O **Copaiba Lexikon** é um ambiente de desenvolvimento integrado (IDE) de alta performance especializado na criação, calibração e manutenção de arquivos `oto.ini` para os sintetizadores de voz [UTAU](https://utau.wiki/) e [OpenUtau](https://github.com/stakira/OpenUtau).

Desenvolvido sob a arquitetura do ecossistema **YVYRA / Studio Pomar**, o Copaiba transcende o conceito de um simples editor de anotações: ele gerencia o ciclo de vida completo do voicebank, desde a captação e afinação da gravação até o processamento espectral acelerado por GPU, verificação de consistência matemática e validação auditiva imediata através de testes de síntese em tempo real.

---

## Sobre a Linha e-LTS(se) da YVYRA

O **Copaiba Lexikon** é o pilar central da linha **e-LTS(se)** (*Estável e de Longo Tempo de Suporte*). Esta linha foi concebida para atender estúdios e desenvolvedores que dependem de previsibilidade, consistência e confiabilidade absoluta em longas jornadas de otoing.

> [!IMPORTANT]
> **Pilares da Linha e-LTS(se):**
> 1. **Estabilidade em Primeiro Lugar:** Versões são exaustivamente lapidadas para eliminar regressões e comportamentos inesperados.
> 2. **Revisão Minuciosa ("Pente Fino"):** Cada módulo e funcionalidade passa por rígidos critérios de integração e usabilidade.
> 3. **Planejamento e Longevidade:** Desenvolvimento focado em manutenibilidade e padrões sólidos em vez de modificações experimentais frequentes.
> 4. **Autonomia Tecnológica:** Ferramenta desenvolvida para fortalecer o ecossistema e a comunidade de síntese vocal.

---

## Principais Recursos

### Visualização & Motor Gráfico de Alta Fidelidade
- **Waveform Dinâmica & Suave:** Renderização acelerada com suporte a zoom horizontal/vertical e pan contínuo sem travamentos.
- **Mini-Mapa Interativo:** Navegação panorâmica instantânea por arquivos de áudio extensos.
- **Espectrograma Acelerado por Hardware:** Renderização em tempo real via **PyOpenGL** com suporte a **CUDA** e **OpenCL** ([backend_gpu.py](file:///Users/victor/copaiba-lexicon-lts/backend_gpu.py)), com ajuste fino de contraste, gama, resolução e paletas de cor.

### Edição e Calibração de Parâmetros
- **Manipulação Direta:** Ajuste visual dos 5 parâmetros essenciais (*Offset, Overlap, Preutterance, Consonant/Fixed, Cutoff*) por arraste do mouse ou teclado.
- **Código de Cores Estruturado:**
  - **Azul:** Início (Offset) e Fim (Cutoff)
  - **Verde:** Ponto de Sobreposição (Overlap)
  - **Vermelho:** Pré-articulação (Preutterance)
  - **Rosa:** Região Consonantal Invariável (Fixed / Consonant)
- **Atalhos Rápidos de Fixação:** Teclas `Q`, `W`, `E`, `R` e `T` posicionam marcadores diretamente sob o cursor.

### Teste de Síntese em Tempo Real
- Reprodução imediata de fonemas e concatenações com resamplers externos (TIPS, moresampler, resampler.exe, etc.) via `Ctrl + Shift + Espaço`.
- Elimina a necessidade de exportar arquivos e alternar para softwares externos durante o ajuste fino.

### Presets e Edição em Lote
- Presets prontos para estruturas **CV**, **VCV**, **VV**, **VC** e **-V** acessíveis por atalhos (`Ctrl+1` a `Ctrl+5`).
- Criação e gerenciamento de presets customizados com suporte a regras automatizadas.
- Modificação em massa de múltiplos aliases selecionados com cálculo de offsets relativos ou absolutos.

### Segurança de Dados & Codificações
- Suporte nativo a múltiplos encodings: **UTF-8**, **Shift-JIS (cp932)** e **ANSI (mbcs)**.
- **Salvamento Automático & Backups Incrementais:** Protege contra perdas acidentais de dados.

### Internacionalização Completa & Discord RPC
- Interface traduzida para **14 idiomas**: Português (`pt_BR`), Inglês (`en_US`), Japonês (`ja_JP`), Russo (`ru`), Espanhol (`es_ES`), Francês (`fr_FR`), Árabe (`ar_SA`), Italiano (`it_IT`), Polonês (`pl_PL`), Chinês (`zh_CN`), Havaiano (`haw`), Esperanto (`eo`), Basco/Bretão (`br_EU`) e Papiamento (`ptt`).
- **Discord Rich Presence:** Transmissão em tempo real da sessão de trabalho, alias atual e voicebank em edição.

---

## Suíte de Plugins Integrados (Pomar Tools)

O Copaiba Lexikon vem equipado com um conjunto completo de ferramentas especializadas na pasta [plugins/](file:///Users/victor/copaiba-lexicon-lts/plugins):

| Ferramenta | Descrição |
| :--- | :--- |
| **Colheita** (*Pitch Analyzer*) | Análise e sobreposição gráfica da frequência fundamental ($F_0$) para controle rigoroso de pitch. |
| **Pomar Tuner** (*Mic Tuner*) | Afinador cromático em tempo real via microfone, permitindo ao cantor checar notas durante a gravação. |
| **Maturação** (*Detector VV*) | Identificação automática inteligente dos pontos ótimos de crossfade para bancos VCV e transições vocálicas. |
| **Enxertia** (*Renomeação em Massa*) | Edição e renomeação em lote de aliases com suporte a Expressões Regulares (Regex), prefixos e sufixos. |
| **Polinizador** (*Romaji ↔ Hiragana*) | Conversor bidirecional entre sistemas fonéticos Romaji e Hiragana com múltiplos esquemas de romanização. |
| **Podador** (*Detector de Duplicatas*) | Varredura e higienização automática do banco contra aliases repetidos e redundâncias conflitantes. |
| **Inspetor** (*Consistência de Parâmetros*) | Validador matemático que detecta Overlaps maiores que Preutterances, Cutoffs inválidos e anomalias de limites. |
| **Geradores de Metadados** | Criação automática de arquivos `README.md` estruturados e `character.yaml` padronizados para OpenUtau. |

---

## Guia Rápido de Atalhos

> [!TIP]
> Consulte o manual detalhado em [manual/atalhos_br.md](file:///Users/victor/copaiba-lexicon-lts/manual/atalhos_br.md) para a lista completa de comandos e remapeamento de teclas.

### Waveform & Marcação de Parâmetros
| Tecla | Ação | Descrição |
| :---: | :--- | :--- |
| `Q` | **Offset** | Posiciona o marcador de Offset no ponto do cursor |
| `W` | **Overlap** | Posiciona o marcador de Overlap no ponto do cursor |
| `E` | **Preutterance** | Posiciona o marcador de Preutterance no ponto do cursor |
| `R` | **Consonant** | Posiciona a fronteira de consoante fixa no cursor |
| `T` | **Cutoff** | Posiciona o ponto de corte final no cursor |

### Navegação & Zoom
| Atalho | Ação |
| :--- | :--- |
| `Ctrl + Scroll` | Zoom Horizontal (Eixo do Tempo) |
| `Alt + Scroll` | Zoom Vertical (Amplitude da Onda) |
| `Shift + Scroll` | Deslocamento Horizontal (Pan) |
| `Seta Cima / Baixo` | Alterna para o Alias Anterior / Próximo |
| `Scroll do Mouse` | Roda de navegação rápida entre aliases da lista |

### Reprodução & Testes
| Atalho | Ação |
| :--- | :--- |
| `Espaço` | Reproduz o segmento configurado do alias atual |
| `Shift + Espaço` | Reproduz o arquivo de áudio WAV completo |
| `Ctrl + Shift + Espaço` | **Teste de Síntese** (Renderização imediata via Resampler) |

### Presets Rápidos
| Atalho | Preset Aplicado |
| :--- | :--- |
| `Ctrl + 1` | Preset **CV** |
| `Ctrl + 2` | Preset **VCV** |
| `Ctrl + 3` | Preset **VV** |
| `Ctrl + 4` | Preset **VC** |
| `Ctrl + 5` | Preset **-V** |

---

## Instalação e Execução

### Executando a partir do Código Fonte

#### Pré-requisitos
- **Python 3.10** ou superior instalado
- Interface de áudio compatível (WASAPI, ALSA, PulseAudio, CoreAudio)

#### Passo a Passo
```bash
# 1. Clone o repositório
git clone https://github.com/studiopomar/Copaiba-Lexicon-LTS.git
cd Copaiba-Lexicon-LTS

# 2. Crie e ative um ambiente virtual
# Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# Windows (Prompt / PowerShell):
python -m venv venv
venv\Scripts\activate

# 3. Instale as dependências
pip install --upgrade pip
pip install -r requirements.txt

# 4. Inicie o Copaiba Lexikon
python main.py
```

---

## CI/CD & Builds Automatizados

Os executáveis e instaladores são gerados automaticamente a cada release via **GitHub Actions** ([.github/workflows/build.yml](file:///Users/victor/copaiba-lexicon-lts/.github/workflows/build.yml)) para **Windows**, **Linux** e **macOS**.

As especificações do PyInstaller ficam centralizadas no diretório [packaging/](file:///Users/victor/copaiba-lexicon-lts/packaging):
- [Copaiba_Windows.spec](file:///Users/victor/copaiba-lexicon-lts/packaging/Copaiba_Windows.spec)
- [Copaiba_Linux.spec](file:///Users/victor/copaiba-lexicon-lts/packaging/Copaiba_Linux.spec)
- [Copaiba_macOS.spec](file:///Users/victor/copaiba-lexicon-lts/packaging/Copaiba_macOS.spec)

Caso queira compilar localmente:
```bash
# Windows
pyinstaller --clean packaging/Copaiba_Windows.spec

# Linux
pyinstaller --clean packaging/Copaiba_Linux.spec

# macOS
pyinstaller --clean packaging/Copaiba_macOS.spec
```

---

## Estrutura do Projeto

```text
copaiba-lexicon-lts/
├── .github/workflows/    # Pipelines de CI/CD e automação de releases
├── controllers/          # Controladores de fluxo e manipulação de estado
├── copaiba/              # Classes centrais do parser e entidades do oto.ini
├── core/                 # Motores de áudio, logging, cache e sessões
├── dialogs/              # Diálogos modais (Configurações, Plugins, Áudio, Atalhos)
├── manual/               # Documentação completa, manuais de atalhos e changelog
├── packaging/            # Especificações PyInstaller para Windows, Linux e macOS
├── plugins/              # Suíte de plugins Pomar (Colheita, Enxertia, Afinador, etc.)
├── tests/                # Bateria de testes unitários e de integração
├── translations/         # Arquivos de internacionalização (.txt i18n)
├── views/                # Componentes de interface e painéis acopláveis
├── widgets/              # Widgets especializados (Waveform, Espectrograma, Mini-mapa)
├── backend_gpu.py        # Motor de aceleração de espectrograma via CUDA/OpenCL
├── discord_rpc.py        # Módulo de integração Discord Rich Presence
├── main.py               # Ponto de entrada e janela principal da aplicação
├── requirements.txt      # Dependências do projeto em Python
└── README.md             # Apresentação e documentação do projeto
```

---

## Documentação e Manuais

Para aprofundar-se em todos os aspectos e fluxos de trabalho do Copaiba Lexikon, consulte a documentação detalhada na pasta [manual/](file:///Users/victor/copaiba-lexicon-lts/manual):

- [**Manual do Usuário (Português)**](file:///Users/victor/copaiba-lexicon-lts/manual/manual_br.md)
- [**Guia de Atalhos Completo (Português)**](file:///Users/victor/copaiba-lexicon-lts/manual/atalhos_br.md)
- [**Catálogo de Recursos & Painéis**](file:///Users/victor/copaiba-lexicon-lts/manual/recursos_br.md)
- [**Copaiba Lexikon vs vLabeler: Comparativo Técnico**](file:///Users/victor/copaiba-lexicon-lts/manual/copaiba_vs_vlabeler.md)
- [**User Manual (English)**](file:///Users/victor/copaiba-lexicon-lts/manual/manual_eng.md)
- [**Руководство пользователя (Русский)**](file:///Users/victor/copaiba-lexicon-lts/manual/manual_rus.md)

---

## Contribuições

Contribuições alinhadas com os padrões de qualidade e estabilidade da linha **e-LTS(se)** são bem-vindas:

1. Faça um Fork do projeto.
2. Crie uma Branch para a sua funcionalidade ou correção (`git checkout -b feature/minha-melhoria`).
3. Certifique-se de que os testes passem (`pytest tests/`).
4. Envie seus commits com mensagens claras (`git commit -m 'feat: adiciona suporte a novo resampler'`).
5. Abra um Pull Request detalhado descrevendo as alterações.

---

## Créditos & Realização

Desenvolvido pelo **[Studio Pomar Yvyra](https://github.com/studiopomar)**.

*Copaiba Lexikon — Precisão e estabilidade para a comunidade vocal synth.*

# Guia de Atalhos — Copaiba Lexikon `e-LTS(se)`

Relação completa de atalhos de teclado, ações de mouse e combinações de comando do **Copaiba Lexikon**.

---

## Arquivos e Projetos

| Ação | Atalho | Descrição |
| :--- | :--- | :--- |
| **Abrir Voicebank...** | `Ctrl + O` | Abre a pasta de um voicebank e carrega automaticamente o `oto.ini` |
| **Abrir Projeto...** | `Ctrl + Shift + O` | Abre um arquivo de projeto salvo (`.copaiba`) |
| **Salvar (oto.ini)** | `Ctrl + S` | Salva as alterações diretamente no arquivo `oto.ini` |
| **Salvar Projeto** | `Ctrl + Shift + P` | Salva o estado atual como projeto |
| **Salvar Como...** | `Ctrl + Shift + S` | Salva o arquivo `oto.ini` com outro nome ou localização |
| **Recarregar Tudo** | `Ctrl + F5` | Recarrega as configurações e o banco de dados do disco |
| **Abrir Pasta no Sistema** | `Ctrl + P` | Abre o gerenciador de arquivos (Explorer/Finder) na pasta do voicebank |
| **Configurações Gerais** | `Ctrl + ,` | Abre o painel global de preferências do sistema |

---

## Waveform e Posicionamento de Marcadores

> [!NOTE]
> Os atalhos de letra posicionam o marcador correspondente exatamente na posição horizontal onde o cursor do mouse estiver sobre a waveform.

| Tecla | Marcador | Código de Cor | Descrição |
| :---: | :--- | :---: | :--- |
| **`Q`** | **Offset** | Azul | Define o ponto de início do áudio aproveitável |
| **`W`** | **Overlap** | Verde | Define o ponto de transição e cruzamento (crossfade) |
| **`E`** | **Preutterance** | Vermelho | Define o ponto de ataque da vogal (tempo de compasso) |
| **`R`** | **Consonant** | Rosa | Define o fim da área fixa consonantal invariável |
| **`T`** | **Cutoff** | Azul | Define o ponto de corte do final do áudio |

---

## Navegação, Zoom e Pan

| Ação | Comando | Descrição |
| :--- | :--- | :--- |
| **Zoom Horizontal** | `Ctrl + Scroll` | Aumenta ou diminui o zoom na escala de tempo |
| **Zoom Vertical** | `Alt + Scroll` | Aumenta ou diminui o ganho visual da amplitude |
| **Deslocamento (Pan)** | `Shift + Scroll` | Desloca a visualização para a esquerda ou direita |
| **Arrastar Marcador** | `Clique e Arraste` | Move linhas de parâmetros diretamente com o mouse |
| **Navegar Aliases** | `Seta Cima / Baixo` | Seleciona o alias anterior ou próximo na lista |
| **Navegar por Scroll** | `Scroll do Mouse` | Roda do mouse sobre a waveform troca de alias |
| **Tocar Setor** | `Clique Esquerdo` | Reproduz o setor da waveform clicado |
| **Reprodução Precisa** | `Alt + Clique` | Reproduz trecho a partir da posição exata do cursor |

---

## Reprodução e Validação Auditiva

| Ação | Atalho | Descrição |
| :--- | :--- | :--- |
| **Tocar Segmento** | `Espaço` | Reproduz apenas o trecho delimitado entre Offset e Cutoff |
| **Tocar Áudio Completo** | `Shift + Espaço` | Reproduz o arquivo `.wav` original inteiro |
| **Teste de Síntese** | `Ctrl + Shift + Espaço` | Renderiza o fonema pelo resampler externo configurado e toca |

---

## Presets Rápidos de Parâmetros

| Atalho | Preset | Aplicação Típica |
| :--- | :--- | :--- |
| **`Ctrl + 1`** | **CV** | Consoante + Vogal padrão (ex: `ka`, `sa`, `ta`) |
| **`Ctrl + 2`** | **VCV** | Vogal-Consoante-Vogal (ex: `- ka`, `a ka`, `i sa`) |
| **`Ctrl + 3`** | **VV** | Transição entre Vogais (ex: `a i`, `u e`) |
| **`Ctrl + 4`** | **VC** | Vogal + Consoante final (ex: `a k`, `o s`) |
| **`Ctrl + 5`** | **-V** | Ataque inicial de vogal isolada (ex: `- a`, `- o`) |

---

## Edição e Manipulação da Tabela

| Ação | Atalho | Descrição |
| :--- | :--- | :--- |
| **Desfazer** | `Ctrl + Z` | Desfaz a última modificação de parâmetro ou texto |
| **Refazer** | `Ctrl + Y` | Refaz a última ação desfeita |
| **Marcar Concluído** | `Ctrl + M` | Alterna a marcação de status de conclusão do alias |
| **Renomear Alias** | `Ctrl + R` | Abre diálogo de renomeação do alias atual |
| **Duplicar Alias** | `Ctrl + I` | Cria uma cópia da linha atual para criar variações |
| **Deletar Alias** | `Ctrl + D` | Remove a linha selecionada da tabela |
| **Copiar Células** | `Ctrl + C` | Copia os dados selecionados na tabela |
| **Colar Células** | `Ctrl + V` | Cola valores da área de transferência nas células |

---

## Interface e Visualização

| Ação | Atalho | Descrição |
| :--- | :--- | :--- |
| **Ciclar Tema da Waveform** | `Ctrl + '` | Alterna os esquemas de cores e contraste da waveform |
| **Restaurar Layout Padrão** | `Ctrl + Shift + R` | Reposiciona todos os painéis e docks ao layout inicial |

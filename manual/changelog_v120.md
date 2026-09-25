# Histórico de Atualizações — Copaiba Lexikon `e-LTS(se)`

---

## Versão 2026.4 (v120.1) — `e-LTS(se)`

### Desempenho e Aceleração de Hardware
- **Aceleração por GPU:** Pipeline de processamento de espectrograma otimizado via OpenGL, CUDA e OpenCL ([backend_gpu.py](file:///Users/victor/copaiba-lexicon-lts/backend_gpu.py)).
- **Carregamento Assíncrono de Áudio:** Otimização do `AudioLoaderWorker` com cache de forma de onda multithread para transições instantâneas entre fonemas sem travamentos na UI.
- **Renderização da Tabela:** Removidas repinturas redundantes de células, garantindo rolagem fluida em arquivos `oto.ini` com mais de 5.000 aliases.

### Interface e Experiência do Usuário (UX)
- **Densidade Otimizada:** Redução de margens e paddings excessivos nas barras de ferramentas, tabelas e menus para maximizar a área útil da forma de onda.
- **Relocação de Abas:** Abas de controle e painéis de sessão posicionados ergonomicamente.
- **Paleta de Cores Semiótica:** Refinamento dos esquemas de cores de alto contraste para os marcadores (Azul, Verde, Vermelho, Rosa) e temas da waveform.
- **Feedback Visual:** Novos estados visuais de foco e botões com relevo tátil moderno.

### Suíte de Plugins Pomar
- **Colheita (*Pitch Analyzer*):** Melhoria na precisão do algoritmo de autocorrelação e sobreposição da curva $F_0$.
- **Pomar Tuner (*Afinador*):** Integração estável com backend `sounddevice` e detecção de afinação em tempo real via microfone.
- **Maturação (*Detector VV*):** Aprimoramento da detecção automática de transição de formantes vocálicos.
- **Geradores de Metadados:** Exportação padronizada de `README.md` e `character.yaml` para projetos compatíveis com OpenUtau.

### Estabilidade, Segurança e CI/CD
- **Automação GitHub Actions:** Pipeline completo de build multiplataforma (.exe para Windows, AppImage/binário para Linux e .app para macOS).
- **Tratamento de Exceções:** Correção de falhas em QThreads durante alternância rápida de arquivos `.wav`.
- **Prevenção de Perda de Dados:** Mecanismo de salvamento e recuperação incremental com suporte a codificações UTF-8 e Shift-JIS (cp932).
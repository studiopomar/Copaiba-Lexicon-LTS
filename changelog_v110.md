# Changelog v110

## Interface e UX
- Otimização da densidade da interface através da redução de paddings e tamanhos de fonte em menus, barras de ferramentas e tabelas.
- Relocação das abas de sessão (ex: VCV) para a parte inferior da seção de parâmetros.
- Eliminação do espaço central vazio entre os parâmetros e a forma de onda, criando um layout mais compacto e organizado.
- Modernização da paleta de cores com tons mais suaves para os modos claro e escuro.
- Aumento do arredondamento (border-radius) de elementos da interface para um visual mais moderno.
- Adição de relevo e estados visuais aprimorados em botões para melhor feedback tátil.

## Correções de Bugs
- Corrigido problema no widget de configuração do espectrograma que aparecia em branco ou perdia o estado após ser fechado e reaberto.
- Ajuste no sistema de eventos do PySide para evitar que comandos de teclado (Ctrl+C / Ctrl+V) sejam ignorados em determinadas células.
- Correção de falhas (craches) de QThread ao alternar rapidamente entre diferentes arquivos de áudio.
- Otimização de performance na tabela principal, removendo repinturas desnecessárias de cores ao navegar rapidamente.

## Funcionalidades
- Implementação de alertas visuais para conflitos de preutterance/cutoff na lista de aliases.
- Suporte a reprodução por segmento via Alt+Clique diretamente na forma de onda.
- Integração de novos geradores de README e Character YAML para projetos OpenUtau.

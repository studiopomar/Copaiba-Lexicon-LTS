# waveform_plot.py

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QLinearGradient
import pyqtgraph as pg
import numpy as np

# OpenGL removido - usando apenas renderização CPU
OPENGL_AVAILABLE = False

# Configurações globais do pyqtgraph (CPU only - PERFORMANCE OTIMIZADA)
pg.setConfigOptions(
    antialias=False,  # Desabilitar antialiasing para máxima performance
    useOpenGL=False,  # Desabilitar OpenGL
    enableExperimental=False,
)




class WaveformPlotWidget(pg.PlotWidget):
    """
    Widget PyQtGraph para exibir a forma de onda principal.
    Gerencia zoom, panning, grades, cursor e configurações visuais.
    
    Melhorias visuais:
    - Visualização espelhada (positivo e negativo)
    - Preenchimento com gradiente
    - Antialiasing suave
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Cores do tema
        self._bg_color = QColor(26, 26, 30)  # Fundo escuro elegante
        self._wave_color_top = QColor(0, 200, 150)      # Ciano/Verde água (parte superior)
        self._wave_color_bottom = QColor(100, 220, 100)  # Verde claro (parte inferior)
        self._fill_color_top = QColor(0, 200, 150, 60)  # Preenchimento superior
        self._fill_color_bottom = QColor(100, 220, 100, 60)  # Preenchimento inferior
        self._grid_color = QColor(60, 60, 70, 80)  # Grid sutil

        # Configurações básicas do plot
        self.setMenuEnabled(False)
        self.showGrid(x=True, y=False, alpha=0.08)  # Grid apenas horizontal
        self.setMouseEnabled(x=False, y=False)
        self.setBackground(self._bg_color)
        
        # Remove eixo Y esquerdo para alinhamento perfeito com espectrograma
        self.hideAxis('left')
        
        # Eixo X com cores sutis (bottom)
        self.getAxis("bottom").setPen(pg.mkPen(QColor(100, 100, 110), width=1))
        self.getAxis("bottom").setTextPen(pg.mkPen(QColor(140, 140, 150)))
        
        # Performance
        self.setDownsampling(auto=True, mode='peak')
        self.setClipToView(True)

        # Habilitar OpenGL se disponível
        if OPENGL_AVAILABLE:
            self.useOpenGL(True)

        # Desabilita o auto-range para controle manual
        self.disableAutoRange()

        # Linha central (zero) - linha mais destacada
        self._zero_line = pg.InfiniteLine(
            pos=0,
            angle=0,  # Horizontal
            pen=pg.mkPen(QColor(80, 80, 90), width=1),
        )
        self._zero_line.setZValue(-1)
        self.addItem(self._zero_line)

        # Linha do cursor (inicialmente oculta)
        self._cursor_line = pg.InfiniteLine(
            pos=0,
            angle=90,  # Vertical
            movable=False,
            pen=pg.mkPen("#ffdd00", width=1, style=Qt.DashLine),
        )
        self._cursor_line.hide()
        self._cursor_line.setZValue(100)
        self.addItem(self._cursor_line)

        # Preenchimento para parte POSITIVA (acima de zero)
        self._fill_positive = pg.PlotCurveItem(
            pen=None,
            fillLevel=0,
            brush=pg.mkBrush(self._fill_color_top),
        )
        self._fill_positive.setZValue(0)
        self.addItem(self._fill_positive)

        # Preenchimento para parte NEGATIVA (abaixo de zero)
        self._fill_negative = pg.PlotCurveItem(
            pen=None,
            fillLevel=0,
            brush=pg.mkBrush(self._fill_color_bottom),
        )
        self._fill_negative.setZValue(0)
        self.addItem(self._fill_negative)

        # Curva principal POSITIVA
        self._curve_positive = pg.PlotCurveItem(
            pen=pg.mkPen(self._wave_color_top, width=1),
        )
        self._curve_positive.setZValue(1)
        self.addItem(self._curve_positive)

        # Curva principal NEGATIVA
        self._curve_negative = pg.PlotCurveItem(
            pen=pg.mkPen(self._wave_color_bottom, width=1),
        )
        self._curve_negative.setZValue(1)
        self.addItem(self._curve_negative)

        # Referência para compatibilidade
        self._curve = self._curve_positive

    def set_cursor_position(self, pos):
        """Define a posição da linha do cursor e a mostra."""
        self._cursor_line.setPos(pos)
        self._cursor_line.show()

    def hide_cursor(self):
        """Oculta a linha do cursor."""
        self._cursor_line.hide()

    def set_wave_pen(self, pen):
        """Atualiza a caneta (pen) usada para desenhar a forma de onda."""
        self._curve_positive.setPen(pen)
        self._curve_negative.setPen(pen)

    def set_background_color(self, color: QColor):
        """Atualiza a cor de fundo do plot."""
        self._bg_color = color
        self.setBackground(color)

    def set_curve_data(self, x, y):
        """
        Define os dados (x, y) para as curvas.
        Separa automaticamente em partes positiva e negativa para o efeito espelhado.
        """
        if len(x) == 0 or len(y) == 0:
            self._curve_positive.setData([], [])
            self._curve_negative.setData([], [])
            self._fill_positive.setData([], [])
            self._fill_negative.setData([], [])
            return

        # Converte para numpy arrays se necessário e garante float32
        x = np.asarray(x, dtype=np.float32)
        y = np.asarray(y, dtype=np.float32)

        # Parte positiva (valores >= 0)
        y_positive = np.clip(y, 0, None)
        
        # Parte negativa (valores <= 0)
        y_negative = np.clip(y, None, 0)

        # Atualiza as curvas
        self._curve_positive.setData(x, y_positive)
        self._curve_negative.setData(x, y_negative)
        
        # Atualiza os preenchimentos
        self._fill_positive.setData(x, y_positive)
        self._fill_negative.setData(x, y_negative)

    def set_x_range(self, x1, x2, padding=0.0):
        """Define o intervalo visível no eixo X."""
        self.setXRange(x1, x2, padding=padding)

    def set_y_range(self, y1, y2, padding=0.0):
        """Define o intervalo visível no eixo Y."""
        self.setYRange(y1, y2, padding=padding)

    def get_view_range(self):
        """Obtém o intervalo atual de visualização (x, y)."""
        return self.viewRange()

    def update_view(self, x_range=None, y_range=None):
        """
        Atualiza a visualização com base em intervalos X e Y fornecidos.
        Se um intervalo for None, ele não é alterado.
        """
        if x_range:
            x1, x2 = x_range
            self.set_x_range(x1, x2)
        if y_range:
            y1, y2 = y_range
            self.set_y_range(y1, y2)

    def set_wave_colors(self, color_top: QColor, color_bottom: QColor = None):
        """
        Define as cores da waveform.
        
        Args:
            color_top: Cor da parte positiva (acima de zero)
            color_bottom: Cor da parte negativa (abaixo de zero). Se None, usa color_top.
        """
        if color_bottom is None:
            color_bottom = color_top
            
        self._wave_color_top = color_top
        self._wave_color_bottom = color_bottom
        
        # Atualiza as curvas
        self._curve_positive.setPen(pg.mkPen(color_top, width=1))
        self._curve_negative.setPen(pg.mkPen(color_bottom, width=1))
        
        # Atualiza os preenchimentos (com transparência)
        fill_top = QColor(color_top)
        fill_top.setAlpha(60)
        fill_bottom = QColor(color_bottom)
        fill_bottom.setAlpha(60)
        
        self._fill_positive.setBrush(pg.mkBrush(fill_top))
        self._fill_negative.setBrush(pg.mkBrush(fill_bottom))

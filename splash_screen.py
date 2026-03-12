# splash_screen.py
"""
Splash Screen moderna para Copaiba Lexikon.
Mostra progresso de carregamento enquanto o aplicativo inicializa.
"""

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QFont, QColor, QPainter, QLinearGradient, QPainterPath
from PySide6.QtWidgets import QSplashScreen, QGraphicsOpacityEffect
from pathlib import Path
import sys


class CopaibaSplashScreen(QSplashScreen):
    """Splash screen com barra de progresso animada e fade in/out."""
    
    def __init__(self):
        # Cria um pixmap com gradiente e bordas mais arredondadas
        pixmap = QPixmap(450, 280)
        pixmap.fill(Qt.transparent)
        
        # Desenha background com gradiente e bordas arredondadas (16px)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Path com bordas arredondadas
        path = QPainterPath()
        path.addRoundedRect(0, 0, 450, 280, 16, 16)
        
        gradient = QLinearGradient(0, 0, 0, 280)
        gradient.setColorAt(0, QColor(35, 35, 40))
        gradient.setColorAt(1, QColor(25, 25, 30))
        
        painter.setClipPath(path)
        painter.fillRect(pixmap.rect(), gradient)
        
        # Borda sutil
        painter.setClipping(False)
        painter.setPen(QColor(55, 55, 65))
        painter.drawRoundedRect(1, 1, 448, 278, 16, 16)
        painter.end()
        
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.SplashScreen)
        
        # Configura ícone
        self._icon_path = self._find_icon()
        
        # Progresso atual e target (para animação suave)
        self._progress = 0.0
        self._target_progress = 0.0
        self._status_text = "Iniciando..."
        
        # Timer para animação suave da barra
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate_progress)
        self._anim_timer.setInterval(16)  # ~60 FPS
        
        # Efeito de opacidade para fade
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)
        
        # Animação de fade
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(200)  # 0.2s
        self._fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
    def _find_icon(self) -> Path:
        """Encontra o ícone do aplicativo."""
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent / 'coffee.jpg'
        return Path(__file__).parent / 'coffee.jpg'
    
    def show(self):
        """Mostra com fade in."""
        super().show()
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()
    
    def fade_out_and_close(self, callback=None):
        """Fecha com fade out."""
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        
        def on_finished():
            self.close()
            if callback:
                callback()
        
        self._fade_anim.finished.connect(on_finished)
        self._fade_anim.start()
    
    def _animate_progress(self):
        """Anima a barra de progresso suavemente."""
        diff = self._target_progress - self._progress
        if abs(diff) < 0.3:
            self._progress = self._target_progress
            self._anim_timer.stop()
        else:
            # Easing mais suave
            self._progress += diff * 0.12
        self.repaint()
    
    def drawContents(self, painter: QPainter):
        """Desenha conteúdo personalizado na splash screen."""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Ícone centralizado no topo com bordas arredondadas
        if self._icon_path.exists():
            icon = QPixmap(str(self._icon_path))
            if not icon.isNull():
                icon_size = 96  # Tamanho maior
                icon_radius = 12  # Bordas arredondadas
                icon_scaled = icon.scaled(icon_size, icon_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                
                # Centraliza e recorta para quadrado
                x_offset = (icon_scaled.width() - icon_size) // 2
                y_offset = (icon_scaled.height() - icon_size) // 2
                icon_cropped = icon_scaled.copy(x_offset, y_offset, icon_size, icon_size)
                
                # Cria máscara arredondada
                rounded_icon = QPixmap(icon_size, icon_size)
                rounded_icon.fill(Qt.transparent)
                
                icon_painter = QPainter(rounded_icon)
                icon_painter.setRenderHint(QPainter.Antialiasing)
                
                clip_path = QPainterPath()
                clip_path.addRoundedRect(0, 0, icon_size, icon_size, icon_radius, icon_radius)
                icon_painter.setClipPath(clip_path)
                icon_painter.drawPixmap(0, 0, icon_cropped)
                icon_painter.end()
                
                icon_x = (self.width() - icon_size) // 2
                painter.drawPixmap(icon_x, 25, rounded_icon)
        
        # Título
        title_font = QFont("Segoe UI", 22, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(0, 125, self.width(), 32, Qt.AlignCenter, "Copaiba Lexikon")
        
        # Versão - menor, abaixo do título, cinza claro
        version_font = QFont("Segoe UI", 9)
        painter.setFont(version_font)
        painter.setPen(QColor(130, 130, 145))
        painter.drawText(0, 155, self.width(), 18, Qt.AlignCenter, "v6.0.0 RC | Canário")
        
        # Status text - acima da barra de progresso
        status_font = QFont("Segoe UI", 8)
        painter.setFont(status_font)
        painter.setPen(QColor(100, 100, 115))
        painter.drawText(0, 178, self.width(), 16, Qt.AlignCenter, self._status_text)
        
        # Barra de progresso
        bar_x = 50
        bar_y = 200
        bar_width = self.width() - 100
        bar_height = 5
        
        # Background da barra
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(45, 45, 50))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 2.5, 2.5)
        
        # Progresso animado - azul claro (#2196F3)
        progress_width = int(bar_width * (self._progress / 100))
        if progress_width > 0:
            painter.setBrush(QColor(33, 150, 243))  # #2196F3
            painter.drawRoundedRect(bar_x, bar_y, progress_width, bar_height, 2.5, 2.5)
        
        # Copyright - canto inferior direito, fonte pequena e discreta
        copyright_font = QFont("Segoe UI", 7)
        painter.setFont(copyright_font)
        painter.setPen(QColor(70, 70, 80))
        painter.drawText(0, 252, self.width() - 15, 18, Qt.AlignRight | Qt.AlignVCenter, 
                        "© 2025 Studio Pomar Yvyra")
    
    def set_progress(self, value: int, status: str = None):
        """Atualiza progresso com animação suave."""
        self._target_progress = min(100, max(0, value))
        if status:
            self._status_text = status
        if not self._anim_timer.isActive():
            self._anim_timer.start()
    
    def advance(self, amount: int = 10, status: str = None):
        """Avança o progresso."""
        self.set_progress(int(self._target_progress) + amount, status)


def create_splash() -> CopaibaSplashScreen:
    """Cria e retorna uma splash screen."""
    splash = CopaibaSplashScreen()
    splash.show()
    return splash

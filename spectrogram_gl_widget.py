# spectrogram_gl_widget.py
"""
Widget de espectrograma com renderização OpenGL via QOpenGLWidget.
Usa shaders GLSL para aplicar colormap na GPU com alta performance.
"""

from __future__ import annotations

import traceback
import numpy as np
import librosa
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QColor, QMouseEvent
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtOpenGL import QOpenGLShaderProgram, QOpenGLShader
from OpenGL.GL import *
import ctypes

# ============================================================
# Colormaps
# ============================================================

_colormap_cache = {}


def _generate_colormap(name: str) -> np.ndarray:
    """Gera array RGB 256x3 float32 para o colormap."""
    import matplotlib.pyplot as plt
    cmap = plt.get_cmap(name)
    colors = cmap(np.linspace(0, 1, 256))[:, :3]  # RGB sem alpha
    return np.ascontiguousarray(colors, dtype=np.float32)


def _get_colormap(name: str) -> np.ndarray:
    """Retorna colormap, gerando se necessário."""
    if name not in _colormap_cache:
        _colormap_cache[name] = _generate_colormap(name)
    return _colormap_cache[name]


# ============================================================
# Shaders GLSL (versão 130 — compatível com OpenGL 3.0+)
# ============================================================

VERTEX_SHADER_SRC = """
#version 130
in vec2 position;
in vec2 texCoord;
out vec2 vTexCoord;

void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    vTexCoord = texCoord;
}
"""

FRAGMENT_SHADER_SRC = """
#version 130
in vec2 vTexCoord;
out vec4 fragColor;

uniform sampler2D specData;
uniform sampler2D colormapTex;   // 256x1 RGB
uniform vec2  xRange;            // (start, end) em segundos
uniform float duration;          // duração total do áudio
uniform float gamma;
uniform float contrast;

void main() {
    // Mapeia X do quad para a posição na textura do espectrograma
    float tNorm = xRange.x / duration + vTexCoord.x * (xRange.y - xRange.x) / duration;
    vec2 samplePos = vec2(clamp(tNorm, 0.0, 1.0), vTexCoord.y);

    float v = texture2D(specData, samplePos).r;

    // Gamma + contraste (na GPU)
    v = pow(v, gamma);
    v = clamp((v - 0.5) * contrast + 0.5, 0.0, 1.0);

    // Lookup no colormap (textura 256x1)
    vec3 color = texture2D(colormapTex, vec2(v, 0.5)).rgb;
    fragColor = vec4(color, 1.0);
}
"""

MARKER_VERT_SRC = """
#version 130
in vec2 position;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

MARKER_FRAG_SRC = """
#version 130
out vec4 fragColor;
uniform vec4 markerColor;
void main() {
    fragColor = markerColor;
}
"""


# ============================================================
# Worker Thread
# ============================================================

class SpectrogramWorkerGL(QThread):
    """Worker thread para cálculo do espectrograma."""
    finished = Signal(np.ndarray)
    error = Signal(str)

    def __init__(self, data, sample_rate, config):
        super().__init__()
        self.data = data
        self.sample_rate = sample_rate
        self.config = config
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True
        try:
            self.finished.disconnect()
        except Exception:
            pass
        try:
            self.error.disconnect()
        except Exception:
            pass

    def run(self):
        try:
            if self._is_cancelled:
                return

            data = self.data
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            data = data.astype(np.float32)

            if self._is_cancelled:
                return

            n_fft = self.config.get('n_fft', 4096)
            hop_size = self.config.get('hop_size', 256)
            window_size = self.config.get('window_size', 4096)

            # Ajusta parâmetros se dados forem menores que n_fft
            data_len = len(data)
            if data_len < n_fft:
                n_fft = max(64, 2 ** int(np.log2(data_len)))
            if window_size > n_fft:
                window_size = n_fft
            if hop_size > n_fft:
                hop_size = n_fft // 4

            S = librosa.stft(
                data,
                n_fft=n_fft,
                hop_length=hop_size,
                win_length=window_size,
                window='hann',
                center=False
            )

            if self._is_cancelled:
                return

            S_mag = np.abs(S)
            S_db = librosa.amplitude_to_db(S_mag, ref=np.max)

            if self._is_cancelled:
                return

            # Normaliza para 0‑1
            db_min = S_db.min()
            db_max = S_db.max()
            if db_max > db_min:
                S_norm = (S_db - db_min) / (db_max - db_min)
            else:
                S_norm = np.zeros_like(S_db)

            if not self._is_cancelled:
                self.finished.emit(S_norm.astype(np.float32))

        except Exception as e:
            if not self._is_cancelled:
                self.error.emit(str(e))


# ============================================================
# Widget Principal
# ============================================================

class SpectrogramGLWidget(QOpenGLWidget):
    """
    Widget de espectrograma com renderização OpenGL.
    API compatível com SpectrogramWidget (Matplotlib).
    """
    mouseMoved = Signal(float)
    markerMoved = Signal(str, float)
    markerDragFinished = Signal()  # Emitido quando arraste de marcador termina

    def __init__(self, parent=None):
        super().__init__(parent)

        # Dados de áudio
        self._wave_data = None
        self._sample_rate = 44100
        self._audio_duration = 0.0
        self._current_wav_path = None

        # Espectrograma
        self._spectrogram_cache = None
        self._cache_valid = False
        self._worker = None
        self._running_workers = []
        self._needs_texture_upload = False

        # Configurações
        self._window_size = 512
        self._hop_size = 64
        self._n_fft = 1024
        self._max_freq = 22000
        self._min_freq = 0
        self._gamma = 0.8
        self._contrast = 1.2
        self._resolution_quality = 'ultra'
        self._use_gpu = False
        self._colormap_name = 'inferno'
        self._needs_colormap_update = False

        # View range
        self._x_start = 0.0
        self._x_end = 1.0

        # Cores
        self._background_color = QColor(0, 0, 0)

        # Marcadores
        self._marker_positions = {}
        self._marker_styles = {
            "offset":    (0.30, 0.65, 1.00, 0.90),
            "overlap":   (0.00, 1.00, 0.00, 0.90),
            "preutter":  (1.00, 0.00, 0.00, 0.90),
            "consonant": (1.00, 0.41, 0.71, 0.90),
            "cutoff":    (0.30, 0.65, 1.00, 0.90),
        }
        self._dragging_marker = None

        # OpenGL (inicializados em initializeGL)
        self._shader = None
        self._marker_shader = None
        self._vao = 0
        self._vbo = 0
        self._tex_spec = 0
        self._tex_cmap = 0
        self._marker_vao = 0
        self._marker_vbo = 0
        self._gl_ready = False

        # Timer debounce
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(100)
        self._debounce_timer.timeout.connect(self._do_compute_spectrogram)

        # Widget config
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    # --------------------------------------------------------
    # OpenGL lifecycle
    # --------------------------------------------------------

    def initializeGL(self):
        """Cria shaders, VAO/VBO e texturas dummy."""
        try:
            # --- shader do espectrograma ---
            self._shader = QOpenGLShaderProgram(self)
            ok_v = self._shader.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, VERTEX_SHADER_SRC)
            ok_f = self._shader.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, FRAGMENT_SHADER_SRC)
            if not ok_v or not ok_f:
                print(f"[GL] Shader compile error: {self._shader.log()}")
                return
            if not self._shader.link():
                print(f"[GL] Shader link error: {self._shader.log()}")
                return

            # --- shader dos marcadores ---
            self._marker_shader = QOpenGLShaderProgram(self)
            ok_mv = self._marker_shader.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Vertex, MARKER_VERT_SRC)
            ok_mf = self._marker_shader.addShaderFromSourceCode(QOpenGLShader.ShaderTypeBit.Fragment, MARKER_FRAG_SRC)
            if not ok_mv or not ok_mf:
                print(f"[GL] Marker shader compile error: {self._marker_shader.log()}")
                return
            if not self._marker_shader.link():
                print(f"[GL] Marker shader link error: {self._marker_shader.log()}")
                return

            # --- quad (preenche toda a viewport) ---
            #   position (x,y) | texcoord (u,v)
            quad = np.array([
                -1, -1, 0, 0,
                 1, -1, 1, 0,
                 1,  1, 1, 1,
                -1, -1, 0, 0,
                 1,  1, 1, 1,
                -1,  1, 0, 1,
            ], dtype=np.float32)

            self._vao = glGenVertexArrays(1)
            self._vbo = glGenBuffers(1)
            glBindVertexArray(self._vao)
            glBindBuffer(GL_ARRAY_BUFFER, self._vbo)
            glBufferData(GL_ARRAY_BUFFER, quad.nbytes, quad, GL_STATIC_DRAW)

            stride = 4 * 4  # 4 floats * 4 bytes
            pos_loc = self._shader.attributeLocation("position")
            tex_loc = self._shader.attributeLocation("texCoord")
            glEnableVertexAttribArray(pos_loc)
            glVertexAttribPointer(pos_loc, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
            glEnableVertexAttribArray(tex_loc)
            glVertexAttribPointer(tex_loc, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(8))
            glBindVertexArray(0)

            # --- VAO/VBO para marcadores ---
            self._marker_vao = glGenVertexArrays(1)
            self._marker_vbo = glGenBuffers(1)
            glBindVertexArray(self._marker_vao)
            glBindBuffer(GL_ARRAY_BUFFER, self._marker_vbo)
            # Reserva buffer para até 2 vértices por chamada
            glBufferData(GL_ARRAY_BUFFER, 4 * 4, None, GL_DYNAMIC_DRAW)
            m_pos_loc = self._marker_shader.attributeLocation("position")
            glEnableVertexAttribArray(m_pos_loc)
            glVertexAttribPointer(m_pos_loc, 2, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
            glBindVertexArray(0)

            # --- texturas dummy (1×1 preto) ---
            self._tex_spec = self._create_tex2d(np.zeros((1, 1), dtype=np.float32))
            self._tex_cmap = self._create_colormap_texture()

            self._gl_ready = True
            print("[GL] initializeGL OK")

        except Exception:
            traceback.print_exc()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)

    def paintGL(self):
        bg = self._background_color
        glClearColor(bg.redF(), bg.greenF(), bg.blueF(), 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        if not self._gl_ready:
            return

        # Upload pendente (feito dentro de paintGL = contexto ativo)
        if self._needs_texture_upload and self._spectrogram_cache is not None:
            self._upload_spectrogram()
            self._needs_texture_upload = False

        if self._needs_colormap_update:
            glDeleteTextures(1, [self._tex_cmap])
            self._tex_cmap = self._create_colormap_texture()
            self._needs_colormap_update = False

        if not self._cache_valid:
            return

        # --- Desenha espectrograma ---
        self._shader.bind()

        # Uniforms com chamadas OpenGL diretas (evita PySide6 overload issues)
        loc_xr = self._shader.uniformLocation("xRange")
        loc_dur = self._shader.uniformLocation("duration")
        loc_gam = self._shader.uniformLocation("gamma")
        loc_con = self._shader.uniformLocation("contrast")
        loc_sd = self._shader.uniformLocation("specData")
        loc_cm = self._shader.uniformLocation("colormapTex")

        glUniform2f(loc_xr, float(self._x_start), float(self._x_end))
        glUniform1f(loc_dur, float(max(0.001, self._audio_duration)))
        glUniform1f(loc_gam, float(self._gamma))
        glUniform1f(loc_con, float(self._contrast))

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._tex_spec)
        glUniform1i(loc_sd, 0)

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self._tex_cmap)
        glUniform1i(loc_cm, 1)

        glBindVertexArray(self._vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        self._shader.release()

        # --- Desenha marcadores ---
        self._draw_markers()

    # --------------------------------------------------------
    # Texturas
    # --------------------------------------------------------

    def _create_tex2d(self, data_2d: np.ndarray) -> int:
        """Cria textura GL_R32F a partir de array 2D float32."""
        data = np.ascontiguousarray(data_2d, dtype=np.float32)
        h, w = data.shape
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, w, h, 0, GL_RED, GL_FLOAT, data)
        glBindTexture(GL_TEXTURE_2D, 0)
        return int(tex)

    def _create_colormap_texture(self) -> int:
        """Cria textura 256×1 RGB com o colormap atual."""
        cmap = _get_colormap(self._colormap_name)  # (256, 3)
        # Armazena como textura 2D 256×1
        cmap_row = np.ascontiguousarray(cmap.reshape(1, 256, 3), dtype=np.float32)
        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, 256, 1, 0, GL_RGB, GL_FLOAT, cmap_row)
        glBindTexture(GL_TEXTURE_2D, 0)
        return int(tex)

    def _upload_spectrogram(self):
        """Envia dados do espectrograma para textura GPU."""
        if self._spectrogram_cache is None:
            return

        # Dados do librosa: (freq_bins, time_frames)
        # OpenGL: row 0 = bottom → freq_bin 0 = DC (baixa freq) → correto
        # width = n_frames (eixo X = tempo), height = freq_bins (eixo Y = freq)
        data = np.ascontiguousarray(self._spectrogram_cache, dtype=np.float32)
        freq_bins, n_frames = data.shape

        if self._tex_spec:
            glDeleteTextures(1, [self._tex_spec])
        self._tex_spec = self._create_tex2d(data)

        print(f"[GL] Textura espectrograma: {n_frames}×{freq_bins} (tempo×freq)")

    # --------------------------------------------------------
    # Marcadores
    # --------------------------------------------------------

    def _draw_markers(self):
        """Desenha linhas verticais dos marcadores."""
        if not self._marker_positions or self._audio_duration <= 0:
            return

        self._marker_shader.bind()
        color_loc = self._marker_shader.uniformLocation("markerColor")
        visible_w = self._x_end - self._x_start
        if visible_w <= 0:
            self._marker_shader.release()
            return

        glLineWidth(2.0)

        for name, pos_s in self._marker_positions.items():
            x_ndc = (pos_s - self._x_start) / visible_w * 2.0 - 1.0
            if not (-1.0 <= x_ndc <= 1.0):
                continue

            color = self._marker_styles.get(name, (1.0, 1.0, 1.0, 0.9))
            glUniform4f(color_loc, *color)

            verts = np.array([x_ndc, -1.0, x_ndc, 1.0], dtype=np.float32)
            glBindVertexArray(self._marker_vao)
            glBindBuffer(GL_ARRAY_BUFFER, self._marker_vbo)
            glBufferSubData(GL_ARRAY_BUFFER, 0, verts.nbytes, verts)
            glDrawArrays(GL_LINES, 0, 2)
            glBindVertexArray(0)

        self._marker_shader.release()

    # --------------------------------------------------------
    # Mouse
    # --------------------------------------------------------

    def _pixel_to_time(self, x_pixel: float) -> float:
        w = self.width()
        if w <= 0:
            return 0.0
        t = self._x_start + (x_pixel / w) * (self._x_end - self._x_start)
        return max(0.0, min(t, self._audio_duration))

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._audio_duration <= 0:
            return
        t = self._pixel_to_time(event.position().x())
        self.mouseMoved.emit(t)

        if self._dragging_marker:
            self.markerMoved.emit(self._dragging_marker, t)
            self._marker_positions[self._dragging_marker] = t
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton or self._audio_duration <= 0:
            return
        t = self._pixel_to_time(event.position().x())

        tolerance = (self._x_end - self._x_start) * 0.02
        best_name, best_dist = None, float('inf')
        for name, pos in self._marker_positions.items():
            d = abs(pos - t)
            if d < best_dist and d < tolerance:
                best_name, best_dist = name, d

        self._dragging_marker = best_name

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self._dragging_marker:
                self._dragging_marker = None
                self.markerDragFinished.emit()
            self._dragging_marker = None

    # --------------------------------------------------------
    # Cálculo do espectrograma
    # --------------------------------------------------------

    def set_audio_data(self, wave_data, sample_rate, duration, wav_path=None):
        if wav_path and wav_path == self._current_wav_path and self._cache_valid:
            if self.isVisible():
                self.update()
            return

        self._wave_data = wave_data
        self._sample_rate = sample_rate
        self._audio_duration = duration
        self._current_wav_path = wav_path
        self._cache_valid = False
        self._x_start = 0.0
        self._x_end = duration

        if self.isVisible():
            self._do_compute_spectrogram()

    def _do_compute_spectrogram(self):
        if self._wave_data is None or len(self._wave_data) == 0:
            return

        if self._worker is not None:
            old = self._worker
            self._worker = None
            if old.isRunning():
                old.cancel()
                self._running_workers.append(old)
                old.finished.connect(lambda _, w=old: self._cleanup_worker(w))
                old.error.connect(lambda _, w=old: self._cleanup_worker(w))
            else:
                old.deleteLater()

        config = {
            'n_fft': self._n_fft,
            'hop_size': self._hop_size,
            'window_size': self._window_size,
        }
        self._worker = SpectrogramWorkerGL(self._wave_data, self._sample_rate, config)
        self._worker.finished.connect(self._on_ready)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_ready(self, data: np.ndarray):
        print(f"[GL] Espectrograma pronto: shape={data.shape}")
        self._spectrogram_cache = data
        self._cache_valid = True
        self._needs_texture_upload = True
        self._worker = None
        self.update()  # Dispara paintGL → upload + render

    def _on_error(self, msg):
        print(f"[GL ERROR] {msg}")
        self._worker = None

    def _cleanup_worker(self, w):
        if w in self._running_workers:
            self._running_workers.remove(w)
        w.deleteLater()

    # --------------------------------------------------------
    # API pública (compatível com SpectrogramWidget)
    # --------------------------------------------------------

    def update_markers(self, positions: dict):
        self._marker_positions = positions.copy()
        self.update()

    def set_x_range(self, start_time: float, end_time: float):
        self._x_start = start_time
        self._x_end = end_time
        self.update()

    def set_visible_region(self, start_time: float, end_time: float):
        self.set_x_range(start_time, end_time)

    def set_colormap(self, name: str):
        if name != self._colormap_name:
            self._colormap_name = name
            self._needs_colormap_update = True
            self.update()

    def set_gamma(self, gamma: float):
        self._gamma = max(0.1, min(3.0, gamma))
        self.update()  # Shader aplica — sem recompute

    def set_contrast(self, contrast: float):
        self._contrast = max(0.1, min(5.0, contrast))
        self.update()  # Shader aplica — sem recompute

    def set_fft_params(self, n_fft, hop_size, window_size):
        if self._n_fft != n_fft or self._hop_size != hop_size or self._window_size != window_size:
            self._n_fft, self._hop_size, self._window_size = n_fft, hop_size, window_size
            self._cache_valid = False
            if self._wave_data is not None and self.isVisible():
                self._debounce_timer.start()

    def set_freq_range(self, min_freq, max_freq):
        self._min_freq = max(0, min_freq)
        self._max_freq = min(max_freq, self._sample_rate // 2)
        self.update()

    def set_resolution_quality(self, quality: str):
        pass  # Removido — usar set_fft_params diretamente

    def set_use_gpu(self, use_gpu: bool):
        self._use_gpu = use_gpu

    def set_background_color(self, color):
        if isinstance(color, str):
            color = QColor(color)
        self._background_color = color
        self.update()

    def set_spectrum_color(self, color):
        pass  # Colormap controla cores

    def get_background_color(self):
        return self._background_color

    def get_spectrum_color(self):
        return QColor(255, 180, 0)

    def set_height(self, height):
        self.setFixedHeight(max(80, min(height, 600)))

    def get_plot_item(self):
        """Compatibilidade — sem axes matplotlib."""
        return None

    def clear(self):
        if self._worker is not None:
            old = self._worker
            self._worker = None
            if old.isRunning():
                old.cancel()
                self._running_workers.append(old)
                old.finished.connect(lambda _, w=old: self._cleanup_worker(w))
                old.error.connect(lambda _, w=old: self._cleanup_worker(w))
            else:
                old.deleteLater()
        self._wave_data = None
        self._spectrogram_cache = None
        self._cache_valid = False
        self._marker_positions = {}
        self.update()

    def cleanup(self):
        self.clear()
        if self._worker:
            self._worker.cancel()
            self._worker.wait(500)

    def showEvent(self, event):
        super().showEvent(event)
        if self._wave_data is not None and not self._cache_valid:
            self._do_compute_spectrogram()

    def closeEvent(self, event):
        if self._worker:
            self._worker.cancel()
            self._worker.wait(500)
        for w in self._running_workers:
            w.cancel()
            w.wait(200)
        super().closeEvent(event)

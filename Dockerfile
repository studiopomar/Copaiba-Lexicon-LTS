FROM ubuntu:22.04

# Evita prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libgl1-mesa-glx \
    libegl1-mesa \
    libxkbcommon0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    libxcb-cursor0 \
    libfontconfig1 \
    libdbus-1-3 \
    libpulse0 \
    libasound2 \
    binutils \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia arquivos do projeto
COPY requirements-build.txt .
COPY *.py ./
COPY *.spec ./
COPY copaiba/ ./copaiba/
COPY core/ ./core/
COPY controllers/ ./controllers/
COPY dialogs/ ./dialogs/
COPY views/ ./views/
COPY widgets/ ./widgets/
COPY plugins/ ./plugins/
COPY translations/ ./translations/
COPY site/ ./site/
COPY favicon.ico .
COPY coffee.jpg .
COPY site.webmanifest .

# Cria ambiente virtual e instala dependências
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install -r requirements-build.txt && \
    pip install pyinstaller

# Comando de build
CMD ["pyinstaller", "--clean", "Copaiba_Linux.spec"]

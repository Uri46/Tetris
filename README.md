# Tetris Profesional en Python

## Descripción

Juego Tetris hecho con Python y Pygame CE, organizado con programación orientada a objetos y una estructura lista para subir a GitHub. Incluye menú principal, pausa, reinicio, pantalla de Game Over, sistema de puntaje, niveles, líneas eliminadas, hold, vista previa, sonidos, música de fondo reemplazable y récord persistente en JSON.

## Capturas

> Espacios reservados para capturas del proyecto.

![Menú principal](docs/screenshots/menu.png)
![Partida en curso](docs/screenshots/gameplay.png)
![Game Over](docs/screenshots/game-over.png)

## Características

- Siete tetrominós oficiales.
- Rotación con wall kicks estilo SRS.
- Colisiones, bloqueo, hard drop y soft drop.
- Hold de pieza y vista previa de la siguiente pieza.
- Eliminación de líneas con animación.
- Efecto visual al tocar el suelo.
- Velocidad progresiva por nivel.
- Panel lateral con puntaje, nivel, líneas, récord, próxima pieza y hold.
- Música y efectos reemplazables desde `assets/`.
- Récord guardado automáticamente en `high_score.json`.
- Contador de FPS opcional con la tecla `F`.

## Estructura

```text
Tetris/
├── assets/
│   ├── fonts/
│   ├── music/
│   ├── sounds/
│   └── images/
├── src/
│   ├── board.py
│   ├── piece.py
│   ├── game.py
│   ├── ui.py
│   ├── config.py
│   └── score.py
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

## Instalación

1. Clonar el repositorio o descargar el proyecto.
2. Entrar a la carpeta del proyecto. Este paso es importante: `main.py` está dentro de `Tetris`, no en la carpeta de usuario.

```bash
git clone https://github.com/Uri46/Tetris.git
cd Tetris
```

3. Crear y activar un entorno virtual:

```bash
python -m venv .venv
```

En Windows:

```bash
.venv\Scripts\activate
```

En macOS/Linux:

```bash
source .venv/bin/activate
```

4. Instalar dependencias:

```bash
pip install -r requirements.txt
```

> En Python 3.14 se usa `pygame-ce`, que mantiene el import clásico `import pygame` y evita problemas de compilación en Windows.

## Cómo ejecutar

Desde la raíz del proyecto, es decir, estando dentro de la carpeta `Tetris`:

```bash
python main.py
```

En Windows PowerShell, el flujo completo sería:

```powershell
cd C:\Users\uriel
git clone https://github.com/Uri46/Tetris.git
cd Tetris
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Controles

| Acción | Tecla |
| --- | --- |
| Mover izquierda/derecha | Flechas izquierda y derecha |
| Soft Drop | Flecha abajo |
| Rotar | Flecha arriba |
| Hard Drop | Espacio |
| Hold | Shift |
| Pausa | P |
| Salir | Esc |
| Mostrar/ocultar FPS | F |

## Assets reemplazables

El juego funciona aunque las carpetas de assets estén vacías, porque genera un icono y sonidos simples por defecto. Para personalizarlo, agrega archivos con estos nombres:

- Música: `assets/music/theme.ogg`
- Icono: `assets/images/icon.png`
- Sonidos: `assets/sounds/move.wav`, `rotate.wav`, `drop.wav`, `clear.wav`, `hold.wav`, `game_over.wav`, `menu.wav`

## Tecnologías utilizadas

- Python 3
- Pygame CE, compatible con el import clásico `pygame`
- JSON para persistencia del récord

## Licencia

Este proyecto está publicado bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

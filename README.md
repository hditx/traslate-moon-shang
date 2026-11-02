# 🏮 Moon Shang (墨裳) — Traductor Chino-Español Interactivo

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Vue 3](https://img.shields.io/badge/vue-3.4+-emerald.svg)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5.4+-blue.svg)](https://www.typescriptlang.org/)
[![Android SDK 34](https://img.shields.io/badge/android-API%2034-green.svg)](https://developer.android.com/)
[![Clean Architecture](https://img.shields.io/badge/architecture-Hexagonal%20%2F%20Clean-purple.svg)](#-arquitectura-del-sistema)
[![Tests Passing](https://img.shields.io/badge/tests-153%2F153%20passing-brightgreen.svg)](#-testing-linting-y-seguridad)

**Moon Shang (墨裳)** es una plataforma de software multiplataforma (escritorio **Linux / Windows** y móvil **Android**) diseñada para la lectura, estudio y traducción interactiva de documentos en chino (PDFs e imágenes `.png`, `.jpg`), complementada con un **Diccionario Erudito Chino-Español**, animación caligráfica de trazos paso a paso (笔顺) y captura fotográfica instantánea mediante cámara móvil.

La interfaz implementa el tema de diseño **Oro Antiguo Erudito** (*pergamino cálido, obsidiana, velo de tinta china y acentos en oro mate `#c5a059`*), optimizado para una lectura descansada y una experiencia de usuario de alta gama.

---

## 📑 Tabla de Contenidos

1. [Visión y Características Principales](#-visión-y-características-principales)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Estructura del Monorepo](#-estructura-del-monorepo)
4. [Prerrequisitos del Sistema](#-prerrequisitos-del-sistema)
5. [Instalación Rápida](#-instalación-rápida)
6. [Cómo Levantar el Proyecto (Modos de Ejecución)](#-cómo-levantar-el-proyecto-modos-de-ejecución)
   - [Modo 1: Desarrollo Frontend Aislado (Vite)](#1-modo-desarrollo-frontend-aislado-mock-ui)
   - [Modo 2: Aplicación de Escritorio Nativa (Desktop)](#2-modo-aplicación-de-escritorio-nativa-desktop)
   - [Modo 3: Servidor Backend FastAPI (API Server)](#3-modo-servidor-backend-fastapi-api-server)
   - [Modo 4: Aplicación Móvil Android (APK & Emulador)](#4-modo-aplicación-móvil-android-apk--emulador)
7. [Empaquetado y Distribución](#-empaquetado-y-distribución)
8. [Configuración y Variables de Entorno](#-configuración-y-variables-de-entorno)
9. [Testing, Linting y Seguridad](#-testing-linting-y-seguridad)
10. [Referencia de Comandos (`Makefile`)](#-referencia-de-comandos-makefile)
11. [Solución de Problemas (FAQ / Troubleshooting)](#-solución-de-problemas-faq--troubleshooting)

---

## 🌟 Visión y Características Principales

* **Lector y Traductor Interactivo de Documentos:**
  * Carga de imágenes (`.png`, `.jpg`, `.jpeg`, `.webp`) y documentos `.pdf` de múltiples páginas con renderizado nítido vía **PDF.js**.
  * Detección y segmentación automática de caracteres chinos mediante OCR (**PaddleOCR PP-OCRv4** en PC y **Google ML Kit Text Recognition** en Android).
  * Capa vectorial interactiva (*Bounding Boxes*) con reescalado automático según los niveles de **Zoom** y **Paneo** del visor.
* **Tarjeta Flotante Inteligente (*Translation Popover*):**
  * Despliegue con cursor (*hover*) o toque táctil (*tap*) sin salirse de la pantalla mediante `@floating-ui/vue`.
  * Visualización de caracteres originales (**Hanzi 汉字**), fonética **Pinyin** con marcas exactas de tonos y traducción contextual al español.
  * Pronunciación en audio (chino mandarín estándar) y botón de copiado directo al portapapeles.
* **Caligrafía y Orden de Trazos Paso a Paso (HanziWriter 笔顺):**
  * Descomposición de palabras en caracteres individuales.
  * Visualización en cuadrícula caligráfica china (**Tian Zi Ge 田字格**).
  * Animación vectorial trazo por trazo, velocidad ajustable, bucle de repetición y **modo de práctica interactiva** (con detección de errores y trazos correctos).
* **Diccionario Erudito Chino-Español:**
  * Buscador rápido con autocompletado en tiempo real por caracteres Hanzi, Pinyin o significado en español.
  * Desglose de radicales, nivel de dificultad, clasificación gramatical y frases de ejemplo contextualizadas.
* **Captura Fotográfica con Cámara (Android Nativo):**
  * Botón central ergonómico en la barra de navegación para capturar fotos directamente con la cámara del dispositivo.
  * Corrección automática de orientación EXIF, compresión inteligente y análisis OCR inmediato en dispositivo.
* **Operación Híbrida Online / Offline:**
  * **Modo Offline:** Diccionario CC-CEDICT empaquetado en memoria, OCR ML Kit en el dispositivo y caché local SQLite en PC.
  * **Modo Online:** Traducción dinámica con Google Translate GTX, MyMemory API o modelos avanzados de Google Gemini si se configura una API key.

---

## 🏗️ Arquitectura del Sistema

El proyecto está diseñado bajo los principios de **Clean Architecture (Arquitectura Hexagonal / Puertos y Adaptadores)** y **SOLID**, separando completamente las reglas de negocio de los detalles de infraestructura o librerías externas.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vue 3 + TypeScript)                        │
│  - Vistas: DictionarySearch, DocumentViewer, Toolbar, BottomNav             │
│  - Componentes: BoundingBoxOverlay, TranslationPopover, StrokeOrderModal    │
│  - Composables: useZoomPan, useCoordinateScaler, useSpeech                  │
│  - Estado Global: Pinia (documentStore, settingsStore)                      │
│  - Abstracción Gateway: IDesktopBridge                                      │
└───────────────────────┬─────────────────────────────┬───────────────────────┘
                        │ IPC (PyWebView / JSON-RPC)  │ @JavascriptInterface (Bridge)
┌───────────────────────▼─────────────┐ ┌─────────────▼───────────────────────┐
│          BACKEND (Python)           │ │        ANDROID (Kotlin Nativo)      │
│  - Fachada: DesktopFacade           │ │  - UI / Shell: MainActivity, WebView│
│  - Casos de Uso:                    │ │  - OCR: SmartHybridOcrEngine        │
│    ProcessDocumentUseCase,          │ │    (ML Kit en dispositivo + Remoto) │
│    TranslateTokenUseCase            │ │  - Diccionario Local:               │
│  - Adaptadores:                     │ │    LocalDictionaryHelper (CEDICT)   │
│    PaddleOCR, PyMuPDF, Jieba,       │ │  - Cliente Traductor Remoto:        │
│    Pypinyin, SQLite Cache           │ │    RemoteTranslatorClient           │
│  - Servidor HTTP: FastAPI / Uvicorn │ │  - Cámara: CameraCaptureHelper      │
└─────────────────────────────────────┘ └─────────────────────────────────────┘
```

### Patrón Gateway / Bridge en Frontend:
La interfaz web es agnóstica de la plataforma en la que corre gracias a `getDesktopBridge()`:
* **`PyWebViewBridge`:** Se activa en escritorio cuando detecta `window.pywebview.api`.
* **`AndroidBridge`:** Se activa en Android cuando detecta `window.AndroidBridge` o `window.androidApi`.
* **`MockDesktopBridge`:** Se activa en desarrollo en navegador (`pnpm dev`) sirviendo documentos, OCR y traducciones simuladas sin requerir backend.

---

## 📁 Estructura del Monorepo

```text
traslate-moon-shang/
├── Makefile                 # Orquestador unificado de tareas (build, test, run, emu)
├── PLAN.md                  # Plan maestro de arquitectura, progreso y roadmap
├── README.md                # Este documento de documentación e instalación
├── translations.db          # Base de datos SQLite para caché de traducciones
├── android/                 # Aplicación Móvil Android Nativa (Kotlin + Gradle)
│   ├── app/
│   │   ├── build.gradle.kts # Configuración de dependencias Android (SDK 34, ML Kit, JUnit 5)
│   │   └── src/
│   │       ├── main/        # MainActivity, WebView, SmartHybridOcrEngine, Bridges
│   │       │   └── assets/  # Bundle compilado del frontend y datos offline
│   │       └── test/        # 59 pruebas unitarias de Android (MockK + JUnit Platform)
│   └── assets_data/         # Tablas de pinyin y recursos estáticos de Android
├── backend/                 # Backend en Python (FastAPI + PyWebView + Clean Arch)
│   ├── pyproject.toml       # Dependencias y configuración de uv / ruff / pytest
│   ├── uv.lock              # Bloqueo determinista de dependencias Python
│   ├── src/
│   │   ├── main.py          # Punto de entrada de la aplicación de escritorio
│   │   ├── api_server.py    # Servidor FastAPI HTTP para clientes móviles y web
│   │   ├── domain/          # Entidades (Pydantic) y Puertos/Interfaces
│   │   ├── use_cases/       # Casos de uso de procesamiento y traducción
│   │   ├── adapters/        # Adaptadores (PaddleOCR, PyMuPDF, Jieba, SQLite, TTS)
│   │   ├── bridge/          # Fachada expuesta vía IPC (DesktopFacade)
│   │   └── core/            # Logging estructurado y configuración
│   └── tests/               # Pruebas de integración y unitarias de Python (pytest)
├── frontend/                # Frontend SPA en Vue 3 + TypeScript (Vite + Pinia)
│   ├── package.json         # Dependencias de npm / scripts de pnpm
│   ├── pnpm-lock.yaml       # Bloqueo determinista de paquetes frontend
│   ├── vite.config.ts       # Configuración de compilación de Vite
│   ├── src/
│   │   ├── App.vue          # Componente raíz con pestañas y barra ergonómica
│   │   ├── assets/          # Estilos CSS del tema "Oro Antiguo Erudito"
│   │   ├── components/      # DocumentViewer, DictionarySearch, TranslationPopover, etc.
│   │   ├── composables/     # useZoomPan, useCoordinateScaler, useSpeech
│   │   ├── stores/          # documentStore (Pinia)
│   │   ├── services/        # Implementaciones de bridges (PyWebView, Android, Mock)
│   │   └── utils/           # Utilidades de caracteres Hanzi y Pinyin
│   └── tests/               # Pruebas unitarias de componentes y stores (Vitest)
└── packaging/               # Configuración de empaquetado autónomo
    ├── app.spec             # Especificación de PyInstaller para binario de escritorio
    └── dist/                # Directorio de salida del ejecutable empaquetado
```

---

## 💻 Prerrequisitos del Sistema

Asegúrate de contar con las siguientes herramientas instaladas según las plataformas que desees ejecutar:

### 1. Requisitos para Backend y Escritorio (PC)
* **Linux** (Ubuntu 22.04+, Debian 12+, Fedora, Arch) o **Windows 10/11**.
* **Python >= 3.12** instalado.
* **[uv](https://docs.astral.sh/uv/)** (gestor de paquetes ultrarrápido para Python):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
* **Bibliotecas del sistema (solo en Linux para interfaz Qt/PyWebView):**
  * En Ubuntu/Debian:
    ```bash
    sudo apt-get update && sudo apt-get install -y \
      build-essential libgl1 libglx-mesa0 libegl1 \
      libpulse0 libasound2 libnss3 libxcomposite1 libxcursor1 \
      libxi6 libxtst6 libxrandr2
    ```

### 2. Requisitos para Frontend
* **Node.js >= 20.x** (LTS recomendado).
* **[pnpm](https://pnpm.io/)** (gestor de dependencias estricto y eficiente):
  ```bash
  corepack enable && corepack prepare pnpm@latest --activate
  # O alternativamente:
  npm install -g pnpm
  ```

### 3. Requisitos para Android (Opcional, para compilar y probar en móvil)
* **Java Development Kit (JDK) 21**:
  ```bash
  # En Ubuntu/Debian:
  sudo apt-get install -y openjdk-21-jdk
  ```
* **Android SDK (API Level 34)** y **Command-line Tools**:
  * Configura tu variable de entorno en `~/.bashrc` o `~/.zshrc`:
    ```bash
    export ANDROID_SDK=$HOME/Android/Sdk
    export PATH=$ANDROID_SDK/cmdline-tools/latest/bin:$ANDROID_SDK/platform-tools:$PATH
    ```
* **Emulador AVD o Dispositivo Físico** con Depuración por USB habilitada.

---

## ⚡ Instalación Rápida

El repositorio incluye un `Makefile` que automatiza la instalación simultánea de todas las dependencias del backend de Python y del frontend:

```bash
# 1. Clonar o acceder a la carpeta del proyecto
cd traslate-moon-shang

# 2. Instalar todas las dependencias de Python (uv) y Node (pnpm)
make install
```

> **¿Qué hace `make install` por debajo?**
> * En `backend/`: ejecuta `uv sync` creando el entorno virtual e instalando todas las librerías necesarias (PaddleOCR, PyMuPDF, FastAPI, PyQt6, PyWebView, etc.).
> * En `frontend/`: ejecuta `pnpm install` descargando los paquetes de Vue 3, Floating UI, HanziWriter, PDF.js y Vitest.

---

## 🚀 Cómo Levantar el Proyecto (Modos de Ejecución)

Dependiendo de tu objetivo de desarrollo o uso, puedes levantar el proyecto en cualquiera de los siguientes modos:

### 1. Modo Desarrollo Frontend Aislado (Mock UI)
Permite trabajar en la interfaz gráfica, el diccionario, las animaciones caligráficas y la reactividad en el navegador **sin necesidad de inicializar Python ni los modelos de OCR**:

```bash
make dev
```
* **URL:** `http://localhost:5173`
* **Comportamiento:** Se activa automáticamente `MockDesktopBridge`, simulando páginas de prueba, coordenadas de caracteres y respuestas de traducción instantáneas.

---

### 2. Modo Aplicación de Escritorio Nativa (Desktop)
Ejecuta la aplicación de escritorio completa en una ventana nativa de alta resolución con el motor gráfico **PyWebView (PyQt6 WebEngine)** y el backend de procesamiento local con **PaddleOCR**:

```bash
make run-desktop
```

> **Consejo para Desarrolladores:** Si deseas modificar el frontend en caliente mientras pruebas en la ventana de escritorio nativa:
> ```bash
> # Terminal 1: Inicia el servidor de desarrollo de Vite
> cd frontend && pnpm dev
>
> # Terminal 2: Abre la ventana de escritorio apuntando al servidor local
> cd backend && uv run python src/main.py --dev
> ```

---

### 3. Modo Servidor Backend FastAPI (API Server)
Levanta la API REST de procesamiento documental, OCR, fonética Pinyin, audio TTS y traducción. Es utilizada por la aplicación móvil Android o para consumo web:

```bash
make run-server
```
* **Host:** `http://0.0.0.0:8000`
* **Documentación interactiva Swagger UI:** `http://localhost:8000/docs`
* **Endpoints principales:**
  * `GET /health`: Verificación de salud y estado del servicio.
  * `POST /api/translate`: Traducción de caracteres chinos con fonética y caché.
  * `GET /api/pinyin`: Transcripción Pinyin con tonos.
  * `GET /api/audio`: Generación y descarga de archivo MP3 de pronunciación en mandarín.
  * `POST /api/process-page`: Procesamiento OCR y extracción de tokens de una imagen o página PDF.

---

### 4. Modo Aplicación Móvil Android (APK & Emulador)

El monorepo cuenta con automatización completa para compilar y desplegar en Android:

#### Paso 4.1: Sincronizar Frontend y Compilar APK
```bash
# Compila el frontend para producción, copia los assets a Android y genera el APK Debug:
make mobile-build
```
El archivo `.apk` generado se ubicará en:
`android/app/build/outputs/apk/debug/app-debug.apk`

#### Paso 4.2: Levantar el Emulador Oficial y Desplegar la App
Si tienes configurado el Android SDK:

```bash
# 1. Descarga la imagen del sistema y crea el dispositivo virtual Pixel 7 (API 34)
make mobile-emu-setup

# 2. Inicia la ventana del emulador
make mobile-emu-start

# 3. Espera a que el emulador inicie, instala el APK y abre Moon Shang automáticamente
make mobile-emu-deploy
```

#### Paso 4.3: Instalación en Dispositivo Físico
Conecta tu teléfono Android por cable USB (con Depuración USB activada) y ejecuta:
```bash
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

---

## 📦 Empaquetado y Distribución

### Compilación del Frontend
Para compilar la aplicación Vue 3 optimizada para producción:
```bash
make build
```
Los archivos estáticos se generarán en `frontend/dist/`.

### Binario Autónomo de Escritorio (PyInstaller)
Para generar un ejecutable independiente de la aplicación de escritorio (sin requerir que el usuario final tenga Python instalado):
```bash
make package
```
El ejecutable autónomo y sus dependencias se generarán en:
`packaging/dist/MoonShangTranslator/MoonShangTranslator`

---

## ⚙️ Configuración y Variables de Entorno

La aplicación funciona de forma **100% autónoma y gratuita** sin requerir ninguna clave de API obligatoria:
* Utiliza por defecto el adaptador `FreeWebTranslatorAdapter` (con Google Translate GTX público, MyMemory API y diccionario local).
* Almacena las traducciones en `translations.db` (SQLite) para evitar reconsultar términos ya analizados.

### Configuración Opcional con Google Gemini
Si deseas que las traducciones al español sean enriquecidas mediante los modelos de Inteligencia Artificial de Google Gemini:

1. Crea un archivo `.env` en la raíz del proyecto o en `backend/.env`:
   ```env
   GEMINI_API_KEY=tu_clave_de_api_aqui
   ```
2. Al reiniciar la aplicación o el servidor, el sistema detectará automáticamente la clave y utilizará `GeminiTranslatorAdapter` con respaldo web automático en caso de fallas de red.

---

## 🧪 Testing, Linting y Seguridad

El proyecto cuenta con una cobertura integral de pruebas automatizadas en las tres capas del sistema (**153 pruebas unitarias y de integración pasando al 100%**):

### Ejecutar Pruebas
```bash
# Ejecutar todas las pruebas del monorepo (Backend + Frontend + Android)
make test

# Ejecutar pruebas individuales por capa
make test-backend   # 28 tests en pytest (adaptadores, casos de uso, OCR, PDF)
make test-frontend  # 66 tests en vitest (componentes Vue, Pinia stores, zoom, bridges)
make mobile-test    # 59 tests en Android JUnit 5 (MockK, ML Kit, seguridad WebView)
```

### Verificación de Código y Linters
```bash
# Linter de Python (Ruff) y verificación de tipos TypeScript (vue-tsc)
make lint
```

### Auditoría de Seguridad (SAST y Análisis de CVEs)
```bash
# Escaneo de vulnerabilidades en código con Bandit y análisis de dependencias
make audit
```

---

## 📋 Referencia de Comandos (`Makefile`)

| Comando | Descripción |
| :--- | :--- |
| `make install` | Instala dependencias completas del backend (`uv`) y frontend (`pnpm`). |
| `make dev` | Inicia el servidor de desarrollo Vite con interfaz reactiva y mock bridge. |
| `make run-desktop` | Inicia la aplicación de escritorio nativa PyWebView con backend local. |
| `make run-server` | Inicia el servidor FastAPI de Moon Shang en `0.0.0.0:8000`. |
| `make mobile-sync` | Compila el frontend y sincroniza el bundle con los assets de Android. |
| `make mobile-build` | Sincroniza assets y compila el APK Debug de Android. |
| `make mobile-emu-setup` | Descarga paquetes oficiales y crea el AVD `MoonShang_Pixel7`. |
| `make mobile-emu-start` | Inicia el emulador de Android en pantalla. |
| `make mobile-emu-deploy` | Espera al dispositivo, instala el APK y abre la aplicación. |
| `make mobile-test` | Ejecuta las pruebas unitarias de Android en JVM con JUnit 5. |
| `make test` | Ejecuta la suite de pruebas completa de las 3 capas (153 tests). |
| `make lint` | Ejecuta análisis estático con Ruff y comprobación de tipos con `vue-tsc`. |
| `make audit` | Analiza código con Bandit SAST y dependencias con `pip-audit` y `pnpm audit`. |
| `make build` | Compila el frontend para producción en `frontend/dist`. |
| `make package` | Compila el ejecutable nativo para PC con PyInstaller. |
| `make clean` | Limpia cachés temporales (`.pytest_cache`, `__pycache__`, builds). |
| `make help` | Muestra la ayuda interactiva de comandos disponibles. |

---

## ❓ Solución de Problemas (FAQ / Troubleshooting)

### 1. Error de locales numéricos en Linux (`ValueError / Protobuf Float Parse`)
En algunos entornos Linux con configuraciones regionales en español (`es_ES.UTF-8`), el separador decimal puede ser una coma `,` en lugar de un punto `.`, lo cual provoca fallos en los analizadores de C++/Protobuf de PaddleOCR o Qt.
* **Solución aplicada:** Moon Shang fuerza internamente `LC_NUMERIC="C"` en `main.py` de forma automática. Si ejecutas scripts manualmente, puedes exportarlo antes:
  ```bash
  export LC_NUMERIC="C"
  ```

### 2. Error al abrir la ventana gráfica en Linux (`libGL error / Qt platform plugin xcb`)
Si al ejecutar `make run-desktop` recibes un error indicando que falta el plugin `xcb` o librerías de OpenGL:
* Instala las dependencias gráficas de Qt6:
  ```bash
  sudo apt-get install -y libxcb-cursor0 libxkbcommon-x11-0 libgl1-mesa-glx
  ```

### 3. El emulador de Android no inicia o `avdmanager` no se encuentra
* Verifica que la variable `ANDROID_SDK` apunte a la ruta correcta de tu SDK (por ejemplo `/home/usuario/Android/Sdk`).
* Puedes sobreescribir la ruta en el comando de Make:
  ```bash
  make mobile-emu-start ANDROID_SDK=/mi/ruta/Android/Sdk
  ```

### 4. Permisos de Cámara o Portapapeles en Android
* En Android, el acceso a la cámara utiliza `FileProvider` con URIs protegidas y solicita permisos en tiempo de ejecución.
* El copiado al portapapeles se realiza de forma nativa a través del servicio del sistema `ClipboardManager` para evitar restricciones de foco en el WebView móvil.

---

<p align="center">
  Desarrollado con dedicación para el estudio y lectura fluida del idioma chino. 🏮<br>
  <b>Moon Shang — 墨裳</b>
</p>

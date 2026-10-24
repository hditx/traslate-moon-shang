.PHONY: all install dev test test-backend test-frontend lint lint-backend lint-frontend audit audit-backend audit-frontend build package clean run-desktop run-server mobile-sync mobile-test help

SHELL := /bin/bash
PATH := $(HOME)/.local/bin:$(PATH)

all: test lint

help:
	@echo "=================================================================="
	@echo "🏮 Moon Shang - Traductor Chino (Monorepo Orchestrator)"
	@echo "=================================================================="
	@echo "  make install        Instala dependencias de backend (uv) y frontend (pnpm)"
	@echo "  make dev            Inicia el servidor de desarrollo de Vue (Vite)"
	@echo "  make run-desktop    Ejecuta la app de escritorio en modo local"
	@echo "  make test           Ejecuta todas las pruebas unitarias y E2E"
	@echo "  make lint           Ejecuta verificación de tipos y linters (Ruff + vue-tsc)"
	@echo "  make mobile-build   Compila el APK Debug (frontend sincronizado)"
	@echo "  make mobile-emu-setup Descarga paquetes oficiales y crea el AVD MoonShang_Pixel7"
	@echo "  make mobile-emu-start Inicia la ventana del emulador en pantalla"
	@echo "  make mobile-emu-deploy Instala y abre la app en el emulador activo"
	@echo "  make build          Compila el frontend para producción"
	@echo "  make package        Compila el ejecutable nativo con PyInstaller"
	@echo "  make clean          Limpia artefactos generados y cachés temporales"
	@echo "=================================================================="

install:
	@echo "📦 Instalando dependencias de Python con uv..."
	cd backend && uv sync
	@echo "📦 Instalando dependencias de Frontend con pnpm..."
	cd frontend && pnpm install

dev:
	@echo "🚀 Iniciando servidor frontend Vite..."
	cd frontend && pnpm dev

run-desktop:
	@echo "🖥️  Iniciando aplicación de escritorio..."
	cd backend && uv run python src/main.py

run-server:
	@echo "🌐 Iniciando servidor FastAPI Moon Shang en 0.0.0.0:8000..."
	cd backend && uv run uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload

mobile-sync: build
	@echo "📦 Sincronizando bundle de frontend a los assets de Android..."
	rm -rf android/app/src/main/assets/*
	mkdir -p android/app/src/main/assets/data
	cp -r frontend/dist/* android/app/src/main/assets/
	cp -r android/assets_data/* android/app/src/main/assets/data/
	@echo "✅ Assets sincronizados en android/app/src/main/assets/"

mobile-test:
	@echo "🧪 Ejecutando pruebas unitarias de Android (JUnit 5 / Java 21 / MockK)..."
	cd android && ./gradlew testDebugUnitTest

ANDROID_SDK ?= $(HOME)/Android/Sdk
EMULATOR ?= $(ANDROID_SDK)/emulator/emulator
AVDMANAGER ?= $(ANDROID_SDK)/cmdline-tools/latest/bin/avdmanager
SDKMANAGER ?= $(ANDROID_SDK)/cmdline-tools/latest/bin/sdkmanager
ADB ?= $(ANDROID_SDK)/platform-tools/adb
AVD_NAME ?= MoonShang_Pixel7

mobile-build: mobile-sync
	@echo "🔨 Compilando APK Debug de Android..."
	cd android && ./gradlew assembleDebug
	@echo "✅ APK generado exitosamente en android/app/build/outputs/apk/debug/app-debug.apk"

mobile-emu-setup:
	@echo "📥 Descargando e instalando componentes del emulador (Google APIs x86_64)..."
	yes | $(SDKMANAGER) --licenses >/dev/null 2>&1 || true
	$(SDKMANAGER) "emulator" "system-images;android-34;google_apis;x86_64"
	@echo "📱 Creando dispositivo virtual $(AVD_NAME)..."
	echo "no" | $(AVDMANAGER) create avd -n $(AVD_NAME) -k "system-images;android-34;google_apis;x86_64" --device "pixel_7" --force
	@echo "✅ Dispositivo virtual $(AVD_NAME) creado con éxito."

mobile-emu-start:
	@echo "🚀 Iniciando emulador $(AVD_NAME) en pantalla..."
	$(EMULATOR) -avd $(AVD_NAME) -netdelay none -netspeed full &

mobile-emu-deploy: mobile-build
	@echo "⏳ Esperando a que el emulador esté listo..."
	$(ADB) wait-for-device
	@echo "📦 Instalando APK en el emulador..."
	$(ADB) install -r android/app/build/outputs/apk/debug/app-debug.apk
	@echo "🚀 Abriendo Moon Shang en el emulador..."
	$(ADB) shell am start -n com.moonshang.translator/.MainActivity
	@echo "✨ ¡App abierta en el emulador!"

test: test-backend test-frontend mobile-test
	@echo "🎉 Todas las pruebas unitarias del monorepo pasaron exitosamente (Backend + Frontend + Android)."

test-backend:
	@echo "🧪 Ejecutando pruebas de Backend (pytest)..."
	cd backend && uv run pytest

test-frontend:
	@echo "🧪 Ejecutando pruebas de Frontend (vitest)..."
	cd frontend && pnpm test:run

lint: lint-backend lint-frontend

lint-backend:
	@echo "🔍 Verificando Backend con Ruff..."
	cd backend && uv run ruff check .

lint-frontend:
	@echo "🔍 Verificando tipos de Frontend con vue-tsc..."
	cd frontend && pnpm vue-tsc --noEmit

audit: audit-backend audit-frontend

audit-backend:
	@echo "🛡️  Escaneando vulnerabilidades de código en Backend (Bandit SAST)..."
	cd backend && uv run bandit -r src -ll
	@echo "🛡️  Escaneando CVEs en dependencias de Python (pip-audit)..."
	cd backend && uv run pip-audit --desc

audit-frontend:
	@echo "🛡️  Escaneando CVEs en dependencias de Frontend (pnpm audit)..."
	cd frontend && pnpm audit --prod

build:
	@echo "🏗️  Compilando frontend para producción..."
	cd frontend && pnpm build

package: build
	@echo "📦 Compilando aplicación de escritorio autónoma con PyInstaller..."
	cd backend && uv run pyinstaller --noconfirm --distpath ../packaging/dist --workpath ../packaging/build ../packaging/app.spec

clean:
	@echo "🧹 Limpiando cachés y artefactos..."
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/__pycache__
	rm -rf frontend/dist frontend/.vitest
	rm -rf packaging/dist packaging/build
	find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

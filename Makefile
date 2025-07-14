# Universal Camera Viewer - Makefile
# Comandos profesionales de desarrollo y despliegue
# Proyecto: Visor Universal de Cámaras Multi-Marca

.PHONY: help install install-dev test test-cov lint format clean run run-legacy build pre-commit docs security backup

# Comandos predeterminados de Python y herramientas
PYTHON := python
PIP := pip
PYTEST := pytest
BLACK := black
ISORT := isort
FLAKE8 := flake8
MYPY := mypy
BANDIT := bandit

# Directorios del proyecto
SRC_DIR := src-python
FRONTEND_DIR := src
TEST_DIR := tests
EXAMPLES_DIR := examples
CONFIG_DIR := config
DATA_DIR := data

# Colores para salida en terminal (mejora la experiencia de usuario)
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
RESET := \033[0m

##@ Ayuda

help: ## Mostrar este mensaje de ayuda
	@echo "$(CYAN)Universal Camera Viewer - Comandos de Desarrollo$(RESET)"
	@echo "$(WHITE)Visor Universal de Cámaras Multi-Marca v0.7.0$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso:\n  make $(CYAN)<comando>$(RESET)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(PURPLE)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Instalación

install: ## Instalar dependencias de producción
	@echo "$(YELLOW)Instalando dependencias de producción...$(RESET)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Dependencias de producción instaladas$(RESET)"

install-dev: install ## Instalar dependencias de desarrollo
	@echo "$(YELLOW)Instalando dependencias de desarrollo...$(RESET)"
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)✓ Dependencias de desarrollo instaladas$(RESET)"

install-pre-commit: install-dev ## Instalar y configurar hooks de pre-commit
	@echo "$(YELLOW)Configurando hooks de pre-commit...$(RESET)"
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Hooks de pre-commit instalados$(RESET)"

##@ Desarrollo

run: ## Ejecutar la aplicación Flet (principal)
	@echo "$(BLUE)🚀 Iniciando Universal Camera Viewer (Flet)...$(RESET)"
	cd $(SRC_DIR) && $(PYTHON) main.py

run-debug: ## Ejecutar aplicación con salida de depuración
	@echo "$(BLUE)🔍 Iniciando en modo debug...$(RESET)"
	cd $(SRC_DIR) && $(PYTHON) main.py --debug

run-legacy: ## Ejecutar versión legacy de Tkinter (si está disponible)
	@echo "$(BLUE)🕰️  Iniciando versión legacy de Tkinter...$(RESET)"
	@if [ -f "main_tkinter.py" ]; then \
		$(PYTHON) main_tkinter.py; \
	else \
		echo "$(RED)❌ Versión legacy no encontrada$(RESET)"; \
	fi

dev: install-dev run ## Configuración rápida de desarrollo y ejecución

##@ Calidad de Código

format: ## Formatear código con black e isort
	@echo "$(YELLOW)🎨 Formateando código...$(RESET)"
	$(BLACK) $(SRC_DIR) --line-length 88
	$(ISORT) $(SRC_DIR) --profile black
	@echo "$(GREEN)✓ Código formateado correctamente$(RESET)"

lint: ## Ejecutar todas las verificaciones de linting
	@echo "$(YELLOW)🔍 Ejecutando verificaciones de linting...$(RESET)"
	$(FLAKE8) $(SRC_DIR) --max-line-length=88 --extend-ignore=E203,W503
	@echo "$(GREEN)✓ Flake8 ejecutado exitosamente$(RESET)"

type-check: ## Ejecutar verificación de tipos con mypy
	@echo "$(YELLOW)🔍 Ejecutando verificación de tipos...$(RESET)"
	$(MYPY) $(SRC_DIR) --ignore-missing-imports
	@echo "$(GREEN)✓ Verificación de tipos completada$(RESET)"

security: ## Ejecutar análisis de seguridad con bandit
	@echo "$(YELLOW)🔒 Ejecutando análisis de seguridad...$(RESET)"
	$(BANDIT) -r $(SRC_DIR) -f json -o security-report.json || true
	$(BANDIT) -r $(SRC_DIR)
	@echo "$(GREEN)✓ Análisis de seguridad completado$(RESET)"

pre-commit: ## Ejecutar hooks de pre-commit en todos los archivos
	@echo "$(YELLOW)🚀 Ejecutando hooks de pre-commit...$(RESET)"
	pre-commit run --all-files
	@echo "$(GREEN)✓ Verificaciones de pre-commit completadas$(RESET)"

check-all: format lint type-check security ## Ejecutar todas las verificaciones de calidad
	@echo "$(GREEN)✅ Todas las verificaciones de calidad completadas$(RESET)"

##@ Pruebas y Testing

test: ## Ejecutar pruebas con pytest
	@echo "$(YELLOW)🧪 Ejecutando pruebas...$(RESET)"
	$(PYTEST) $(TEST_DIR) -v
	@echo "$(GREEN)✓ Pruebas completadas$(RESET)"

test-cov: ## Ejecutar pruebas con reporte de cobertura
	@echo "$(YELLOW)📊 Ejecutando pruebas con cobertura...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Reporte de cobertura generado en htmlcov/$(RESET)"

test-watch: ## Ejecutar pruebas en modo observación
	@echo "$(YELLOW)👀 Ejecutando pruebas en modo observación...$(RESET)"
	$(PYTEST) $(TEST_DIR) -f

test-examples: ## Probar scripts de ejemplo
	@echo "$(YELLOW)📋 Probando scripts de ejemplo...$(RESET)"
	@for script in $(EXAMPLES_DIR)/testing/*.py; do \
		echo "Probando $$script..."; \
		$(PYTHON) $$script || echo "$(RED)❌ $$script falló$(RESET)"; \
	done
	@echo "$(GREEN)✓ Pruebas de ejemplos completadas$(RESET)"

##@ Base de Datos y Datos

db-backup: ## Hacer respaldo de la base de datos de cámaras
	@echo "$(YELLOW)💾 Creando respaldo de base de datos...$(RESET)"
	@mkdir -p $(DATA_DIR)/backups
	@cp $(DATA_DIR)/camera_data.db $(DATA_DIR)/backups/camera_data_backup_$$(date +%Y%m%d_%H%M%S).db
	@echo "$(GREEN)✓ Base de datos respaldada$(RESET)"

db-clean: ## Limpiar caché de base de datos
	@echo "$(YELLOW)🧹 Limpiando caché de base de datos...$(RESET)"
	@rm -rf $(DATA_DIR)/cache/*
	@echo "$(GREEN)✓ Caché de base de datos limpiado$(RESET)"

##@ Limpieza y Mantenimiento

clean: ## Limpiar archivos temporales y cachés
	@echo "$(YELLOW)🧹 Limpiando archivos temporales...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -f security-report.json
	@echo "$(GREEN)✓ Limpieza completada$(RESET)"

clean-all: clean ## Limpieza profunda incluyendo cachés de datos
	@echo "$(YELLOW)🧹 Ejecutando limpieza profunda...$(RESET)"
	rm -rf $(DATA_DIR)/cache/*
	rm -rf $(DATA_DIR)/snapshots/*
	@echo "$(GREEN)✓ Limpieza profunda completada$(RESET)"

##@ Documentación

docs: ## Generar documentación del proyecto
	@echo "$(YELLOW)📚 Generando documentación...$(RESET)"
	@echo "$(BLUE)Documentación del proyecto disponible en:$(RESET)"
	@echo "  - README.md"
	@echo "  - CURRENT_STATUS.md" 
	@echo "  - CHANGELOG.md"
	@echo "$(GREEN)✓ Documentación lista$(RESET)"

##@ Empaquetado y Distribución

build: clean ## Construir paquetes de distribución
	@echo "$(YELLOW)📦 Construyendo paquetes de distribución...$(RESET)"
	$(PYTHON) -m build
	@echo "$(GREEN)✓ Paquetes de distribución construidos en dist/$(RESET)"

build-app: ## Construir aplicación independiente con Flet
	@echo "$(YELLOW)📱 Construyendo aplicación independiente...$(RESET)"
	cd $(SRC_DIR) && flet pack main.py --name "Universal Camera Viewer" --icon ../assets/icon.ico
	@echo "$(GREEN)✓ Aplicación independiente construida$(RESET)"

release-check: ## Verificar si está listo para lanzamiento
	@echo "$(YELLOW)🔍 Verificando preparación para lanzamiento...$(RESET)"
	$(PYTHON) -m twine check dist/*
	@echo "$(GREEN)✓ Verificación de lanzamiento completada$(RESET)"

##@ Configuración

config-backup: ## Respaldar archivos de configuración
	@echo "$(YELLOW)💾 Respaldando configuración...$(RESET)"
	@mkdir -p $(CONFIG_DIR)/backups
	@cp $(CONFIG_DIR)/*.json $(CONFIG_DIR)/backups/ 2>/dev/null || true
	@echo "$(GREEN)✓ Configuración respaldada$(RESET)"

config-restore: ## Restaurar configuración desde respaldo
	@echo "$(YELLOW)📁 Respaldos de configuración disponibles:$(RESET)"
	@ls -la $(CONFIG_DIR)/backups/ || echo "$(RED)No se encontraron respaldos$(RESET)"

##@ Monitoreo y Análisis

performance: ## Ejecutar análisis de rendimiento
	@echo "$(YELLOW)⚡ Ejecutando análisis de rendimiento...$(RESET)"
	cd $(EXAMPLES_DIR)/testing && $(PYTHON) performance_test.py
	@echo "$(GREEN)✓ Análisis de rendimiento completado$(RESET)"

network-test: ## Probar conectividad de red para cámaras
	@echo "$(YELLOW)🌐 Probando conectividad de red...$(RESET)"
	cd $(EXAMPLES_DIR)/diagnostics && $(PYTHON) network_analyzer.py
	@echo "$(GREEN)✓ Prueba de red completada$(RESET)"

##@ Comandos Rápidos

all: install-dev check-all test ## Configuración completa de desarrollo y validación
	@echo "$(GREEN)🎉 ¡Todas las verificaciones pasaron! Listo para desarrollo$(RESET)"

ci: format lint test ## Verificaciones de integración continua
	@echo "$(GREEN)✅ Verificaciones de CI completadas$(RESET)"

fresh-start: clean-all install-dev install-pre-commit run ## Inicio fresco de desarrollo
	@echo "$(GREEN)🌟 Inicio fresco completado$(RESET)"

##@ Información

status: ## Mostrar estado del proyecto
	@echo "$(CYAN)📊 Estado de Universal Camera Viewer$(RESET)"
	@echo "$(YELLOW)Versión:$(RESET) 0.7.0"
	@echo "$(YELLOW)Python:$(RESET) $$($(PYTHON) --version)"
	@echo "$(YELLOW)Arquitectura:$(RESET) Patrón MVP (65% completo)"
	@echo "$(YELLOW)Framework UI:$(RESET) Flet + Material Design 3"
	@echo "$(YELLOW)Marcas de Cámaras:$(RESET) Dahua, TP-Link, Steren, Genérica"
	@echo "$(YELLOW)Protocolos:$(RESET) ONVIF, RTSP, HTTP/CGI"
	@echo ""
	@echo "$(GREEN)📁 Estructura del Proyecto:$(RESET)"
	@echo "  src/          - Código fuente (arquitectura MVP)"
	@echo "  tests/        - Suites de pruebas"
	@echo "  examples/     - Scripts de ejemplo y diagnósticos"
	@echo "  config/       - Archivos de configuración"
	@echo "  data/         - Base de datos y caché"

version: ## Mostrar información de versión
	@echo "$(CYAN)Universal Camera Viewer v0.7.0$(RESET)"
	@echo "$(BLUE)Visor de cámaras multi-marca con UI moderna en Flet$(RESET)" 
# Universal Camera Viewer - Makefile
# Professional development and deployment commands

.PHONY: help install install-dev test test-cov lint format clean run run-legacy build pre-commit docs security backup

# Default Python and pip commands
PYTHON := python
PIP := pip
PYTEST := pytest
BLACK := black
ISORT := isort
FLAKE8 := flake8
MYPY := mypy
BANDIT := bandit

# Project directories
SRC_DIR := src
TEST_DIR := tests
EXAMPLES_DIR := examples
CONFIG_DIR := config
DATA_DIR := data

# Colors for terminal output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[0;37m
RESET := \033[0m

##@ Help

help: ## Display this help message
	@echo "$(CYAN)Universal Camera Viewer - Development Commands$(RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(CYAN)<target>$(RESET)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(PURPLE)%s$(RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Installation

install: ## Install production dependencies
	@echo "$(YELLOW)Installing production dependencies...$(RESET)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Production dependencies installed$(RESET)"

install-dev: install ## Install development dependencies
	@echo "$(YELLOW)Installing development dependencies...$(RESET)"
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)✓ Development dependencies installed$(RESET)"

install-pre-commit: install-dev ## Install and setup pre-commit hooks
	@echo "$(YELLOW)Setting up pre-commit hooks...$(RESET)"
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Pre-commit hooks installed$(RESET)"

##@ Development

run: ## Run the Flet application (main)
	@echo "$(BLUE)🚀 Starting Universal Camera Viewer (Flet)...$(RESET)"
	cd $(SRC_DIR) && $(PYTHON) main.py

run-debug: ## Run application with debug output
	@echo "$(BLUE)🔍 Starting with debug mode...$(RESET)"
	cd $(SRC_DIR) && $(PYTHON) main.py --debug

run-legacy: ## Run legacy Tkinter version (if available)
	@echo "$(BLUE)🕰️  Starting legacy Tkinter version...$(RESET)"
	@if [ -f "main_tkinter.py" ]; then \
		$(PYTHON) main_tkinter.py; \
	else \
		echo "$(RED)❌ Legacy version not found$(RESET)"; \
	fi

dev: install-dev run ## Quick development setup and run

##@ Code Quality

format: ## Format code with black and isort
	@echo "$(YELLOW)🎨 Formatting code...$(RESET)"
	$(BLACK) $(SRC_DIR) --line-length 88
	$(ISORT) $(SRC_DIR) --profile black
	@echo "$(GREEN)✓ Code formatted$(RESET)"

lint: ## Run all linting checks
	@echo "$(YELLOW)🔍 Running linting checks...$(RESET)"
	$(FLAKE8) $(SRC_DIR) --max-line-length=88 --extend-ignore=E203,W503
	@echo "$(GREEN)✓ Flake8 passed$(RESET)"

type-check: ## Run type checking with mypy
	@echo "$(YELLOW)🔍 Running type checks...$(RESET)"
	$(MYPY) $(SRC_DIR) --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking passed$(RESET)"

security: ## Run security checks with bandit
	@echo "$(YELLOW)🔒 Running security analysis...$(RESET)"
	$(BANDIT) -r $(SRC_DIR) -f json -o security-report.json || true
	$(BANDIT) -r $(SRC_DIR)
	@echo "$(GREEN)✓ Security analysis completed$(RESET)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(YELLOW)🚀 Running pre-commit hooks...$(RESET)"
	pre-commit run --all-files
	@echo "$(GREEN)✓ Pre-commit checks completed$(RESET)"

check-all: format lint type-check security ## Run all code quality checks
	@echo "$(GREEN)✅ All quality checks completed$(RESET)"

##@ Testing

test: ## Run tests with pytest
	@echo "$(YELLOW)🧪 Running tests...$(RESET)"
	$(PYTEST) $(TEST_DIR) -v
	@echo "$(GREEN)✓ Tests completed$(RESET)"

test-cov: ## Run tests with coverage report
	@echo "$(YELLOW)📊 Running tests with coverage...$(RESET)"
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(RESET)"

test-watch: ## Run tests in watch mode
	@echo "$(YELLOW)👀 Running tests in watch mode...$(RESET)"
	$(PYTEST) $(TEST_DIR) -f

test-examples: ## Test example scripts
	@echo "$(YELLOW)📋 Testing example scripts...$(RESET)"
	@for script in $(EXAMPLES_DIR)/testing/*.py; do \
		echo "Testing $$script..."; \
		$(PYTHON) $$script || echo "$(RED)❌ $$script failed$(RESET)"; \
	done
	@echo "$(GREEN)✓ Example tests completed$(RESET)"

##@ Database & Data

db-backup: ## Backup camera database
	@echo "$(YELLOW)💾 Creating database backup...$(RESET)"
	@mkdir -p $(DATA_DIR)/backups
	@cp $(DATA_DIR)/camera_data.db $(DATA_DIR)/backups/camera_data_backup_$$(date +%Y%m%d_%H%M%S).db
	@echo "$(GREEN)✓ Database backed up$(RESET)"

db-clean: ## Clean database cache
	@echo "$(YELLOW)🧹 Cleaning database cache...$(RESET)"
	@rm -rf $(DATA_DIR)/cache/*
	@echo "$(GREEN)✓ Database cache cleaned$(RESET)"

##@ Cleanup

clean: ## Clean temporary files and caches
	@echo "$(YELLOW)🧹 Cleaning temporary files...$(RESET)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -f security-report.json
	@echo "$(GREEN)✓ Cleanup completed$(RESET)"

clean-all: clean ## Deep clean including data caches
	@echo "$(YELLOW)🧹 Deep cleaning...$(RESET)"
	rm -rf $(DATA_DIR)/cache/*
	rm -rf $(DATA_DIR)/snapshots/*
	@echo "$(GREEN)✓ Deep cleanup completed$(RESET)"

##@ Documentation

docs: ## Generate documentation
	@echo "$(YELLOW)📚 Generating documentation...$(RESET)"
	@echo "$(BLUE)Project documentation available in:$(RESET)"
	@echo "  - README.md"
	@echo "  - CURRENT_STATUS.md" 
	@echo "  - CHANGELOG.md"
	@echo "$(GREEN)✓ Documentation ready$(RESET)"

##@ Packaging & Distribution

build: clean ## Build distribution packages
	@echo "$(YELLOW)📦 Building distribution packages...$(RESET)"
	$(PYTHON) -m build
	@echo "$(GREEN)✓ Distribution packages built in dist/$(RESET)"

build-app: ## Build standalone application with Flet
	@echo "$(YELLOW)📱 Building standalone application...$(RESET)"
	cd $(SRC_DIR) && flet pack main.py --name "Universal Camera Viewer" --icon ../assets/icon.ico
	@echo "$(GREEN)✓ Standalone application built$(RESET)"

release-check: ## Check if ready for release
	@echo "$(YELLOW)🔍 Checking release readiness...$(RESET)"
	$(PYTHON) -m twine check dist/*
	@echo "$(GREEN)✓ Release check completed$(RESET)"

##@ Configuration

config-backup: ## Backup configuration files
	@echo "$(YELLOW)💾 Backing up configuration...$(RESET)"
	@mkdir -p $(CONFIG_DIR)/backups
	@cp $(CONFIG_DIR)/*.json $(CONFIG_DIR)/backups/ 2>/dev/null || true
	@echo "$(GREEN)✓ Configuration backed up$(RESET)"

config-restore: ## Restore configuration from backup
	@echo "$(YELLOW)📁 Available configuration backups:$(RESET)"
	@ls -la $(CONFIG_DIR)/backups/ || echo "$(RED)No backups found$(RESET)"

##@ Monitoring & Analysis

performance: ## Run performance analysis
	@echo "$(YELLOW)⚡ Running performance analysis...$(RESET)"
	cd $(EXAMPLES_DIR)/testing && $(PYTHON) performance_test.py
	@echo "$(GREEN)✓ Performance analysis completed$(RESET)"

network-test: ## Test network connectivity for cameras
	@echo "$(YELLOW)🌐 Testing network connectivity...$(RESET)"
	cd $(EXAMPLES_DIR)/diagnostics && $(PYTHON) network_analyzer.py
	@echo "$(GREEN)✓ Network test completed$(RESET)"

##@ Quick Commands

all: install-dev check-all test ## Full development setup and validation
	@echo "$(GREEN)🎉 All checks passed! Ready for development$(RESET)"

ci: format lint test ## Continuous integration checks
	@echo "$(GREEN)✅ CI checks completed$(RESET)"

fresh-start: clean-all install-dev pre-commit run ## Fresh development start
	@echo "$(GREEN)🌟 Fresh start completed$(RESET)"

##@ Information

status: ## Show project status
	@echo "$(CYAN)📊 Universal Camera Viewer Status$(RESET)"
	@echo "$(YELLOW)Version:$(RESET) 0.7.0"
	@echo "$(YELLOW)Python:$(RESET) $$($(PYTHON) --version)"
	@echo "$(YELLOW)Architecture:$(RESET) MVP Pattern (65% complete)"
	@echo "$(YELLOW)UI Framework:$(RESET) Flet + Material Design 3"
	@echo "$(YELLOW)Camera Brands:$(RESET) Dahua, TP-Link, Steren, Generic"
	@echo "$(YELLOW)Protocols:$(RESET) ONVIF, RTSP, HTTP/CGI"
	@echo ""
	@echo "$(GREEN)📁 Project Structure:$(RESET)"
	@echo "  src/          - Source code (MVP architecture)"
	@echo "  tests/        - Test suites"
	@echo "  examples/     - Example scripts and diagnostics"
	@echo "  config/       - Configuration files"
	@echo "  data/         - Database and cache"

version: ## Show version information
	@echo "$(CYAN)Universal Camera Viewer v0.7.0$(RESET)"
	@echo "$(BLUE)Multi-brand camera viewer with modern Flet UI$(RESET)" 
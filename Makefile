# =============================================================================
# Stage A — Makefile
# =============================================================================
# Usage:
#   make              — show help
#   make validate     — validate all contracts
#   make test         — run unit tests
#   make all          — validate + test (full check)
#   make quick        — quick validation only (no tests)
#   make new          — generate new contract template (interactive)
#   make clean        — remove generated reports
# =============================================================================

.PHONY: help all validate test quick new clean lint

# Default Python interpreter
PYTHON ?= python3

# Paths
CONTRACTS_DIR := stageA/contracts
SCHEMA := stageA/schema/contract_schema_stageA_v4.json
GLOSSARY := stageA/glossary/glossary_v1.json
REPORTS_DIR := stageA/_reports

# Colors (optional, for pretty output)
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# =============================================================================
# HELP (default target)
# =============================================================================
help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║              Stage A — Make Commands                         ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "  make all        — Full validation + tests (recommended)"
	@echo "  make validate   — Validate all contracts"
	@echo "  make test       — Run unit tests"
	@echo "  make quick      — Quick validation (skip tests)"
	@echo "  make lint       — Lint contracts with verbose output"
	@echo "  make new        — Generate new contract from template"
	@echo "  make clean      — Remove generated reports"
	@echo ""
	@echo "Examples:"
	@echo "  make all"
	@echo "  make new MODULE_ID=A-V-1 ABBR=TONE TYPE=PROCESS"
	@echo ""

# =============================================================================
# MAIN TARGETS
# =============================================================================

## Full validation + tests
all: validate test
	@echo ""
	@echo "$(GREEN)✅ All checks passed!$(NC)"

## Validate all contracts
validate:
	@echo ""
	@echo "▶ Validating contracts..."
	@mkdir -p $(REPORTS_DIR)
	@$(PYTHON) stageA/tools/batch_validator.py $(CONTRACTS_DIR) \
		--glossary $(GLOSSARY) \
		--schema $(SCHEMA) \
		--out $(REPORTS_DIR) \
		--verbose

## Run unit tests
test:
	@echo ""
	@echo "▶ Running unit tests..."
	@$(PYTHON) -m unittest discover -s stageA/tests -p "test_*.py" -v

## Quick validation (no tests)
quick:
	@echo ""
	@echo "▶ Quick validation..."
	@$(PYTHON) stageA/tools/batch_validator.py $(CONTRACTS_DIR) \
		--glossary $(GLOSSARY) \
		--schema $(SCHEMA)

## Lint with verbose output
lint:
	@echo ""
	@echo "▶ Linting contracts..."
	@$(PYTHON) stageA/tools/batch_validator.py $(CONTRACTS_DIR) \
		--glossary $(GLOSSARY) \
		--schema $(SCHEMA) \
		--out $(REPORTS_DIR) \
		--verbose

# =============================================================================
# GENERATE NEW CONTRACT
# =============================================================================

## Generate new contract from template
## Usage: make new MODULE_ID=A-V-1 ABBR=TONE TYPE=PROCESS NAME_UK="ТОНАЛЬНА КАРТА" NAME_EN="TONE MAP"
new:
ifndef MODULE_ID
	@echo "$(RED)Error: MODULE_ID is required$(NC)"
	@echo "Usage: make new MODULE_ID=A-V-1 ABBR=TONE TYPE=PROCESS NAME_UK=\"...\" NAME_EN=\"...\""
	@exit 1
endif
ifndef ABBR
	@echo "$(RED)Error: ABBR is required$(NC)"
	@exit 1
endif
ifndef TYPE
	@echo "$(RED)Error: TYPE is required (PROCESS/RULESET/BRIDGE)$(NC)"
	@exit 1
endif
	@$(PYTHON) stageA/tools/generate_from_template.py \
		--module-id $(MODULE_ID) \
		--module-abbr $(ABBR) \
		--module-type $(TYPE) \
		--module-name-uk "$(or $(NAME_UK),TODO: Ukrainian name)" \
		--module-name-en "$(or $(NAME_EN),TODO: English name)" \
		--out $(CONTRACTS_DIR)/$(MODULE_ID)_$(ABBR)_contract_stageA_FINAL.json
	@echo ""
	@echo "$(GREEN)✅ Contract created: $(CONTRACTS_DIR)/$(MODULE_ID)_$(ABBR)_contract_stageA_FINAL.json$(NC)"
	@echo "$(YELLOW)→ Don't forget to fill in TODO sections!$(NC)"

# =============================================================================
# CLEANUP
# =============================================================================

## Remove generated reports
clean:
	@echo "▶ Cleaning up..."
	@rm -rf $(REPORTS_DIR)
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Cleaned$(NC)"

# =============================================================================
# CI SIMULATION
# =============================================================================

## Simulate CI pipeline locally
ci: clean all
	@echo ""
	@echo "$(GREEN)✅ CI simulation passed!$(NC)"

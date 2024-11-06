BASE_DIR := $(shell pwd)

REQUIREMENTS_IN ?= $(BASE_DIR)/tests/requirements.in
REQUIREMENTS_COMPILE ?= $(BASE_DIR)/tests/requirements-pip-compile.txt
REQUIREMENTS_FILE ?= $(BASE_DIR)/tests/requirements-raw.txt
PACKAGE_OUTPUT ?= $(BASE_DIR)/output
VENV_PATH ?= $(BASE_DIR)/.venv
ZIP_FILE ?= $(BASE_DIR)/output.zip

venv:
	@echo "Creating virtual environment at $(VENV_PATH) if it doesn't exist..."
	@test -d "$(VENV_PATH)" || python3 -m venv "$(VENV_PATH)"
	@echo "Activating virtual environment and installing pre-commit..."
	. "$(VENV_PATH)/bin/activate" && pip install --upgrade pip pre-commit
	@echo "pre-commit installed in virtual environment."

compile: venv
	@echo "Compiling requirements from $(REQUIREMENTS_IN) to $(REQUIREMENTS_COMPILE)..."
	. "$(VENV_PATH)/bin/activate" && pip-compile -o "$(REQUIREMENTS_COMPILE)" "$(REQUIREMENTS_IN)"
	@if [ $$? -ne 0 ]; then echo "Error: pip-compile failed."; exit 1; fi

download: venv
	@echo "Downloading packages from $(REQUIREMENTS_COMPILE) to $(PACKAGE_OUTPUT)..."
	. "$(VENV_PATH)/bin/activate" && pip download -r "$(REQUIREMENTS_COMPILE)" -d "$(PACKAGE_OUTPUT)"
	@if [ $$? -ne 0 ]; then echo "Error: pip download failed."; exit 1; fi

test: venv
	@echo "Test run: requirements from $(REQUIREMENTS_FILE)..."
	. "$(VENV_PATH)/bin/activate" && pip install -r "$(REQUIREMENTS_FILE)" && dbt -v
	@if [ $$? -ne 0 ]; then echo "Error: pip install for test requirements failed."; exit 1; fi

zip:
	@echo "Zipping $(PACKAGE_OUTPUT) directory to $(ZIP_FILE) with execution rights preserved..."
	@chmod -R 755 $(PACKAGE_OUTPUT)
	@cd $(PACKAGE_OUTPUT) && zip -j "$(ZIP_FILE)" *
	@if [ $$? -ne 0 ]; then echo "Error: Zipping $(PACKAGE_OUTPUT) failed."; exit 1; fi
	@echo "$(PACKAGE_OUTPUT) successfully zipped to $(ZIP_FILE)."

all: compile download
	@echo "All operations completed successfully."

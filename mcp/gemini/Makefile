GEMINI_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
VENV := $(GEMINI_DIR).venv
PYTHON := $(VENV)/bin/python

.PHONY: install start register status

install: ## Install all dependencies into venv
	@echo "Creating venv..."
	uv venv $(VENV)
	@echo "Installing packages..."
	uv pip install mcp google-genai --python $(VENV)/bin/python
	@echo "Installing Gemini CLI..."
	npm install -g @google/gemini-cli
	@echo "Done. Run 'gemini auth' to authenticate the CLI."

start: ## Test-run the MCP server (exits immediately via stdio)
	@echo "Starting Gemini MCP server (Ctrl+C to stop)..."
	$(PYTHON) $(GEMINI_DIR)mcp-server.py

register: ## Register with Claude Code globally (user scope)
	claude mcp add -s user gemini $(PYTHON) $(GEMINI_DIR)mcp-server.py

status: ## Show registered MCP servers
	claude mcp list

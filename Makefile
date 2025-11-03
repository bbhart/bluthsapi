.PHONY: build-BluthsApiFunction

build-BluthsApiFunction:
	# Install Python dependencies (use python3 in container, not python3.13)
	pip install -r requirements.txt -t $(ARTIFACTS_DIR)
	# Copy application code
	cp -r app $(ARTIFACTS_DIR)/
	cp -r public $(ARTIFACTS_DIR)/ 2>/dev/null || true
	# Copy LICENSE and README.md to build directory for SAM packaging
	cp LICENSE $(ARTIFACTS_DIR)/
	cp README.md $(ARTIFACTS_DIR)/

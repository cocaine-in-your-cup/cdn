# Makefile

# Set the name of your Python virtual environment
VENV_NAME := venv

.PHONY: all venv install

all: venv install

# Create a virtual environment
venv:
	@python3 -m venv $(VENV_NAME)
	@$(VENV_NAME)/bin/python -m pip install --upgrade pip

# Install the required packages from requirements.txt
install: venv
	@$(VENV_NAME)/bin/pip install -r requirements.txt

# Build and install python-p2p-master using setup.py
python-p2p-master: venv
	@$(VENV_NAME)/bin/pip install -e python-p2p-master

# Clean the virtual environment
clean:
	@rm -rf $(VENV_NAME)

# Run the main.py script using the virtual environment
run: venv
	@$(VENV_NAME)/bin/python main.py --cdn-url https://cdn-service-api-7nricgvmca-ew.a.run.app/cdn/lb/ip

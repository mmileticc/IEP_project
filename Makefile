# Each service has its own `app` package, so tests run once per service.
TEST_DIRS := services/common services/auth services/employee services/director
PYTHON ?= python

.PHONY: up up-fast down test lint compile-contract

up:            ## Build images and deploy to the local Kubernetes cluster
	./scripts/k8s-up.sh

up-fast:       ## Deploy without rebuilding images
	./scripts/k8s-up.sh --skip-build

down:          ## Delete the namespace and all data
	./scripts/k8s-down.sh

test:          ## Run the unit tests of every service
	@for dir in $(TEST_DIRS); do echo "==> $$dir"; $(PYTHON) -m pytest $$dir || exit 1; done

lint:
	$(PYTHON) -m ruff check .

compile-contract:
	./scripts/compile-contract.sh

# MASDojo convenience targets. See docs/deploy-kvm.md for the full KVM deploy.
.PHONY: help env apps up up-core runner-dryrun down logs ps test test-backend test-runner clean

ANDROID_BUILD_IMAGE ?= mingc/android-build-box:latest

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

env: ## Create .env with fresh secrets if missing
	@test -f .env || (cp .env.example .env && \
		sed -i.bak "s|^JWT_SECRET=.*|JWT_SECRET=$$(openssl rand -hex 32)|" .env && \
		sed -i.bak "s|^MASTER_KEY=.*|MASTER_KEY=$$(python3 -c 'from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())')|" .env && \
		sed -i.bak "s|^INSTALL_SALT=.*|INSTALL_SALT=$$(openssl rand -hex 16)|" .env && \
		rm -f .env.bak && echo "wrote .env")

apps: ## Build the vulnerable target APKs (needs Docker; no host Android SDK)
	docker run --rm -v "$$PWD":/work -w /work $(ANDROID_BUILD_IMAGE) bash infra/build-apps.sh

up: env ## Build + start the FULL stack (requires a KVM host for the runner)
	docker compose up --build -d

up-core: env ## Start everything EXCEPT the runner (works without KVM, e.g. on macOS)
	docker compose up --build -d db redis backend frontend

solo: env ## Run for a single local participant: no login, straight to the curriculum
	@if grep -q '^SOLO_MODE=' .env; then sed -i.bak 's|^SOLO_MODE=.*|SOLO_MODE=true|' .env && rm -f .env.bak; else echo 'SOLO_MODE=true' >> .env; fi
	@grep -qE '^INSTALL_SALT=.+' .env || (echo "INSTALL_SALT=$$(openssl rand -hex 16)" >> .env && sed -i.bak '/^INSTALL_SALT=$$/d' .env && rm -f .env.bak)
	docker compose up --build -d db redis backend frontend vulnapi
	@echo "MASDojo (solo) is up -> http://localhost:5173  (no login; Lab 3 API -> http://localhost:8091)"
	@echo "For live Frida/RASP grading, run the runner on your host against a local AVD (see docs)."

runner-dryrun: ## Start a no-emulator grader (grades flag/static_assert tasks; macOS-friendly)
	docker compose --profile dryrun up --build -d runner-dryrun

doctor: ## Pre-flight: check your machine has everything for the workshop
	bash infra/preflight.sh

avd-up: ## Provision a local AVD (rooted + frida) for live Frida/RASP grading
	bash infra/avd-up.sh

avd-check: ## Pre-flight: confirm the local AVD is ready for live grading
	bash infra/avd-check.sh

runner-host: ## Run the grader on THIS host in attach mode against the local AVD (no KVM)
	cd runner && RUNNER_ATTACH=true \
		DATABASE_URL="postgresql+psycopg://masdojo:masdojo@localhost:5432/masdojo" \
		REDIS_URL="redis://localhost:6379/0" \
		TASKS_ROOT="$(CURDIR)/tasks" \
		python -m runner.worker

down: ## Stop the stack
	docker compose down

logs: ## Tail all logs
	docker compose logs -f

ps: ## Show service status
	docker compose ps

test: test-backend test-runner ## Run all test suites

test-backend: ## Run backend tests
	cd backend && python -m pytest -q

test-runner: ## Run runner tests (dry-run)
	cd runner && RUNNER_DRY_RUN=true python -m pytest -q

clean: ## Stop the stack and remove volumes (wipes the database)
	docker compose down -v

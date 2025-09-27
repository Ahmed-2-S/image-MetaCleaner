# Default kubectl binary/namespace and location of manifests
KUBECTL ?= kubectl
NAMESPACE ?= metacleaner
K8S_DIR := k8s
SECRETS_FILE ?= $(K8S_DIR)/secrets.local.yaml
LOG_FLAGS ?= --follow --tail=200

MANIFESTS_WITH_PVC := \
	$(SECRETS_FILE) \
	$(K8S_DIR)/db-init.yaml \
	$(K8S_DIR)/db-pvc.yaml \
	$(K8S_DIR)/db.yaml \
	$(K8S_DIR)/cleaner.yaml \
	$(K8S_DIR)/app.yaml \
	$(K8S_DIR)/ingress.yaml

MANIFESTS_NO_PVC := $(filter-out $(K8S_DIR)/db-pvc.yaml,$(MANIFESTS_WITH_PVC))


.PHONY: deploy namespace apply down purge status check-secrets-file logs-app logs-cleaner logs-db

# Top-level setup target
deploy: namespace apply

# Namespace must exist before other resources
namespace:
	@echo "Applying namespace manifest"
	@$(KUBECTL) apply -f $(K8S_DIR)/namespace.yaml

# Apply all manifests, including PVC
apply: check-secrets-file
	@$(call kube_apply,$(MANIFESTS_WITH_PVC))

# Tear down workloads but keep PVC for data persistence
down:
	@$(call kube_delete,$(MANIFESTS_NO_PVC))

# Fully remove cluster resources, including storage
purge: down
	@echo "Deleting persistent volume claim"
	@$(KUBECTL) delete --ignore-not-found -f $(K8S_DIR)/db-pvc.yaml
	@echo "Deleting namespace"
	@$(KUBECTL) delete namespace $(NAMESPACE) --ignore-not-found

# Quick cluster status helper
status:
	@$(KUBECTL) get all -n $(NAMESPACE)

# Stream logs for core deployments (override LOG_FLAGS to tweak tail/follow)
logs-app:
	@echo "Streaming logs for metacleaner-app"
	@$(KUBECTL) logs -n $(NAMESPACE) deployment/metacleaner-app $(LOG_FLAGS)

logs-cleaner:
	@echo "Streaming logs for metacleaner-cleaner"
	@$(KUBECTL) logs -n $(NAMESPACE) deployment/metacleaner-cleaner $(LOG_FLAGS)

logs-db:
	@echo "Streaming logs for metacleaner-db"
	@$(KUBECTL) logs -n $(NAMESPACE) deployment/metacleaner-db $(LOG_FLAGS)

# Helper to apply manifests in order
define kube_apply
	for file in $(1); do \
		echo "Applying $$file"; \
		$(KUBECTL) apply -f $$file; \
	done
endef

# Helper to delete manifests while tolerating missing resources
define kube_delete
	for file in $(1); do \
		echo "Deleting $$file"; \
		$(KUBECTL) delete --ignore-not-found -f $$file; \
	done
endef
# Ensure the secrets manifest exists before applying resources
check-secrets-file:
	@if [ ! -f "$(SECRETS_FILE)" ]; then \
		echo "Missing secrets manifest: $(SECRETS_FILE)"; \
		echo "Create it from k8s/secrets.template.yaml before running make deploy"; \
		exit 1; \
	fi

# vaultpatch

> CLI tool to diff and apply secret changes across multiple Vault namespaces

---

## Installation

```bash
pip install vaultpatch
```

Or install from source:

```bash
git clone https://github.com/yourorg/vaultpatch.git && cd vaultpatch && pip install .
```

---

## Usage

```bash
# Diff secrets between two namespaces
vaultpatch diff --source ns/prod --target ns/staging

# Apply changes from a patch file across namespaces
vaultpatch apply --patch changes.yaml --namespaces ns/staging ns/dev

# Dry run to preview changes without applying
vaultpatch apply --patch changes.yaml --namespaces ns/staging --dry-run
```

**Requirements:**
- A running HashiCorp Vault instance
- `VAULT_ADDR` and `VAULT_TOKEN` environment variables set

```bash
export VAULT_ADDR=https://vault.example.com
export VAULT_TOKEN=s.yourtoken
```

---

## Configuration

vaultpatch reads from a `vaultpatch.yaml` config file in the working directory:

```yaml
vault_addr: https://vault.example.com
namespaces:
  - ns/prod
  - ns/staging
  - ns/dev
```

---

## License

MIT © 2024 yourorg
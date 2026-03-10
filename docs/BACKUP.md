# Workspace Backup

Guia de backup de workspace Databricks usando export em formato `.dbc` com compactacao final em `.zip`.

## Visao Geral

O modo de backup exporta objetos do workspace de forma recursiva e gera:

- Pasta com os arquivos exportados (`.dbc`)
- Arquivo `.zip` com todo o backup consolidado

Fluxo:
1. Lista diretorios/objetos recursivamente
2. Exporta item a item via Workspace Export API
3. Salva localmente como `.dbc`
4. Gera um `.zip` final

## Configuracao via `config.yaml`

Arquivo: `.lakeventory/config.yaml`

```yaml
global_config:
  output_dir: ./output
  backup_workspace: true
  backup_output_dir: ./backups
```

- `backup_workspace`: habilita backup antes da coleta
- `backup_output_dir`: diretorio base do backup
  - vazio (`""`) => usa `output_dir`

## Configuracao via variáveis de ambiente (CI/CD)

Para sobrescrever temporariamente em pipelines:

```bash
export BACKUP_WORKSPACE=true
export BACKUP_OUTPUT_DIR=./backups
```

## Prioridade de parametros

Ordem de precedencia:

1. CLI
2. `config.yaml`
3. Variáveis de ambiente (`BACKUP_WORKSPACE`, `BACKUP_OUTPUT_DIR`)

## Comandos

### Backup de um workspace

```bash
python -m lakeventory --workspace prod --backup-workspace
```

Com Makefile:

```bash
make inventory-backup BACKUP_OUT_DIR=./backups
```

### Backup de todos os workspaces

```bash
python -m lakeventory --all-workspaces --backup-workspace
```

Com Makefile:

```bash
make inventory-all-backup BACKUP_OUT_DIR=./backups
```

## Setup Wizard (`make setup`)

No wizard existe a opcao:

- `Configure backup settings`

Ela grava os campos `backup_workspace` e `backup_output_dir` no `global_config`.

## Estrutura de saida

Exemplo:

```text
<backup_output_dir>/
└── workspace_backup_<workspace_id>_<timestamp>/
    ├── Users/admin@example.com/Notebook.dbc
    └── Shared/Project/file.txt.dbc

<backup_output_dir>/workspace_backup_<workspace_id>_<timestamp>.zip
```

## Limitacao de tamanho (10 MB)

A API tem limite por request/conteudo em alguns modos. Para reduzir falhas, o backup exporta item por item e nao tenta exportacao unica do workspace inteiro.

Se um item individual ultrapassar limite/nao puder ser exportado, ele aparece em `Backup warnings`.

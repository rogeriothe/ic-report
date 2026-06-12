# Publicação no PyPI com uv

Este projeto já está configurado para empacotamento via `hatchling` no `pyproject.toml`.

## 1) Pré-requisitos

- Conta no PyPI: <https://pypi.org/account/register/>
- (Opcional) Conta no TestPyPI: <https://test.pypi.org/account/register/>
- Token de API gerado no PyPI/TestPyPI:
  - PyPI: `Account settings` -> `API tokens`
  - TestPyPI: `Account settings` -> `API tokens`
- `uv` instalado: <https://docs.astral.sh/uv/>

## 2) Ajustes antes da primeira publicação

Revise no `pyproject.toml`:

- `project.name` (nome final do pacote)
- `project.version` (não pode repetir versão já publicada)
- `project.urls.Homepage` e `project.urls.Repository` (hoje estão com `example.com`)

## 3) Build local do pacote

Na raiz do projeto:

```bash
uv build
```

Isso gera os artefatos em `dist/` (`.tar.gz` e `.whl`).

## 4) Validar artefatos antes de publicar

```bash
uv run python -m twine check dist/*
```

## 5) Publicar no TestPyPI (recomendado)

Defina o token (sessão atual):

```bash
export UV_PUBLISH_TOKEN="pypi-..."
```

Publique no TestPyPI:

```bash
uv publish --index testpypi
```

Teste instalação:

```bash
uv pip install --index-url https://test.pypi.org/simple/ tabularium
```

## 6) Publicar no PyPI

Com token de produção:

```bash
export UV_PUBLISH_TOKEN="pypi-..."
uv publish
```

## 7) Fluxo para nova versão

1. Atualize `project.version` no `pyproject.toml`.
2. Limpe artefatos antigos:
   ```bash
   rm -rf dist/
   ```
3. Gere novamente:
   ```bash
   uv build
   uv run python -m twine check dist/*
   ```
4. Publique (`uv publish` ou `uv publish --index testpypi`).

## 8) Problemas comuns

- `File already exists`: a versão já foi publicada. Incremente `project.version`.
- `403 Forbidden`: token inválido, expirado ou sem permissão.
- Pacote instala sem fontes/arquivos esperados: revise `tool.hatch.build.targets.wheel/sdist`.

## 9) Comandos rápidos

```bash
# Build
uv build

# Verificação
uv run python -m twine check dist/*

# Publicar teste
UV_PUBLISH_TOKEN="pypi-..." uv publish --index testpypi

# Publicar produção
UV_PUBLISH_TOKEN="pypi-..." uv publish
```

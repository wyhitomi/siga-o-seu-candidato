# state-deputy-search Specification

## Purpose

Permitir que qualquer pessoa, de forma anônima, encontre deputados estaduais
(e distritais, no DF) eleitos por nome, UF ou partido.

## Requirements

### Requirement: Anonymous state deputy search

The system SHALL expose `GET /api/v1/state-deputies` without authentication,
filtering by `q` (accent and case insensitive), `uf` and `party`, paginated.

#### Scenario: Filter by state and party
- **WHEN** a visitor searches `uf=MG&party=PT`
- **THEN** only deputies from Minas Gerais and that party are returned

### Requirement: State deputy details

The system SHALL expose `GET /api/v1/state-deputies/{id}` or `404`.

### Requirement: Data loaded from TSE

Elected state and district deputies SHALL be loaded from the TSE candidate
dataset (`consulta_cand_<ano>`) for the configured election year, keeping only
candidates whose final status starts with "ELEITO".

#### Scenario: Admin triggers a load
- **WHEN** an admin calls `POST /api/v1/admin/sync/state-deputies?uf=SP`
- **THEN** the API responds `202 Accepted` and the load runs in background
- **AND** the snapshot for that UF replaces the previous one

### Requirement: Data minimisation

The load SHALL NOT store CPF, voter ID, birth date or personal e-mail of
candidates.

### Known limitation

TSE data reflects who was elected; substitutions during the term (suplentes)
are not reflected until Assembly data sources are integrated.

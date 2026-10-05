# senator-search Specification

## Purpose

Permitir que qualquer pessoa, de forma anônima, encontre senadores em
exercício por nome, UF ou partido.

## Requirements

### Requirement: Anonymous senator search

The system SHALL expose `GET /api/v1/senators` without authentication,
filtering by `q` (name, accent and case insensitive), `uf` and `party`, with
pagination (`page`, `page_size` ≤ 100).

#### Scenario: Search by name without accents
- **WHEN** a visitor searches `q=jose`
- **THEN** senators named "José ..." are returned

#### Scenario: Filter by state
- **WHEN** a visitor searches `uf=SP`
- **THEN** only senators from São Paulo are returned

### Requirement: Senator details

The system SHALL expose `GET /api/v1/senators/{id}` returning the senator or
`404` when not found.

### Requirement: Fresh data with resilience

The system SHALL refresh senators from the Senate Open Data API when the
stored data is older than `SENATORS_STALE_AFTER_HOURS`, and SHALL keep serving
stored data when the source is unavailable.

#### Scenario: Source is down but data exists
- **WHEN** the refresh fails and senators are already stored
- **THEN** the stored senators are returned, including `fetched_at`

#### Scenario: Source is down and no data exists
- **WHEN** the refresh fails and nothing is stored
- **THEN** the API responds `503 Service Unavailable`

### Requirement: Cached responses

Search responses SHALL be cached in Redis and invalidated whenever a new
snapshot of senators is stored.

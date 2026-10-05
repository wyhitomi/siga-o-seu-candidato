# admin-auth Specification

## Purpose

Permitir que apenas administradores pré-cadastrados acessem a área restrita,
usando login sem senha por link enviado ao e-mail (magic link). O público em
geral nunca faz login.

## Requirements

### Requirement: Admin login by e-mail link

The system SHALL send a single-use login link, valid for a limited time, to
the e-mail of an active administrator who requests it.

#### Scenario: Active admin requests a link
- **WHEN** an active admin submits their e-mail to `POST /api/v1/auth/magic-link`
- **THEN** the API responds `202 Accepted`
- **AND** an e-mail with a single-use link is sent, valid for `MAGIC_LINK_TTL_MINUTES`

#### Scenario: Unknown e-mail requests a link
- **WHEN** an e-mail that is not an active admin is submitted
- **THEN** the API responds `202 Accepted` with the same body
- **AND** no e-mail is sent (no account enumeration)

#### Scenario: Too many requests
- **WHEN** the same e-mail requests more than 5 links within 15 minutes
- **THEN** the API responds `429 Too Many Requests`

### Requirement: Link verification issues an access token

The system SHALL exchange a valid link token for a short-lived bearer token
(JWT) and invalidate the link token.

#### Scenario: Valid token
- **WHEN** `POST /api/v1/auth/verify` receives an unused, unexpired token
- **THEN** the API returns an access token
- **AND** the same token cannot be used again

#### Scenario: Invalid or reused token
- **WHEN** the token is unknown, expired or already used
- **THEN** the API responds `401 Unauthorized`

### Requirement: Protected admin routes

Routes under `/api/v1/admin` SHALL require a valid admin bearer token.

#### Scenario: Missing token
- **WHEN** an admin route is called without a valid token
- **THEN** the API responds `401 Unauthorized`

### Requirement: No self sign-up

Admins SHALL only be created by an operator via CLI
(`python -m app.cli create-admin <email>`).

# Defense Hackathon 2026 — Backend Design

## Overview

FastAPI backend with Clean Architecture for the Defense Hackathon 2026 platform. Supports team registration, Razorpay payments, problem statement selection, project submissions, and certificate generation.

## Architecture

### Layer Structure

```
defense-hackathon-backend/
├── app/
│   ├── core/                    # Domain Layer (no external dependencies)
│   │   ├── entities/           # Team, ProblemStatement, Submission, Admin, TeamMember
│   │   ├── value_objects/      # TeamId, TeamCode, Fee, Email, etc.
│   │   ├── enums/              # TeamCategory, PaymentStatus, SubmissionStatus
│   │   ├── commands/           # RegisterTeam, SelectProblem, Submit, etc.
│   │   ├── queries/            # GetTeam, ListProblems, etc.
│   │   └── exceptions/         # Domain errors
│   │
│   ├── inbound/                # HTTP Layer (depends on core)
│   │   ├── http/
│   │   │   ├── registration/   # POST /api/register/student, /startup
│   │   │   ├── payment/        # POST /api/payment/create-order, /verify
│   │   │   ├── team/           # GET /api/team/profile, POST /select-problem
│   │   │   ├── submission/     # POST /api/submission/submit
│   │   │   └── admin/          # GET /api/admin/dashboard, exports
│   │   └── middleware/         # Auth, Deadline checks
│   │
│   └── outbound/               # Infrastructure (depends on core)
│       ├── adapters/           # SQLAlchemy, Razorpay, S3, Email
│       └── persistence/        # Mappings, migrations
│
├── alembic/
├── tests/
└── docs/
```

### Dependency Rule
- **Core** knows nothing of FastAPI, SQLAlchemy, or external APIs
- **Inbound** depends on Core
- **Outbound** depends on Core
- Dependencies flow inward only

## Core Domain Entities

### Team (Aggregate Root)

```python
class Team(Entity[TeamId]):
    team_code: TeamCode               # "STU-2026-0001" (display ID)
    category: TeamCategory            # STUDENT | STARTUP
    team_name: str
    team_size: int                    # 2-5 (student) or 2-3 (startup)
    lead_name: str
    lead_email: Email                 # Used for login
    lead_mobile: str
    password_hash: PasswordHash
    payment_status: PaymentStatus     # PENDING | SUCCESS | FAILED
    selected_problem_id: Optional[ProblemId]  # NULL until selected
    submission: Optional[Submission]        # NULL until submitted
    members: List[TeamMember]         # 1 to team_size-1 additional members
    created_at: UtcDatetime
    updated_at: UtcDatetime
```

### TeamMember (Value Object)

```python
class TeamMember(ValueObject):
    name: str
    email: Email
    mobile: str
```

### ProblemStatement (Entity)

```python
class ProblemStatement(Entity[ProblemId]):
    problem_code: str       # "PS-001"
    title: str
    description: str
    track: str              # Domain/category
    is_active: bool
    created_at: UtcDatetime
```

### Submission (Value Object - owned by Team)

```python
class Submission(ValueObject):
    problem_id: ProblemId
    abstract: str
    description: str
    project_file_url: Optional[str]    # S3 URL
    presentation_url: Optional[str]    # S3 URL
    deployment_link: Optional[str]
    submitted_at: UtcDatetime
    certificate_approved: bool = False
    certificate_url: Optional[str] = None
```

### Admin (Entity)

```python
class Admin(Entity[AdminId]):
    email: Email
    password_hash: PasswordHash
    name: str
    created_at: UtcDatetime
```

## Commands

### Registration Commands

| Command | Business Logic |
|---------|----------------|
| `RegisterStudentTeam` | Validate size (2-5), calculate fee (₹500 × size), generate team_code (STU-2026-XXXX), hash password, create team with PENDING status |
| `RegisterStartupTeam` | Validate size (2-3), calculate fee (₹1000 × size), generate team_code (STR-2026-XXXX), hash password, create team with PENDING status |

### Payment Commands

| Command | Business Logic |
|---------|----------------|
| `CreatePaymentOrder` | Call Razorpay API, return order_id to frontend |
| `VerifyPayment` | Verify HMAC signature with Razorpay secret, update team.payment_status=SUCCESS, send confirmation email |

### Team Commands

| Command | Business Logic |
|---------|----------------|
| `SelectProblemStatement` | Check deadline, SELECT FOR UPDATE on team, ensure not already selected, lock problem selection permanently |
| `CreateSubmission` | Check deadline, check problem selected, create Submission value object, attach to team |
| `UploadSubmissionFiles` | Upload to S3 (10MB limit), validate MIME type, update submission URLs |

### Admin Commands

| Command | Business Logic |
|---------|----------------|
| `ApproveCertificate` | Admin only, set submission.certificate_approved=true |
| `CreateProblemStatement` | Admin only, create new problem |
| `UpdateEventDeadline` | Admin only, update registration/submission deadlines |

## Queries

| Query | Purpose |
|-------|---------|
| `GetTeamProfile` | Team details + members + selected problem |
| `ListProblemStatements` | Available problems with counts (total/available) |
| `GetTeamSubmissionStatus` | Submission state |
| `AdminDashboardStats` | Total registrations, revenue, submissions |
| `ExportTeamsCsv` | All teams with filters (category, payment, submission status) |
| `ExportPaymentsCsv` | Payment records with invoice links |
| `ExportSubmissionsCsv` | Submissions with problem mapping |

## Error Handling

### Domain Exceptions

```python
class DomainError(Exception):
    """Base for all domain errors"""
    pass

class RegistrationClosedError(DomainError):
    """Registration deadline passed"""
    pass

class SubmissionClosedError(DomainError):
    """Submission deadline passed"""
    pass

class InvalidTeamSizeError(DomainError):
    """Student: 2-5, Startup: 2-3"""
    pass

class ProblemAlreadySelectedError(DomainError):
    """Team tried to select second problem"""
    pass

class PaymentVerificationError(DomainError):
    """Razorpay signature mismatch"""
    pass

class SubmissionNotAllowedError(DomainError):
    """No problem selected or deadline passed"""
    pass

class CertificateNotApprovedError(DomainError):
    """Certificate not yet approved by admin"""
    pass

class FileTooLargeError(DomainError):
    """File exceeds 10MB limit"""
    pass

class InvalidFileTypeError(DomainError):
    """Invalid MIME type"""
    pass
```

### HTTP Error Mapping

| Domain Error | HTTP Status |
|--------------|-------------|
| RegistrationClosedError | 403 Forbidden |
| SubmissionClosedError | 403 Forbidden |
| InvalidTeamSizeError | 400 Bad Request |
| ProblemAlreadySelectedError | 409 Conflict |
| PaymentVerificationError | 400 Bad Request |
| FileTooLargeError | 413 Payload Too Large |
| InvalidFileTypeError | 415 Unsupported Media Type |

## Validation Rules

### Password
- Minimum 6 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one special character (!@#$%^&* etc.)

### Team Size
- Student: 2-5 members
- Startup: 2-3 members

### File Upload
- Maximum: 10MB per file
- Validate MIME type server-side
- Store only in S3, save URL in database

### Deadlines
- Middleware checks `event_config` table
- Returns 403 if endpoint called after deadline

## Testing Strategy

```
tests/
├── unit/                       # Core domain logic (no DB, no HTTP)
│   ├── entities/              # Team creation, validation, business rules
│   └── value_objects/        # TeamCode generation, Email validation
│
├── integration/                # Database + adapters
│   ├── persistence/            # SQLAlchemy mappings, queries
│   └── adapters/               # Razorpay mock, S3 mock, Email mock
│
├── e2e/                        # Full HTTP API tests
│   ├── registration/           # POST /api/register/*
│   ├── payment/                # Payment flow with mocked Razorpay
│   ├── team/                   # Problem selection, submission
│   └── admin/                  # Admin endpoints
│
└── fixtures/                   # Test data factories
```

### Test Examples

**Unit Test:**
```python
def test_student_team_size_validation():
    with pytest.raises(InvalidTeamSizeError):
        Team.create(
            category=TeamCategory.STUDENT,
            team_size=1,  # Too small
            ...
        )
```

**Integration Test:**
```python
async def test_payment_verification_updates_status(db_session):
    team = await create_test_team(db_session, payment_status=PENDING)
    await VerifyPaymentHandler(db_session).execute(...)
    assert team.payment_status == PaymentStatus.SUCCESS
```

**E2E Test:**
```python
async def test_registration_flow(client):
    response = await client.post("/api/register/student", json={...})
    assert response.status_code == 201
    assert response.json()["team_code"].startswith("STU-2026-")
```

## Fee Calculation

```python
STUDENT_FEE_PER_PERSON = 500    # INR
STARTUP_FEE_PER_PERSON = 1000   # INR

def calculate_fee(category: TeamCategory, team_size: int) -> Decimal:
    rate = STUDENT_FEE_PER_PERSON if category == TeamCategory.STUDENT else STARTUP_FEE_PER_PERSON
    return Decimal(rate * team_size)
```

## Team ID Generation

```python
def generate_team_code(category: TeamCategory, year: int, sequence: int) -> TeamCode:
    prefix = "STU" if category == TeamCategory.STUDENT else "STR"
    return TeamCode(f"{prefix}-{year}-{sequence:04d}")
# Examples: STU-2026-0001, STR-2026-0001
```

Use database sequence or atomic counter to prevent race conditions.

## Certificate Generation

1. Admin calls `ApproveCertificate` endpoint after event completion
2. System generates PDF using WeasyPrint or ReportLab
3. Template includes team name, problem statement, submission date
4. Upload PDF to S3
5. Store URL in `submission.certificate_url`
6. Certificate only available for download after approval

## Security Checklist

- [ ] Hash passwords with bcrypt (12+ salt rounds)
- [ ] JWT tokens with 2-hour expiry + refresh tokens
- [ ] Rate limit auth endpoints (slowapi)
- [ ] HTTPS only in production
- [ ] Validate ALL inputs with Pydantic
- [ ] Sanitize file uploads (MIME check, 10MB limit)
- [ ] Verify Razorpay webhook signatures
- [ ] CORS whitelist only frontend domain
- [ ] Security headers via middleware
- [ ] SQL injection prevention via SQLAlchemy
- [ ] Store secrets in `.env`, never commit
- [ ] Admin endpoints require separate role check
- [ ] Only one admin account (no role management)

## API Endpoints Summary

### Public
- `GET /api/event/details`
- `GET /api/problem-statements`
- `GET /api/event/status`

### Registration & Payment
- `POST /api/register/student`
- `POST /api/register/startup`
- `POST /api/payment/create-order`
- `POST /api/payment/verify`
- `POST /api/payment/webhook`

### Authentication
- `POST /api/auth/login`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `POST /api/auth/logout`

### Team Dashboard (Authenticated)
- `GET /api/team/profile`
- `GET /api/team/problem-statements`
- `POST /api/team/select-problem`
- `GET /api/team/selected-problem`

### Submission (Authenticated)
- `POST /api/submission/upload`
- `POST /api/submission/submit`
- `GET /api/submission/status`
- `GET /api/submission/certificate`

### Admin (Admin JWT)
- `GET /api/admin/dashboard`
- `GET /api/admin/teams`
- `GET /api/admin/teams/:id`
- `GET /api/admin/export/teams.csv`
- `GET /api/admin/export/payments.csv`
- `GET /api/admin/export/submissions.csv`
- `POST /api/admin/problem-statements`
- `PUT /api/admin/problem-statements/:id`
- `DELETE /api/admin/problem-statements/:id`
- `PUT /api/admin/config/deadlines`
- `POST /api/admin/certificates/approve/:teamId`

## Design Decisions

1. **Team as Aggregate Root:** Team replaces User entity from the clean example. Authentication happens via lead email.

2. **Dynamic Fee Calculation:** Fee is calculated from category × team_size, not stored. This prevents data inconsistency.

3. **UUID Primary Key:** Internal UUID for database efficiency, formatted `team_code` (STU-2026-XXXX) for display and user reference.

4. **Submission as Value Object:** Owned by Team entity, not a separate aggregate. One submission per team.

5. **Admin Separate Entity:** Completely separate from Team, own table, own authentication.

6. **Problem Selection Lock:** Permanent, irreversible lock using SELECT FOR UPDATE transaction.

7. **Certificate Approval:** Admin must approve before certificate is generated and available.

8. **Deadline Middleware:** Checks `event_config` table before allowing registration/submission.

---

**Approved:** 2026-04-21

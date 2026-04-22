# Defense Hackathon 2026 — Complete Backend Development Plan

I've reviewed your MVP document thoroughly. Here's a comprehensive backend plan covering architecture, data models, API endpoints, and implementation strategy.

---

## 1. Recommended Tech Stack

**Backend Framework:** Python + FastAPI
**Database:** PostgreSQL
**ORM:** SQLAlchemy (with Alembic for migrations)
**Authentication:** JWT (JSON Web Tokens) + passlib[bcrypt] for password hashing
**Payment Gateway:** Razorpay (best for INR transactions in India)
**Email Service:** FastAPI-Mail + SendGrid/AWS SES
**File Storage:** AWS S3 or Cloudinary (for project submissions)
**PDF Generation:** WeasyPrint or ReportLab (for certificates & invoices)
**Hosting:** Railway / Render / AWS EC2 (backend), AWS RDS (database)
**Validation:** Pydantic (built into FastAPI)
**Environment:** python-dotenv

**Why this stack:** Razorpay is India-native with excellent INR support, PostgreSQL handles your relational team→problem→submission mappings cleanly, and FastAPI with Pydantic provides automatic validation, OpenAPI docs, and high performance out of the box.

---

## 2. High-Level Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  (React/Next)│◀────│   REST API   │◀────│  Database   │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
         ┌────────┐   ┌──────────┐   ┌─────────┐
         │Razorpay│   │ AWS S3   │   │SendGrid │
         │Payment │   │File Store│   │  Email  │
         └────────┘   └──────────┘   └─────────┘
```

---

## 3. Database Schema (Data Models)

### 3.1 `teams` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | Internal ID |
| `team_id` | VARCHAR(20) UNIQUE | Auto-generated, e.g., `STU-2026-0001` or `STR-2026-0001` |
| `team_name` | VARCHAR(100) | Required |
| `category` | ENUM('student','startup') | Required |
| `team_size` | INT | Student: 2-5, Startup: 2-3 |
| `lead_name` | VARCHAR(100) | Team leader |
| `lead_email` | VARCHAR(150) UNIQUE | Used for login |
| `lead_mobile` | VARCHAR(15) | |
| `password_hash` | VARCHAR(255) | bcrypt hash |
| `payment_status` | ENUM('pending','success','failed') | Default: pending |
| `payment_amount` | DECIMAL(10,2) | Calculated fee |
| `selected_problem_id` | UUID (FK) | Nullable, links to problem_statements |
| `submission_status` | ENUM('pending','submitted') | Default: pending |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

### 3.2 `team_members` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `team_id` | UUID (FK) | References teams.id |
| `name` | VARCHAR(100) | |
| `email` | VARCHAR(150) | |
| `mobile` | VARCHAR(15) | |

### 3.3 `problem_statements` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `problem_code` | VARCHAR(20) UNIQUE | e.g., `PS-001` |
| `title` | VARCHAR(200) | |
| `description` | TEXT | |
| `track` | VARCHAR(100) | Domain/category |
| `is_active` | BOOLEAN | Default: true |
| `created_at` | TIMESTAMP | |

### 3.4 `submissions` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `team_id` | UUID (FK) UNIQUE | One submission per team |
| `problem_statement_id` | UUID (FK) | |
| `abstract` | TEXT | |
| `description` | TEXT | |
| `project_file_url` | VARCHAR(500) | S3 URL |
| `presentation_url` | VARCHAR(500) | S3 URL |
| `deployment_link` | VARCHAR(500) | |
| `certificate_approved` | BOOLEAN | Default: false — set to true by admin after event completion |
| `certificate_url` | VARCHAR(500) | S3 URL — populated only after admin approval |
| `submitted_at` | TIMESTAMP | |

### 3.5 `payments` table

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `team_id` | UUID (FK) | |
| `razorpay_order_id` | VARCHAR(100) | |
| `razorpay_payment_id` | VARCHAR(100) | |
| `razorpay_signature` | VARCHAR(255) | For verification |
| `amount` | DECIMAL(10,2) | |
| `currency` | VARCHAR(10) | INR |
| `status` | ENUM('created','paid','failed') | |
| `invoice_url` | VARCHAR(500) | PDF invoice |
| `created_at` | TIMESTAMP | |

### 3.6 `admins` table (single admin account only)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `email` | VARCHAR(150) UNIQUE | |
| `password_hash` | VARCHAR(255) | |
| `name` | VARCHAR(100) | |
| `created_at` | TIMESTAMP | |

### 3.7 `event_config` table (for admin-controlled deadlines)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | |
| `key` | VARCHAR(50) UNIQUE | e.g., `registration_deadline`, `submission_deadline` |
| `value` | VARCHAR(255) | ISO datetime string |

---

## 4. Complete API Endpoints

### 4.1 Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/event/details` | Returns event date, time, venue, voting info |
| GET | `/api/problem-statements` | Public list of problem statements |
| GET | `/api/event/status` | Returns whether registration/submission is open |

### 4.2 Registration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register/student` | Create student team (returns team_id, triggers payment) |
| POST | `/api/register/startup` | Create startup team |
| POST | `/api/payment/create-order` | Creates Razorpay order |
| POST | `/api/payment/verify` | Verifies signature, confirms registration, sends invoice email |
| POST | `/api/payment/webhook` | Razorpay webhook handler (backup verification) |

### 4.3 Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/student` | Team lead login (email + password) |
| POST | `/api/auth/login/startup` | Startup lead login |
| POST | `/api/auth/admin/login` | Admin login |
| POST | `/api/auth/forgot-password` | Send reset link |
| POST | `/api/auth/reset-password` | Reset with token |
| POST | `/api/auth/logout` | Invalidate session |

### 4.4 Team Dashboard (Authenticated)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/team/profile` | Get logged-in team details |
| GET | `/api/team/problem-statements` | List problems with `total` and `available` count |
| POST | `/api/team/select-problem` | Lock in 1 problem (1-to-1, irreversible or admin-only reset) |
| GET | `/api/team/selected-problem` | Get the team's chosen PS |

### 4.5 Submission Endpoints (Authenticated)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/submission/upload` | Multipart upload (project file + presentation) → S3 |
| POST | `/api/submission/submit` | Final submit with abstract, description, deployment link |
| GET | `/api/submission/status` | Check submission state |
| GET | `/api/submission/certificate` | Generates and returns PDF certificate |

### 4.6 Admin Endpoints (Admin JWT required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Stats: total registrations, revenue, submissions |
| GET | `/api/admin/teams` | Paginated list with filters (category, payment, submission status) |
| GET | `/api/admin/teams/:id` | Full team details + members + submission |
| GET | `/api/admin/export/teams.csv` | CSV export — all teams with members, mobile, email, topic, submission |
| GET | `/api/admin/export/payments.csv` | CSV export — payment records with invoice links |
| GET | `/api/admin/export/submissions.csv` | CSV export — submissions with PS mapping |
| POST | `/api/admin/problem-statements` | Create new PS |
| PUT | `/api/admin/problem-statements/:id` | Edit PS |
| DELETE | `/api/admin/problem-statements/:id` | Soft-delete PS |
| PUT | `/api/admin/config/deadlines` | Update registration/submission deadlines |
| GET | `/api/admin/payments/:teamId/invoice` | Download invoice copy |
| POST | `/api/admin/certificates/approve/:teamId` | Approve certificate generation for a team after event completion |

---

## 5. Critical Business Logic

### 5.1 Team ID Generation

```
Format: {CATEGORY_PREFIX}-{YEAR}-{SEQUENCE}
Student: STU-2026-0001, STU-2026-0002...
Startup: STR-2026-0001, STR-2026-0002...
```

Use a database sequence or atomic counter to prevent race conditions.

### 5.2 Fee Calculation

```python
STUDENT_FEE_PER_PERSON = 500
STARTUP_FEE_PER_PERSON = 1000
total_fee = team_size * (STUDENT_FEE_PER_PERSON if category == "student" else STARTUP_FEE_PER_PERSON)
```

### 5.3 Registration Confirmation Flow

1. User submits registration form → team created with `payment_status: 'pending'`
2. Backend creates Razorpay order, returns `order_id` to frontend
3. Frontend opens Razorpay checkout → user pays
4. Frontend sends `payment_id`, `order_id`, `signature` to `/api/payment/verify`
5. Backend verifies HMAC signature using Razorpay secret
6. On success: update `payment_status: 'success'`, generate invoice PDF, email confirmation
7. Webhook fires as fallback (idempotent — check if already processed)

### 5.4 Deadline Enforcement (Middleware)

Create a middleware that checks `event_config` before allowing registration or submission endpoints. Returns 403 if past deadline.

### 5.5 Problem Statement Locking

Use a database transaction: SELECT FOR UPDATE on the team row, check if `selected_problem_id` is null, then update. Prevents double-selection from concurrent requests.

### 5.6 Certificate Generation

Use WeasyPrint or ReportLab to render an HTML/PDF template with team data → PDF. Cache generated certificates in S3 to avoid regeneration on every download. Certificate is issued only after admin approval / event completion via a dedicated admin approval endpoint.

### 5.7 Password Validation Rules

```python
import re

def validate_password(password: str) -> bool:
    """
    Rules:
    - Minimum 6 characters total (more than 6 means >= 7 recommended, enforced as > 6)
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one special character (!@#$%^&*etc.)
    """
    if len(password) <= 6:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[^a-zA-Z0-9]', password):
        return False
    return True
```

Password confirmation flow:
1. User enters password + confirm password on registration form
2. Frontend checks both fields match before submitting
3. Backend re-validates password rules on the server side
4. On pass: hash with bcrypt, save to DB, send confirmation email to registered email ID
5. Email subject: "Your Defense Hackathon 2026 Password Has Been Set Successfully"

---

## 6. Folder Structure

```
defense-hackathon-backend/
├── app/
│   ├── config/
│   │   ├── database.py
│   │   ├── razorpay.py
│   │   └── s3.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── registration.py
│   │   ├── payment.py
│   │   ├── team.py
│   │   ├── submission.py
│   │   └── admin.py
│   ├── middleware/
│   │   ├── auth.py
│   │   ├── deadline.py
│   │   └── error_handler.py
│   ├── models/
│   │   └── models.py          (SQLAlchemy ORM models)
│   ├── schemas/
│   │   └── schemas.py         (Pydantic request/response schemas)
│   ├── services/
│   │   ├── email_service.py
│   │   ├── pdf_service.py
│   │   ├── csv_service.py
│   │   └── payment_service.py
│   ├── utils/
│   │   ├── team_id_generator.py
│   │   └── validators.py
│   ├── templates/
│   │   ├── invoice.html
│   │   ├── certificate.html
│   │   └── email_templates/
│   └── main.py
├── alembic/
│   └── versions/              (migration files)
├── alembic.ini
├── .env
├── requirements.txt
└── run.py
```

---

## 7. Security Checklist

- Hash passwords with passlib[bcrypt] (10+ salt rounds)
- JWT tokens with short expiry (1-2 hours) + refresh tokens
- Rate limit auth endpoints (slowapi for FastAPI)
- HTTPS only in production
- Validate ALL inputs with Pydantic (built into FastAPI)
- Sanitize file uploads (check MIME type, size limits — max 10MB per file)
- Verify Razorpay webhook signatures
- CORS whitelist only your frontend domain (fastapi.middleware.cors)
- Security headers via custom FastAPI middleware
- SQL injection prevention via parameterized queries (SQLAlchemy handles this)
- Store secrets in `.env`, never commit
- Admin endpoints require separate role check, not just JWT presence
- Only one admin account — no role management needed

---

## 8. Development Phases (Recommended Order)

**Phase 1 — Foundation (Days 1-2)**
Set up project, database, SQLAlchemy models, Alembic migrations, basic FastAPI server, environment config.

**Phase 2 — Registration + Payment (Days 3-5)**
Registration endpoints, Razorpay integration, payment verification, invoice generation, email service.

**Phase 3 — Authentication (Day 6)**
JWT auth for students, startups, and single admin account. Login/logout/password reset.

**Phase 4 — Dashboard + Problem Selection (Days 7-8)**
Problem statement APIs, selection logic with 1-to-1 permanent lock enforcement.

**Phase 5 — Submission + Certificates (Days 9-10)**
File upload to S3 (max 10MB), submission endpoint, PDF certificate generation (issued only after admin approval).

**Phase 6 — Admin Portal (Days 11-12)**
Dashboard stats, CSV exports, deadline controls, PS management, certificate approval trigger.

**Phase 7 — Testing + Deployment (Days 13-14)**
Unit tests with pytest, API testing via FastAPI's built-in /docs (Swagger UI), deploy to Railway/Render, set up production database.

---

## 9. Environment Variables (`.env`)

```
APP_ENV=production
PORT=8000
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
JWT_SECRET=your-secret-here
JWT_EXPIRY_HOURS=2
RAZORPAY_KEY_ID=rzp_xxx
RAZORPAY_KEY_SECRET=xxx
RAZORPAY_WEBHOOK_SECRET=xxx
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_S3_BUCKET=defense-hackathon-2026
AWS_REGION=ap-south-1
SENDGRID_API_KEY=xxx
EMAIL_FROM=noreply@defensehackathon2026.com
FRONTEND_URL=https://defensehackathon2026.com
ADMIN_EMAIL=admin@defensehackathon2026.com
```

---

## 10. Answered Design Decisions

1. **Login credentials** — Password is set by the team lead during or after registration. Requirements: minimum 6 characters, at least one uppercase letter, at least one lowercase letter, and at least one special character. After entering and confirming the password, it is saved and a confirmation email is sent to the registered email ID notifying that the password has been successfully set.

2. **Problem statement re-selection** — Once a team selects a problem statement, it is **permanently locked**. No changes are allowed under any circumstances, including by the admin.

3. **Voting Information** — Removed from scope. No voting feature exists in this MVP. The home page will not include any voting-related information.

4. **Certificate timing** — Certificates are **not generated immediately on submission**. They are issued only after explicit admin approval upon event completion. A dedicated admin endpoint (`POST /api/admin/certificates/approve/:teamId`) triggers certificate generation and delivery.

5. **File size limits** — Maximum upload size is **10MB per file** for both project files and presentation files. File type validation (MIME check) is also enforced server-side.

6. **Multiple admins** — **Only one admin account** exists. No role management or multi-admin support is needed.

---

When you're ready, tell me which phase to start with and I'll generate the actual code — I'd suggest beginning with **Phase 1 (project setup + SQLAlchemy models + Alembic)** since everything else depends on it. I can scaffold the entire repo with working code for each phase, one at a time.

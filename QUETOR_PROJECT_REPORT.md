# Quetor: A Web Service for Students Evaluation
## Comprehensive Technical Project Report

**Project Title**: Quetor — An AI-Powered Educational Platform for Lecture-Based Assessment

**Undergraduate Project (UGP)**
**Institute**: Indian Institute of Technology Kanpur (IITK)
**Supervisor**: Professor Shubham Sahay
**Developed by**:
- Snehasis Satapathy (Roll No. 221070)
- Gautam Arora (Roll No. 220405)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [System Architecture](#3-system-architecture)
4. [Directory Structure](#4-directory-structure)
5. [Database Design & Models](#5-database-design--models)
6. [User Roles & Access Control](#6-user-roles--access-control)
7. [Core Features](#7-core-features)
8. [LLM Integration & MCQ Generation](#8-llm-integration--mcq-generation)
9. [URL Routing](#9-url-routing)
10. [Views & Business Logic](#10-views--business-logic)
11. [Frontend & Templates](#11-frontend--templates)
12. [Configuration](#12-configuration)
13. [Data Flow Diagrams](#13-data-flow-diagrams)
14. [Security Considerations](#14-security-considerations)
15. [Limitations & Future Scope](#15-limitations--future-scope)

---

## 1. Project Overview

**Quetor** is a Django-based, full-stack web application designed to streamline the teaching and evaluation workflow at IITK. The platform bridges the gap between content delivery and student assessment by combining traditional course material management with AI-powered quiz generation.

### Core Problem Statement

Instructors routinely upload lecture slides to course portals, but creating question papers from those slides is manual, time-consuming, and inconsistent in difficulty distribution. At the same time, students lack a structured channel to raise doubts that are visible to teaching staff in a tracked, resolvable manner.

### What Quetor Does

| Capability | Description |
|---|---|
| Material Upload | Professors upload PDFs, PPTX slides, notes; content is extracted and cached automatically |
| AI-Powered MCQ Generation | An on-premises LLM (via OLLAMA) generates multiple-choice questions directly from uploaded slides |
| Online Quiz System | Students take timed, shuffled quizzes; answers are auto-graded with instant feedback |
| Doubt Resolution | Students post queries; TAs and professors respond in a threaded message system |
| Role-Based Access | Separate dashboards and permissions for Students, Professors, and Teaching Assistants |

---

## 2. Technology Stack

| Layer | Technology | Version / Notes |
|---|---|---|
| Web Framework | Django | ==4.2.30 |
| Language | Python | 3.8+ |
| Database | SQLite | Development; PostgreSQL recommended for production |
| LLM Backend | OLLAMA | Local; default model: `gemma3` |
| PDF Extraction | pypdf | >=4.0 |
| PPTX Extraction | python-pptx | >=0.6.23 |
| HTTP Client | requests | >=2.31 (for OLLAMA API calls) |
| Environment Config | python-dotenv | >=1.0 |
| Frontend | Django Templates + inline CSS | No external JS frameworks |

### `requirements.txt`
```
Django==4.2.30
requests>=2.31
pypdf>=4.0
python-pptx>=0.6.23
python-dotenv>=1.0
```

---

## 3. System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Client (Browser)                              │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │ HTTP
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Django Development Server                       │
│                      python manage.py runserver                        │
└──────────────────┬───────────────────────────────┬─────────────────────┘
                   │ ORM Queries                   │ HTTP POST (requests)
                   ▼                               ▼
    ┌──────────────────────┐        ┌──────────────────────────┐
    │       SQLite         │        │  OLLAMA (Local LLM)      │
    │      Database        │        │  http://127.0.0.1:11434  │
    └──────────────────────┘        │  Model: gemma3 (default) │
                                    └──────────────────────────┘
```

### Django Apps Overview

```
Django Application
│
├── users        — Custom User model, registration, role management
├── courses      — Semester, Course, enrollment (Professor / TA / Student)
├── content      — CourseMaterial upload, text extraction & caching
├── assignments  — Assignment creation, MCQ generation via OLLAMA, quiz taking
└── queries      — Student doubt creation, threaded replies, status tracking
```

---

## 4. Directory Structure

```
A-Web-Service-for-Students-Evaluation/
│
├── config/                          # Django project configuration
│   ├── __init__.py
│   ├── settings.py                  # All Django settings (DB, auth, email, timezone)
│   ├── urls.py                      # Root URL routing
│   ├── wsgi.py                      # WSGI entry point
│   └── asgi.py                      # ASGI entry point
│
├── users/                           # User authentication & profiles
│   ├── models.py                    # Custom User model (extends AbstractUser)
│   ├── views.py                     # Registration view, account page, contact
│   ├── forms.py                     # CustomUserCreationForm
│   ├── admin.py                     # Admin registration for User
│   ├── urls.py                      # /accounts/register/ route
│   └── migrations/
│       ├── 0001_initial.py          # Create User model
│       └── 0002_add_department.py   # Add department field
│
├── courses/                         # Course & semester management
│   ├── models.py                    # Semester, Course, CourseProfessor, CourseTA, CourseStudent
│   ├── views.py                     # Dashboard, role routing, material upload
│   ├── admin.py                     # Admin config for all course models
│   ├── urls.py                      # /courses/ routes
│   └── migrations/
│       ├── 0001_initial.py          # Create Semester, Course
│       ├── 0002_initial.py          # Create enrollment models
│       ├── 0003_alter_semester_sem.py
│       ├── 0004_alter_course_id_...
│       └── 0005_alter_course_id_...
│
├── content/                         # Course material management
│   ├── models.py                    # CourseMaterial, CourseMaterialText
│   ├── views.py                     # delete_material, toggle_visibility
│   ├── signals.py                   # post_save signal → triggers text extraction
│   ├── extract.py                   # Text extraction dispatcher (pdf/pptx/txt)
│   ├── admin.py                     # CourseMaterial admin
│   ├── apps.py                      # Registers signals on app ready
│   └── migrations/
│       ├── 0001_initial.py          # Create CourseMaterial
│       ├── 0002_initial.py          # Intermediate migration
│       └── 0003_coursematerialtext.py  # Add CourseMaterialText cache model
│
├── assignments/                     # Quiz & assessment engine
│   ├── models.py                    # Assignment, AssignmentQuestion, StudentAnswer, StudentAttempt
│   ├── views.py                     # Quiz lifecycle views (create, generate, take, grade)
│   ├── services.py                  # MCQ generation orchestration logic
│   ├── llm_client.py                # OLLAMA HTTP API integration
│   ├── material_text.py             # File format text extraction (pdf/pptx/txt)
│   ├── pdf_text.py                  # Text chunking utility (4500 chars/chunk, max 20 chunks)
│   ├── admin.py                     # Assignment admin
│   ├── urls.py                      # /assignments/ routes
│   └── migrations/
│       ├── 0001_initial.py          # Create Assignment
│       ├── 0002_assignmentquestion.py
│       ├── 0003_studentanswer.py
│       └── 0004_quiz_timing_and_marks.py  # Add StudentAttempt, duration, score tracking
│
├── queries/                         # Student doubt resolution system
│   ├── models.py                    # Query, QueryMessage
│   ├── views.py                     # Query create, detail, TA dashboard, status update
│   ├── admin.py                     # Query & QueryMessage admin with filters
│   ├── urls.py                      # /queries/ routes
│   └── migrations/
│       ├── 0001_initial.py          # Create Query, QueryMessage
│       └── 0002_alter_query_id_...  # ID field update
│
├── templates/                       # All Django HTML templates
│   ├── base.html                    # Minimal base (used by auth pages)
│   ├── registration/
│   │   ├── login.html               # IITK-branded login page
│   │   ├── register.html            # Self-registration with role selector
│   │   └── password_*.html          # Django built-in password reset templates
│   ├── courses/
│   │   ├── base.html                # Main app chrome (header + sidebar)
│   │   ├── my_courses.html          # Landing dashboard grouped by semester
│   │   ├── professor_home.html      # Material upload form + table + stats
│   │   ├── student_home.html        # Quick action cards + material list
│   │   ├── ta_home.html             # TA material view
│   │   ├── my_account.html          # User account info page
│   │   └── contact_us.html          # Contact page
│   ├── assignments/
│   │   ├── professor_assignments.html     # Active/past assignment list (professor)
│   │   ├── create_assignment.html         # Create/edit quiz form
│   │   ├── generate_mcqs.html             # MCQ generation form (material picker, topic, count)
│   │   ├── assignment_questions.html      # Review generated MCQs
│   │   ├── assignment_results.html        # Student grades & analytics table
│   │   ├── student_assignments.html       # Student quiz list
│   │   └── student_take_assignment.html   # Live quiz interface with countdown timer
│   └── queries/
│       ├── student_queries.html           # Student's own query list (card grid)
│       ├── create_query.html              # Create new query with attachment
│       ├── query_detail.html              # Threaded chat-style message view
│       └── ta_queries.html                # All-course queries for TA/professor (filterable)
│
├── static/
│   ├── css/
│   │   ├── auth.css                 # Login/registration page styling
│   │   └── courses.css              # Main app styling
│   └── img/
│       └── iitk_logo.png            # Institute logo
│
├── media/                           # User-uploaded files (runtime, gitignored)
│   ├── course_materials/            # Lecture slides and PDFs uploaded by professors
│   └── query_attachments/           # Files attached to student query messages
│
├── manage.py                        # Django CLI entry point
├── requirements.txt                 # Python package dependencies
└── .env.example                     # Environment variable template
```

---

## 5. Database Design & Models

### 5.1 Entity-Relationship Overview

```
User ──< CourseProfessor >── Course ──< Semester
User ──< CourseTA       >── Course
User ──< CourseStudent  >── Course
Course ──< CourseMaterial ──── CourseMaterialText
Course ──< Assignment ──< AssignmentQuestion
Assignment ──< StudentAttempt >── User
AssignmentQuestion ──< StudentAnswer >── User
Course ──< Query >── User (student)
Query ──< QueryMessage >── User (sender)
```

### 5.2 Model Definitions

#### `users.User` — Custom AbstractUser
| Field | Type | Notes |
|---|---|---|
| username | CharField | Inherited from AbstractUser |
| email | EmailField | Inherited |
| first_name | CharField | Inherited |
| last_name | CharField | Inherited |
| role | CharField(20) | Choices: `student`, `professor`, `ta`, `admin` |
| department | CharField(100) | Blank/null allowed |

#### `courses.Semester`
| Field | Type | Notes |
|---|---|---|
| year_start | IntegerField | e.g., 2024 |
| year_end | IntegerField | e.g., 2025 |
| sem | IntegerField | 1 = Odd, 2 = Even, 3 = Summer |
| is_active | BooleanField | Marks current semester |
| **Unique Together** | (year_start, year_end, sem) | Prevents duplicate semesters |

#### `courses.Course`
| Field | Type | Notes |
|---|---|---|
| code | CharField(20) | Unique course code (e.g., CS340) |
| name | CharField(200) | Full course name |
| semester | ForeignKey → Semester | Cascades on delete |

#### `courses.CourseProfessor`
| Field | Type | Notes |
|---|---|---|
| course | OneToOneField → Course | One professor per course enforced |
| professor | ForeignKey → User | Role: professor |

#### `courses.CourseTA`
| Field | Type | Notes |
|---|---|---|
| course | ForeignKey → Course | Multiple TAs per course |
| ta | ForeignKey → User | Role: ta |
| **Unique Together** | (course, ta) | No duplicate TA assignments |

#### `courses.CourseStudent`
| Field | Type | Notes |
|---|---|---|
| course | ForeignKey → Course | |
| student | ForeignKey → User | Role: student |
| **Unique Together** | (course, student) | No duplicate enrollments |

#### `content.CourseMaterial`
| Field | Type | Notes |
|---|---|---|
| course | ForeignKey → Course | |
| title | CharField(200) | |
| content_type | CharField(20) | Choices: `notes`, `slides`, `ppt`, `pyq`, `other` |
| file | FileField | Stored under `/media/course_materials/` |
| is_published | BooleanField | Controls student visibility |
| uploaded_at | DateTimeField | Auto-set on creation |

#### `content.CourseMaterialText`
| Field | Type | Notes |
|---|---|---|
| material | OneToOneField → CourseMaterial | |
| file_name | CharField | Original filename |
| kind | CharField | `pdf`, `pptx`, `text` |
| text | TextField | Extracted plain text (cached) |
| status | CharField | `ok`, `unsupported`, `error` |
| error_message | TextField | Blank unless error |
| extracted_at | DateTimeField | When extraction ran |
| extractor_version | CharField | Version tag for cache invalidation |

#### `assignments.Assignment`
| Field | Type | Notes |
|---|---|---|
| course | ForeignKey → Course | |
| created_by | ForeignKey → User | Professor who created it |
| title | CharField(200) | |
| description | TextField | Blank allowed |
| due_date | DateTimeField | Deadline for students |
| duration_minutes | PositiveIntegerField | Default 20; max 300 |
| is_published | BooleanField | Controls student visibility |
| created_at | DateTimeField | Auto-set |

#### `assignments.AssignmentQuestion`
| Field | Type | Notes |
|---|---|---|
| assignment | ForeignKey → Assignment | |
| question_text | TextField | The MCQ question |
| option_a / option_b / option_c / option_d | CharField(300) | Four answer options |
| correct_option | CharField(1) | `A`, `B`, `C`, or `D` |
| difficulty | CharField(10) | `easy`, `medium`, `hard` |
| marks | PositiveIntegerField | 1 (easy), 2 (medium), 4 (hard) |
| explanation | TextField | LLM-generated explanation |
| is_active | BooleanField | Professor can deactivate questions |
| created_at | DateTimeField | Auto-set |

#### `assignments.StudentAttempt`
| Field | Type | Notes |
|---|---|---|
| assignment | ForeignKey → Assignment | |
| student | ForeignKey → User | |
| started_at | DateTimeField | Auto-set when attempt begins |
| expires_at | DateTimeField | `started_at + duration_minutes` |
| submitted_at | DateTimeField | Null until submission |
| seed | CharField | SHA256 hash for deterministic shuffling |
| score | PositiveIntegerField | Marks scored |
| total_marks | PositiveIntegerField | Total marks available |
| **Unique Together** | (assignment, student) | Prevents retakes |

#### `assignments.StudentAnswer`
| Field | Type | Notes |
|---|---|---|
| assignment | ForeignKey → Assignment | |
| question | ForeignKey → AssignmentQuestion | |
| student | ForeignKey → User | |
| selected_option | CharField(1) | Student's choice: A/B/C/D |
| is_correct | BooleanField | Auto-computed on save |
| answered_at | DateTimeField | Auto-set |
| **Unique Together** | (assignment, question, student) | One answer per question |

#### `queries.Query`
| Field | Type | Notes |
|---|---|---|
| course | ForeignKey → Course | |
| student | ForeignKey → User | Student who raised it |
| title | CharField(200) | Query subject |
| status | CharField(20) | `open`, `in_progress`, `resolved` |
| created_at | DateTimeField | Auto-set |
| updated_at | DateTimeField | Auto-updated on save |
| **Ordering** | ['-updated_at'] | Most recently active first |

#### `queries.QueryMessage`
| Field | Type | Notes |
|---|---|---|
| query | ForeignKey → Query | |
| sender | ForeignKey → User | Student or staff |
| message | TextField | Message body |
| attachment | FileField | Optional; `/media/query_attachments/` |
| created_at | DateTimeField | Auto-set |
| **Ordering** | ['created_at'] | Chronological thread |

---

## 6. User Roles & Access Control

### Role Hierarchy

```
admin
  └── Full Django admin panel access; manages all users, courses, enrollments

professor
  ├── Upload / delete / publish course materials
  ├── Create, edit, delete assignments
  ├── Generate MCQs via OLLAMA
  ├── View all student submissions and grades
  └── Respond to student queries & update query status

ta (Teaching Assistant)
  ├── View published course materials
  ├── View all student queries in assigned courses
  └── Respond to queries & update query status

student
  ├── View published course materials
  ├── Take published assignments (once, time-limited)
  ├── View own grades and per-question feedback
  ├── Create queries (doubts)
  └── View and reply to own queries
```

### Access Enforcement

All views use the `@login_required` decorator. Role checks are done inline in each view:

```python
# Role-based routing pattern used throughout the codebase
if request.user.role == 'professor':
    return professor_assignments(request, course_id)
elif request.user.role == 'student':
    return student_assignments(request, course_id)
```

Enrollment is also verified by querying the relevant through-model (`CourseStudent`, `CourseTA`, `CourseProfessor`) before granting access to any course page.

---

## 7. Core Features

### 7.1 Course & Semester Management

- Courses are organised by `Semester` (year_start, year_end, sem)
- The landing dashboard (`/courses/`) groups a user's courses into **Recent** and **Past** semesters
- Role-aware entry point `/courses/<id>/enter/` routes each user to the correct home

### 7.2 Lecture Material Upload & Auto Text Extraction

1. Professor uploads a file (PDF, PPTX, TXT, MD) with a title and content type
2. File saved to `/media/course_materials/`
3. A `post_save` Django signal fires immediately after the record is created (`content/signals.py`)
4. Signal calls `extract_and_cache_material_text()` (`content/extract.py`):
   - `.pdf` → parsed with `pypdf.PdfReader`, text joined from all pages
   - `.pptx` → parsed with `python-pptx`, text extracted from all shapes across all slides
   - `.txt` / `.md` → decoded as UTF-8
   - `.ppt` → rejected with "use .pptx" error message
5. Result stored in `CourseMaterialText` with status `ok`, `unsupported`, or `error`
6. Professor can toggle `is_published` to show/hide material from students at any time

### 7.3 Online Quiz / Assignment System

**Creating an Assignment**:
- Professor fills title, description, due date, duration (1–300 minutes)
- Can optionally publish immediately

**MCQ Generation** (detailed in Section 8):
- Select course materials to ground questions in
- Choose number of questions and optionally specify a topic/focus area
- OLLAMA generates questions; professor reviews and activates/deactivates individual questions

**Student Taking a Quiz**:
1. Student visits the assignment list; sees only published assignments not yet past due
2. Clicks "Take Assignment" — system creates a `StudentAttempt` with:
   - SHA256 seed: `sha256(f"{assignment.id}:{student.id}:{timestamp}")`
   - Expiry: `now + timedelta(minutes=duration_minutes)`
3. Questions are fetched and shuffled deterministically using the seed
4. Answer options per question are also shuffled using the same seed
5. A JavaScript countdown timer shows remaining time; auto-submits on expiry
6. On submit, `StudentAnswer` records are created and `is_correct` is evaluated
7. Score computed: sum of `question.marks` where `is_correct=True`
8. Results page shows score/total, per-question correct/incorrect indicator, and explanation
9. Attempt is locked after submission (`submitted_at` is non-null); no retakes allowed

**Viewing Results (Professor)**:
- Class-wide table showing each student's score and percentage
- Individual student answer breakdown available

### 7.4 Student Doubt / Query System

- Student creates a Query with a title and initial message (optional file attachment)
- Query status starts as `open`
- TAs and professors see all course queries on their dashboard, filterable by status
- Any party can add messages to the thread
- When a TA/professor responds, status automatically advances to `in_progress`
- TAs/professors can manually set status to `resolved` or back to `open`
- Students see status badges on their query list

---

## 8. LLM Integration & MCQ Generation

### 8.1 OLLAMA Setup

Quetor uses OLLAMA — a tool for running large language models locally on the server. This means:
- All inference is on-premises; no data leaves the institution's infrastructure
- Default model: **Gemma 3** (`gemma3`); configurable via the `OLLAMA_MODEL` environment variable
- OLLAMA listens on `http://127.0.0.1:11434` by default (configurable via `OLLAMA_BASE_URL`)

### 8.2 MCQ Generation Pipeline (`assignments/services.py`)

```
Professor initiates MCQ generation
        │
        ▼
Collect selected CourseMaterial IDs
        │
        ▼
Read CourseMaterialText.text for each selected material
        │
        ▼
Chunk text: max 4500 chars/chunk, max 20 chunks  (pdf_text.py)
        │
        ▼
Compute difficulty distribution:
  Easy:   40% of total questions (1 mark each)
  Medium: 30% of total questions (2 marks each)
  Hard:   30% of total questions (4 marks each)
        │
        ▼
Generate 2× target count (over-generate pool)
        │
        ▼
Call generate_mcqs_with_ollama() per chunk  (llm_client.py)
        │
        ▼
Collect all questions, deduplicate by (difficulty, question_text.lower())
        │
        ▼
Randomly sample down to exact target counts per difficulty
        │
        ▼
Save AssignmentQuestion records in an atomic DB transaction
```

### 8.3 OLLAMA API Client (`assignments/llm_client.py`)

**Request**:
```
POST http://127.0.0.1:11434/api/generate
Content-Type: application/json

{
  "model": "gemma3",
  "prompt": "<constructed prompt>",
  "stream": false
}
```

**Timeout**: 300 seconds per request

**Expected LLM Response Format**:
```json
{
  "questions": [
    {
      "question": "What is ...",
      "options": {
        "A": "...",
        "B": "...",
        "C": "...",
        "D": "..."
      },
      "correct": "B",
      "explanation": "Because ..."
    }
  ]
}
```

**Error Handling**:
- Strips markdown code fences (` ```json ... ``` `) before JSON parsing
- Falls back to searching for the first `{...}` block in the response
- Returns empty list on `json.JSONDecodeError`
- Detects empty OLLAMA response and raises informative error
- Raises `RuntimeError` if pypdf / python-pptx are not installed

### 8.4 Prompt Design

**Document-Grounded Prompt** (when materials are selected — primary mode):
```
You are a professor creating exam questions STRICTLY from the provided course material.

SOURCE TEXT:
<extracted text from slides>

STRICT RULES:
1. Generate ONLY from the SOURCE TEXT above
2. Do NOT use general knowledge
3. All facts must be explicitly stated in the SOURCE
4. Generate {n} {difficulty} MCQs

Return ONLY valid JSON: {"questions": [...]}
```

**Generic Prompt** (no materials selected — fallback):
```
Generate {n} {difficulty} MCQs for course {code} - {name}.
Topic: {topic}

Return ONLY valid JSON: {"questions": [...]}
```

The document-grounded mode is the primary mode and reduces LLM hallucinations by anchoring all questions to actual slide content.

### 8.5 Text Chunking (`assignments/pdf_text.py`)

Large documents are split to stay within the LLM's context window:
- Maximum chunk size: **4500 characters**
- Maximum chunks per document: **20**
- Questions are generated per chunk, then pooled across all chunks and deduplicated

---

## 9. URL Routing

### Root URLs (`config/urls.py`)

| URL Prefix | Routed To | Description |
|---|---|---|
| `/` | Redirect → `/accounts/login/` | Root redirects to login |
| `/admin/` | Django admin | Admin panel |
| `/accounts/register/` | `users.urls` | User registration |
| `/accounts/` | `django.contrib.auth.urls` | Login, logout, password reset |
| `/courses/` | `courses.urls` | Course management |
| `/content/` | `content.urls` | Material delete / toggle visibility |
| `/assignments/` | `assignments.urls` | Quiz management |
| `/queries/` | `queries.urls` | Doubt system |
| `/media/` | Media files | Uploaded file serving (dev only) |

### Courses URLs (`courses/urls.py`)

| URL Pattern | View | Description |
|---|---|---|
| `` (empty) | `my_courses` | Landing dashboard |
| `<int:course_id>/enter/` | `enter_course` | Role-aware router |
| `<int:course_id>/professor/home/` | `professor_course_home` | Professor home |
| `<int:course_id>/ta/home/` | `ta_course_home` | TA home |
| `<int:course_id>/student/home/` | `student_course_home` | Student home |
| `account/` | `my_account` | Account page |
| `contact/` | `contact_us` | Contact page |

### Content URLs (`content/urls.py`)

| URL Pattern | View | Description |
|---|---|---|
| `<int:material_id>/delete/` | `delete_material` | Delete material (professor only) |
| `<int:material_id>/toggle/` | `toggle_visibility` | Publish/unpublish material |

### Assignment URLs (`assignments/urls.py`)

| URL Pattern | View | Description |
|---|---|---|
| `<int:course_id>/` | `course_assignments` | Role router |
| `<int:course_id>/professor/` | `professor_assignments` | Professor assignment list |
| `<int:course_id>/professor/create/` | `create_assignment` | Create new quiz |
| `<int:course_id>/professor/<int:assignment_id>/edit/` | `edit_assignment` | Edit quiz details |
| `<int:course_id>/professor/<int:assignment_id>/delete/` | `delete_assignment` | Delete quiz |
| `<int:course_id>/professor/<int:assignment_id>/generate/` | `generate_mcqs` | LLM MCQ generation |
| `<int:course_id>/professor/<int:assignment_id>/questions/` | `assignment_questions` | Review questions |
| `<int:course_id>/professor/<int:assignment_id>/results/` | `assignment_results` | Student grades |
| `<int:course_id>/student/` | `student_assignments` | Student assignment list |
| `<int:course_id>/student/<int:assignment_id>/take/` | `student_take_assignment` | Take quiz |

### Query URLs (`queries/urls.py`)

| URL Pattern | View | Description |
|---|---|---|
| `<int:course_id>/student/` | `student_queries` | Student's own queries |
| `<int:course_id>/create/` | `create_query` | Create new query |
| `<int:query_id>/detail/` | `query_detail` | Threaded message view |
| `<int:course_id>/ta/` | `ta_queries` | TA/professor view of all queries |
| `<int:query_id>/status/` | `update_query_status` | Change query status |

---

## 10. Views & Business Logic

### 10.1 Users (`users/views.py`)

**`register(request)`**
- GET: Renders `CustomUserCreationForm` with role selector
- POST: Validates form, creates user, redirects to login

### 10.2 Courses (`courses/views.py`)

**`my_courses(request)`**
- Fetches courses for the logged-in user based on role (professor/ta/student)
- Groups into Recent and Past semesters
- Renders the landing dashboard

**`enter_course(request, course_id)`**
- Verifies user is enrolled/assigned to the course
- Redirects based on `request.user.role` to the appropriate home view

**`professor_course_home(request, course_id)`**
- GET: Lists all materials with published status; shows material count stats
- POST: Handles file upload form; creates `CourseMaterial`; signal fires text extraction

### 10.3 Content (`content/views.py`)

**`delete_material(request, material_id)`**
- POST only; professor only; deletes file and DB record

**`toggle_visibility(request, material_id)`**
- POST only; professor only; flips `is_published` on the material

### 10.4 Assignments (`assignments/views.py`)

**`course_assignments(request, course_id)`**
- Routes to `professor_assignments` or `student_assignments` based on role

**`generate_mcqs(request, course_id, assignment_id)`**
- GET: Renders form with course materials checklist, topic field, question count
- POST: Calls `services.generate_mcqs_for_assignment()`; redirects to questions review on success

**`student_take_assignment(request, course_id, assignment_id)`**
- GET: Creates or retrieves `StudentAttempt`; checks expiry; shuffles questions and options using seed; renders quiz
- POST: Iterates submitted answers; creates/updates `StudentAnswer` records; computes and stores score; marks attempt as submitted; re-renders with results

**`assignment_results(request, course_id, assignment_id)`**
- Professor only; queries all `StudentAttempt` records for the assignment
- Renders score table with percentage per student

### 10.5 Queries (`queries/views.py`)

**`query_detail(request, query_id)`**
- GET: Renders full message thread; students can only see their own queries
- POST: Creates new `QueryMessage`; if sender is TA/professor and status is `open`, auto-advances to `in_progress`

**`update_query_status(request, query_id)`**
- POST only; TA/professor only; sets `query.status` to the submitted value
- Returns 403 if called by a student

---

## 11. Frontend & Templates

### 11.1 Template Hierarchy

```
base.html  (minimal — used by auth/registration pages)
└── courses/base.html  (main chrome: header + sidebar navigation)
    ├── courses/my_courses.html
    ├── courses/professor_home.html
    ├── courses/student_home.html
    ├── courses/ta_home.html
    ├── courses/my_account.html
    ├── courses/contact_us.html
    ├── assignments/professor_assignments.html
    ├── assignments/create_assignment.html
    ├── assignments/generate_mcqs.html
    ├── assignments/assignment_questions.html
    ├── assignments/assignment_results.html
    ├── assignments/student_assignments.html
    ├── assignments/student_take_assignment.html
    ├── queries/student_queries.html
    ├── queries/create_query.html
    ├── queries/query_detail.html
    └── queries/ta_queries.html
```

### 11.2 Key Template Descriptions

**`registration/login.html`**
- IITK logo header, email/password form, "Remember me" checkbox, link to register

**`courses/my_courses.html`**
- Semester-grouped course cards; Recent vs Past clearly separated; one-click entry to course home

**`courses/professor_home.html`**
- Two-column layout: upload form on one side, materials table with publish toggle + delete on the other
- Stats card showing uploaded/published counts

**`courses/student_home.html`**
- Quick action cards: "Take Assignments", "View Grades", "Ask Questions"
- List of published course materials with download links

**`assignments/generate_mcqs.html`**
- Checklist of all course materials with their extraction status
- Topic/instruction text field, question count input
- Submit triggers OLLAMA MCQ generation

**`assignments/student_take_assignment.html`**
- JavaScript countdown timer (minutes:seconds display)
- Auto-submits form when timer reaches zero
- Shuffled question list with radio-button option groups
- Post-submission: results rendered inline with correct/incorrect colour coding and LLM-generated explanations

**`queries/query_detail.html`**
- Chat-style message bubbles differentiated by sender role
- Optional attachment download link per message
- Reply form at bottom
- Status dropdown (TA/professor only)

**`queries/ta_queries.html`**
- All course queries in a table with status badges
- Filterable by status (open / in_progress / resolved)

### 11.3 Styling

- **`static/css/auth.css`**: Login and registration page styling
- **`static/css/courses.css`**: Main application styling (cards, tables, forms, badges, sidebar)
- Inline CSS also used in several templates for component-specific styles
- No external CSS or JS frameworks — all styling is custom
- Timezone `Asia/Kolkata` ensures all displayed timestamps match IST

---

## 12. Configuration

### 12.1 Django Settings Highlights (`config/settings.py`)

| Setting | Value | Notes |
|---|---|---|
| `AUTH_USER_MODEL` | `users.User` | Custom user model |
| `LOGIN_REDIRECT_URL` | `/courses/` | Post-login destination |
| `LOGOUT_REDIRECT_URL` | `/accounts/login/` | Post-logout destination |
| `TIME_ZONE` | `Asia/Kolkata` | IST |
| `DEFAULT_AUTO_FIELD` | `BigAutoField` | 64-bit primary keys |
| `MEDIA_ROOT` | `BASE_DIR / 'media'` | Upload storage path |
| `MEDIA_URL` | `/media/` | URL prefix for uploaded files |
| `STATIC_ROOT` | `BASE_DIR / 'staticfiles'` | Collected static for production |
| `STATICFILES_DIRS` | `[BASE_DIR / "static"]` | Source static directory |
| Database | SQLite3 at `BASE_DIR/db.sqlite3` | |

**Installed Apps**:
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'courses',
    'content',
    'queries',
    'assignments',
]
```

### 12.2 Environment Variables (`.env.example`)

```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*

# OLLAMA (local LLM)
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma3

# Email (optional — for password reset)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
DEFAULT_FROM_EMAIL=Your Name <your_email@gmail.com>
```

### 12.3 Running the Project

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env   # then edit .env

# 4. Set up database
python manage.py migrate
python manage.py createsuperuser

# 5. Start development server
python manage.py runserver 0.0.0.0:8100
```

OLLAMA must be running separately before MCQ generation is used:
```bash
ollama serve          # starts OLLAMA on port 11434
ollama pull gemma3    # download the default model
```

### 12.4 Admin Interface

Registered models and their customisations:

| Model | Admin Features |
|---|---|
| `User` | Basic registration |
| `Semester` | Create/manage academic periods |
| `Course` | Create/manage courses |
| `CourseProfessor` | Assign professor to course |
| `CourseTA` | Assign TAs to course |
| `CourseStudent` | Enrol students |
| `CourseMaterial` | View uploaded materials |
| `Assignment` | Basic registration |
| `Query` | list_display, list_filter (status, course), search, date hierarchy |
| `QueryMessage` | list_display with message preview, filters |

---

## 13. Data Flow Diagrams

### 13.1 MCQ Generation Flow

```
Professor uploads lecture slide (PDF / PPTX)
        │
        ▼
CourseMaterial record saved in DB
        │
        │  post_save signal (content/signals.py)
        ▼
extract_and_cache_material_text()
        │
        │  pypdf / python-pptx / UTF-8 decode
        ▼
CourseMaterialText.text cached in DB  (status = ok / unsupported / error)
        │
        │  Professor visits /generate/ form
        │  Selects materials, sets topic, sets question count
        ▼
services.generate_mcqs_for_assignment()
        │
        │  Read CourseMaterialText.text
        │  Chunk into ≤4500 char segments (max 20 chunks)
        ▼
llm_client.generate_mcqs_with_ollama()
        │
        │  HTTP POST → OLLAMA /api/generate
        │  Prompt: "Generate {n} MCQs ONLY from SOURCE: <text chunk>"
        ▼
OLLAMA (Gemma3 model) returns JSON
        │
        ▼
services.py:
  Parse JSON → deduplicate → sample by difficulty
  (40% easy @ 1 mark, 30% medium @ 2 marks, 30% hard @ 4 marks)
        │
        ▼
AssignmentQuestion records saved in DB (atomic transaction)
        │
        │  Professor reviews at /questions/
        │  Activates or deactivates individual questions
        ▼
Assignment published → visible to students
```

### 13.2 Student Quiz Flow

```
Student visits /assignments/{course_id}/student/
        │
        ▼
List of published, non-expired assignments shown
        │
        │  Student clicks "Take Assignment"
        ▼
StudentAttempt created:
  seed       = SHA256("{assignment_id}:{student_id}:{timestamp}")
  expires_at = now + timedelta(minutes=duration_minutes)
        │
        ▼
Active questions fetched, shuffled by seed
Options A/B/C/D per question also shuffled by seed
        │
        ▼
Quiz rendered with JavaScript countdown timer
        │
        │  Student selects answers and submits
        │  (or timer auto-submits)
        ▼
For each question:
  StudentAnswer created  (selected_option, is_correct)
  is_correct = (selected_option == correct_option)
        │
        ▼
attempt.score      = Σ marks where is_correct=True
attempt.total_marks = Σ all active question marks
attempt.submitted_at = now  →  attempt locked (no retakes)
        │
        ▼
Page re-renders showing:
  Score and percentage
  Per-question: student's answer, correct answer, LLM explanation
```

---

## 14. Security Considerations

### Implemented Protections

| Concern | Mechanism |
|---|---|
| Authentication | Django session auth with PBKDF2 password hashing |
| CSRF | `{% csrf_token %}` on all POST forms via Django middleware |
| Role enforcement | Inline `request.user.role` checks in every protected view |
| Enrollment checks | DB queries verify user is enrolled before granting access |
| Unique quiz attempt | `unique_together` on `StudentAttempt(assignment, student)` prevents retakes |
| Server-side timer | `expires_at` stored server-side; JS timer is UI-only and cannot be forged |
| File storage | Uploads stored in `/media/`, not served with execute permissions |
| Secret Key | Loaded from `.env`, not hardcoded in source |
| ORM usage | Django ORM prevents raw SQL injection throughout |

### Production Recommendations

- Set `DEBUG=False` and configure `ALLOWED_HOSTS` to the actual domain
- Replace SQLite with PostgreSQL for concurrent access
- Set a long random `SECRET_KEY` in the production `.env`
- Use environment-level secrets management instead of `.env` files on shared systems
- Add rate limiting to the login and MCQ generation endpoints
- Add file upload size limits and MIME type validation

---

## 15. Limitations & Future Scope

### Current Limitations

| Area | Limitation |
|---|---|
| Database | SQLite not suitable for concurrent production load |
| LLM Quality | MCQ quality depends on Gemma3's capability; questions may occasionally be trivial |
| Synchronous LLM | MCQ generation is synchronous; large PPTX on a slow GPU can timeout the browser request |
| No Retakes | Students cannot retake quizzes even for practice purposes |
| Single Professor | Each course supports only one primary professor (`OneToOneField`) |
| No Analytics | No aggregate analytics across courses or over time |
| No Notifications | No email/in-app notifications for new query responses or grade releases |

### Suggested Future Enhancements

1. **Async MCQ Generation** — Use Celery + Redis to run OLLAMA generation in the background with a progress indicator
2. **PostgreSQL Migration** — Switch to PostgreSQL for production-grade concurrency
3. **Question Bank** — Reuse and curate generated questions across multiple assignments
4. **Question Editing** — Allow professors to edit LLM-generated questions before publishing
5. **Configurable Retakes** — Per-assignment setting for number of allowed attempts
6. **Analytics Dashboard** — Per-course difficulty distribution, student performance trends over time
7. **Email Notifications** — Alert students when queries are answered or grades posted
8. **Better LLM Model Support** — UI to switch between OLLAMA-compatible models (Llama 3, Mistral, etc.)
9. **REST API** — Expose endpoints for a potential mobile application
10. **File Upload Validation** — Server-side MIME type checking and size limits

---

## Summary

Quetor is a complete, end-to-end educational platform that uniquely combines **on-premises AI** with a **structured academic workflow**. By integrating OLLAMA-powered MCQ generation with Django's ORM and role-based access control, the platform enables instructors to go from raw lecture slides to published, auto-graded quizzes in minutes — without sending any data to external cloud AI services.

The five Django apps (users, courses, content, assignments, queries) provide a clean separation of concerns. The codebase uses signal-based event handling for automatic text extraction, deterministic seeding for fair quiz shuffling, a two-phase over-generate-then-sample strategy for balanced difficulty distribution, and a threaded message model for structured doubt resolution.

---

*Report prepared by Snehasis Satapathy (221070) and Gautam Arora (220405)*
*Under the supervision of Professor Shubham Sahay, IIT Kanpur*

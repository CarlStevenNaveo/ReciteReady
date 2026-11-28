# ReciteReady — Practice Randomly, Answer Confidently

**ReciteReady** is a Django & PostgreSQL (Supabase) web application designed to help students prepare for oral recitations and graded defenses. Instead of memorizing questions in a fixed sequence, learners organize study prompts into shareable decks, run randomized timed oral drills with live voice transcription, self-evaluate against model answers, and track readiness analytics over time.

---

## Core Feature (Project Development 2 — Vertical Slice)

### Question Bank & Randomized Timed Recitation Practice
The core vertical slice spans the database (PostgreSQL/Supabase), backend (Django views, forms, models, URLs), and frontend (monochrome minimalist Bootstrap 5 templates):

1. **Question Bank & Deck Sharing (`Deck`, `Question`):**
   - Full CRUD for creating, viewing, updating, and deleting recitation decks and questions.
   - Difficulty tagging (`EASY`, `MEDIUM`, `HARD`) and comma-separated topic tags.
   - Automatic unique 8-character share codes (`RR-XXXXXX`), public/private visibility toggles, Join-by-Code lookup, and 1-click deck cloning.
2. **Randomized Timed Practice & Scoring (`PracticeSession`, `PracticeAttempt`):**
   - Configure sessions by difficulty filter, question count, randomized shuffle order, and per-question countdown timer (30s–120s or untimed).
   - Interactive oral practice screen with a live SVG countdown ring, browser Web Speech API microphone transcription, expandable model answer, and 3-tier self-evaluation rubric (*Mastered 100%*, *Partially Correct 50%*, *Needs Practice 0%*).
   - Automatic score calculation and question-by-question results breakdown.
3. **Performance Analytics & Practice Reminders (`PracticeReminder`, `Notification`):**
   - Dynamic readiness index, historical attempt log, accuracy distribution bars, and automated **Target Weak Areas** tracking.
   - Configurable recurring practice reminders and in-app notification center.
4. **Role-Based Access & Live Dashboards:**
   - **Students** manage personal decks, run randomized drills, view personal analytics, and can only access/modify their own records.
   - **Instructors** author and publish decks, monitor live registered student counts, class mastery averages, and review completed student drill results.

---

## Standard Features (Project Development 1)

- **Account Registration** (Student & Instructor role selection, password hashing, email/username uniqueness validation)
- **Login / Logout** (Username or email login, secure session clearing)
- **Role-Based User Dashboards** (Dedicated Student Portal and Instructor Portal backed by live PostgreSQL queries)
- **User Profile & Account Management** (View/edit profile, avatar upload, password change, account deactivation)

---

## Tech Stack

- **Backend:** Python 3.12, Django 6.1.3, Gunicorn
- **Database:** PostgreSQL (Supabase) via `psycopg2-binary` & `dj-database-url`
- **Frontend:** HTML5, Bootstrap 5.3, Bootstrap Icons, Jost & DM Sans typography, Web Speech API
- **Static Files & Deployment:** WhiteNoise, Render (`render.yaml`, `build.sh`, `Procfile`)

---

## Local Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CarlStevenNaveo/ReciteReady.git
   cd ReciteReady
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # macOS / Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy `.env.example` to `.env` and set your values:
   ```env
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   DATABASE_URL=postgresql://user:password@host:5432/postgres
   ```

5. **Run database migrations & optional sample deck seed:**
   ```bash
   python manage.py migrate
   python manage.py seed_recitations
   ```

6. **Run the development server & test suite:**
   ```bash
   python manage.py test
   python manage.py runserver
   ```
   Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## Branching Strategy

- `main`: Stable production code only (updated via Pull Request from `develop`).
- `develop`: Integration branch created from `main`.
- `feature/<feature-name>`: Feature branches created from `develop` and merged back via Pull Requests (merged feature branches are preserved for audit history).

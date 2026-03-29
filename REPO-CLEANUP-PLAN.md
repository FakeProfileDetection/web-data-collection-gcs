# Web Data Collection GCS — Anonymous Repo Cleanup Plan

> Created: 2026-03-29
> Target org: **FPD-Research-2026** (via `github-anon` SSH alias)
> Approach: Fresh repo, no commit history carried over

---

## Overview

Prepare a clean, publishable copy of this repo for the anonymous GitHub org
`FPD-Research-2026`. The published version should be **usable by others** — with
clear instructions on what they need to configure (GCP, hosting, etc.) — but must
contain no PII, team-identifying info, or infrastructure tied to our accounts.

---

## Cleanup Issues

### 1. Videos — Copyright Review
**Files:** `pages/hosting/videos/` (3 clips, ~12.4 MB total)
- Coach Carter movie clip (2005)
- Will Smith / Oscars clip
- Trump / Vance / Zelenskyy clip

**Concern:** Redistributing copyrighted video clips in a public GitHub repo.
**Decision:** Keep all clips. Add fair use notice, copyright table, and video replacement
instructions in README.md. Emphasize research-only use at top of README.

**Status:** DONE (2026-03-29) — README.md rewritten with fair use notice, copyright table,
replacement instructions, and research-only disclaimer

---

### 2. PII — Researcher Email (Indrani)
**Found in:** `pages/hosting/survey-code.html` (4 occurrences of `irentala@myharrisburgu.com`)
**Action:** Replace with a generic placeholder (e.g., `researcher@example.edu`) or a
role-based address, with a comment to update.
**Status:** DONE (2026-03-29) — all 4 occurrences replaced with `fpd.research.2026@gmail.com` (anonymous contact for blind review)

---

### 3. GCP Infrastructure — Project ID, Bucket, Service Account
**Found in:**
| Value | File(s) |
|-------|---------|
| `fake-profile-detection-460117` (project ID) | `cloud-functions/saver/deployment.sh`, `gcs-to-supabase-sync/main.py` |
| `fake-profile-detection-eda-bucket` (bucket) | `cloud-functions/saver/index.js` |
| `web-data-collection-sa@...iam.gserviceaccount.com` | `cloud-functions/saver/deployment.sh` |
| `https://us-east1-fake-profile-detection-460117.cloudfunctions.net/saver` | `utils/common.js` |

**Action:** Replace all with `YOUR_GCP_PROJECT_ID`, `YOUR_GCS_BUCKET`, etc.
Add a setup guide explaining how to create your own GCP project, bucket, Cloud
Function, and service account.
**Status:** DONE (2026-03-29) — All GCP project IDs, bucket names, service accounts, Cloud Function
URLs, and GitHub Pages URLs replaced with `YOUR_*` placeholders across 5 files:
`deployment.sh`, `index.js`, `common.js`, `test-upload.html`, `km_headless_testbed/index.html`,
`mturk-Design-Layout.html`. Also fixed two hardcoded URLs in `common.js` to use `CONFIG.API.BASE_URL`.

---

### 4. Supabase References — Remove
**Found in:** `gcs-to-supabase-sync/` directory, references in `main.py`
**Context:** Legacy from earlier work; no current dependencies.
**Action:** Remove `gcs-to-supabase-sync/` directory entirely.
**Status:** DONE (2026-03-29) — directory removed via `git rm -r`, untracked `.env` deleted

---

### 5. Netlify Reference — Remove
**Found in:** `pages/hosting/mturk-Design-Layout.html`
(`melodious-squirrel-b0930c.netlify.app`)
**Context:** Earlier survey-code validation; no current dependency.
**Action:** Replace URL with placeholder or remove the validation call.
**Status:** DONE (2026-03-29) — Netlify URL replaced with `YOUR_VALIDATION_API_URL` placeholder + TODO comment

---

### 6. Consent Page / IRB Document
**Files:**
- `pages/hosting/Informed Consent.pdf` — likely contains PI names, institution, IRB number
- `pages/hosting/consent.html` — links to the PDF
- `pages/hosting/demographics.html` — mentions IRB approval

**Action:** Review PDF for identifying info. Options:
- (a) Redact PI names/IRB# and include redacted version
- (b) Remove PDF, keep consent.html as a template with placeholder text
- (c) Replace with anonymized summary of consent language

**Status:** DONE (2026-03-29) — replaced PDF with generic template generated from
`Informed Consent.md`. All PII (researcher names, emails, institutions, IRB contacts)
replaced with "Your Information". README updated with customization instructions.

---

### 7. GitHub Org / URLs — FakeProfileDetection References
**Found in:**
- `cloud-functions/saver/index.js` — CORS origin `https://fakeprofiledetection.github.io`
- `utils/common.js` — Cloud Function URL
- `README.md` — live study link
- `package.json` — homepage URL (AlvinKuruvilla/kmlog reference)

**Action:** Replace org-specific URLs with `YOUR_GITHUB_PAGES_URL` placeholders.
Update README for the anonymous context.
**Status:** DONE (2026-03-29) — all FakeProfileDetection URLs replaced with placeholders across index.js, common.js, and mturk-Design-Layout.html

---

### 8. Team / Author References
**Found in:**
- `package.json` — `AlvinKuruvilla` homepage reference
- `README.md` — credits to cloned repos (these are fine — they're open source attribution)
- Third-party clone credits (Facebook, Instagram) — keep as proper attribution

**Action:** Remove `AlvinKuruvilla` reference from package.json. Keep open-source
attribution for cloned projects (required by their licenses).
**Status:** DONE (2026-03-29) — replaced homepage, bugs, and repository URLs with `YOUR_GITHUB_ORG/YOUR_REPO` placeholders

---

### 9. Instructions / Study-Specific Content
**Files:** `pages/hosting/instructions.html`, `pages/hosting/tasks.html`, etc.
**Action:** Review for team-specific language, institution names, or researcher
identifiers.
**Status:** DONE (2026-03-29) — replaced "University of Harrisburg" → INSTITUTION_NAME,
"Multimodal Fake Profile Detection Research" → STUDY_DESCRIPTION,
"Fake Profile Detection Study" → STUDY_NAME (in start_study.html, consent.html),
fpd.research.2026@gmail.com → RESEARCHER_EMAIL. Added STUDY_NAME, STUDY_DESCRIPTION,
INSTITUTION_NAME to config.env and configure.sh

---

### 10. Setup Guide for New Users
**Action:** Create a `SETUP.md` (or section in README) with instructions for:
- Creating a GCP project and storage bucket
- Deploying the Cloud Function
- Configuring GitHub Pages hosting
- Updating placeholder values throughout the code

**Status:** DONE (2026-03-29) — Setup guide is in README.md (Steps 1-5), powered by
`config.env` + `configure.sh`. Also includes Informed Consent template instructions,
video replacement guide, and verification step. No separate SETUP.md needed.

---

## Execution Order

1. **Decisions needed first:** Videos (issue 1), Consent/IRB (issue 6)
2. **Removals:** Supabase (4), Netlify (5)
3. **Scrubbing:** Email (2), GCP (3), GitHub URLs (7), Author refs (8)
4. **Review:** Instructions/study pages (9)
5. **New content:** Setup guide (10)
6. **Final review & publish** to FPD-Research-2026

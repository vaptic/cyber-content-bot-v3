# VAPTIC LMS — Go-Live Guide
## 6 Manual Steps to Production

> **Who is this for?** The person running the final pre-launch checks and
> doing the deployment. No coding is required. Every step is explained.
>
> **Prerequisites:** You need access to
> - The Firebase Console (console.firebase.google.com) — project: `vaptic--lms`
> - Google Cloud Console (console.cloud.google.com)
> - Resend.com account (resend.com) — for the email API key
> - A terminal in the project root (`/home/jason/vaptic-lms`)
> - Firebase CLI installed (checked in Step 3)

---

## Quick Map

| Step | What it is | Where | Time |
|------|-----------|-------|------|
| [1](#step-1-test-firestore-security-rules) | Test Firestore rules in Rules Playground | Firebase Console | ~20 min |
| [2](#step-2-cross-browser-verification) | Verify all pages on Chrome, Firefox, Safari | Your browsers | ~30 min |
| [3](#step-3-firebase-emulator-end-to-end-test) | End-to-end test via Firebase Emulators | Terminal | ~45 min |
| [4](#step-4-final-security-rules-verification) | Pre-launch security rules check | Firebase Console | ~10 min |
| [5](#step-5-set-firebase-budget-alert) | Set $1/month billing alert | GCP Console | ~5 min |
| [6](#step-6-deploy-to-firebase-hosting) | Deploy to production | Terminal | ~10 min |

---

## Step 1 — Test Firestore Security Rules

### What is this and why does it matter?

Your `firestore.rules` file controls who can read or write what data in the
database. It is the last line of defence if someone bypasses the frontend.
The **Rules Playground** is a simulator inside Firebase Console that lets you
test these rules without touching real data. You pretend to be different types
of users and see what gets allowed or denied.

### 1.1 Open the Rules Playground

1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Select the project **vaptic--lms**
3. Left sidebar → **Firestore Database**
4. Click the **Rules** tab at the top
5. Click **Edit rules** (you should see your current rules file)
6. At the top right of the rules editor click **Rules Playground**

You will see a panel with fields: **Simulation type**, **Path**, **Auth state**, **Data**.

---

### 1.2 Run These 12 Tests

For each test, fill in the fields as described, click **Run**, and verify the
expected result. The result appears as a green **Allow** or red **Deny** badge.

> **How to set Auth state:**
> Toggle "Authenticated" ON, then fill in the UID field with a fake ID like
> `student123` or `admin456`. For "unauthenticated" tests, toggle it OFF.

---

#### Test A — Unauthenticated user cannot read anything

- **Simulation type:** `get`
- **Path:** `/databases/(default)/documents/users/student123`
- **Auth state:** OFF (not authenticated)
- **Expected:** **DENY**
- **Why:** The `isAuthenticated()` function returns false → the `isOwner()` check fails.

---

#### Test B — Student can read their own profile

- **Simulation type:** `get`
- **Path:** `/databases/(default)/documents/users/student123`
- **Auth state:** ON — UID: `student123`
- **Expected:** **ALLOW**
- **Why:** `isOwner(userId)` is true because `request.auth.uid == userId`.

---

#### Test C — Student CANNOT read another student's profile

- **Simulation type:** `get`
- **Path:** `/databases/(default)/documents/users/otherStudent999`
- **Auth state:** ON — UID: `student123`
- **Expected:** **DENY**
- **Why:** `isOwner()` fails (wrong UID) and `isAdmin()` fails (not admin).

---

#### Test D — Student CANNOT change their own role

- **Simulation type:** `update`
- **Path:** `/databases/(default)/documents/users/student123`
- **Auth state:** ON — UID: `student123`
- **JSON data (the update):**
  ```json
  { "role": "admin" }
  ```
- **Expected:** **DENY**
- **Why:** `isValidUserSelfUpdate()` only allows `fullName`, `phone`,
  `profileUpdatedAt`. Writing `role` is not in that list.

---

#### Test E — Student can update their own name

- **Simulation type:** `update`
- **Path:** `/databases/(default)/documents/users/student123`
- **Auth state:** ON — UID: `student123`
- **JSON data (the update):**
  ```json
  { "fullName": "Jane Smith" }
  ```
- **Expected:** **ALLOW**
- **Why:** `fullName` is in the allowed self-update fields.

---

#### Test F — Authenticated student can read a course

- **Simulation type:** `get`
- **Path:** `/databases/(default)/documents/courses/foundation`
- **Auth state:** ON — UID: `student123`
- **Expected:** **ALLOW**
- **Why:** `allow read: if isAuthenticated()` on the courses collection.

---

#### Test G — Student CANNOT create an enrollment

- **Simulation type:** `create`
- **Path:** `/databases/(default)/documents/enrollments/newEnroll1`
- **Auth state:** ON — UID: `student123`
- **JSON data:**
  ```json
  { "userId": "student123", "courseId": "foundation" }
  ```
- **Expected:** **DENY**
- **Why:** `allow create: if isAdmin()` — only admins can create enrollments.

---

#### Test H — Student can read their own enrollment

For this test you need to provide "existing document data" (the current
document as it exists in the DB). In the Rules Playground, there is a
**Resource data** field below the path — fill it in.

- **Simulation type:** `get`
- **Path:** `/databases/(default)/documents/enrollments/enroll001`
- **Auth state:** ON — UID: `student123`
- **Resource data (existing doc):**
  ```json
  { "userId": "student123", "courseId": "foundation" }
  ```
- **Expected:** **ALLOW**
- **Why:** `isOwner(resource.data.userId)` → `student123 == student123` is true.

---

#### Test I — Student CANNOT read another student's enrollment

- **Simulation type:** `get`
- **Path:** `/databases/(default)/documents/enrollments/enroll002`
- **Auth state:** ON — UID: `student123`
- **Resource data (existing doc):**
  ```json
  { "userId": "otherStudent999", "courseId": "advanced" }
  ```
- **Expected:** **DENY**
- **Why:** `isOwner()` fails (wrong UID) and `isAdmin()` fails.

---

#### Test J — Student CANNOT delete their enrollment

- **Simulation type:** `delete`
- **Path:** `/databases/(default)/documents/enrollments/enroll001`
- **Auth state:** ON — UID: `student123`
- **Resource data:**
  ```json
  { "userId": "student123", "courseId": "foundation" }
  ```
- **Expected:** **DENY**
- **Why:** `allow delete: if isAdmin()` — only admins can delete enrollments.

---

#### Test K — Unauthenticated cannot access any path (catch-all)

- **Simulation type:** `get`
- **Path:** `/databases/(default)/documents/auditLog/log001`
- **Auth state:** OFF
- **Expected:** **DENY**
- **Why:** The final `match /{document=**}` rule denies everything not explicitly
  allowed, and `isAdmin()` requires authentication.

---

#### Test L — Student CANNOT access the audit log

- **Simulation type:** `get`
- **Path:** `/databases/(default)/documents/auditLog/log001`
- **Auth state:** ON — UID: `student123`
- **Expected:** **DENY**
- **Why:** `allow read: if isAdmin()` on auditLog — `student123` is not admin.
  (Note: The Rules Playground will call `isAdmin()` which does a Firestore read
  internally. Since no real data exists in the playground, it evaluates as not
  admin and correctly denies.)

---

### 1.3 What to do if a test fails

| Failure | Likely cause | Fix |
|---------|-------------|-----|
| Test B denies student reading own profile | UID in the path doesn't match UID in Auth state | Make sure both say `student123` |
| Test L allows student to read audit log | `isAdmin()` helper returning unexpected value in simulator | This is usually a simulator quirk — re-run with a fresh session |
| Any unexpected ALLOW on a DENY test | Check for typos in the path | Double check collection name casing (`users` not `Users`) |

---

### 1.4 Add a test summary comment to firestore.rules

Once all 12 tests pass, open `firestore.rules` and add this comment block at
the very top (above `rules_version`). This documents what was tested:

```
/**
 * FIRESTORE RULES — TEST RECORD
 * Tested in Firebase Rules Playground — [DATE]
 * Tests passed:
 *   A. Unauthenticated cannot read /users         → DENY ✓
 *   B. Student reads own /users/{uid}             → ALLOW ✓
 *   C. Student cannot read other /users/{uid}     → DENY ✓
 *   D. Student cannot change own role             → DENY ✓
 *   E. Student can update own fullName            → ALLOW ✓
 *   F. Authenticated reads /courses/{id}          → ALLOW ✓
 *   G. Student cannot create enrollment           → DENY ✓
 *   H. Student reads own enrollment               → ALLOW ✓
 *   I. Student cannot read other's enrollment     → DENY ✓
 *   J. Student cannot delete enrollment           → DENY ✓
 *   K. Unauthenticated denied catch-all           → DENY ✓
 *   L. Student cannot read auditLog               → DENY ✓
 */
```

---

## Step 2 — Cross-Browser Verification

### What is this and why does it matter?

Different browsers render CSS differently and enforce security policies
differently. Safari on iOS is notorious for behaving differently from Chrome.
Firefox has stricter cookie handling. We need to make sure every page loads
without JavaScript errors on all three.

### 2.1 Browsers to test

| Browser | Where to get it |
|---------|----------------|
| Google Chrome | Already installed on most machines |
| Mozilla Firefox | firefox.com |
| Safari | Only on macOS/iOS — use macOS or an iPhone/iPad |

If you don't have Safari on a Mac, you can use the free **BrowserStack** trial
(browserstack.com) — it gives you real Safari on real macOS in the browser.

---

### 2.2 For each browser — setup

1. Open the browser
2. Open Developer Tools:
   - Chrome/Firefox: press `F12` or `Ctrl+Shift+I`
   - Safari: `Cmd+Option+I` (must enable Developer menu in Preferences → Advanced first)
3. Click the **Console** tab — this is where JavaScript errors appear
4. Click the **Network** tab — this is where failed requests appear

Keep the Console and Network tabs open the entire time you test. Any red errors
are problems.

---

### 2.3 Pages to test and what to look for

Since the app requires login, start with the public pages, then test logged-in
pages with a real or test account.

Go to your production URL for now it's `https://vaptic--lms.web.app` (after
Step 6 deploy), or run locally with `firebase serve` (see Step 3).

---

#### Page: `login.html`

1. Load the page
2. **Console:** should be empty (no red errors)
3. **What to check visually:**
   - Logo appears
   - Form fields are visible and editable
   - "Login" button is present
4. **Test interaction:** Enter a wrong email/password → should see an error
   message (not a raw Firebase error string)
5. **Test interaction:** Enter a correct admin email/password → should redirect
   to `dashboard.html`

**Common issue — Safari:** If you see a console error about `enablePersistence`,
it means IndexedDB is blocked. This is a known Safari quirk in private browsing
mode. It won't affect normal browsing. The code already handles it gracefully
with a `catch` block.

---

#### Page: `signup.html`

1. Load the page
2. Console: no red errors
3. Fill in the form with a test name, email, phone, and select a course
4. Submit → should show "Account created! Awaiting admin approval."
5. Check Firestore in Firebase Console: a new user doc should appear with
   `status: "pending"` and `role: "student"`

---

#### Page: `dashboard.html` (logged in as student)

1. Log in as a student whose status is `approved`
2. Check that the dashboard loads the enrollment card(s)
3. Progress bar should show a percentage
4. If no courses: the "Available Courses" section should show foundation/advanced
5. **Console:** look specifically for any `innerHTML` warnings or CSP violations
   (these appear in red in the console)

**CSP violation looks like:**
```
Refused to load script from 'example.com' because it violates the Content Security Policy
```
If you see one, note the URL it's complaining about and let me know — we may
need to add it to the CSP allowlist in `firebase.json`.

---

#### Page: `admin-panel.html` (logged in as admin)

1. Log in as admin
2. Navigate to `admin-panel.html` (or click "Admin Panel" button in dashboard nav)
3. Click each tab: **Students**, **Enrollments**, **Batches**, **Live Sessions**
4. Each tab should load data without errors
5. **Mobile check:** Resize the browser window to 375px wide (iPhone size)
   - The table should not overflow horizontally
   - The "Course Interest" column should disappear (it has a media query for this)
   - The modal (if you click "Enroll") should be full-width

---

#### Page: `module-viewer.html`

1. Log in as a student who has an approved enrollment with module 1 unlocked
2. Navigate to `module-viewer.html?courseId=foundation&moduleId=1`
3. Check that:
   - The video area shows (even if no YouTube URL is set, placeholder should show)
   - The "Previous" button is disabled on module 1
   - The "Next" button is disabled if module 2 is not unlocked
   - The "Mark as Complete" button is visible
4. Resize to mobile: the video should stay in a 16:9 ratio

---

#### Page: `live-class.html`

1. Navigate to `live-class.html?courseId=foundation`
2. If no live session is active: should show "No live session is currently active"
   and the next class date if set
3. Console: no errors

---

#### Pages: `reset-password.html`, `course-viewer.html`, `content-editor.html`, `lab-setup.html`

For each:
1. Load the page
2. Console should have no red errors
3. Visually confirm the layout looks correct

---

### 2.4 What to record

Keep a simple note for anything that fails:

```
Browser: Firefox 123
Page: dashboard.html
Error: "Refused to connect to wss://... " in Console (CSP violation)
```

Then report it — I can add the missing domain to the CSP in `firebase.json`.

---

## Step 3 — Firebase Emulator End-to-End Test

### What is this and why does it matter?

The Firebase Emulator Suite runs a local fake version of Firestore, Auth,
Cloud Functions, Storage, and Hosting entirely on your machine. No internet
required, no real data touched, no charges. You test the entire student journey
— signup to course completion — and confirm every piece works together.

**This is the most important step.** If something is broken, you find it here
before your students do.

---

### 3.1 Prerequisites — Install Firebase CLI

Open a terminal in the project root (`/home/jason/vaptic-lms`).

Check if Firebase CLI is installed:
```bash
firebase --version
```

**If you see a version number (e.g. `13.x.x`):** good, skip to 3.2.

**If you see "command not found":**
```bash
npm install -g firebase-tools
firebase --version   # confirm it now shows a version
```

Then log in:
```bash
firebase login
```

This opens a browser window. Log in with the Google account that owns the
`vaptic--lms` Firebase project. Once logged in, you'll see:
```
✔  Success! Logged in as your@email.com
```

---

### 3.2 Create the Firebase project alias file

The `.firebaserc` file tells the CLI which Firebase project to use. This file
is missing from the repo. Create it now:

```bash
echo '{
  "projects": {
    "default": "vaptic--lms"
  }
}' > .firebaserc
```

Verify it was created:
```bash
cat .firebaserc
```

Should output:
```json
{
  "projects": {
    "default": "vaptic--lms"
  }
}
```

---

### 3.3 Create the functions environment file

The Cloud Functions need two environment variables: your Resend API key (for
sending emails) and your admin email address. Without these, email functions
will fail with an error (but the app still works — the error is caught and
logged).

```bash
# Create the file — replace the values with your real ones
cat > functions/.env << 'EOF'
RESEND_API_KEY=re_PASTE_YOUR_KEY_HERE
ADMIN_EMAIL=your@email.here
EOF
```

**Where to get the Resend API key:**
1. Go to [resend.com](https://resend.com) → Log in
2. Click **API Keys** in the left sidebar
3. Click **Create API Key** → Name it "vaptic-lms-functions"
4. Copy the key (starts with `re_`)
5. Paste it in place of `re_PASTE_YOUR_KEY_HERE` above

**Verify the file looks right:**
```bash
cat functions/.env
```

Should show two lines like:
```
RESEND_API_KEY=re_abc123xyz
ADMIN_EMAIL=you@yourdomain.com
```

> **Security note:** `functions/.env` is in `.gitignore` so it will NOT be
> committed to git. Never commit this file.

---

### 3.4 Install function dependencies

```bash
cd functions
npm install
cd ..
```

You should see npm output ending with something like:
```
added 87 packages in 12s
```

If you see errors: the most common issue is a Node.js version mismatch.
Run `node --version` — it should be v18 or v20. If it's older:
```bash
nvm install 20
nvm use 20
```
Then retry `npm install`.

---

### 3.5 Start the emulators

From the project root:
```bash
firebase emulators:start --only auth,firestore,functions,storage,hosting
```

You will see output like:
```
✔  firestore: Firestore Emulator started on port 8080
✔  auth: Authentication Emulator started on port 9099
✔  functions: Firebase Emulated Functions started on port 5001
✔  hosting: Firebase Hosting Emulator started on port 5000
✔  All emulators started successfully

┌────────────────────────────────────────────────────────┐
│ Emulator  │ Host:Port          │ View in Emulator UI  │
│ auth      │ localhost:9099     │                      │
│ functions │ localhost:5001     │                      │
│ firestore │ localhost:8080     │                      │
│ hosting   │ localhost:5000     │ http://localhost:4000│
│ storage   │ localhost:9199     │                      │
└────────────────────────────────────────────────────────┘
```

> **Leave this terminal open.** The emulators must keep running while you test.
> Open a second terminal for any other commands.

**If you see a port conflict error:**
```
Error: Could not start Firestore Emulator, port 8080 is in use
```
Solution: Kill the process using that port:
```bash
lsof -ti:8080 | xargs kill -9
```
Then try starting again.

---

### 3.6 Open the Emulator UI

In your browser, go to: `http://localhost:4000`

You will see a dashboard showing all emulators. This is where you can inspect
Firestore data, Auth users, and function logs in real time.

---

### 3.7 Walk through the full student journey

**Open a second browser tab:** go to `http://localhost:5000/signup.html`

> **Note:** When running locally, the app communicates with the local emulators,
> not the real Firebase. Any data you create here is temporary and disappears
> when you stop the emulators.

---

#### Stage A — Student signup

1. On `signup.html`, fill in:
   - Full Name: `Test Student`
   - Email: `student@test.com`
   - Phone: `+1234567890`
   - Course Interest: select Foundation
   - Password: `TestPass123!`
2. Click **Create Account**
3. Expected: green message "Account created. Awaiting admin approval."

**Verify in Emulator UI (http://localhost:4000):**
- Click **Firestore** → expand `users` collection
- You should see a new document with:
  - `status: "pending"`
  - `role: "student"`
  - `fullName: "Test Student"`

**Verify in Functions logs (http://localhost:4000 → Functions):**
- You should see `onUserCreate` and `notifyAdminOnSignup` in the log
- If `RESEND_API_KEY` is set correctly, the log shows email sent
- If not, you'll see a warning — that's fine for local testing

**If signup fails with a console error:**
- Check the browser console (F12) for the exact error message
- Most common: "auth/weak-password" → use a stronger password
- "auth/email-already-in-use" → use a different email
- "permission-denied" → Firestore rules are blocking the user doc creation.
  This is the most important one to fix. Open `firestore.rules` and verify
  the `isValidUserCreate` function allows `status: "pending"` and `role: "student"`.

---

#### Stage B — Create an admin account

You need an admin account to approve the student. Do this directly in the
Emulator UI (no signup form needed):

1. Go to `http://localhost:4000` → **Authentication** tab
2. Click **Add User**
3. Email: `admin@test.com`, Password: `AdminPass123!`
4. Click **Save** — note the **UID** it generates (a long string like `abc123...`)
5. Now go to **Firestore** → `users` collection → click **Add Document**
6. Document ID: paste the admin UID from step 4
7. Add these fields:
   ```
   email        (string)  admin@test.com
   fullName     (string)  Admin User
   role         (string)  admin
   status       (string)  approved
   enrolledCourses (array) [empty]
   createdAt    (timestamp) [click the calendar icon]
   ```
8. Click **Save**

---

#### Stage C — Admin approves the student

1. Go to `http://localhost:5000/login.html`
2. Log in as `admin@test.com` / `AdminPass123!`
3. You should be redirected to `dashboard.html` which shows an "Admin Panel"
   button in the nav (because `role === "admin"`)
4. Click **Admin Panel**
5. In the Students tab, find `Test Student` with status **Pending**
6. Click **Approve**
7. The status should change to **Approved** in the UI

**Verify in Emulator UI:**
- Firestore → `users` → student doc → `status` should now be `"approved"`

**Check Functions log:**
- `notifyStudentOnApproval` should appear, indicating the approval email was
  attempted

---

#### Stage D — Admin enrolls the student

Still on the admin panel:

1. First, make sure there are courses in Firestore. Go to Emulator UI →
   Firestore → check if `courses` collection exists.
   - If not, run the seed script:
     ```bash
     # In a second terminal (emulators still running)
     FIRESTORE_EMULATOR_HOST=localhost:8080 node scripts/seed-firestore.js
     ```
   - This creates the `foundation` and `advanced` course documents.

2. Back in `admin-panel.html`:
   - Go to the **Enrollments** tab
   - Select student: `Test Student`
   - Select course: `Foundation`
   - Batch number: `1`
   - Click **Enroll Student**
   - Expected: green "Student enrolled successfully"

**Verify in Emulator UI:**
- Firestore → `enrollments` collection → a new document should appear with
  `userId`, `courseId: "foundation"`, `unlockedModules: []` (or `[1]` if
  module 1 is auto-unlocked)

---

#### Stage E — Student logs in and sees their course

1. Open a new Incognito/Private window
2. Go to `http://localhost:5000/login.html`
3. Log in as `student@test.com` / `TestPass123!`
4. Expected: redirect to `dashboard.html` showing the Foundation course card
5. Progress bar should show 0%

**If you still see "Pending approval":**
- Sign out and sign back in — the auth state may be cached
- Check that the student's Firestore doc actually has `status: "approved"`

---

#### Stage F — Admin unlocks module 1

1. Back in the admin session
2. Go to **Admin Panel** → **Batches** tab
3. Select Batch 1
4. Click "Unlock Next Module for All" (this unlocks module 1 for all batch 1 students)

OR do it per-student from the Enrollments tab.

**Verify in Emulator UI:**
- Firestore → `enrollments` → student's enrollment doc → `unlockedModules: [1]`

---

#### Stage G — Student views module 1

1. In the student session
2. Click on the Foundation course card → should go to `course-viewer.html`
3. Module 1 should be clickable (unlocked), modules 2+ should be locked
4. Click Module 1 → goes to `module-viewer.html?courseId=foundation&moduleId=1`
5. The video area should show (placeholder or iframe)
6. The "Previous Module" button should be disabled
7. The "Next Module" button should be disabled (module 2 is not unlocked yet)
8. Click **Mark as Complete**
9. Expected: module marked, progress updates

**Verify:**
- Firestore → `enrollments` → student doc → `completedModules: [1]`
- Dashboard progress bar should increase

---

#### Stage H — Stop the emulators

Once all stages pass, press `Ctrl+C` in the terminal running the emulators.

All test data is discarded — it never touched the real Firebase project.

---

### 3.8 Emulator troubleshooting table

| Problem | Solution |
|---------|----------|
| `ENOENT: functions/index.js not found` | Make sure you're running from the project root, not inside `/functions` |
| Functions don't start | Run `cd functions && npm install && cd ..` then retry |
| `Cannot connect to Firestore emulator` | Restart emulators; check no other process on port 8080 |
| Signup says permission-denied | The Firestore rules are rejecting the user doc. Re-check `isValidUserCreate` in `firestore.rules` |
| Admin panel shows no students | Make sure you're pointing at the emulator (localhost:5000), not prod |
| `auth/network-request-failed` | Usually means the page is trying to reach real Firebase instead of emulator. Hard-refresh the page. |

---

## Step 4 — Final Security Rules Verification

### What is this?

This is a final sanity check — same tool as Step 1 (Firebase Rules Playground)
but focused on the most critical attack vectors for a live system. Step 1 was
thorough; Step 4 is a rapid "last look" before you go live.

### Why run it again?

Between Step 1 and now, you may have edited `firestore.rules` (e.g. to add the
test comment block). This confirms nothing broke.

### 4.1 Three critical checks

Go to Firebase Console → Firestore → Rules → Rules Playground.

**Check 1: No privilege escalation**
- Sim type: `update`, Path: `/users/student123`, Auth UID: `student123`
- Data: `{ "role": "admin", "status": "approved" }`
- Expected: **DENY**
- If this passes (allows): stop immediately and do not deploy. The rules have
  a bug that lets students make themselves admin.

**Check 2: Enrollment isolation**
- Sim type: `get`, Path: `/enrollments/anyId`, Auth UID: `student123`
- Resource data: `{ "userId": "COMPLETELY_DIFFERENT_UID", "courseId": "foundation" }`
- Expected: **DENY**
- If this allows: students can see each other's enrollment data.

**Check 3: Catch-all works**
- Sim type: `get`, Path: `/databases/(default)/documents/internalSecretData/doc1`
- Auth: ON, UID: `student123`
- Expected: **DENY**
- If this allows: there's a wildcard rule open somewhere.

All three should be DENY. If any unexpectedly ALLOWs, stop and report it — do
not proceed to deployment.

---

## Step 5 — Set Firebase Budget Alert

### What is this and why does it matter?

The Firebase project is on the **Blaze (pay-as-you-go)** plan, which is needed
for Cloud Functions. At ~40 students/month this costs essentially $0, but
without a budget alert, a bug or an unexpected traffic spike could generate
a bill you don't notice until the end of the month. A $1 alert gives you
immediate notification if anything goes wrong.

### 5.1 Steps

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Make sure the project selected in the top bar is **vaptic--lms**
   (click the project name in the top bar to switch if needed)
3. In the left sidebar, search for **"Billing"** and click it
4. Click **Budgets & Alerts** in the billing left sidebar
5. Click **Create Budget**
6. Fill in:
   - **Name:** `vaptic-lms-alert`
   - **Projects:** select `vaptic--lms`
   - **Services:** leave as "All services"
   - **Time period:** Monthly
   - **Budget amount:** `Specified amount` → `$1.00`
7. Click **Next**
8. Under **Alert thresholds** — you'll see preset thresholds at 50%, 90%, 100%.
   Keep them all. This means:
   - Alert at $0.50 spend
   - Alert at $0.90 spend
   - Alert at $1.00 spend
9. Under **Manage notifications** → add your email address under
   "Email recipients"
10. Click **Finish**

You should see the new budget appear in the list.

**What happens if you exceed the budget?**
Google does NOT automatically shut down your project. The alert is just an
email. At this scale, a $1 bill means something is very wrong (a runaway
function loop, for example). If you get the alert, go to Firebase Console →
Functions → check the logs for unusual activity.

---

## Step 6 — Deploy to Firebase Hosting

### What is this?

This pushes your code to Firebase's CDN (Content Delivery Network). After this,
`https://vaptic--lms.web.app` (and any custom domain you've configured) will
serve the latest version of the app to your students.

### What gets deployed

From `firebase.json`:
- **Hosting:** all files in the project root (`.`) except those in the `ignore`
  list (node_modules, functions/, docs/, markdown files, etc.)
- **Firestore rules:** `firestore.rules`
- **Storage rules:** `storage.rules`
- **Cloud Functions:** everything in `functions/`

### 6.1 Pre-deployment checklist

Before running the deploy command, verify:

```bash
# 1. Are you in the right directory?
pwd
# Expected output: /home/jason/vaptic-lms

# 2. Is .firebaserc present?
cat .firebaserc
# Expected: { "projects": { "default": "vaptic--lms" } }

# 3. Is functions/.env present with real values?
cat functions/.env
# Expected: two lines with RESEND_API_KEY and ADMIN_EMAIL

# 4. Are function dependencies installed?
ls functions/node_modules | head -5
# Expected: several package names

# 5. Is Firebase CLI logged in?
firebase projects:list
# Expected: a table showing vaptic--lms in the list
```

If any of the above fail, fix them before continuing:
- Missing `.firebaserc` → go back to Step 3.2
- Missing `functions/.env` → go back to Step 3.3
- Missing `node_modules` → run `cd functions && npm install && cd ..`
- Not logged in → run `firebase login`

---

### 6.2 Deploy

```bash
firebase deploy
```

This deploys everything: hosting, functions, rules.

You will see output progressing through several stages:
```
=== Deploying to 'vaptic--lms'...

i  deploying firestore, storage, functions, hosting
i  firestore: checking firestore.rules for compilation errors...
✔  firestore: rules file firestore.rules compiled successfully
i  storage: checking storage.rules for compilation errors...
✔  storage: rules compiled successfully
i  functions: preparing functions directory for uploading...
✔  functions[onUserCreate]: Successful create operation.
✔  functions[notifyAdminOnSignup]: Successful create operation.
✔  functions[notifyStudentOnApproval]: Successful create operation.
✔  functions[enrollStudent]: Successful create operation.
✔  functions[unlockModule]: Successful create operation.
✔  functions[generateCertificate]: Successful create operation.
i  hosting[vaptic--lms]: beginning deploy...
✔  hosting[vaptic--lms]: 12 files uploaded successfully

✔  Deploy complete!

Project Console: https://console.firebase.google.com/project/vaptic--lms
Hosting URL: https://vaptic--lms.web.app
```

**Typical time:** 3–8 minutes depending on your internet speed.

---

### 6.3 If deployment fails

**Error: "Functions deploy had errors"**
```
Error: There was an error deploying functions
```
- Run `firebase functions:log` to see what failed
- Most common cause: syntax error in a function file
- Check that `functions/index.js` and all subdirectory `index.js` files are
  valid (no stray characters)

**Error: "Billing account not configured"**
```
Error: HTTP Error: 400, Billing account for project is not set
```
- Go to Firebase Console → click the spark/flame icon → Upgrade to Blaze
- Cloud Functions require Blaze plan even at $0 usage

**Error: "Rules compilation failed"**
```
Error: Failed to compile Firestore rules
```
- There's a syntax error in `firestore.rules`
- Run: `firebase firestore:rules --dry-run` to see the exact line

**Error: "Permission denied on hosting upload"**
- Run `firebase login --reauth` to refresh your credentials

**Error: "Project not found"**
- Run `firebase projects:list` to see available projects
- Make sure `.firebaserc` has the correct project ID `vaptic--lms`

---

### 6.4 Post-deployment verification

After a successful deploy, verify the production site:

#### Check 1: Pages load

Open in an Incognito window (so there's no cached session):
- `https://vaptic--lms.web.app/login.html` → should load the login page
- `https://vaptic--lms.web.app/signup.html` → should load the signup page

#### Check 2: Security headers are present

In Chrome: open the login page → F12 → **Network** tab → click on the
`login.html` request → click **Headers** tab → scroll to **Response Headers**.

You should see:
```
content-security-policy: default-src 'self'; ...
strict-transport-security: max-age=31536000; includeSubDomains
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: strict-origin-when-cross-origin
permissions-policy: camera=(), microphone=(), geolocation=()
```

If any of these are missing: the `firebase.json` headers were not deployed.
Re-run `firebase deploy --only hosting` and check again.

#### Check 3: Console is clean

On the login page, open F12 → Console. Should be empty (no red errors).
If you see a CSP violation, note the blocked URL and add it to the `firebase.json`
`Content-Security-Policy` header value, then redeploy with:
```bash
firebase deploy --only hosting
```

#### Check 4: Functions are live

Go to Firebase Console → Functions. You should see 6 functions listed:
- `onUserCreate`
- `notifyAdminOnSignup`
- `notifyStudentOnApproval`
- `enrollStudent`
- `unlockModule`
- `generateCertificate`

All should have a green status indicator.

#### Check 5: Test a real signup

1. On the live site, go to `signup.html` and create a test account
2. Log in to Firebase Console → Authentication → you should see the new user
3. Firebase Console → Firestore → `users` → you should see their document
4. Check your admin email inbox for the "New Student Signup" notification
   (if this email doesn't arrive within 2 minutes, check Functions logs
   for errors from `notifyAdminOnSignup`)

---

### 6.5 You're live

The app is deployed. Share the URL with students:
```
https://vaptic--lms.web.app
```

Or your custom domain if you've configured one in Firebase Console → Hosting →
Add Custom Domain.

---

## Appendix — Deploy only part of the app

You don't have to redeploy everything every time. Use these targeted commands:

| What changed | Deploy command |
|---|---|
| HTML/CSS/JS files only | `firebase deploy --only hosting` |
| Firestore rules only | `firebase deploy --only firestore:rules` |
| Storage rules only | `firebase deploy --only storage` |
| Cloud Functions only | `firebase deploy --only functions` |
| Specific function | `firebase deploy --only functions:enrollStudent` |
| Everything | `firebase deploy` |

---

## Appendix — Checking function logs after go-live

```bash
# See all recent function logs
firebase functions:log

# See logs for a specific function
firebase functions:log --only enrollStudent

# Stream logs live (like tail -f)
firebase functions:log --follow
```

---

*Guide written for VAPTIC LMS — project vaptic--lms — March 2026*

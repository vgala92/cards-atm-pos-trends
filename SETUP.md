# Auto-updating RBI ATM/POS/Card Dashboard — Setup (one time, ~10 minutes)

A free GitHub robot checks RBI's **Bankwise ATM/POS/Card Statistics** page a few times a day,
downloads any new month (or a re-issued "Revised" month), rebuilds the dashboard, and
republishes it to a public link. No computer of yours needs to be on.

You do this setup **once**. It's the same as the NFS dashboard — if you've done that, this is identical.

---

## Files in this folder

| File | Purpose |
|------|---------|
| `index.html` | The dashboard your team opens. |
| `build_dashboard.py` | Scrapes the RBI ATM page → downloads months → rebuilds the dashboard. |
| `requirements.txt` | Tools the script needs. |
| `.github/workflows/update.yml` | The schedule + failure email. |

Keep the structure exactly as-is (especially the `.github/workflows` folder).

---

## Steps

1. **Create a repository** at <https://github.com> → **New repository** → name e.g. `atm-dashboard` → **Public** → Create.
2. **Upload the files**: on the repo page → **Add file → Upload files** → drag in everything from this
   folder (including the `.github` folder) → **Commit changes**.
   - ⚠️ If the **Actions** tab later shows no workflow, the `.github` folder didn't upload. Add it by hand:
     **Add file → Create new file**, name it exactly `.github/workflows/update.yml`, paste the contents of
     that file, and commit.
3. **Permissions**: **Settings → Actions → General → Workflow permissions → Read and write permissions → Save.**
   (Needed so the robot can publish updates and post a failure alert.)
4. **Public link**: **Settings → Pages → Deploy from a branch → main → / (root) → Save.**
   Your link appears at the top: `https://YOUR-USERNAME.github.io/atm-dashboard/`. Share it with the team.
5. **Test now**: **Actions → Update RBI ATM dashboard → Run workflow.** Green ✓ = it scraped RBI,
   pulled the months, and published. This first run also **backfills history** — it grabs every month
   currently listed on the RBI page (about 10 months), so your trends fill out immediately.

---

## Schedule

Runs **3 times a day** (cron `23 4,10,16 * * *` → ~09:53, 15:53, 21:53 IST). Since the report is
monthly, that's plenty to catch a new month or a revision quickly. The **no-change guard** means
runs that find nothing new make no commit, so your history stays clean (≈ one commit per new/revised
month). To change frequency, edit the `cron` line. Need it now? **Actions → Run workflow.**

## How the data grows

The RBI page only lists the ~10 most recent months. The robot **merges** newly scraped months into
the data already in `index.html`, so older months are **retained** even after they drop off the page —
your history keeps growing over time. Re-issued **"Revised"** months overwrite the earlier version
automatically.

## Failure alerts (email)

If a run fails (e.g. RBI blocks the download or changes the page), the workflow opens a GitHub issue
titled "⚠️ RBI ATM auto-update failed" with a link to the run — GitHub emails you about it, and it
**closes automatically** on the next successful run. No passwords/SMTP needed.

## If the robot can't download

RBI's document server has bot protection. The script tries a normal download first, then falls back to
a full headless browser (Playwright) that clears the challenge. If a cloud run is ever blocked, re-run
it, or update manually: download the monthly XLSX from
<https://rbi.org.in/Scripts/ATMView.aspx>, open the live dashboard, use **Update Data → Upload RBI File**,
then **⤓ Publish** and re-upload `index.html` to the repo.

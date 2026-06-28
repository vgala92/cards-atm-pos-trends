# RBI ATM / POS / Card Dashboard — Setup & Reference

A free GitHub robot checks RBI's **Bankwise ATM/POS/Card Statistics** page a few times a day,
downloads any new month (or a re-issued "Revised" month), rebuilds the dashboard, and republishes it
to a public link. No computer of yours needs to stay on. You do the setup **once**.

---

## What the dashboard shows

Bank-wise RBI ATM/POS/Card data, with a **Metric** picker and a **Scope** picker (System total /
bank group / individual bank) driving five tabs:

- **Cash · ATMs** — ATMs (on/off-site), Micro ATMs, ATM cash withdrawals (volume & value).
- **Digital · PoS & Cards** — PoS terminals, QR codes, card spends (PoS / online / total).
- **Card Base & Productivity** — credit/debit cards outstanding, plus ratios: avg txns per card / per
  ATM / per PoS, and avg spend per card / per PoS.
- **Compare** — compare several months *or* several banks side by side (% vs a baseline).
- **YoY Growth** — year-on-year growth with a **Month + As-of-year picker**: YoY % over time, the
  chosen month across all years, multi-year **CAGR**, and a "top banks by YoY growth" leaderboard.

Every theme tab also has a stacked-by-group trend, a **market-composition donut**, a **bank
leaderboard** (with a minimum-size filter), and **Top gainers / decliners** tiles — all of which
follow the Scope selection.

**Exports:** every chart has **⤓ PNG** (image) and **⤓ Data** (the chart's data as CSV); every table
has **⤓ CSV**; and a header **⤓ Data CSV** button downloads the full bank-wise dataset (all months ×
all banks × all fields). Values shown in ₹ Crore; the dashboard also works offline and installs to a
phone home screen.

---

## Files in this folder

| File | Purpose |
|------|---------|
| `index.html` | The dashboard your team opens (data is baked in). |
| `build_dashboard.py` | Daily job: scrape the RBI ATM page → download new/revised months → rebuild. |
| `backfill.py` | One-off: pull historical months from RBI's archive (era-aware; handles the pre-2022 layout). |
| `requirements.txt` | Tools the scripts need. |
| `.github/workflows/update.yml` | The daily schedule + failure email. |
| `.github/workflows/backfill.yml` | The manual "pull history" workflow. |

Keep the folder structure exactly as-is (especially the `.github/workflows` folder).

---

## One-time setup

1. **Create a repository** at <https://github.com> → **New repository** → name e.g. `cards-atm-pos-trends`
   → **Public** → Create.
2. **Upload the files**: repo page → **Add file → Upload files** → drag in everything from this folder
   (including the `.github` folder) → **Commit changes**.
   - `index.html` is ~1 MB — that's fine for drag-and-drop *upload* (don't try to paste it).
   - ⚠️ If the **Actions** tab later shows no workflows, the `.github` folder didn't upload. Add each
     by hand: **Add file → Create new file**, name it exactly `.github/workflows/update.yml`
     (then again for `backfill.yml`), paste the contents, and commit.
3. **Permissions**: **Settings → Actions → General → Workflow permissions → Read and write permissions
   → Save.** (Needed so the robot can publish updates and post failure alerts.)
4. **Public link**: **Settings → Pages → Deploy from a branch → main → / (root) → Save.** After ~1 min
   your link appears at the top: `https://YOUR-USERNAME.github.io/<repo>/`. Share it with the team
   (it also installs to a phone home screen).
5. **Test now**: **Actions → Update RBI ATM dashboard → Run workflow** → wait for green ✓.

---

## Load the full history (run once)

The daily job only sees the ~10 months currently listed on the RBI page. To pull older months:

- **Actions → Backfill ATM history (one-off) → Run workflow** (leave the defaults).

It walks RBI's archive, downloads each month, and **merges** them in. It understands **both** the
current layout and the **older pre-2022 layout** (different columns, values in ₹ Lakh) and converts
them onto the same footing; any month in an unrecognised layout is skipped and listed in the log. The
run's **BACKFILL SUMMARY** tells you the earliest month reached. After this, the daily job keeps
everything current.

---

## Schedule

The daily job runs **3 times a day** (cron `23 4,10,16 * * *` → ~09:53, 15:53, 21:53 IST). Since the
report is monthly, that's plenty to catch a new month or a revision quickly. A **no-change guard**
means runs that find nothing new make no commit, so history stays clean (≈ one commit per new/revised
month). To change frequency, edit the `cron` line. Need it now? **Actions → Run workflow.**

## How the data grows

The robot **merges** newly scraped months into the data already in `index.html`, so older months are
**retained** even after they drop off the RBI page. Re-issued **"Revised"** months overwrite the
earlier version automatically.

## Failure alerts (email)

If a run fails (RBI blocks the download or changes the page), the workflow opens a GitHub issue titled
"⚠️ RBI ATM auto-update failed" with a link to the run — GitHub emails you about it, and it **closes
automatically** on the next successful run. No passwords / SMTP needed.

## Updating the dashboard's features later

When the dashboard's *code* changes (new chart, new export, a fix), replace the files in the repo and
re-run the backfill once:

1. **Add file → Upload files** → drag in the updated `index.html`, `build_dashboard.py`, and
   `backfill.py` → Commit.
2. **Actions → Backfill ATM history → Run workflow.** This re-fills the full history into the new
   `index.html`, so you keep all your months *and* get the new features in one go.

## If the robot can't download

RBI's document server has bot protection. The scripts try a normal download first, then fall back to a
full headless browser (Playwright) that clears the challenge. If a cloud run is ever blocked, just
re-run it (challenges are often intermittent). As a manual fallback: download the monthly XLSX from
<https://rbi.org.in/Scripts/ATMView.aspx>, open the live dashboard, use **Update Data → Upload RBI
File**, then **⤓ Publish** and re-upload `index.html` to the repo.

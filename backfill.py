#!/usr/bin/env python3
"""ONE-OFF history backfill for the ATM/POS/Card dashboard — ERA-AWARE (handles old + new RBI layouts)."""
import os, io, re, time, datetime
import build_dashboard as B  # read_embedded, splice, month_sort_key, DOC_RE, LIST_URL, UA, HTML_PATH, SCHEMA

START = int(os.environ.get("START_ATMID", "40"))
END   = int(os.environ.get("END_ATMID", "190"))
START_YEAR = int(os.environ.get("START_YEAR", "2017"))

MAB={'january':'Jan','february':'Feb','march':'Mar','april':'Apr','may':'May','june':'Jun','july':'Jul',
     'august':'Aug','september':'Sep','october':'Oct','november':'Nov','december':'Dec'}
GROUPS={"public sector banks":"Public Sector","private sector banks":"Private Sector",
        "foreign banks":"Foreign","payment banks":"Payments","payments banks":"Payments",
        "small finance banks":"Small Finance"}

_BANK_ALIAS={"CITY UNION BANK":"CITY UNION BANK LTD","IDBI LTD":"IDBI BANK LTD",
             "JAMMU AND KASHMIR BANK":"JAMMU AND KASHMIR BANK LTD","SBM BANK INDIA":"SBM BANK INDIA LTD",
             "BANDHAN BANK":"BANDHAN BANK LTD"}
def canon_bank(name):
    s=re.sub(r"\s+"," ",str(name).strip())
    u=re.sub(r"\.","",s.upper())
    u=re.sub(r"\bLIMITED\b","LTD",u)
    u=re.sub(r"\s+"," ",u).strip()
    return _BANK_ALIAS.get(u,u)

def _num(x):
    if x is None: return 0
    if isinstance(x,(int,float)): return x
    s=str(x).strip().replace(",","")
    if s=="" or s=="-": return 0
    try: return float(s)
    except Exception: return 0

def _parse_new(rows):
    banks={}; total=None; cur=None; groups={}
    for r in rows:
        c1=r[1] if len(r)>1 else None; c2=r[2] if len(r)>2 else None
        if c1 is None and c2 is None: continue
        s1=str(c1).strip() if c1 is not None else ""
        if s1.lower()=="total" or (c2 is not None and str(c2).strip().lower()=="total"):
            total=[round(_num(r[c]),3) if c<len(r) else 0 for c in range(3,29)]; continue
        if c2 is None or str(c2).strip()=="":
            g=GROUPS.get(s1.lower())
            if g: cur=g
            continue
        name=str(c2).strip()
        if not name or name.lower()=="bank name": continue
        name=canon_bank(name)
        banks[name]=[round(_num(r[c]),3) if c<len(r) else 0 for c in range(3,29)]
        groups[name]=cur or "Other"
    return banks, total, groups

def _old_row(r):
    def g(i): return _num(r[i]) if i<len(r) else 0
    return [round(x,3) for x in [
        g(2), g(3), g(4)+g(5), g(6), g(7), 0, g(8), g(13),
        g(10), g(12)*100, 0,0, 0,0, g(9), g(11)*100,
        g(15), g(17)*100, 0,0, 0,0, g(14), g(16)*100, 0,0]]

def _parse_old(rows):
    banks={}; total=None; cur=None; groups={}
    for r in rows:
        c1=r[1] if len(r)>1 else None; c2=r[2] if len(r)>2 else None
        if c1 is None: continue
        s1=str(c1).strip()
        if s1.lower()=="total" or (c2 is not None and str(c2).strip().lower()=="total"):
            total=_old_row(r); continue
        if c2 is None or str(c2).strip()=="":
            g=GROUPS.get(s1.lower())
            if g: cur=g
            continue
        if not isinstance(c2,(int,float)): continue
        if s1.lower()=="bank name": continue
        nm=canon_bank(s1)
        banks[nm]=_old_row(r); groups[nm]=cur or "Other"
    return banks, total, groups

# ---- OLDEST era (2017 -> early 2020): Sr.No in col1, Bank in col2, NO Micro-ATM /
# Bharat QR / UPI QR columns; amounts in Rupees Lakh (x100 -> Rs'000). Flat bank list
# with a numbered legend block + a "Note-" row at the bottom that must be ignored.
def _oldest_row(r, amul):
    # amul = multiplier that converts this file's amount unit to Rs'000
    #   "(Rs. Millions)"  -> x1000     "(Lakh)" -> x100   (RBI switched units mid-2019)
    def g(i): return _num(r[i]) if i<len(r) else 0
    return [round(x,3) for x in [
        g(3), g(4), g(5)+g(6), 0, 0, 0, g(7), g(12),               # atm_on,atm_off,pos,micro,bqr,upi,cc_out,dc_out
        g(9), g(11)*amul, 0,0, 0,0, g(8), g(10)*amul,              # cc_pos v/val, cc_online, cc_other, cc_atm v/val
        g(14), g(16)*amul, 0,0, 0,0, g(13), g(15)*amul, 0,0]]      # dc_pos v/val, dc_online, dc_other, dc_atm v/val, dc_poscw

def _oldest_amul(rows):
    txt=" ".join(str(c) for r in rows[:6] for c in (r or []) if c is not None).lower()
    if "million" in txt: return 1000.0
    if "lakh"    in txt: return 100.0
    return 1000.0   # oldest unlabelled files are Millions

# Legacy groups for banks that existed only in the oldest era (mostly PSBs later merged).
_LEGACY_GROUP={
 "ALLAHABAD BANK":"Public Sector","ANDHRA BANK":"Public Sector","CORPORATION BANK":"Public Sector",
 "DENA BANK":"Public Sector","VIJAYA BANK":"Public Sector","SYNDICATE BANK":"Public Sector",
 "ORIENTAL BANK OF COMMERCE":"Public Sector","UNITED BANK OF INDIA":"Public Sector",
 "STATE BANK OF BIKANER AND JAIPUR":"Public Sector","STATE BANK OF HYDERABAD":"Public Sector",
 "STATE BANK OF MYSORE":"Public Sector","STATE BANK OF PATIALA":"Public Sector",
 "STATE BANK OF TRAVANCORE":"Public Sector","BHARATIYA MAHILA BANK":"Public Sector",
 "IDBI BANK LTD":"Public Sector","THE LAKSHMI VILAS BANK LTD":"Private Sector",
 "THE LAXMI VILAS BANK LTD":"Private Sector","LAKSHMI VILAS BANK":"Private Sector",
 "CATHOLIC SYRIAN BANK LTD":"Private Sector","DEVELOPMENT CREDIT BANK":"Private Sector",
 "IDFC BANK LTD":"Private Sector","RATNAKAR BANK LTD":"Private Sector","BANDHAN BANK LTD":"Private Sector",
 "AMERICAN EXPRESS":"Foreign","DBS BANK":"Foreign","FIRSTRAND BANK":"Foreign",
 "HONGKONG AND SHANGHAI BKG CORPN":"Foreign","ROYAL BANK OF SCOTLAND N V":"Foreign",
 "BANK OF AMERICA":"Foreign","BARCLAYS BANK PLC":"Foreign","CITI BANK":"Foreign",
 "DEUTSCHE BANK LTD":"Foreign","STANDARD CHARTERED BANK LTD":"Foreign",
}
def _oldest_group(nm):
    g=_LEGACY_GROUP.get(nm)
    if g: return g
    u=nm.upper()
    if "SMALL FINANCE" in u: return "Small Finance"
    if "PAYMENT" in u: return "Payments"
    return "Other"

def _parse_oldest(rows):
    banks={}; total=None; groups={}
    amul=_oldest_amul(rows)
    for r in rows:
        c1=r[1] if len(r)>1 else None; c2=r[2] if len(r)>2 else None
        s2=str(c2).strip() if c2 is not None else ""
        s1=str(c1).strip() if c1 is not None else ""
        # catches "Total" and "Grand Total" (2017 files); no bank name contains "total"
        if "total" in s2.lower() or "total" in s1.lower():
            total=_oldest_row(r, amul); continue
        if not s2 or s2.lower()=="bank name": continue
        # real bank rows carry numeric values in cols 3..16; legend/footnote rows do not
        if not any(isinstance(r[j],(int,float)) for j in range(3,17) if j<len(r)):
            continue
        nm=canon_bank(s2)
        if nm.lower() in GROUPS: continue          # skip a group header if one ever appears
        banks[nm]=_oldest_row(r, amul); groups[nm]=_oldest_group(nm)
    return banks, total, groups

def detect_format(rows):
    txt=" ".join(str(c) for r in rows[:8] for c in (r or []) if c is not None)
    if "UPI QR" in txt: return "new"
    has_micro = ("Micro" in txt) or ("MICRO" in txt)
    has_bharat = "Bharat" in txt
    has_online = ("On-line" in txt) or ("On- line" in txt) or ("Off-line" in txt)
    if has_online and not has_micro and not has_bharat:
        return "oldest"
    if ("Rupees Lakh" in txt) or has_online:
        return "old"
    if "Sr. No" in txt or "Sr.No" in txt: return "new"
    return None

_MON3={'jan':'Jan','feb':'Feb','mar':'Mar','apr':'Apr','may':'May','jun':'Jun','jul':'Jul',
       'aug':'Aug','sep':'Sep','oct':'Oct','nov':'Nov','dec':'Dec'}
def month_from_name(sn):
    # tolerant of "Month YYYY", "Month-YYYY", "Month - YYYY", "Month YY", RBI typos ("Novmber")
    for m in re.finditer(r"([A-Za-z]{3,})\s*[-–]?\s*(\d{2,4})", str(sn)):
        p=m.group(1)[:3].lower()
        if p in _MON3:
            y=int(m.group(2)); y=2000+y if y<100 else y
            if 2000<=y<=2100: return f"{_MON3[p]} {y}"
    return None

def parse_any(b):
    import openpyxl
    wb=openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    sn=wb.sheetnames[0]
    rows=list(wb[sn].iter_rows(values_only=True))
    mk=month_from_name(sn)
    if not mk:
        # fall back to the in-sheet title, e.g. "ATM & Card Statistics for February 2017"
        title=" ".join(str(c) for r in rows[:4] for c in (r or []) if c is not None)
        mk=month_from_name(title)
    if not mk: return None
    fmt=detect_format(rows)
    if fmt=="new": banks,total,groups=_parse_new(rows)
    elif fmt=="old": banks,total,groups=_parse_old(rows)
    elif fmt=="oldest": banks,total,groups=_parse_oldest(rows)
    else: return ("UNRECOGNISED", mk)
    if not banks: return ("UNRECOGNISED", mk)
    return mk, {"rows":banks,"total":total}, groups

def main():
    from playwright.sync_api import sync_playwright
    html=open(B.HTML_PATH, encoding="utf-8").read()
    cur=B.read_embedded(html); months=dict(cur.get("months",{})); groups=dict(cur.get("groups",{}))
    before_n=len(months)
    links=set()
    with sync_playwright() as p:
        br=p.chromium.launch(args=["--no-sandbox"]); ctx=br.new_context(user_agent=B.UA); pg=ctx.new_page()
        pg.goto(B.LIST_URL, wait_until="domcontentloaded", timeout=90000); pg.wait_for_timeout(2500)
        links |= set(B.DOC_RE.findall(pg.content()))
        for N in range(END, START-1, -1):
            try:
                pg.goto(B.LIST_URL+"?atmid=%d"%N, wait_until="domcontentloaded", timeout=45000)
                links |= set(B.DOC_RE.findall(pg.content()))
            except Exception as e:
                print("  atmid", N, "skipped:", e)
        print("Collected %d unique monthly file link(s)." % len(links))
        files={}
        for u in sorted(links):
            try:
                r=ctx.request.get(u, headers={"Referer":B.LIST_URL}, timeout=90000); b=r.body()
                if b[:2]==b"PK": files[u]=b
            except Exception as e:
                print("  download failed:", u[-34:], e)
        br.close()
    added=0; skipped=[]
    for u,b in files.items():
        try:
            res=parse_any(b)
            if not res: continue
            if res[0]=="UNRECOGNISED":
                skipped.append(res[1]); continue
            mk,md,g=res
            if int(mk.split()[1])<START_YEAR: continue
            months[mk]=md; groups.update(g); added+=1
        except Exception as e:
            print("  parse error:", e)
    order=sorted(months, key=B.month_sort_key)
    payload={"version":1,"exportedAt":datetime.datetime.utcnow().isoformat()+"Z",
             "source":"RBI Bankwise ATM/POS/Card Statistics","schema":cur.get("schema",B.SCHEMA),
             "valueUnit":"Rs'000","groups":groups,"monthOrder":order,"months":months}
    html=B.splice(html, payload, int(time.time()*1000), order[-1] if order else "")
    open(B.HTML_PATH,"w",encoding="utf-8").write(html)
    print("\n==== BACKFILL SUMMARY ====")
    print("Downloaded files       :", len(files))
    print("Months ingested        :", added)
    if skipped:
        sk=sorted(set(x for x in skipped if x))
        print("Skipped (unrecognised) :", len(sk), "->", ", ".join(sk[:24]) + (" …" if len(sk)>24 else ""))
    print("Dashboard now has %d month(s): %s -> %s" % (len(order), order[0] if order else "-", order[-1] if order else "-"))
    print("Was %d before backfill." % before_n)

if __name__ == "__main__":
    main()

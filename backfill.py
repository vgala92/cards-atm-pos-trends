#!/usr/bin/env python3
"""One-off history backfill for the ATM/POS/Card dashboard (see SETUP/notes)."""
import os, io, time, datetime, re
import build_dashboard as B  # reuse parse_bytes, read_embedded, splice, month_sort_key, DOC_RE, LIST_URL, UA, HTML_PATH, SCHEMA

START = int(os.environ.get("START_ATMID", "40"))
END   = int(os.environ.get("END_ATMID", "190"))
START_YEAR = int(os.environ.get("START_YEAR", "2017"))

MAB={'january':'Jan','february':'Feb','march':'Mar','april':'Apr','may':'May','june':'Jun','july':'Jul',
     'august':'Aug','september':'Sep','october':'Oct','november':'Nov','december':'Dec'}

def sheet_month(b):
    import openpyxl
    wb=openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    sn=wb.sheetnames[0]; m=re.search(r"([A-Za-z]+)\s+(\d{4})", sn)
    if not m: return None
    mon=MAB.get(m.group(1).lower()); return f"{mon} {m.group(2)}" if mon else None

def current_format(b):
    import openpyxl
    wb=openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    ws=wb[wb.sheetnames[0]]; txt=[]
    for i,r in enumerate(ws.iter_rows(values_only=True)):
        txt.append(' '.join(str(c) for c in r if c is not None))
        if i>8: break
    t=' '.join(txt)
    return ('UPI QR' in t) and ('PoS' in t) and ('ATM' in t)

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
            mk=sheet_month(b)
            if mk and int(mk.split()[1])<START_YEAR: continue
            if not current_format(b):
                skipped.append(mk or u[-30:]); continue
            res=B.parse_bytes(b)
            if not res: continue
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
    print("Months ingested (new+refreshed):", added)
    if skipped:
        sk=sorted(set(x for x in skipped if x))
        print("Skipped (older format) :", len(sk), "->", ", ".join(sk[:24]) + (" …" if len(sk)>24 else ""))
    print("Dashboard now has %d month(s): %s -> %s" % (len(order), order[0] if order else "-", order[-1] if order else "-"))
    print("Was %d before backfill." % before_n)

if __name__ == "__main__":
    main()

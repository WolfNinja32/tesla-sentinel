#!/usr/bin/env python3
import json, sys, pathlib, datetime
from collections import OrderedDict

def load(p):
    if not pathlib.Path(p).exists(): return None
    return json.load(open(p))

def md_table(rows):
    cols = ["Time (PT)","Headline","Verification","Sources","Market Impact","Update/New","Notes","System"]
    out = ["| " + " | ".join(cols) + " |","|" + "|".join(["---"]*len(cols)) + "|"]
    for r in rows:
        sources = ", ".join(r.get("sources", [])[:4])
        mk = r.get("market", {})
        price = mk.get('price', '?')
        pct = mk.get('pct_change', '?')
        vol = mk.get('volume_rel_30d', '?')
        mi = f"${price} / {pct}% / {vol}×"
        out.append("| " + " | ".join([
            r.get("time_pt",""),
            r.get("headline",""),
            r.get("verification",""),
            sources,
            mi,
            r.get("update_new",""),
            r.get("notes",""),
            r.get("system","")
        ]) + " |")
    return "\n".join(out)

def main(day):
    base = pathlib.Path("data")/day
    chat = load(base/"chatgpt.json")
    grok = load(base/"grok.json")
    rows = []
    for sysname, blob in [("ChatGPT",chat),("Grok",grok)]:
        if not blob: continue
        for a in blob.get("alerts",[]):
            a["system"]=sysname
            rows.append(a)
    rows.sort(key=lambda r: r.get("time_pt","00:00"))
    report = f"# Tesla Market Sentinel – Daily Comparison\n**Date:** {day}\n\n"
    if not rows:
        report += "_No data ingested yet._\n"
    else:
        report += md_table(rows) + "\n\n"
        ch_h = {a["headline"] for a in rows if a["system"]=="ChatGPT"}
        gr_h = {a["headline"] for a in rows if a["system"]=="Grok"}
        overlap = len(ch_h & gr_h)
        uniq_chat = len(ch_h - gr_h)
        uniq_grok = len(gr_h - ch_h)
        report += "## Quick Analysis\n"
        report += f"- Overlap (same headlines): **{overlap}**\n"
        report += f"- Unique to ChatGPT: **{uniq_chat}**\n"
        report += f"- Unique to Grok: **{uniq_grok}**\n"

    outdir = pathlib.Path("out")
    outdir.mkdir(exist_ok=True, parents=True)
    (outdir/f"{day}-report.md").write_text(report)
    (outdir/"latest.md").write_text(report)
    print(f"Wrote out/{day}-report.md and out/latest.md")

if __name__=="__main__":
    day = sys.argv[1] if len(sys.argv)>1 else datetime.date.today().isoformat()
    main(day)

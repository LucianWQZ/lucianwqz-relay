#!/usr/bin/env python3
import argparse, hashlib, json, sys, zipfile
from pathlib import Path, PurePosixPath
def h(p):
 d=hashlib.sha256()
 with p.open("rb") as f:
  while b:=f.read(8*1024*1024): d.update(b)
 return d.hexdigest()
ap=argparse.ArgumentParser(); ap.add_argument("--archive",type=Path); ap.add_argument("--manifest",type=Path); ap.add_argument("--root",type=Path); a=ap.parse_args()
errors=[]
if a.archive:
 m=json.loads(a.manifest.read_text()) if a.manifest else None
 if m:
  item=next((x for x in m["packages"] if x["filename"]==a.archive.name),None)
  if not item or a.archive.stat().st_size!=item["bytes"] or h(a.archive)!=item["sha256"]: errors.append("archive identity mismatch")
 with zipfile.ZipFile(a.archive) as z:
  for i in z.infolist():
   p=PurePosixPath(i.filename)
   if p.is_absolute() or ".." in p.parts: errors.append("unsafe member: "+i.filename)
  bad=z.testzip()
  if bad: errors.append("CRC failure: "+bad)
if a.root:
 sums=a.root/"SHA256SUMS"
 for line in sums.read_text().splitlines():
  digest,rel=line.split("  ",1); p=a.root/rel
  if not p.is_file() or h(p)!=digest: errors.append("file mismatch: "+rel)
print(json.dumps({"status":"PASS" if not errors else "FAIL","errors":errors},ensure_ascii=False,indent=2))
sys.exit(0 if not errors else 1)

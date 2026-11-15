import json, sys
src = sys.argv[1]; out = sys.argv[2]
def fix(s):
    if not isinstance(s, str): return s
    try: return s.encode('cp1252').decode('utf-8')
    except Exception: return s
d = json.load(open(src, encoding='utf-8'))
keep = ['id','origin','title','authors','year','venue','doi','url','summary','use','limits']
json.dump([{k: fix(r.get(k)) for k in keep} for r in d], open(out,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(d),'references')

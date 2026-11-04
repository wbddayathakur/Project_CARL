import re,json,sys
p="legacy/carl-legacy-source-master/looker-inventory-analytics/models/eg_order_management.model.lkml"
lines=open(p,encoding="utf-8",errors="replace").read().split("\n")
# explore range
start=7; end=2394
out=[]
i=start
while i<end:
    m=re.match(r'^\s*join:\s*(\w+)\s*\{',lines[i])
    if m:
        depth=0;j=i;blk=[]
        while j<len(lines):
            l=lines[j]; c=re.sub(r'#.*$','',l) if ';;' not in l else l
            depth+=c.count('{')-c.count('}'); blk.append(l); j+=1
            if depth<=0:break
        b="\n".join(blk)
        frm=re.search(r'\bfrom:\s*(\w+)',b); so=re.search(r'sql_on:\s*(.*?);;',b,re.S); f=re.search(r'\bfields:\s*\[(.*?)\]',b,re.S)
        ty=re.search(r'\btype:\s*(\w+)',b); vl=re.search(r'view_label:\s*"([^"]*)"',b)
        out.append(dict(join=m.group(1),line=i+1,end=j,frm=frm.group(1) if frm else m.group(1),type=ty.group(1) if ty else None,view_label=vl.group(1) if vl else None,sql_on=re.sub(r'\s+',' ',so.group(1)).strip() if so else None,fields=re.sub(r'\s+',' ',f.group(1)).strip() if f else None))
        i=j
    else: i+=1
json.dump(out,open("explore_joins_op1.json","w"),indent=1)
print(len(out))
for o in out:
    if o["sql_on"] and re.search(r'custom_field_id',o["sql_on"]):
        print(o["line"],o["join"],"<-",o["frm"],"|",o["sql_on"][:260])

import re, json, sys
def parse(path):
    txt=open(path,encoding="utf-8",errors="replace").read()
    lines=txt.split("\n")
    # strip full-line comments for structure, but keep line numbers
    out=[]; i=0; n=len(lines)
    view=None
    m=re.search(r'^\s*view:\s*(\S+)\s*\{',txt,re.M)
    view=m.group(1) if m else None
    st=re.search(r'sql_table_name:\s*(.*?)\s*;;',txt,re.S)
    der=re.search(r'derived_table:\s*\{',txt)
    pat=re.compile(r'^\s*(dimension_group|dimension|measure|filter|parameter)\s*:\s*(\w+)\s*\{')
    i=0
    while i<n:
        mm=pat.match(lines[i])
        if mm:
            kind,name=mm.groups()
            depth=0; j=i; blk=[]
            while j<n:
                l=lines[j]
                code=re.sub(r'#.*$','',l) if not ';;' in l else l
                depth+=code.count('{')-code.count('}')
                blk.append(l)
                j+=1
                if depth<=0: break
            body="\n".join(blk)
            def g(k):
                r=re.search(r'\b'+k+r':\s*"([^"]*)"',body)
                if r: return r.group(1)
                r=re.search(r'\b'+k+r':\s*([^\s;\[\{]+)',body)
                return r.group(1) if r else None
            sql=re.search(r'\bsql:\s*(.*?);;',body,re.S)
            out.append(dict(kind=kind,name=name,line_start=i+1,line_end=j,label=g("label"),group_label=g("group_label"),view_label=g("view_label"),type=g("type"),description=g("description"),hidden=g("hidden"),sql=(sql.group(1).strip() if sql else None),timeframes=(re.search(r'timeframes:\s*\[(.*?)\]',body,re.S).group(1).split() if 'timeframes' in body and re.search(r'timeframes:\s*\[(.*?)\]',body,re.S) else None)))
            i=j
        else: i+=1
    return dict(file=path,view=view,sql_table_name=(st.group(1).strip() if st else None),is_derived=bool(der),fields=out,loc=n)
if __name__=="__main__":
    r=parse(sys.argv[1]); print(json.dumps(r,indent=1)[:200000])

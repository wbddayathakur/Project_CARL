/* =============================================================================
   30-kit.js — shared surfaces.
   The grid is deliberately spreadsheet-shaped: column letters, row numbers, a
   name box, a formula strip, arrow-key navigation and CSV out. A planner
   arriving from Excel should recognise the surface before they read a label.
   ============================================================================= */
const { useState, useMemo, useEffect, useRef, useCallback, Fragment } = React;

/* ------------------------------------------------------------------- atoms */
const Chip = ({c="", children, title}) => <span className={"chip " + c} title={title}>{children}</span>;

const ProvChip = ({cls, small}) => {
  const p = PROV[cls]; if (!p) return null;
  return <span className={"chip " + p.cls} title={p.label}>{small ? p.short : p.label}</span>;
};

const Btn = ({c="", onClick, disabled, children, title, style}) =>
  <button className={"btn " + c} onClick={onClick} disabled={disabled} title={title} style={style}>{children}</button>;

const Card = ({title, right, children, tight, style, sub}) => (
  <div className="card" style={style}>
    {(title || right) && <div className="card-h">
      <div><h3>{title}</h3>{sub && <div className="mini dim" style={{marginTop:1}}>{sub}</div>}</div>
      <div className="sp"/>{right}
    </div>}
    <div className={"card-b" + (tight ? " tight" : "")}>{children}</div>
  </div>
);

const Stat = ({label, value, delta, tone}) => (
  <div className="stat">
    <div className="lb">{label}</div>
    <div className="vl" style={tone==="good"?{color:"var(--good)"}:tone==="bad"?{color:"var(--bad)"}:null}>{value}</div>
    {delta && <div className="dl">{delta}</div>}
  </div>
);

const Bar = ({v, c=""}) => <div className={"bar " + c}><i style={{width: clamp(v*100,0,100) + "%"}}/></div>;

const Seg = ({opts, value, onChange}) => (
  <div className="seg">{opts.map(o =>
    <button key={o.v} className={value===o.v?"on":""} onClick={()=>onChange(o.v)}>{o.l}</button>)}</div>
);

const Switch = ({on, onChange, label}) => (
  <button className="row" style={{gap:7}} onClick={()=>onChange(!on)}>
    <span className={"sw" + (on?" on":"")}><i/></span>
    {label && <span className="tiny">{label}</span>}
  </button>
);

const Modal = ({title, sub, onClose, children, footer, wide}) => (
  <div className="scrim" onMouseDown={e => { if (e.target === e.currentTarget) onClose && onClose(); }}>
    <div className={"modal" + (wide?" wide":"")}>
      <div className="modal-h">
        <div><h3>{title}</h3>{sub && <div className="mini dim" style={{marginTop:2}}>{sub}</div>}</div>
        <div style={{flex:1}}/>
        <Btn c="gho sm" onClick={onClose}>Close</Btn>
      </div>
      <div className="modal-b">{children}</div>
      {footer && <div className="modal-f">{footer}</div>}
    </div>
  </div>
);

const Drawer = ({title, sub, onClose, children, foot}) => (
  <>
    <div className="scrim" style={{background:"rgba(15,21,25,.28)"}} onMouseDown={onClose}/>
    <div className="drawer">
      <div className="drawer-h">
        <div style={{minWidth:0}}><h3 style={{fontSize:13.5}}>{title}</h3>{sub && <div className="mini dim">{sub}</div>}</div>
        <div style={{flex:1}}/><Btn c="gho sm" onClick={onClose}>Close</Btn>
      </div>
      <div className="drawer-b">{children}</div>
      {foot && <div className="modal-f">{foot}</div>}
    </div>
  </>
);

/* -------------------------------------------------------- justify-to-change */
/* T6: justify, then override. A change without a stated reason is not accepted.
   The reason travels forward into the plan brief and the approval package. */
const Justify = ({title, what, min=25, onCancel, onConfirm, verb="Record change", hints=[]}) => {
  const [t, setT] = useState("");
  const ok = t.trim().length >= min;
  return (
    <Modal title={title} sub="Every deviation from the system proposal carries a justification that travels forward (T6)." onClose={onCancel}
      footer={<>
        <div className="tiny dim">{ok ? "This reason will be attached to the strategy brief and the approval package."
          : `${min - t.trim().length} more characters. A reason P&I can read on its own.`}</div>
        <div style={{flex:1}}/>
        <Btn onClick={onCancel}>Cancel</Btn>
        <Btn c="pri" disabled={!ok} onClick={()=>onConfirm(t.trim())}>{verb}</Btn>
      </>}>
      <div className="banner b" style={{marginBottom:14}}><span className="bi">Change</span><div>{what}</div></div>
      <label className="lbl">Why</label>
      <textarea className="inp" autoFocus value={t} onChange={e=>setT(e.target.value)}
        placeholder="State what the system got wrong and why your change is right. This is what P&I will read." />
      {hints.length > 0 && <div style={{marginTop:10}}>
        <div className="lbl">Reasons used on this deal before</div>
        <div className="row wrap" style={{gap:6}}>
          {hints.map((h,i)=><button key={i} className="chip o" style={{cursor:"pointer"}} onClick={()=>setT(h)}>{h.slice(0,64)}…</button>)}
        </div>
      </div>}
    </Modal>
  );
};

/* ------------------------------------------------------------- toast system */
const ToastCtx = React.createContext(()=>{});
const useToast = () => React.useContext(ToastCtx);

/* ------------------------------------------------------ spreadsheet surface */
const COLLET = (i) => { let s=""; i++; while(i>0){ const m=(i-1)%26; s=String.fromCharCode(65+m)+s; i=Math.floor((i-1)/26);} return s; };

function toCSV(cols, rows){
  const esc = v => { const s = v == null ? "" : String(v); return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; };
  return [cols.map(c=>esc(c.label)).join(",")]
    .concat(rows.map(r => cols.map(c => esc(c.raw ? c.raw(r) : c.get(r))).join(",")))
    .join("\n");
}
function download(name, text, mime="text/csv"){
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], {type:mime}));
  a.download = name; a.click(); setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
}

/**
 * XL — the grid.
 * cols: [{ key, label, w, align:'r'|'c', get(row), raw(row), cell(row) , tone(row) }]
 */
const XL = ({name="Sheet1", cols, rows, total, height=540, onRowClick, rowTone, sub, actions, dense}) => {
  const [sel, setSel] = useState({r:0, c:0});
  const wrapRef = useRef(null);
  const toast = useToast();

  const onKey = useCallback((e) => {
    const k = e.key;
    if (!["ArrowUp","ArrowDown","ArrowLeft","ArrowRight","Home","End"].includes(k)) return;
    e.preventDefault();
    setSel(s => {
      let {r,c} = s;
      if (k==="ArrowUp") r = Math.max(0, r-1);
      if (k==="ArrowDown") r = Math.min(rows.length-1, r+1);
      if (k==="ArrowLeft") c = Math.max(0, c-1);
      if (k==="ArrowRight") c = Math.min(cols.length-1, c+1);
      if (k==="Home") c = 0;
      if (k==="End") c = cols.length-1;
      return {r,c};
    });
  }, [rows.length, cols.length]);

  const selRow = rows[sel.r], selCol = cols[sel.c];
  const fx = selRow && selCol ? (selCol.raw ? selCol.raw(selRow) : selCol.get(selRow)) : "";

  return (
    <div className="xl" style={{"--xlh": height + "px"}}>
      <div className="xl-bar">
        <div className="xl-name mono">{selCol ? COLLET(sel.c) + (sel.r+1) : "—"}</div>
        <div className="xl-fx">{fx === "" || fx == null ? "" : String(fx)}</div>
        {actions}
        <Btn c="sm" title="Download this grid as CSV — opens straight in Excel"
          onClick={()=>{ download(name.replace(/\s+/g,"_")+".csv", toCSV(cols, rows)); toast("Downloaded " + name + ".csv"); }}>
          Export CSV
        </Btn>
      </div>
      <div className="xl-scroll" ref={wrapRef} tabIndex={0} onKeyDown={onKey} style={{outline:"none"}}>
        <table className="xg">
          <thead>
            <tr className="abc">
              <th className="rn"/>
              {cols.map((c,i)=><th key={i} style={c.w?{width:c.w,minWidth:c.w}:null}>{COLLET(i)}</th>)}
            </tr>
            <tr className="hdr">
              <th className="rn"/>
              {cols.map((c,i)=><th key={i} className={c.align||""} style={c.w?{width:c.w,minWidth:c.w}:null} title={c.help}>{c.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={ri} className={rowTone ? rowTone(row) : ""} onClick={()=>onRowClick && onRowClick(row)}>
                <td className="rn">{ri+1}</td>
                {cols.map((c, ci) => (
                  <td key={ci} className={(c.align||"") + (sel.r===ri && sel.c===ci ? " sel":"") + (c.editable ? " edit":"")}
                      onMouseDown={()=>setSel({r:ri,c:ci})}>
                    {c.cell ? c.cell(row) : c.get(row)}
                  </td>
                ))}
              </tr>
            ))}
            {total && (
              <tr className="tot">
                <td className="rn">Σ</td>
                {cols.map((c,ci)=><td key={ci} className={c.align||""}>{total[c.key] != null ? total[c.key] : ""}</td>)}
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="xl-foot">
        <span>{rows.length} rows</span>
        <span className="dim">·</span>
        <span className="dim">Arrow keys to move · click a cell to read it in the strip above</span>
        {sub && <><span className="dim">·</span><span>{sub}</span></>}
      </div>
    </div>
  );
};

/* --------------------------------------------------------------- assistant */
/* Not a companion in the corner. Shows up at the point of need, shaped by the
   task, and knows what the planner is looking at (T8, design philosophy). */
const Assist = ({title="On this screen", children, actions}) => (
  <div className="assistant">
    <div className="ah"><span className="dot" style={{background:"var(--accent)"}}/>{title}</div>
    <div style={{fontSize:12.5, lineHeight:1.55}}>{children}</div>
    {actions && <div className="row wrap" style={{gap:6, marginTop:10}}>{actions}</div>}
  </div>
);

/* ------------------------------------------------------------- small charts */
const Donut = ({parts, size=104, thick=13, center}) => {
  const tot = parts.reduce((s,p)=>s+p.v,0) || 1;
  const R = (size - thick)/2, C = 2*Math.PI*R;
  let off = 0;
  return (
    <div style={{position:"relative", width:size, height:size, flex:"none"}}>
      <svg width={size} height={size} style={{transform:"rotate(-90deg)"}}>
        {parts.map((p,i)=>{
          const len = C * (p.v/tot);
          const el = <circle key={i} cx={size/2} cy={size/2} r={R} fill="none" stroke={p.c} strokeWidth={thick}
            strokeDasharray={`${len} ${C-len}`} strokeDashoffset={-off}/>;
          off += len; return el;
        })}
      </svg>
      {center && <div style={{position:"absolute", inset:0, display:"flex", flexDirection:"column",
        alignItems:"center", justifyContent:"center", lineHeight:1.1}}>{center}</div>}
    </div>
  );
};

const HBars = ({rows, fmt, max}) => {
  const m = max || Math.max(...rows.map(r=>r.v), 1);
  return <div className="col" style={{gap:7}}>
    {rows.map((r,i)=>(
      <div key={i}>
        <div className="row tiny" style={{justifyContent:"space-between", marginBottom:2}}>
          <span style={{whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis"}}>{r.l}</span>
          <span className="dim" style={{flex:"none", marginLeft:8}}>{fmt ? fmt(r.v) : r.v}</span>
        </div>
        <div className="bar"><i style={{width:(r.v/m*100)+"%", background:r.c||"var(--accent)"}}/></div>
      </div>
    ))}
  </div>;
};

/* Weekly flighting strip — 17 weeks, front-loaded. */
const FlightStrip = ({frontLoad=0.6, weeks=17, dark=[]}) => {
  const half = 8;
  const vals = Array.from({length:weeks}, (_,i) =>
    i < half ? frontLoad/half : (1-frontLoad)/(weeks-half));
  const m = Math.max(...vals);
  return <div className="row" style={{gap:2, alignItems:"flex-end", height:40}}>
    {vals.map((v,i)=>(
      <div key={i} title={`W${i+1} — ${pct(v,1)} of impressions`} style={{
        flex:1, height: Math.max(4, v/m*40), borderRadius:"2px 2px 0 0",
        background: dark.includes(i+1) ? "repeating-linear-gradient(45deg,#e2e6ea,#e2e6ea 3px,#fff 3px,#fff 6px)"
          : i < half ? "var(--accent)" : "#9dbef2" }}/>
    ))}
  </div>;
};

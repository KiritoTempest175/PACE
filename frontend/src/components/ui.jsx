import React, { useEffect, useRef } from 'react';
import { X, Info } from 'lucide-react';
export function Button({variant='primary',size='md',children,className='',...props}){
  return <button className={`button button--${variant} button--${size} ${className}`} {...props}>{children}</button>;
}
export function Input({label,id,...props}){return <label className="field" htmlFor={id}><span>{label}</span><input id={id} {...props}/></label>;}
export function Card({children,className='',...props}){return <section className={`card ${className}`} {...props}>{children}</section>;}
export function Badge({children,tone='neutral'}){return <span className={`badge badge--${tone}`}>{children}</span>;}
export function Tabs({label,items,value,onChange}){return <div role="tablist" aria-label={label} className="tabs">{items.map(item=><button key={item.value} type="button" role="tab" aria-selected={value===item.value} className={value===item.value?'active':''} onClick={()=>onChange(item.value)}>{item.label}</button>)}</div>;}
export function Skeleton({width='100%'}){return <div className="skeleton" aria-hidden="true" style={{width}}/>;}
export function Toast({message,onClose}){useEffect(()=>{if(!message)return;const t=setTimeout(onClose,6000);return ()=>clearTimeout(t);},[message,onClose]);return message?<div role="status" className="toast"><span>{message}</span><Button variant="ghost" size="sm" onClick={onClose} aria-label="Dismiss notification"><X size={15}/></Button></div>:null;}
export function Tooltip({text,children}){return <span className="tooltip-wrap">{children}<span className="tooltip" role="tooltip">{text}</span></span>;}
export function Modal({title,open,onClose,children}){
  const ref=useRef(null);
  useEffect(()=>{if(!open)return;const prev=document.activeElement;ref.current?.focus();const onKey=e=>{if(e.key==='Escape')onClose();if(e.key==='Tab'){const nodes=ref.current?.querySelectorAll('button,input,a,select,textarea,[tabindex]:not([tabindex="-1"])');if(!nodes?.length)return;const first=nodes[0],last=nodes[nodes.length-1];if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}};document.addEventListener('keydown',onKey);return ()=>{document.removeEventListener('keydown',onKey);prev?.focus?.();};},[open,onClose]);
  if(!open)return null;
  return <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}><section role="dialog" aria-modal="true" aria-label={title} tabIndex={-1} ref={ref} className="modal"><header><h2>{title}</h2><Button variant="ghost" size="sm" onClick={onClose} aria-label="Close dialog"><X size={18}/></Button></header>{children}</section></div>;
}

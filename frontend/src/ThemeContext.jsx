import {createContext,useContext,useEffect,useState} from 'react';
const C=createContext(null);const KEY='pace.theme';
export function ThemeProvider({children}){
  const [preference,setPreference]=useState(()=>localStorage.getItem(KEY)||'system');
  const [systemDark,setSystemDark]=useState(()=>window.matchMedia?.('(prefers-color-scheme: dark)').matches||false);
  useEffect(()=>{const media=window.matchMedia?.('(prefers-color-scheme: dark)');if(!media)return;const onChange=e=>setSystemDark(e.matches);media.addEventListener?.('change',onChange);return ()=>media.removeEventListener?.('change',onChange);},[]);
  useEffect(()=>{document.documentElement.dataset.theme=preference==='system'?(systemDark?'dark':'light'):preference;localStorage.setItem(KEY,preference);},[preference,systemDark]);
  return <C.Provider value={{preference,setPreference,theme:preference==='system'?(systemDark?'dark':'light'):preference}}>{children}</C.Provider>;
}
export const useTheme=()=>useContext(C);

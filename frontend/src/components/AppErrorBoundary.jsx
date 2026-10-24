import {Component} from 'react';

export default class AppErrorBoundary extends Component {
  state={hasError:false};
  static getDerivedStateFromError(){return {hasError:true};}
  render(){
    if(!this.state.hasError)return this.props.children;
    return <main role="alert" style={{minHeight:'100dvh',display:'grid',placeContent:'center',padding:24,background:'#0A0A0F',color:'#f7f2ff',fontFamily:'system-ui, sans-serif'}}>
      <h1 style={{color:'#9D5CE0'}}>PACE could not open this screen</h1>
      <p>Something went wrong while loading the interface. Try reloading the page.</p>
      <div style={{display:'flex',gap:12,flexWrap:'wrap'}}>
        <button type="button" onClick={()=>window.location.reload()} style={{background:'#7B3FBF',color:'#fff',border:0,padding:'12px 20px',cursor:'pointer'}}>Reload PACE</button>
        <a href="/" style={{color:'#00F0FF',padding:'12px 0'}}>Return to dashboard</a>
      </div>
    </main>;
  }
}

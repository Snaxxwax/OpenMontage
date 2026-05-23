import React from "react";
import { useCurrentFrame } from "remotion";
import type { MediaItem } from "../../types";
import { labelStyle } from "./mediaStyles";
export const CodeWalkthrough: React.FC<{ media: Extract<MediaItem, { kind: "code_walkthrough" }> }> = ({ media }) => { const frame=useCurrentFrame(); const lines=media.content.split("\n"); const active=Math.min(lines.length-1, Math.floor(frame/18)); return <div style={{height:"100%"}}><div style={labelStyle}>{media.filename ?? media.language ?? "CODE WALKTHROUGH"}</div><pre style={{marginTop:28,fontSize:34,lineHeight:1.34,color:"#D7FFF7",fontFamily:"JetBrains Mono,Fira Code,monospace"}}>{lines.map((line,i)=><div key={i} style={{display:"block",padding:"6px 12px",borderLeft:i===active?"8px solid #FF3333":"8px solid transparent",background:i===active?"rgba(255,0,0,.18)":"transparent"}}><span style={{color:"rgba(246,244,234,.38)",marginRight:22}}>{String(i+1).padStart(2,"0")}</span>{line}</div>)}</pre></div> };

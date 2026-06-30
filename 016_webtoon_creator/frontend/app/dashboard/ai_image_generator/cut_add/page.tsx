'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

// ════════════════════════════════════════════════════════════
// 타입 정의
// ════════════════════════════════════════════════════════════

type LibraryImage = { id: number; url: string; prompt_kr: string };

type PanelImage = {
  libId: number; url: string;
  offsetX: number; offsetY: number;
  scale: number; cropping: boolean;
};

type BubbleInstance = {
  id: string; type: string;
  x: number; y: number;   // % of panel (top-left)
  w: number; h: number;   // % of panel size
  rotation: number;       // degrees
  text: string;
};

type Panel = {
  id: string;
  image: PanelImage | null;
  bubbles: BubbleInstance[];
};

// 말풍선 편집 작업 타입
type BubbleMoveOp   = { panelId: string; bubbleId: string; sx: number; sy: number; ox: number; oy: number; pRect: DOMRect };
type BubbleResizeOp = { panelId: string; bubbleId: string; handle: string; sx: number; sy: number; ox: number; oy: number; ow: number; oh: number; pRect: DOMRect };
type BubbleRotateOp = { panelId: string; bubbleId: string; cx: number; cy: number; startAngle: number; origRot: number };

// ════════════════════════════════════════════════════════════
// 말풍선 SVG 렌더러
// ════════════════════════════════════════════════════════════

function BubbleSVG({ type }: { type: string }) {
  const base = { fill: 'white', stroke: '#1a1a1a', strokeWidth: 3, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
  const s = { width: '100%', height: '100%' };
  switch (type) {
    case 'round':     return <svg viewBox="0 0 200 130" {...base} style={s} xmlns="http://www.w3.org/2000/svg"><ellipse cx="100" cy="50" rx="94" ry="42"/><path d="M62,89 Q50,115 35,122 Q68,110 80,94" fill="white" stroke="#1a1a1a" strokeWidth="3"/></svg>;
    case 'rect':      return <svg viewBox="0 0 200 130" {...base} style={s} xmlns="http://www.w3.org/2000/svg"><rect x="5" y="5" width="190" height="85" rx="10"/><path d="M38,90 L28,122 L58,90" fill="white" stroke="#1a1a1a" strokeWidth="3"/></svg>;
    case 'think':     return <svg viewBox="0 0 220 150" {...base} strokeWidth={2.5} style={s} xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="70" r="34"/><circle cx="88" cy="45" r="37"/><circle cx="138" cy="40" r="40"/><circle cx="178" cy="62" r="34"/><circle cx="174" cy="102" r="26"/><circle cx="132" cy="118" r="22"/><circle cx="55" cy="108" r="28"/><circle cx="45" cy="136" r="9"/><circle cx="30" cy="147" r="6"/></svg>;
    case 'shout':     return <svg viewBox="0 0 220 220" {...base} strokeWidth={2.5} style={s} xmlns="http://www.w3.org/2000/svg"><polygon points="110,5 122,52 160,22 144,68 188,50 168,90 215,90 178,120 210,155 168,148 180,190 140,172 130,215 110,175 90,215 80,172 40,190 52,148 10,155 42,120 5,90 52,90 32,50 76,68 60,22 98,52"/></svg>;
    case 'whisper':   return <svg viewBox="0 0 200 130" {...base} strokeDasharray="8 5" style={s} xmlns="http://www.w3.org/2000/svg"><ellipse cx="100" cy="50" rx="94" ry="42"/><path d="M62,89 Q50,115 35,122 Q68,110 80,94" fill="white" stroke="#1a1a1a" strokeWidth="3" strokeDasharray="none"/></svg>;
    case 'sharp':     return <svg viewBox="0 0 200 130" {...base} strokeLinejoin="miter" style={s} xmlns="http://www.w3.org/2000/svg"><path d="M5,5 H195 V88 H120 L100,122 L80,88 H5 Z"/></svg>;
    case 'scream':    return <svg viewBox="0 0 220 220" {...base} strokeWidth={2.5} style={s} xmlns="http://www.w3.org/2000/svg"><path d="M110,6 L120,35 L145,18 L132,46 L162,40 L144,64 L175,68 L152,86 L178,100 L150,108 L168,132 L140,130 L148,158 L122,146 L118,175 L110,148 L102,175 L98,146 L72,158 L80,130 L52,132 L70,108 L42,100 L68,86 L45,68 L76,64 L58,40 L88,46 L75,18 L100,35 Z"/></svg>;
    case 'narration': return <svg viewBox="0 0 200 100" {...base} style={s} xmlns="http://www.w3.org/2000/svg"><rect x="5" y="5" width="190" height="90"/><line x1="20" y1="32" x2="180" y2="32" strokeWidth="1.5"/><line x1="20" y1="52" x2="180" y2="52" strokeWidth="1.5"/><line x1="20" y1="72" x2="130" y2="72" strokeWidth="1.5"/></svg>;
    default:          return null;
  }
}

// ════════════════════════════════════════════════════════════
// 말풍선 팔레트 정의
// ════════════════════════════════════════════════════════════

const BUBBLE_TYPES: { id: string; label: string; icon: React.ReactNode }[] = [
  { id: 'round',     label: '일반',    icon: <svg viewBox="0 0 60 56" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><ellipse cx="30" cy="22" rx="24" ry="15"/><path d="M20,35 Q15,46 9,50 Q22,44 28,37"/></svg> },
  { id: 'rect',      label: '사각',    icon: <svg viewBox="0 0 60 56" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round"><rect x="5" y="6" width="50" height="32" rx="4"/><path d="M14,38 L10,52 L24,38"/></svg> },
  { id: 'think',     label: '생각',    icon: <svg viewBox="0 0 60 60" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="17" cy="26" r="11"/><circle cx="31" cy="19" r="13"/><circle cx="45" cy="26" r="10"/><circle cx="38" cy="37" r="8"/><circle cx="22" cy="47" r="4"/><circle cx="17" cy="54" r="2.5"/></svg> },
  { id: 'shout',     label: '외침',    icon: <svg viewBox="0 0 60 60" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><polygon points="30,3 36,17 50,10 42,23 57,28 42,33 50,47 36,40 30,57 24,40 10,47 18,33 3,28 18,23 10,10 24,17"/></svg> },
  { id: 'whisper',   label: '속삭임',  icon: <svg viewBox="0 0 60 56" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeDasharray="4 3"><ellipse cx="30" cy="22" rx="24" ry="15"/></svg> },
  { id: 'sharp',     label: '각진',    icon: <svg viewBox="0 0 60 56" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="miter"><path d="M5,5 H55 V38 H36 L30,52 L24,38 H5 Z"/></svg> },
  { id: 'scream',    label: '절규',    icon: <svg viewBox="0 0 60 60" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"><path d="M30,4 L35,14 L45,8 L40,19 L52,18 L44,26 L54,30 L44,34 L52,42 L40,41 L45,52 L35,46 L30,56 L25,46 L15,52 L20,41 L8,42 L16,34 L6,30 L16,26 L8,18 L20,19 L15,8 L25,14 Z"/></svg> },
  { id: 'narration', label: '나레이션', icon: <svg viewBox="0 0 60 56" fill="none" stroke="currentColor" strokeWidth="2.5"><rect x="5" y="10" width="50" height="36" rx="0"/><line x1="12" y1="22" x2="48" y2="22"/><line x1="12" y1="31" x2="48" y2="31"/><line x1="12" y1="40" x2="34" y2="40"/></svg> },
];

// ════════════════════════════════════════════════════════════
// 레이아웃 템플릿
// ════════════════════════════════════════════════════════════

const LAYOUT_TEMPLATES = [
  { id: 'single',        label: '1컷',           areas: ['a'],               preview: [['a']],                gridAreas: '"a"',             rows: '1fr',           cols: '1fr' },
  { id: 'two-row',       label: '2컷 세로',       areas: ['a','b'],           preview: [['a'],['b']],          gridAreas: '"a" "b"',         rows: '1fr 1fr',       cols: '1fr' },
  { id: 'two-col',       label: '2컷 가로',       areas: ['a','b'],           preview: [['a','b']],            gridAreas: '"a b"',           rows: '1fr',           cols: '1fr 1fr' },
  { id: 'three-top',     label: '3컷 상단 와이드', areas: ['a','b','c'],       preview: [['a','a'],['b','c']],  gridAreas: '"a a" "b c"',     rows: '1.2fr 1fr',     cols: '1fr 1fr' },
  { id: 'three-bottom',  label: '3컷 하단 와이드', areas: ['a','b','c'],       preview: [['a','b'],['c','c']],  gridAreas: '"a b" "c c"',     rows: '1fr 1.2fr',     cols: '1fr 1fr' },
  { id: 'four-grid',     label: '4컷 2×2',        areas: ['a','b','c','d'],   preview: [['a','b'],['c','d']],  gridAreas: '"a b" "c d"',     rows: '1fr 1fr',       cols: '1fr 1fr' },
  { id: 'four-left',     label: '4컷 좌측 와이드', areas: ['a','b','c','d'],   preview: [['a','b'],['a','c'],['a','d']], gridAreas: '"a b" "a c" "a d"', rows: '1fr 1fr 1fr', cols: '1.4fr 1fr' },
  { id: 'five',          label: '5컷',            areas: ['a','b','c','d','e'],preview: [['a','b'],['c','c'],['d','e']], gridAreas: '"a b" "c c" "d e"', rows: '1fr 0.8fr 1fr', cols: '1fr 1fr' },
];

function makePanels(areas: string[]): Panel[] {
  return areas.map(id => ({ id, image: null, bubbles: [] }));
}

// ════════════════════════════════════════════════════════════
// 유틸
// ════════════════════════════════════════════════════════════

let _bc = 0;
function newBubbleId() { return `b${++_bc}`; }

function angleDeg(cx: number, cy: number, px: number, py: number) {
  return Math.atan2(py - cy, px - cx) * 180 / Math.PI;
}

function getPanelRect(el: Element): DOMRect | null {
  const p = el.closest('[data-panel]') as HTMLElement | null;
  return p ? p.getBoundingClientRect() : null;
}

// ════════════════════════════════════════════════════════════
// ToolBtn 컴포넌트
// ════════════════════════════════════════════════════════════

function ToolBtn({ children, onClick, active = false, danger = false, title }: {
  children: React.ReactNode; onClick: () => void;
  active?: boolean; danger?: boolean; title?: string;
}) {
  return (
    <button onClick={e => { e.stopPropagation(); onClick(); }} title={title}
      style={{ display:'flex', alignItems:'center', justifyContent:'center', width:'26px', height:'26px', borderRadius:'5px', fontSize:'11px', fontWeight:700, border:'none', cursor:'pointer', flexShrink:0,
        backgroundColor: active ? '#00C73C' : danger ? 'rgba(239,68,68,0.9)' : 'rgba(20,20,20,0.85)',
        color: '#FFFFFF', backdropFilter:'blur(4px)' }}>
      {children}
    </button>
  );
}

// ════════════════════════════════════════════════════════════
// 상수
// ════════════════════════════════════════════════════════════

const SAMPLE_WEBTOONS: { id: number; title: string }[] = [];
const SAMPLE_EPISODES: { id: number; webtoon_id: number; episode_number: number; title: string }[] = [];
const SAMPLE_IMAGES:   LibraryImage[] = [];

const RESIZE_HANDLES: { key: string; style: React.CSSProperties; cursor: string }[] = [
  { key:'nw', style:{ top:'-5px',    left:'-5px'   },                           cursor:'nwse-resize' },
  { key:'ne', style:{ top:'-5px',    right:'-5px'  },                           cursor:'nesw-resize' },
  { key:'sw', style:{ bottom:'-5px', left:'-5px'   },                           cursor:'nesw-resize' },
  { key:'se', style:{ bottom:'-5px', right:'-5px'  },                           cursor:'nwse-resize' },
  { key:'n',  style:{ top:'-5px',    left:'50%', transform:'translateX(-50%)' }, cursor:'n-resize'   },
  { key:'s',  style:{ bottom:'-5px', left:'50%', transform:'translateX(-50%)' }, cursor:'s-resize'   },
  { key:'e',  style:{ top:'50%', right:'-5px', transform:'translateY(-50%)' },   cursor:'e-resize'   },
  { key:'w',  style:{ top:'50%', left:'-5px',  transform:'translateY(-50%)' },   cursor:'w-resize'   },
];

// ════════════════════════════════════════════════════════════
// 메인 컴포넌트
// ════════════════════════════════════════════════════════════

export default function CutAddPage() {
  const [selectedWebtoon,  setSelectedWebtoon]  = useState('');
  const [selectedEpisode,  setSelectedEpisode]  = useState('');
  const [activeTemplate,   setActiveTemplate]   = useState('three-top');
  const [panels,           setPanels]           = useState<Panel[]>(() => makePanels(LAYOUT_TEMPLATES.find(t => t.id === 'three-top')!.areas));
  const [selectedPanel,    setSelectedPanel]    = useState<string | null>(null);
  const [selectedBubbleId, setSelectedBubbleId] = useState<string | null>(null);
  const [draggingImg,      setDraggingImg]      = useState<LibraryImage | null>(null);
  const [draggingBubble,   setDraggingBubble]   = useState<string | null>(null);
  const [showPrompt,       setShowPrompt]        = useState(false);
  const [prompt,           setPrompt]           = useState('');
  const [canvasZoom,       setCanvasZoom]       = useState(1);
  const [canvasOffset,     setCanvasOffset]     = useState({ x: 0, y: 0 });

  const canvasWrapRef = useRef<HTMLDivElement>(null);
  const panRef        = useRef({ active: false, sx: 0, sy: 0, ox: 0, oy: 0 });
  const imgRef        = useRef({ active: false, panelId: '', sx: 0, sy: 0, ox: 0, oy: 0 });
  const moveOpRef     = useRef<BubbleMoveOp | null>(null);
  const resizeOpRef   = useRef<BubbleResizeOp | null>(null);
  const rotateOpRef   = useRef<BubbleRotateOp | null>(null);

  // ── 마우스 휠: 캔버스 줌 ──
  useEffect(() => {
    const el = canvasWrapRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      setCanvasZoom(z => Math.max(0.25, Math.min(3, z - e.deltaY * 0.001)));
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, []);

  // ── 오른쪽 클릭 드래그: 캔버스 이동 ──
  const onCanvasMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 2) return;
    e.preventDefault();
    panRef.current = { active: true, sx: e.clientX, sy: e.clientY, ox: canvasOffset.x, oy: canvasOffset.y };
  };
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!panRef.current.active) return;
      setCanvasOffset({ x: panRef.current.ox + (e.clientX - panRef.current.sx), y: panRef.current.oy + (e.clientY - panRef.current.sy) });
    };
    const onUp = (e: MouseEvent) => { if (e.button === 2) panRef.current.active = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, []);

  // ── 레이아웃 변경 ──
  const changeTemplate = (id: string) => {
    const tpl = LAYOUT_TEMPLATES.find(t => t.id === id)!;
    setActiveTemplate(id);
    setPanels(makePanels(tpl.areas));
    setSelectedPanel(null);
    setSelectedBubbleId(null);
  };

  // ── 패널 드롭 ──
  const handlePanelDrop = (panelId: string, e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const pRect = e.currentTarget.getBoundingClientRect();
    if (draggingImg) {
      setPanels(prev => prev.map(p =>
        p.id === panelId ? { ...p, image: { libId: draggingImg.id, url: draggingImg.url, offsetX: 0, offsetY: 0, scale: 1, cropping: false } } : p
      ));
      setSelectedPanel(panelId);
      setDraggingImg(null);
    } else if (draggingBubble) {
      const rawX = ((e.clientX - pRect.left) / pRect.width) * 100;
      const rawY = ((e.clientY - pRect.top) / pRect.height) * 100;
      const nb: BubbleInstance = {
        id: newBubbleId(), type: draggingBubble,
        x: Math.max(0, Math.min(70, rawX - 15)),
        y: Math.max(0, Math.min(65, rawY - 15)),
        w: 35, h: 30, rotation: 0, text: '말풍선',
      };
      setPanels(prev => prev.map(p => p.id === panelId ? { ...p, bubbles: [...p.bubbles, nb] } : p));
      setSelectedPanel(panelId);
      setSelectedBubbleId(nb.id);
      setDraggingBubble(null);
    }
  };

  // ── 이미지 드래그 (패널 내) ──
  const onImgPD = (panelId: string, e: React.PointerEvent<HTMLDivElement>) => {
    const panel = panels.find(p => p.id === panelId);
    if (!panel?.image || panel.image.cropping) return;
    e.stopPropagation();
    imgRef.current = { active: true, panelId, sx: e.clientX, sy: e.clientY, ox: panel.image.offsetX, oy: panel.image.offsetY };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onImgPM = (panelId: string, e: React.PointerEvent<HTMLDivElement>) => {
    if (!imgRef.current.active || imgRef.current.panelId !== panelId) return;
    const dx = e.clientX - imgRef.current.sx, dy = e.clientY - imgRef.current.sy;
    setPanels(prev => prev.map(p =>
      p.id === panelId && p.image ? { ...p, image: { ...p.image, offsetX: imgRef.current.ox + dx, offsetY: imgRef.current.oy + dy } } : p
    ));
  };
  const onImgPU = (e: React.PointerEvent<HTMLDivElement>) => {
    imgRef.current.active = false;
    e.currentTarget.releasePointerCapture(e.pointerId);
  };

  const scalePanel   = (panelId: string, d: number) => setPanels(prev => prev.map(p => p.id === panelId && p.image ? { ...p, image: { ...p.image, scale: Math.max(0.3, Math.min(6, p.image.scale + d)) } } : p));
  const toggleCrop   = (panelId: string)             => setPanels(prev => prev.map(p => p.id === panelId && p.image ? { ...p, image: { ...p.image, cropping: !p.image.cropping } } : p));
  const clearPanel   = (panelId: string)             => { setPanels(prev => prev.map(p => p.id === panelId ? { ...p, image: null } : p)); if (selectedPanel === panelId) setSelectedPanel(null); };
  const deleteBubble = (panelId: string, bid: string)=> { setPanels(prev => prev.map(p => p.id === panelId ? { ...p, bubbles: p.bubbles.filter(b => b.id !== bid) } : p)); setSelectedBubbleId(null); };

  // ── 말풍선 이동 ──
  const onBubblePD = (panelId: string, bubbleId: string, e: React.PointerEvent<HTMLDivElement>) => {
    e.stopPropagation();
    setSelectedPanel(panelId); setSelectedBubbleId(bubbleId);
    const bubble = panels.find(p => p.id === panelId)?.bubbles.find(b => b.id === bubbleId);
    const pRect  = getPanelRect(e.currentTarget);
    if (!bubble || !pRect) return;
    moveOpRef.current = { panelId, bubbleId, sx: e.clientX, sy: e.clientY, ox: bubble.x, oy: bubble.y, pRect };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onBubblePM = (e: React.PointerEvent<HTMLDivElement>) => {
    const op = moveOpRef.current; if (!op) return;
    const dx = ((e.clientX - op.sx) / op.pRect.width)  * 100;
    const dy = ((e.clientY - op.sy) / op.pRect.height) * 100;
    setPanels(prev => prev.map(p =>
      p.id === op.panelId ? { ...p, bubbles: p.bubbles.map(b =>
        b.id === op.bubbleId ? { ...b, x: Math.max(0, Math.min(90, op.ox + dx)), y: Math.max(0, Math.min(90, op.oy + dy)) } : b
      )} : p
    ));
  };
  const onBubblePU = (e: React.PointerEvent<HTMLDivElement>) => {
    moveOpRef.current = null;
    e.currentTarget.releasePointerCapture(e.pointerId);
  };

  // ── 말풍선 리사이즈 ──
  const onResizePD = (panelId: string, bubbleId: string, handle: string, e: React.PointerEvent<HTMLDivElement>) => {
    e.stopPropagation();
    const bubble = panels.find(p => p.id === panelId)?.bubbles.find(b => b.id === bubbleId);
    const pRect  = getPanelRect(e.currentTarget);
    if (!bubble || !pRect) return;
    resizeOpRef.current = { panelId, bubbleId, handle, sx: e.clientX, sy: e.clientY, ox: bubble.x, oy: bubble.y, ow: bubble.w, oh: bubble.h, pRect };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onResizePM = (e: React.PointerEvent<HTMLDivElement>) => {
    const op = resizeOpRef.current; if (!op) return;
    const dxP = ((e.clientX - op.sx) / op.pRect.width)  * 100;
    const dyP = ((e.clientY - op.sy) / op.pRect.height) * 100;
    setPanels(prev => prev.map(p =>
      p.id === op.panelId ? { ...p, bubbles: p.bubbles.map(b => {
        if (b.id !== op.bubbleId) return b;
        let { x, y, w, h } = { x: op.ox, y: op.oy, w: op.ow, h: op.oh };
        if (op.handle.includes('e')) w = Math.max(10, op.ow + dxP);
        if (op.handle.includes('s')) h = Math.max(8,  op.oh + dyP);
        if (op.handle.includes('w')) { x = op.ox + dxP; w = Math.max(10, op.ow - dxP); }
        if (op.handle.includes('n')) { y = op.oy + dyP; h = Math.max(8,  op.oh - dyP); }
        return { ...b, x, y, w, h };
      })} : p
    ));
  };
  const onResizePU = (e: React.PointerEvent<HTMLDivElement>) => {
    resizeOpRef.current = null;
    e.currentTarget.releasePointerCapture(e.pointerId);
  };

  // ── 말풍선 회전 ──
  const onRotatePD = (panelId: string, bubbleId: string, e: React.PointerEvent<HTMLDivElement>) => {
    e.stopPropagation();
    const bubble = panels.find(p => p.id === panelId)?.bubbles.find(b => b.id === bubbleId);
    const pRect  = getPanelRect(e.currentTarget);
    if (!bubble || !pRect) return;
    const cx = pRect.left + (bubble.x + bubble.w / 2) / 100 * pRect.width;
    const cy = pRect.top  + (bubble.y + bubble.h / 2) / 100 * pRect.height;
    rotateOpRef.current = { panelId, bubbleId, cx, cy, startAngle: angleDeg(cx, cy, e.clientX, e.clientY), origRot: bubble.rotation };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onRotatePM = (e: React.PointerEvent<HTMLDivElement>) => {
    const op = rotateOpRef.current; if (!op) return;
    const delta = angleDeg(op.cx, op.cy, e.clientX, e.clientY) - op.startAngle;
    setPanels(prev => prev.map(p =>
      p.id === op.panelId ? { ...p, bubbles: p.bubbles.map(b =>
        b.id === op.bubbleId ? { ...b, rotation: (op.origRot + delta + 360) % 360 } : b
      )} : p
    ));
  };
  const onRotatePU = (e: React.PointerEvent<HTMLDivElement>) => {
    rotateOpRef.current = null;
    e.currentTarget.releasePointerCapture(e.pointerId);
  };

  // ── 파생 값 ──
  const currentTpl  = LAYOUT_TEMPLATES.find(t => t.id === activeTemplate)!;
  const filledCount = panels.filter(p => p.image !== null).length;
  const filteredEps = SAMPLE_EPISODES.filter(e => e.webtoon_id === parseInt(selectedWebtoon));

  const SEL_STYLE: React.CSSProperties = {
    backgroundColor:'var(--dash-surface)', color:'var(--dash-text)', border:'1px solid var(--dash-border)', borderRadius:'6px',
    padding:'5px 26px 5px 9px', fontSize:'12px', outline:'none', cursor:'pointer', appearance:'none',
    backgroundImage:`url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23666'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'/%3E%3C/svg%3E")`,
    backgroundRepeat:'no-repeat', backgroundPosition:'right 5px center', backgroundSize:'12px',
  };

  // ═══════════════════════════════════════════════════════════
  // 렌더
  // ═══════════════════════════════════════════════════════════

  return (
    <div className="flex flex-col h-screen" style={{ backgroundColor:'var(--dash-bg)', color:'var(--dash-text)' }}
      onContextMenu={e => e.preventDefault()}>

      {/* ══ GNB ═══════════════════════════════════════════════ */}
      <header className="flex items-center justify-between px-5 flex-shrink-0"
        style={{ height:'50px', backgroundColor:'var(--dash-panel)', borderBottom:'1px solid var(--dash-border)', zIndex:10 }}>
        <div className="flex items-center gap-2">
          <Link href="/dashboard" className="font-black tracking-tight transition-opacity hover:opacity-70"
            style={{ fontSize:'15px', color:'var(--dash-text)', textDecoration:'none' }}>ToonCraft</Link>
          <span style={{ color:'var(--dash-text-muted)', fontSize:'11px' }}>›</span>
          <Link href="/dashboard/ai_image_generator" className="text-xs transition-opacity hover:opacity-70"
            style={{ color:'var(--dash-text-sub)', textDecoration:'none' }}>AI 이미지 만들기</Link>
          <span style={{ color:'var(--dash-text-muted)', fontSize:'11px' }}>›</span>
          <span className="text-xs font-semibold" style={{ color:'var(--dash-text)' }}>웹툰 편집기</span>
        </div>
        <div className="flex items-center gap-2">
          <select value={selectedWebtoon} onChange={e => { setSelectedWebtoon(e.target.value); setSelectedEpisode(''); }} style={SEL_STYLE}>
            <option value="">웹툰 선택</option>
            {SAMPLE_WEBTOONS.map(w => <option key={w.id} value={String(w.id)} style={{ backgroundColor:'#1A1A1A' }}>{w.title}</option>)}
          </select>
          <select value={selectedEpisode} onChange={e => setSelectedEpisode(e.target.value)} disabled={!selectedWebtoon} style={{ ...SEL_STYLE, opacity: selectedWebtoon ? 1 : 0.45 }}>
            <option value="">에피소드 선택</option>
            {filteredEps.map(ep => <option key={ep.id} value={String(ep.id)} style={{ backgroundColor:'#1A1A1A' }}>{ep.episode_number}화 · {ep.title}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => { setPanels(makePanels(currentTpl.areas)); setSelectedPanel(null); setSelectedBubbleId(null); }}
            className="px-3 py-1.5 rounded text-xs font-medium transition-opacity hover:opacity-70"
            style={{ backgroundColor:'var(--dash-surface)', color:'var(--dash-text-sub)', border:'1px solid var(--dash-border)' }}>
            초기화
          </button>
          <button className="px-3 py-1.5 rounded text-xs font-semibold transition-opacity hover:opacity-80"
            style={{ backgroundColor:'var(--dash-surface)', color:'var(--dash-text)', border:'1px solid var(--dash-border)' }}>
            임시저장
          </button>
          <button className="px-4 py-1.5 rounded text-xs font-bold transition-opacity hover:opacity-85"
            style={{ backgroundColor:'#00C73C', color:'#FFFFFF' }}>
            저장하기
          </button>
        </div>
      </header>

      {/* ══ 본문 ═══════════════════════════════════════════════ */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── LEFT: 이미지 라이브러리 ─────────────────────────── */}
        <aside className="flex flex-col flex-shrink-0 overflow-y-auto"
          style={{ width:'200px', backgroundColor:'var(--dash-panel)', borderRight:'1px solid var(--dash-border)' }}>
          <div className="px-3 pt-3 pb-2.5" style={{ borderBottom:'1px solid var(--dash-border)' }}>
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color:'var(--dash-text-muted)' }}>이미지 라이브러리</p>
            <p style={{ fontSize:'10px', color:'var(--dash-text-muted)', marginTop:'2px' }}>드래그하여 패널에 배치</p>
          </div>
          <div className="px-3 py-2.5" style={{ borderBottom:'1px solid var(--dash-border)' }}>
            {showPrompt ? (
              <div className="flex flex-col gap-2">
                <textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="웹툰 장면을 한국어로 묘사하세요..." rows={3}
                  style={{ width:'100%', backgroundColor:'var(--dash-surface)', color:'var(--dash-text)', border:'1px solid var(--dash-border)', borderRadius:'6px', padding:'7px 9px', fontSize:'11px', outline:'none', resize:'none', lineHeight:1.5 }}/>
                <div className="flex gap-1.5">
                  <button onClick={() => setShowPrompt(false)} className="flex-1 py-1.5 rounded text-xs transition-opacity hover:opacity-70"
                    style={{ backgroundColor:'var(--dash-surface)', color:'var(--dash-text-sub)', border:'1px solid var(--dash-border)' }}>취소</button>
                  <button className="py-1.5 rounded text-xs font-bold" style={{ backgroundColor:'#00C73C', color:'#FFFFFF', flexGrow:2 }}>생성</button>
                </div>
              </div>
            ) : (
              <button onClick={() => setShowPrompt(true)} className="w-full py-2 rounded flex items-center justify-center gap-1.5 text-xs font-semibold transition-opacity hover:opacity-80"
                style={{ backgroundColor:'#00C73C', color:'#FFFFFF' }}>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
                AI 이미지 생성
              </button>
            )}
          </div>
          <div className="flex-1 p-2.5 overflow-y-auto">
            {SAMPLE_IMAGES.length > 0 ? (
              <div className="grid gap-2" style={{ gridTemplateColumns:'1fr 1fr' }}>
                {SAMPLE_IMAGES.map(img => (
                  <div key={img.id} draggable onDragStart={() => setDraggingImg(img)} onDragEnd={() => setDraggingImg(null)} title={img.prompt_kr}
                    style={{ aspectRatio:'3/4', borderRadius:'5px', overflow:'hidden', border:'2px solid var(--dash-border)', cursor:'grab' }}>
                    <img src={img.url} alt={img.prompt_kr} style={{ width:'100%', height:'100%', objectFit:'cover', pointerEvents:'none' }} draggable={false}/>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-10 gap-3 h-full">
                <div className="w-11 h-11 rounded-full flex items-center justify-center" style={{ backgroundColor:'var(--dash-surface)' }}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color:'var(--dash-text-muted)' }}>
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                  </svg>
                </div>
                <p className="text-center" style={{ fontSize:'10px', color:'var(--dash-text-muted)', lineHeight:1.7 }}>
                  생성된 이미지가 없습니다.<br/><span style={{ color:'#00C73C' }}>AI 이미지 생성</span>을 눌러보세요.
                </p>
              </div>
            )}
          </div>
        </aside>

        {/* ── CENTER: 캔버스 ──────────────────────────────────── */}
        <main className="flex-1 flex flex-col overflow-hidden" style={{ backgroundColor:'#252525' }}>
          {/* 툴바 */}
          <div className="flex items-center justify-between px-4 flex-shrink-0"
            style={{ height:'38px', backgroundColor:'var(--dash-panel)', borderBottom:'1px solid var(--dash-border)' }}>
            <div className="flex items-center gap-3">
              <span style={{ fontSize:'11px', color:'var(--dash-text-muted)' }}>{currentTpl.label}</span>
              <span className="px-2 py-0.5 rounded" style={{ backgroundColor:'var(--dash-surface)', fontSize:'10px', color: filledCount === panels.length ? '#00C73C' : 'var(--dash-text-muted)' }}>
                {filledCount}/{panels.length} 배치됨
              </span>
              <span style={{ fontSize:'10px', color:'var(--dash-text-muted)' }}>우클릭 드래그: 이동 | 휠: 줌</span>
            </div>
            <div className="flex items-center gap-1.5">
              <button onClick={() => setCanvasZoom(z => Math.min(3, z + 0.1))}
                style={{ width:'22px', height:'22px', borderRadius:'4px', fontSize:'14px', fontWeight:700, backgroundColor:'var(--dash-surface)', color:'var(--dash-text-sub)', border:'1px solid var(--dash-border)', cursor:'pointer', lineHeight:1 }}>+</button>
              <span style={{ fontSize:'10px', color:'var(--dash-text-muted)', minWidth:'36px', textAlign:'center' }}>{Math.round(canvasZoom * 100)}%</span>
              <button onClick={() => setCanvasZoom(z => Math.max(0.25, z - 0.1))}
                style={{ width:'22px', height:'22px', borderRadius:'4px', fontSize:'14px', fontWeight:700, backgroundColor:'var(--dash-surface)', color:'var(--dash-text-sub)', border:'1px solid var(--dash-border)', cursor:'pointer', lineHeight:1 }}>−</button>
              <button onClick={() => { setCanvasZoom(1); setCanvasOffset({ x:0, y:0 }); }}
                style={{ padding:'2px 7px', borderRadius:'4px', fontSize:'10px', backgroundColor:'var(--dash-surface)', color:'var(--dash-text-muted)', border:'1px solid var(--dash-border)', cursor:'pointer' }}>
                1:1
              </button>
            </div>
          </div>

          {/* 캔버스 뷰포트 */}
          <div ref={canvasWrapRef} className="flex-1 overflow-hidden flex items-center justify-center"
            onMouseDown={onCanvasMouseDown} onContextMenu={e => e.preventDefault()}>
            {/* 웹툰 페이지 */}
            <div style={{
              width:'380px', height:'507px', flexShrink:0,
              transform:`translate(${canvasOffset.x}px, ${canvasOffset.y}px) scale(${canvasZoom})`,
              transformOrigin:'center center',
              display:'grid', gap:'3px', padding:'3px', backgroundColor:'#000',
              boxShadow:'0 8px 40px rgba(0,0,0,0.7)',
              gridTemplateAreas: currentTpl.gridAreas,
              gridTemplateRows: currentTpl.rows,
              gridTemplateColumns: currentTpl.cols,
            }}>
              {currentTpl.areas.map(areaId => {
                const panel    = panels.find(p => p.id === areaId)!;
                const isActive = selectedPanel === areaId;
                return (
                  <div key={areaId} data-panel={areaId}
                    onClick={e => { if (e.target === e.currentTarget) { setSelectedPanel(isActive ? null : areaId); setSelectedBubbleId(null); } }}
                    onDragOver={e => e.preventDefault()}
                    onDrop={e => handlePanelDrop(areaId, e)}
                    style={{ gridArea:areaId, position:'relative', overflow:'hidden', backgroundColor:'#1A1A1A',
                      outline: isActive ? '2px solid #00C73C' : '2px solid transparent', outlineOffset:'-2px' }}>

                    {/* ── 이미지 레이어 ── */}
                    {panel.image ? (
                      <>
                        <div style={{ position:'absolute', inset:0, cursor: panel.image.cropping ? 'crosshair' : 'move', touchAction:'none' }}
                          onPointerDown={e => onImgPD(areaId, e)}
                          onPointerMove={e => onImgPM(areaId, e)}
                          onPointerUp={onImgPU}>
                          <img src={panel.image.url} draggable={false} style={{ position:'absolute', top:'50%', left:'50%', width:'100%', height:'100%', objectFit:'cover', pointerEvents:'none', userSelect:'none', transform:`translate(calc(-50% + ${panel.image.offsetX}px), calc(-50% + ${panel.image.offsetY}px)) scale(${panel.image.scale})`, transformOrigin:'center' }}/>
                        </div>
                        {/* 자르기 오버레이 */}
                        {panel.image.cropping && (
                          <div style={{ position:'absolute', inset:0, pointerEvents:'none' }}>
                            <div style={{ position:'absolute', inset:0, background:'rgba(0,0,0,0.55)', clipPath:'polygon(0% 0%, 0% 100%, 12% 100%, 12% 12%, 88% 12%, 88% 88%, 12% 88%, 12% 100%, 100% 100%, 100% 0%)' }}/>
                            <div style={{ position:'absolute', top:'12%', left:'12%', right:'12%', bottom:'12%', border:'1.5px solid #00C73C' }}>
                              {[1,2].map(i=><div key={`h${i}`} style={{ position:'absolute', left:0, right:0, top:`${i*33.33}%`, height:'1px', backgroundColor:'rgba(0,199,60,0.4)' }}/>)}
                              {[1,2].map(i=><div key={`v${i}`} style={{ position:'absolute', top:0, bottom:0, left:`${i*33.33}%`, width:'1px', backgroundColor:'rgba(0,199,60,0.4)' }}/>)}
                              {[{top:'-4px',left:'-4px'},{top:'-4px',right:'-4px'},{bottom:'-4px',left:'-4px'},{bottom:'-4px',right:'-4px'}].map((pos,i)=>(
                                <div key={i} style={{ position:'absolute', width:'8px', height:'8px', backgroundColor:'#00C73C', ...pos }}/>
                              ))}
                            </div>
                          </div>
                        )}
                        {/* 편집 툴바 */}
                        {isActive && (
                          <div onClick={e=>e.stopPropagation()}
                            style={{ position:'absolute', bottom:'6px', left:'50%', transform:'translateX(-50%)', display:'flex', gap:'3px', backgroundColor:'rgba(10,10,10,0.75)', borderRadius:'7px', padding:'4px 5px', backdropFilter:'blur(6px)', zIndex:20, border:'1px solid rgba(255,255,255,0.08)' }}>
                            <ToolBtn title="이동" active={!panel.image.cropping} onClick={() => { if(panel.image?.cropping) toggleCrop(areaId); }}>
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4m0 6l-4 4-4-4"/></svg>
                            </ToolBtn>
                            <ToolBtn title="확대" onClick={() => scalePanel(areaId, 0.2)}>
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7"/></svg>
                            </ToolBtn>
                            <ToolBtn title="축소" onClick={() => scalePanel(areaId, -0.2)}>
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7"/></svg>
                            </ToolBtn>
                            <div style={{ width:'1px', backgroundColor:'rgba(255,255,255,0.12)', margin:'0 1px' }}/>
                            <ToolBtn title="자르기" active={panel.image.cropping} onClick={() => toggleCrop(areaId)}>
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 2v14a2 2 0 002 2h14M6 2L2 6m4-4l4 4M18 22l4-4m-4 4V8a2 2 0 00-2-2H2"/></svg>
                            </ToolBtn>
                            {panel.image.cropping && (
                              <ToolBtn title="자르기 확정" active onClick={() => toggleCrop(areaId)}>
                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7"/></svg>
                              </ToolBtn>
                            )}
                            <div style={{ width:'1px', backgroundColor:'rgba(255,255,255,0.12)', margin:'0 1px' }}/>
                            <ToolBtn title="이미지 제거" danger onClick={() => clearPanel(areaId)}>
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12"/></svg>
                            </ToolBtn>
                          </div>
                        )}
                        {isActive && (
                          <div style={{ position:'absolute', top:'5px', right:'6px', fontSize:'9px', fontWeight:700, backgroundColor:'rgba(0,0,0,0.65)', color:'#AAAAAA', padding:'2px 5px', borderRadius:'4px', zIndex:5 }}>
                            {Math.round(panel.image.scale * 100)}%
                          </div>
                        )}
                      </>
                    ) : (
                      /* 빈 패널 */
                      <div className="absolute inset-0 flex flex-col items-center justify-center gap-1"
                        style={{ backgroundColor:(draggingImg||draggingBubble)&&isActive ? 'rgba(0,199,60,0.06)' : 'transparent', border:(draggingImg||draggingBubble)?'2px dashed rgba(0,199,60,0.4)':'2px dashed transparent', transition:'all 0.15s' }}>
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color:(draggingImg||draggingBubble)?'rgba(0,199,60,0.6)':'#2A2A2A' }}>
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                        </svg>
                        <span style={{ fontSize:'8px', color:(draggingImg||draggingBubble)?'rgba(0,199,60,0.8)':'#2A2A2A', fontWeight:600 }}>
                          {(draggingImg||draggingBubble) ? '여기에 놓기' : '드래그로 배치'}
                        </span>
                        <span style={{ fontSize:'7px', color:'#202020', fontWeight:700, marginTop:'1px' }}>{areaId.toUpperCase()}</span>
                      </div>
                    )}

                    {/* ── 말풍선 레이어 ── */}
                    {panel.bubbles.map(bubble => {
                      const isSelected = selectedPanel === areaId && selectedBubbleId === bubble.id;
                      return (
                        <div key={bubble.id}
                          style={{ position:'absolute', left:`${bubble.x}%`, top:`${bubble.y}%`, width:`${bubble.w}%`, height:`${bubble.h}%`,
                            transform:`rotate(${bubble.rotation}deg)`, transformOrigin:'center center',
                            cursor:'move', zIndex:30,
                            outline: isSelected ? '1.5px dashed rgba(0,199,60,0.8)' : 'none', outlineOffset:'2px' }}
                          onPointerDown={e => onBubblePD(areaId, bubble.id, e)}
                          onPointerMove={onBubblePM}
                          onPointerUp={onBubblePU}
                        >
                          {/* SVG 배경 */}
                          <div style={{ position:'absolute', inset:0, pointerEvents:'none' }}>
                            <BubbleSVG type={bubble.type}/>
                          </div>
                          {/* 텍스트 */}
                          <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center',
                            fontSize:`${Math.max(7, bubble.w * 0.18)}px`, fontWeight:700, color:'#111', pointerEvents:'none', lineHeight:1.2, padding:'10% 12%', textAlign:'center', wordBreak:'keep-all' }}>
                            {bubble.text}
                          </div>

                          {/* ── 선택 핸들 ── */}
                          {isSelected && (
                            <>
                              {/* 리사이즈 8방향 핸들 */}
                              {RESIZE_HANDLES.map(h => (
                                <div key={h.key}
                                  onPointerDown={e => onResizePD(areaId, bubble.id, h.key, e)}
                                  onPointerMove={onResizePM}
                                  onPointerUp={onResizePU}
                                  style={{ position:'absolute', width:'10px', height:'10px', backgroundColor:'#00C73C', border:'1.5px solid white', borderRadius:'2px', cursor:h.cursor, zIndex:40, ...h.style }}
                                />
                              ))}

                              {/* 회전 핸들 연결선 */}
                              <div style={{ position:'absolute', top:'-22px', left:'50%', transform:'translateX(-50%)', width:'1px', height:'18px', backgroundColor:'rgba(0,199,60,0.6)', pointerEvents:'none', zIndex:39 }}/>

                              {/* 회전 핸들 */}
                              <div title="드래그하여 회전"
                                onPointerDown={e => onRotatePD(areaId, bubble.id, e)}
                                onPointerMove={onRotatePM}
                                onPointerUp={onRotatePU}
                                style={{ position:'absolute', top:'-30px', left:'50%', transform:'translateX(-50%)', width:'14px', height:'14px', backgroundColor:'#00C73C', border:'2px solid white', borderRadius:'50%', cursor:'grab', zIndex:40 }}
                              />

                              {/* 삭제 버튼 */}
                              <button onClick={e => { e.stopPropagation(); deleteBubble(areaId, bubble.id); }}
                                style={{ position:'absolute', top:'-10px', right:'-10px', width:'16px', height:'16px', backgroundColor:'rgba(239,68,68,0.9)', color:'#fff', border:'none', borderRadius:'50%', cursor:'pointer', fontSize:'10px', fontWeight:700, display:'flex', alignItems:'center', justifyContent:'center', zIndex:41, lineHeight:1 }}>
                                ×
                              </button>

                              {/* 회전각 표시 */}
                              <div style={{ position:'absolute', bottom:'-20px', left:'50%', transform:'translateX(-50%)', fontSize:'8px', color:'#00C73C', fontWeight:700, whiteSpace:'nowrap', pointerEvents:'none', backgroundColor:'rgba(0,0,0,0.65)', padding:'1px 5px', borderRadius:'3px', zIndex:38 }}>
                                {Math.round(bubble.rotation)}°
                              </div>
                            </>
                          )}
                        </div>
                      );
                    })}

                    {/* 말풍선 드래그 중 비활성 패널 강조 */}
                    {draggingBubble && !isActive && (
                      <div style={{ position:'absolute', inset:0, border:'2px dashed rgba(0,199,60,0.25)', pointerEvents:'none', zIndex:50 }}/>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </main>

        {/* ── RIGHT 1: 말풍선 팔레트 (110px) ─────────────────── */}
        <aside className="flex flex-col flex-shrink-0 overflow-y-auto"
          style={{ width:'110px', backgroundColor:'var(--dash-panel)', borderLeft:'1px solid var(--dash-border)' }}>
          <div className="px-2.5 pt-3 pb-2" style={{ borderBottom:'1px solid var(--dash-border)' }}>
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color:'var(--dash-text-muted)' }}>말풍선</p>
            <p style={{ fontSize:'9px', color:'var(--dash-text-muted)', marginTop:'2px' }}>드래그하여 패널에 배치</p>
          </div>
          <div className="p-2 flex flex-col gap-1.5">
            {BUBBLE_TYPES.map(bt => (
              <div key={bt.id} draggable
                onDragStart={() => setDraggingBubble(bt.id)}
                onDragEnd={() => setDraggingBubble(null)}
                title={`${bt.label} 말풍선`}
                style={{ display:'flex', flexDirection:'column', alignItems:'center', gap:'3px', padding:'6px 4px', borderRadius:'7px', cursor:'grab',
                  backgroundColor: draggingBubble === bt.id ? 'rgba(0,199,60,0.12)' : 'var(--dash-surface)',
                  border: draggingBubble === bt.id ? '1px solid rgba(0,199,60,0.35)' : '1px solid var(--dash-border)', transition:'all 0.15s' }}>
                <div style={{ width:'44px', height:'36px', color:'var(--dash-text-sub)', pointerEvents:'none' }}>
                  {bt.icon}
                </div>
                <span style={{ fontSize:'9px', color:'var(--dash-text-muted)', fontWeight:500, pointerEvents:'none' }}>
                  {bt.label}
                </span>
              </div>
            ))}
          </div>
        </aside>

        {/* ── RIGHT 2: 레이아웃 + 도구 (120px) ───────────────── */}
        <aside className="flex flex-col flex-shrink-0 overflow-y-auto"
          style={{ width:'120px', backgroundColor:'var(--dash-panel)', borderLeft:'1px solid var(--dash-border)' }}>
          <div className="px-2.5 pt-3 pb-2" style={{ borderBottom:'1px solid var(--dash-border)' }}>
            <p className="text-xs font-bold uppercase tracking-widest" style={{ color:'var(--dash-text-muted)' }}>레이아웃</p>
          </div>
          <div className="p-2 flex flex-col gap-1.5">
            {LAYOUT_TEMPLATES.map(tpl => {
              const isActive = activeTemplate === tpl.id;
              const rows = tpl.preview.length;
              const cols = tpl.preview[0].length;
              return (
                <button key={tpl.id} onClick={() => changeTemplate(tpl.id)}
                  style={{ display:'flex', alignItems:'center', gap:'7px', padding:'5px 7px', borderRadius:'7px', width:'100%', cursor:'pointer', transition:'all 0.15s',
                    backgroundColor: isActive ? 'rgba(0,199,60,0.1)' : 'var(--dash-surface)',
                    border: isActive ? '1px solid rgba(0,199,60,0.35)' : '1px solid var(--dash-border)' }}>
                  <div style={{ display:'grid', width:'34px', height:'26px', gap:'1.5px', padding:'2px', backgroundColor:'#111', borderRadius:'2px', flexShrink:0,
                    gridTemplateAreas: tpl.preview.map(r=>`"${r.join(' ')}"`).join(' '),
                    gridTemplateRows:`repeat(${rows}, 1fr)`, gridTemplateColumns:`repeat(${cols}, 1fr)` }}>
                    {[...new Set(tpl.preview.flat())].map(a=>(
                      <div key={a} style={{ gridArea:a, backgroundColor: isActive ? 'rgba(0,199,60,0.55)' : '#333', borderRadius:'1px' }}/>
                    ))}
                  </div>
                  <span style={{ fontSize:'9px', textAlign:'left', lineHeight:1.3, fontWeight: isActive ? 700 : 400, color: isActive ? '#00C73C' : 'var(--dash-text-muted)' }}>
                    {tpl.label}
                  </span>
                </button>
              );
            })}
          </div>
          <div className="px-2.5 pt-2.5 pb-3 mt-auto" style={{ borderTop:'1px solid var(--dash-border)' }}>
            <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color:'var(--dash-text-muted)' }}>도구</p>
            <button onClick={() => { setPanels(makePanels(currentTpl.areas)); setSelectedPanel(null); setSelectedBubbleId(null); }}
              style={{ display:'flex', alignItems:'center', gap:'5px', width:'100%', padding:'5px 7px', borderRadius:'6px', fontSize:'10px', backgroundColor:'var(--dash-surface)', color:'#EF4444', border:'1px solid rgba(239,68,68,0.2)', cursor:'pointer' }}>
              <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
              전체 비우기
            </button>
          </div>
        </aside>

      </div>
    </div>
  );
}

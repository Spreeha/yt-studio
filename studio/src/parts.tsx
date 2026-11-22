import React from 'react';
import {AbsoluteFill, Easing, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {brand} from './brand';

export type Caption = {text: string; startMs: number; endMs: number};

const c = brand.colors;

export const Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const rise = spring({frame, fps, config: {damping: 200}});
  const bar = spring({frame: frame - 6, fps, config: {damping: 200}});
  const out = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <AbsoluteFill style={{background: c.bg, justifyContent: 'center', alignItems: 'center', opacity: out}}>
      <div style={{transform: `translateY(${(1 - rise) * 40}px)`, opacity: rise, textAlign: 'center'}}>
        <div style={{fontFamily: brand.font, fontSize: 110, fontWeight: 800, color: c.text, letterSpacing: -2}}>
          {brand.name}
        </div>
        <div style={{height: 10, width: 520 * bar, background: c.accent, margin: '24px auto 0', borderRadius: 5}} />
      </div>
    </AbsoluteFill>
  );
};

export const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const inn = spring({frame, fps, config: {damping: 200}});
  return (
    <AbsoluteFill style={{background: c.bg, justifyContent: 'center', alignItems: 'center'}}>
      <div style={{opacity: inn, textAlign: 'center', fontFamily: brand.font}}>
        <div style={{fontSize: 96, fontWeight: 800, color: c.text, letterSpacing: -2}}>{brand.name}</div>
        <div style={{fontSize: 40, color: c.muted, marginTop: 24}}>{brand.outroLine}</div>
      </div>
    </AbsoluteFill>
  );
};

export const LowerThird: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const inn = spring({frame, fps, config: {damping: 200}});
  const out = spring({frame: frame - (durationInFrames - 15), fps, config: {damping: 200}});
  const x = (1 - inn + out) * -700;
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', padding: '0 0 110px 90px'}}>
      <div style={{transform: `translateX(${x}px)`, display: 'flex', alignItems: 'stretch', fontFamily: brand.font}}>
        <div style={{width: 10, background: c.accent, borderRadius: 4}} />
        <div style={{background: 'rgba(14,17,22,0.88)', padding: '18px 30px', borderRadius: '0 10px 10px 0'}}>
          <div style={{fontSize: 52, fontWeight: 700, color: c.text}}>{brand.host}</div>
          <div style={{fontSize: 30, color: c.muted, marginTop: 4}}>
            {brand.role} · {brand.name}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// Group word timings into on-screen lines: break on long pauses, sentence ends, or the word limit.
const paginate = (caps: Caption[], maxWords: number) => {
  const pages: Caption[][] = [];
  let cur: Caption[] = [];
  caps.forEach((w, i) => {
    const prev = caps[i - 1];
    const pause = prev ? w.startMs - prev.endMs > 500 : false;
    const sentence = prev ? /[.?!]$/.test(prev.text) : false;
    if (cur.length && (cur.length >= maxWords || pause || sentence)) {
      pages.push(cur);
      cur = [];
    }
    cur.push(w);
  });
  if (cur.length) pages.push(cur);
  return pages;
};

// Caption styles.
// short: bold sentence-case lines in the lower middle of a vertical frame, the spoken word in yellow.
// long:  white lines at the bottom of a landscape frame, the spoken word on a purple highlight.
// True while a stacked (two-person) layout is on screen; captions and the title card move to the seam.
export const inStacked = (sec: number, ranges?: [number, number][]) => (ranges ?? []).some(([a, b]) => sec >= a && sec < b);

export const Captions: React.FC<{captions: Caption[]; mode: 'short' | 'long'; stacked?: [number, number][]}> = ({captions, mode, stacked}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = (frame / fps) * 1000;
  const short = mode === 'short';
  const pages = React.useMemo(() => paginate(captions, short ? 6 : 12), [captions, short]);
  const page = pages.find((p, i) => {
    const next = pages.at(i + 1);
    const end = next && next[0].startMs - p[p.length - 1].endMs < 300 ? next[0].startMs : p[p.length - 1].endMs + 200;
    return t >= p[0].startMs && t < end;
  });
  if (!page) return null;
  return (
    <AbsoluteFill
      style={
        short && inStacked(t / 1000, stacked)
          ? {justifyContent: 'flex-start', alignItems: 'center', paddingTop: 985}
          : {justifyContent: 'flex-end', alignItems: 'center', paddingBottom: short ? 560 : 48}
      }
    >
      <div
        style={{
          fontFamily: `${brand.type.caption}, ${brand.font}`,
          fontWeight: short ? brand.type.captionWeight : Math.min(brand.type.captionWeight, 800),
          fontSize: short ? 60 : 40,
          textAlign: 'center',
          maxWidth: short ? 900 : 1300,
          lineHeight: 1.25,
          color: c.text,
          textShadow: '0 3px 14px rgba(0,0,0,0.9), 0 0 3px rgba(0,0,0,0.9)',
        }}
      >
        {page.map((w, i) => {
          const next = page.at(i + 1);
          const active = t >= w.startMs && t < (next ? Math.min(w.endMs + 80, next.startMs) : w.endMs + 80);
          return (
            <React.Fragment key={`${w.startMs}-${i}`}>
              <span
                style={{
                  padding: short ? 0 : '0 0.12em',
                  borderRadius: 6,
                  color: short && active ? c.accent : c.text,
                  background: !short && active ? brand.colors.highlight : 'transparent',
                }}
              >
                {w.text}
              </span>{' '}
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// Small channel-name tag in the top-left corner, on every frame.
export const Tag: React.FC<{scale?: number}> = ({scale = 1}) => (
  <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'flex-start'}}>
    <div style={{background: 'rgba(0,0,0,0.85)', color: '#fff', fontFamily: brand.tagFont, fontSize: 26 * scale, padding: `${6 * scale}px ${14 * scale}px`}}>
      {brand.name}
    </div>
  </AbsoluteFill>
);

// Title card: dark box with the video's title, for the first beat of a Short.
export const TitleCard: React.FC<{text: string; stacked?: boolean}> = ({text, stacked}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const o = interpolate(frame, [0, 5, durationInFrames - 6, durationInFrames], [0, 1, 1, 0], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: stacked ? 975 : 860, opacity: o}}>
      <div style={{background: 'rgba(0,0,0,0.82)', color: '#fff', fontFamily: `${brand.type.title}, ${brand.font}`, fontWeight: brand.type.titleWeight, textTransform: brand.type.titleCaps ? 'uppercase' : 'none', letterSpacing: brand.type.titleCaps ? 1 : 0, fontSize: brand.type.titleCaps ? 66 : 54, lineHeight: 1.15, padding: '20px 34px', maxWidth: 860, textAlign: 'center'}}>
        {text}
      </div>
    </AbsoluteFill>
  );
};

// Cards that pop in over the video for a few seconds. Times are seconds in the rough cut.
// logo:    product or company card (logo image if one is in assets/, else the name), above the captions.
// section: handwritten-style chapter card, top centre (long-form).
// stat:    a big number that counts up, with a label.        {"kind":"stat","value":2.7,"suffix":"T","label":"parameters"}
// compare: two to four animated bars.                       {"kind":"compare","text":"per million tokens","items":[{"label":"Kimi K3","value":15,"display":"$15"},{"label":"Rival","value":50,"display":"$50"}]}
// list:    items tick in one by one.                        {"kind":"list","text":"What changes","items":["Cost","Speed","Lock-in"]}
// zoom:    a quick punch-in on the video for emphasis.       {"kind":"zoom","scale":1.12}
// sticker: a small tilted tag for a light-hearted beat.     {"kind":"sticker","text":"plot twist"}
export type CardItem = string | {label: string; value?: number; display?: string};
export type CardSpec = {
  at: number;
  dur?: number;
  text?: string;
  img?: string;
  kind?: 'logo' | 'section' | 'stat' | 'compare' | 'list' | 'zoom' | 'sticker';
  value?: number;
  prefix?: string;
  suffix?: string;
  label?: string;
  items?: CardItem[];
  scale?: number;
};

const panel = (vertical: boolean): React.CSSProperties =>
  vertical
    ? {justifyContent: 'flex-start', alignItems: 'center', paddingTop: 230}
    : {justifyContent: 'flex-start', alignItems: 'flex-end', padding: '110px 70px 0 0'};
const box: React.CSSProperties = {background: 'rgba(10,12,16,0.9)', borderRadius: 22, padding: '26px 34px', boxShadow: '0 10px 40px rgba(0,0,0,0.35)'};
const capFont = () => `${brand.type.caption}, ${brand.font}`;
const titleFont = () => `${brand.type.title}, ${brand.font}`;

const Stat: React.FC<{card: CardSpec; vertical: boolean; inn: number; frame: number; fps: number}> = ({card, vertical, inn, frame, fps}) => {
  const v = card.value ?? 0;
  const decimals = (String(v).split('.')[1] ?? '').length;
  const p = interpolate(frame, [0, Math.round(0.8 * fps)], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  return (
    <div style={{...box, transform: `scale(${0.8 + 0.2 * inn})`, opacity: inn, textAlign: 'center', minWidth: vertical ? 560 : 440}}>
      <div style={{fontFamily: titleFont(), fontWeight: brand.type.titleWeight, fontSize: vertical ? 150 : 110, lineHeight: 1, color: c.accent, letterSpacing: brand.type.titleCaps ? 1 : -2}}>
        {card.prefix ?? ''}{(v * p).toFixed(decimals)}{card.suffix ?? ''}
      </div>
      {card.label || card.text ? (
        <div style={{fontFamily: capFont(), fontWeight: 800, fontSize: vertical ? 46 : 34, color: c.text, marginTop: 10}}>{card.label ?? card.text}</div>
      ) : null}
    </div>
  );
};

const Compare: React.FC<{card: CardSpec; vertical: boolean; inn: number; frame: number; fps: number}> = ({card, vertical, inn, frame, fps}) => {
  const items = (card.items ?? []).map((it) => (typeof it === 'string' ? {label: it, value: 1} : it));
  const max = Math.max(...items.map((i) => i.value ?? 0), 1);
  const w = vertical ? 600 : 520;
  return (
    <div style={{...box, opacity: inn, width: w + 68}}>
      {card.text ? <div style={{fontFamily: capFont(), fontWeight: 800, fontSize: vertical ? 38 : 28, color: c.muted, marginBottom: 18}}>{card.text}</div> : null}
      {items.map((it, i) => {
        const grow = spring({frame: frame - 6 - i * 6, fps, config: {damping: 16}});
        const first = i === 0;
        return (
          <div key={i} style={{marginBottom: 18}}>
            <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: capFont(), fontWeight: 800, fontSize: vertical ? 40 : 30, color: c.text, marginBottom: 8}}>
              <span>{it.label}</span>
              <span style={{color: first ? c.accent : c.text}}>{it.display ?? it.value}</span>
            </div>
            <div style={{height: vertical ? 30 : 22, borderRadius: 15, background: 'rgba(255,255,255,0.12)'}}>
              <div style={{height: '100%', borderRadius: 15, width: `${(100 * grow * (it.value ?? 0)) / max}%`, background: first ? c.accent : 'rgba(255,255,255,0.75)'}} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

const List: React.FC<{card: CardSpec; vertical: boolean; inn: number; frame: number; fps: number}> = ({card, vertical, inn, frame, fps}) => {
  const items = (card.items ?? []).map((it) => (typeof it === 'string' ? it : it.label));
  const each = Math.max(8, Math.round((((card.dur ?? 3.5) * fps) * 0.6) / Math.max(1, items.length)));
  return (
    <div style={{...box, opacity: inn, minWidth: vertical ? 600 : 460}}>
      {card.text ? <div style={{fontFamily: titleFont(), fontWeight: brand.type.titleWeight, textTransform: brand.type.titleCaps ? 'uppercase' : 'none', fontSize: vertical ? 50 : 38, color: c.text, marginBottom: 16}}>{card.text}</div> : null}
      {items.map((t, i) => {
        const pop = spring({frame: frame - 4 - i * each, fps, config: {damping: 14, mass: 0.5}});
        return (
          <div key={i} style={{display: 'flex', alignItems: 'center', gap: 16, opacity: pop, transform: `translateX(${(1 - pop) * -40}px)`, marginBottom: 12}}>
            <div style={{width: vertical ? 44 : 34, height: vertical ? 44 : 34, borderRadius: 10, background: c.accent, color: c.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: capFont(), fontWeight: 900, fontSize: vertical ? 30 : 24}}>
              {i + 1}
            </div>
            <div style={{fontFamily: capFont(), fontWeight: 800, fontSize: vertical ? 44 : 32, color: c.text}}>{t}</div>
          </div>
        );
      })}
    </div>
  );
};

const Sticker: React.FC<{card: CardSpec; vertical: boolean; inn: number}> = ({card, vertical, inn}) => (
  <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'flex-end', padding: vertical ? '300px 60px 0 0' : '90px 80px 0 0'}}>
    <div style={{transform: `rotate(${-6 + 2 * (1 - inn)}deg) scale(${0.6 + 0.4 * inn})`, opacity: Math.min(1, inn * 1.5), background: c.accent, color: c.bg, fontFamily: capFont(), fontWeight: 900, fontSize: vertical ? 50 : 38, padding: '10px 24px', borderRadius: 12, boxShadow: '0 8px 24px rgba(0,0,0,0.35)'}}>
      {card.text}
    </div>
  </AbsoluteFill>
);

// Punch-in zoom on the video itself, driven by the zoom cards. Wrap the video with it.
export const ZoomWrap: React.FC<{cards: CardSpec[]; children: React.ReactNode}> = ({cards, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  let s = 1;
  for (const z of cards) {
    if (z.kind !== 'zoom') continue;
    const a = Math.round(z.at * fps), b = Math.round((z.at + (z.dur ?? 1.5)) * fps);
    if (frame < a || frame > b) continue;
    const k = Math.min(interpolate(frame, [a, a + 5], [0, 1], {extrapolateRight: 'clamp'}), interpolate(frame, [b - 6, b], [1, 0], {extrapolateLeft: 'clamp'}));
    s = Math.max(s, 1 + ((z.scale ?? 1.12) - 1) * k);
  }
  return <AbsoluteFill style={{transform: `scale(${s})`}}>{children}</AbsoluteFill>;
};

export const Card: React.FC<{card: CardSpec; vertical: boolean}> = ({card, vertical}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const inn = spring({frame, fps, config: {damping: 14, mass: 0.6}});
  const out = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {extrapolateLeft: 'clamp'});
  if (card.kind === 'zoom') return null;
  if (card.kind === 'sticker') return <AbsoluteFill style={{opacity: out}}><Sticker card={card} vertical={vertical} inn={inn} /></AbsoluteFill>;
  if (card.kind === 'stat' || card.kind === 'compare' || card.kind === 'list') {
    const G = card.kind === 'stat' ? Stat : card.kind === 'compare' ? Compare : List;
    return (
      <AbsoluteFill style={{...panel(vertical), opacity: out}}>
        <G card={card} vertical={vertical} inn={inn} frame={frame} fps={fps} />
      </AbsoluteFill>
    );
  }
  if (card.kind === 'section') {
    return (
      <AbsoluteFill style={{justifyContent: 'flex-start', alignItems: 'center', paddingTop: vertical ? 220 : 36, opacity: out}}>
        <div style={{transform: `scale(${0.9 + 0.1 * inn})`, opacity: inn, background: 'rgba(30,30,30,0.9)', color: '#fff', fontFamily: brand.handFont, fontSize: vertical ? 54 : 40, padding: '10px 28px', borderRadius: 6}}>
          {card.text}
        </div>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: vertical ? 700 : 170, opacity: out}}>
      <div style={{transform: `scale(${0.85 + 0.15 * inn})`, opacity: inn, display: 'flex', alignItems: 'center', gap: 18, background: 'rgba(0,0,0,0.88)', padding: '16px 30px', borderRadius: 16}}>
        {card.img ? <Img src={staticFile(card.img)} style={{height: vertical ? 72 : 56, width: 'auto', borderRadius: 10}} /> : null}
        <div style={{fontFamily: `${brand.type.caption}, ${brand.font}`, fontWeight: 800, fontSize: vertical ? 60 : 46, color: '#fff', letterSpacing: 0.5}}>{card.text}</div>
      </div>
    </AbsoluteFill>
  );
};

export const Cards: React.FC<{cards: CardSpec[]; vertical: boolean}> = ({cards, vertical}) => {
  const {fps} = useVideoConfig();
  return (
    <>
      {cards.map((card, i) => (
        <Sequence key={i} from={Math.max(0, Math.round(card.at * fps))} durationInFrames={Math.max(15, Math.round((card.dur ?? (card.kind === 'list' || card.kind === 'compare' ? 3.5 : 2.5)) * fps))} name={`${card.kind ?? 'logo'}: ${card.text ?? card.label ?? ''}`}>
          <Card card={card} vertical={vertical} />
        </Sequence>
      ))}
    </>
  );
};

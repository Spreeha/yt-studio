import React from 'react';
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  Composition,
  Img,
  OffthreadVideo,
  Sequence,
  Still,
  staticFile,
} from 'remotion';
import {brand} from './brand';
import {Caption, CardSpec, Cards, Captions, Intro, LowerThird, Outro, Tag, TitleCard, ZoomWrap, inStacked} from './parts';

const FPS = 30;
const c = brand.colors;

const Placeholder: React.FC<{label: string}> = ({label}) => (
  <AbsoluteFill style={{background: '#222', justifyContent: 'center', alignItems: 'center', color: '#888', fontSize: 48, fontFamily: brand.font}}>
    {label}
  </AbsoluteFill>
);

// ---------- Main: intro, your rough cut, lower third, optional captions, outro ----------
export type MainProps = {
  src: string;
  durationSec: number;
  captions: Caption[];
  burnCaptions: boolean;
  intro: boolean;
  lowerThirdAt: number;
  cards: CardSpec[];
};

const introFrames = (p: MainProps) => (p.intro ? Math.round(brand.introSec * FPS) : 0);
const bodyFrames = (p: MainProps) => Math.max(1, Math.ceil(p.durationSec * FPS));
const outroFrames = Math.round(brand.outroSec * FPS);

export const Main: React.FC<MainProps> = (p) => {
  const intro = introFrames(p);
  const body = bodyFrames(p);
  return (
    <AbsoluteFill style={{background: c.bg}}>
      {intro > 0 && (
        <Sequence durationInFrames={intro} name="Intro">
          <Intro />
        </Sequence>
      )}
      <Sequence from={intro} durationInFrames={body} name="Video">
        <ZoomWrap cards={p.cards ?? []}>
          {p.src ? <OffthreadVideo src={staticFile(p.src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} /> : <Placeholder label="Run tools/props.py main <slug>" />}
        </ZoomWrap>
        {p.lowerThirdAt >= 0 && (
          <Sequence from={Math.round(p.lowerThirdAt * FPS)} durationInFrames={4 * FPS} name="Lower third">
            <LowerThird />
          </Sequence>
        )}
        <Cards cards={p.cards ?? []} vertical={false} />
        {p.burnCaptions && <Captions captions={p.captions} mode="long" />}
        <Tag />
      </Sequence>
      <Sequence from={intro + body} durationInFrames={outroFrames} name="Outro">
        <Outro />
      </Sequence>
    </AbsoluteFill>
  );
};

const mainMeta: CalculateMetadataFunction<MainProps> = ({props}) => ({
  durationInFrames: introFrames(props) + bodyFrames(props) + outroFrames,
});

// ---------- Short: vertical clip, word-pop captions, hook card for the first 2.5 s ----------
export type ShortProps = {src: string; durationSec: number; captions: Caption[]; hook: string; cards: CardSpec[]; stacked?: [number, number][]};

export const Short: React.FC<ShortProps> = (p) => (
  <AbsoluteFill style={{background: '#000'}}>
    <ZoomWrap cards={p.cards ?? []}>
      {p.src ? <OffthreadVideo src={staticFile(p.src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} /> : <Placeholder label="Run tools/props.py short <slug> <short>" />}
    </ZoomWrap>
    <Cards cards={p.cards ?? []} vertical />
    <Captions captions={p.captions} mode="short" stacked={p.stacked} />
    {p.hook && (
      <Sequence durationInFrames={Math.round(2.5 * FPS)} name="Title card">
        <TitleCard text={p.hook} stacked={inStacked(0, p.stacked)} />
      </Sequence>
    )}
    <Tag scale={2.2} />
  </AbsoluteFill>
);

const shortMeta: CalculateMetadataFunction<ShortProps> = ({props}) => ({
  durationInFrames: Math.max(1, Math.ceil(props.durationSec * FPS)),
});

// ---------- Thumbnail: a frame of you, the /yt-package text, the accent bar ----------
export type ThumbProps = {frame: string; text: string; accent: string};

export const Thumbnail: React.FC<ThumbProps> = ({frame, text, accent}) => {
  // Words wrapped in *stars* get the accent colour: "Your pager is *lying*"
  const parts = text.split(/(\*[^*]+\*)/g).filter(Boolean);
  return (
    <AbsoluteFill style={{background: c.bg}}>
      {frame && <Img src={staticFile(frame)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />}
      <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(14,17,22,0.92) 0%, rgba(14,17,22,0.6) 45%, rgba(14,17,22,0) 70%)'}} />
      <AbsoluteFill style={{justifyContent: 'center', padding: '0 0 0 64px'}}>
        <div style={{width: 680, fontFamily: `${brand.type.title}, ${brand.font}`, fontWeight: brand.type.titleWeight, textTransform: brand.type.titleCaps ? 'uppercase' : 'none', fontSize: brand.type.titleCaps ? 124 : 104, lineHeight: 1.02, color: c.text, letterSpacing: brand.type.titleCaps ? 0 : -2}}>
          {parts.map((s, i) =>
            s.startsWith('*') ? (
              <span key={i} style={{color: accent || c.accent}}>{s.slice(1, -1)}</span>
            ) : (
              <span key={i}>{s}</span>
            ),
          )}
        </div>
        <div style={{width: 140, height: 12, background: accent || c.accent, borderRadius: 6, marginTop: 28}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Main"
      component={Main}
      fps={FPS}
      width={1920}
      height={1080}
      durationInFrames={10 * FPS}
      defaultProps={{src: '', durationSec: 5, captions: [], burnCaptions: true, intro: true, lowerThirdAt: 1, cards: [{at: 1.5, text: 'Section one', kind: 'section'}, {at: 3, text: 'KIMI K3', kind: 'logo'}]}}
      calculateMetadata={mainMeta}
    />
    <Composition
      id="Short"
      component={Short}
      fps={FPS}
      width={1080}
      height={1920}
      durationInFrames={5 * FPS}
      defaultProps={{src: '', durationSec: 5, captions: [], hook: 'The AI Race Just Got a New Player', cards: [{at: 2.6, text: 'KIMI K3', kind: 'logo'}]}}
      calculateMetadata={shortMeta}
    />
    <Still
      id="Thumbnail"
      component={Thumbnail}
      width={1280}
      height={720}
      defaultProps={{frame: '', text: 'Three to five *words*', accent: ''}}
    />
  </>
);

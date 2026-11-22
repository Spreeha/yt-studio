// The look of every video. Your channel's own values (name, host, colours, font style, timings)
// live in brand.json at the top of the studio folder; edit that file, not this one.
// Three font styles. Set "style" in brand.json to switch every caption, title card and thumbnail at once.
//   clean:   Montserrat ExtraBold captions, Montserrat Black titles. Modern creator look, very legible.
//   punchy:  Poppins captions, Anton (tall condensed caps) titles. News-explainer energy, big thumbnail text.
//   classic: Inter Black captions, Playfair Display serif titles. Softer, more editorial.
import cfg from '../../brand.json';

const styles = {
  clean: {caption: 'Montserrat', captionWeight: 800, title: 'Montserrat', titleWeight: 900, titleCaps: false},
  punchy: {caption: 'Poppins', captionWeight: 800, title: 'Anton', titleWeight: 400, titleCaps: true},
  classic: {caption: 'Inter', captionWeight: 900, title: 'Playfair Display', titleWeight: 700, titleCaps: false},
} as const;
type StyleName = keyof typeof styles;
const style: StyleName = cfg.style in styles ? (cfg.style as StyleName) : 'clean';

export const brand = {
  style,
  type: styles[style],
  name: cfg.name,
  host: cfg.host,
  role: cfg.role,
  outroLine: cfg.outroLine,
  colors: {
    bg: cfg.colors.bg,
    text: cfg.colors.text,
    muted: cfg.colors.muted,
    accent: cfg.colors.accent, // the highlighted word in Shorts captions
    highlight: cfg.colors.highlight, // the word highlight in long-form captions
  },
  font: 'Inter, "SF Pro Display", -apple-system, Helvetica, Arial, sans-serif',
  tagFont: '"Playfair Display", Georgia, serif', // corner tag
  handFont: '"Bradley Hand", "Marker Felt", "Comic Sans MS", cursive', // long-form section cards (Mac fonts)
  introSec: cfg.introSec,
  outroSec: cfg.outroSec, // YouTube end screens need at least 5 s at the end
};

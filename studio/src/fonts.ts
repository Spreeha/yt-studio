import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';

// Fonts ship inside the kit (studio/public/fonts), so renders never depend on the internet.
const files: [string, string, string][] = [
  ['Anton', '400', 'Anton-400.woff2'],
  ['Montserrat', '800', 'Montserrat-800.woff2'],
  ['Montserrat', '900', 'Montserrat-900.woff2'],
  ['Inter', '800', 'Inter-800.woff2'],
  ['Inter', '900', 'Inter-900.woff2'],
  ['Poppins', '700', 'Poppins-700.woff2'],
  ['Poppins', '800', 'Poppins-800.woff2'],
  ['Playfair Display', '700', 'PlayfairDisplay-700.woff2'],
];

for (const [family, weight, file] of files) {
  loadFont({family, url: staticFile(`fonts/${file}`), weight});
}

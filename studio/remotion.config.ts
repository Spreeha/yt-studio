import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(95); // default 80 softens fine detail; 95 is visually lossless
Config.setCrf(16); // H.264 quality for the final file (lower = better; Remotion's default is 18)
Config.setOverwriteOutput(true);
Config.setEntryPoint('./src/index.ts');

# Credits

| Part | Where it comes from | Licence | In this repo? |
| --- | --- | --- | --- |
| youtube-agent-skill (the `yt-*` pack skills: yt-script, yt-package, yt-seo, yt-shorts, yt-edit, yt-chapters, yt-viral and others) | [Jakeschincariol/youtube-agent-skill](https://github.com/Jakeschincariol/youtube-agent-skill), pinned to commit a2feb21 | MIT, Copyright (c) 2026 Jake Schincariol | No. `setup.sh` clones it into `.claude/vendor/` |
| YuNet face detector (`tools/models/face_detection_yunet_2023mar.onnx`) | [opencv/opencv_zoo](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) | MIT, Copyright (c) 2020 Shiqi Yu; full text in `tools/models/LICENSE-YuNet.txt` | Yes |
| Fonts: Anton, Inter, Montserrat, Playfair Display, Poppins (`studio/public/fonts/`) | Google Fonts, via Fontsource | SIL Open Font License 1.1; notices in `studio/public/fonts/OFL-*.txt` | Yes |
| Remotion and @remotion/fonts | [remotion.dev](https://www.remotion.dev) (installed by npm) | Remotion License: free for individuals and companies of up to 3 people; larger companies need a [company licence](https://www.remotion.dev/license) | No (npm) |
| FFmpeg, whisper.cpp, Whisper model ggml-small.en | Homebrew and Hugging Face (installed by setup.sh) | FFmpeg: LGPL/GPL; whisper.cpp: MIT; Whisper weights: MIT | No |
| OpenCV (opencv-python-headless) | PyPI (installed by setup.sh) | Apache 2.0 | No |

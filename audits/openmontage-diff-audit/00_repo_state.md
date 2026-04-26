# Repo State

- current branch: `main`
- origin URL: `https://github.com/Snaxxwax/OpenMontage.git`
- upstream URL: `https://github.com/calesthio/OpenMontage.git`
- chosen upstream comparison base: `upstream/main`
- latest upstream commit SHA: `386338c92b0d20120176e1929616c25683746d3e`
- current HEAD SHA: `e2df3effaaec4eee3eb5f1d448c0aaa084f40d73`
- merge base (HEAD vs upstream): `0efed7427c7c106f94ce1d07f4e842cba96e5f36`
- whether there are staged changes: **no** (0 files)
- whether there are unstaged changes: **yes** (8 files)
- whether there are untracked files: **yes** (7 files)
- ahead/behind origin (origin/main): ahead=0 behind=0
- ahead/behind upstream (upstream/main): ahead=1 behind=7

## Commands + Output

### git rev-parse HEAD

```
e2df3effaaec4eee3eb5f1d448c0aaa084f40d73
```

### git rev-parse upstream/main

```
386338c92b0d20120176e1929616c25683746d3e
```

### git merge-base HEAD upstream/main

```
0efed7427c7c106f94ce1d07f4e842cba96e5f36
```

### git status --short

```
 M tools/analysis/audio_energy.py
 M tools/analysis/audio_probe.py
 M tools/analysis/composition_validator.py
 M tools/audio/acestep_music.py
 M tools/base_tool.py
 M tools/capture/screen_recorder.py
 M tools/video/video_stitch.py
 M tools/video/video_trimmer.py
?? audits/
?? pipelines/
?? server.pid
```

### git branch -vv

```
* main e2df3ef [origin/main] feat: add ComfyUI integration, Asymmetric channel strategy, and tool updates
```

### git log --oneline --decorate --graph --all -n 40

```
* e2df3ef (HEAD -> main, origin/main, origin/HEAD) feat: add ComfyUI integration, Asymmetric channel strategy, and tool updates
| * 386338c (upstream/main) feat(remotion): upgrade cinematic TitleCard + add new scene components
| *   578d77e Merge pull request #47 from itsuzef/fix/architecture-hyperframes-package-name
| |\  
| | * 36c921e docs(architecture): fix HyperFrames npm package name
| * |   676aec6 Merge pull request #46 from itsuzef/fix/source-media-review-get-tool
| |\ \  
| | * | f53f078 fix(source_media_review): use registry.get() not get_tool()
| | |/  
| * / d88b048 Merge pull request #45 from itsuzef/fix/seedance-upload-image-name
|/| | 
| |/  
| * 099cde3 fix(seedance): correct upload_image_fal call name
|/  
| * bc27cfc (origin/fix/local-gpu-gating) Fix local GPU gating and docs
|/  
* 0efed74 video-compose: catch TTS punctuation leaks in final review
* b6ce481 hyperframes skill: document the six gotchas hard-earned on the first production
* b4f7ec4 hyperframes: add HTML/CSS/GSAP as a parallel composition runtime
* 9e17263 video-gen: prefer Seedance 2.0 on every gateway that supports it
* 16791a3 video-gen: adopt Seedance 2.0 as preferred premium default
* 4822454 pipelines: require meta/animation-runtime-selector in animation-heavy pipelines
* a37b581 skills: adopt GSAP Layer 3 + Layer 2 animation-runtime routing
* a36ce99 screen-demo: add synthetic-terminal mode via Remotion TerminalScene
* 33ba377 docmontage: add children's fantasy content routing + CaptionOverlayOnly composition
* 55c08ac sources: add 11 stock source adapters, expand catalog from 5 to 16 providers
* a06d4c2 readme: add YouTube channel badge and subscribe CTA after showcase
* ddc8901 cleanup: register HeroTitle composition, harden gitignore
* 0999ead docmontage: add direct_clip_search tool for fast provider-agnostic clip acquisition
*   61fa591 Merge pull request #21 from calesthio/codex/fix-demo-and-requirements
|\  
| * 1f2ed2f (upstream/codex/fix-demo-and-requirements) Fix demo rendering and baseline requirements
|/  
* cf3527f docmontage: end-tag overlay default + Chirp 3 HD as default TTS voice
* a8d1ebd docmontage: corpus builder hardening from P1 + P2 audit observations
* b80b7a0 docmontage: make music + end-tag mandatory, add Remotion EndTag component
* de94d4d Documentary Montage hardening plus governance fixes
* 44baede Add documentary-montage pipeline for retrieval-first motion-clip montage
| * 43f6c5a (origin/channel-brand) Add Asymmetric channel brand, pipeline fixes, and new components
| * 2b6a725 Add ComfyUI/Fish Speech tools, map components, new schemas, and pipeline skill updates
|/  
*   e815126 Merge pull request #14 from calesthio/codex/fix-fal-provider-bias
|\  
| * a919fde (upstream/codex/fix-fal-provider-bias) Remove fal-first provider guidance
|/  
*   dfae315 Merge pull request #12 from calesthio/add-higgsfield-and-update-runway
|\  
| * 4f682c8 (upstream/add-higgsfield-and-update-runway) Add Higgsfield provider and update Runway to v0.2.0
|/  
* b1a078b Add screen capture tools with FFmpeg and Cap dual-provider system
* d5e754b Add Chirp 3 HD and Journey voice support to Google TTS
* 1b7e13d Fix Remotion-first rendering docs and post-render verification gaps
* 5a10ef1 Update README social links
* 7ca04e6 Add Grok media providers and improve selector routing
```

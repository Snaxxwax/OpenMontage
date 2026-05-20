# Asset Director (svg-character)

Read `skills/pipelines/character-animation/asset-director.md` and follow it, with
one important change:

**Character assets are already built.** The `character_generation` stage has already
written `character.svg`, `rig_manifest.json`, and `pose_library.json` to
`projects/<name>/assets/characters/<id>/`. Do not regenerate the character.

Your job in this stage is backgrounds, props, TTS audio, and music only:
- Use `image_selector` for scene backgrounds and props
- Use `tts_selector` for narration (if script has VO)
- Use `music_gen` or `music_library/` for background music
- Call `character_rig_renderer` with `svg_path` pointing to the already-written
  `character.svg` to build the HyperFrames composition package

Pass `svg_path: projects/<name>/assets/characters/<id>/character.svg` to
`character_rig_renderer`. Do not omit this — without it the renderer uses placeholders.

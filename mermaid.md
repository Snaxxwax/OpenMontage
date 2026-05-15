# OpenMontage Data Flow

This diagram set summarizes how data moves through this repo. OpenMontage is instruction-driven: the agent is the orchestrator, while Python modules provide tool execution, validation, persistence, and render adapters.

## Repo-Wide Production Loop

```mermaid
flowchart TD
    request[User production request] --> preflight[Preflight and tool discovery]
    preflight --> registry[tools/tool_registry.py]
    registry --> contracts[Tool contracts from tools/base_tool.py]
    contracts --> capability{Required capabilities available?}

    capability -- no --> blocker[Report blocker or request provider approval]
    capability -- yes --> manifest[Read pipeline_defs/pipeline-name.yaml]
    manifest --> director[Read skills/pipelines/pipeline-name/stage-director.md]
    director --> inputs[Gather required artifacts from Artifact Bus]
    inputs --> execute[Execute stage: agent work or BaseTool call]
    execute --> validate[Validate output against schemas/artifacts/*.schema.json]
    validate --> persist[Persist stage artifacts]
    persist --> checkpoint[Record run checkpoint / manifest]
    checkpoint --> gate{Human checkpoint or gate failure?}
    gate -- yes --> human[Pause for approval or remediation]
    gate -- no --> next{More stages?}
    next -- yes --> director
    next -- no --> done[Finished production handoff]

    persist --> bus[(shared_studio/projects/project_slug/)]
    checkpoint --> bus
```

## Artifact Bus Layout

```mermaid
flowchart LR
    project[(shared_studio/projects/project_slug/)]
    project --> artifacts[artifacts: schema-valid JSON and YAML]
    project --> receipts[receipts: clip-use and tool receipts]
    project --> clips[clips: approved local media]
    project --> audio[assets/audio: narration and mixes]
    project --> renders[renders: HTML, MP4, render reports]
    project --> qc[qc: gate receipts, probe logs, QC reports]
    project --> manifest[run_manifest.json]

    schemas[schemas/artifacts/*.schema.json] --> artifacts
    gates[scripts/asymmetric_gate.py] --> qc
    runlib[lib/artifact_bus.py] --> project
    runner[lib/pipeline_run.py] --> manifest
```

## Asymmetric Source-Commentary Pipeline

```mermaid
flowchart TD
    topic[Episode topic] --> greenlight[greenlight]
    greenlight --> ag[asymmetric_greenlight.json]

    ag --> source_discovery[source_discovery]
    source_discovery --> sqp[source_query_plan.json]
    source_discovery --> scm[source_candidate_manifest.json]

    scm --> youtube[youtube_source_discovery]
    youtube --> ysm[youtube_source_manifest.json]

    scm --> capture[capture_plan]
    ysm --> capture
    capture --> scp[source_capture_plan.json]

    ag --> claim_map[claim_map]
    scm --> claim_map
    claim_map --> acm[asymmetric_claim_map.json]

    acm --> triage[evidence_triage]
    scp --> triage
    ysm --> triage
    triage --> ecm[evidence_candidate_manifest.json]
    triage --> rrm[rights_risk_manifest.json]

    acm --> script[script]
    ecm --> script
    rrm --> script
    script --> narrative[Narration/script artifact or markdown]

    narrative --> rhythm[visual_rhythm]
    ecm --> rhythm
    rhythm --> vrp[visual_rhythm_plan.json]

    ecm --> approval[segment_approval]
    rrm --> approval
    vrp --> approval
    approval --> ssam[source_segment_approval_manifest.json]

    ssam --> render_gate{render-readiness gate}
    scp --> render_gate
    vrp --> render_gate
    render_gate --> acquisition[acquisition]
    acquisition --> clips[clips: approved extracts and source cards]
    acquisition --> receipts[receipts: local tool receipts]

    clips --> edit[edit]
    receipts --> edit
    narrative --> edit
    edit --> editplan[source_commentary_edit_plan or render inputs]

    editplan --> compose[compose]
    clips --> compose
    compose --> render_report[source_commentary_render_report or render_report.json]
    compose --> mp4[renders/episode.mp4]

    render_report --> qc[qc]
    mp4 --> qc
    qc --> qc_report[source_commentary_qc_report.json]
    qc_report --> final{operator approval}
```

## Evidence-Locked Source-Commentary Flow

```mermaid
flowchart TD
    research[research_brief.json] --> claim[narration_claim_map.json]
    claim --> candidates[source_candidate_manifest.json]
    candidates --> transcripts[transcript_index.json]
    claim --> evidence[evidence_candidate_manifest.json]
    transcripts --> evidence
    evidence --> gate[clip_use_gate]
    gate --> receipts[clip_use_receipts.json / receipts/*.json]

    receipts --> acquisition[clip_acquisition]
    acquisition --> extracted[extracted_clip_manifest.json]
    extracted --> media_qc[media_qc]
    media_qc --> approved[approved_clip_manifest.json]
    approved --> edit[source_commentary_edit_plan.json]
    claim --> edit
    edit --> compose[video_compose + audio_mixer]
    approved --> compose
    compose --> render[source_commentary_render_report.json]
    render --> final_qc[source_commentary_qc_report.json]
    research --> final_qc

    gate -. blocks without approval .-> acquisition
    approved -. required before edit .-> edit
    edit -. required before render .-> compose
```

## Runtime and Tool Data Flow

```mermaid
flowchart LR
    stage[Pipeline stage director] --> registry[ToolRegistry.discover]
    registry --> selected[Selected BaseTool]

    selected --> source_tools[Source tools: transcript_fetcher, youtube_metadata_adapter, clip_search]
    selected --> acquisition_tools[Acquisition tools: video_downloader, video_trimmer, clip_acquisition_adapter]
    selected --> qc_tools[Analysis tools: video_analyzer, frame_sampler, visual_qa, media_qc_adapter]
    selected --> audio_tools[Audio tools: fish_speech_tts, tts_selector, audio_mixer]
    selected --> render_tools[Render tools: source_commentary_render_adapter, video_compose, hyperframes_compose]

    source_tools --> artifacts[(Artifact Bus artifacts)]
    acquisition_tools --> clips[(Artifact Bus clips)]
    qc_tools --> qc[(Artifact Bus qc)]
    audio_tools --> audio[(Artifact Bus assets/audio)]
    render_tools --> renders[(Artifact Bus renders)]

    artifacts --> adapter[source_commentary_render_adapter]
    clips --> adapter
    audio --> adapter
    adapter --> edit_decisions[edit_decisions]
    adapter --> asset_manifest[asset_manifest]
    edit_decisions --> video_compose[tools/video/video_compose.py]
    asset_manifest --> video_compose

    video_compose --> remotion[remotion-composer]
    video_compose --> hyperframes[HyperFrames]
    video_compose --> ffmpeg[FFmpeg renderer]
    remotion --> renders
    hyperframes --> renders
    ffmpeg --> renders
```

## Validation and Gate Flow

```mermaid
flowchart TD
    output[Stage output artifact] --> schema[schemas/artifacts/*.schema.json]
    schema --> valid{Schema valid?}
    valid -- no --> repair[Repair artifact before persistence]
    valid -- yes --> persist[Write to Artifact Bus]

    persist --> gate_type{Gate type}
    gate_type --> audience[audience_equity_gate]
    gate_type --> evidence[evidence_gate]
    gate_type --> rights[youtube_rights_gate]
    gate_type --> render[asymmetric_render_readiness_gate]
    gate_type --> qc[asymmetric_qc_gate]

    audience --> checkpoint[Checkpoint / run_manifest.json]
    evidence --> checkpoint
    rights --> checkpoint
    render --> checkpoint
    qc --> checkpoint

    checkpoint --> pass{Pass?}
    pass -- yes --> next_stage[Next pipeline stage]
    pass -- no --> human[Human approval, revision, or blocker]
```

## Key Source Files

- `AGENTS.md`: operating contract and Golden Loop.
- `PROJECT_CONTEXT.md`: architecture overview and repo-wide conventions.
- `pipeline_defs/`: pipeline manifests and stage contracts.
- `skills/pipelines/`: stage director instructions.
- `schemas/artifacts/`: canonical artifact schemas.
- `lib/artifact_bus.py`: project storage paths and JSON helpers.
- `lib/pipeline_contract.py`: manifest normalization and reference validation.
- `lib/pipeline_run.py`: concrete run manifest and stage recording.
- `tools/tool_registry.py`: tool discovery and capability catalog.
- `tools/base_tool.py`: shared tool contract and result shape.
- `tools/video/source_commentary_render_adapter.py`: adapts source-commentary edit plans into render contracts.
- `tools/video/video_compose.py`: runtime-aware composition orchestrator.
- `scripts/run_asymmetric_source_commentary.py`: fixture-mode Asymmetric pipeline runner.
- `scripts/asymmetric_gate.py`: render-readiness and QC gate checks.

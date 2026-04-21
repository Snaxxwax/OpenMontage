# OpenMontage

**MANDATORY: Read [`AGENT_GUIDE.md`](AGENT_GUIDE.md) before responding to ANY user message.**

Do not act on the user's request until you have read AGENT_GUIDE.md.
It contains routing rules that determine your first action based on what the user asked.
Skipping it WILL cause you to take the wrong action.

There are no instructions in this file. All instructions are in AGENT_GUIDE.md.

## Compact Instructions

When compacting context, you MUST preserve the following information:

1. **Active project name** and current pipeline stage (e.g., "the-credit-bureau-cartel, stage: assets")
2. **Creative decisions** — approved brief/concept, tone, style playbook, target duration, chapter structure
3. **Script state** — whether the full script is written, which chapters are complete
4. **Asset manifest** — paths to all generated assets (images, audio, video, music) and their verification status
5. **Pipeline decisions** — which providers/models were chosen and approved by the user, any blockers encountered
6. **Chapter progress** — for multi-part productions, which chapters are rendered and which remain
7. **User preferences** — any explicit creative direction or constraints the user stated during this session

After compaction, re-read these files before resuming work:
- `AGENT_GUIDE.md` — routing rules and protocol
- The active pipeline manifest in `pipeline_defs/`
- The latest checkpoint file in `projects/<project-name>/`
- The stage director skill for the current stage
- The project's `artifacts/` directory contents

# Modern Archivist Thumbnail Director

Use this skill when producing a thumbnail brief for a new episode.
This is advisory output — the operator approves the final thumbnail concept before any image generation.

## Mission

Produce a thumbnail brief that sells the mystery, stakes, or contradiction of the episode.
A Modern Archivist thumbnail is not a summary. It is a provocation.

## The One Rule

The thumbnail must make a stranger stop scrolling and need to know the answer.
If someone can look at the thumbnail and already guess the conclusion, the thumbnail has failed.

## Thumbnail Formulas

Pick the strongest match for the episode's core tension. Rank in order of CTR expected for this topic:

1. **Big face/object + disturbing claim** — protagonist, company logo, or key artifact with a brief accusatory or destabilizing claim overlaid
2. **Company logo + failure word** — brand mark against dark background + one tension word (see below)
3. **Old screenshot + modern consequence** — the "before" that turned into the "after"
4. **Glowing artifact + redacted case-file text** — digital relic, leaked doc, or product image with redaction stamp aesthetic
5. **Before/after: promise vs reality** — the pitch deck vs the outcome, the demo vs the product

## Headline Rules

- 3–5 words if possible; never more than 7
- Specific beats generic: "The App That Broke Trust" beats "A Failed App"
- Use tension words: `vanished`, `failed`, `lied`, `broke`, `poisoned`, `collapsed`, `exposed`, `forgotten`, `trapped`, `rotten`, `buried`, `erased`
- Avoid generic titles: "The History of X", "What Happened to X", "How X Works"
- Do not explain. Destabilize.

## Strong Headline Patterns

- "The [COMPANY] Lie Collapsed"
- "They Sold a Fantasy"
- "The App That Broke Trust"
- "Everyone Missed This"
- "The Platform Was Rotten"
- "This Demo Changed Everything"
- "The Internet Forgot [NAME/IT]"
- "A [DOLLAR AMOUNT] Illusion"
- "[COMPANY] Was Always Going to Break"
- "The [PRODUCT] Nobody Asked About"

## Visual Style Contract

All thumbnails must read as Modern Archivist at a glance:

- Background: near-black (`#0F1117`) or dark slate (`#1E2330`) — never white
- Primary text: stark white or signal teal (`#00CEC9`)
- Accent/warning: red (`#E53935`) for contradiction or failure labels
- Typography: Barlow Condensed 800–900 weight — same face as the channel title cards
- Grain overlay: subtle, documentary — not clean-corporate
- Lighting: ominous, directional; never cheerful or flat
- No clip-art, no stock-photo cheerfulness, no bright gradients

## Thumbnail Packaging Contract

### Multi-Variant Requirement

Each episode MUST generate 3 ranked thumbnail variants:
1. PRIMARY (A-tier): Most likely to maximize click-through rate
2. SECONDARY (B-tier): Alternate compelling framing 
3. FALLBACK (C-tier): Safe, technically compliant variant

### Safe-Zone Checks

Each thumbnail variant REQUIRES:
- Legible text within 20% margins from all edges
- Primary subject visible within central 60% of frame
- No critical information in corner areas
- Passes color contrast minimum (WCAG 2.1 AA)

### Upload Winner Selection

MANDATORY DECISION REQUIRED:
- UPLOAD_WINNER: Must specify which variant should be uploaded to platform
- FALLBACK_REASON: Explicit rationale if A-tier is not selected
- PLATFORM_SPECIFIC: Note any platform-specific thumbnail requirements

### Output Format

Produce a thumbnail brief with:

```json
{
    "EPISODE": "<title>",
    "VARIANTS": [
        {
            "TIER": "A",
            "FORMULA": "<which formula, from the list above>",
            "MAIN_SUBJECT": "<what is visually dominant>",
            "HEADLINE": "<3–7 words>",
            "SECONDARY_TEXT": "<optional, smaller — date, dollar figure, or sub-claim>",
            "VISUAL_DESCRIPTION": "<what the image generator needs to render this>",
            "COLOR_STATE": "<which colors are dominant — dark/teal/red>",
            "MOOD": "<one-phrase mood description>",
            "RATIONALE": "<why this formula + headline creates the click impulse>",
            "SAFE_ZONE_COMPLIANT": true/false,
            "PLATFORM_SCORE": 0-10
        },
        {
            "TIER": "B",
            "...": "<same structure as A variant>"
        },
        {
            "TIER": "C",
            "...": "<same structure as A variant>"
        }
    ],
    "UPLOAD_WINNER": {
        "VARIANT_TIER": "A|B|C",
        "RATIONALE": "<explicit reasoning>"
    },
    "PLATFORM_COMPATIBILITY": {
        "YouTube": true/false,
        "X/Twitter": true/false,
        "LinkedIn": true/false
    }
}
```

## Episode Title Patterns

When finalizing the episode title (distinct from the thumbnail headline), prefer these structures:

**Strongest patterns:**
- "The Lie Behind [Company/Product/Platform]"
- "The Strange Collapse of [Company/Product/Platform]"
- "How [Company] Sold the Future and Lost Reality"
- "The Forgotten Failure That Predicted Everything"
- "Why [Platform] Was Always Going to Break"
- "The Demo That Fooled Everyone"
- "The Internet Mystery Nobody Packaged Correctly"
- "The Product That Became a Warning"
- "How [Technology] Became a Trap"
- "The Company That Turned Hype Into Damage"

**Title rules:**
- The title and thumbnail headline can differ — the title is for search/shelf; the thumbnail is for the scroll-stop
- Titles should be evergreen and specific: name the company or product
- Avoid clickbait vagueness: the viewer should know the subject but not the conclusion

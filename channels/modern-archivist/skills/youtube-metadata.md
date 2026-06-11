# YouTube Metadata Packaging Workflow

## Artifact Contract: Publish Packet

### Purpose
The publish packet is a first-class artifact in the Modern Archivist pipeline that encapsulates all metadata required for YouTube video publication. It ensures consistent, high-quality, and platform-optimized content packaging.

### AI Content Disclosure Guidelines

#### YouTube Synthetic Content Disclosure Requirements
- Disclosure is mandatory for photorealistic synthetic media that could be mistaken for real content.
- This includes simulated real person voices/likenesses, altered real events/places, or realistic fake scenes.
- Minor AI assistance (scripts, captions, infographics) typically does not require disclosure.

#### Provenance and Transparency
- Explicitly track the nature and extent of AI/synthetic content used.
- Provide a clear, honest rationale for any generated or recreated assets.
- List all synthetic elements with their sources and generation methods.

#### Workflow Integration
1. At each stage, identify potential synthetic content elements.
2. During publish_prep, complete the ai_disclosure_review artifact.
3. Mark realistic synthetic media and required disclosures.
4. Attach a clear, concise rationale explaining the use of AI/synthetic content.

### Workflow Stages

1. **Title Generation**
   - Minimum 1 title variant required
   - Priority-weighted selection
   - Platform-specific customization support

2. **Thumbnail Selection**
   - Primary thumbnail identified
   - Optional fallback thumbnails
   - Explicit selection criteria

3. **Chapter Markers**
   - Timestamp-based chapters
   - Optional descriptions
   - Enhances viewer navigation

4. **Description Construction**
   - Maximum 5000 characters
   - SEO and narrative considerations

5. **Pinned Comment Strategy**
   - Primary engagement mechanism
   - Call-to-action included
   - Optional external links

6. **End Screen Targeting**
   - Channel cross-promotion
   - Playlist or specific video linking

7. **Teaser Generation**
   - Short promotional text
   - Duration and stylistic hints

### Validation Rules
- Schema-validated artifact
- Required fields prevent incomplete publication
- Platform-specific adjustments allowed via metadata

### Performance Considerations
- Minimize manual intervention
- Maximize algorithmic consistency
- Support A/B testing via variant weighting
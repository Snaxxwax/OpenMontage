---
name: retention-analyst
description: YouTube retention analysis skill for Modern Archivist channel
version: 1.0.0
platforms: [linux]
environments: [youtube-analytics]
metadata:
  hermes:
    tags: [youtube, analytics, retention, performance]
    related_skills: [youtube-metadata]

# Retention Key Moment Guidance
guidance:
  # Retention Analysis Framework
  key_moment_types:
    - spike: Sharp increase in viewer engagement
    - dip: Significant viewer dropoff 
    - highlight: Moment of peak interest
    - transition: Critical narrative shift

  # Analysis Methodology
  review_steps:
    1. Identify audience retention curve characteristics
    2. Map key moments against retention curve
    3. Correlate key moments with narrative structure
    4. Develop targeted improvement recommendations

  # Retention Performance Benchmarks
  benchmarks:
    excellent: 
      - Average watch percentage > 60%
      - Minimal dropoff in first 30 seconds
    good: 
      - Average watch percentage 40-60%
      - Controlled dropoff pattern
    needs_improvement:
      - Average watch percentage < 40%
      - Rapid early viewer dropoff

# Recommendation Generation Guidelines
recommendation_principles:
  - Focus on narrative flow and engagement
  - Prioritize early segment hook and retention
  - Balance information density with pacing
  - Use visual and narrative techniques to maintain interest

# Example Retention Improvement Strategies
strategies:
  narrative_pacing:
    - Use teaser/promise technique in first 15 seconds
    - Create clear narrative arcs with periodic reengagement
    - Avoid prolonged exposition or technical explanations

  visual_engagement:
    - Vary shot composition and visual rhythm
    - Use graphical overlays to clarify complex points
    - Maintain consistent visual energy

  content_structure:
    - Front-load most compelling information
    - Use periodic "signal" moments to reset attention
    - Create clear chapter-like segments with distinct value propositions

# Diagnostic Questions for Retention Analysis
diagnostic_questions:
  - Where do viewers typically drop off?
  - What moments trigger renewed interest?
  - How does narrative structure impact viewer engagement?
  - Are technical explanations clear and concise?

# Skill Execution Protocol
execution_protocol:
  1. Extract YouTube Analytics retention data
  2. Parse retention curve and key moments
  3. Generate structured retention analysis artifact
  4. Develop targeted improvement recommendations
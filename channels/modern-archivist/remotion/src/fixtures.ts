import type { ModernArchivistEpisode } from "./types";

export const modernArchivistFixture: ModernArchivistEpisode = {
  episode_id: "modern-archivist-demo",
  title: "The Web Page That Refused To Die",
  duration_seconds: 60,
  puppet: {
    version: "1.0",
    character_id: "modern_archivist",
    display_name: "The Archivist",
    temporary: true,
    layers: {
      body: "modern-archivist/archivist-body.png",
      mug: "modern-archivist/archivist-mug.png",
    },
    anchors: {
      mouth: { x: 0.51, y: 0.62 },
      glasses: { x: 0.5, y: 0.43 },
      arm_pivot: { x: 0.62, y: 0.74 },
    },
  },
  sections: [
    {
      id: "s01_hook",
      start: 0,
      end: 10,
      text: "This abandoned-looking web page is still holding up half the internet.",
      tags: [
        { at: 0, type: "layout", value: "STATE_MONOLOGUE" },
        { at: 6, type: "sip" },
      ],
    },
    {
      id: "s02_evidence",
      start: 10,
      end: 32,
      text: "To understand why, we need to inspect the source.",
      tags: [
        { at: 10, type: "layout", value: "STATE_DEEP_DIVE" },
        {
          at: 11,
          type: "media",
          value: {
            id: "html-spec",
            kind: "code",
            language: "html",
            title: "Archived Markup",
            content: "<table>\n  <tr><td>Still here.</td></tr>\n</table>",
          },
        },
      ],
    },
    {
      id: "s03_interrupt",
      start: 32,
      end: 45,
      text: "And this is where the archive starts screaming.",
      tags: [{ at: 32, type: "layout", value: "STATE_CRITICAL_ERROR" }],
    },
    {
      id: "s04_close",
      start: 45,
      end: 60,
      text: "The modern web is not as modern as it thinks.",
      tags: [{ at: 45, type: "layout", value: "STATE_MONOLOGUE" }],
    },
  ],
  amplitude: Array.from({ length: 121 }, (_, index) => {
    const time = index * 0.5;
    const speakingWindows =
      (time > 0.5 && time < 9.2) ||
      (time > 10.5 && time < 30.5) ||
      (time > 32.2 && time < 43.5) ||
      (time > 45.2 && time < 58.5);
    return { time, volume: speakingWindows ? 0.18 + 0.07 * Math.sin(time * 7) : 0.01 };
  }),
};

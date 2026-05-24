import React from "react";
import type { LayoutState } from "../types";

const archiveText = `GET /wiki/HTML/2.0 HTTP/1.1
GET /r/InternetIsBeautiful/comments/archive_fragments
SELECT * FROM forgotten_standards WHERE still_running = true;
<html>
  <head><title>1997 mirror</title></head>
  <body bgcolor="#2F4F4F">
    <table width="100%"><tr><td>the past is not dead code</td></tr></table>
  </body>
</html>

RFC 1866: Hypertext Markup Language - 2.0
Last-Modified: Tue, 21 May 1996 19:43:12 GMT
CACHE HIT: public-records/municipal-broadband/minutes.txt
ARCHIVE WARNING: dependency chain contains unmaintained social memory
`;

const repeatedArchiveText = Array.from({ length: 3 }, () => archiveText).join("\n");

export const ScrollingCodeBackdrop: React.FC<{ layout: LayoutState }> = React.memo(({ layout }) => {
  return (
    <>
      <style>{`@keyframes modernArchivistBackdropScroll { from { transform: translate3d(0, 0, 0); } to { transform: translate3d(0, -420px, 0); } }`}</style>
      <pre
        style={{
          position: "absolute",
          inset: 0,
          margin: 0,
          padding: "80px 90px",
          animation: "modernArchivistBackdropScroll 36s linear infinite",
          willChange: "transform",
          color: layout === "STATE_CRITICAL_ERROR" ? "rgba(255, 210, 210, 0.16)" : "rgba(214, 255, 247, 0.13)",
          fontSize: 32,
          lineHeight: 1.28,
          fontFamily: "JetBrains Mono, Fira Code, monospace",
          whiteSpace: "pre-wrap",
          zIndex: 0,
          userSelect: "none",
        }}
      >
        <code>{repeatedArchiveText}</code>
      </pre>
    </>
  );
});

ScrollingCodeBackdrop.displayName = "ScrollingCodeBackdrop";

import React from "react";
import ChannelFrame, { ChannelFrameProps } from "../components/ChannelFrame";

export const channelFrameTestProps: ChannelFrameProps = {
  title: "FAILURE LEDGER",
  subtitle: "Humane AI Pin: a postmortem in chapters",
  beats: [
    { id: "01", title: "The Promise", startSeconds: 0, endSeconds: 3.5 },
    { id: "02", title: "The Preorder", startSeconds: 3.5, endSeconds: 7, emphasis: "normal" },
    { id: "03", title: "The Reviews", startSeconds: 7, endSeconds: 10.5, emphasis: "critical" },
    { id: "04", title: "The Refunds", startSeconds: 10.5, endSeconds: 14, emphasis: "critical" },
    { id: "05", title: "The Silence", startSeconds: 14, endSeconds: 17.5 },
  ],
};

export const ChannelFrameTest: React.FC<ChannelFrameProps> = (props) => (
  <ChannelFrame {...props} />
);

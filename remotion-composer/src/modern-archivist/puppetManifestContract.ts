import type { AnyPuppetManifest, PuppetManifest } from "../../../channels/modern-archivist/remotion/src/types";

export const typecheckedModernArchivistV2Fixture = {
  version: "2.0",
  character_id: "modern_archivist",
  display_name: "The Archivist",
  rig_contract: "full_body_layered",
  canvas: { width: 1254, height: 1254 },
  palette_policy: "hard_alpha_limited_palette",
  coordinate_modes: ["canvas_registered", "anchored_overlay"],
  layer_groups: {
    body: ["body"],
    head: ["head"],
    eyes: ["eye_closed_l"],
    brows: ["brow_neutral_l"],
    mouths: ["mouth_closed"],
    glasses: ["glasses_frame"],
    arms: ["arm_right_idle"],
    props: ["mug"],
  },
  layers: [
    {
      id: "body",
      src: "modern-archivist/layers/modern_archivist_body.png",
      group: "body",
      z: 1,
      status: "production",
      coordinate_mode: "canvas_registered",
      anchor: { x: 0.5, y: 0.5 },
      pivot: { x: 0.5, y: 0.75 },
      bounds_required: true,
    },
    {
      id: "mouth_closed",
      src: "modern-archivist/mouth-closed.png",
      group: "mouths",
      z: 7,
      status: "production",
      coordinate_mode: "anchored_overlay",
      anchor: { x: 0.51, y: 0.62 },
      pivot: { x: 0.51, y: 0.62 },
      bounds_required: true,
    },
  ],
} as const satisfies PuppetManifest;

export const acceptsRuntimePuppetManifest = (manifest: AnyPuppetManifest): AnyPuppetManifest => manifest;

acceptsRuntimePuppetManifest(typecheckedModernArchivistV2Fixture);

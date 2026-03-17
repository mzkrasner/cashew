import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

// Deprecated. pi-web-access should be installed as a Pi package via:
//   pi install npm:pi-web-access
// Pi loads installed packages directly, so this legacy wrapper is now a no-op.
// Keeping the file prevents startup failures for users who already symlinked it.
export default function (_pi: ExtensionAPI) {}

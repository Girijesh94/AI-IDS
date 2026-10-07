import { useEffect, useState } from "react";

let supported: boolean | undefined;
/** Probe once; both shader mounts share the same static fallback decision. */
export function useWebGLSupport() {
  const [available, setAvailable] = useState(supported ?? false);
  useEffect(() => {
    if (supported === undefined) {
      try {
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("webgl2");
        supported = !!context;
        context?.getExtension("WEBGL_lose_context")?.loseContext();
      } catch {
        supported = false;
      }
    }
    setAvailable(supported);
  }, []);
  return available;
}

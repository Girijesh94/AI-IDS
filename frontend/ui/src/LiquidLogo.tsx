import { LiquidMetal } from "@paper-design/shaders-react";
import { useEffect, useRef, useState } from "react";
import { useWebGLSupport } from "./graphics";
export default function LiquidLogo({ animated }: { animated: boolean }) {
  const [hover, setHover] = useState(false);
  const [visible, setVisible] = useState(false);
  const element = useRef<HTMLDivElement>(null);
  const webgl = useWebGLSupport();
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) =>
      setVisible(entry.isIntersecting),
    );
    if (element.current) observer.observe(element.current);
    return () => observer.disconnect();
  }, []);
  return (
    <div
      className="liquid-logo"
      ref={element}
      aria-hidden="true"
      onPointerEnter={() => setHover(true)}
      onPointerLeave={() => setHover(false)}
    >
      {visible && webgl && (
        <LiquidMetal
          image="/static/ids-mark.svg"
          width={44}
          height={44}
          maxPixelCount={16384}
          minPixelRatio={1}
          speed={animated ? (hover ? 0.8 : 0.25) : 0}
          distortion={hover ? 0.65 : 0.25}
          repetition={3}
          softness={0.15}
          colorBack="#00000000"
          colorTint="#c6f5ab"
          fit="contain"
        />
      )}
    </div>
  );
}

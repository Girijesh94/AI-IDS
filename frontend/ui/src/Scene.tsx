import {
  useEffect,
  useMemo,
  useRef,
  type MutableRefObject,
  type ComponentProps,
} from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { ShaderGradient, ShaderGradientCanvas } from "@shadergradient/react";
import * as THREE from "three";

type Pointer = {
  x: number;
  y: number;
  inside: boolean;
  ripple: number;
  rx: number;
  ry: number;
};
type Props = {
  pointer: MutableRefObject<Pointer>;
  xray: boolean;
  animated: boolean;
};
const vertex = /* glsl */ `
  uniform float uTime; uniform vec2 uPointer; uniform float uForce;
  varying vec3 vNormal; varying vec3 vPosition;
  void main(){
    vec3 p = position;
    float wave = sin(p.y*4.8+uTime*.7)*cos(p.x*4.1-uTime*.5)*sin(p.z*3.2+uTime*.4);
    p += normal * wave * (.08+uForce*.09);
    p += normal * pow(max(0.,dot(normal,normalize(vec3(uPointer*1.7,1.6)))),8.)*uForce*.28;
    vNormal=normalize(normalMatrix*normal); vPosition=p;
    gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.);
  }
`;
const fragment = /* glsl */ `
  uniform float uTime; varying vec3 vNormal; varying vec3 vPosition;
  void main(){
    vec3 n=normalize(vNormal);
    float bands=sin(vPosition.y*7.+vPosition.x*3.+sin(vPosition.z*3.+uTime*.3)*1.5+uTime*.35);
    float light=pow(max(0.,dot(n,normalize(vec3(-.4,.8,1.)))),3.);
    float rim=pow(1.-abs(n.z),2.);
    vec3 color=mix(vec3(.045,.085,.09),vec3(.55,.69,.66),smoothstep(-.2,.5,bands));
    color=mix(color,vec3(.83,.96,.66),light*.85);
    color+=vec3(.25,.55,.42)*rim*.6;
    gl_FragColor=vec4(color,1.);
  }
`;
function Core({ pointer, xray, animated }: Props) {
  const group = useRef<THREE.Group>(null!);
  const shell = useRef<THREE.Mesh>(null!);
  const material = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: vertex,
        fragmentShader: fragment,
        uniforms: {
          uTime: { value: 0 },
          uPointer: { value: new THREE.Vector2() },
          uForce: { value: 0 },
        },
      }),
    [],
  );
  const wireMaterial = useMemo(
    () =>
      new THREE.ShaderMaterial({
        vertexShader: vertex,
        fragmentShader: "void main(){gl_FragColor=vec4(.75,.94,.62,.7);}",
        wireframe: true,
        transparent: true,
        uniforms: material.uniforms,
      }),
    [material],
  );
  const clock = useRef(0);
  useEffect(
    () => () => {
      material.dispose();
      wireMaterial.dispose();
    },
    [material, wireMaterial],
  );
  useFrame((_, delta) => {
    if (animated) clock.current += Math.min(delta, 0.04);
    const t = clock.current;
    material.uniforms.uTime.value = t;
    const p = pointer.current;
    material.uniforms.uPointer.value.lerp(new THREE.Vector2(p.x, p.y), 0.08);
    material.uniforms.uForce.value = THREE.MathUtils.lerp(
      material.uniforms.uForce.value,
      animated && p.inside ? 1 : 0,
      0.07,
    );
    group.current.rotation.y = animated ? t * 0.09 + p.x * 0.17 : 0.35;
    group.current.rotation.x = animated ? -0.15 + p.y * 0.12 : -0.15;
    group.current.position.y = animated ? Math.sin(t * 0.55) * 0.055 : 0;
    group.current.position.x = THREE.MathUtils.lerp(
      group.current.position.x,
      animated && p.inside ? p.x * 0.16 : 0,
      0.07,
    );
    shell.current.scale.setScalar(
      THREE.MathUtils.lerp(shell.current.scale.x, xray ? 1.12 : 1, 0.07),
    );
  });
  return (
    <group ref={group} rotation={[0, 0, 0.15]}>
      <mesh ref={shell} material={material} visible={!xray}>
        <icosahedronGeometry args={[1.18, 5]} />
      </mesh>
      <mesh visible={xray} material={wireMaterial}>
        <icosahedronGeometry args={[1.2, 2]} />
      </mesh>
      <mesh visible={xray}>
        <icosahedronGeometry args={[0.78, 1]} />
        <meshBasicMaterial
          color="#71a39c"
          wireframe
          transparent
          opacity={0.65}
        />
      </mesh>
      <mesh visible={xray}>
        <octahedronGeometry args={[0.42]} />
        <meshBasicMaterial color="#d6f6a5" wireframe />
      </mesh>
      {[0, 1, 2].map((i) => (
        <group key={i} rotation={[0.65 + i * 0.65, i * 0.75, 0.4 + i * 0.3]}>
          <mesh>
            <torusGeometry args={[1.65 + i * 0.23, 0.006, 6, 128]} />
            <meshBasicMaterial
              color={i === 1 ? "#c7ef97" : "#4a7770"}
              transparent
              opacity={i === 1 ? 0.65 : 0.55}
            />
          </mesh>
          <mesh position={[1.65 + i * 0.23, 0, 0]}>
            <sphereGeometry args={[0.035, 8, 8]} />
            <meshBasicMaterial color="#d5f7ac" />
          </mesh>
        </group>
      ))}
    </group>
  );
}
function Field({ pointer, animated }: Pick<Props, "pointer" | "animated">) {
  const lines = useRef<THREE.LineSegments>(null!);
  const dots = useRef<THREE.Points>(null!);
  const ripple = useRef<THREE.Mesh>(null!);
  const geometry = useMemo(() => {
    const points: number[] = [];
    for (let y = -4; y <= 4; y++)
      for (let x = -5; x <= 5; x++) {
        points.push(x * 0.6, y * 0.6, -1.8, (x + 0.6) * 0.6, y * 0.6, -1.8);
        points.push(x * 0.6, y * 0.6, -1.8, x * 0.6, (y + 0.6) * 0.6, -1.8);
      }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
    return g;
  }, []);
  const original = useMemo(
    () => Float32Array.from(geometry.getAttribute("position").array),
    [geometry],
  );
  const particles = useMemo(() => {
    const p = [];
    for (let i = 0; i < 55; i++)
      p.push(
        Math.sin(i * 127.1) * 3.4,
        Math.cos(i * 311.7) * 2.6,
        Math.sin(i * 74.7) * 1.2 - 1,
      );
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute(p, 3));
    return g;
  }, []);
  useEffect(
    () => () => {
      geometry.dispose();
      particles.dispose();
    },
    [geometry, particles],
  );
  useFrame(() => {
    if (!animated) return;
    const p = pointer.current,
      positions = geometry.getAttribute("position");
    for (let i = 0; i < positions.count; i++) {
      const x = original[i * 3],
        y = original[i * 3 + 1];
      const dx = p.x * 3 - x,
        dy = p.y * 2 - y,
        dist = dx * dx + dy * dy;
      const force = p.inside ? Math.exp(-dist * 1.3) * 0.25 : 0;
      positions.setXYZ(i, x + dx * force, y + dy * force, -1.8 + force * 0.7);
    }
    positions.needsUpdate = true;
    const age = performance.now() / 1000 - p.ripple;
    ripple.current.visible = p.ripple > 0 && age < 2;
    ripple.current.position.set(p.rx, p.ry, -1.7);
    ripple.current.scale.setScalar(Math.max(0.001, age * 2.4));
    (ripple.current.material as THREE.MeshBasicMaterial).opacity = Math.max(
      0,
      0.5 - age * 0.25,
    );
    dots.current.rotation.z += 0.0002;
  });
  return (
    <>
      <lineSegments ref={lines} geometry={geometry}>
        <lineBasicMaterial color="#679a86" transparent opacity={0.16} />
      </lineSegments>
      <points ref={dots} geometry={particles}>
        <pointsMaterial
          color="#cceea6"
          size={0.018}
          transparent
          opacity={0.55}
        />
      </points>
      <mesh ref={ripple} visible={false}>
        <ringGeometry args={[0.97, 1, 100]} />
        <meshBasicMaterial
          color="#d5fca7"
          transparent
          opacity={0}
          side={THREE.DoubleSide}
        />
      </mesh>
    </>
  );
}
export default function Scene(props: Props) {
  const gradient: ComponentProps<typeof ShaderGradient> = {
    type: "waterPlane",
    animate: props.animated ? "on" : "off",
    uSpeed: 0.13,
    uStrength: 1.8,
    uFrequency: 3.5,
    uDensity: 1.2,
    color1: "#102b28",
    color2: "#234a38",
    color3: "#080d11",
    lightType: "3d",
    brightness: 0.7,
    cDistance: 4.8,
    cPolarAngle: 75,
    rotationX: 0,
    grain: "off",
    enableTransition: false,
  };
  return (
    <div className="scene-renderer" aria-hidden="true">
      <div className="shader-halo">
        {props.animated && (
          <ShaderGradientCanvas
            pixelDensity={1}
            powerPreference="low-power"
            pointerEvents="none"
            lazyLoad
          >
            <ShaderGradient {...gradient} />
          </ShaderGradientCanvas>
        )}
      </div>
      <Canvas
        dpr={[1, 1.35]}
        camera={{ position: [0, 0, 6.5], fov: 44 }}
        frameloop={props.animated ? "always" : "demand"}
        gl={{ alpha: true, antialias: true, powerPreference: "low-power" }}
        onCreated={({ gl }) => {
          gl.domElement.dataset.renderer = "sensor";
        }}
      >
        <Field pointer={props.pointer} animated={props.animated} />
        <Core {...props} />
      </Canvas>
    </div>
  );
}

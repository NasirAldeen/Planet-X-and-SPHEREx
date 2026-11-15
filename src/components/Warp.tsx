import { useEffect, useRef, useState } from "react";

/*
 * Warp tunnel fragment shader by Matthias Hurrle (@atzedent), as distributed in the
 * "light-speed" component by rahil1202 on 21st.dev. The licence is listed there as unknown;
 * replace this shader before any public release if the licence cannot be confirmed.
 */
const FRAG = `#version 300 es
precision highp float;
out vec4 O;
uniform float time;
uniform vec2 resolution;
#define FC gl_FragCoord.xy
#define R  resolution
#define T  time
#define hue(a) (.6+.6*cos(6.3*(a)+vec3(0,83,21)))
float rnd(float a) {
  vec2 p = fract(a * vec2(12.9898, 78.233));
  p += dot(p, p*345.);
  return fract(p.x * p.y);
}
vec3 pattern(vec2 uv) {
  vec3 col = vec3(0.);
  for (float i=.0; i++<20.;) {
    float a = rnd(i);
    vec2 n = vec2(a, fract(a*34.56));
    vec2 p = sin(n*(T+7.) + T*.5);
    float d = dot(uv-p, uv-p);
    col += .00125/d * hue(dot(uv,uv) + i*.125 + T);
  }
  return col;
}
void main(void) {
  vec2 uv = (FC - .5 * R) / min(R.x, R.y);
  vec3 col = vec3(0.);
  float s = 2.4;
  float a = atan(uv.x, uv.y);
  float b = length(uv);
  uv = vec2(a * 5. / 6.28318, .05 / tan(b) + T);
  uv = fract(uv) - .5;
  col += pattern(uv * s);
  O = vec4(col, 1.);
}`;

const VERT = `#version 300 es
precision highp float;
in vec2 position;
void main(){ gl_Position = vec4(position, 0.0, 1.0); }`;

type Props = { speedRef: { current: number } };

/** Full-screen warp tunnel. Speed is read from a ref each frame so it can ramp without recompiling. */
export default function Warp({ speedRef }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [ok, setOk] = useState(true);

  useEffect(() => {
    const canvas = ref.current!;
    const gl = canvas.getContext("webgl2");
    if (!gl) {
      setOk(false);
      return;
    }
    const compile = (type: number, src: string) => {
      const sh = gl.createShader(type)!;
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh) || "shader error");
      return sh;
    };
    let prog: WebGLProgram;
    try {
      prog = gl.createProgram()!;
      gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT));
      gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG));
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog) || "link error");
    } catch {
      setOk(false);
      return;
    }
    gl.useProgram(prog);
    const vbo = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, 1, -1, -1, 1, 1, 1, -1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, "position");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const uTime = gl.getUniformLocation(prog, "time");
    const uRes = gl.getUniformLocation(prog, "resolution");

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      canvas.width = Math.floor(canvas.clientWidth * dpr);
      canvas.height = Math.floor(canvas.clientHeight * dpr);
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.uniform2f(uRes, canvas.width, canvas.height);
    };
    resize();
    window.addEventListener("resize", resize);

    let raf = 0;
    let last = performance.now();
    let time = 0;
    const loop = (now: number) => {
      raf = requestAnimationFrame(loop);
      time += ((now - last) / 1000) * speedRef.current;
      last = now;
      gl.uniform1f(uTime, time);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    };
    raf = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      gl.deleteProgram(prog);
      gl.deleteBuffer(vbo);
    };
  }, [speedRef]);

  return ok ? <canvas ref={ref} className="fill" aria-hidden="true" /> : <div className="fill warp-fallback" />;
}

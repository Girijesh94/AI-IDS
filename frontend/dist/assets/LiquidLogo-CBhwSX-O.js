import{i as e,n as t,s as n,t as r}from"./app.js";var i=`#version 300 es
precision mediump float;

layout(location = 0) in vec4 a_position;

uniform vec2 u_resolution;
uniform float u_pixelRatio;
uniform float u_imageAspectRatio;
uniform float u_originX;
uniform float u_originY;
uniform float u_worldWidth;
uniform float u_worldHeight;
uniform float u_fit;
uniform float u_scale;
uniform float u_rotation;
uniform float u_offsetX;
uniform float u_offsetY;

out vec2 v_objectUV;
out vec2 v_objectBoxSize;
out vec2 v_responsiveUV;
out vec2 v_responsiveBoxGivenSize;
out vec2 v_patternUV;
out vec2 v_patternBoxSize;
out vec2 v_imageUV;

vec3 getBoxSize(float boxRatio, vec2 givenBoxSize) {
  vec2 box = vec2(0.);
  // fit = none
  box.x = boxRatio * min(givenBoxSize.x / boxRatio, givenBoxSize.y);
  float noFitBoxWidth = box.x;
  if (u_fit == 1.) { // fit = contain
    box.x = boxRatio * min(u_resolution.x / boxRatio, u_resolution.y);
  } else if (u_fit == 2.) { // fit = cover
    box.x = boxRatio * max(u_resolution.x / boxRatio, u_resolution.y);
  }
  box.y = box.x / boxRatio;
  return vec3(box, noFitBoxWidth);
}

void main() {
  gl_Position = a_position;

  vec2 uv = gl_Position.xy * .5;
  vec2 boxOrigin = vec2(.5 - u_originX, u_originY - .5);
  vec2 givenBoxSize = vec2(u_worldWidth, u_worldHeight);
  givenBoxSize = max(givenBoxSize, vec2(1.)) * u_pixelRatio;
  float r = u_rotation * 3.14159265358979323846 / 180.;
  mat2 graphicRotation = mat2(cos(r), sin(r), -sin(r), cos(r));
  vec2 graphicOffset = vec2(-u_offsetX, u_offsetY);


  // ===================================================

  float fixedRatio = 1.;
  vec2 fixedRatioBoxGivenSize = vec2(
  (u_worldWidth == 0.) ? u_resolution.x : givenBoxSize.x,
  (u_worldHeight == 0.) ? u_resolution.y : givenBoxSize.y
  );

  v_objectBoxSize = getBoxSize(fixedRatio, fixedRatioBoxGivenSize).xy;
  vec2 objectWorldScale = u_resolution.xy / v_objectBoxSize;

  v_objectUV = uv;
  v_objectUV *= objectWorldScale;
  v_objectUV += boxOrigin * (objectWorldScale - 1.);
  v_objectUV += graphicOffset;
  v_objectUV /= u_scale;
  v_objectUV = graphicRotation * v_objectUV;

  // ===================================================

  v_responsiveBoxGivenSize = vec2(
  (u_worldWidth == 0.) ? u_resolution.x : givenBoxSize.x,
  (u_worldHeight == 0.) ? u_resolution.y : givenBoxSize.y
  );
  float responsiveRatio = v_responsiveBoxGivenSize.x / v_responsiveBoxGivenSize.y;
  vec2 responsiveBoxSize = getBoxSize(responsiveRatio, v_responsiveBoxGivenSize).xy;
  vec2 responsiveBoxScale = u_resolution.xy / responsiveBoxSize;

  #ifdef ADD_HELPERS
  v_responsiveHelperBox = uv;
  v_responsiveHelperBox *= responsiveBoxScale;
  v_responsiveHelperBox += boxOrigin * (responsiveBoxScale - 1.);
  #endif

  v_responsiveUV = uv;
  v_responsiveUV *= responsiveBoxScale;
  v_responsiveUV += boxOrigin * (responsiveBoxScale - 1.);
  v_responsiveUV += graphicOffset;
  v_responsiveUV /= u_scale;
  v_responsiveUV.x *= responsiveRatio;
  v_responsiveUV = graphicRotation * v_responsiveUV;
  v_responsiveUV.x /= responsiveRatio;

  // ===================================================

  float patternBoxRatio = givenBoxSize.x / givenBoxSize.y;
  vec2 patternBoxGivenSize = vec2(
  (u_worldWidth == 0.) ? u_resolution.x : givenBoxSize.x,
  (u_worldHeight == 0.) ? u_resolution.y : givenBoxSize.y
  );
  patternBoxRatio = patternBoxGivenSize.x / patternBoxGivenSize.y;

  vec3 boxSizeData = getBoxSize(patternBoxRatio, patternBoxGivenSize);
  v_patternBoxSize = boxSizeData.xy;
  float patternBoxNoFitBoxWidth = boxSizeData.z;
  vec2 patternBoxScale = u_resolution.xy / v_patternBoxSize;

  v_patternUV = uv;
  v_patternUV += graphicOffset / patternBoxScale;
  v_patternUV += boxOrigin;
  v_patternUV -= boxOrigin / patternBoxScale;
  v_patternUV *= u_resolution.xy;
  v_patternUV /= u_pixelRatio;
  if (u_fit > 0.) {
    v_patternUV *= (patternBoxNoFitBoxWidth / v_patternBoxSize.x);
  }
  v_patternUV /= u_scale;
  v_patternUV = graphicRotation * v_patternUV;
  v_patternUV += boxOrigin / patternBoxScale;
  v_patternUV -= boxOrigin;
  // x100 is a default multiplier between vertex and fragmant shaders
  // we use it to avoid UV presision issues
  v_patternUV *= .01;

  // ===================================================

  vec2 imageBoxSize;
  if (u_fit == 1.) { // contain
    imageBoxSize.x = min(u_resolution.x / u_imageAspectRatio, u_resolution.y) * u_imageAspectRatio;
  } else if (u_fit == 2.) { // cover
    imageBoxSize.x = max(u_resolution.x / u_imageAspectRatio, u_resolution.y) * u_imageAspectRatio;
  } else {
    imageBoxSize.x = min(10.0, 10.0 / u_imageAspectRatio * u_imageAspectRatio);
  }
  imageBoxSize.y = imageBoxSize.x / u_imageAspectRatio;
  vec2 imageBoxScale = u_resolution.xy / imageBoxSize;

  v_imageUV = uv;
  v_imageUV *= imageBoxScale;
  v_imageUV += boxOrigin * (imageBoxScale - 1.);
  v_imageUV += graphicOffset;
  v_imageUV /= u_scale;
  v_imageUV.x *= u_imageAspectRatio;
  v_imageUV = graphicRotation * v_imageUV;
  v_imageUV.x /= u_imageAspectRatio;

  v_imageUV += .5;
  v_imageUV.y = 1. - v_imageUV.y;
}`,a=8294400,o=class{parentElement;canvasElement;gl;program=null;uniformLocations={};fragmentShader;rafId=null;lastRenderTime=0;currentFrame=0;speed=0;currentSpeed=0;providedUniforms;mipmaps=[];hasBeenDisposed=!1;resolutionChanged=!0;textures=new Map;minPixelRatio;maxPixelCount;isSafari=u();uniformCache={};textureUnitMap=new Map;ownerDocument;constructor(e,t,n,r,i=0,o=0,s=2,c=a,u=[]){if(e?.nodeType===1)this.parentElement=e;else throw Error(`Paper Shaders: parent element must be an HTMLElement`);if(this.ownerDocument=e.ownerDocument,!this.ownerDocument.querySelector(`style[data-paper-shader]`)){let e=this.ownerDocument.createElement(`style`);e.innerHTML=l,e.setAttribute(`data-paper-shader`,``),this.ownerDocument.head.prepend(e)}let d=this.ownerDocument.createElement(`canvas`);this.canvasElement=d,this.parentElement.prepend(d),this.fragmentShader=t,this.providedUniforms=n,this.mipmaps=u,this.currentFrame=o,this.minPixelRatio=s,this.maxPixelCount=c;let f=d.getContext(`webgl2`,r);if(!f)throw Error(`Paper Shaders: WebGL is not supported in this browser`);this.gl=f,this.initProgram(),this.setupPositionAttribute(),this.setupUniforms(),this.setUniformValues(this.providedUniforms),this.setupResizeObserver(),visualViewport?.addEventListener(`resize`,this.handleVisualViewportChange),this.setupIntersectionObserver(),this.setSpeed(i),this.parentElement.setAttribute(`data-paper-shader`,``),this.parentElement.paperShaderMount=this,this.ownerDocument.addEventListener(`visibilitychange`,this.handleDocumentVisibilityChange)}initProgram=()=>{let e=c(this.gl,i,this.fragmentShader);e&&(this.program=e)};setupPositionAttribute=()=>{let e=this.gl.getAttribLocation(this.program,`a_position`),t=this.gl.createBuffer();this.gl.bindBuffer(this.gl.ARRAY_BUFFER,t),this.gl.bufferData(this.gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),this.gl.STATIC_DRAW),this.gl.enableVertexAttribArray(e),this.gl.vertexAttribPointer(e,2,this.gl.FLOAT,!1,0,0)};setupUniforms=()=>{let e={u_time:this.gl.getUniformLocation(this.program,`u_time`),u_pixelRatio:this.gl.getUniformLocation(this.program,`u_pixelRatio`),u_resolution:this.gl.getUniformLocation(this.program,`u_resolution`)};Object.entries(this.providedUniforms).forEach(([t,n])=>{if(e[t]=this.gl.getUniformLocation(this.program,t),n instanceof HTMLImageElement){let n=`${t}AspectRatio`;e[n]=this.gl.getUniformLocation(this.program,n)}}),this.uniformLocations=e};renderScale=1;parentWidth=0;parentHeight=0;parentDevicePixelWidth=0;parentDevicePixelHeight=0;devicePixelsSupported=!1;intersectionObserver=null;isInViewport=!0;resizeObserver=null;setupResizeObserver=()=>{this.resizeObserver=new ResizeObserver(([e])=>{if(e?.borderBoxSize[0]){let t=e.devicePixelContentBoxSize?.[0];t!==void 0&&(this.devicePixelsSupported=!0,this.parentDevicePixelWidth=t.inlineSize,this.parentDevicePixelHeight=t.blockSize),this.parentWidth=e.borderBoxSize[0].inlineSize,this.parentHeight=e.borderBoxSize[0].blockSize}this.handleResize()}),this.resizeObserver.observe(this.parentElement)};setupIntersectionObserver=()=>{let e=this.ownerDocument.defaultView;e?.IntersectionObserver&&(this.intersectionObserver=new e.IntersectionObserver(([e])=>{this.isInViewport=e?.isIntersecting??!0,this.updateCurrentSpeed()}),this.intersectionObserver.observe(this.parentElement))};handleVisualViewportChange=()=>{this.resizeObserver?.disconnect(),this.setupResizeObserver()};handleResize=()=>{let e=0,t=0,n=Math.max(1,window.devicePixelRatio),r=visualViewport?.scale??1;if(this.devicePixelsSupported){let i=Math.max(1,this.minPixelRatio/n);e=this.parentDevicePixelWidth*i*r,t=this.parentDevicePixelHeight*i*r}else{let i=Math.max(n,this.minPixelRatio)*r;if(this.isSafari){let e=d(this.ownerDocument);i*=Math.max(1,e)}e=Math.round(this.parentWidth)*i,t=Math.round(this.parentHeight)*i}let i=Math.sqrt(this.maxPixelCount)/Math.sqrt(e*t),a=Math.min(1,i),o=Math.round(e*a),s=Math.round(t*a),c=o/Math.round(this.parentWidth);(this.canvasElement.width!==o||this.canvasElement.height!==s||this.renderScale!==c)&&(this.renderScale=c,this.canvasElement.width=o,this.canvasElement.height=s,this.resolutionChanged=!0,this.gl.viewport(0,0,this.gl.canvas.width,this.gl.canvas.height),this.render(performance.now()))};render=e=>{if(this.hasBeenDisposed)return;if(this.program===null){console.warn(`Tried to render before program or gl was initialized`);return}let t=e-this.lastRenderTime;this.lastRenderTime=e,this.currentSpeed!==0&&(this.currentFrame+=t*this.currentSpeed),this.gl.clear(this.gl.COLOR_BUFFER_BIT),this.gl.useProgram(this.program),this.gl.uniform1f(this.uniformLocations.u_time,this.currentFrame*.001),this.resolutionChanged&&=(this.gl.uniform2f(this.uniformLocations.u_resolution,this.gl.canvas.width,this.gl.canvas.height),this.gl.uniform1f(this.uniformLocations.u_pixelRatio,this.renderScale),!1),this.gl.drawArrays(this.gl.TRIANGLES,0,6),this.currentSpeed===0?this.rafId=null:this.requestRender()};requestRender=()=>{this.rafId!==null&&cancelAnimationFrame(this.rafId),this.rafId=requestAnimationFrame(this.render)};setTextureUniform=(e,t)=>{if(!t.complete||t.naturalWidth===0)throw Error(`Paper Shaders: image for uniform ${e} must be fully loaded`);let n=this.textures.get(e);n&&this.gl.deleteTexture(n),this.textureUnitMap.has(e)||this.textureUnitMap.set(e,this.textureUnitMap.size);let r=this.textureUnitMap.get(e);this.gl.activeTexture(this.gl.TEXTURE0+r);let i=this.gl.createTexture();this.gl.bindTexture(this.gl.TEXTURE_2D,i),this.gl.texParameteri(this.gl.TEXTURE_2D,this.gl.TEXTURE_WRAP_S,this.gl.CLAMP_TO_EDGE),this.gl.texParameteri(this.gl.TEXTURE_2D,this.gl.TEXTURE_WRAP_T,this.gl.CLAMP_TO_EDGE),this.gl.texParameteri(this.gl.TEXTURE_2D,this.gl.TEXTURE_MIN_FILTER,this.gl.LINEAR),this.gl.texParameteri(this.gl.TEXTURE_2D,this.gl.TEXTURE_MAG_FILTER,this.gl.LINEAR),this.gl.texImage2D(this.gl.TEXTURE_2D,0,this.gl.RGBA,this.gl.RGBA,this.gl.UNSIGNED_BYTE,t),this.mipmaps.includes(e)&&(this.gl.generateMipmap(this.gl.TEXTURE_2D),this.gl.texParameteri(this.gl.TEXTURE_2D,this.gl.TEXTURE_MIN_FILTER,this.gl.LINEAR_MIPMAP_LINEAR));let a=this.gl.getError();if(a!==this.gl.NO_ERROR||i===null){console.error(`Paper Shaders: WebGL error when uploading texture:`,a);return}this.textures.set(e,i);let o=this.uniformLocations[e];if(o){this.gl.uniform1i(o,r);let n=`${e}AspectRatio`,i=this.uniformLocations[n];if(i){let e=t.naturalWidth/t.naturalHeight;this.gl.uniform1f(i,e)}}};areUniformValuesEqual=(e,t)=>e===t?!0:Array.isArray(e)&&Array.isArray(t)&&e.length===t.length?e.every((e,n)=>this.areUniformValuesEqual(e,t[n])):!1;setUniformValues=e=>{this.gl.useProgram(this.program),Object.entries(e).forEach(([e,t])=>{let n=t;if(t instanceof HTMLImageElement&&(n=`${t.src.slice(0,200)}|${t.naturalWidth}x${t.naturalHeight}`),this.areUniformValuesEqual(this.uniformCache[e],n))return;this.uniformCache[e]=n;let r=this.uniformLocations[e];if(!r){console.warn(`Uniform location for ${e} not found`);return}if(t instanceof HTMLImageElement)this.setTextureUniform(e,t);else if(Array.isArray(t)){let n=null,i=null;if(t[0]!==void 0&&Array.isArray(t[0])){let r=t[0].length;if(t.every(e=>e.length===r))n=t.flat(),i=r;else{console.warn(`All child arrays must be the same length for ${e}`);return}}else n=t,i=n.length;switch(i){case 2:this.gl.uniform2fv(r,n);break;case 3:this.gl.uniform3fv(r,n);break;case 4:this.gl.uniform4fv(r,n);break;case 9:this.gl.uniformMatrix3fv(r,!1,n);break;case 16:this.gl.uniformMatrix4fv(r,!1,n);break;default:console.warn(`Unsupported uniform array length: ${i}`)}}else typeof t==`number`?this.gl.uniform1f(r,t):typeof t==`boolean`?this.gl.uniform1i(r,+!!t):console.warn(`Unsupported uniform type for ${e}: ${typeof t}`)})};getCurrentFrame=()=>this.currentFrame;setFrame=e=>{this.currentFrame=e,this.lastRenderTime=performance.now(),this.render(performance.now())};setSpeed=(e=1)=>{this.speed=e,this.updateCurrentSpeed()};updateCurrentSpeed=()=>{this.setCurrentSpeed(this.ownerDocument.hidden||!this.isInViewport?0:this.speed)};setCurrentSpeed=e=>{this.currentSpeed=e,this.rafId===null&&e!==0&&(this.lastRenderTime=performance.now(),this.rafId=requestAnimationFrame(this.render)),this.rafId!==null&&e===0&&(cancelAnimationFrame(this.rafId),this.rafId=null)};setMaxPixelCount=(e=a)=>{this.maxPixelCount=e,this.handleResize()};setMinPixelRatio=(e=2)=>{this.minPixelRatio=e,this.handleResize()};setUniforms=e=>{this.setUniformValues(e),this.providedUniforms={...this.providedUniforms,...e},this.render(performance.now())};handleDocumentVisibilityChange=()=>{this.updateCurrentSpeed()};dispose=()=>{this.hasBeenDisposed=!0,this.rafId!==null&&(cancelAnimationFrame(this.rafId),this.rafId=null),this.gl&&this.program&&(this.textures.forEach(e=>{this.gl.deleteTexture(e)}),this.textures.clear(),this.gl.deleteProgram(this.program),this.program=null,this.gl.bindBuffer(this.gl.ARRAY_BUFFER,null),this.gl.bindBuffer(this.gl.ELEMENT_ARRAY_BUFFER,null),this.gl.bindRenderbuffer(this.gl.RENDERBUFFER,null),this.gl.bindFramebuffer(this.gl.FRAMEBUFFER,null),this.gl.getError()),this.resizeObserver&&=(this.resizeObserver.disconnect(),null),this.intersectionObserver&&=(this.intersectionObserver.disconnect(),null),visualViewport?.removeEventListener(`resize`,this.handleVisualViewportChange),this.ownerDocument.removeEventListener(`visibilitychange`,this.handleDocumentVisibilityChange),this.uniformLocations={},this.canvasElement.remove(),delete this.parentElement.paperShaderMount}};function s(e,t,n){let r=e.createShader(t);return r?(e.shaderSource(r,n),e.compileShader(r),e.getShaderParameter(r,e.COMPILE_STATUS)?r:(console.error(`An error occurred compiling the shaders: `+e.getShaderInfoLog(r)),e.deleteShader(r),null)):null}function c(e,t,n){let r=e.getShaderPrecisionFormat(e.FRAGMENT_SHADER,e.MEDIUM_FLOAT),i=r?r.precision:null;i&&i<23&&(t=t.replace(/precision\s+(lowp|mediump)\s+float;/g,`precision highp float;`),n=n.replace(/precision\s+(lowp|mediump)\s+float/g,`precision highp float`).replace(/\b(uniform|varying|attribute)\s+(lowp|mediump)\s+(\w+)/g,`$1 highp $3`));let a=s(e,e.VERTEX_SHADER,t),o=s(e,e.FRAGMENT_SHADER,n);if(!a||!o)return null;let c=e.createProgram();return c?(e.attachShader(c,a),e.attachShader(c,o),e.linkProgram(c),e.getProgramParameter(c,e.LINK_STATUS)?(e.detachShader(c,a),e.detachShader(c,o),e.deleteShader(a),e.deleteShader(o),c):(console.error(`Unable to initialize the shader program: `+e.getProgramInfoLog(c)),e.deleteProgram(c),e.deleteShader(a),e.deleteShader(o),null)):null}var l=`@layer paper-shaders {
  :where([data-paper-shader]) {
    isolation: isolate;
    position: relative;

    & canvas {
      contain: strict;
      display: block;
      position: absolute;
      inset: 0;
      z-index: -1;
      width: 100%;
      height: 100%;
      border-radius: inherit;
      corner-shape: inherit;
    }
  }
}`;function u(){let e=navigator.userAgent.toLowerCase();return e.includes(`safari`)&&!e.includes(`chrome`)&&!e.includes(`android`)}function d(e){let t=visualViewport?.scale??1,n=visualViewport?.width??window.innerWidth,r=window.innerWidth-e.documentElement.clientWidth,i=t*n+r,a=outerWidth/i,o=Math.round(100*a);return o%5==0?o/100:o===33?1/3:o===67?2/3:o===133?4/3:a}var f={fit:`contain`,scale:1,rotation:0,offsetX:0,offsetY:0,originX:.5,originY:.5,worldWidth:0,worldHeight:0},p={none:0,contain:1,cover:2},m=`#version 300 es
precision mediump float;

uniform sampler2D u_image;

uniform vec2 u_resolution;
uniform float u_time;

uniform vec4 u_colorBack;
uniform vec4 u_colorTint;

uniform float u_softness;
uniform float u_repetition;
uniform float u_shiftRed;
uniform float u_shiftBlue;
uniform float u_distortion;
uniform float u_contour;
uniform float u_angle;

uniform float u_shape;
uniform bool u_isImage;

in vec2 v_objectUV;
in vec2 v_responsiveUV;
in vec2 v_responsiveBoxGivenSize;
in vec2 v_imageUV;

out vec4 fragColor;


#define TWO_PI 6.28318530718
#define PI 3.14159265358979323846


vec2 rotate(vec2 uv, float th) {
  return mat2(cos(th), sin(th), -sin(th), cos(th)) * uv;
}


vec3 permute(vec3 x) { return mod(((x * 34.0) + 1.0) * x, 289.0); }
float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
    -0.577350269189626, 0.024390243902439);
  vec2 i = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1;
  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
    + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy),
      dot(x12.zw, x12.zw)), 0.0);
  m = m * m;
  m = m * m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g;
  g.x = a0.x * x0.x + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}


float getColorChanges(float c1, float c2, float stripe_p, vec3 w, float blur, float bump, float tint) {

  float ch = mix(c2, c1, smoothstep(.0, 2. * blur, stripe_p));

  float border = w[0];
  ch = mix(ch, c2, smoothstep(border, border + 2. * blur, stripe_p));

  if (u_isImage == true) {
    bump = smoothstep(.2, .8, bump);
  }
  border = w[0] + .4 * (1. - bump) * w[1];
  ch = mix(ch, c1, smoothstep(border, border + 2. * blur, stripe_p));

  border = w[0] + .5 * (1. - bump) * w[1];
  ch = mix(ch, c2, smoothstep(border, border + 2. * blur, stripe_p));

  border = w[0] + w[1];
  ch = mix(ch, c1, smoothstep(border, border + 2. * blur, stripe_p));

  float gradient_t = (stripe_p - w[0] - w[1]) / w[2];
  float gradient = mix(c1, c2, smoothstep(0., 1., gradient_t));
  ch = mix(ch, gradient, smoothstep(border, border + .5 * blur, stripe_p));

  // Tint color is applied with color burn blending
  ch = mix(ch, 1. - min(1., (1. - ch) / max(tint, 0.0001)), u_colorTint.a);
  return ch;
}

float getImgFrame(vec2 uv, float th) {
  float frame = 1.;
  frame *= smoothstep(0., th, uv.y);
  frame *= 1.0 - smoothstep(1. - th, 1., uv.y);
  frame *= smoothstep(0., th, uv.x);
  frame *= 1.0 - smoothstep(1. - th, 1., uv.x);
  return frame;
}

float blurEdge3x3(sampler2D tex, vec2 uv, vec2 dudx, vec2 dudy, float radius, float centerSample) {
  vec2 texel = 1.0 / vec2(textureSize(tex, 0));
  vec2 r = radius * texel;

  float w1 = 1.0, w2 = 2.0, w4 = 4.0;
  float norm = 16.0;
  float sum = w4 * centerSample;

  sum += w2 * textureGrad(tex, uv + vec2(0.0, -r.y), dudx, dudy).r;
  sum += w2 * textureGrad(tex, uv + vec2(0.0, r.y), dudx, dudy).r;
  sum += w2 * textureGrad(tex, uv + vec2(-r.x, 0.0), dudx, dudy).r;
  sum += w2 * textureGrad(tex, uv + vec2(r.x, 0.0), dudx, dudy).r;

  sum += w1 * textureGrad(tex, uv + vec2(-r.x, -r.y), dudx, dudy).r;
  sum += w1 * textureGrad(tex, uv + vec2(r.x, -r.y), dudx, dudy).r;
  sum += w1 * textureGrad(tex, uv + vec2(-r.x, r.y), dudx, dudy).r;
  sum += w1 * textureGrad(tex, uv + vec2(r.x, r.y), dudx, dudy).r;

  return sum / norm;
}

float lst(float edge0, float edge1, float x) {
  return clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0);
}

void main() {

  const float firstFrameOffset = 2.8;
  float t = .3 * (u_time + firstFrameOffset);

  vec2 uv = v_imageUV;
  vec2 dudx = dFdx(v_imageUV);
  vec2 dudy = dFdy(v_imageUV);
  vec4 img = textureGrad(u_image, uv, dudx, dudy);

  if (u_isImage == false) {
    uv = v_objectUV + .5;
    uv.y = 1. - uv.y;
  }

  float cycleWidth = u_repetition;
  float edge = 0.;
  float contOffset = 1.;

  vec2 rotatedUV = uv - vec2(.5);
  float angle = (-u_angle + 70.) * PI / 180.;
  float cosA = cos(angle);
  float sinA = sin(angle);
  rotatedUV = vec2(
  rotatedUV.x * cosA - rotatedUV.y * sinA,
  rotatedUV.x * sinA + rotatedUV.y * cosA
  ) + vec2(.5);

  // u_contour is applied in 2 separate ranges:
  // - 0 to .4 sets the edge hardness, saturated above .4 (both branches below)
  // - .5 to 1 warps the stripes direction along the edges, inactive below .5 (see u_contour range 2)
  if (u_isImage == true) {
    float edgeRaw = img.r;
    edge = blurEdge3x3(u_image, uv, dudx, dudy, 6., edgeRaw);
    edge = pow(edge, 1.6);
    edge *= mix(0.0, 1.0, smoothstep(0.0, 0.4, u_contour));
  } else {
    if (u_shape < 1.) {
      // full-fill on canvas
      vec2 borderUV = v_responsiveUV + .5;
      float ratio = v_responsiveBoxGivenSize.x / v_responsiveBoxGivenSize.y;
      vec2 mask = min(borderUV, 1. - borderUV);
      vec2 pixel_thickness = min(250. / v_responsiveBoxGivenSize, vec2(.5));
      float maskX = smoothstep(0.0, pixel_thickness.x, mask.x);
      float maskY = smoothstep(0.0, pixel_thickness.y, mask.y);
      maskX = pow(maskX, .25);
      maskY = pow(maskY, .25);
      edge = clamp(1. - maskX * maskY, 0., 1.);

      uv = v_responsiveUV;
      if (ratio > 1.) {
        uv.y /= ratio;
      } else {
        uv.x *= ratio;
      }
      uv += .5;
      uv.y = 1. - uv.y;

      cycleWidth *= 2.;
      contOffset = 1.5;

    } else if (u_shape < 2.) {
      // circle
      vec2 shapeUV = uv - .5;
      shapeUV *= .67;
      edge = pow(clamp(3. * length(shapeUV), 0., 1.), 18.);
    } else if (u_shape < 3.) {
      // daisy
      vec2 shapeUV = uv - .5;
      shapeUV *= 1.68;

      float r = length(shapeUV) * 2.;
      float a = atan(shapeUV.y, shapeUV.x) + .2;
      r *= (1. + .05 * sin(3. * a + 2. * t));
      float f = abs(cos(a * 3.));
      edge = smoothstep(f, f + .7, r);
      edge *= edge;

      uv *= .8;
      cycleWidth *= 1.6;

    } else if (u_shape < 4.) {
      // diamond
      vec2 shapeUV = uv - .5;
      shapeUV = rotate(shapeUV, .25 * PI);
      shapeUV *= 1.42;
      shapeUV += .5;
      vec2 mask = min(shapeUV, 1. - shapeUV);
      vec2 pixel_thickness = vec2(.15);
      float maskX = smoothstep(0.0, pixel_thickness.x, mask.x);
      float maskY = smoothstep(0.0, pixel_thickness.y, mask.y);
      maskX = pow(maskX, .25);
      maskY = pow(maskY, .25);
      edge = clamp(1. - maskX * maskY, 0., 1.);
    } else if (u_shape < 5.) {
      // metaballs
      vec2 shapeUV = uv - .5;
      shapeUV *= 1.3;
      edge = 0.;
      for (int i = 0; i < 5; i++) {
        float fi = float(i);
        float speed = 1.5 + 2./3. * sin(fi * 12.345);
        float angle = -fi * 1.5;
        vec2 dir1 = vec2(cos(angle), sin(angle));
        vec2 dir2 = vec2(cos(angle + 1.57), sin(angle + 1.));
        vec2 traj = .4 * (dir1 * sin(t * speed + fi * 1.23) + dir2 * cos(t * (speed * 0.7) + fi * 2.17));
        float d = length(shapeUV + traj);
        edge += pow(1.0 - clamp(d, 0.0, 1.0), 4.0);
      }
      edge = 1. - smoothstep(.65, .9, edge);
      edge = pow(edge, 4.);
    }

    edge = mix(smoothstep(.9 - 2. * fwidth(edge), .9, edge), edge, smoothstep(0.0, 0.4, u_contour));

  }

  float opacity = 0.;
  if (u_isImage == true) {
    opacity = img.g;
    float frame = getImgFrame(v_imageUV, 0.);
    opacity *= frame;
  } else {
    opacity = 1. - smoothstep(.9 - 2. * fwidth(edge), .9, edge);
    if (u_shape < 2.) {
      edge = 1.2 * edge;
    } else if (u_shape < 5.) {
      edge = 1.8 * pow(edge, 1.5);
    }
  }

  float diagBLtoTR = rotatedUV.x - rotatedUV.y;
  float diagTLtoBR = rotatedUV.x + rotatedUV.y;

  vec3 color = vec3(0.);
  vec3 color1 = vec3(.98, 0.98, 1.);
  vec3 color2 = vec3(.1, .1, .1 + .1 * smoothstep(.7, 1.3, diagTLtoBR));

  vec2 grad_uv = uv - .5;

  float dist = length(grad_uv + vec2(0., .2 * diagBLtoTR));
  grad_uv = rotate(grad_uv, (.25 - .2 * diagBLtoTR) * PI);
  float direction = grad_uv.x;

  float bump = pow(1.8 * dist, 1.2);
  bump = 1. - bump;
  bump *= pow(uv.y, .3);


  float thin_strip_1_ratio = .12 / cycleWidth * (1. - .4 * bump);
  float thin_strip_2_ratio = .07 / cycleWidth * (1. + .4 * bump);
  float wide_strip_ratio = (1. - thin_strip_1_ratio - thin_strip_2_ratio);

  float thin_strip_1_width = cycleWidth * thin_strip_1_ratio;
  float thin_strip_2_width = cycleWidth * thin_strip_2_ratio;

  float noise = snoise(uv - t);

  edge += (1. - edge) * u_distortion * noise;

  direction += diagBLtoTR;
  float contour = 0.;
  direction -= 2. * noise * diagBLtoTR * (smoothstep(0., 1., edge) * (1.0 - smoothstep(0., 1., edge)));
  // u_contour range 2
  direction *= mix(1., 1. - edge, smoothstep(.5, 1., u_contour));
  direction -= 1.7 * edge * smoothstep(.5, 1., u_contour);
  direction += .2 * pow(u_contour, 4.) * (1.0 - smoothstep(0., 1., edge));

  bump *= clamp(pow(uv.y, .1), .3, 1.);
  direction *= (.1 + (1.1 - edge) * bump);

  direction *= (.4 + .6 * (1.0 - smoothstep(.5, 1., edge)));
  direction += .18 * (smoothstep(.1, .2, uv.y) * (1.0 - smoothstep(.2, .4, uv.y)));
  direction += .03 * (smoothstep(.1, .2, 1. - uv.y) * (1.0 - smoothstep(.2, .4, 1. - uv.y)));

  direction *= (.5 + .5 * pow(uv.y, 2.));
  direction *= cycleWidth;
  direction -= t;


  float colorDispersion = (1. - bump);
  colorDispersion = clamp(colorDispersion, 0., 1.);
  float dispersionRed = colorDispersion;
  dispersionRed += .03 * bump * noise;
  dispersionRed += 5. * (smoothstep(-.1, .2, uv.y) * (1.0 - smoothstep(.1, .5, uv.y))) * (smoothstep(.4, .6, bump) * (1.0 - smoothstep(.4, 1., bump)));
  dispersionRed -= diagBLtoTR;

  float dispersionBlue = colorDispersion;
  dispersionBlue *= 1.3;
  dispersionBlue += (smoothstep(0., .4, uv.y) * (1.0 - smoothstep(.1, .8, uv.y))) * (smoothstep(.4, .6, bump) * (1.0 - smoothstep(.4, .8, bump)));
  dispersionBlue -= .2 * edge;

  dispersionRed *= (u_shiftRed / 20.);
  dispersionBlue *= (u_shiftBlue / 20.);

  float blur = 0.;
  float rExtraBlur = 0.;
  float gExtraBlur = 0.;
  if (u_isImage == true) {
    float softness = 0.05 * u_softness;
    blur = softness + .5 * smoothstep(1., 10., u_repetition) * smoothstep(.0, 1., edge);
    float smallCanvasT = 1.0 - smoothstep(100., 500., min(u_resolution.x, u_resolution.y));
    blur += smallCanvasT * smoothstep(.0, 1., edge);
    rExtraBlur = softness * (0.05 + .1 * (u_shiftRed / 20.) * bump);
    gExtraBlur = softness * 0.05 / max(0.001, abs(1. - diagBLtoTR));
  } else {
    blur = u_softness / 15. + .3 * contour;
  }

  vec3 w = vec3(thin_strip_1_width, thin_strip_2_width, wide_strip_ratio);
  w[1] -= .02 * smoothstep(.0, 1., edge + bump);
  float stripe_r = fract(direction + dispersionRed);
  float r = getColorChanges(color1.r, color2.r, stripe_r, w, blur + fwidth(stripe_r) + rExtraBlur, bump, u_colorTint.r);
  float stripe_g = fract(direction);
  float g = getColorChanges(color1.g, color2.g, stripe_g, w, blur + fwidth(stripe_g) + gExtraBlur, bump, u_colorTint.g);
  float stripe_b = fract(direction - dispersionBlue);
  float b = getColorChanges(color1.b, color2.b, stripe_b, w, blur + fwidth(stripe_b), bump, u_colorTint.b);

  color = vec3(r, g, b);
  color *= opacity;

  vec3 bgColor = u_colorBack.rgb * u_colorBack.a;
  color = color + bgColor * (1. - opacity);
  opacity = opacity + u_colorBack.a * (1. - opacity);

  
  color += 1. / 256. * (fract(sin(dot(.014 * gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453123) - .5);


  fragColor = vec4(color, opacity);
}
`,h={measurePerformance:!1,workingSize:512,iterations:40};function g(e){let t=document.createElement(`canvas`),n=t.getContext(`2d`),r=typeof e==`string`&&e.startsWith(`blob:`);return new Promise((i,a)=>{if(!e||!n){a(Error(`Invalid file or canvas context`));return}let o=r&&fetch(e).then(e=>e.headers.get(`Content-Type`)),s=new Image;s.crossOrigin=`anonymous`;let c=performance.now();s.onload=async()=>{let r,l=await o;r=l?l===`image/svg+xml`:typeof e==`string`?e.endsWith(`.svg`)||e.startsWith(`data:image/svg+xml`):e.type===`image/svg+xml`;let u=s.width||s.naturalWidth,d=s.height||s.naturalHeight;if(r){let e=4096,t=u/d;u>d?(u=e,d=e/t):(d=e,u=e*t),s.width=u,s.height=d}let f=Math.min(u,d),p=h.workingSize/f,m=Math.round(u*p),g=Math.round(d*p);h.measurePerformance&&(console.log(`[Processing Mode]`),console.log(`  Original: ${u}\xD7${d}`),console.log(`  Working: ${m}\xD7${g} (${(p*100).toFixed(1)}% scale)`),p<1&&console.log(`  Speedup: ~${Math.round(1/(p*p))}\xD7`)),t.width=u,t.height=d;let y=document.createElement(`canvas`);y.width=m,y.height=g;let b=y.getContext(`2d`);b.drawImage(s,0,0,m,g);let x=performance.now(),S=b.getImageData(0,0,m,g).data,C=new Uint8Array(m*g),w=new Uint8Array(m*g),T=0;for(let e=0,t=0;e<S.length;e+=4,t++){let n=S[e+3]===0?0:1;C[t]=n,T+=n}let E=[],D=[];for(let e=0;e<g;e++)for(let t=0;t<m;t++){let n=e*m+t;if(!C[n])continue;let r=!1;r=t===0||t===m-1||e===0||e===g-1||!C[n-1]||!C[n+1]||!C[n-m]||!C[n+m]||!C[n-m-1]||!C[n-m+1]||!C[n+m-1]||!C[n+m+1],r?(w[n]=1,E.push(n)):D.push(n)}h.measurePerformance&&(console.log(`[Mask Building] Time: ${(performance.now()-x).toFixed(2)}ms`),console.log(`  Shape pixels: ${T} / ${m*g} (${(T/(m*g)*100).toFixed(1)}%)`),console.log(`  Interior pixels: ${D.length}`),console.log(`  Boundary pixels: ${E.length}`));let O=_(C,w,new Uint32Array(D),new Uint32Array(E),m,g),k=performance.now(),A=v(O,C,w,m,g);h.measurePerformance&&console.log(`[Poisson Solve] Time: ${(performance.now()-k).toFixed(2)}ms`);let j=0,M;for(let e=0;e<D.length;e++){let t=D[e];A[t]>j&&(j=A[t])}let N=document.createElement(`canvas`);N.width=m,N.height=g;let P=N.getContext(`2d`),F=P.createImageData(m,g);for(let e=0;e<g;e++)for(let t=0;t<m;t++){let n=e*m+t,r=n*4;if(!C[n])F.data[r]=255,F.data[r+1]=255,F.data[r+2]=255,F.data[r+3]=0;else{let e=255*(1-A[n]/j);F.data[r]=e,F.data[r+1]=e,F.data[r+2]=e,F.data[r+3]=255}}P.putImageData(F,0,0),n.imageSmoothingEnabled=!0,n.imageSmoothingQuality=`high`,n.drawImage(N,0,0,m,g,0,0,u,d);let I=n.getImageData(0,0,u,d),L=document.createElement(`canvas`);L.width=u,L.height=d;let R=L.getContext(`2d`);R.drawImage(s,0,0,u,d);let z=R.getImageData(0,0,u,d);for(let e=0;e<I.data.length;e+=4){let t=z.data[e+3],n=I.data[e+3];t===0?(I.data[e]=255,I.data[e+1]=0):(I.data[e]=n===0?0:I.data[e],I.data[e+1]=t),I.data[e+2]=255,I.data[e+3]=255}n.putImageData(I,0,0),M=I,t.toBlob(e=>{if(!e){a(Error(`Failed to create PNG blob`));return}if(h.measurePerformance){let e=performance.now()-c;if(console.log(`[Total Processing Time] ${e.toFixed(2)}ms`),p<1){let t=e*(u*d/(m*g))**1.5;console.log(`[Estimated time at full resolution] ~${t.toFixed(0)}ms`),console.log(`[Time saved] ~${(t-e).toFixed(0)}ms (${Math.round(t/e)}\xD7 faster)`)}}i({imageData:M,pngBlob:e})},`image/png`)},s.onerror=()=>a(Error(`Failed to load image`)),s.src=typeof e==`string`?e:URL.createObjectURL(e)})}function _(e,t,n,r,i,a){let o=n.length,s=new Int32Array(o*4);for(let t=0;t<o;t++){let r=n[t],o=r%i,c=Math.floor(r/i);s[t*4+0]=o<i-1&&e[r+1]?r+1:-1,s[t*4+1]=o>0&&e[r-1]?r-1:-1,s[t*4+2]=c>0&&e[r-i]?r-i:-1,s[t*4+3]=c<a-1&&e[r+i]?r+i:-1}return{interiorPixels:n,boundaryPixels:r,pixelCount:o,neighborIndices:s}}function v(e,t,n,r,i){let a=h.iterations,o=.01,s=new Float32Array(r*i),{interiorPixels:c,neighborIndices:l,pixelCount:u}=e,d=performance.now(),f=1.9,p=[],m=[];for(let e=0;e<u;e++){let t=c[e];(t%r+Math.floor(t/r))%2==0?p.push(e):m.push(e)}for(let e=0;e<a;e++){for(let e of p){let t=c[e],n=l[e*4+0],r=l[e*4+1],i=l[e*4+2],a=l[e*4+3],u=0;n>=0&&(u+=s[n]),r>=0&&(u+=s[r]),i>=0&&(u+=s[i]),a>=0&&(u+=s[a]),s[t]=f*((o+u)/4)+-.8999999999999999*s[t]}for(let e of m){let t=c[e],n=l[e*4+0],r=l[e*4+1],i=l[e*4+2],a=l[e*4+3],u=0;n>=0&&(u+=s[n]),r>=0&&(u+=s[r]),i>=0&&(u+=s[i]),a>=0&&(u+=s[a]),s[t]=f*((o+u)/4)+-.8999999999999999*s[t]}}if(h.measurePerformance){let e=performance.now()-d;console.log(`[Optimized Poisson Solver (SOR \u03C9=${f})]`),console.log(`  Working size: ${r}\xD7${i}`),console.log(`  Iterations: ${a}`),console.log(`  Time: ${e.toFixed(2)}ms`),console.log(`  Interior pixels processed: ${u}`),console.log(`  Speed: ${(a*u/(e*1e3)).toFixed(2)} Mpixels/sec`)}return s}var y={none:0,circle:1,daisy:2,diamond:3,metaballs:4};function b(e){if(Array.isArray(e))return e.length===4?e:e.length===3?[...e,1]:E;if(typeof e!=`string`)return E;let t,n,r,i=1;if(e.startsWith(`#`))[t,n,r,i]=x(e);else if(e.startsWith(`rgb`)){let a=S(e);if(a===null)return E;[t,n,r,i]=a}else if(e.startsWith(`hsl`)){let a=C(e);if(a===null)return E;[t,n,r,i]=w(a)}else return console.error(`Unsupported color format`,e),E;return[T(t,0,1),T(n,0,1),T(r,0,1),T(i,0,1)]}function x(e){return e=e.replace(/^#/,``),(e.length===3||e.length===4)&&(e=e.split(``).map(e=>e+e).join(``)),e.length===6&&(e+=`ff`),/^[0-9a-f]{8}$/i.test(e)?[parseInt(e.slice(0,2),16)/255,parseInt(e.slice(2,4),16)/255,parseInt(e.slice(4,6),16)/255,parseInt(e.slice(6,8),16)/255]:(console.warn(`Invalid hex color`),E)}function S(e){let t=e.match(/^rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([0-9.]+))?\s*\)$/i);return t?[parseInt(t[1]??`0`)/255,parseInt(t[2]??`0`)/255,parseInt(t[3]??`0`)/255,t[4]===void 0?1:parseFloat(t[4])]:null}function C(e){let t=e.match(/^hsla?\s*\(\s*(\d+)\s*,\s*(\d+)%\s*,\s*(\d+)%\s*(?:,\s*([0-9.]+))?\s*\)$/i);return t?[parseInt(t[1]??`0`),parseInt(t[2]??`0`),parseInt(t[3]??`0`),t[4]===void 0?1:parseFloat(t[4])]:null}function w(e){let[t,n,r,i]=e,a=t/360,o=n/100,s=r/100,c,l,u;if(n===0)c=l=u=s;else{let e=(e,t,n)=>(n<0&&(n+=1),n>1&&--n,n<1/6?e+(t-e)*6*n:n<1/2?t:n<2/3?e+(t-e)*(2/3-n)*6:e),t=s<.5?s*(1+o):s+o-s*o,n=2*s-t;c=e(n,t,a+1/3),l=e(n,t,a),u=e(n,t,a-1/3)}return[c,l,u,i]}var T=(e,t,n)=>Math.min(Math.max(e,t),n),E=[.5,.5,.5,1],D=n(e(),1);function O(e){let t=D.useRef(void 0),n=D.useCallback(t=>{let n=e.map(e=>{if(e!=null){if(typeof e==`function`){let n=e,r=n(t);return typeof r==`function`?r:()=>{n(null)}}return e.current=t,()=>{e.current=null}}});return()=>{n.forEach(e=>e?.())}},e);return D.useMemo(()=>e.every(e=>e==null)?null:e=>{t.current&&=(t.current(),void 0),e!=null&&(t.current=n(e))},e)}function k(e){if(e.naturalWidth<1024&&e.naturalHeight<1024){if(e.naturalWidth<1||e.naturalHeight<1)return;let t=e.naturalWidth/e.naturalHeight;e.width=Math.round(t>1?1024*t:1024),e.height=Math.round(t>1?1024:1024/t)}}var A=r();async function j(e){let t={},n=[],r=e=>{try{return e.startsWith(`/`)||new URL(e),!0}catch{return!1}},i=e=>{try{return!e.startsWith(`/`)&&new URL(e,window.location.origin).origin!==window.location.origin}catch{return!1}};return Object.entries(e).forEach(([e,a])=>{if(typeof a==`string`){let o=a||`data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==`;if(!r(o)){console.warn(`Uniform "${e}" has invalid URL "${o}". Skipping image loading.`);return}let s=new Promise((n,r)=>{let a=new Image;i(o)&&(a.crossOrigin=`anonymous`),a.onload=()=>{k(a),t[e]=a,n()},a.onerror=()=>{console.error(`Could not set uniforms. Failed to load image at ${o}`),r()},a.src=o});n.push(s)}else if(a instanceof HTMLImageElement){let r=a.decode().then(()=>{k(a),t[e]=a});n.push(r)}else t[e]=a}),await Promise.all(n),t}var M=(0,D.forwardRef)(function({fragmentShader:e,uniforms:t,webGlContextAttributes:n,speed:r=0,frame:i=0,width:a,height:s,minPixelRatio:c,maxPixelCount:l,mipmaps:u,style:d,...f},p){let[m,h]=(0,D.useState)(!1),g=(0,D.useRef)(null),_=(0,D.useRef)(null),v=(0,D.useRef)(n);(0,D.useEffect)(()=>((async()=>{let n=await j(t);g.current&&!_.current&&(_.current=new o(g.current,e,n,v.current,r,i,c,l,u),h(!0))})(),()=>{_.current?.dispose(),_.current=null}),[e]),(0,D.useEffect)(()=>{let e=!1;return(async()=>{let n=await j(t);e||_.current?.setUniforms(n)})(),()=>{e=!0}},[t,m]),(0,D.useEffect)(()=>{_.current?.setSpeed(r)},[r,m]),(0,D.useEffect)(()=>{_.current?.setMaxPixelCount(l)},[l,m]),(0,D.useEffect)(()=>{_.current?.setMinPixelRatio(c)},[c,m]),(0,D.useEffect)(()=>{_.current?.setFrame(i)},[i,m]);let y=O([g,p]);return(0,A.jsx)(`div`,{ref:y,style:a!==void 0||s!==void 0?{width:typeof a==`string`&&isNaN(+a)===!1?+a:a,height:typeof s==`string`&&isNaN(+s)===!1?+s:s,...d}:d,...f})});M.displayName=`ShaderMount`;var N=`data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==`,P=e=>typeof e==`object`&&typeof e.then==`function`,F=[];function I(e,t){if(e===t)return!0;if(!e||!t)return!1;let n=e.length;if(t.length!==n)return!1;for(let r=0;r<n;r++)if(e[r]!==t[r])return!1;return!0}function L(e,t=null){t===null&&(t=[e]);for(let e of F)if(I(t,e.keys)){if(Object.prototype.hasOwnProperty.call(e,`error`))throw e.error;if(Object.prototype.hasOwnProperty.call(e,`response`))return e.response;throw e.promise}let n={keys:t,promise:(P(e)?e:e(...t)).then(e=>{n.response=e}).catch(e=>n.error=e)};throw F.push(n),n.promise}var R=(e,t)=>L(e,t),z={name:`Default`,params:{...f,scale:.6,speed:1,frame:0,colorBack:`#AAAAAC`,colorTint:`#ffffff`,distortion:.07,repetition:2,shiftRed:.3,shiftBlue:.3,contour:.4,softness:.1,angle:70,shape:`diamond`}};({...f}),{...f},{...f};var B=(0,D.memo)(function({colorBack:e=z.params.colorBack,colorTint:t=z.params.colorTint,speed:n=z.params.speed,frame:r=z.params.frame,image:i=``,contour:a=z.params.contour,distortion:o=z.params.distortion,softness:s=z.params.softness,repetition:c=z.params.repetition,shiftRed:l=z.params.shiftRed,shiftBlue:u=z.params.shiftBlue,angle:d=z.params.angle,shape:f=z.params.shape,suspendWhenProcessingImage:h=!1,fit:_=z.params.fit,scale:v=z.params.scale,rotation:x=z.params.rotation,originX:S=z.params.originX,originY:C=z.params.originY,offsetX:w=z.params.offsetX,offsetY:T=z.params.offsetY,worldWidth:E=z.params.worldWidth,worldHeight:O=z.params.worldHeight,...k}){let j=typeof i==`string`?i:i.src,[P,F]=(0,D.useState)(N),I;I=h&&typeof window<`u`&&j?R(()=>g(j).then(e=>URL.createObjectURL(e.pngBlob)),[j,`liquid-metal`]):P,(0,D.useLayoutEffect)(()=>{if(h)return;if(!j){F(N);return}let e,t=!0;return g(j).then(n=>{t&&(e=URL.createObjectURL(n.pngBlob),F(e))}),()=>{t=!1}},[j,h]);let L={u_colorBack:b(e),u_colorTint:b(t),u_image:I,u_contour:a,u_distortion:o,u_softness:s,u_repetition:c,u_shiftRed:l,u_shiftBlue:u,u_angle:d,u_isImage:!!i,u_shape:y[f],u_fit:p[_],u_scale:v,u_rotation:x,u_offsetX:w,u_offsetY:T,u_originX:S,u_originY:C,u_worldWidth:E,u_worldHeight:O};return(0,A.jsx)(M,{...k,speed:n,frame:r,fragmentShader:m,mipmaps:[`u_image`],uniforms:L})});function V({animated:e}){let[n,r]=(0,D.useState)(!1),[i,a]=(0,D.useState)(!1),o=(0,D.useRef)(null),s=t();return(0,D.useEffect)(()=>{let e=new IntersectionObserver(([e])=>a(e.isIntersecting));return o.current&&e.observe(o.current),()=>e.disconnect()},[]),(0,A.jsx)(`div`,{className:`liquid-logo`,ref:o,"aria-hidden":`true`,onPointerEnter:()=>r(!0),onPointerLeave:()=>r(!1),children:i&&s&&(0,A.jsx)(B,{image:`/static/ids-mark.svg`,width:44,height:44,maxPixelCount:16384,minPixelRatio:1,speed:e?n?.8:.25:0,distortion:n?.65:.25,repetition:3,softness:.15,colorBack:`#00000000`,colorTint:`#c6f5ab`,fit:`contain`})})}export{V as default};
# 3D operations interface

The existing Flask routes serve one React application with separate Operations, Network traffic, Commands and System logs views. The shipped build in `frontend/dist/` lets Python startup work without Node or a runtime CDN. Fonts and the authored SVG emblem are local.

## Rebuild

Use Node 22.12+ or Node 20.19+ (developed with Node 24.18.0):

```powershell
cd frontend/ui
npm ci
npm run build
```

The build runs TypeScript checking and emits `/static/dist/assets/app.js` and `app.css`, with hashed, lazy graphics chunks. Commit the generated assets with source changes. `npm run dev` serves the development entry and proxies API requests to the local Python server. Use the Python server for authorized writes; its origin checks apply.

## Interaction map

| Requested effect | Implementation |
| --- | --- |
| X-ray hover | Moving over the sensor reveals a deformed wireframe shell and its inner geometry. The X-ray button pins that view for keyboard and touch use. |
| Text hover | Hero letters lift and brighten, with a staggered response. |
| Ripple background | A water-plane ShaderGradient under the sensor; clicking the sensor emits expanding rings at the pointer. |
| Magnetizing lines | Grid vertices are attracted toward the pointer using a distance falloff in the Three.js frame loop. |
| Hover force | The sensor moves toward the pointer; a vertex shader pushes its surface toward the interaction point. The main action also follows the pointer slightly. |
| Liquid distortion | An authored animated surface shader and a Paper LiquidMetal SVG emblem. Hover changes the emblem's distortion and speed. |

The sensor is an abstract interactive illustration, explicitly labeled as such. It does not invent network topology. Status, counters, incidents, commands, flows, benchmark reports and source progress come from the existing local APIs. Scores are not described as certainty or live accuracy. Event labels and incident updates still require a server-validated token, kept only in React memory.

## Motion and rendering

- React Three Fiber 9.8.1 and React 19 are paired. Three.js, ShaderGradient 2.4.20 and Paper Shaders React 0.0.81 versions are locked in the package lock.
- The graphics code is loaded separately from the usable data interface. Sensor DPR is capped at 1.35; the gradient uses pixel density 1; the emblem is bounded to 16,384 pixels.
- The sensor unmounts offscreen. Hidden documents pause rendering and polling. Geometry and custom materials are disposed on unmount.
- Reduced motion and the header's pause control stop visual animation and pointer forces. X-ray remains a usable button. Without WebGL2, the sensor uses a static SVG/CSS illustration. Graphics failures do not remove the data interface.
- Tables scroll within their own regions, keyboard focus is visible, messages are announced, and the authorization dialog traps focus with an inert background.
- Read failures retain previous observations with a visible stale-data notice. Requests time out after ten seconds. Polling refreshes every fifteen seconds while visible.

## Sources and attribution

- [React Three Fiber](https://github.com/pmndrs/react-three-fiber), MIT.
- [ShaderGradient](https://github.com/ruucm/shadergradient), MIT, © ruucm and stone-skipper.
- [Paper liquid-logo](https://github.com/paper-design/liquid-logo), the visual reference named in the request, uses **PolyForm Shield 1.0.0**. Its license is preserved in `frontend-licenses/paper-liquid-logo-PolyForm-Shield.md`. No app code is copied from that repository.
- The integrated npm packages `@paper-design/shaders` and `@paper-design/shaders-react` 0.0.81 ship Apache-2.0 licenses and Paper copyright notices. Those notices are preserved separately; the liquid-logo repository is not described as MIT.
- Runtime package versions, licenses and font notices: [frontend license inventory](frontend-licenses/PACKAGE_LICENSES.md).

The interface changes do not complete independent model qualification or repair the Windows Sysmon event channel. Those remain tracked in the implementation status.

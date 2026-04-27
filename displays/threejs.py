"""Three.js display addon — 3D visualizations for math and physics."""

import json
from ._base import BG_VOID, TEXT_SECONDARY
from ._page import write_page

THREE_HEAD = (
    '<script type="importmap">'
    '{"imports":{'
    '"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",'
    '"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"'
    '}}'
    '</script>'
    f'<style>'
    f'html,body{{overflow:hidden;}}'
    f'.tp-body{{padding:0;height:100vh;}}'
    f'canvas{{display:block;}}'
    f'#info{{position:absolute;top:12px;left:16px;color:{TEXT_SECONDARY};'
    f'font-size:11px;pointer-events:none;z-index:10;}}'
    f'</style>'
)


def _three_body(body_js, data):
    data_script = (
        f'const data = {json.dumps(data)};' if data is not None else ''
    )
    return (
        '<div id="info"></div>'
        '<script type="module">'
        'import * as THREE from "three";'
        'import { OrbitControls } from "three/addons/controls/OrbitControls.js";'
        'const scene = new THREE.Scene();'
        f'scene.background = new THREE.Color("{BG_VOID}");'
        'const camera = new THREE.PerspectiveCamera(45,'
        ' window.innerWidth/window.innerHeight, 0.1, 1000);'
        'camera.position.set(4, 3, 4);'
        'const renderer = new THREE.WebGLRenderer({antialias:true});'
        'renderer.setSize(window.innerWidth, window.innerHeight);'
        'renderer.setPixelRatio(window.devicePixelRatio);'
        'document.body.appendChild(renderer.domElement);'
        'scene.add(new THREE.AmbientLight(0x444444));'
        'const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);'
        'dirLight.position.set(5, 10, 7);'
        'scene.add(dirLight);'
        'const axes = new THREE.AxesHelper(2);'
        'axes.material.opacity = 0.4; axes.material.transparent = true;'
        'scene.add(axes);'
        'const gridHelper = new THREE.GridHelper(6, 12, 0x222228, 0x222228);'
        'scene.add(gridHelper);'
        'const colors = {'
        'blue:0x6e73ff, green:0x34d399, red:0xf87171,'
        ' yellow:0xfbbf24, cyan:0x22d3ee, purple:0xc084fc, text:0xc8c8d0};'
        'function setInfo(text){document.getElementById("info").textContent = text;}'
        f'{data_script}'
        f'{body_js}'
        'const controls = new OrbitControls(camera, renderer.domElement);'
        'controls.enableDamping = true;'
        'if (typeof _target !== "undefined") controls.target.copy(_target);'
        'controls.update();'
        '(function animate(){'
        'requestAnimationFrame(animate);'
        'controls.update();'
        'if (typeof onFrame === "function") onFrame();'
        'renderer.render(scene, camera);'
        '})();'
        'window.addEventListener("resize", () => {'
        'camera.aspect = window.innerWidth/window.innerHeight;'
        'camera.updateProjectionMatrix();'
        'renderer.setSize(window.innerWidth, window.innerHeight);'
        '});'
        '</script>'
    )


def threejs_scaffold(body_js, data=None):
    """Generate complete HTML for a Three.js visualization."""
    from ._page import render_page
    return render_page(_three_body(body_js, data), head=THREE_HEAD)


def show_threejs(js_code, data=None, filename='index.html', title=None,
                 name=None, display_id=None):
    """Write a Three.js 3D visualization to the display.

    Args:
        js_code: JavaScript (ES module) using scene, camera, renderer, THREE,
                 colors, setInfo. Set `_target` to a Vector3 to change orbit
                 center. Define `onFrame()` for per-frame updates.
        data: optional data embedded as JSON (accessible as `data` in JS)
        filename: output filename for unnamed displays
        title: optional title (shown as a small caption above the canvas)
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    body = _three_body(js_code, data)
    return write_page(
        body, name=name, display_id=display_id, filename=filename,
        title=title, head=THREE_HEAD,
    )


def show_surface(func_js, x_range=(-2, 2), z_range=(-2, 2), resolution=50,
                 title='', filename='index.html', name=None, display_id=None):
    """Show a 3D surface plot y = f(x, z).

    Args:
        func_js: JavaScript expression for y given x, z (e.g., "Math.sin(x) * Math.cos(z)")
        x_range: (min, max) for x axis
        z_range: (min, max) for z axis
        resolution: grid points per axis
        title: optional info text
        filename: output filename for unnamed displays
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    js = f'''
  const xMin = {x_range[0]}, xMax = {x_range[1]};
  const zMin = {z_range[0]}, zMax = {z_range[1]};
  const res = {resolution};

  const vertices = [], colorArr = [], indices = [];
  let yMin = Infinity, yMax = -Infinity;
  const grid = [];
  for (let i = 0; i <= res; i++) {{
    grid[i] = [];
    const x = xMin + (xMax - xMin) * i / res;
    for (let j = 0; j <= res; j++) {{
      const z = zMin + (zMax - zMin) * j / res;
      const y = {func_js};
      grid[i][j] = y;
      if (y < yMin) yMin = y;
      if (y > yMax) yMax = y;
      vertices.push(x, y, z);
    }}
  }}

  const range = yMax - yMin || 1;
  for (let i = 0; i <= res; i++)
    for (let j = 0; j <= res; j++) {{
      const t = (grid[i][j] - yMin) / range;
      const c = new THREE.Color().setHSL(0.65 - t * 0.65, 0.8, 0.5);
      colorArr.push(c.r, c.g, c.b);
    }}

  for (let i = 0; i < res; i++)
    for (let j = 0; j < res; j++) {{
      const a = i * (res + 1) + j, b = a + 1;
      const c = (i + 1) * (res + 1) + j, d = c + 1;
      indices.push(a, c, b, b, c, d);
    }}

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colorArr, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();

  scene.add(new THREE.Mesh(geometry, new THREE.MeshPhongMaterial({{
    vertexColors: true, side: THREE.DoubleSide, shininess: 30,
  }})));

  scene.add(new THREE.LineSegments(
    new THREE.WireframeGeometry(geometry),
    new THREE.LineBasicMaterial({{ color: 0x222228, opacity: 0.3, transparent: true }})
  ));

  scene.remove(gridHelper);
  const span = Math.max(xMax - xMin, zMax - zMin);
  scene.add(new THREE.GridHelper(span * 1.2, 12, 0x222228, 0x222228));

  setInfo({json.dumps(title)} || 'y = {func_js}');

  const midY = (yMin + yMax) / 2;
  camera.position.set(span * 0.9, span * 1.4, span * 0.9);
  const _target = new THREE.Vector3(0, midY, 0);
'''
    return show_threejs(js, filename=filename, name=name, display_id=display_id)


def show_vector_field(field_js, range=(-2, 2), resolution=5, title='',
                      filename='index.html', name=None, display_id=None):
    """Show a 3D vector field.

    Args:
        field_js: JavaScript returning [vx, vy, vz] given x, y, z
                  (e.g., "[-y, x, 0]" for a rotation field)
        range: (min, max) for all axes
        resolution: points per axis
        title: optional info text
        filename: output filename for unnamed displays
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    js = f'''
  const lo = {range[0]}, hi = {range[1]}, res = {resolution};
  const step = (hi - lo) / res;

  for (let i = 0; i <= res; i++)
    for (let j = 0; j <= res; j++)
      for (let k = 0; k <= res; k++) {{
        const x = lo + step * i, y = lo + step * j, z = lo + step * k;
        const [vx, vy, vz] = (function(x,y,z) {{ return {field_js}; }})(x,y,z);
        const mag = Math.sqrt(vx*vx + vy*vy + vz*vz);
        if (mag < 1e-10) continue;
        const dir = new THREE.Vector3(vx, vy, vz).normalize();
        const len = Math.min(mag * step * 0.8, step * 0.9);
        const c = new THREE.Color().setHSL(0.65 - Math.min(mag, 2) / 2 * 0.65, 0.8, 0.5);
        scene.add(new THREE.ArrowHelper(dir, new THREE.Vector3(x, y, z), len, c.getHex(), len * 0.3, len * 0.15));
      }}

  setInfo({json.dumps(title)} || 'Vector field');
  camera.position.set({range[1]*2}, {range[1]*2}, {range[1]*2});
'''
    return show_threejs(js, filename=filename, name=name, display_id=display_id)


def show_parametric(curve_js, t_range=(0, 6.283), steps=200, color=0x6e73ff,
                    title='', filename='index.html', name=None, display_id=None):
    """Show a parametric 3D curve.

    Args:
        curve_js: JavaScript returning [x, y, z] given t
                  (e.g., "[Math.cos(t), Math.sin(t), t/5]" for a helix)
        t_range: (min, max) for parameter t
        steps: number of line segments
        color: line color (hex int)
        title: optional info text
        filename: output filename for unnamed displays
        name: if given, writes to `<name>.html` — appears as a named tab.
        display_id: alias for `name`.
    """
    js = f'''
  const points = [];
  for (let i = 0; i <= {steps}; i++) {{
    const t = {t_range[0]} + ({t_range[1]} - {t_range[0]}) * i / {steps};
    const [x, y, z] = (function(t) {{ return {curve_js}; }})(t);
    points.push(new THREE.Vector3(x, y, z));
  }}

  scene.add(new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(points),
    new THREE.LineBasicMaterial({{ color: {color} }})
  ));

  const dotGeo = new THREE.SphereGeometry(0.04);
  const s = new THREE.Mesh(dotGeo, new THREE.MeshBasicMaterial({{ color: colors.green }}));
  s.position.copy(points[0]); scene.add(s);
  const e = new THREE.Mesh(dotGeo, new THREE.MeshBasicMaterial({{ color: colors.red }}));
  e.position.copy(points[points.length - 1]); scene.add(e);

  setInfo({json.dumps(title)} || 'Parametric curve');
'''
    return show_threejs(js, filename=filename, name=name, display_id=display_id)

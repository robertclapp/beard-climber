"""Shared helpers for the Beard Climber retro pipeline (Blender 4.x, Linux/macOS).

* Palettes are dicts of ROLE -> "#rrggbb". Every level ships its own 16-colour
  palette (see levels/*.py); models only ever reference roles ("hair2",
  "skin", "acc1", ...), so one model renders correctly in any level.
* MeshBuilder batches many low-poly primitives into ONE mesh object (fast,
  even for a whole beard) with one flat material per palette role.
This module imports cleanly without Blender (postprocess.py uses it).
"""
import math

try:
    import bpy, bmesh
    from mathutils import Matrix, Vector, Euler
except ImportError:          # plain Python (postprocess.py)
    bpy = None

# Palette used for the stand-alone climber sprite sheet (roles the climber needs).
CLIMBER_PALETTE = {
    "black": "#000000", "white": "#f8f8f8", "skin": "#f8b888", "skin_shade": "#c87858",
    "shirt": "#3060e8", "pants": "#283878", "cap": "#f8c800", "bg": "#183048",
    "beanie": "#e83828", "hardhat": "#f8d800", "hardhat_shade": "#c89000",
    "hair1": "#583820", "hair2": "#986038", "hair3": "#c88850", "hair4": "#e8b878",   # for the tangled hat item
}

# Climber-only roles (beanie, hard-hat power-up) are ALIASES of a level's existing
# palette roles, so every level still quantises to its own 16 colours.
# Override per level with L["climber_roles"].
DEFAULT_CLIMBER_ROLES = {"beanie": "acc1", "hardhat": "cap", "hardhat_shade": "acc3"}


def with_roles(pal, roles=None):
    """Palette + alias roles, e.g. {"hardhat": "cap"} -> pal["hardhat"] = pal["cap"]."""
    pal = dict(pal)
    for k, v in {**DEFAULT_CLIMBER_ROLES, **(roles or {})}.items():
        if k not in pal:
            pal[k] = pal[v] if v in pal else v
    return pal


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def palette_rgb(pal):
    """Unique RGB tuples of a role palette (what post-processing quantises to)."""
    out = []
    for v in pal.values():
        c = hex_rgb(v)
        if c not in out:
            out.append(c)
    return out


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


# ---------------------------------------------------------------- Blender side
_PALETTE = dict(CLIMBER_PALETTE)


def set_palette(pal):
    """Select the active role palette; call before building (after clear_scene)."""
    global _PALETTE
    _PALETTE = dict(pal)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0   # don't write .blend1 backups


def material(role):
    """Flat material for a palette role (cached per file)."""
    name = "PAL_" + role
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        r, g, b = (srgb_to_linear(v / 255.0) for v in hex_rgb(_PALETTE[role]))
        mat.diffuse_color = (r, g, b, 1.0)   # Workbench MATERIAL colour mode reads this
        mat.roughness, mat.metallic = 1.0, 0.0
    return mat


def _matrix(loc, rot_deg, scale):
    rot = Euler([math.radians(a) for a in rot_deg]).to_quaternion()
    return Matrix.LocRotScale(Vector(loc), rot, Vector(scale))


class MeshBuilder:
    """Accumulate boxes/discs/spheres into one bmesh, then emit one object.

    Coordinates: X = screen right, Z = screen up, -Y = toward the camera.
    Angles are degrees; rotation about Y ("ry") spins a part in the picture plane.
    """

    def __init__(self):
        self.bm = bmesh.new()
        self.roles = []

    def _tag(self, verts, role):
        if role not in self.roles:
            self.roles.append(role)
        idx = self.roles.index(role)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = idx

    def box(self, size, loc, role, ry=0.0, rot=None):
        m = _matrix(loc, rot or (0, ry, 0), size)
        self._tag(bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)["verts"], role)

    def disc(self, r, loc, role, depth=0.1, seg=8, ry=0.0, sz=1.0):
        """Flat cylinder facing the camera (octagon by default = nice pixel circle)."""
        m = _matrix(loc, (90, ry, 0), (1, sz, 1))
        v = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r,
                                  radius2=r, depth=depth, matrix=m)["verts"]
        self._tag(v, role)

    def sphere(self, r, loc, role, seg=8, rings=6):
        m = _matrix(loc, (0, 0, 0), (1, 1, 1))
        v = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=rings,
                                      radius=r, matrix=m)["verts"]
        self._tag(v, role)

    def bar(self, p0, p1, thick, y, role, depth=0.1):
        """Box spanning 2D points p0->p1 (x, z) in the picture plane."""
        dx, dz = p1[0] - p0[0], p1[1] - p0[1]
        length = math.hypot(dx, dz)
        ang = -math.degrees(math.atan2(dz, dx))   # rotation about +Y
        self.box((length + thick * 0.4, depth, thick),
                 ((p0[0] + p1[0]) / 2, y, (p0[1] + p1[1]) / 2), role, ry=ang)

    def to_object(self, name, collection, location=(0, 0, 0)):
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        for role in self.roles:
            mesh.materials.append(material(role))
        obj = bpy.data.objects.new(name, mesh)
        obj.location = location
        collection.objects.link(obj)
        return obj


def new_collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def setup_workbench(scene, res_x, res_y, transparent=False):
    """Fast CPU-friendly Workbench: flat colours, no AA, exact palette output."""
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x, scene.render.resolution_y = res_x, res_y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.display.render_aa = "OFF"
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    sh = scene.display.shading
    sh.light, sh.color_type = "FLAT", "MATERIAL"
    sh.show_shadows = sh.show_cavity = sh.show_object_outline = False
    sh.show_specular_highlight = False
    sh.background_type = "WORLD"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    r, g, b = (srgb_to_linear(v / 255) for v in hex_rgb(_PALETTE.get("bg", "#000000")))
    scene.world.color = (r, g, b)


def ortho_camera(scene, center, extent, fit="VERTICAL"):
    """Orthographic camera at -Y looking along +Y; `extent` units along `fit` axis."""
    cam = scene.camera
    if cam is None:
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
        scene.collection.objects.link(cam)
        scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.sensor_fit = fit
    cam.data.ortho_scale = extent
    cam.data.clip_end = 100
    cam.location = (center[0], -30, center[1])
    cam.rotation_euler = (math.radians(90), 0, 0)
    return cam

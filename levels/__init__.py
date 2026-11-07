"""Level registry. Each level is one module in this package exposing LEVEL (a dict).

To add a beard: copy e.g. viking.py to mybeard.py, edit palette / style / hazards,
and append "mybeard" to ORDER. Nothing else in the pipeline needs to change.
Level modules must not import bpy at top level (postprocess.py reads palettes
from plain Python); their builder functions only call MeshBuilder methods.
"""
import importlib

ORDER = ["grandpa", "goat", "lumberjack", "mountain", "bigfoot", "elf", "rudolph", "ice", "yeti", "santa", "gnome", "rumpel", "rapunzel", "dwarf", "wizard", "viking", "pirate"]


def load(name):
    L = importlib.import_module(f"{__name__}.{name}").LEVEL
    L.setdefault("id", name)
    return L

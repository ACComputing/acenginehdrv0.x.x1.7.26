#!/usr/bin/env python3
"""
AC Engine 0.1 — A Clickteam Fusion 2.5-Style Game Development IDE
Developed by Team Flames / Samsoft / Flames Co.
FIXED VERSION

A complete visual game creation tool featuring:
  - Storyboard Editor (multi-frame management)
  - Frame Editor (visual scene designer with layers & grid)
  - Event Editor (condition → action programming)
  - Object Library (Active, Backdrop, Counter, Text, Lives, Timer)
  - Properties Inspector
  - Animation Editor (per-object frame sequences)
  - Layer Manager
  - Expression Builder
  - Runtime Engine (play-test your game)
  - Undo/Redo System
  - Full Project Save/Load (.acp JSON)
  - Build stub (export settings)
    
Controls (Runtime):
  Arrow Keys = Move Player
  Space = Jump
  Escape = Close Runtime
"""

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk, colorchooser, font as tkfont
import json
import copy
import math
import time
import os
import uuid
import colorsys

# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

APP_TITLE = "AC Engine 0.1 — Developer Edition"
APP_VERSION = "0.1.0"
WINDOW_SIZE = "1400x900"

# Grid
GRID_SIZE = 16
GRID_COLOR = "#e8e8e8"
GRID_MAJOR_COLOR = "#d0d0d0"
GRID_MAJOR_EVERY = 4  # major line every 4 cells

# Default frame
DEFAULT_FRAME_W = 800
DEFAULT_FRAME_H = 600

# Colors (Clickteam-inspired palette)
COL_BG = "#2b2b2b"
COL_BG_LIGHT = "#3c3c3c"
COL_PANEL = "#333333"
COL_PANEL_HEADER = "#444444"
COL_ACCENT = "#4a90d9"
COL_ACCENT_HOVER = "#5ba0e9"
COL_TEXT = "#e0e0e0"
COL_TEXT_DIM = "#999999"
COL_TOOLBAR = "#383838"
COL_CANVAS_BG = "#1a1a2e"
COL_SELECTION = "#4a90d9"
COL_DANGER = "#d94a4a"
COL_SUCCESS = "#4ad97a"
COL_WARNING = "#d9b44a"

# Custom Button Styles
COL_BTN_FACE = "#E0E0E0"  # Silver
COL_BTN_TEXT = "#0033CC"  # Blue Text
COL_BLUE_TEXT = "#6495ED" # Cornflower Blue for dark backgrounds

# Object type colors
OBJ_COLORS = {
    "Active":   ("#e74c3c", "#c0392b"),
    "Backdrop":  ("#27ae60", "#1e8449"),
    "Counter":   ("#f39c12", "#d68910"),
    "Text":      ("#3498db", "#2980b9"),
    "Lives":     ("#e91e63", "#c2185b"),
    "Timer":     ("#9b59b6", "#7d3c98"),
    "Player":    ("#e74c3c", "#c0392b"),
    "Platform":  ("#27ae60", "#1e8449"),
    "Enemy":     ("#8b4513", "#654321"),
    "Coin":      ("#ffd700", "#daa520"),
    "Trigger":   ("#00bcd4", "#0097a7"),
    "Particle":  ("#ff6f00", "#e65100"),
}

# Event system conditions/actions
CONDITIONS = [
    "Always", "Never", "Once", "Every N ms", "Timer equals",
    "Collides with", "Overlaps", "Is overlapping backdrop",
    "Key pressed", "Key released", "Mouse clicked", "Mouse on object",
    "Compare X", "Compare Y", "Compare counter", "Compare speed",
    "Object is visible", "Object is invisible",
    "Animation finished", "Frame changed",
    "At start of frame", "At end of frame",
    "Number of objects == N", "Object out of playfield",
    "Pick random", "Compare global value",
]

ACTIONS = [
    "Create object", "Destroy", "Set position", "Set X", "Set Y",
    "Set speed", "Set direction", "Bounce", "Stop", "Reverse",
    "Set animation", "Set frame", "Next frame", "Restart animation",
    "Make invisible", "Make visible", "Flash",
    "Set counter to", "Add to counter", "Subtract from counter",
    "Set text", "Set color",
    "Set lives", "Add life", "Subtract life",
    "Go to frame", "Next frame (app)", "Previous frame (app)", "Restart frame",
    "End application", "Pause", "Unpause",
    "Play sound", "Stop sound",
    "Set global value", "Add to global value",
    "Set score", "Add to score",
    "Set effect", "Bring to front", "Send to back",
    "Set layer", "Set alterable value",
]

EXPRESSIONS = [
    "X position", "Y position", "Speed", "Direction",
    "Counter value", "Global value", "Score", "Lives",
    "Frame number", "Timer value",
    "Random(min,max)", "Abs()", "Sin()", "Cos()",
    "Mouse X", "Mouse Y",
    "Object count", "Alterable value",
    "String$", "Mid$", "Len()", "Val()",
    "LoopIndex", "FrameWidth", "FrameHeight",
]


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def uid():
    return uuid.uuid4().hex[:8]

def snap(val, grid=GRID_SIZE):
    return round(val / grid) * grid

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def lerp(a, b, t):
    return a + (b - a) * t

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def darken(hex_color, factor=0.8):
    try:
        r, g, b = hex_to_rgb(hex_color)
        return rgb_to_hex(r*factor, g*factor, b*factor)
    except:
        return hex_color

def lighten(hex_color, factor=1.2):
    try:
        r, g, b = hex_to_rgb(hex_color)
        return rgb_to_hex(min(255, r*factor), min(255, g*factor), min(255, b*factor))
    except:
        return hex_color


# ══════════════════════════════════════════════════════════════════════════════
#  UNDO/REDO SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

class UndoManager:
    def __init__(self, max_history=100):
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = max_history
       
    def push(self, state_snapshot):
        self.undo_stack.append(copy.deepcopy(state_snapshot))
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
       
    def undo(self, current_state):
        if not self.undo_stack:
            return None
        self.redo_stack.append(copy.deepcopy(current_state))
        return self.undo_stack.pop()
       
    def redo(self, current_state):
        if not self.redo_stack:
            return None
        self.undo_stack.append(copy.deepcopy(current_state))
        return self.redo_stack.pop()
       
    def can_undo(self):
        return len(self.undo_stack) > 0
       
    def can_redo(self):
        return len(self.redo_stack) > 0


# ══════════════════════════════════════════════════════════════════════════════
#  PROJECT DATA MODEL
# ══════════════════════════════════════════════════════════════════════════════

def make_default_object(obj_type, x=0, y=0):
    """Create a default game object definition."""
    obj = {
        "id": uid(),
        "type": obj_type,
        "name": f"{obj_type}_{uid()[:4]}",
        "x": x, "y": y,
        "w": 32, "h": 32,
        "layer": 0,
        "visible": True,
        "color": OBJ_COLORS.get(obj_type, ("#888888", "#666666"))[0],
        "outline": OBJ_COLORS.get(obj_type, ("#888888", "#666666"))[1],
        "speed": 0,
        "direction": 0,
        "animations": {"Stopped": [0], "Walking": [0,1,2,1], "Running": [0,1,2,3,2,1], "Jump": [4]},
        "current_anim": "Stopped",
        "anim_frame": 0,
        "anim_speed": 100,
        "movement": "Static",  # Static, Player, Bouncing, Path, Platform, Race Car, 8Dir
        "values": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # alterable values A-J
        "strings": ["", "", ""],
        "counter_value": 0,
        "text_content": "Text" if obj_type == "Text" else "",
        "text_font": "Arial",
        "text_size": 14,
        "lives_count": 3 if obj_type == "Lives" else 0,
        "timer_ms": 0,
        "opacity": 255,
        "rotation": 0,
        "scale_x": 1.0,
        "scale_y": 1.0,
        "solid": obj_type in ("Backdrop", "Platform"),
        "score_value": 0 if obj_type != "Coin" else 100,
        "destroy_on_collect": obj_type == "Coin",
        "shape": "rect",  # rect, oval, triangle
        "flags": {},
    }
       
    # Type-specific defaults
    if obj_type == "Platform":
        obj["w"] = 96
        obj["solid"] = True
        obj["movement"] = "Static"
    elif obj_type == "Player":
        obj["movement"] = "Player"
        obj["speed"] = 5
    elif obj_type == "Enemy":
        obj["movement"] = "Bouncing"
        obj["speed"] = 2
        obj["shape"] = "oval"
    elif obj_type == "Coin":
        obj["shape"] = "oval"
        obj["w"] = 24
        obj["h"] = 24
    elif obj_type == "Counter":
        obj["counter_value"] = 0
        obj["w"] = 64
        obj["h"] = 24
    elif obj_type == "Text":
        obj["w"] = 120
        obj["h"] = 28
    elif obj_type == "Trigger":
        obj["w"] = 48
        obj["h"] = 48
        obj["visible"] = False
    elif obj_type == "Particle":
        obj["w"] = 16
        obj["h"] = 16
        obj["shape"] = "oval"
       
    return obj


def make_default_frame(name="Frame 1", index=0):
    """Create a default frame (scene/level)."""
    return {
        "id": uid(),
        "name": name,
        "index": index,
        "width": DEFAULT_FRAME_W,
        "height": DEFAULT_FRAME_H,
        "bg_color": "#87CEEB",
        "layers": [
            {"name": "Layer 1", "visible": True, "locked": False, "opacity": 255},
        ],
        "objects": [],
        "events": [],  # List of event groups
        "transition_in": "None",
        "transition_out": "None",
        "music": "",
    }


def make_event_group():
    """Create an empty event group (one row in the event editor)."""
    return {
        "id": uid(),
        "active": True,
        "comment": "",
        "conditions": [],
        "actions": [],
    }


def make_condition(cond_type="Always", params=None):
    return {
        "id": uid(),
        "type": cond_type,
        "target": "",
        "params": params or {},
        "negated": False,
    }


def make_action(action_type="Destroy", params=None):
    return {
        "id": uid(),
        "type": action_type,
        "target": "",
        "params": params or {},
    }


def make_default_project():
    """Create a new empty project."""
    return {
        "name": "Untitled Application",
        "author": "Team Flames",
        "version": "1.0",
        "window_width": DEFAULT_FRAME_W,
        "window_height": DEFAULT_FRAME_H,
        "fps": 60,
        "global_values": [0] * 26,
        "global_strings": [""] * 10,
        "score": 0,
        "lives": 3,
        "frames": [make_default_frame()],
        "object_library": [],  # Reusable object templates
        "sounds": [],
        "fonts": [],
        "build_type": "Standalone",  # Standalone, HTML5, Android
        "build_settings": {
            "icon": "",
            "splash": "",
            "fullscreen": False,
            "resizable": True,
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
#  RUNTIME ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class GameRuntime(tk.Toplevel):
    """The play-test runtime window. Interprets frame data + events."""
       
    def __init__(self, master, project, start_frame=0):
        super().__init__(master)
        self.title("AC Engine Runtime")
          
        fw = project["window_width"]
        fh = project["window_height"]
        self.geometry(f"{fw}x{fh}")
        self.resizable(False, False)
          
        self.canvas = tk.Canvas(self, bg="black", width=fw, height=fh, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
          
        self.project = copy.deepcopy(project)
        self.current_frame_idx = start_frame
        self.running = True
        self.paused = False
        self.fps = project.get("fps", 60)
        self.frame_ms = max(1, 1000 // self.fps)
        self.tick = 0
        self.score = 0
        self.lives = project.get("lives", 3)
        self.global_values = list(project.get("global_values", [0]*26))
          
        # Input state
        self.keys = {}
        self.keys_just_pressed = set()
        self.keys_just_released = set()
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_buttons = set()
          
        # Entity state
        self.entities = []
        self.timers = {}
        self.frame_started = False
        self.particles = []
          
        # Load first frame
        self.load_frame(self.current_frame_idx)
          
        # Bindings
        self.bind("<KeyPress>", self.on_key_down)
        self.bind("<KeyRelease>", self.on_key_up)
        self.bind("<Motion>", self.on_mouse_move)
        self.bind("<Button-1>", lambda e: self.mouse_buttons.add(1))
        self.bind("<ButtonRelease-1>", lambda e: self.mouse_buttons.discard(1))
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.focus_force()
          
        self.game_loop()
       
    def close(self):
        self.running = False
        self.destroy()
       
    def on_key_down(self, event):
        if event.keysym == "Escape":
            self.close()
            return
        if event.keysym not in self.keys or not self.keys[event.keysym]:
            self.keys_just_pressed.add(event.keysym)
        self.keys[event.keysym] = True
       
    def on_key_up(self, event):
        self.keys[event.keysym] = False
        self.keys_just_released.add(event.keysym)
       
    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
       
    def load_frame(self, idx):
        """Load frame data into runtime entities."""
        if idx < 0 or idx >= len(self.project["frames"]):
            self.close()
            return
          
        self.current_frame_idx = idx
        frame = self.project["frames"][idx]
        self.canvas.configure(bg=frame.get("bg_color", "#87CEEB"))
          
        self.entities = []
        for obj in frame["objects"]:
            entity = copy.deepcopy(obj)
            entity["dx"] = 0
            entity["dy"] = 0
            entity["grounded"] = False
            entity["alive"] = True
            entity["flash_timer"] = 0
            entity["dir_x"] = 1 if entity.get("movement") != "Static" else 0
            entity["gravity"] = entity.get("movement") in ("Player", "Platform")
            self.entities.append(entity)
          
        self.frame_started = True
        self.tick = 0
       
    def aabb_overlap(self, a, b):
        return (a["x"] < b["x"] + b["w"] and
                a["x"] + a["w"] > b["x"] and
                a["y"] < b["y"] + b["h"] and
                a["y"] + a["h"] > b["y"])
       
    def process_events(self, frame):
        """Simple event interpreter."""
        for group in frame.get("events", []):
            if not group.get("active", True):
                continue
               
            all_conditions_met = True
            for cond in group.get("conditions", []):
                met = self.eval_condition(cond)
                if cond.get("negated", False):
                    met = not met
                if not met:
                    all_conditions_met = False
                    break
               
            if all_conditions_met and group.get("conditions"):
                for action in group.get("actions", []):
                    self.exec_action(action)
       
    def eval_condition(self, cond):
        ctype = cond.get("type", "")
        target = cond.get("target", "")
        params = cond.get("params", {})
          
        if ctype == "Always":
            return True
        elif ctype == "Never":
            return False
        elif ctype == "Once":
            if not cond.get("_fired"):
                cond["_fired"] = True
                return True
            return False
        elif ctype == "At start of frame":
            return self.frame_started
        elif ctype == "Key pressed":
            key = params.get("key", "")
            return self.keys.get(key, False)
        elif ctype == "Every N ms":
            n = params.get("ms", 1000)
            return (self.tick * self.frame_ms) % n < self.frame_ms
        elif ctype == "Collides with":
            src = self.find_entities(target)
            tgt = self.find_entities(params.get("other", ""))
            for s in src:
                for t in tgt:
                    if s["id"] != t["id"] and self.aabb_overlap(s, t):
                        return True
            return False
        elif ctype == "Compare counter":
            ents = self.find_entities(target)
            op = params.get("op", "==")
            val = params.get("value", 0)
            for e in ents:
                cv = e.get("counter_value", 0)
                if self.compare(cv, op, val):
                    return True
            return False
        elif ctype == "Mouse clicked":
            return 1 in self.mouse_buttons
        elif ctype == "Object out of playfield":
            frame = self.project["frames"][self.current_frame_idx]
            ents = self.find_entities(target)
            for e in ents:
                if (e["x"] + e["w"] < -50 or e["x"] > frame["width"] + 50 or
                    e["y"] + e["h"] < -50 or e["y"] > frame["height"] + 50):
                    return True
            return False
          
        return False
       
    def exec_action(self, action):
        atype = action.get("type", "")
        target = action.get("target", "")
        params = action.get("params", {})
          
        if atype == "Destroy":
            for e in self.find_entities(target):
                e["alive"] = False
        elif atype == "Set position":
            for e in self.find_entities(target):
                e["x"] = params.get("x", e["x"])
                e["y"] = params.get("y", e["y"])
        elif atype == "Set X":
            for e in self.find_entities(target):
                e["x"] = params.get("value", 0)
        elif atype == "Set Y":
            for e in self.find_entities(target):
                e["y"] = params.get("value", 0)
        elif atype == "Set speed":
            for e in self.find_entities(target):
                e["speed"] = params.get("value", 0)
        elif atype == "Add to counter":
            for e in self.find_entities(target):
                e["counter_value"] = e.get("counter_value", 0) + params.get("value", 1)
        elif atype == "Set counter to":
            for e in self.find_entities(target):
                e["counter_value"] = params.get("value", 0)
        elif atype == "Add to score":
            self.score += params.get("value", 100)
        elif atype == "Set score":
            self.score = params.get("value", 0)
        elif atype == "Subtract life":
            self.lives = max(0, self.lives - 1)
        elif atype == "Add life":
            self.lives += 1
        elif atype == "Go to frame":
            fidx = params.get("frame", 0)
            self.load_frame(fidx)
        elif atype == "Next frame (app)":
            self.load_frame(self.current_frame_idx + 1)
        elif atype == "Restart frame":
            self.load_frame(self.current_frame_idx)
        elif atype == "End application":
            self.close()
        elif atype == "Make invisible":
            for e in self.find_entities(target):
                e["visible"] = False
        elif atype == "Make visible":
            for e in self.find_entities(target):
                e["visible"] = True
        elif atype == "Flash":
            for e in self.find_entities(target):
                e["flash_timer"] = params.get("duration", 30)
        elif atype == "Bounce":
            for e in self.find_entities(target):
                e["dir_x"] *= -1
                e["dx"] *= -1
        elif atype == "Set global value":
            idx = params.get("index", 0)
            val = params.get("value", 0)
            if 0 <= idx < len(self.global_values):
                self.global_values[idx] = val
        elif atype == "Add to global value":
            idx = params.get("index", 0)
            val = params.get("value", 1)
            if 0 <= idx < len(self.global_values):
                self.global_values[idx] += val
        elif atype == "Create object":
            obj_type = params.get("obj_type", "Active")
            new_obj = make_default_object(obj_type, params.get("x", 0), params.get("y", 0))
            new_obj["dx"] = 0
            new_obj["dy"] = 0
            new_obj["grounded"] = False
            new_obj["alive"] = True
            new_obj["flash_timer"] = 0
            new_obj["dir_x"] = 1
            new_obj["gravity"] = False
            self.entities.append(new_obj)
       
    def find_entities(self, name_or_type):
        results = []
        for e in self.entities:
            if not e.get("alive", True):
                continue
            if e.get("name") == name_or_type or e.get("type") == name_or_type:
                results.append(e)
        return results
       
    def compare(self, a, op, b):
        if op == "==": return a == b
        if op == "!=": return a != b
        if op == "<": return a < b
        if op == "<=": return a <= b
        if op == ">": return a > b
        if op == ">=": return a >= b
        return False
       
    def update_physics(self):
        """Update all entity positions and handle collisions."""
        frame_data = self.project["frames"][self.current_frame_idx]
        fw = frame_data["width"]
        fh = frame_data["height"]
          
        solids = [e for e in self.entities if e.get("alive") and e.get("solid")]
          
        for e in self.entities:
            if not e.get("alive"):
                continue
               
            movement = e.get("movement", "Static")
               
            if movement == "Player":
                # Horizontal
                spd = e.get("speed", 5)
                if self.keys.get("Left"):
                    e["dx"] = -spd
                elif self.keys.get("Right"):
                    e["dx"] = spd
                else:
                    e["dx"] *= 0.7  # friction
                    if abs(e["dx"]) < 0.5:
                        e["dx"] = 0
                  
                # Jump
                if (self.keys.get("Up") or self.keys.get("space")) and e.get("grounded"):
                    e["dy"] = -12
                    e["grounded"] = False
                  
                # Gravity
                e["dy"] += 0.6
                if e["dy"] > 15:
                    e["dy"] = 15
                  
                # Move X
                e["x"] += e["dx"]
                  
                # Resolve X collisions
                for s in solids:
                    if s["id"] == e["id"]:
                        continue
                    if self.aabb_overlap(e, s):
                        if e["dx"] > 0:
                            e["x"] = s["x"] - e["w"]
                        elif e["dx"] < 0:
                            e["x"] = s["x"] + s["w"]
                        e["dx"] = 0
                  
                # Move Y
                e["y"] += e["dy"]
                e["grounded"] = False
                  
                # Resolve Y collisions
                for s in solids:
                    if s["id"] == e["id"]:
                        continue
                    if self.aabb_overlap(e, s):
                        if e["dy"] > 0:
                            e["y"] = s["y"] - e["h"]
                            e["dy"] = 0
                            e["grounded"] = True
                        elif e["dy"] < 0:
                            e["y"] = s["y"] + s["h"]
                            e["dy"] = 0
                  
                # Wrap/clamp
                if e["y"] > fh + 50:
                    e["y"] = 0
                    e["dy"] = 0
                e["x"] = clamp(e["x"], -e["w"], fw)
               
            elif movement == "Bouncing":
                spd = e.get("speed", 2)
                e["x"] += spd * e.get("dir_x", 1)
                  
                # Bounce off edges
                if e["x"] <= 0 or e["x"] + e["w"] >= fw:
                    e["dir_x"] = e.get("dir_x", 1) * -1
                  
                # Bounce off solids
                for s in solids:
                    if s["id"] == e["id"]:
                        continue
                    if self.aabb_overlap(e, s):
                        e["dir_x"] = e.get("dir_x", 1) * -1
                        e["x"] += spd * e["dir_x"] * 2
               
            elif movement == "8Dir":
                spd = e.get("speed", 4)
                dx = dy = 0
                if self.keys.get("Left"): dx -= spd
                if self.keys.get("Right"): dx += spd
                if self.keys.get("Up"): dy -= spd
                if self.keys.get("Down"): dy += spd
                e["x"] += dx
                e["y"] += dy
               
            # Flash effect
            if e.get("flash_timer", 0) > 0:
                e["flash_timer"] -= 1
       
    def render(self):
        self.canvas.delete("all")
          
        frame_data = self.project["frames"][self.current_frame_idx]
          
        # Sort by layer
        visible_entities = [e for e in self.entities if e.get("alive")]
        visible_entities.sort(key=lambda e: e.get("layer", 0))
          
        for e in visible_entities:
            if not e.get("visible", True):
                continue
            if e.get("flash_timer", 0) > 0 and self.tick % 4 < 2:
                continue
               
            x, y, w, h = e["x"], e["y"], e["w"], e["h"]
            fill = e.get("color", "#888")
            outline = e.get("outline", "#666")
            shape = e.get("shape", "rect")
               
            if e["type"] == "Text":
                self.canvas.create_text(
                    x, y, text=e.get("text_content", "Text"),
                    fill=fill, font=(e.get("text_font", "Arial"), e.get("text_size", 14)),
                    anchor="nw"
                )
            elif e["type"] == "Counter":
                self.canvas.create_rectangle(x, y, x+w, y+h, fill="#222", outline=outline)
                self.canvas.create_text(x+w//2, y+h//2, text=str(e.get("counter_value", 0)),
                                        fill=fill, font=("Consolas", 12, "bold"))
            elif shape == "oval":
                # FIX: Ensure no RGBA or invalid colors
                self.canvas.create_oval(x, y, x+w, y+h, fill=fill, outline=outline, width=2)
            elif shape == "triangle":
                pts = [x+w//2, y, x, y+h, x+w, y+h]
                self.canvas.create_polygon(pts, fill=fill, outline=outline, width=2)
            else:
                self.canvas.create_rectangle(x, y, x+w, y+h, fill=fill, outline=outline, width=2)
               
            # Draw label in editor-style (type icon)
            if e["type"] == "Player":
                self.canvas.create_text(x+w//2, y+h//2, text="P", fill="white",
                                        font=("Arial", 10, "bold"))
            elif e["type"] == "Enemy":
                self.canvas.create_text(x+w//2, y+h//2, text="E", fill="white",
                                        font=("Arial", 10, "bold"))
          
        # HUD - Fixed color code here
        self.canvas.create_rectangle(0, 0, frame_data["width"], 30, fill="#000000", outline="")
        self.canvas.create_text(10, 15, text=f"Score: {self.score}", fill="white",
                               font=("Consolas", 11), anchor="w")
        self.canvas.create_text(200, 15, text=f"Lives: {self.lives}", fill="#ff6666",
                               font=("Consolas", 11), anchor="w")
        self.canvas.create_text(frame_data["width"]-10, 15, 
                               text=f"Frame {self.current_frame_idx+1}/{len(self.project['frames'])}",
                               fill="#aaa", font=("Consolas", 10), anchor="e")
       
    def game_loop(self):
        if not self.running:
            return
          
        if not self.paused:
            frame_data = self.project["frames"][self.current_frame_idx]
               
            # Process events
            self.process_events(frame_data)
               
            # Physics
            self.update_physics()
               
            # Remove dead entities
            self.entities = [e for e in self.entities if e.get("alive", True)]
               
            # Check player-coin collisions for auto scoring
            players = [e for e in self.entities if e.get("type") == "Player" and e.get("alive")]
            coins = [e for e in self.entities if e.get("type") == "Coin" and e.get("alive")]
            for p in players:
                for c in coins:
                    if self.aabb_overlap(p, c):
                        self.score += c.get("score_value", 100)
                        if c.get("destroy_on_collect"):
                            c["alive"] = False
               
            # Check player-enemy collisions
            enemies = [e for e in self.entities if e.get("type") == "Enemy" and e.get("alive")]
            for p in players:
                for en in enemies:
                    if self.aabb_overlap(p, en):
                        # Stomp from above
                        if p.get("dy", 0) > 0 and p["y"] + p["h"] - 10 < en["y"]:
                            en["alive"] = False
                            p["dy"] = -8
                            self.score += 200
                        else:
                            # Hurt player
                            self.lives -= 1
                            p["x"] = 50
                            p["y"] = 50
                            p["dy"] = 0
                            if self.lives <= 0:
                                self.close()
               
            # Render
            self.render()
               
            self.frame_started = False
            self.tick += 1
            self.keys_just_pressed.clear()
            self.keys_just_released.clear()
          
        self.after(self.frame_ms, self.game_loop)


# ══════════════════════════════════════════════════════════════════════════════
#  EXPRESSION BUILDER DIALOG
# ══════════════════════════════════════════════════════════════════════════════

class ExpressionBuilder(tk.Toplevel):
    def __init__(self, master, callback=None):
        super().__init__(master)
        self.title("Expression Builder")
        self.geometry("500x350")
        self.configure(bg=COL_BG)
        self.result = None
        self.callback = callback
          
        tk.Label(self, text="Build Expression", bg=COL_BG, fg=COL_TEXT,
                font=("Arial", 12, "bold")).pack(pady=5)
          
        # Expression entry
        self.expr_var = tk.StringVar()
        entry = tk.Entry(self, textvariable=self.expr_var, font=("Consolas", 12),
                        bg=COL_BG_LIGHT, fg=COL_TEXT, insertbackground=COL_TEXT)
        entry.pack(fill=tk.X, padx=10, pady=5)
          
        # Expression buttons
        btn_frame = tk.Frame(self, bg=COL_BG)
        btn_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
          
        for i, expr in enumerate(EXPRESSIONS):
            btn = tk.Button(btn_frame, text=expr, bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                          command=lambda e=expr: self.insert_expr(e),
                          relief=tk.FLAT, padx=5, pady=2)
            btn.grid(row=i//4, column=i%4, padx=2, pady=2, sticky="ew")
          
        for c in range(4):
            btn_frame.columnconfigure(c, weight=1)
          
        # OK/Cancel
        bottom = tk.Frame(self, bg=COL_BG)
        bottom.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(bottom, text="OK", bg=COL_ACCENT, fg="white",
                 command=self.ok).pack(side=tk.RIGHT, padx=5)
        tk.Button(bottom, text="Cancel", bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 command=self.destroy).pack(side=tk.RIGHT, padx=5)
       
    def insert_expr(self, expr):
        current = self.expr_var.get()
        self.expr_var.set(current + expr)
       
    def ok(self):
        self.result = self.expr_var.get()
        if self.callback:
            self.callback(self.result)
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  ANIMATION EDITOR DIALOG
# ══════════════════════════════════════════════════════════════════════════════

class AnimationEditor(tk.Toplevel):
    def __init__(self, master, obj_data, callback=None):
        super().__init__(master)
        self.title(f"Animation Editor — {obj_data.get('name', 'Object')}")
        self.geometry("600x400")
        self.configure(bg=COL_BG)
        self.obj = obj_data
        self.callback = callback
          
        # Animation list
        left = tk.Frame(self, bg=COL_PANEL, width=180)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
          
        tk.Label(left, text="Animations", bg=COL_PANEL_HEADER, fg=COL_TEXT,
                font=("Arial", 10, "bold")).pack(fill=tk.X)
          
        self.anim_listbox = tk.Listbox(left, bg=COL_BG_LIGHT, fg=COL_TEXT,
                                      selectbackground=COL_ACCENT, borderwidth=0)
        self.anim_listbox.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
          
        anims = obj_data.get("animations", {})
        for name in anims:
            self.anim_listbox.insert(tk.END, name)
          
        btn_row = tk.Frame(left, bg=COL_PANEL)
        btn_row.pack(fill=tk.X, pady=2)
        tk.Button(btn_row, text="+", bg=COL_SUCCESS, fg="white", width=3,
                 command=self.add_anim).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_row, text="-", bg=COL_DANGER, fg="white", width=3,
                 command=self.del_anim).pack(side=tk.LEFT, padx=2)
          
        # Frame editor area
        right = tk.Frame(self, bg=COL_BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
          
        tk.Label(right, text="Frames (indices)", bg=COL_BG, fg=COL_TEXT,
                font=("Arial", 10)).pack(pady=5)
          
        self.frames_var = tk.StringVar()
        self.frames_entry = tk.Entry(right, textvariable=self.frames_var,
                                    font=("Consolas", 12), bg=COL_BG_LIGHT, fg=COL_TEXT,
                                    insertbackground=COL_TEXT)
        self.frames_entry.pack(fill=tk.X, padx=10)
          
        tk.Label(right, text="Speed (ms per frame):", bg=COL_BG, fg=COL_TEXT).pack(pady=5)
        self.speed_var = tk.IntVar(value=obj_data.get("anim_speed", 100))
        tk.Scale(right, from_=16, to=1000, variable=self.speed_var, orient=tk.HORIZONTAL,
                bg=COL_BG, fg=COL_TEXT, highlightthickness=0, troughcolor=COL_BG_LIGHT).pack(fill=tk.X, padx=10)
          
        # Preview area
        tk.Label(right, text="Preview:", bg=COL_BG, fg=COL_TEXT).pack(pady=5)
        self.preview_canvas = tk.Canvas(right, bg=COL_CANVAS_BG, width=200, height=100, highlightthickness=0)
        self.preview_canvas.pack(padx=10)
          
        self.anim_listbox.bind("<<ListboxSelect>>", self.on_select_anim)
          
        # Bottom buttons
        bottom = tk.Frame(self, bg=COL_BG)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        tk.Button(bottom, text="Save", bg=COL_ACCENT, fg="white",
                 command=self.save).pack(side=tk.RIGHT, padx=5)
        tk.Button(bottom, text="Close", bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 command=self.destroy).pack(side=tk.RIGHT, padx=5)
       
    def on_select_anim(self, event=None):
        sel = self.anim_listbox.curselection()
        if not sel:
            return
        name = self.anim_listbox.get(sel[0])
        frames = self.obj.get("animations", {}).get(name, [])
        self.frames_var.set(", ".join(str(f) for f in frames))
       
    def add_anim(self):
        name = simpledialog.askstring("New Animation", "Animation name:", parent=self)
        if name:
            if "animations" not in self.obj:
                self.obj["animations"] = {}
            self.obj["animations"][name] = [0]
            self.anim_listbox.insert(tk.END, name)
       
    def del_anim(self):
        sel = self.anim_listbox.curselection()
        if not sel:
            return
        name = self.anim_listbox.get(sel[0])
        if name in self.obj.get("animations", {}):
            del self.obj["animations"][name]
        self.anim_listbox.delete(sel[0])
       
    def save(self):
        sel = self.anim_listbox.curselection()
        if sel:
            name = self.anim_listbox.get(sel[0])
            try:
                frames = [int(x.strip()) for x in self.frames_var.get().split(",") if x.strip()]
                self.obj["animations"][name] = frames
            except ValueError:
                pass
        self.obj["anim_speed"] = self.speed_var.get()
        if self.callback:
            self.callback(self.obj)


# ══════════════════════════════════════════════════════════════════════════════
#  EVENT EDITOR PANEL
# ══════════════════════════════════════════════════════════════════════════════

class EventEditorPanel(tk.Frame):
    """The spreadsheet-style event editor, the core of Clickteam-style programming."""
       
    def __init__(self, master, project, frame_idx=0, on_change=None):
        super().__init__(master, bg=COL_BG)
        self.project = project
        self.frame_idx = frame_idx
        self.on_change = on_change
          
        self.setup_ui()
        self.refresh()
       
    def get_frame(self):
        return self.project["frames"][self.frame_idx]
       
    def setup_ui(self):
        # Toolbar
        toolbar = tk.Frame(self, bg=COL_TOOLBAR, height=36)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
          
        tk.Label(toolbar, text="⚡ Event Editor", bg=COL_TOOLBAR, fg=COL_ACCENT,
                font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=10)
          
        tk.Button(toolbar, text="+ New Event", bg=COL_SUCCESS, fg="white",
                 relief=tk.FLAT, command=self.add_event_group).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="+ Comment", bg=COL_WARNING, fg="black",
                 relief=tk.FLAT, command=self.add_comment).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Delete Selected", bg=COL_DANGER, fg="white",
                 relief=tk.FLAT, command=self.delete_selected).pack(side=tk.LEFT, padx=5)
          
        # Event list area with scrollbar
        container = tk.Frame(self, bg=COL_BG)
        container.pack(fill=tk.BOTH, expand=True)
          
        self.v_scroll = tk.Scrollbar(container)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
          
        self.event_canvas = tk.Canvas(container, bg=COL_BG, highlightthickness=0,
                                    yscrollcommand=self.v_scroll.set)
        self.event_canvas.pack(fill=tk.BOTH, expand=True)
        self.v_scroll.config(command=self.event_canvas.yview)
          
        self.inner_frame = tk.Frame(self.event_canvas, bg=COL_BG)
        self.event_canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", lambda e: self.event_canvas.configure(
            scrollregion=self.event_canvas.bbox("all")))
          
        self.selected_group_idx = None
       
    def refresh(self):
        """Rebuild the event list display."""
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
          
        frame = self.get_frame()
        events = frame.get("events", [])
          
        if not events:
            tk.Label(self.inner_frame, text="No events yet. Click '+ New Event' to start programming!",
                    bg=COL_BG, fg=COL_TEXT_DIM, font=("Arial", 10)).pack(pady=20)
            return
          
        # Header row
        header = tk.Frame(self.inner_frame, bg=COL_PANEL_HEADER)
        header.pack(fill=tk.X, padx=2, pady=(0, 2))
        tk.Label(header, text="#", bg=COL_PANEL_HEADER, fg=COL_TEXT, width=4,
                font=("Consolas", 9)).pack(side=tk.LEFT)
        tk.Label(header, text="Conditions", bg=COL_PANEL_HEADER, fg=COL_TEXT, width=40,
                font=("Arial", 9, "bold"), anchor="w").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="→", bg=COL_PANEL_HEADER, fg=COL_ACCENT, width=3,
                font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text="Actions", bg=COL_PANEL_HEADER, fg=COL_TEXT, width=40,
                font=("Arial", 9, "bold"), anchor="w").pack(side=tk.LEFT, padx=5)
          
        for i, group in enumerate(events):
            row_bg = COL_PANEL if i % 2 == 0 else COL_BG_LIGHT
               
            if self.selected_group_idx == i:
                row_bg = "#2a4a6a"
               
            row = tk.Frame(self.inner_frame, bg=row_bg, relief=tk.FLAT, bd=1)
            row.pack(fill=tk.X, padx=2, pady=1)
            row.bind("<Button-1>", lambda e, idx=i: self.select_group(idx))
               
            # Comment row
            if group.get("comment"):
                tk.Label(row, text=f"  💬 {group['comment']}", bg="#4a4a2a", fg="#dddd88",
                        font=("Arial", 9, "italic"), anchor="w").pack(fill=tk.X)
                continue
               
            # Event number
            active = group.get("active", True)
            num_color = COL_TEXT if active else COL_TEXT_DIM
            chk_text = f" {i+1:2d}" if active else f"×{i+1:2d}"
               
            num_label = tk.Label(row, text=chk_text, bg=row_bg, fg=num_color, width=4,
                                font=("Consolas", 9))
            num_label.pack(side=tk.LEFT)
            num_label.bind("<Button-1>", lambda e, idx=i: self.toggle_active(idx))
               
            # Conditions
            conds = group.get("conditions", [])
            cond_text = " + ".join(
                ("NOT " if c.get("negated") else "") + c.get("type", "?") +
                (f" [{c.get('target', '')}]" if c.get("target") else "")
                for c in conds
            ) or "(no conditions)"
               
            cond_label = tk.Label(row, text=cond_text, bg=row_bg, fg="#7fbaff" if conds else COL_TEXT_DIM,
                                 width=40, anchor="w", font=("Arial", 9))
            cond_label.pack(side=tk.LEFT, padx=5)
            cond_label.bind("<Double-Button-1>", lambda e, idx=i: self.edit_conditions(idx))
               
            # Arrow
            tk.Label(row, text="→", bg=row_bg, fg=COL_ACCENT, width=3,
                    font=("Arial", 10, "bold")).pack(side=tk.LEFT)
               
            # Actions
            acts = group.get("actions", [])
            act_text = " ; ".join(
                a.get("type", "?") + (f" [{a.get('target', '')}]" if a.get("target") else "")
                for a in acts
            ) or "(no actions)"
               
            act_label = tk.Label(row, text=act_text, bg=row_bg, fg="#7fff7f" if acts else COL_TEXT_DIM,
                                width=40, anchor="w", font=("Arial", 9))
            act_label.pack(side=tk.LEFT, padx=5)
            act_label.bind("<Double-Button-1>", lambda e, idx=i: self.edit_actions(idx))
       
    def select_group(self, idx):
        self.selected_group_idx = idx
        self.refresh()
       
    def toggle_active(self, idx):
        frame = self.get_frame()
        events = frame.get("events", [])
        if 0 <= idx < len(events):
            events[idx]["active"] = not events[idx].get("active", True)
            self.refresh()
       
    def add_event_group(self):
        frame = self.get_frame()
        if "events" not in frame:
            frame["events"] = []
          
        new_group = make_event_group()
        # Open condition picker
        self.pick_condition_action(new_group, frame)
       
    def add_comment(self):
        text = simpledialog.askstring("Comment", "Enter comment:", parent=self)
        if text:
            frame = self.get_frame()
            if "events" not in frame:
                frame["events"] = []
            frame["events"].append({
                "id": uid(),
                "active": True,
                "comment": text,
                "conditions": [],
                "actions": [],
            })
            self.refresh()
       
    def pick_condition_action(self, group, frame):
        """Dialog to add conditions and actions to an event group."""
        dlg = tk.Toplevel(self)
        dlg.title("Edit Event")
        dlg.geometry("700x500")
        dlg.configure(bg=COL_BG)
          
        paned = tk.PanedWindow(dlg, orient=tk.HORIZONTAL, bg=COL_BG, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
          
        # Conditions side
        cond_frame = tk.Frame(paned, bg=COL_PANEL)
        paned.add(cond_frame)
          
        tk.Label(cond_frame, text="Conditions", bg=COL_PANEL_HEADER, fg=COL_TEXT,
                font=("Arial", 10, "bold")).pack(fill=tk.X)
          
        cond_listbox = tk.Listbox(cond_frame, bg=COL_BG_LIGHT, fg=COL_TEXT,
                                 selectbackground=COL_ACCENT, borderwidth=0, font=("Arial", 9))
        cond_listbox.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
          
        for c in CONDITIONS:
            cond_listbox.insert(tk.END, c)
          
        # Target entry for condition
        cond_target_frame = tk.Frame(cond_frame, bg=COL_PANEL)
        cond_target_frame.pack(fill=tk.X, padx=2)
        tk.Label(cond_target_frame, text="Target:", bg=COL_PANEL, fg=COL_TEXT,
                font=("Arial", 9)).pack(side=tk.LEFT)
        cond_target_var = tk.StringVar()
        tk.Entry(cond_target_frame, textvariable=cond_target_var, bg=COL_BG_LIGHT, fg=COL_TEXT,
                insertbackground=COL_TEXT, font=("Arial", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)
          
        cond_negate_var = tk.BooleanVar()
        tk.Checkbutton(cond_frame, text="Negate (NOT)", variable=cond_negate_var,
                      bg=COL_PANEL, fg=COL_TEXT, selectcolor=COL_BG_LIGHT,
                      activebackground=COL_PANEL).pack(anchor="w", padx=5)
          
        def add_condition():
            sel = cond_listbox.curselection()
            if sel:
                ctype = cond_listbox.get(sel[0])
                cond = make_condition(ctype)
                cond["target"] = cond_target_var.get()
                cond["negated"] = cond_negate_var.get()
                group["conditions"].append(cond)
                refresh_selected()
          
        tk.Button(cond_frame, text="+ Add Condition", bg=COL_ACCENT, fg="white",
                 command=add_condition).pack(fill=tk.X, padx=2, pady=2)
          
        # Actions side
        act_frame = tk.Frame(paned, bg=COL_PANEL)
        paned.add(act_frame)
          
        tk.Label(act_frame, text="Actions", bg=COL_PANEL_HEADER, fg=COL_TEXT,
                font=("Arial", 10, "bold")).pack(fill=tk.X)
          
        act_listbox = tk.Listbox(act_frame, bg=COL_BG_LIGHT, fg=COL_TEXT,
                                selectbackground=COL_ACCENT, borderwidth=0, font=("Arial", 9))
        act_listbox.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
          
        for a in ACTIONS:
            act_listbox.insert(tk.END, a)
          
        act_target_frame = tk.Frame(act_frame, bg=COL_PANEL)
        act_target_frame.pack(fill=tk.X, padx=2)
        tk.Label(act_target_frame, text="Target:", bg=COL_PANEL, fg=COL_TEXT,
                font=("Arial", 9)).pack(side=tk.LEFT)
        act_target_var = tk.StringVar()
        tk.Entry(act_target_frame, textvariable=act_target_var, bg=COL_BG_LIGHT, fg=COL_TEXT,
                insertbackground=COL_TEXT, font=("Arial", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)
          
        def add_action():
            sel = act_listbox.curselection()
            if sel:
                atype = act_listbox.get(sel[0])
                act = make_action(atype)
                act["target"] = act_target_var.get()
                group["actions"].append(act)
                refresh_selected()
          
        tk.Button(act_frame, text="+ Add Action", bg=COL_SUCCESS, fg="white",
                 command=add_action).pack(fill=tk.X, padx=2, pady=2)
          
        # Current selections display
        sel_frame = tk.Frame(dlg, bg=COL_BG, height=100)
        sel_frame.pack(fill=tk.X, padx=5, pady=5)
          
        sel_label = tk.Label(sel_frame, text="", bg=COL_BG, fg=COL_TEXT,
                            font=("Consolas", 9), anchor="w", justify=tk.LEFT)
        sel_label.pack(fill=tk.X)
          
        def refresh_selected():
            conds = ", ".join(c["type"] for c in group["conditions"]) or "(none)"
            acts = ", ".join(a["type"] for a in group["actions"]) or "(none)"
            sel_label.config(text=f"Conditions: {conds}\nActions: {acts}")
          
        refresh_selected()
          
        # Bottom buttons
        bottom = tk.Frame(dlg, bg=COL_BG)
        bottom.pack(fill=tk.X, padx=5, pady=5)
          
        def confirm():
            if "events" not in frame:
                frame["events"] = []
            frame["events"].append(group)
            self.refresh()
            dlg.destroy()
          
        tk.Button(bottom, text="✓ Add Event", bg=COL_ACCENT, fg="white",
                 command=confirm).pack(side=tk.RIGHT, padx=5)
        tk.Button(bottom, text="Cancel", bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 command=dlg.destroy).pack(side=tk.RIGHT, padx=5)
       
    def edit_conditions(self, idx):
        frame = self.get_frame()
        events = frame.get("events", [])
        if 0 <= idx < len(events):
            group = events[idx]
            # Simple: reopen the full editor
            self.pick_condition_action_edit(group)
       
    def edit_actions(self, idx):
        self.edit_conditions(idx)
       
    def pick_condition_action_edit(self, group):
        """Edit existing event group."""
        dlg = tk.Toplevel(self)
        dlg.title("Edit Event Group")
        dlg.geometry("600x400")
        dlg.configure(bg=COL_BG)
          
        # Show current conditions
        tk.Label(dlg, text="Current Conditions:", bg=COL_BG, fg=COL_ACCENT,
                font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=5)
          
        for i, c in enumerate(group.get("conditions", [])):
            row = tk.Frame(dlg, bg=COL_PANEL)
            row.pack(fill=tk.X, padx=10, pady=1)
            neg = "NOT " if c.get("negated") else ""
            tgt = f" [{c.get('target')}]" if c.get("target") else ""
            tk.Label(row, text=f"  {neg}{c['type']}{tgt}", bg=COL_PANEL, fg="#7fbaff",
                    font=("Arial", 9), anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Button(row, text="×", bg=COL_DANGER, fg="white", width=3,
                     command=lambda idx=i: self.remove_from_group(group, "conditions", idx, dlg)).pack(side=tk.RIGHT)
          
        tk.Label(dlg, text="Current Actions:", bg=COL_BG, fg=COL_SUCCESS,
                font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
          
        for i, a in enumerate(group.get("actions", [])):
            row = tk.Frame(dlg, bg=COL_PANEL)
            row.pack(fill=tk.X, padx=10, pady=1)
            tgt = f" [{a.get('target')}]" if a.get("target") else ""
            tk.Label(row, text=f"  {a['type']}{tgt}", bg=COL_PANEL, fg="#7fff7f",
                    font=("Arial", 9), anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Button(row, text="×", bg=COL_DANGER, fg="white", width=3,
                     command=lambda idx=i: self.remove_from_group(group, "actions", idx, dlg)).pack(side=tk.RIGHT)
          
        tk.Button(dlg, text="Close", bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 command=lambda: (dlg.destroy(), self.refresh())).pack(pady=10)
       
    def remove_from_group(self, group, key, idx, dlg):
        if 0 <= idx < len(group.get(key, [])):
            group[key].pop(idx)
        dlg.destroy()
        self.pick_condition_action_edit(group)
       
    def delete_selected(self):
        if self.selected_group_idx is not None:
            frame = self.get_frame()
            events = frame.get("events", [])
            if 0 <= self.selected_group_idx < len(events):
                events.pop(self.selected_group_idx)
                self.selected_group_idx = None
                self.refresh()


# ══════════════════════════════════════════════════════════════════════════════
#  LAYER MANAGER
# ══════════════════════════════════════════════════════════════════════════════

class LayerManager(tk.Frame):
    def __init__(self, master, frame_data, on_change=None):
        super().__init__(master, bg=COL_PANEL)
        self.frame_data = frame_data
        self.on_change = on_change
        self.selected_layer = 0
          
        tk.Label(self, text="Layers", bg=COL_PANEL_HEADER, fg=COL_BLUE_TEXT,
                font=("Arial", 9, "bold")).pack(fill=tk.X)
          
        self.list_frame = tk.Frame(self, bg=COL_PANEL)
        self.list_frame.pack(fill=tk.BOTH, expand=True)
          
        btn_row = tk.Frame(self, bg=COL_PANEL)
        btn_row.pack(fill=tk.X)
        tk.Button(btn_row, text="+", width=3, bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 command=self.add_layer, relief=tk.FLAT).pack(side=tk.LEFT, padx=1)
        tk.Button(btn_row, text="-", width=3, bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 command=self.del_layer, relief=tk.FLAT).pack(side=tk.LEFT, padx=1)
        tk.Button(btn_row, text="↑", width=3, bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 command=self.move_up, relief=tk.FLAT).pack(side=tk.LEFT, padx=1)
        tk.Button(btn_row, text="↓", width=3, bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 command=self.move_down, relief=tk.FLAT).pack(side=tk.LEFT, padx=1)
          
        self.refresh()
       
    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
          
        layers = self.frame_data.get("layers", [])
        for i, layer in enumerate(layers):
            bg = "#2a4a6a" if i == self.selected_layer else COL_BG_LIGHT
            row = tk.Frame(self.list_frame, bg=bg)
            row.pack(fill=tk.X, pady=1)
            row.bind("<Button-1>", lambda e, idx=i: self.select(idx))
               
            vis_text = ":3" if layer.get("visible", True) else "  "
            vis_btn = tk.Label(row, text=vis_text, bg=bg, fg=COL_TEXT, width=3, cursor="hand2")
            vis_btn.pack(side=tk.LEFT)
            vis_btn.bind("<Button-1>", lambda e, idx=i: self.toggle_visible(idx))
               
            lock_text = "🔒" if layer.get("locked", False) else "  "
            lock_btn = tk.Label(row, text=lock_text, bg=bg, fg=COL_TEXT, width=3, cursor="hand2")
            lock_btn.pack(side=tk.LEFT)
            lock_btn.bind("<Button-1>", lambda e, idx=i: self.toggle_locked(idx))
               
            name_label = tk.Label(row, text=layer.get("name", f"Layer {i+1}"), bg=bg, fg=COL_TEXT,
                                 font=("Arial", 9), anchor="w")
            name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            name_label.bind("<Button-1>", lambda e, idx=i: self.select(idx))
            name_label.bind("<Double-Button-1>", lambda e, idx=i: self.rename(idx))
       
    def select(self, idx):
        self.selected_layer = idx
        self.refresh()
        if self.on_change:
            self.on_change()
       
    def toggle_visible(self, idx):
        layers = self.frame_data.get("layers", [])
        if 0 <= idx < len(layers):
            layers[idx]["visible"] = not layers[idx].get("visible", True)
            self.refresh()
            if self.on_change:
                self.on_change()
       
    def toggle_locked(self, idx):
        layers = self.frame_data.get("layers", [])
        if 0 <= idx < len(layers):
            layers[idx]["locked"] = not layers[idx].get("locked", False)
            self.refresh()
       
    def rename(self, idx):
        layers = self.frame_data.get("layers", [])
        if 0 <= idx < len(layers):
            name = simpledialog.askstring("Rename Layer", "New name:", 
                                        initialvalue=layers[idx].get("name", ""),
                                        parent=self)
            if name:
                layers[idx]["name"] = name
                self.refresh()
       
    def add_layer(self):
        layers = self.frame_data.get("layers", [])
        layers.append({"name": f"Layer {len(layers)+1}", "visible": True, "locked": False, "opacity": 255})
        self.refresh()
       
    def del_layer(self):
        layers = self.frame_data.get("layers", [])
        if len(layers) > 1 and 0 <= self.selected_layer < len(layers):
            layers.pop(self.selected_layer)
            self.selected_layer = max(0, self.selected_layer - 1)
            self.refresh()
       
    def move_up(self):
        layers = self.frame_data.get("layers", [])
        if self.selected_layer > 0:
            layers[self.selected_layer], layers[self.selected_layer-1] = \
                layers[self.selected_layer-1], layers[self.selected_layer]
            self.selected_layer -= 1
            self.refresh()
       
    def move_down(self):
        layers = self.frame_data.get("layers", [])
        if self.selected_layer < len(layers) - 1:
            layers[self.selected_layer], layers[self.selected_layer+1] = \
                layers[self.selected_layer+1], layers[self.selected_layer]
            self.selected_layer += 1
            self.refresh()


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION — AC ENGINE IDE
# ══════════════════════════════════════════════════════════════════════════════

class ACEngine:
    """The main IDE window with all editors integrated."""
       
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.configure(bg=COL_BG)
          
        # Project data
        self.project = make_default_project()
        self.project_path = None
        self.modified = False
          
        # Editor state
        self.current_frame_idx = 0
        self.current_tool = "Select"
        self.selected_object = None
        self.selected_object_idx = None
        self.drag_data = {"x": 0, "y": 0, "active": False}
        self.clipboard = None
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.show_grid = True
        self.snap_to_grid = True
        self.current_editor = "frame"  # frame, event, storyboard
          
        # Undo
        self.undo_mgr = UndoManager()
          
        # Build UI - ORDER MATTERS HERE
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()  # Must be before setup_main_layout because set_status depends on it
        self.setup_main_layout()
          
        # Keyboard shortcuts
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-s>", lambda e: self.save_project())
        self.root.bind("<Control-o>", lambda e: self.load_project())
        self.root.bind("<Control-n>", lambda e: self.new_project())
        self.root.bind("<Control-c>", lambda e: self.copy_object())
        self.root.bind("<Control-v>", lambda e: self.paste_object())
        self.root.bind("<Delete>", lambda e: self.delete_selected_object())
        self.root.bind("<F5>", lambda e: self.run_game())
          
        # Initial refresh
        self.refresh_all()
        self.update_title()
       
    # ──────────────────────────────────────────────────────────────────────
    #  UNDO / REDO IMPLEMENTATION
    # ──────────────────────────────────────────────────────────────────────

    def get_current_frame(self):
        if 0 <= self.current_frame_idx < len(self.project["frames"]):
            return self.project["frames"][self.current_frame_idx]
        return None

    def save_undo(self):
        # Create a snapshot of the current frame state
        frame = self.get_current_frame()
        if frame:
            snapshot = {
                "frame_idx": self.current_frame_idx,
                "frame_data": copy.deepcopy(frame)
            }
            self.undo_mgr.push(snapshot)

    def undo(self):
        current_frame = self.get_current_frame()
        if not current_frame:
            return
            
        snapshot = {
            "frame_idx": self.current_frame_idx,
            "frame_data": copy.deepcopy(current_frame)
        }
        
        prev_state = self.undo_mgr.undo(snapshot)
        if prev_state:
            # Restore state
            if prev_state["frame_idx"] == self.current_frame_idx:
                self.project["frames"][self.current_frame_idx] = prev_state["frame_data"]
                self.selected_object = None # clear selection to avoid errors
                self.refresh_all()
                self.set_status("Undid last action")

    def redo(self):
        current_frame = self.get_current_frame()
        if not current_frame:
            return

        snapshot = {
            "frame_idx": self.current_frame_idx,
            "frame_data": copy.deepcopy(current_frame)
        }
        
        next_state = self.undo_mgr.redo(snapshot)
        if next_state:
             if next_state["frame_idx"] == self.current_frame_idx:
                self.project["frames"][self.current_frame_idx] = next_state["frame_data"]
                self.selected_object = None
                self.refresh_all()
                self.set_status("Redid action")

    # ──────────────────────────────────────────────────────────────────────
    #  MENU BAR
    # ──────────────────────────────────────────────────────────────────────
       
    def setup_menu(self):
        menubar = tk.Menu(self.root, bg=COL_TOOLBAR, fg=COL_TEXT, activebackground=COL_ACCENT)
          
        # File
        file_menu = tk.Menu(menubar, tearoff=0, bg=COL_BG_LIGHT, fg=COL_TEXT)
        file_menu.add_command(label="New Project                    Ctrl+N", command=self.new_project)
        file_menu.add_command(label="Open Project                   Ctrl+O", command=self.load_project)
        file_menu.add_command(label="Save Project                   Ctrl+S", command=self.save_project)
        file_menu.add_command(label="Save As...", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Project Properties...", command=self.project_properties)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)
          
        # Edit
        edit_menu = tk.Menu(menubar, tearoff=0, bg=COL_BG_LIGHT, fg=COL_TEXT)
        edit_menu.add_command(label="Undo                        Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="Redo                        Ctrl+Y", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Copy                        Ctrl+C", command=self.copy_object)
        edit_menu.add_command(label="Paste                       Ctrl+V", command=self.paste_object)
        edit_menu.add_command(label="Delete                      Delete", command=self.delete_selected_object)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All Objects", command=self.select_all)
        menubar.add_cascade(label="Edit", menu=edit_menu)
          
        # View
        view_menu = tk.Menu(menubar, tearoff=0, bg=COL_BG_LIGHT, fg=COL_TEXT)
        view_menu.add_command(label="Frame Editor                F1", command=lambda: self.switch_editor("frame"))
        view_menu.add_command(label="Event Editor                F2", command=lambda: self.switch_editor("event"))
        view_menu.add_command(label="Storyboard                  F3", command=lambda: self.switch_editor("storyboard"))
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Grid", command=self.toggle_grid)
        view_menu.add_command(label="Toggle Snap", command=self.toggle_snap)
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In                     +", command=lambda: self.set_zoom(self.zoom * 1.25))
        view_menu.add_command(label="Zoom Out                    -", command=lambda: self.set_zoom(self.zoom / 1.25))
        view_menu.add_command(label="Zoom 100%                   0", command=lambda: self.set_zoom(1.0))
        menubar.add_cascade(label="View", menu=view_menu)
          
        # Insert
        insert_menu = tk.Menu(menubar, tearoff=0, bg=COL_BG_LIGHT, fg=COL_TEXT)
        for otype in ["Active", "Backdrop", "Platform", "Player", "Enemy", "Coin",
                      "Counter", "Text", "Lives", "Timer", "Trigger", "Particle"]:
            insert_menu.add_command(label=f"New {otype} Object",
                                  command=lambda t=otype: self.insert_object(t))
        menubar.add_cascade(label="Insert", menu=insert_menu)
          
        # Frame
        frame_menu = tk.Menu(menubar, tearoff=0, bg=COL_BG_LIGHT, fg=COL_TEXT)
        frame_menu.add_command(label="New Frame", command=self.add_frame)
        frame_menu.add_command(label="Duplicate Frame", command=self.duplicate_frame)
        frame_menu.add_command(label="Delete Frame", command=self.delete_frame)
        frame_menu.add_command(label="Rename Frame", command=self.rename_frame)
        frame_menu.add_separator()
        frame_menu.add_command(label="Frame Properties...", command=self.frame_properties)
        menubar.add_cascade(label="Frame", menu=frame_menu)
          
        # Run
        run_menu = tk.Menu(menubar, tearoff=0, bg=COL_BG_LIGHT, fg=COL_TEXT)
        run_menu.add_command(label="Run Application         F5", command=self.run_game)
        run_menu.add_command(label="Run Current Frame       F6", command=self.run_current_frame)
        run_menu.add_separator()
        run_menu.add_command(label="Build Settings...", command=self.build_settings)
        menubar.add_cascade(label="Run", menu=run_menu)
          
        # Help
        help_menu = tk.Menu(menubar, tearoff=0, bg=COL_BG_LIGHT, fg=COL_TEXT)
        help_menu.add_command(label="About AC Engine", command=self.show_about)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        menubar.add_cascade(label="Help", menu=help_menu)
          
        self.root.config(menu=menubar)
          
        # F-key bindings
        self.root.bind("<F1>", lambda e: self.switch_editor("frame"))
        self.root.bind("<F2>", lambda e: self.switch_editor("event"))
        self.root.bind("<F3>", lambda e: self.switch_editor("storyboard"))
        self.root.bind("<F6>", lambda e: self.run_current_frame())
       
    # ──────────────────────────────────────────────────────────────────────
    #  TOOLBAR
    # ──────────────────────────────────────────────────────────────────────
       
    def setup_toolbar(self):
        self.toolbar = tk.Frame(self.root, bg=COL_TOOLBAR, height=40)
        self.toolbar.pack(fill=tk.X)
        self.toolbar.pack_propagate(False)
          
        # Editor tabs
        tab_frame = tk.Frame(self.toolbar, bg=COL_TOOLBAR)
        tab_frame.pack(side=tk.LEFT, padx=5)
          
        self.tab_buttons = {}
        for name, label in [("storyboard", "📋 Storyboard"), ("frame", "🎨 Frame Editor"), ("event", "⚡ Event Editor")]:
            btn = tk.Button(tab_frame, text=label, bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                          relief=tk.FLAT, padx=10, pady=2,
                          command=lambda n=name: self.switch_editor(n))
            btn.pack(side=tk.LEFT, padx=1)
            self.tab_buttons[name] = btn
          
        # Separator
        tk.Label(self.toolbar, text="│", bg=COL_TOOLBAR, fg=COL_BTN_TEXT).pack(side=tk.LEFT, padx=5)
          
        # Tool selector (frame editor tools)
        self.tool_frame = tk.Frame(self.toolbar, bg=COL_TOOLBAR)
        self.tool_frame.pack(side=tk.LEFT, padx=5)
          
        self.tool_var = tk.StringVar(value="Select")
        tools = [
            ("👆 Select", "Select"),
            ("🟥 Player", "Player"),
            ("🟩 Platform", "Platform"),
            ("🟤 Enemy", "Enemy"),
            ("🟡 Coin", "Coin"),
            ("⬛ Active", "Active"),
            ("🟦 Backdrop", "Backdrop"),
            ("🔢 Counter", "Counter"),
            ("📝 Text", "Text"),
        ]
          
        for text, mode in tools:
            rb = tk.Radiobutton(self.tool_frame, text=text, variable=self.tool_var, value=mode,
                               indicatoron=0, command=self.set_tool,
                               bg=COL_BTN_FACE, fg=COL_BTN_TEXT, selectcolor=COL_ACCENT,
                               relief=tk.FLAT, padx=6, pady=2,
                               font=("Arial", 9))
            rb.pack(side=tk.LEFT, padx=1)
          
        # Right side: Run button
        tk.Button(self.toolbar, text="▶ RUN (F5)", bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 font=("Arial", 10, "bold"), relief=tk.FLAT, padx=15,
                 command=self.run_game).pack(side=tk.RIGHT, padx=10)
          
        # Zoom controls
        zoom_frame = tk.Frame(self.toolbar, bg=COL_TOOLBAR)
        zoom_frame.pack(side=tk.RIGHT, padx=5)
        tk.Button(zoom_frame, text="-", bg=COL_BTN_FACE, fg=COL_BTN_TEXT, width=3,
                 relief=tk.FLAT, command=lambda: self.set_zoom(self.zoom / 1.25)).pack(side=tk.LEFT)
        self.zoom_label = tk.Label(zoom_frame, text="100%", bg=COL_TOOLBAR, fg=COL_BTN_TEXT,
                                  font=("Consolas", 9), width=6)
        self.zoom_label.pack(side=tk.LEFT)
        tk.Button(zoom_frame, text="+", bg=COL_BTN_FACE, fg=COL_BTN_TEXT, width=3,
                 relief=tk.FLAT, command=lambda: self.set_zoom(self.zoom * 1.25)).pack(side=tk.LEFT)
       
    # ──────────────────────────────────────────────────────────────────────
    #  MAIN LAYOUT
    # ──────────────────────────────────────────────────────────────────────
       
    def setup_main_layout(self):
        self.main_container = tk.Frame(self.root, bg=COL_BG)
        self.main_container.pack(fill=tk.BOTH, expand=True)
          
        # Create all editor panels (only one visible at a time)
        self.editors = {}
          
        # Frame Editor
        self.setup_frame_editor()
          
        # Event Editor
        self.setup_event_editor()
          
        # Storyboard
        self.setup_storyboard()
          
        # Default to frame editor
        self.switch_editor("frame")
       
    def setup_frame_editor(self):
        """Build the frame/level editor with canvas, object tree, and properties."""
        frame_editor = tk.Frame(self.main_container, bg=COL_BG)
        self.editors["frame"] = frame_editor
          
        # 3-panel layout
        paned = tk.PanedWindow(frame_editor, orient=tk.HORIZONTAL, bg=COL_BG,
                              sashwidth=3, sashrelief=tk.FLAT)
        paned.pack(fill=tk.BOTH, expand=True)
          
        # LEFT PANEL: Object tree + Layer manager
        left_panel = tk.Frame(paned, bg=COL_PANEL, width=220)
        paned.add(left_panel, minsize=180)
          
        # Object tree
        tree_label = tk.Label(left_panel, text="🗂 Objects", bg=COL_PANEL_HEADER, fg=COL_BLUE_TEXT,
                             font=("Arial", 10, "bold"), anchor="w", padx=10)
        tree_label.pack(fill=tk.X)
          
        tree_frame = tk.Frame(left_panel, bg=COL_PANEL)
        tree_frame.pack(fill=tk.BOTH, expand=True)
          
        tree_scroll = tk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
          
        self.object_tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set,
                                      show="tree", style="Dark.Treeview")
        self.object_tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.object_tree.yview)
        self.object_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
          
        # Style the treeview
        style = ttk.Style()
        style.configure("Dark.Treeview", background=COL_BG_LIGHT, foreground=COL_TEXT,
                        fieldbackground=COL_BG_LIGHT, borderwidth=0)
        style.map("Dark.Treeview", background=[("selected", COL_ACCENT)])
          
        # Layer manager
        self.layer_mgr_container = tk.Frame(left_panel, bg=COL_PANEL, height=200)
        self.layer_mgr_container.pack(fill=tk.X, side=tk.BOTTOM)
        self.layer_mgr_container.pack_propagate(False)
        self.layer_manager = None  # Created in refresh
          
        # CENTER: Canvas
        center = tk.Frame(paned, bg=COL_CANVAS_BG)
        paned.add(center, minsize=400)
          
        h_scroll = tk.Scrollbar(center, orient=tk.HORIZONTAL)
        v_scroll = tk.Scrollbar(center, orient=tk.VERTICAL)
          
        self.editor_canvas = tk.Canvas(center, bg=COL_CANVAS_BG,
                                     scrollregion=(0, 0, 2000, 2000),
                                     xscrollcommand=h_scroll.set,
                                     yscrollcommand=v_scroll.set,
                                     highlightthickness=0)
          
        h_scroll.config(command=self.editor_canvas.xview)
        v_scroll.config(command=self.editor_canvas.yview)
          
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.editor_canvas.pack(fill=tk.BOTH, expand=True)
          
        # Canvas bindings
        self.editor_canvas.bind("<Button-1>", self.on_canvas_click)
        self.editor_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.editor_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.editor_canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.editor_canvas.bind("<MouseWheel>", self.on_canvas_scroll)
          
        # RIGHT PANEL: Properties
        right_panel = tk.Frame(paned, bg=COL_PANEL, width=260)
        paned.add(right_panel, minsize=200)
          
        tk.Label(right_panel, text="📋 Properties", bg=COL_PANEL_HEADER, fg=COL_BLUE_TEXT,
                font=("Arial", 10, "bold"), anchor="w", padx=10).pack(fill=tk.X)
          
        prop_scroll_frame = tk.Frame(right_panel, bg=COL_PANEL)
        prop_scroll_frame.pack(fill=tk.BOTH, expand=True)
          
        prop_canvas = tk.Canvas(prop_scroll_frame, bg=COL_PANEL, highlightthickness=0)
        prop_scrollbar = tk.Scrollbar(prop_scroll_frame, command=prop_canvas.yview)
          
        self.prop_container = tk.Frame(prop_canvas, bg=COL_PANEL)
        self.prop_container.bind("<Configure>", lambda e: prop_canvas.configure(
            scrollregion=prop_canvas.bbox("all")))
          
        prop_canvas.create_window((0, 0), window=self.prop_container, anchor="nw")
        prop_canvas.configure(yscrollcommand=prop_scrollbar.set)
          
        prop_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        prop_canvas.pack(fill=tk.BOTH, expand=True)
       
    def setup_event_editor(self):
        """Build the event editor tab."""
        event_editor = tk.Frame(self.main_container, bg=COL_BG)
        self.editors["event"] = event_editor
        self.event_panel = None  # Created on switch
       
    def setup_storyboard(self):
        """Build the storyboard tab (frame overview/management)."""
        storyboard = tk.Frame(self.main_container, bg=COL_BG)
        self.editors["storyboard"] = storyboard
          
        # Toolbar
        sb_toolbar = tk.Frame(storyboard, bg=COL_TOOLBAR, height=36)
        sb_toolbar.pack(fill=tk.X)
        sb_toolbar.pack_propagate(False)
          
        tk.Label(sb_toolbar, text="📋 Storyboard", bg=COL_TOOLBAR, fg=COL_ACCENT,
                font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=10)
        tk.Button(sb_toolbar, text="+ New Frame", bg=COL_SUCCESS, fg="white",
                 relief=tk.FLAT, command=self.add_frame).pack(side=tk.LEFT, padx=5)
        tk.Button(sb_toolbar, text="Duplicate", bg=COL_ACCENT, fg="white",
                 relief=tk.FLAT, command=self.duplicate_frame).pack(side=tk.LEFT, padx=5)
        tk.Button(sb_toolbar, text="Delete", bg=COL_DANGER, fg="white",
                 relief=tk.FLAT, command=self.delete_frame).pack(side=tk.LEFT, padx=5)
          
        # Frame thumbnails area
        self.storyboard_canvas = tk.Canvas(storyboard, bg=COL_BG, highlightthickness=0)
        self.storyboard_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.storyboard_canvas.bind("<Button-1>", self.on_storyboard_click)
        self.storyboard_canvas.bind("<Double-Button-1>", self.on_storyboard_dblclick)
       
    # ──────────────────────────────────────────────────────────────────────
    #  STATUS BAR
    # ──────────────────────────────────────────────────────────────────────
       
    def setup_statusbar(self):
        self.statusbar = tk.Frame(self.root, bg=COL_BG_LIGHT, height=24)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.statusbar.pack_propagate(False)
          
        self.status_label = tk.Label(self.statusbar, text="Ready", bg=COL_BG_LIGHT, fg=COL_TEXT_DIM,
                                    font=("Consolas", 9), anchor="w", padx=10)
        self.status_label.pack(side=tk.LEFT)
          
        self.pos_label = tk.Label(self.statusbar, text="X: 0  Y: 0", bg=COL_BG_LIGHT, fg=COL_TEXT_DIM,
                                 font=("Consolas", 9), padx=10)
        self.pos_label.pack(side=tk.RIGHT)
          
        self.obj_count_label = tk.Label(self.statusbar, text="Objects: 0", bg=COL_BG_LIGHT, fg=COL_TEXT_DIM,
                                       font=("Consolas", 9), padx=10)
        self.obj_count_label.pack(side=tk.RIGHT)
          
        self.frame_label = tk.Label(self.statusbar, text="Frame 1/1", bg=COL_BG_LIGHT, fg=COL_TEXT_DIM,
                                   font=("Consolas", 9), padx=10)
        self.frame_label.pack(side=tk.RIGHT)
       
    def set_status(self, text):
        self.status_label.config(text=text)
    
    def update_statusbar(self):
        frame = self.get_current_frame()
        if frame:
             obj_count = len(frame.get("objects", []))
             self.obj_count_label.config(text=f"Objects: {obj_count}")
             self.frame_label.config(text=f"Frame {self.current_frame_idx + 1}/{len(self.project['frames'])}")
       
    # ──────────────────────────────────────────────────────────────────────
    #  EDITOR SWITCHING
    # ──────────────────────────────────────────────────────────────────────
       
    def switch_editor(self, name):
        self.current_editor = name
          
        # Hide all
        for key, widget in self.editors.items():
            widget.pack_forget()
          
        # Show selected
        self.editors[name].pack(fill=tk.BOTH, expand=True)
          
        # Update tab button highlights
        for key, btn in self.tab_buttons.items():
            if key == name:
                btn.configure(bg="#D0D0D0", fg=COL_BTN_TEXT, relief=tk.SUNKEN)
            else:
                btn.configure(bg=COL_BTN_FACE, fg=COL_BTN_TEXT, relief=tk.FLAT)
          
        # Show/hide frame editor tools
        if name == "frame":
            self.tool_frame.pack(side=tk.LEFT, padx=5)
        else:
            self.tool_frame.pack_forget()
          
        # Refresh specific editor
        if name == "event":
            self.refresh_event_editor()
        elif name == "storyboard":
            self.refresh_storyboard()
        elif name == "frame":
            self.refresh_canvas()
          
        self.set_status(f"Switched to {name.title()} Editor")
       
    # ──────────────────────────────────────────────────────────────────────
    #  FRAME EDITOR — Canvas Rendering
    # ──────────────────────────────────────────────────────────────────────
       
    def refresh_all(self):
        self.refresh_canvas()
        self.refresh_object_tree()
        self.refresh_properties()
        self.refresh_layer_manager()
        self.update_statusbar()
       
    def refresh_canvas(self):
        """Redraw the entire frame editor canvas."""
        self.editor_canvas.delete("all")
          
        frame = self.get_current_frame()
        if not frame:
            return
          
        fw = frame["width"]
        fh = frame["height"]
        z = self.zoom
          
        # Background color fill for the frame area
        self.editor_canvas.create_rectangle(0, 0, fw*z, fh*z, fill=frame.get("bg_color", "#87CEEB"),
                                           outline="", tags="bg")
          
        # Grid
        if self.show_grid:
            gs = max(1, int(GRID_SIZE * z))
            for x in range(0, int(fw * z) + 1, gs):
                major = (x // gs) % GRID_MAJOR_EVERY == 0
                color = GRID_MAJOR_COLOR if major else GRID_COLOR
                self.editor_canvas.create_line(x, 0, x, fh*z, fill=color, tags="grid")
            for y in range(0, int(fh * z) + 1, gs):
                major = (y // gs) % GRID_MAJOR_EVERY == 0
                color = GRID_MAJOR_COLOR if major else GRID_COLOR
                self.editor_canvas.create_line(0, y, fw*z, y, fill=color, tags="grid")
          
        # Frame border - Fixed color code here (no alpha allowed)
        self.editor_canvas.create_rectangle(0, 0, fw*z, fh*z, outline="#aaaaaa", width=2,
                                           dash=(6, 3), tags="border")
          
        # Objects (sorted by layer)
        objects = frame.get("objects", [])
        layers = frame.get("layers", [])
          
        for obj in sorted(objects, key=lambda o: o.get("layer", 0)):
            layer_idx = obj.get("layer", 0)
            if layer_idx < len(layers) and not layers[layer_idx].get("visible", True):
                continue
               
            self.draw_object(obj, z)
          
        # Update scroll region
        self.editor_canvas.configure(scrollregion=(
            -50, -50, max(fw*z + 100, 800), max(fh*z + 100, 600)))
       
    def draw_object(self, obj, z=1.0):
        """Draw a single object on the editor canvas."""
        x = obj["x"] * z
        y = obj["y"] * z
        w = obj["w"] * z
        h = obj["h"] * z
          
        fill = obj.get("color", "#888")
        outline = obj.get("outline", "#666")
        shape = obj.get("shape", "rect")
        obj_type = obj.get("type", "Active")
          
        is_selected = (self.selected_object and self.selected_object.get("id") == obj.get("id"))
          
        sel_outline = "#00aaff" if is_selected else outline
        sel_width = 3 if is_selected else 1
          
        tag = f"obj_{obj['id']}"
          
        if not obj.get("visible", True):
            # Draw ghost outline for invisible objects in editor
            self.editor_canvas.create_rectangle(x, y, x+w, y+h,
                                               outline="#888888", width=1, dash=(3, 3),
                                               tags=("object", tag))
            self.editor_canvas.create_text(x + w/2, y + h/2, text="👻",
                                          font=("Arial", int(8*z)), tags=("object", tag))
            return
          
        if obj_type == "Text":
            self.editor_canvas.create_rectangle(x, y, x+w, y+h, fill="",
                                               outline=sel_outline, width=sel_width,
                                               tags=("object", tag))
            self.editor_canvas.create_text(x+4, y+2,
                                          text=obj.get("text_content", "Text"),
                                          fill=fill, font=(obj.get("text_font", "Arial"),
                                                           max(6, int(obj.get("text_size", 14)*z))),
                                          anchor="nw", tags=("object", tag))
        elif obj_type == "Counter":
            self.editor_canvas.create_rectangle(x, y, x+w, y+h, fill="#222222",
                                               outline=sel_outline, width=sel_width,
                                               tags=("object", tag))
            self.editor_canvas.create_text(x+w/2, y+h/2,
                                          text=str(obj.get("counter_value", 0)),
                                          fill=fill, font=("Consolas", max(6, int(12*z)), "bold"),
                                          tags=("object", tag))
        elif shape == "oval":
            self.editor_canvas.create_oval(x, y, x+w, y+h, fill=fill,
                                          outline=sel_outline, width=sel_width,
                                          tags=("object", tag))
        elif shape == "triangle":
            pts = [x+w/2, y, x, y+h, x+w, y+h]
            self.editor_canvas.create_polygon(pts, fill=fill, outline=sel_outline,
                                             width=sel_width, tags=("object", tag))
        else:
            self.editor_canvas.create_rectangle(x, y, x+w, y+h, fill=fill,
                                               outline=sel_outline, width=sel_width,
                                               tags=("object", tag))
          
        # Type label
        label_map = {"Player": "P", "Enemy": "E", "Active": "A", "Backdrop": "B",
                     "Lives": "♥", "Timer": "⏱", "Trigger": "🔷", "Particle": "✦"}
        label = label_map.get(obj_type, "")
        if label and w > 15 and h > 15:
            self.editor_canvas.create_text(x + w/2, y + h/2, text=label,
                                          fill="white", font=("Arial", max(6, int(9*z)), "bold"),
                                          tags=("object", tag))
          
        # Selection handles
        if is_selected:
            hs = 4 * z
            for hx, hy in [(x, y), (x+w, y), (x, y+h), (x+w, y+h),
                           (x+w/2, y), (x+w/2, y+h), (x, y+h/2), (x+w, y+h/2)]:
                self.editor_canvas.create_rectangle(hx-hs, hy-hs, hx+hs, hy+hs,
                                                   fill="#00aaff", outline="white",
                                                   tags=("handle", tag))
               
            # Object name tooltip
            self.editor_canvas.create_text(x, y - 10*z, text=obj.get("name", ""),
                                          fill="#aaddff", font=("Arial", max(6, int(8*z))),
                                          anchor="sw", tags=("label", tag))
       
    # ──────────────────────────────────────────────────────────────────────
    #  FRAME EDITOR — Canvas Interaction
    # ──────────────────────────────────────────────────────────────────────
       
    def set_tool(self):
        self.current_tool = self.tool_var.get()
        cursor = "crosshair" if self.current_tool != "Select" else "arrow"
        self.editor_canvas.config(cursor=cursor)
       
    def on_canvas_click(self, event):
        cx = self.editor_canvas.canvasx(event.x)
        cy = self.editor_canvas.canvasy(event.y)
        z = self.zoom
          
        # Real coordinates
        rx = cx / z
        ry = cy / z
          
        # Snap
        if self.snap_to_grid:
            gx = snap(rx)
            gy = snap(ry)
        else:
            gx, gy = int(rx), int(ry)
          
        if self.current_tool == "Select":
            self.handle_select(cx, cy, rx, ry)
        else:
            self.save_undo()
            self.insert_object(self.current_tool, gx, gy)
          
        self.update_statusbar()
       
    def handle_select(self, cx, cy, rx, ry):
        """Handle click in select mode — find and select object."""
        frame = self.get_current_frame()
        if not frame:
            return
          
        # Find object under cursor (reverse order = topmost first)
        found = None
        for obj in reversed(frame.get("objects", [])):
            if (obj["x"] <= rx <= obj["x"] + obj["w"] and
                obj["y"] <= ry <= obj["y"] + obj["h"]):
                found = obj
                break
          
        if found:
            self.selected_object = found
            self.drag_data = {"x": rx, "y": ry, "active": True,
                             "ox": found["x"], "oy": found["y"]}
        else:
            self.selected_object = None
            self.drag_data["active"] = False
          
        self.refresh_canvas()
        self.refresh_properties()
        self.refresh_object_tree()
       
    def on_canvas_drag(self, event):
        if self.current_tool != "Select" or not self.drag_data.get("active"):
            return
        if not self.selected_object:
            return
          
        cx = self.editor_canvas.canvasx(event.x)
        cy = self.editor_canvas.canvasy(event.y)
        z = self.zoom
        rx, ry = cx / z, cy / z
          
        dx = rx - self.drag_data["x"]
        dy = ry - self.drag_data["y"]
          
        new_x = self.drag_data["ox"] + dx
        new_y = self.drag_data["oy"] + dy
          
        if self.snap_to_grid:
            new_x = snap(new_x)
            new_y = snap(new_y)
          
        self.selected_object["x"] = int(new_x)
        self.selected_object["y"] = int(new_y)
          
        self.refresh_canvas()
        self.refresh_properties()
          
        self.pos_label.config(text=f"X: {int(new_x)}  Y: {int(new_y)}")
       
    def on_canvas_release(self, event):
        if self.drag_data.get("active") and self.selected_object:
            ox = self.drag_data.get("ox", 0)
            oy = self.drag_data.get("oy", 0)
            if self.selected_object["x"] != ox or self.selected_object["y"] != oy:
                self.save_undo()
                self.modified = True
                self.update_title()
        self.drag_data["active"] = False
       
    def on_canvas_right_click(self, event):
        """Context menu on canvas."""
        cx = self.editor_canvas.canvasx(event.x)
        cy = self.editor_canvas.canvasy(event.y)
        z = self.zoom
        rx, ry = cx / z, cy / z
          
        menu = tk.Menu(self.root, tearoff=0, bg=COL_BG_LIGHT, fg=COL_TEXT)
          
        if self.selected_object:
            menu.add_command(label=f"Edit '{self.selected_object.get('name', '')}'...",
                           command=self.edit_selected_object)
            menu.add_command(label="Animation Editor...",
                           command=lambda: AnimationEditor(self.root, self.selected_object))
            menu.add_separator()
            menu.add_command(label="Copy", command=self.copy_object)
            menu.add_command(label="Duplicate", command=self.duplicate_object)
            menu.add_command(label="Delete", command=self.delete_selected_object)
            menu.add_separator()
            menu.add_command(label="Bring to Front", command=self.bring_to_front)
            menu.add_command(label="Send to Back", command=self.send_to_back)
        else:
            menu.add_command(label="Paste", command=self.paste_object,
                           state=tk.NORMAL if self.clipboard else tk.DISABLED)
            menu.add_separator()
            for otype in ["Active", "Player", "Platform", "Enemy", "Coin", "Counter", "Text"]:
                menu.add_command(label=f"Insert {otype}",
                               command=lambda t=otype, x=rx, y=ry: self.insert_object(t, int(x), int(y)))
          
        menu.tk_popup(event.x_root, event.y_root)
       
    def on_canvas_scroll(self, event):
        """Zoom with mouse wheel."""
        if event.delta > 0:
            self.set_zoom(self.zoom * 1.1)
        else:
            self.set_zoom(self.zoom / 1.1)

    def set_zoom(self, zoom_level):
        self.zoom = clamp(zoom_level, 0.1, 5.0)
        self.zoom_label.config(text=f"{int(self.zoom*100)}%")
        self.refresh_canvas()

    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.refresh_canvas()

    def toggle_snap(self):
        self.snap_to_grid = not self.snap_to_grid

    def update_title(self):
        mod = "*" if self.modified else ""
        name = os.path.basename(self.project_path) if self.project_path else "Untitled"
        self.root.title(f"{APP_TITLE} — {name}{mod}")

    def run_game(self):
        try:
            GameRuntime(self.root, self.project, start_frame=0)
        except Exception as e:
            messagebox.showerror("Runtime Error", str(e))

    def run_current_frame(self):
        try:
            GameRuntime(self.root, self.project, start_frame=self.current_frame_idx)
        except Exception as e:
            messagebox.showerror("Runtime Error", str(e))
       
    # ──────────────────────────────────────────────────────────────────────
    #  OBJECT MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────
       
    def insert_object(self, obj_type, x=100, y=100):
        frame = self.get_current_frame()
        if not frame:
            return
          
        # Only 1 player per frame
        if obj_type == "Player":
            frame["objects"] = [o for o in frame["objects"] if o["type"] != "Player"]
          
        obj = make_default_object(obj_type, x, y)
          
        # Set layer to current layer
        if self.layer_manager:
            obj["layer"] = self.layer_manager.selected_layer
          
        frame["objects"].append(obj)
        self.selected_object = obj
        self.modified = True
        self.update_title()
        self.refresh_all()
        self.set_status(f"Inserted {obj_type} at ({x}, {y})")
       
    def delete_selected_object(self):
        if not self.selected_object:
            return
          
        frame = self.get_current_frame()
        if frame:
            self.save_undo()
            frame["objects"] = [o for o in frame["objects"] if o.get("id") != self.selected_object.get("id")]
            name = self.selected_object.get("name", "")
            self.selected_object = None
            self.modified = True
            self.update_title()
            self.refresh_all()
            self.set_status(f"Deleted {name}")
       
    def copy_object(self):
        if self.selected_object:
            self.clipboard = copy.deepcopy(self.selected_object)
            self.set_status(f"Copied {self.selected_object.get('name', '')}")
       
    def paste_object(self):
        if not self.clipboard:
            return
        frame = self.get_current_frame()
        if not frame:
            return
          
        self.save_undo()
        new_obj = copy.deepcopy(self.clipboard)
        new_obj["id"] = uid()
        new_obj["name"] = f"{new_obj['type']}_{uid()[:4]}"
        new_obj["x"] += 32
        new_obj["y"] += 32
        frame["objects"].append(new_obj)
        self.selected_object = new_obj
        self.modified = True
        self.update_title()
        self.refresh_all()
        self.set_status(f"Pasted {new_obj.get('name', '')}")
       
    def duplicate_object(self):
        if self.selected_object:
            self.copy_object()
            self.paste_object()
       
    def bring_to_front(self):
        if not self.selected_object:
            return
        frame = self.get_current_frame()
        if frame:
            objs = frame["objects"]
            if self.selected_object in objs:
                objs.remove(self.selected_object)
                objs.append(self.selected_object)
                self.refresh_canvas()
       
    def send_to_back(self):
        if not self.selected_object:
            return
        frame = self.get_current_frame()
        if frame:
            objs = frame["objects"]
            if self.selected_object in objs:
                objs.remove(self.selected_object)
                objs.insert(0, self.selected_object)
                self.refresh_canvas()
       
    def select_all(self):
        pass  # Multi-select would go here
       
    def edit_selected_object(self):
        """Open detailed object editor dialog."""
        if not self.selected_object:
            return
          
        obj = self.selected_object
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Edit Object — {obj.get('name', '')}")
        dlg.geometry("450x550")
        dlg.configure(bg=COL_BG)
          
        # Scrollable content
        canvas = tk.Canvas(dlg, bg=COL_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(dlg, command=canvas.yview)
        content = tk.Frame(canvas, bg=COL_BG)
          
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
          
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(fill=tk.BOTH, expand=True)
          
        def make_field(parent, label, key, var_type=tk.StringVar):
            frame = tk.Frame(parent, bg=COL_BG)
            frame.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(frame, text=label, bg=COL_BG, fg=COL_TEXT, width=15, anchor="w",
                    font=("Arial", 9)).pack(side=tk.LEFT)
            var = var_type(value=obj.get(key, ""))
            entry = tk.Entry(frame, textvariable=var, bg=COL_BG_LIGHT, fg=COL_TEXT,
                            insertbackground=COL_TEXT, font=("Arial", 9))
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            return var
          
        tk.Label(content, text=f"Object: {obj.get('type', '')}", bg=COL_BG, fg=COL_ACCENT,
                font=("Arial", 12, "bold")).pack(pady=10)
          
        name_var = make_field(content, "Name:", "name")
        x_var = make_field(content, "X:", "x", tk.IntVar)
        y_var = make_field(content, "Y:", "y", tk.IntVar)
        w_var = make_field(content, "Width:", "w", tk.IntVar)
        h_var = make_field(content, "Height:", "h", tk.IntVar)
        speed_var = make_field(content, "Speed:", "speed", tk.IntVar)
          
        # Movement type
        mv_frame = tk.Frame(content, bg=COL_BG)
        mv_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(mv_frame, text="Movement:", bg=COL_BG, fg=COL_TEXT, width=15, anchor="w",
                font=("Arial", 9)).pack(side=tk.LEFT)
        mv_var = tk.StringVar(value=obj.get("movement", "Static"))
        mv_combo = ttk.Combobox(mv_frame, textvariable=mv_var,
                               values=["Static", "Player", "Bouncing", "8Dir", "Path", "Platform", "Race Car"],
                               state="readonly")
        mv_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
          
        # Shape
        sh_frame = tk.Frame(content, bg=COL_BG)
        sh_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(sh_frame, text="Shape:", bg=COL_BG, fg=COL_TEXT, width=15, anchor="w",
                font=("Arial", 9)).pack(side=tk.LEFT)
        sh_var = tk.StringVar(value=obj.get("shape", "rect"))
        ttk.Combobox(sh_frame, textvariable=sh_var, values=["rect", "oval", "triangle"],
                    state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
          
        # Color
        color_frame = tk.Frame(content, bg=COL_BG)
        color_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(color_frame, text="Color:", bg=COL_BG, fg=COL_TEXT, width=15, anchor="w",
                font=("Arial", 9)).pack(side=tk.LEFT)
        color_preview = tk.Label(color_frame, text="  ", bg=obj.get("color", "#888"), width=4)
        color_preview.pack(side=tk.LEFT, padx=5)
          
        def pick_color():
            result = colorchooser.askcolor(color=obj.get("color", "#888"), parent=dlg)
            if result[1]:
                obj["color"] = result[1]
                color_preview.configure(bg=result[1])
          
        tk.Button(color_frame, text="Pick...", bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 command=pick_color).pack(side=tk.LEFT)
          
        # Checkboxes
        solid_var = tk.BooleanVar(value=obj.get("solid", False))
        tk.Checkbutton(content, text="Solid (collision)", variable=solid_var,
                      bg=COL_BG, fg=COL_TEXT, selectcolor=COL_BG_LIGHT,
                      activebackground=COL_BG, font=("Arial", 9)).pack(anchor="w", padx=10, pady=2)
          
        visible_var = tk.BooleanVar(value=obj.get("visible", True))
        tk.Checkbutton(content, text="Visible at start", variable=visible_var,
                      bg=COL_BG, fg=COL_TEXT, selectcolor=COL_BG_LIGHT,
                      activebackground=COL_BG, font=("Arial", 9)).pack(anchor="w", padx=10, pady=2)
          
        # Type-specific fields
        if obj["type"] == "Text":
            text_var = make_field(content, "Text:", "text_content")
            font_var = make_field(content, "Font:", "text_font")
            size_var = make_field(content, "Size:", "text_size", tk.IntVar)
          
        if obj["type"] == "Counter":
            counter_var = make_field(content, "Initial Value:", "counter_value", tk.IntVar)
          
        if obj["type"] in ("Coin",):
            score_var = make_field(content, "Score Value:", "score_value", tk.IntVar)
          
        # Save button
        def save():
            self.save_undo()
            try:
                obj["name"] = name_var.get()
                obj["x"] = x_var.get()
                obj["y"] = y_var.get()
                obj["w"] = w_var.get()
                obj["h"] = h_var.get()
                obj["speed"] = speed_var.get()
                obj["movement"] = mv_var.get()
                obj["shape"] = sh_var.get()
                obj["solid"] = solid_var.get()
                obj["visible"] = visible_var.get()
                  
                if obj["type"] == "Text":
                    obj["text_content"] = text_var.get()
                    obj["text_font"] = font_var.get()
                    obj["text_size"] = size_var.get()
                if obj["type"] == "Counter":
                    obj["counter_value"] = counter_var.get()
                if obj["type"] in ("Coin",):
                    obj["score_value"] = score_var.get()
            except (tk.TclError, ValueError):
                pass
              
            self.modified = True
            self.update_title()
            self.refresh_all()
            dlg.destroy()
          
        tk.Button(content, text="Save Changes", bg=COL_ACCENT, fg="white",
                 font=("Arial", 10, "bold"), command=save).pack(pady=15, padx=10, fill=tk.X)
       
    # ──────────────────────────────────────────────────────────────────────
    #  OBJECT TREE
    # ──────────────────────────────────────────────────────────────────────
       
    def refresh_object_tree(self):
        self.object_tree.delete(*self.object_tree.get_children())
          
        frame = self.get_current_frame()
        if not frame:
            return
          
        layers = frame.get("layers", [])
        objects = frame.get("objects", [])
          
        # Group by layer
        for li, layer in enumerate(layers):
            layer_node = self.object_tree.insert("", "end",
                text=f"{':3' if layer.get('visible') else '  '} {layer.get('name', f'Layer {li+1}')}",
                open=True)
               
            for obj in objects:
                if obj.get("layer", 0) == li:
                    icon = {"Player": "🟥", "Platform": "🟩", "Enemy": "🟤", "Coin": "🟡",
                            "Active": "⬛", "Backdrop": "🟩", "Counter": "🔢", "Text": "📝",
                            "Lives": "❤️", "Timer": "⏱", "Trigger": "🔷", "Particle": "✦"
                            }.get(obj["type"], "⬜")
                       
                    item_id = self.object_tree.insert(layer_node, "end",
                        text=f"{icon} {obj.get('name', '?')}")
                       
                    # Highlight if selected
                    if self.selected_object and self.selected_object.get("id") == obj.get("id"):
                        self.object_tree.selection_set(item_id)
       
    def on_tree_select(self, event):
        """When clicking an item in the object tree, select it on canvas."""
        sel = self.object_tree.selection()
        if not sel:
            return
          
        text = self.object_tree.item(sel[0], "text")
        # Find matching object
        frame = self.get_current_frame()
        if not frame:
            return
          
        for obj in frame.get("objects", []):
            if obj.get("name", "") in text:
                self.selected_object = obj
                self.refresh_canvas()
                self.refresh_properties()
                return
       
    # ──────────────────────────────────────────────────────────────────────
    #  PROPERTIES PANEL
    # ──────────────────────────────────────────────────────────────────────
       
    def refresh_properties(self):
        for w in self.prop_container.winfo_children():
            w.destroy()
          
        if not self.selected_object:
            tk.Label(self.prop_container, text="No Selection", bg=COL_PANEL, fg=COL_BLUE_TEXT,
                    font=("Arial", 10)).pack(pady=20)
            tk.Label(self.prop_container, text="Click an object to\nview its properties",
                    bg=COL_PANEL, fg=COL_BLUE_TEXT, font=("Arial", 9)).pack()
            return
          
        obj = self.selected_object
          
        # Header
        type_color = OBJ_COLORS.get(obj["type"], ("#888", "#666"))[0]
        header = tk.Frame(self.prop_container, bg=type_color)
        header.pack(fill=tk.X, pady=(0, 5))
        tk.Label(header, text=f"  {obj['type']}", bg=type_color, fg="white",
                font=("Arial", 11, "bold"), anchor="w").pack(fill=tk.X, padx=5, pady=3)
          
        def prop_row(label, key, var_class=tk.StringVar, **kwargs):
            row = tk.Frame(self.prop_container, bg=COL_PANEL)
            row.pack(fill=tk.X, padx=5, pady=1)
            tk.Label(row, text=label, bg=COL_PANEL, fg=COL_BLUE_TEXT, width=10, anchor="w",
                    font=("Arial", 8)).pack(side=tk.LEFT)
            var = var_class(value=obj.get(key, kwargs.get("default", "")))
            entry = tk.Entry(row, textvariable=var, bg=COL_BG_LIGHT, fg=COL_TEXT,
                            insertbackground=COL_TEXT, font=("Consolas", 9), width=15)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
               
            def on_change(*args):
                try:
                    val = var.get()
                    if var_class == tk.IntVar:
                        val = int(val)
                    elif var_class == tk.DoubleVar:
                        val = float(val)
                    obj[key] = val
                    self.refresh_canvas()
                except (ValueError, tk.TclError):
                    pass
               
            var.trace_add("write", on_change)
            return var
          
        prop_row("Name", "name")
        prop_row("X", "x", tk.IntVar)
        prop_row("Y", "y", tk.IntVar)
        prop_row("Width", "w", tk.IntVar)
        prop_row("Height", "h", tk.IntVar)
          
        if obj.get("movement") != "Static":
            prop_row("Speed", "speed", tk.IntVar)
          
        tk.Label(self.prop_container, text=f"Movement: {obj.get('movement', 'Static')}",
                bg=COL_PANEL, fg=COL_BLUE_TEXT, font=("Arial", 8), anchor="w").pack(fill=tk.X, padx=5, pady=2)
        tk.Label(self.prop_container, text=f"Layer: {obj.get('layer', 0)}",
                bg=COL_PANEL, fg=COL_BLUE_TEXT, font=("Arial", 8), anchor="w").pack(fill=tk.X, padx=5)
        tk.Label(self.prop_container, text=f"Solid: {'Yes' if obj.get('solid') else 'No'}",
                bg=COL_PANEL, fg=COL_BLUE_TEXT, font=("Arial", 8), anchor="w").pack(fill=tk.X, padx=5)
          
        if obj["type"] == "Text":
            prop_row("Text", "text_content")
            prop_row("Font Size", "text_size", tk.IntVar)
          
        if obj["type"] == "Counter":
            prop_row("Value", "counter_value", tk.IntVar)
          
        if obj["type"] == "Coin":
            prop_row("Score", "score_value", tk.IntVar)
          
        # Action buttons
        tk.Frame(self.prop_container, bg=COL_PANEL, height=10).pack()
          
        tk.Button(self.prop_container, text="Edit Details...", bg=COL_ACCENT, fg="white",
                 relief=tk.FLAT, command=self.edit_selected_object).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(self.prop_container, text="Animation Editor", bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 relief=tk.FLAT,
                 command=lambda: AnimationEditor(self.root, self.selected_object)).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(self.prop_container, text="Delete Object", bg=COL_DANGER, fg="white",
                 relief=tk.FLAT, command=self.delete_selected_object).pack(fill=tk.X, padx=5, pady=2)
       
    # ──────────────────────────────────────────────────────────────────────
    #  LAYER MANAGER
    # ──────────────────────────────────────────────────────────────────────
       
    def refresh_layer_manager(self):
        for w in self.layer_mgr_container.winfo_children():
            w.destroy()
          
        frame = self.get_current_frame()
        if frame:
            self.layer_manager = LayerManager(self.layer_mgr_container, frame,
                                            on_change=self.refresh_canvas)
            self.layer_manager.pack(fill=tk.BOTH, expand=True)
       
    # ──────────────────────────────────────────────────────────────────────
    #  EVENT EDITOR
    # ──────────────────────────────────────────────────────────────────────
       
    def refresh_event_editor(self):
        for w in self.editors["event"].winfo_children():
            w.destroy()
          
        self.event_panel = EventEditorPanel(
            self.editors["event"], self.project, self.current_frame_idx,
            on_change=lambda: setattr(self, 'modified', True)
        )
        self.event_panel.pack(fill=tk.BOTH, expand=True)
       
    # ──────────────────────────────────────────────────────────────────────
    #  STORYBOARD
    # ──────────────────────────────────────────────────────────────────────
       
    def refresh_storyboard(self):
        self.storyboard_canvas.delete("all")
          
        frames = self.project.get("frames", [])
        thumb_w = 160
        thumb_h = 120
        margin = 20
        per_row = max(1, (self.storyboard_canvas.winfo_width() - margin) // (thumb_w + margin))
        if per_row < 1:
            per_row = 4
          
        for i, frame in enumerate(frames):
            col = i % per_row
            row = i // per_row
            x = margin + col * (thumb_w + margin)
            y = margin + row * (thumb_h + margin + 30)
               
            # Selected highlight
            if i == self.current_frame_idx:
                self.storyboard_canvas.create_rectangle(
                    x-4, y-4, x+thumb_w+4, y+thumb_h+24,
                    outline=COL_ACCENT, width=3, tags="sb_sel")
               
            # Thumbnail bg
            bg_color = frame.get("bg_color", "#87CEEB")
            self.storyboard_canvas.create_rectangle(x, y, x+thumb_w, y+thumb_h,
                                                   fill=bg_color, outline="#555",
                                                   tags=f"sb_{i}")
               
            # Mini objects
            scale_x = thumb_w / frame.get("width", 800)
            scale_y = thumb_h / frame.get("height", 600)
               
            for obj in frame.get("objects", []):
                ox = x + obj["x"] * scale_x
                oy = y + obj["y"] * scale_y
                ow = max(2, obj["w"] * scale_x)
                oh = max(2, obj["h"] * scale_y)
                color = obj.get("color", "#888")
                  
                if obj.get("shape") == "oval":
                    self.storyboard_canvas.create_oval(ox, oy, ox+ow, oy+oh,
                                                      fill=color, outline="", tags=f"sb_{i}")
                else:
                    self.storyboard_canvas.create_rectangle(ox, oy, ox+ow, oy+oh,
                                                           fill=color, outline="", tags=f"sb_{i}")
               
            # Frame label
            self.storyboard_canvas.create_text(x + thumb_w/2, y + thumb_h + 10,
                                              text=f"{i+1}. {frame.get('name', 'Frame')}",
                                              fill=COL_TEXT, font=("Arial", 9, "bold"),
                                              tags=f"sb_{i}")
               
            obj_count = len(frame.get("objects", []))
            evt_count = len(frame.get("events", []))
            self.storyboard_canvas.create_text(x + thumb_w/2, y + thumb_h + 22,
                                              text=f"{obj_count} objs, {evt_count} events",
                                              fill=COL_TEXT_DIM, font=("Arial", 8),
                                              tags=f"sb_{i}")
       
    def on_storyboard_click(self, event):
        """Select frame in storyboard."""
        frames = self.project.get("frames", [])
        thumb_w = 160
        thumb_h = 120
        margin = 20
        per_row = max(1, 4)
          
        cx = event.x
        cy = event.y
          
        for i in range(len(frames)):
            col = i % per_row
            row = i // per_row
            x = margin + col * (thumb_w + margin)
            y = margin + row * (thumb_h + margin + 30)
               
            if x <= cx <= x + thumb_w and y <= cy <= y + thumb_h + 25:
                self.current_frame_idx = i
                self.selected_object = None
                self.refresh_storyboard()
                self.set_status(f"Selected {frames[i].get('name', f'Frame {i+1}')}")
                return
       
    def on_storyboard_dblclick(self, event):
        """Double-click to switch to frame editor."""
        self.on_storyboard_click(event)
        self.switch_editor("frame")
        self.refresh_all()
       
    # ──────────────────────────────────────────────────────────────────────
    #  FRAME MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────
       
    def add_frame(self):
        idx = len(self.project["frames"])
        name = simpledialog.askstring("New Frame", "Frame name:",
                                     initialvalue=f"Frame {idx + 1}", parent=self.root)
        if name:
            self.project["frames"].append(make_default_frame(name, idx))
            self.current_frame_idx = idx
            self.selected_object = None
            self.modified = True
            self.update_title()
            self.refresh_all()
            if self.current_editor == "storyboard":
                self.refresh_storyboard()
       
    def duplicate_frame(self):
        frame = self.get_current_frame()
        if frame:
            new_frame = copy.deepcopy(frame)
            new_frame["id"] = uid()
            new_frame["name"] = f"{frame['name']} (Copy)"
            for obj in new_frame.get("objects", []):
                obj["id"] = uid()
            self.project["frames"].append(new_frame)
            self.current_frame_idx = len(self.project["frames"]) - 1
            self.modified = True
            self.update_title()
            self.refresh_all()
       
    def delete_frame(self):
        if len(self.project["frames"]) <= 1:
            messagebox.showwarning("Cannot Delete", "Must have at least one frame.", parent=self.root)
            return
          
        frame = self.get_current_frame()
        if frame and messagebox.askyesno("Delete Frame", f"Delete '{frame['name']}'?", parent=self.root):
            self.project["frames"].pop(self.current_frame_idx)
            self.current_frame_idx = max(0, self.current_frame_idx - 1)
            self.selected_object = None
            self.modified = True
            self.update_title()
            self.refresh_all()
       
    def rename_frame(self):
        frame = self.get_current_frame()
        if frame:
            name = simpledialog.askstring("Rename Frame", "New name:",
                                         initialvalue=frame["name"], parent=self.root)
            if name:
                frame["name"] = name
                self.modified = True
                self.update_title()
                self.refresh_all()
       
    def frame_properties(self):
        frame = self.get_current_frame()
        if not frame:
            return
          
        dlg = tk.Toplevel(self.root)
        dlg.title(f"Frame Properties — {frame['name']}")
        dlg.geometry("400x350")
        dlg.configure(bg=COL_BG)
          
        tk.Label(dlg, text="Frame Properties", bg=COL_BG, fg=COL_ACCENT,
                font=("Arial", 12, "bold")).pack(pady=10)
          
        fields = {}
        for label, key, default in [
            ("Name:", "name", frame["name"]),
            ("Width:", "width", frame["width"]),
            ("Height:", "height", frame["height"]),
        ]:
            row = tk.Frame(dlg, bg=COL_BG)
            row.pack(fill=tk.X, padx=20, pady=3)
            tk.Label(row, text=label, bg=COL_BG, fg=COL_TEXT, width=10, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=str(default))
            tk.Entry(row, textvariable=var, bg=COL_BG_LIGHT, fg=COL_TEXT,
                    insertbackground=COL_TEXT).pack(side=tk.LEFT, fill=tk.X, expand=True)
            fields[key] = var
          
        # BG color
        color_row = tk.Frame(dlg, bg=COL_BG)
        color_row.pack(fill=tk.X, padx=20, pady=3)
        tk.Label(color_row, text="BG Color:", bg=COL_BG, fg=COL_TEXT, width=10, anchor="w").pack(side=tk.LEFT)
        color_preview = tk.Label(color_row, text="  ", bg=frame.get("bg_color", "#87CEEB"), width=4)
        color_preview.pack(side=tk.LEFT, padx=5)
          
        def pick_bg():
            result = colorchooser.askcolor(color=frame.get("bg_color", "#87CEEB"), parent=dlg)
            if result[1]:
                frame["bg_color"] = result[1]
                color_preview.configure(bg=result[1])
          
        tk.Button(color_row, text="Pick...", bg=COL_BTN_FACE, fg=COL_BTN_TEXT, command=pick_bg).pack(side=tk.LEFT)
          
        def save():
            try:
                frame["name"] = fields["name"].get()
                frame["width"] = int(fields["width"].get())
                frame["height"] = int(fields["height"].get())
            except ValueError:
                pass
            self.modified = True
            self.update_title()
            self.refresh_all()
            dlg.destroy()
          
        tk.Button(dlg, text="Save", bg=COL_ACCENT, fg="white", command=save).pack(pady=15)
       
    # ──────────────────────────────────────────────────────────────────────
    #  PROJECT MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────
       
    def new_project(self):
        if self.modified:
            if not messagebox.askyesno("New Project", "Discard unsaved changes?", parent=self.root):
                return
          
        self.project = make_default_project()
        self.project_path = None
        self.current_frame_idx = 0
        self.selected_object = None
        self.modified = False
        self.undo_mgr = UndoManager()
        self.update_title()
        self.refresh_all()
        self.set_status("New project created")
       
    def save_project(self):
        if self.project_path:
            self._do_save(self.project_path)
        else:
            self.save_project_as()
       
    def save_project_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".acp",
            filetypes=[("AC Engine Project", "*.acp"), ("JSON", "*.json"), ("All Files", "*.*")],
            parent=self.root
        )
        if path:
            self._do_save(path)
       
    def _do_save(self, path):
        try:
            with open(path, "w") as f:
                json.dump(self.project, f, indent=2)
            self.project_path = path
            self.modified = False
            self.update_title()
            self.set_status(f"Saved to {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Save Error", str(e), parent=self.root)
       
    def load_project(self):
        if self.modified:
            if not messagebox.askyesno("Open Project", "Discard unsaved changes?", parent=self.root):
                return
          
        path = filedialog.askopenfilename(
            filetypes=[("AC Engine Project", "*.acp"), ("JSON", "*.json"), ("All Files", "*.*")],
            parent=self.root
        )
        if path:
            try:
                with open(path, "r") as f:
                    self.project = json.load(f)
                self.project_path = path
                self.current_frame_idx = 0
                self.selected_object = None
                self.modified = False
                self.undo_mgr = UndoManager()
                self.update_title()
                self.refresh_all()
                self.set_status(f"Loaded {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Load Error", str(e), parent=self.root)
       
    def project_properties(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Project Properties")
        dlg.geometry("450x400")
        dlg.configure(bg=COL_BG)
          
        tk.Label(dlg, text="Application Properties", bg=COL_BG, fg=COL_ACCENT,
                font=("Arial", 13, "bold")).pack(pady=10)
          
        fields = {}
        for label, key, default in [
            ("App Name:", "name", self.project.get("name", "")),
            ("Author:", "author", self.project.get("author", "")),
            ("Version:", "version", self.project.get("version", "")),
            ("Window Width:", "window_width", self.project.get("window_width", 800)),
            ("Window Height:", "window_height", self.project.get("window_height", 600)),
            ("FPS:", "fps", self.project.get("fps", 60)),
            ("Initial Lives:", "lives", self.project.get("lives", 3)),
        ]:
            row = tk.Frame(dlg, bg=COL_BG)
            row.pack(fill=tk.X, padx=20, pady=3)
            tk.Label(row, text=label, bg=COL_BG, fg=COL_TEXT, width=14, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value=str(default))
            tk.Entry(row, textvariable=var, bg=COL_BG_LIGHT, fg=COL_TEXT,
                    insertbackground=COL_TEXT).pack(side=tk.LEFT, fill=tk.X, expand=True)
            fields[key] = var
          
        def save():
            try:
                self.project["name"] = fields["name"].get()
                self.project["author"] = fields["author"].get()
                self.project["version"] = fields["version"].get()
                self.project["window_width"] = int(fields["window_width"].get())
                self.project["window_height"] = int(fields["window_height"].get())
                self.project["fps"] = int(fields["fps"].get())
                self.project["lives"] = int(fields["lives"].get())
            except ValueError:
                pass
            self.modified = True
            self.update_title()
            dlg.destroy()
          
        tk.Button(dlg, text="Save", bg=COL_ACCENT, fg="white", font=("Arial", 10, "bold"),
                 command=save).pack(pady=15)
       
    def build_settings(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Build Settings")
        dlg.geometry("400x300")
        dlg.configure(bg=COL_BG)
          
        tk.Label(dlg, text="🔨 Build Settings", bg=COL_BG, fg=COL_ACCENT,
                font=("Arial", 13, "bold")).pack(pady=10)
          
        tk.Label(dlg, text="Build Target:", bg=COL_BG, fg=COL_TEXT).pack(anchor="w", padx=20)
        build_var = tk.StringVar(value=self.project.get("build_type", "Standalone"))
        for target in ["Standalone (EXE)", "HTML5 (Web)", "Android (APK)"]:
            tk.Radiobutton(dlg, text=target, variable=build_var, value=target.split()[0],
                          bg=COL_BG, fg=COL_TEXT, selectcolor=COL_BG_LIGHT,
                          activebackground=COL_BG).pack(anchor="w", padx=40)
          
        fs_var = tk.BooleanVar(value=self.project.get("build_settings", {}).get("fullscreen", False))
        tk.Checkbutton(dlg, text="Fullscreen", variable=fs_var, bg=COL_BG, fg=COL_TEXT,
                      selectcolor=COL_BG_LIGHT, activebackground=COL_BG).pack(anchor="w", padx=20, pady=10)
          
        tk.Label(dlg, text="(Build/export is a stub in v0.1)", bg=COL_BG, fg=COL_TEXT_DIM,
                font=("Arial", 9, "italic")).pack(pady=10)
          
        tk.Button(dlg, text="Close", bg=COL_BTN_FACE, fg=COL_BTN_TEXT,
                 command=dlg.destroy).pack(pady=10)
       
    # ──────────────────────────────────────────────────────────────────────
    #  DIALOGS
    # ──────────────────────────────────────────────────────────────────────
       
    def show_about(self):
        messagebox.showinfo("About AC Engine", (
            f"AC Engine {APP_VERSION}\n"
            f"A Clickteam Fusion-Style Game IDE\n\n"
            f"Developed by Team Flames / Samsoft\n"
            f"Built with Python & Tkinter\n\n"
            f"Features:\n"
            f"  • Visual Frame Editor with layers\n"
            f"  • Event Editor (condition→action)\n"
            f"  • Storyboard (multi-frame management)\n"
            f"  • Runtime Engine for play-testing\n"
            f"  • Animation Editor\n"
            f"  • Expression Builder\n"
            f"  • Undo/Redo, Copy/Paste\n"
            f"  • Project Save/Load (.acp)\n"
            f"  • Grid, Snap, Zoom controls\n"
            f"\n© 2026 Team Flames"
        ), parent=self.root)
       
    def show_shortcuts(self):
        messagebox.showinfo("Keyboard Shortcuts", (
            "Ctrl+N — New Project\n"
            "Ctrl+O — Open Project\n"
            "Ctrl+S — Save Project\n"
            "Ctrl+Z — Undo\n"
            "Ctrl+Y — Redo\n"
            "Ctrl+C — Copy Object\n"
            "Ctrl+V — Paste Object\n"
            "Delete — Delete Selected\n"
            "F1 — Frame Editor\n"
            "F2 — Event Editor\n"
            "F3 — Storyboard\n"
            "F5 — Run Application\n"
            "F6 — Run Current Frame\n"
            "Mouse Wheel — Zoom\n"
            "Right Click — Context Menu"
        ), parent=self.root)
       
    def on_exit(self):
        if self.modified:
            if not messagebox.askyesno("Exit", "Discard unsaved changes?", parent=self.root):
                return
        self.root.quit()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
      
    # Try to set a nicer theme on supported platforms
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
      
    app = ACEngine(root)
    root.protocol("WM_DELETE_WINDOW", app.on_exit)
    root.mainloop()

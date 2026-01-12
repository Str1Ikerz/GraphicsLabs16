import tkinter as tk
from tkinter import filedialog
import math
import os

class Camera3D:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.cx = w // 2
        self.cy = h // 2
        self.scale = 100
        self.rx = 0.6
        self.ry = 0.6
        self.shift_x = 0
        self.shift_y = 0
        self.shift_z = 0

    def project(self, x, y, z):
        x -= self.shift_x
        y -= self.shift_y
        z -= self.shift_z

        cx, sx = math.cos(self.rx), math.sin(self.rx)
        cy, sy = math.cos(self.ry), math.sin(self.ry)

        y1 = y * cx - z * sx
        z1 = y * sx + z * cx

        x2 = x * cy + z1 * sy
        y2 = y1

        return (
            x2 * self.scale + self.cx,
            -y2 * self.scale + self.cy,
            z1
        )

def load_mtl(path):
    materials = {}
    current = None

    def load_mtl(path):
        print(f"Пытаюсь загрузить MTL: {path}")
        materials = {}
        current = None

        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    print(f"Обрабатываю строку: {line}")  # ← ДОБАВЬ ЭТО

                    if line.startswith("newmtl"):
                        current = line.split()[1]
                        materials[current] = (200, 200, 200)

                    elif line.startswith("Kd") and current:
                        r, g, b = map(float, line.split()[1:])
                        materials[current] = (
                            int(r * 255),
                            int(g * 255),
                            int(b * 255)
                        )
        except Exception as e:
            print(f"Ошибка при чтении MTL: {e}")

        return materials

    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("newmtl"):
                current = line.split()[1]
                materials[current] = (200, 200, 200)

            elif line.startswith("Kd") and current:
                r, g, b = map(float, line.split()[1:])
                materials[current] = (
                    int(r * 255),
                    int(g * 255),
                    int(b * 255)
                )
    return materials

def load_obj(path):
    vertices = []
    faces = []
    materials = {}
    current_mtl = None

    base_dir = os.path.dirname(path)

    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("mtllib"):
                mtl_file = line.split()[1].strip()
                mtl_path = os.path.join(base_dir, mtl_file)
                if os.path.exists(mtl_path):
                    materials = load_mtl(mtl_path)

            elif line.startswith("v "):
                vertices.append(tuple(map(float, line.split()[1:4])))

            elif line.startswith("usemtl"):
                current_mtl = line.split()[1].strip()

            elif line.startswith("f"):
                idx = [int(v.split("/")[0]) - 1 for v in line.split()[1:]]
                faces.append((idx, current_mtl))

    return vertices, faces, materials

class ViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OBJ + MTL Viewer (Auto Fit)")

        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack()

        self.cam = Camera3D(800, 600)

        tk.Button(root, text="Открыть OBJ", command=self.open_obj).pack(pady=5)

    def open_obj(self):
        path = filedialog.askopenfilename(filetypes=[("OBJ files", "*.obj")])
        if not path:
            return

        self.vertices, self.faces, self.materials = load_obj(path)
        self.auto_fit()
        self.draw()
        print(self.materials)

    # ========== АВТОПОДБОР ==========
    def auto_fit(self):
        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]
        zs = [v[2] for v in self.vertices]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)

        self.cam.shift_x = (min_x + max_x) / 2
        self.cam.shift_y = (min_y + max_y) / 2
        self.cam.shift_z = (min_z + max_z) / 2

        size_x = max_x - min_x
        size_y = max_y - min_y
        size_z = max_z - min_z

        max_size = max(size_x, size_y, size_z)
        self.cam.scale = min(self.cam.w, self.cam.h) / (max_size * 2)

    def draw(self):
        self.canvas.delete("all")
        polys = []

        for idxs, mtl in self.faces:
            pts = [self.cam.project(*self.vertices[i]) for i in idxs]
            depth = sum(p[2] for p in pts) / len(pts)
            color = self.materials.get(mtl, (180, 180, 180))
            polys.append((depth, pts, color))

        polys.sort(key=lambda x: x[0], reverse=True)

        for _, pts, color in polys:
            self.canvas.create_polygon(
                [(p[0], p[1]) for p in pts],
                fill=f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
                outline="black"
            )

if __name__ == "__main__":
    root = tk.Tk()
    ViewerApp(root)
    root.mainloop()

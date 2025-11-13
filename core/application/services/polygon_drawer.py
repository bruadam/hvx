import base64
import sys
from io import BytesIO

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image, ImageDraw


class PolygonDrawingInterface:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.points = []
        self.polygons = []  # [{"room_id": ..., "polygon": [(x,y), ...]}]
        self.fig, self.ax = plt.subplots()
        self.img = mpimg.imread(image_path)
        self.ax.imshow(self.img)
        self.ax.set_title("Left-click: add points | Right-click: finish polygon | Close to finish")
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)

    def onclick(self, event):
        if event.xdata is None or event.ydata is None:
            return  # Ignore clicks outside image

        if event.button == 1:  # Left-click
            self.points.append((event.xdata, event.ydata))
            self.ax.plot(event.xdata, event.ydata, 'ro')
            self.fig.canvas.draw()

        elif event.button == 3:  # Right-click
            if len(self.points) > 2:
                room_id = input("Enter room_id for this polygon: ").strip()
                poly = Polygon(self.points, closed=True, fill=False, edgecolor='red', linewidth=2)
                self.ax.add_patch(poly)
                self.polygons.append({"room_id": room_id, "polygon": self.points.copy()})
                self.points.clear()
                self.fig.canvas.draw()
            else:
                print("⚠ Need at least 3 points to create a polygon.")

    def run(self):
        plt.show()
        return self.polygons


class PolygonDrawer:
    def __init__(self, image_path: str, polygons: list[dict]):
        """
        polygons: [{"room_id": "101", "polygon": [(x,y), ...]}, ...]
        """
        self.image_path = image_path
        self.polygons = polygons
        self.image = Image.open(image_path).convert("RGBA")

    def draw(self, outline_color="red", text_color="blue", width=3):
        draw = ImageDraw.Draw(self.image, "RGBA")
        for p in self.polygons:
            coords = [(float(x), float(y)) for x, y in p["polygon"]]
            draw.line(coords + [coords[0]], fill=outline_color, width=width)
            # Draw room ID at centroid
            cx = sum(x for x, _ in coords) / len(coords)
            cy = sum(y for _, y in coords) / len(coords)
            draw.text((cx, cy), str(p["room_id"]), fill=text_color)

    def to_base64(self):
        buffer = BytesIO()
        self.image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def save(self, out_path: str):
        self.image.save(out_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: python polygon_drawer.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    interface = PolygonDrawingInterface(image_path)
    polygons = interface.run()

    if not polygons:
        print("No polygons drawn.")
        return

    drawer = PolygonDrawer(image_path, polygons)
    drawer.draw()
    base64_img = drawer.to_base64()
    out_path = "output_with_polygons.png"
    drawer.save(out_path)

    print(f"✅ Saved image with polygons to {out_path}")
    print(f"✅ Base64 length: {len(base64_img)}")


if __name__ == "__main__":
    main()

import os
import pickle
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
from concurrent.futures import ThreadPoolExecutor, as_completed

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class CoordinatePlotter:
    def __init__(self, df):
        self.df = df
        self.app = ctk.CTk()
        self.app.title("Song Cluster Visualization")
        self.app.geometry("600x600")
        self.app.after(0, lambda: self.app.state('zoomed'))
        self.canvas = tk.Canvas(self.app, bg='white')
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', self.on_resize)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<MouseWheel>', self.on_zoom)
        self.canvas.bind('<Motion>', self.on_hover)
        self.canvas_width = 600
        self.canvas_height = 600
        self.zoom_level = 0.6
        self.offset_x = 0
        self.offset_y = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.image_cache = {}
        self.images_loaded = False
        self.loading_lock = threading.Lock()
        self.canvas_items = []
        self.tooltip = tk.Label(self.canvas, bg='black', fg='white', font=('Arial', 10), padx=4, pady=2)
        self.tooltip.place_forget()
        self.status_label = ctk.CTkLabel(self.app, text="Loading images...")
        self.status_label.pack(side='bottom')
        self.cluster_label_map = {
            "Classic": 0,
            "Phonk": 1,
            "Casual Pop": 2,
            "Energetic Pop": 3
        }
        self.selected_cluster = tk.StringVar(value="all")
        cluster_frame = ctk.CTkFrame(self.app, fg_color="#FFFFFF")
        cluster_frame.place(relx=1, y=10, anchor='ne')
        clusters = ["all", "Classic", "Phonk", "Casual Pop", "Energetic Pop"]
        for c in clusters:
            rb = ctk.CTkRadioButton(
                cluster_frame,
                text=c.capitalize(),
                variable=self.selected_cluster,
                value=c,
                command=self.plot_points,
                bg_color="#FFFFFF"
            )
            rb.pack(anchor='w', padx=5, pady=2)
        self.load_all_images()

    def load_image_for_row(self, row_data):
        image_path = os.path.join("./covers", row_data['cover'])
        cluster = row_data['cluster']
        cluster_colors = {0: "#FFA500", 1: "#BE3B3B", 2: "#5656C1", 3: '#2B7D2B'}
        stroke_color = cluster_colors.get(cluster, '#FFFFFF')
        zoom_levels = [0.25, 0.5, 0.75, 1, 1.5, 2.0, 2.5, 3, 3.5, 4]
        base_size = 16
        images_for_row = {}
        try:
            original_img = Image.open(image_path)
            for zoom in zoom_levels:
                size = max(8, int(base_size * zoom))
                img = original_img.resize((size-4, size-4), Image.Resampling.LANCZOS)
                final_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                mask = Image.new('L', (size-4, size-4), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, size-4, size-4), fill=255)
                rounded_img = Image.new('RGBA', (size-4, size-4), (0, 0, 0, 0))
                rounded_img.paste(img, (0, 0))
                rounded_img.putalpha(mask)
                final_img.paste(rounded_img, (2, 2), rounded_img)
                draw = ImageDraw.Draw(final_img)
                draw.ellipse((0, 0, size-1, size-1), outline=stroke_color, width=4)
                photo = ImageTk.PhotoImage(final_img)
                images_for_row[zoom] = photo
        except Exception:
            images_for_row = None
        return row_data['cover'], images_for_row

    def load_all_images(self):
        def loading_thread():
            total_images = len(self.df)
            loaded_count = 0
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_row = {executor.submit(self.load_image_for_row, row): row for _, row in self.df.iterrows()}
                for future in as_completed(future_to_row):
                    cover_name, images = future.result()
                    with self.loading_lock:
                        if images:
                            self.image_cache[cover_name] = images
                        loaded_count += 1
                        progress = (loaded_count / total_images) * 100
                        self.app.after(0, lambda p=progress: self.status_label.configure(text=f"Loading images... {int(p)}%"))
            with self.loading_lock:
                self.images_loaded = True
            self.app.after(0, lambda: self.status_label.configure(text="Ready"))
            self.app.after(100, self.plot_points)
            self.app.after(3000, self.status_label.pack_forget)
        threading.Thread(target=loading_thread, daemon=True).start()

    def get_best_zoom_image(self, cover_name, target_zoom):
        if cover_name not in self.image_cache:
            return None
        available_zooms = list(self.image_cache[cover_name].keys())
        best_zoom = min(available_zooms, key=lambda x: abs(x - target_zoom))
        return self.image_cache[cover_name][best_zoom]

    def on_resize(self, event):
        self.canvas_width = event.width
        self.canvas_height = event.height
        if self.images_loaded:
            self.plot_points()

    def on_click(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_drag(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.offset_x += dx
        self.offset_y += dy
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        if self.images_loaded:
            self.plot_points()

    def on_zoom(self, event):
        if event.delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level *= 0.9
        if self.images_loaded:
            self.plot_points()

    def on_hover(self, event):
        x, y = event.x, event.y
        hovered = False
        for item in self.canvas_items:
            dx = x - item['x']
            dy = y - item['y']
            dist_sq = dx * dx + dy * dy
            if dist_sq <= 400:
                self.tooltip.configure(text=item['title'])
                self.tooltip.place(x=x + 15, y=y + 10)
                hovered = True
                break
        if not hovered:
            self.tooltip.place_forget()

    def draw_grid(self, spacing=100):
        for x in range(0, self.canvas_width, spacing):
            self.canvas.create_line(x, 0, x, self.canvas_height, fill='lightgray', dash=(2, 4))
        for y in range(0, self.canvas_height, spacing):
            self.canvas.create_line(0, y, self.canvas_width, y, fill='lightgray', dash=(2, 4))

    def plot_points(self):
        with self.loading_lock:
            if not self.images_loaded:
                return
        self.canvas.delete("all")
        self.canvas_items.clear()
        self.draw_grid()
        center_x = self.canvas_width // 2 + self.offset_x
        center_y = self.canvas_height // 2 + self.offset_y
        self.canvas.create_line(center_x - 10, center_y, center_x + 10, center_y, fill='lightgray', width=1)
        self.canvas.create_line(center_x, center_y - 10, center_x, center_y + 10, fill='lightgray', width=1)
        if len(self.df) == 0:
            return
        x_min, x_max = self.df['x'].min(), self.df['x'].max()
        y_min, y_max = self.df['y'].min(), self.df['y'].max()
        margin = 50
        scale_x = (self.canvas_width - 2 * margin) / max(abs(x_min), abs(x_max), 1) if max(abs(x_min), abs(x_max)) != 0 else 1
        scale_y = (self.canvas_height - 2 * margin) / max(abs(y_min), abs(y_max), 1) if max(abs(y_min), abs(y_max)) != 0 else 1
        scale = min(scale_x, scale_y) * 0.8 * self.zoom_level
        selected = self.selected_cluster.get()
        for _, row in self.df.iterrows():
            if selected != "all" and self.cluster_label_map.get(selected) != row['cluster']:
                continue
            canvas_x = center_x + (row['x'] * scale)
            canvas_y = center_y - (row['y'] * scale)
            rounded_img = self.get_best_zoom_image(row['cover'], self.zoom_level)
            title = row['title']
            if rounded_img:
                item = self.canvas.create_image(canvas_x, canvas_y, image=rounded_img)
            else:
                cluster_colors = {0: "#FFA500", 1: "#BE3B3B", 2: "#5656C1", 3: '#2B7D2B'}
                color = cluster_colors.get(row['cluster'], '#FFFFFF')
                dot_size = max(2, int(4 * self.zoom_level))
                item = self.canvas.create_oval(canvas_x - dot_size, canvas_y - dot_size,
                                               canvas_x + dot_size, canvas_y + dot_size,
                                               fill=color, outline='darkgray', width=2)
            self.canvas_items.append({'id': item, 'x': canvas_x, 'y': canvas_y, 'title': title})

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    with open('song_clusters.pkl', 'rb') as f:
        df = pickle.load(f)
    plotter = CoordinatePlotter(df)
    plotter.run()
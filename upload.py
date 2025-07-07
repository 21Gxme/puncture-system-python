# Now let's patch the draw_realtime_line and draw_realtime_line_optimized methods
import re

# Replace or rewrite the existing draw_realtime_line and draw_realtime_line_optimized methods with smoother logic
# Load the main_window_code from a file or define it as a string before using it
with open("/mnt/data/main_window.py", "r", encoding="utf-8") as f:
    main_window_code = f.read()

patched_main_window_code = re.sub(
    r"def draw_realtime_line\(self,.*?def",
    '''
def draw_realtime_line(self, point):
    if not hasattr(self, "realtime_points"):
        self.realtime_points = []
    self.realtime_points.append(point)

    if len(self.realtime_points) < 2:
        return

    points_array = np.array([[p.x, p.y] for p in self.realtime_points])

    if self.realtime_line is None:
        self.realtime_line = self.canvas.add_line(points_array, color="red")
    else:
        self.realtime_line.set_data(points_array)

def
''',
    main_window_code,
    flags=re.DOTALL
)

# Inject timer-based smoother updater (optional enhancement if desired)
if "def start_realtime_drawing" not in patched_main_window_code:
    patched_main_window_code += '''

def start_realtime_drawing(self):
    self.realtime_points = []
    self.realtime_line = None
    self.realtime_timer = QTimer()
    self.realtime_timer.timeout.connect(self.update_realtime_line)
    self.realtime_timer.start(50)

def update_realtime_line(self):
    if len(self.realtime_points) < 2:
        return
    points_array = np.array([[p.x, p.y] for p in self.realtime_points])
    if self.realtime_line is None:
        self.realtime_line = self.canvas.add_line(points_array, color="red")
    else:
        self.realtime_line.set_data(points_array)
'''

# Save the patched file
patched_path = "/mnt/data/main_window_patched.py"
with open(patched_path, "w", encoding="utf-8") as f:
    f.write(patched_main_window_code)

patched_path

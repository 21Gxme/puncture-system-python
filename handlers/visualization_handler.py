import numpy as np
from vispy import scene
from vispy.scene import visuals
from vispy.visuals.transforms import STTransform

class VisualizationHandler:
    def __init__(self):
        self.canvas = None
        self.view = None
        self.volume = None
        self.scatter = None
        self.dash_line = None
        self.realtime_line_vispy = None
        
    def visualize_vispy(self, volume3d):
        """Create 3D visualization using VisPy"""
        self.canvas = scene.SceneCanvas(keys='interactive', show=True)
        self.view = self.canvas.central_widget.add_view()

        new_volume3d = np.flipud(np.rollaxis(volume3d, 2))
        self.volume = scene.visuals.Volume(new_volume3d, parent=self.view.scene, threshold=0.225)

        self.view.camera = scene.cameras.TurntableCamera(parent=self.view.scene, fov=60, elevation=90, azimuth=180, roll=180)
        
        self.view.camera.elevation_range = (0, 180)
        self.view.camera.azimuth_range = (None, None)

        axis = scene.visuals.XYZAxis(parent=self.view.scene)
        s = STTransform(translate=(50, 50, 0), scale=(50, 50, 50))
        axis.transform = s

        self.scatter = visuals.Markers()
        self.view.add(self.scatter)
        
        self.dash_line = visuals.Line(color='green', width=3, method='gl', parent=self.view.scene)
        self.realtime_line_vispy = visuals.Line(color='red', width=2, method='gl', parent=self.view.scene)
        self.view.add(self.realtime_line_vispy)
        
    def draw_needle_plan_vispy(self, point_start, point_end, plan_line_deleted):
        """Draw planned needle path in 3D"""
        if plan_line_deleted or not hasattr(self, 'dash_line'):
            return
        try:
            x0, y0, z0 = point_start
            x1, y1, z1 = point_end
            dash_length = 5
            gap_length = 3
            total_length = ((x1 - x0)**2 + (y1 - y0)**2 + (z1 - z0)**2) ** 0.5
            num_dashes = int(total_length // (dash_length + gap_length))

            points = []
            for i in range(num_dashes):
                start_x = x0 + (x1 - x0) * (i * (dash_length + gap_length)) / total_length
                start_y = y0 + (y1 - y0) * (i * (dash_length + gap_length)) / total_length
                start_z = z0 + (z1 - z0) * (i * (dash_length + gap_length)) / total_length
                end_x = start_x + (x1 - x0) * dash_length / total_length
                end_y = start_y + (y1 - y0) * dash_length / total_length
                end_z = start_z + (z1 - z0) * dash_length / total_length
                points.extend([[start_x, start_y, start_z], [end_x, end_y, end_z]])

            self.dash_line.set_data(np.array(points), connect='segments')
        except AttributeError:
            pass
            
    def update_realtime_line_vispy(self, realtime_points, realtime_line_deleted):
        """Update real-time line in 3D visualization"""
        if realtime_line_deleted:
            return
        if not hasattr(self, 'realtime_line_vispy'):
            self.realtime_line_vispy = visuals.Line(color='red', width=2, method='gl', parent=self.view.scene)

        if realtime_points:
            points = np.array(realtime_points)
            self.realtime_line_vispy.set_data(points, connect='strip')
            
    def clear_lines(self):
        """Clear all visualization lines"""
        if hasattr(self, 'dash_line'):
            self.dash_line.set_data(np.array([]))
        if hasattr(self, 'realtime_line_vispy'):
            self.realtime_line_vispy.set_data(np.array([]))

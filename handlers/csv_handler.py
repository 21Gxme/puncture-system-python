import csv
import threading
import time

class CSVHandler:
    def __init__(self, callback_func):
        self.csv_file_path = None
        self.previous_data_length = 0
        self.realtime_points = []
        self.check_csv_thread = None
        self.stop_thread = False
        self.callback_func = callback_func
        
    def set_csv_file(self, file_path):
        """Set the CSV file path for real-time monitoring"""
        self.csv_file_path = file_path
        
    def start_realtime_monitoring(self):
        """Start monitoring CSV file for new data"""
        if self.csv_file_path is None:
            print("Please select a CSV file first.")
            return

        if self.check_csv_thread is None:
            self.stop_thread = False
            self.check_csv_thread = threading.Thread(target=self.check_csv_for_updates)
            self.check_csv_thread.daemon = True
            self.check_csv_thread.start()
            print("Started real-time data acquisition")
            
    def stop_realtime_monitoring(self):
        """Stop monitoring CSV file"""
        self.stop_thread = True
        self.check_csv_thread = None
        print("Stopped real-time data acquisition")
        
    def check_csv_for_updates(self):
        """Check CSV file for new data periodically"""
        while not self.stop_thread:
            try:
                with open(self.csv_file_path, 'r') as file:
                    reader = csv.reader(file)
                    data = list(reader)

                if len(data) > self.previous_data_length:
                    new_rows = data[self.previous_data_length:]
                    self.previous_data_length = len(data)

                    for row in new_rows:
                        x, y, z = map(float, row)
                        self.realtime_points.append([x, y, z])
                        self.callback_func()

                # time.sleep(1)
            except Exception as e:
                print(f"Error reading CSV file: {e}")
                break
                
    def load_plan_coordinates(self, file_path):
        """Load planned coordinates from CSV file"""
        with open(file_path, newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            points = [list(map(float, row)) for row in csv_reader]
        
        if len(points) < 2:
            return None, None
            
        return points[0], points[1]
        
    def clear_realtime_points(self):
        """Clear all real-time points"""
        self.realtime_points = []
        self.previous_data_length = 0

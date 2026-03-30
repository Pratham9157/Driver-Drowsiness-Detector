import os
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "driver.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")

    return {
        "name": "John Doe",
        "id": "DRV12345",
        "vehicle": "TN-01-AB-1234",
        "phone": "+1-555-123-4567"
    }


def save_config(config):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


class DriverConfigApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Driver Credentials Configuration")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        self.config = load_config()

        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Driver Drowsiness Detection System",
                  font=("Helvetica", 14, "bold")).pack(pady=10)
        ttk.Label(main_frame, text="Driver Credentials Configuration",
                  font=("Helvetica", 12)).pack(pady=5)

        form_frame = ttk.LabelFrame(main_frame, text="Driver Information", padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        ttk.Label(name_frame, text="Driver Name:", width=15).pack(side=tk.LEFT)
        self.name_var = tk.StringVar(value=self.config["name"])
        ttk.Entry(name_frame, textvariable=self.name_var, width=30).pack(side=tk.LEFT, padx=5)

        id_frame = ttk.Frame(form_frame)
        id_frame.pack(fill=tk.X, pady=5)
        ttk.Label(id_frame, text="Driver ID:", width=15).pack(side=tk.LEFT)
        self.id_var = tk.StringVar(value=self.config["id"])
        ttk.Entry(id_frame, textvariable=self.id_var, width=30).pack(side=tk.LEFT, padx=5)

        vehicle_frame = ttk.Frame(form_frame)
        vehicle_frame.pack(fill=tk.X, pady=5)
        ttk.Label(vehicle_frame, text="Vehicle Number:", width=15).pack(side=tk.LEFT)
        self.vehicle_var = tk.StringVar(value=self.config["vehicle"])
        ttk.Entry(vehicle_frame, textvariable=self.vehicle_var, width=30).pack(side=tk.LEFT, padx=5)

        phone_frame = ttk.Frame(form_frame)
        phone_frame.pack(fill=tk.X, pady=5)
        ttk.Label(phone_frame, text="Phone Number:", width=15).pack(side=tk.LEFT)
        self.phone_var = tk.StringVar(value=self.config["phone"])
        ttk.Entry(phone_frame, textvariable=self.phone_var, width=30).pack(side=tk.LEFT, padx=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Save Configuration",
                   command=self.save_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save & Run Detection",
                   command=self.run_detection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset to Default",
                   command=self.reset_configuration).pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar()
        ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN,
                  anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Ready")

    def save_configuration(self):
        config = {
            "name": self.name_var.get(),
            "id": self.id_var.get(),
            "vehicle": self.vehicle_var.get(),
            "phone": self.phone_var.get()
        }

        if not all(config.values()):
            messagebox.showerror("Input Error", "All fields must be filled")
            return

        if save_config(config):
            self.config = config
            self.status_var.set("Configuration saved successfully!")
            messagebox.showinfo("Success", "Driver configuration has been saved successfully!")
        else:
            self.status_var.set("Error saving configuration")
            messagebox.showerror("Error", "Failed to save configuration")

    def reset_configuration(self):
        default_config = {
            "name": "John Doe",
            "id": "DRV12345",
            "vehicle": "TN-01-AB-1234",
            "phone": "+1-555-123-4567"
        }
        self.name_var.set(default_config["name"])
        self.id_var.set(default_config["id"])
        self.vehicle_var.set(default_config["vehicle"])
        self.phone_var.set(default_config["phone"])
        self.status_var.set("Configuration reset to default values")

    def run_detection(self):
        self.save_configuration()
        self.status_var.set("Starting drowsiness detection...")
        try:
            detector_path = os.path.join(os.path.dirname(__file__), "detector.py")
            subprocess.Popen(["python", detector_path])
            self.root.destroy()
        except Exception as e:
            self.status_var.set(f"Error launching detection: {e}")
            messagebox.showerror("Launch Error", f"Failed to start drowsiness detection: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DriverConfigApp(root)
    root.mainloop()

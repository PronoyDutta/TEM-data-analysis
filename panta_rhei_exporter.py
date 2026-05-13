import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import zipfile
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import json
import os
import traceback
import io
import sys
import webbrowser
from PIL import Image, ImageTk
import datetime
import time

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PantaRheiExporter:
    def __init__(self, root):
        self.root = root
        self.root.title("Panta Rhei Publication Exporter v3")
        self.root.geometry("500x680")
        
        # Load Icon
        try:
            icon_path = resource_path('icon.png')
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                self.icon_img = ImageTk.PhotoImage(img)
                self.root.iconphoto(False, self.icon_img)
        except Exception as e:
            print(f"Icon load error: {e}")
        
        # Set a modern theme if available
        try:
            style = ttk.Style()
            style.theme_use('clam')
            # Custom Green Style for Progressbar
            style.configure("Green.Horizontal.TProgressbar", 
                            troughcolor='#e8f5e9', 
                            bordercolor='#2e7d32', 
                            background='#4caf50', 
                            lightcolor='#81c784', 
                            darkcolor='#2e7d32')
            
            # Style for Tabs (Modern Green look)
            style.configure("TNotebook", background='#f5f5f5', borderwidth=0)
            style.configure("TNotebook.Tab", padding=[20, 8], font=('Arial', 10), background='#e0e0e0', borderwidth=0, width=15, anchor="center")
            
            # Remove the dotted focus ring
            style.layout("TNotebook.Tab", [
                ('Notebook.tab', {
                    'sticky': 'nswe',
                    'children': [
                        ('Notebook.padding', {
                            'side': 'top',
                            'sticky': 'nswe',
                            'children': [
                                ('Notebook.label', {'sticky': 'nswe'})
                            ]
                        })
                    ]
                })
            ])

            style.map("TNotebook.Tab", 
                      background=[("selected", "#2e7d32"), ("active", "#c8e6c9")], 
                      foreground=[("selected", "white"), ("active", "black")],
                      font=[("selected", ('Arial', 10, 'bold'))],
                      padding=[("selected", [15, 6]), ("!selected", [15, 3])],
                      shift=[("selected", [0, 0])])
        except:
            pass

        tk.Label(root, text="Panta Rhei Image Converter", font=("Arial", 18, "bold"), fg="#2e7d32").pack(pady=10)
        
        # Tabs Setup
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.tab_converter = tk.Frame(self.notebook, bg='#f5f5f5')
        self.tab_about = tk.Frame(self.notebook, bg='#f5f5f5')
        
        self.notebook.add(self.tab_converter, text="Converter")
        self.notebook.add(self.tab_about, text="About")

        # --- CONVERTER TAB ---
        
        # Mode Selection
        mode_frame = tk.LabelFrame(self.tab_converter, text="Select Mode", padx=10, pady=5, bg='#f5f5f5')
        mode_frame.pack(padx=20, pady=5, fill="x")
        self.mode_var = tk.StringVar(value="batch")
        tk.Radiobutton(mode_frame, text="Batch Mode", variable=self.mode_var, value="batch", command=self.update_ui_mode, bg='#f5f5f5', activebackground='#f5f5f5').grid(row=0, column=0, padx=20)
        tk.Radiobutton(mode_frame, text="Auto-Convert", variable=self.mode_var, value="auto", command=self.update_ui_mode, bg='#f5f5f5', activebackground='#f5f5f5').grid(row=0, column=1, padx=20)

        # File/Folder Selection Frame
        self.selection_frame = tk.LabelFrame(self.tab_converter, text="1. Setup Paths", padx=15, pady=10, bg='#f5f5f5')
        self.selection_frame.pack(padx=20, pady=10, fill="x")

        self.btn_select_source = tk.Button(self.selection_frame, text="Select .prz Files", command=self.select_files, width=25)
        self.btn_select_source.pack(pady=5)
        self.lbl_files = tk.Label(self.selection_frame, text="No files selected", fg="gray", wraplength=400, bg='#f5f5f5')
        self.lbl_files.pack()

        tk.Button(self.selection_frame, text="Select Export Folder", command=self.select_folder, width=25).pack(pady=5)
        self.lbl_folder = tk.Label(self.selection_frame, text="No folder selected", fg="gray", wraplength=400, bg='#f5f5f5')
        self.lbl_folder.pack()

        # Settings Frame
        settings = tk.LabelFrame(self.tab_converter, text="2. Export Settings", padx=15, pady=10, bg='#f5f5f5')
        settings.pack(padx=20, pady=10, fill="x")

        tk.Label(settings, text="DPI:", bg='#f5f5f5').grid(row=0, column=0, sticky="w", pady=5)
        self.dpi_var = tk.StringVar(value="300")
        tk.Entry(settings, textvariable=self.dpi_var, width=10).grid(row=0, column=1, sticky="w")

        tk.Label(settings, text="Scalebar (nm):", bg='#f5f5f5').grid(row=1, column=0, sticky="w", pady=5)
        self.sb_var = tk.StringVar(value="50")
        self.sb_entry = tk.Entry(settings, textvariable=self.sb_var, width=10)
        self.sb_entry.grid(row=1, column=1, sticky="w")
        
        self.auto_sb_var = tk.BooleanVar(value=True)
        self.chk_auto_sb = tk.Checkbutton(settings, text="Auto", variable=self.auto_sb_var, command=self.toggle_sb_entry, bg='#f5f5f5', activebackground='#f5f5f5')
        self.chk_auto_sb.grid(row=1, column=2, sticky="w", padx=5)

        self.auto_contrast_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings, text="Auto Contrast (0.1% - 99.9%)", variable=self.auto_contrast_var, bg='#f5f5f5', activebackground='#f5f5f5').grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        self.toggle_sb_entry()

    def toggle_sb_entry(self):
        if self.auto_sb_var.get():
            self.sb_entry.config(state="disabled")
        else:
            self.sb_entry.config(state="normal")

        # Action Button
        self.btn_run = tk.Button(self.tab_converter, text="GENERATE IMAGES", bg="#2e7d32", fg="white", 
                                activebackground="#1b5e20", activeforeground="white",
                                font=("Arial", 12, "bold"), height=2, command=self.run_batch)
        self.btn_run.pack(pady=15, fill="x", padx=40)

        # Progress (Initially hidden)
        self.progress_frame = tk.Frame(self.tab_converter, bg='#f5f5f5')
        self.progress = ttk.Progressbar(self.progress_frame, orient="horizontal", length=400, 
                                        mode="determinate", style="Green.Horizontal.TProgressbar")
        self.progress.pack(pady=5, fill="x")
        self.lbl_status = tk.Label(self.progress_frame, text="Ready", fg="gray", bg='#f5f5f5')
        self.lbl_status.pack()

        # --- ABOUT TAB ---
        self.setup_about_tab()

        self.file_list = []
        self.export_folder = ""
        self.last_source_folder = ""
        self.is_watching = False
        self.seen_files = set()
        
        self.load_config()
        self.update_ui_mode()

    def setup_about_tab(self):
        desc = ("A professional TEM image conversion utility designed to "
                "streamline the process of exporting Panta Rhei (.prz) files "
                "for scientific publications.\n\n"
                "Developed to ensure consistency in scalebars, contrast, "
                "and image quality across large datasets.")
        
        tk.Label(self.tab_about, text="Panta Rhei Image Converter v1.0", font=("Arial", 14, "bold"), fg="#2e7d32", bg='#f5f5f5').pack(pady=20)
        tk.Label(self.tab_about, text=desc, wraplength=400, justify="center", font=("Arial", 10), bg='#f5f5f5').pack(pady=10, padx=20)
        
        tk.Label(self.tab_about, text="Follow, Edit, Change and Contribute here:", font=("Arial", 10, "bold"), bg='#f5f5f5').pack(pady=(20, 0))
        
        link = tk.Label(self.tab_about, text="Pronoy Dutta (GitHub)", fg="#0078d7", cursor="hand2", font=("Arial", 10, "underline"), bg='#f5f5f5')
        link.pack(pady=5)
        link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/PronoyDutta"))
        
        tk.Label(self.tab_about, text="© 2026 MIT License", fg="gray", font=("Arial", 8), bg='#f5f5f5').pack(side="bottom", pady=20)

    def update_ui_mode(self):
        if self.mode_var.get() == "batch":
            self.btn_select_source.config(text="Select .prz Files", command=self.select_files)
            self.btn_run.config(text="GENERATE IMAGES", bg="#2e7d32")
            self.selection_frame.config(text="1. Setup Paths (Batch)")
        else:
            self.btn_select_source.config(text="Select Watch Folder", command=self.select_watch_folder)
            self.btn_run.config(text="START AUTOCONVERT", bg="#2e7d32")
            self.selection_frame.config(text="1. Setup Paths (Live)")
            if self.last_source_folder:
                folder_name = os.path.basename(os.path.normpath(self.last_source_folder))
                self.lbl_files.config(text=f"Watching: {folder_name}", fg="black")

    def select_watch_folder(self):
        initial_dir = self.last_source_folder if os.path.exists(self.last_source_folder) else None
        folder = filedialog.askdirectory(initialdir=initial_dir)
        if folder:
            self.last_source_folder = folder
            self.lbl_files.config(text=f"Watching: {os.path.basename(folder)}", fg="black")
            self.save_config()

    def load_config(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    self.export_folder = config.get('export_folder', '')
                    self.last_source_folder = config.get('source_folder', '')
                    if self.export_folder and os.path.exists(self.export_folder):
                        self.lbl_folder.config(text=f"Saving to: {os.path.basename(self.export_folder)}", fg="black")
                    if self.last_source_folder and os.path.exists(self.last_source_folder):
                        folder_name = os.path.basename(os.path.normpath(self.last_source_folder))
                        self.lbl_files.config(text=f"Last folder: {folder_name}", fg="gray")
        except Exception as e:
            print(f"Error loading config: {e}")

    def save_config(self):
        try:
            config = {
                'export_folder': self.export_folder,
                'source_folder': self.last_source_folder
            }
            with open('config.json', 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def select_files(self):
        initial_dir = self.last_source_folder if os.path.exists(self.last_source_folder) else None
        files = filedialog.askopenfilenames(filetypes=[("Panta Rhei", "*.prz")], initialdir=initial_dir)
        if files:
            self.file_list = files
            self.last_source_folder = os.path.dirname(files[0])
            self.lbl_files.config(text=f"{len(files)} files selected", fg="black")
            self.save_config()

    def select_folder(self):
        initial_dir = self.export_folder if os.path.exists(self.export_folder) else None
        folder = filedialog.askdirectory(initialdir=initial_dir)
        if folder:
            self.export_folder = folder
            folder_name = os.path.basename(os.path.normpath(folder))
            self.lbl_folder.config(text=f"Saving to: {folder_name}", fg="black")
            self.save_config()

    def load_npy_from_zip(self, zip_file, filename):
        """Robustly load a .npy file or JSON from a zip archive."""
        with zip_file.open(filename) as f:
            content = f.read()
            # Try standard numpy load
            try:
                # Use io.BytesIO to make it a seekable file-like object
                return np.load(io.BytesIO(content), allow_pickle=True)
            except Exception as e:
                # Fallback: find JSON content if it's a metadata file wrapped in NPY
                if b'[' in content and b']' in content:
                    start = content.find(b'[')
                    end = content.rfind(b']') + 1
                    try:
                        return json.loads(content[start:end].decode('utf-8'))
                    except:
                        pass
                raise e

    def process_file(self, prz_path):
        with zipfile.ZipFile(prz_path, 'r') as prz:
            # 1. Metadata Handling
            namelist = prz.namelist()
            meta_name = 'meta_data_json.npy' if 'meta_data_json.npy' in namelist else 'metadata.json'
            
            if meta_name.endswith('.json'):
                with prz.open(meta_name) as f:
                    meta_json = json.load(f)
            else:
                meta_data = self.load_npy_from_zip(prz, meta_name)
                meta_json = meta_data

            # Robust unwrap: Handle nested lists, 0-d arrays, or JSON strings
            for _ in range(5):
                if isinstance(meta_json, np.ndarray):
                    if meta_json.ndim == 0:
                        meta_json = meta_json.item()
                    elif len(meta_json) > 0:
                        meta_json = meta_json[0]
                    else:
                        break
                elif isinstance(meta_json, list) and len(meta_json) > 0:
                    meta_json = meta_json[0]
                elif isinstance(meta_json, str):
                    try:
                        # If it's a JSON string inside the NPY
                        meta_json = json.loads(meta_json)
                    except:
                        break
                else:
                    break
            
            # Calibration (Panta Rhei stores this in meters)
            try:
                pixel_size_m = meta_json['device.calib'][0]['value']
            except (KeyError, IndexError):
                # Try alternative paths if structure differs
                pixel_size_m = meta_json.get('pixel_size', 1e-10) # Fallback

            # 2. Image Data Handling
            if 'data.npy' not in namelist:
                raise FileNotFoundError("Could not find 'data.npy' inside the .prz archive.")
                
            with prz.open('data.npy') as f:
                content = f.read()
                try:
                    image = np.load(io.BytesIO(content))
                except Exception:
                    # Robust fallback for corrupted headers or unusual formats
                    # Detect resolution by file size (assuming uint16 = 2 bytes per pixel)
                    file_size = len(content)
                    found = False
                    for res in [4096, 2048, 1024, 8192, 512]:
                        expected_data_size = res * res * 2
                        if file_size >= expected_data_size:
                            # Take the last chunk of bytes that matches the resolution
                            img_bytes = content[-expected_data_size:]
                            image = np.frombuffer(img_bytes, dtype='<u2').reshape(res, res)
                            found = True
                            break
                    if not found:
                        raise ValueError(f"Unknown image format. File size: {file_size} bytes")

        # 3. Processing
        if self.auto_contrast_var.get():
            vmin, vmax = np.percentile(image, [0.1, 99.9])
            image_adj = np.clip(image, vmin, vmax)
        else:
            image_adj = image

        # 4. Visualization
        height, width = image.shape
        # Create figure size proportional to image aspect ratio
        fig, ax = plt.subplots(figsize=(10, 10 * (height/width)))
        ax.imshow(image_adj, cmap='gray', interpolation='bicubic')
        ax.axis('off')

        # 5. Scalebar
        try:
            if self.auto_sb_var.get():
                # Calculate physical width in nm
                width_nm = width * pixel_size_m * 1e9
                # Aim for ~15-20% of image width
                target_sb = width_nm * 0.18
                # Find nearest nice number (1, 2, 5, 10, 20, 50, 100, 200, 500, ...)
                exponent = np.floor(np.log10(target_sb))
                base = 10**exponent
                nice_values = np.array([1, 2, 5, 10]) * base
                sb_nm = nice_values[np.argmin(np.abs(nice_values - target_sb))]
            else:
                sb_nm = float(self.sb_var.get())

            sb_px = (sb_nm * 1e-9) / pixel_size_m
            
            # Position parameters relative to image size
            pad = width * 0.03
            bar_height = height * 0.01
            
            # Add bar
            ax.add_patch(patches.Rectangle((pad, height - pad - bar_height), sb_px, bar_height, color='white', lw=0))
            
            # Standardize font size relative to figure size (10 inches)
            # 72 points per inch * 10 inches = 720 points total. 
            # A value of 26-28 is generally clear and consistent.
            fontsize = 26
            ax.text(pad + sb_px/2, height - pad - bar_height - (height * 0.01), 
                    f'{int(sb_nm)} nm', color='white', 
                    fontsize=fontsize, fontweight='bold', ha='center', va='bottom')
        except Exception as e:
            print(f"Warning: Could not add scalebar: {e}")

        # 6. Save
        base_name = os.path.splitext(os.path.basename(prz_path))[0]
        save_path = os.path.join(self.export_folder, f"{base_name}.png")
        
        plt.savefig(save_path, dpi=int(self.dpi_var.get()), bbox_inches='tight', pad_inches=0)
        plt.close(fig)

    def run_batch(self):
        if self.mode_var.get() == "auto":
            self.toggle_watch()
            return

        if not self.file_list or not self.export_folder:
            messagebox.showerror("Error", "Please select both files and an export folder.")
            return
            
        success_count = 0
        errors = []
        
        self.progress["maximum"] = len(self.file_list)
        self.progress["value"] = 0
        self.btn_run.config(state="disabled")
        self.progress_frame.pack(pady=10, padx=40, fill="x") # Show progress bar
        
        for i, f in enumerate(self.file_list):
            try:
                self.lbl_status.config(text=f"Processing {i+1}/{len(self.file_list)}: {os.path.basename(f)}", fg="black")
                self.root.update()
                
                self.process_file(f)
                success_count += 1
                
                self.progress["value"] = i + 1
            except Exception as e:
                errors.append(f"{os.path.basename(f)}: {str(e)}")
                print(traceback.format_exc())
        
        self.btn_run.config(state="normal")
        self.lbl_status.config(text="Done", fg="green")
        
        if errors:
            err_summary = "\n".join(errors[:5])
            if len(errors) > 5:
                err_summary += f"\n... and {len(errors)-5} more."
            messagebox.showerror("Completed with Errors", f"Successfully exported {success_count} images.\n\nErrors:\n{err_summary}")
        else:
            messagebox.showinfo("Success", f"All {success_count} images exported successfully!")

    def toggle_watch(self):
        if self.is_watching:
            self.is_watching = False
            self.btn_run.config(text="START WATCHING", bg="#2e7d32")
            self.lbl_status.config(text="Stopped watching", fg="gray")
        else:
            if not self.last_source_folder or not self.export_folder:
                messagebox.showerror("Error", "Please select both a watch folder and an export folder.")
                return
            self.is_watching = True
            # Initialize seen_files as empty to trigger a scan of all files on start
            self.seen_files = set() 
            self.btn_run.config(text="STOP WATCHING", bg="#d32f2f")
            self.lbl_status.config(text="Starting folder watch...", fg="#2e7d32")
            self.progress_frame.pack(pady=10, padx=40, fill="x")
            self.check_for_new_files()

    def check_for_new_files(self):
        if not self.is_watching:
            return

        try:
            # 1. Get current files (case-insensitive extension check)
            current_files = {f for f in os.listdir(self.last_source_folder) if f.lower().endswith(".prz")}
            new_files = current_files - self.seen_files
            
            if new_files:
                for f_name in sorted(new_files):
                    f_path = os.path.join(self.last_source_folder, f_name)
                    
                    # 2. Check if output already exists (Smart Scanning)
                    base_name = os.path.splitext(f_name)[0]
                    target_path = os.path.join(self.export_folder, f"{base_name}.png")
                    
                    if os.path.exists(target_path):
                        self.seen_files.add(f_name)
                        continue

                    self.lbl_status.config(text=f"Auto-converting: {f_name}", fg="#2e7d32")
                    self.root.update()
                    try:
                        self.process_file(f_path)
                        # Only mark as seen if successfully processed
                        self.seen_files.add(f_name)
                    except PermissionError:
                        # File is likely still being written by the microscope
                        print(f"File busy, skipping for now: {f_name}")
                        self.lbl_status.config(text=f"Waiting for microscope: {f_name}", fg="#f57c00")
                        self.root.update()
                    except Exception as e:
                        print(f"Error auto-converting {f_name}: {e}")
                        self.lbl_status.config(text=f"Error on {f_name}: {str(e)[:30]}...", fg="red")
                        self.root.update()
                        self.seen_files.add(f_name) # Don't retry if it's a real error
                        time.sleep(1)
            
            # 3. Update heartbeat/status
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.lbl_status.config(text=f"Watching... (Last check: {now})", fg="#2e7d32")
            
        except Exception as e:
            print(f"Watch error: {e}")
            self.lbl_status.config(text=f"Watch Error: {str(e)[:30]}", fg="red")
        
        self.root.after(10000, self.check_for_new_files) # Check every 10 seconds

if __name__ == "__main__":
    root = tk.Tk()
    app = PantaRheiExporter(root)
    root.mainloop()

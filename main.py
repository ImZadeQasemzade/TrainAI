import customtkinter as ctk
import cv2
from PIL import Image
import time
from pose_tracker import PoseTracker
from database import init_db, get_categories, get_workouts_by_category, get_all_workouts, save_workout_session, get_history, delete_history, add_workout, delete_workout

class WorkoutApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("AI Workout Tracker")
        self.geometry("900x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        init_db()
        self.tracker = PoseTracker()
        
        self.cap = None
        self.app_state = "idle"  # idle, in_set, resting
        self.is_paused = False
        self.start_time = None
        self.total_paused_time = 0
        self.pause_start_time = None
        self.rest_start_time = None
        
        self.setup_ui()
        
    def setup_ui(self):
        self.tabview = ctk.CTkTabview(self, text_color="white")
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.tab_tracker = self.tabview.add("Tracker")
        self.tab_history = self.tabview.add("History")
        self.tab_library = self.tabview.add("Manage Library")
        
        self.setup_tracker_tab()
        self.setup_history_tab()
        self.setup_library_tab()
        
        self.tabview.configure(command=self.on_tab_change)

    def on_tab_change(self):
        if self.tabview.get() == "History":
            self.load_history()
        elif self.tabview.get() == "Manage Library":
            self.load_library()

    def setup_tracker_tab(self):
        self.tab_tracker.grid_columnconfigure(0, weight=3)
        self.tab_tracker.grid_columnconfigure(1, weight=1)
        self.tab_tracker.grid_rowconfigure(0, weight=1)
        
        # Left Frame (Video)
        self.video_frame = ctk.CTkFrame(self.tab_tracker, corner_radius=10)
        self.video_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="Camera Feed Offline", font=("Inter", 24))
        self.video_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Right Frame (Controls)
        self.control_frame = ctk.CTkScrollableFrame(self.tab_tracker, corner_radius=10)
        self.control_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Filters
        filter_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        filter_frame.pack(pady=15, fill="x", padx=10)
        
        ctk.CTkLabel(filter_frame, text="Workout Category", font=("Inter", 14, "bold")).pack()
        cats = ["All"] + get_categories()
        self.cat_var = ctk.StringVar(value="All")
        self.cat_dropdown = ctk.CTkOptionMenu(filter_frame, variable=self.cat_var, values=cats, command=self.update_workout_dropdown)
        self.cat_dropdown.pack(pady=5, fill="x")
        
        ctk.CTkLabel(filter_frame, text="Select Exercise", font=("Inter", 14, "bold")).pack(pady=(10,0))
        self.workout_var = ctk.StringVar(value="Auto-Detect")
        self.workout_dropdown = ctk.CTkOptionMenu(filter_frame, variable=self.workout_var, values=["Auto-Detect"])
        self.workout_dropdown.pack(pady=5, fill="x")
        self.update_workout_dropdown(None)
        
        self.detected_label = ctk.CTkLabel(self.control_frame, text="AI Detected: None", font=("Inter", 14), text_color="#f39c12")
        self.detected_label.pack(pady=5)
        
        # Dash / Timer
        dash_frame = ctk.CTkFrame(self.control_frame, corner_radius=10, fg_color="#1e272e")
        dash_frame.pack(pady=15, fill="x", padx=10)
        
        self.time_label = ctk.CTkLabel(dash_frame, text="00:00", font=("Inter", 42, "bold"), text_color="#00d2d3")
        self.time_label.pack(pady=15)
        
        self.reps_frame = ctk.CTkFrame(dash_frame, fg_color="transparent")
        self.reps_frame.pack(pady=10, fill="x", padx=10)
        
        self.l_rep_label = ctk.CTkLabel(self.reps_frame, text="L: 0", font=("Inter", 28, "bold"))
        self.l_rep_label.pack(side="left", padx=20)
        
        self.r_rep_label = ctk.CTkLabel(self.reps_frame, text="R: 0", font=("Inter", 28, "bold"))
        self.r_rep_label.pack(side="right", padx=20)
        
        # Buttons
        self.start_btn = ctk.CTkButton(self.control_frame, text="Start Set", font=("Inter", 16, "bold"), height=40, fg_color="#10ac84", hover_color="#1dd1a1", command=self.start_set)
        self.start_btn.pack(pady=10, fill="x", padx=20)
        
        self.pause_btn = ctk.CTkButton(self.control_frame, text="Pause", font=("Inter", 14), state="disabled", command=self.pause_workout)
        self.pause_btn.pack(pady=5, fill="x", padx=20)
        
        self.finish_btn = ctk.CTkButton(self.control_frame, text="Finish Set", font=("Inter", 16, "bold"), height=40, fg_color="#ff9f43", hover_color="#feca57", state="disabled", command=self.finish_set)
        self.finish_btn.pack(pady=10, fill="x", padx=20)
        
        self.end_session_btn = ctk.CTkButton(self.control_frame, text="End Session", font=("Inter", 14, "bold"), fg_color="#ee5253", hover_color="#ff6b6b", command=self.end_session)
        self.end_session_btn.pack(pady=(30, 10), fill="x", padx=20)

    def setup_history_tab(self):
        self.history_scroll = ctk.CTkScrollableFrame(self.tab_history)
        self.history_scroll.pack(expand=True, fill="both", padx=20, pady=20)
        
    def load_history(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
            
        history = get_history()
        if not history:
            ctk.CTkLabel(self.history_scroll, text="No workout history found.", font=("Inter", 16)).pack(pady=20)
            return
            
        for idx, row in enumerate(history):
            record_id, date, name, dur, l, r = row[0], row[1], row[2], row[3], row[4], row[5]
            mins, secs = divmod(dur, 60)
            
            row_frame = ctk.CTkFrame(self.history_scroll, corner_radius=5)
            row_frame.pack(fill="x", pady=5, padx=5)
            
            info = ctk.CTkLabel(row_frame, text=f"{date}  •  {name}", font=("Inter", 14, "bold"))
            info.pack(side="left", padx=15, pady=10)
            
            stats = ctk.CTkLabel(row_frame, text=f"⏱ {mins}m {secs}s   |   💪 L:{l}  R:{r}", font=("Inter", 14))
            stats.pack(side="left", padx=20)
            
            del_btn = ctk.CTkButton(row_frame, text="Delete", width=60, fg_color="#ee5253", hover_color="#ff6b6b", command=lambda rid=record_id: (delete_history(rid), self.load_history()))
            del_btn.pack(side="right", padx=15)

    def setup_library_tab(self):
        self.tab_library.grid_columnconfigure(0, weight=1)
        self.tab_library.grid_columnconfigure(1, weight=2)
        self.tab_library.grid_rowconfigure(0, weight=1)
        
        # Add form
        add_frame = ctk.CTkFrame(self.tab_library, corner_radius=10)
        add_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(add_frame, text="Add Custom Exercise", font=("Inter", 18, "bold")).pack(pady=20)
        self.name_entry = ctk.CTkEntry(add_frame, placeholder_text="Exercise Name", width=200)
        self.name_entry.pack(pady=10)
        
        ctk.CTkLabel(add_frame, text="Primary Joint").pack()
        self.joint_var = ctk.StringVar(value="elbow")
        ctk.CTkOptionMenu(add_frame, variable=self.joint_var, values=["elbow", "shoulder", "knee", "hip", "ankle", "core"], width=200).pack(pady=5)
        
        ctk.CTkLabel(add_frame, text="Category").pack(pady=(10,0))
        self.new_cat_var = ctk.StringVar(value="Custom")
        ctk.CTkEntry(add_frame, textvariable=self.new_cat_var, width=200).pack(pady=5)
        
        ctk.CTkButton(add_frame, text="Add to Library", fg_color="#10ac84", hover_color="#1dd1a1", command=self.on_add_workout).pack(pady=20)
        
        # List
        self.library_scroll = ctk.CTkScrollableFrame(self.tab_library)
        self.library_scroll.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
    def load_library(self):
        for w in self.library_scroll.winfo_children():
            w.destroy()
            
        workouts = get_all_workouts()
        
        # Group by category visually
        cats = get_categories()
        for cat in cats:
            lbl = ctk.CTkLabel(self.library_scroll, text=cat, font=("Inter", 16, "bold"), text_color="#00d2d3")
            lbl.pack(anchor="w", pady=(15, 5), padx=10)
            
            cat_workouts = [w for w in workouts if w[2] == cat] if len(workouts[0])>2 else get_workouts_by_category(cat)
            
            for w in cat_workouts:
                w_name = w[0]
                row_f = ctk.CTkFrame(self.library_scroll, fg_color="transparent")
                row_f.pack(fill="x", pady=2, padx=15)
                
                ctk.CTkLabel(row_f, text=f"• {w_name} (Joint: {w[1]})", font=("Inter", 14)).pack(side="left")
                ctk.CTkButton(row_f, text="X", width=30, fg_color="#ee5253", hover_color="#ff6b6b", command=lambda wn=w_name: (delete_workout(wn), self.load_library())).pack(side="right")
                
    def on_add_workout(self):
        name = self.name_entry.get().strip()
        cat = self.new_cat_var.get().strip()
        if name and cat:
            add_workout(name, self.joint_var.get(), cat)
            self.name_entry.delete(0, 'end')
            self.load_library()
            # update category dropdown in tracker tab
            cats = ["All"] + get_categories()
            self.cat_dropdown.configure(values=cats)
            self.update_workout_dropdown(None)

    def update_workout_dropdown(self, _):
        cat = self.cat_var.get()
        if cat == "All":
            workouts = ["Auto-Detect"] + [w[0] for w in get_all_workouts()]
        else:
            workouts = ["Auto-Detect"] + [w[0] for w in get_workouts_by_category(cat)]
        self.workout_dropdown.configure(values=workouts)
        self.workout_var.set("Auto-Detect")

    def start_set(self):
        self.app_state = "in_set"
        self.is_paused = False
        self.start_time = time.time()
        self.total_paused_time = 0
        self.tracker.reset_counters()
        
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
            self.update_frame()
            
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal", text="Pause")
        self.finish_btn.configure(state="normal")
        self.time_label.configure(text_color="#10ac84") # Green for running
        
        self.update_timer()
            
    def pause_workout(self):
        if not self.is_paused:
            self.is_paused = True
            self.pause_start_time = time.time()
            self.pause_btn.configure(text="Resume")
            self.time_label.configure(text_color="#f39c12") # Orange for paused
        else:
            self.is_paused = False
            self.total_paused_time += time.time() - self.pause_start_time
            self.pause_btn.configure(text="Pause")
            self.time_label.configure(text_color="#10ac84")
            self.update_timer()

    def finish_set(self):
        if self.app_state != "in_set": return
        self.app_state = "resting"
        
        end_time = time.time()
        if self.is_paused:
            self.total_paused_time += end_time - self.pause_start_time
        duration = int(end_time - self.start_time - self.total_paused_time)
            
        workout_name = self.workout_var.get()
        if workout_name == "Auto-Detect":
            workout_name = self.tracker.detected_workout
            if workout_name == "Unknown" or workout_name == "Auto-Detecting...":
                workout_name = "Unspecified Workout"
                
        save_workout_session(workout_name, duration, self.tracker.reps_left, self.tracker.reps_right)
        
        self.rest_start_time = time.time()
        
        self.start_btn.configure(state="normal", text="Start Next Set")
        self.pause_btn.configure(state="disabled")
        self.finish_btn.configure(state="disabled")
        self.time_label.configure(text_color="#ff9f43") # Orange for resting
        
        self.update_timer()

    def end_session(self):
        self.app_state = "idle"
        if self.cap:
            self.cap.release()
            self.cap = None
            
        self.start_btn.configure(state="normal", text="Start Set")
        self.pause_btn.configure(state="disabled", text="Pause")
        self.finish_btn.configure(state="disabled", text="Finish Set")
        
        self.video_label.configure(image=None, text="Camera Feed Offline")
        self.l_rep_label.configure(text="L: 0")
        self.r_rep_label.configure(text="R: 0")
        self.time_label.configure(text="00:00", text_color="#00d2d3")
        self.detected_label.configure(text="AI Detected: None")

    def update_frame(self):
        if self.app_state in ["in_set", "resting"] and not self.is_paused and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Do NOT flip here. Process raw frame so Left/Right in MediaPipe are accurate.
                workout_param = self.workout_var.get() if self.app_state == "in_set" else "Resting"
                processed_frame, detected, reps_l, reps_r = self.tracker.process_frame(frame, workout_param)
                
                # Flip the PROCESSED frame here so it acts like a mirror on screen
                processed_frame = cv2.flip(processed_frame, 1)
                
                # Update UI
                if self.app_state == "in_set":
                    if self.workout_var.get() == "Auto-Detect":
                        self.detected_label.configure(text=f"AI Detected: {detected}")
                    else:
                        self.detected_label.configure(text=f"Manual: {self.workout_var.get()}")
                        
                    self.l_rep_label.configure(text=f"L: {reps_l}")
                    self.r_rep_label.configure(text=f"R: {reps_r}")
                elif self.app_state == "resting":
                    self.detected_label.configure(text="Resting... (AI Paused)")
                
                rgb_image = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_image)
                ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(550, 410))
                
                self.video_label.configure(image=ctk_image, text="")
                
            self.after(30, self.update_frame)
            
    def update_timer(self):
        if not self.is_paused:
            if self.app_state == "in_set":
                elapsed = int(time.time() - self.start_time - self.total_paused_time)
                mins, secs = divmod(elapsed, 60)
                self.time_label.configure(text=f"{mins:02d}:{secs:02d}")
                self.after(1000, self.update_timer)
            elif self.app_state == "resting":
                elapsed = int(time.time() - self.rest_start_time)
                mins, secs = divmod(elapsed, 60)
                self.time_label.configure(text=f"Rest {mins:02d}:{secs:02d}")
                self.after(1000, self.update_timer)

if __name__ == "__main__":
    app = WorkoutApp()
    app.mainloop()

# AI Workout Assistant 🏋️‍♂️🤖

An AI-powered workout tracker that uses computer vision to track your exercises in real-time. Built with Python, OpenCV, and Google's MediaPipe, this application counts your reps, tracks your form, and logs your workout history. 

It is designed to be cross-platform and includes native support for the Raspberry Pi Camera Module on the latest Raspberry Pi OS (Bookworm) using `picamera2`!

## ✨ Features
* **Real-Time Pose Estimation:** Uses MediaPipe to track 33 body landmarks.
* **Auto-Detect Workouts:** The AI automatically detects what exercise you are doing based on your joint movements.
* **Rep Counting:** Tracks left and right side repetitions independently.
* **Workout History:** Logs duration, exercise type, and rep counts to a local SQLite database.
* **Custom Exercises:** Add your own exercises by defining the primary joint involved.
* **Raspberry Pi Optimized:** Includes a custom `picamera2` fallback to completely bypass OpenCV V4L2 limitations on the newest Raspberry Pi OS.

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/ImZadeQasemzade/TrainAI.git
cd TrainAI
```

### 2. Standard Installation (Windows / Mac / Linux Desktop)
If you are using a standard USB webcam:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 3. Raspberry Pi Installation (Bookworm OS)
If you are using a Raspberry Pi with the official Pi Camera module, you must link to the system's native camera libraries.
```bash
# Install the system opencv package
sudo apt update
sudo apt install python3-opencv

# Create a virtual environment linked to system packages
python3 -m venv venv --system-site-packages
source venv/bin/activate

# Install dependencies (do NOT install opencv-python via pip)
pip install mediapipe==0.10.14 customtkinter "numpy<2"

# Run the app
python main.py
```

## 🛠️ Tech Stack
* **UI:** CustomTkinter
* **Computer Vision:** OpenCV
* **Pose Tracking:** MediaPipe
* **Database:** SQLite3
* **Hardware Interfacing (Pi):** picamera2

import cv2
import numpy as np
import time
import datetime
import json
import threading
import os
import csv
import random
import base64
from collections import deque
from winsound import Beep 

# Try to import pyttsx3 for Text-to-Speech.
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("Warning: 'pyttsx3' not found. Voice features will be text-only logs.")

# Try to import speech_recognition for Voice Commands.
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("Warning: 'speech_recognition' not found. Driver cannot talk back.")

# --- IoT Simulation Configuration ---
DEVICE_ID = "EYE_MONITOR_01"
LOCATION = "Vehicle_Cabin_A"
IOT_ENDPOINT = "wss://mock-iot-broker.cloud/mqtt"
LOG_FILE = "device_telemetry_log.csv"
EVIDENCE_DIR = "forensic_evidence"

if not os.path.exists(EVIDENCE_DIR):
    os.makedirs(EVIDENCE_DIR)

class DriverVoiceAssistant:
    """
    The 'Chatbot' for the car (Output).
    Uses Text-to-Speech to communicate context-aware warnings.
    """
    def __init__(self):
        self.engine = None
        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 150) # Speaking speed
                voices = self.engine.getProperty('voices')
                if len(voices) > 1:
                    self.engine.setProperty('voice', voices[1].id)
            except Exception as e:
                print(f"TTS Init Failed: {e}")
        
        self.last_speech_time = 0
        self.last_warning_time = 0 # Throttles critical alerts
        self.lock = threading.Lock()

    def speak(self, text, priority=False):
        # Don't spam the driver. Minimum 5 seconds between non-priority messages.
        if not priority and (time.time() - self.last_speech_time < 5):
            return

        print(f"\n[ASSISTANT] 🗣️ '{text}'")
        self.last_speech_time = time.time()

        if self.engine:
            threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        with self.lock:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except:
                pass

    def warn_drowsy(self, speed):
        # Prevent "Driver you are drifting off" spam.
        # Only speak critical warnings max once every 5 seconds.
        if time.time() - self.last_warning_time < 5:
            return

        self.last_warning_time = time.time()

        if speed > 60:
            self.speak(f"Danger! High speed detected. Wake up immediately!", priority=True)
        elif speed > 10:
            self.speak("Driver, you are drifting off. Please pull over.", priority=True)
        else:
            self.speak("Wake up. You are falling asleep.", priority=True)

    def suggest_break(self):
        phrases = [
            "I detect fatigue patterns. Consider a coffee break.",
            "You have been zoning out. Time to stretch.",
            "Driving performance is degrading. Please rest."
        ]
        self.speak(random.choice(phrases))

    def chat_environment(self, condition):
        if condition == "NIGHT":
            self.speak("It is getting dark. I am activating night vision monitoring.")
        elif condition == "GLARE":
            self.speak("Sun glare detected. Please use your visor.")

class DriverVoiceListener:
    """
    The 'Ears' of the car (Input).
    Listens for voice commands in a background thread.
    """
    def __init__(self, detector_ref):
        self.detector = detector_ref
        self.recognizer = None
        self.microphone = None
        self.stop_listening = None
        
        if SR_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 4000 # Adjust for background noise
                self.microphone = sr.Microphone()
            except Exception as e:
                print(f"Mic Init Failed: {e}")

    def start(self):
        if not SR_AVAILABLE or not self.microphone: return

        print("[LISTENER] Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        
        # listening in background using a non-blocking thread
        self.stop_listening = self.recognizer.listen_in_background(self.microphone, self.callback)
        print("[LISTENER] Voice Command System Active. Waiting for commands...")

    def callback(self, recognizer, audio):
        try:
            # Using google speech recognition (requires internet)
            # For offline use: recognizer.recognize_sphinx(audio)
            command = recognizer.recognize_google(audio).lower()
            print(f"[DRIVER] 🗣️ Said: '{command}'")
            self.process_command(command)
        except sr.UnknownValueError:
            pass # Speech was unintelligible
        except sr.RequestError:
            print("[LISTENER] Speech Service Unavailable")
        except Exception as e:
            pass

    def process_command(self, text):
        # 0. SOS Confirmation Logic
        if self.detector.sos_verification_pending:
            if any(w in text for w in ["confirm", "yes", "send", "do it", "help"]):
                self.detector.trigger_sos_manual("Voice Verification")
                return
            elif any(w in text for w in ["cancel", "no", "stop", "abort", "false"]):
                self.detector.cancel_sos()
                return

        # 1. False Alarm / Reset
        if "awake" in text or "false alarm" in text or "i am okay" in text:
            self.detector.reset_alert_state("Voice Command")
            self.detector.voice.speak("Understood. Reseting alert.", priority=True)
        
        # 2. Status Report
        elif "status" in text or "report" in text:
            spd = self.detector.vehicle.speed
            fatigue = self.detector.score
            self.detector.voice.speak(f"Current speed {spd} kilometers per hour. Fatigue level {fatigue}.", priority=True)
        
        # 3. Emergency (Direct command always overrides verification)
        elif "sos" in text or "emergency" in text:
            self.detector.trigger_sos_manual("Direct Voice Command")


class IoTClient:
    """
    Simulates a robust network client with Store-and-Forward capabilities.
    """
    def __init__(self, device_id, detector_ref):
        self.device_id = device_id
        self.connected = False
        self.detector_ref = detector_ref 
        self.lock = threading.Lock()
        self.offline_buffer = deque(maxlen=100) 
        threading.Thread(target=self._network_manager_loop, daemon=True).start()

    def _network_manager_loop(self):
        while True:
            # Simulate Random Network Dropouts
            if random.random() < 0.05: 
                self.connected = not self.connected
            
            # Flush Buffer if Online
            if self.connected and len(self.offline_buffer) > 0:
                with self.lock:
                    while len(self.offline_buffer) > 0:
                        self.offline_buffer.popleft()
                        time.sleep(0.05) 
            
            # Simulate Cloud Commands
            if self.connected and random.random() < 0.02:
                pass 

            time.sleep(1)

    def publish_telemetry(self, event_type, payload):
        message = {
            "device_id": self.device_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "event": event_type,
            "data": payload
        }
        with self.lock:
            if not self.connected:
                self.offline_buffer.append(message)
    
    def upload_evidence(self, filename):
        threading.Thread(target=self._mock_file_upload, args=(filename,)).start()

    def _mock_file_upload(self, filename):
        time.sleep(3) 
        print(f"[FORENSICS] Upload Complete: {filename} archived in cloud.")


class BlackBoxRecorder:
    """Forensic Event Data Recorder."""
    def __init__(self, buffer_seconds=5, fps=10):
        self.buffer_len = buffer_seconds * fps
        self.frame_buffer = deque(maxlen=self.buffer_len)
        self.is_recording = False
        self.post_trigger_frames = 0
        self.target_post_frames = buffer_seconds * fps
        self.writer = None
        self.lock = threading.Lock()

    def add_frame(self, frame):
        if self.is_recording:
            if self.writer:
                self.writer.write(frame)
                self.post_trigger_frames += 1
                if self.post_trigger_frames >= self.target_post_frames:
                    self.stop_recording()
        else:
            with self.lock:
                self.frame_buffer.append(frame.copy())

    def trigger_incident_save(self, frame_size):
        if self.is_recording: return 
        self.is_recording = True
        self.post_trigger_frames = 0
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_filename = f"{EVIDENCE_DIR}/incident_{timestamp}.avi"
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.writer = cv2.VideoWriter(self.current_filename, fourcc, 10.0, frame_size)

        with self.lock:
            for saved_frame in self.frame_buffer:
                self.writer.write(saved_frame)
            self.frame_buffer.clear()
        
        print(f"\n[BLACK-BOX] INCIDENT TRIGGERED! Recording evidence to {self.current_filename}")
        return self.current_filename

    def stop_recording(self):
        if self.writer:
            self.writer.release()
            print(f"[BLACK-BOX] Evidence Saved.")
            self.writer = None
        self.is_recording = False
        return self.current_filename

class VehicleTelemetry:
    """Simulates CAN Bus Speed."""
    def __init__(self):
        self.speed = 0 
        self.target_speed = 60
        self.last_update = time.time()
        
    def update(self):
        if time.time() - self.last_update > 0.5:
            if random.random() < 0.1:
                self.target_speed = random.randint(0, 120)
            if self.speed < self.target_speed:
                self.speed += random.randint(1, 5)
            elif self.speed > self.target_speed:
                self.speed -= random.randint(1, 5)
            self.last_update = time.time()
        return self.speed

class DrowsinessDetector:
    def __init__(self):
        self.iot = IoTClient(DEVICE_ID, self)
        self.vehicle = VehicleTelemetry()
        self.voice = DriverVoiceAssistant() 
        self.listener = DriverVoiceListener(self) # NEW: Voice Listener
        self.cap = cv2.VideoCapture(0)
        self.init_log_file()
        self.black_box = BlackBoxRecorder(buffer_seconds=5, fps=10)
        
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        self.score = 0
        self.threshold = 15
        self.font = cv2.FONT_HERSHEY_COMPLEX_SMALL
        self.last_heartbeat = time.time()
        
        self.blink_timestamps = deque(maxlen=10) 
        self.fatigue_history = deque(maxlen=100) 
        self.max_score_in_closure = 0 
        self.eyes_previously_closed = False
        self.last_evidence_time = 0
        self.last_advisory_time = 0
        self.current_env = "DAY"
        self.sos_verification_pending = False # Prevents spamming

    def init_log_file(self):
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Timestamp", "Device_ID", "Event", "Score", "Speed"])

    def log_locally(self, event, score, speed):
        try:
            with open(LOG_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([datetime.datetime.now().isoformat(), DEVICE_ID, event, score, speed])
        except Exception:
            pass

    def update_threshold(self, new_val):
        self.threshold = new_val

    def play_alarm(self):
        try:
            Beep(2500, 200) 
        except:
            print("\a")
            
    def check_blink_patterns(self):
        if len(self.blink_timestamps) < 4: return
        times = list(self.blink_timestamps)[-4:]
        if times[-1] - times[0] < 2.5:
            if not self.sos_verification_pending:
                print("\n*** RAPID BLINK DETECTED: REQUESTING CONFIRMATION ***")
                self.request_sos_confirmation()
            self.blink_timestamps.clear() 

    def request_sos_confirmation(self):
        self.sos_verification_pending = True
        self.voice.speak("SOS sequence detected. Say Confirm to send help, or Cancel to abort.", priority=True)

    def trigger_sos_manual(self, method):
        self.sos_verification_pending = False
        self.voice.speak("SOS Signal Confirmed. Sending Emergency Alert.", priority=True)
        self.iot.publish_telemetry("DRIVER_SIGNAL", {"type": "SOS", "method": method})

    def cancel_sos(self):
        self.sos_verification_pending = False
        self.voice.speak("SOS Request Cancelled.", priority=True)

    def reset_alert_state(self, source):
        self.score = 0
        self.iot.publish_telemetry("STATUS_RESET", {"source": source})

    def analyze_environment(self, gray_frame):
        avg_brightness = np.mean(gray_frame)
        status = "DAY"
        if avg_brightness < 50: status = "NIGHT"
        elif avg_brightness > 200: status = "GLARE"
        
        # Voice Trigger for Environment Change
        if status != self.current_env:
             self.voice.chat_environment(status)
             self.current_env = status
             
        return avg_brightness, status

    def run(self):
        if not self.cap.isOpened():
            print("Error: Webcam not found.")
            return

        self.listener.start() # Start listening in background
        self.voice.speak("System Online. Voice Commands Active.")
        print(f"System Active. CAN Bus Link Established.")

        while True:
            ret, frame = self.cap.read()
            if not ret: break

            height, width = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            current_speed = self.vehicle.update()
            
            # ADAPTIVE THRESHOLD LOGIC
            if current_speed < 5:
                self.threshold = 999 # Parked
                drive_mode = "PARKED"
            elif current_speed > 80:
                self.threshold = 10 # Highway
                drive_mode = "HIGHWAY"
            else:
                self.threshold = 20 # City
                drive_mode = "CITY"
            
            luminance, env_status = self.analyze_environment(gray)
            self.black_box.add_frame(frame)
            faces = self.face_cascade.detectMultiScale(gray, minNeighbors=5, scaleFactor=1.1, minSize=(25,25))
            
            cv2.rectangle(frame, (0,height-60), (width,height), (0,0,0), -1) 
            cv2.rectangle(frame, (0,0), (width, 40), (0,0,0), -1)
            
            if time.time() - self.last_heartbeat > 10:
                self.iot.publish_telemetry("HEARTBEAT", {
                    "status": "ok", 
                    "speed": current_speed,
                    "mode": drive_mode
                })
                self.last_heartbeat = time.time()

            face_detected = False
            eyes_detected = False

            for (x, y, w, h) in faces:
                face_detected = True
                cv2.rectangle(frame, (x, y), (x+w, y+h), (100, 100, 100), 1)
                roi_gray = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(roi_gray, minNeighbors=10)
                for (ex, ey, ew, eh) in eyes:
                    eyes_detected = True
                    cv2.rectangle(frame[y:y+h, x:x+w], (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)

            # Scoring Logic
            if face_detected:
                if not eyes_detected:
                    self.score += 1
                    self.max_score_in_closure = max(self.max_score_in_closure, self.score)
                    self.eyes_previously_closed = True
                    cv2.putText(frame, "EYES CLOSED", (10, height-20), self.font, 1, (0, 0, 255), 2)
                else:
                    if self.eyes_previously_closed:
                        if 2 <= self.max_score_in_closure <= 12:
                            self.blink_timestamps.append(time.time())
                            self.check_blink_patterns()
                        self.eyes_previously_closed = False
                        self.max_score_in_closure = 0
                    self.score -= 1
                    cv2.putText(frame, "DRIVER ACTIVE", (10, height-20), self.font, 1, (0, 255, 0), 2)
            else:
                self.score = 0
                cv2.putText(frame, "NO DRIVER", (10, height-20), self.font, 1, (255, 255, 255), 2)

            if self.score < 0: self.score = 0
            
            # Predictive Analytics
            self.fatigue_history.append(self.score)
            avg_fatigue = sum(self.fatigue_history) / len(self.fatigue_history) if self.fatigue_history else 0
            
            # Display Dashboard Data
            cv2.putText(frame, f"SPD: {current_speed} km/h", (10, 30), self.font, 1, (0, 255, 255), 2)
            cv2.putText(frame, f"MODE: {drive_mode}", (width-200, 30), self.font, 1, (200, 200, 200), 1)
            
            color = (0, 255, 0)
            if self.score > self.threshold * 0.5: color = (0, 165, 255)
            if self.score > self.threshold: color = (0, 0, 255)
            
            limit_text = "INF" if self.threshold == 999 else str(self.threshold)
            cv2.putText(frame, f'FATIGUE: {self.score} / {limit_text}', (width-250, height-20), self.font, 1, color, 1)

            # --- CHATBOT LOGIC ---
            # 1. Predictive "Take a Break" Chat
            if avg_fatigue > 5 and current_speed > 30:
                cv2.putText(frame, "ADVISORY: TAKE A BREAK", (width//2 - 150, height//2), self.font, 1.2, (0, 255, 255), 2)
                if time.time() - self.last_advisory_time > 60: # Chat only once every minute
                    self.voice.suggest_break()
                    self.last_advisory_time = time.time()

            # 2. Critical Alert Chat
            if self.score > self.threshold and drive_mode != "PARKED":
                cv2.rectangle(frame, (0,0), (width, height), (0,0,255), 10) 
                
                # Speak Alert
                if self.score % 10 == 0: # Don't speak every single frame
                    self.voice.warn_drowsy(current_speed)

                if time.time() - self.last_evidence_time > 30:
                    filename = self.black_box.trigger_incident_save((width, height))
                    self.iot.publish_telemetry("EVIDENCE_CREATED", {"filename": filename, "speed": current_speed})
                    self.iot.upload_evidence(filename)
                    self.last_evidence_time = time.time()
                
                if self.score % 5 == 0:
                    threading.Thread(target=self.play_alarm).start()
                    self.iot.publish_telemetry("ALERT", {"score": self.score, "speed": current_speed})
                    self.log_locally("ALERT", self.score, current_speed)
            
            # Show Verification Pending on UI
            if self.sos_verification_pending:
                 cv2.putText(frame, "SAY 'CONFIRM' TO SEND SOS", (width//2 - 200, height//2 + 50), self.font, 1.2, (0, 0, 255), 2)

            cv2.imshow('IoT Advanced Safety System', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = DrowsinessDetector()
    detector.run()
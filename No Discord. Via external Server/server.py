import socket
import threading
import cv2
import numpy as np
import struct
import pickle
import mouse
import keyboard

VIDEO_PORT = 5001
INPUT_PORT = 5002
FPS = 30

# ================= VIDEO SOCKET =================
video_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
video_server.bind(("0.0.0.0", VIDEO_PORT))
video_server.listen(1)
print(f"[SERVER] Warte auf Video-Verbindung (Port {VIDEO_PORT})...")
video_conn, video_addr = video_server.accept()
print(f"[SERVER] Video verbunden: {video_addr}")

# ================= INPUT SOCKET =================
input_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
input_server.bind(("0.0.0.0", INPUT_PORT))
input_server.listen(1)
input_conn, input_addr = input_server.accept()
print(f"[SERVER] Input verbunden: {input_addr}")

# ================= VIDEO WRITER =================
screen_width, screen_height = 1920, 1080  # passe ggf. an VM-Auflösung an
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter("vm_remote_record.mp4", fourcc, FPS, (screen_width, screen_height))

# ================= INPUT THREAD =================
def input_loop():
    while True:
        try:
            data = input_conn.recv(4096)
            if not data:
                break
            cmd = pickle.loads(data)
            if cmd["type"] == "move":
                mouse.move(cmd["x"], cmd["y"])
            elif cmd["type"] == "click":
                # klick ausführen
                mouse.press(cmd["button"])
                mouse.release(cmd["button"])
            elif cmd["type"] == "scroll":
                mouse.wheel(cmd["amount"])
            elif cmd["type"] == "key":
                keyboard.press(cmd["key"])
                keyboard.release(cmd["key"])
        except:
            break

threading.Thread(target=input_loop, daemon=True).start()

# ================= VIDEO ANZEIGE (Haupt-Thread!) =================
data_buffer = b""
payload_size = struct.calcsize(">I")

cv2.namedWindow("Remote VM", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Remote VM", 1280, 720)

try:
    while True:
        # Frame-Größe empfangen
        while len(data_buffer) < payload_size:
            data_buffer += video_conn.recv(4096)
        packed_size = data_buffer[:payload_size]
        data_buffer = data_buffer[payload_size:]
        frame_size = struct.unpack(">I", packed_size)[0]

        # Frame empfangen
        while len(data_buffer) < frame_size:
            data_buffer += video_conn.recv(4096)
        frame_data = data_buffer[:frame_size]
        data_buffer = data_buffer[frame_size:]

        # Frame dekodieren
        frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)

        # Cursor einzeichnen
        mx, my = mouse.get_position()
        cv2.drawMarker(frame, (mx, my), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)

        # Frame anzeigen
        cv2.imshow("Remote VM", frame)

        # Frame in Video speichern
        out.write(frame)

        # ESC zum Beenden
        if cv2.waitKey(1) & 0xFF == 27:
            break

finally:
    video_conn.close()
    input_conn.close()
    out.release()
    cv2.destroyAllWindows()
    print("[SERVER] Beendet, Video gespeichert als vm_remote_record.mp4")

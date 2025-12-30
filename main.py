import cv2
import numpy as np
import os
from email.message import EmailMessage
import smtplib
from skimage.metrics import structural_similarity as ssim

# === 📧 Email Setup ===
from_email = "jakkulasindhu52@gmail.com"       # Replace with your Gmail
from_password = "sehq kuhg jfpl abcd"       # Replace with your App Password
to_email = from_email                     # Sends alert to the same owner email

# === 📂 File Setup ===
reference_filename = "Reference.jpg"      # Reference image of account holder
attempts_file = "failed_attempts.txt"
correct_password = "1234"                 # Change if needed

# === 🧠 Face Detection Setup ===
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def extract_face(gray_img):
    faces = face_cascade.detectMultiScale(gray_img, 1.3, 5)
    for (x, y, w, h) in faces:
        return gray_img[y:y + h, x:x + w]
    return None

# === 1️⃣ Load Reference Image ===
ref_img = cv2.imread(reference_filename)
ref_gray = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
ref_face = extract_face(ref_gray)

if ref_face is None:
    print("❌ Could not detect face in Reference Image. Try a clearer image.")
    exit()

# === 2️⃣ Capture Live Login Image via Webcam ===
cap = cv2.VideoCapture(0)
print("📸 Webcam open. Press 'c' to capture your login image.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to capture frame.")
        continue

    cv2.imshow("Login - Press 'c' to capture, 'q' to quit", frame)
    key = cv2.waitKey(1)
    if key == ord('c'):
        login_img = frame.copy()
        cv2.imwrite("login_capture.jpg", login_img)
        print("✅ Login image captured and saved as login_capture.jpg")
        break
    elif key == ord('q'):
        print("❌ Login cancelled.")
        cap.release()
        cv2.destroyAllWindows()
        exit()

cap.release()
cv2.destroyAllWindows()

# === 3️⃣ Face Detection & Similarity ===
login_gray = cv2.cvtColor(login_img, cv2.COLOR_BGR2GRAY)
login_face = extract_face(login_gray)

if ref_face is not None and login_face is not None:
    ref_resized = cv2.resize(ref_face, (100, 100))
    login_resized = cv2.resize(login_face, (100, 100))
    similarity = ssim(ref_resized, login_resized)
    print(f"🔍 Face similarity score: {similarity:.2f}")
else:
    print("❌ Could not detect faces properly.")
    similarity = 0.0

# === 4️⃣ Handle Password and Attempts ===
if not os.path.exists(attempts_file):
    with open(attempts_file, "w") as f:
        f.write("0")

with open(attempts_file, "r") as f:
    failed_attempts = int(f.read())

password = input("🔐 Enter your password: ")

# ✅ Dual-Layer Verification (Face + Password)
if similarity >= 0.7 and password == correct_password:
    print(f"🔍 Face similarity score: {similarity:.2f}")
    print("✅ ACCESS GRANTED — Welcome to Vision Guard!")
    with open(attempts_file, "w") as f:
        f.write("0")  # Reset failed attempts

elif similarity >= 0.7 and password != correct_password:
    print(f"🔍 Face similarity score: {similarity:.2f}")
    print("⚠️ Face Matched but Password Incorrect!")
    failed_attempts += 1

elif similarity < 0.7 and password == correct_password:
    print(f"🔍 Face similarity score: {similarity:.2f}")
    print("⚠️ Password Correct but Face Not Matched! Try again with better lighting.")
    failed_attempts += 1

else:
    print(f"🔍 Face similarity score: {similarity:.2f}")
    print("❌ Both Face and Password Incorrect!")
    failed_attempts += 1

# Update failed attempts
with open(attempts_file, "w") as f:
    f.write(str(failed_attempts))

# === 🚨 Email Alert After 3 Failed Attempts ===
if failed_attempts >= 3:
    print("⚠️ ALERT: 3 Failed Attempts. Sending Email to Account Owner...")
    try:
        msg = EmailMessage()
        msg["Subject"] = "🚨 Vision Guard Alert: 3 Failed Login Attempts"
        msg["From"] = from_email
        msg["To"] = to_email
        msg.set_content("An unauthorized person tried to access your account 3 times.")

        with open("login_capture.jpg", "rb") as f:
            img_data = f.read()
        msg.add_attachment(img_data, maintype="image", subtype="jpeg", filename="Intruder.jpg")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(from_email, from_password)
            smtp.send_message(msg)

        print("📧 Email Alert Sent Successfully!")
        with open(attempts_file, "w") as f:
            f.write("0")  # Reset after alert
    except Exception as e:
        print("❌ Failed to send email:", e)
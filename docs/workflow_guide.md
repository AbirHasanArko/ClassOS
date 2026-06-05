# ClassOS Workflow Guideline

This document outlines the end-to-end workflow for setting up and running daily operations in the ClassOS system.

## 1. Administrative Workflow (Setup & Enrollment)

Before any classes begin, the system administrator or teacher must enroll students and configure the courses.

### Step 1.1: Create a Course
1. Navigate to the **Courses** page in the dashboard.
2. Click **Add Course** to create a new course.
3. Provide the Course Code (e.g., `CS101`) and Course Name (e.g., `Intro to Computer Science`).

### Step 1.2: Register Students
1. Navigate to the **Students** page in the dashboard.
2. Click **Add Student** and fill in the details (Student ID, First Name, Last Name, Email).
3. The student will appear in the system roster, but will have a "Not Set" status for Face and Fingerprint data.

### Step 1.3: Enroll Biometrics
For each student, you must register their biometrics so the AI can identify them:

**Face Enrollment:**
1. Locate the student in the **Students** table.
2. Under the **Face** column, click **Enroll**.
3. A modal will appear. Select 5-10 clear, front-facing photos of the student and click **Upload**.
4. The system will automatically generate 128D facial embeddings and store them in the database.

**Fingerprint Enrollment:**
1. Under the **Fingerprint** column, click **Enroll**.
2. An alert will prompt you to ask the student to place their finger on the connected R307 fingerprint sensor.
3. The sensor will capture the print, assign it an internal ID, and store the reference in the database.
   *(Note: If the hardware sensor is disconnected, the system will fall back to "Mock Mode" and simulate a successful enrollment).*

---

## 2. Teacher Workflow (Daily Attendance)

Once students and courses are configured, teachers can run automated attendance for their classes.

### Step 2.1: Start a Session
1. Navigate to the **Live Attendance** page in the dashboard.
2. Select the current Course from the dropdown menu.
3. Click **Start Attendance**.
4. The system instantly generates a new Attendance Session and creates a **Tabular Attendance Sheet** with all enrolled students marked as **ABSENT**.
5. The USB Webcam activates, and the live video feed begins streaming to the dashboard.

### Step 2.2: Automated AI Scanning
As students walk into the classroom, the AI engine processes the video feed in real-time:
- **Head Counting (YOLOv8):** The system counts the total number of people in the frame to ensure no one is missed.
- **Face Recognition (dlib):** The system identifies faces. When a student is recognized with high confidence, their status on the Tabular Attendance Sheet automatically flips from **ABSENT (Red)** to **PRESENT (Green)**.
- **Event Log:** A live scrolling log on the dashboard records the exact timestamp and confidence score of every recognition event.

### Step 2.3: Edge Cases & Fingerprint Fallback
If the AI detects a face but is unsure of the identity (low confidence), it will flag a **Mismatch/Warning** on the dashboard.
1. The dashboard will display a **Fingerprint Verification Needed** prompt.
2. The teacher asks the unrecognized student to place their finger on the sensor.
3. The teacher clicks **Scan Fingerprint** on the dashboard.
4. If the fingerprint matches an enrolled student, their attendance is instantly marked **PRESENT** on the sheet.

### Step 2.4: Manual Override
At any point during the session, the teacher can switch to the **Sheet** tab to view the full class roster.
- Next to every student, there is an override dropdown.
- The teacher can manually change a student's status to **Present**, **Absent**, **Late**, or **Excused**.

### Step 2.5: End Session
1. Once all students have arrived and the head count matches the recognized count, the teacher clicks **End Session**.
2. The camera feed is turned off, and the attendance records for that session are permanently locked into the PostgreSQL database.

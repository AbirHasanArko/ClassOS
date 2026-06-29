# ClassOS Workflow Guideline

This document outlines the end-to-end workflow for setting up and running daily operations in the ClassOS system.

## 1. Administrative Workflow (Setup & Enrollment)

Before any classes begin, the system administrator or teacher must enroll students and configure the courses.

### Step 1.1: Manage Courses
1. Navigate to the **Courses** page in the dashboard.
2. Click **Add Course** to create a new course.
3. Provide the Course Code (e.g., `CS101`) and Course Name (e.g., `Intro to Computer Science`).
4. **Assign Teachers:** Click the "Assign Teachers" button on the course card to link one or more registered teachers to the course. Teachers will only see analytics and session histories for the courses they are explicitly assigned to.
5. You can also **Edit** a course's name and schedule or **Delete** it entirely using the action buttons on the course card.

### Step 1.1b: Manage Admin/Teacher Users
1. Navigate to the **Users** page in the dashboard (Admin only).
2. Add new Admin or Teacher accounts. The system automatically provisions the decoupled underlying user profiles.

### Step 1.2: Manage Students
1. Navigate to the **Students** page in the dashboard.
2. Click **Add Student** and fill in the details (Student ID, First Name, Last Name, Email).
3. The student will appear in the system roster, but will have a "Not Set" status for Face and Fingerprint data.
4. You can also **Edit** a student's profile or **Delete** them using the action buttons on the right.

### Step 1.3: Enroll Biometrics
For each student, you must register their biometrics so the AI can identify them:

**Face Enrollment:**
1. Locate the student in the **Students** table.
2. Under the **Face** column, click **Enroll**.
3. A modal will appear with two options:
   - **Upload Files Tab:** Select 5-10 clear, front-facing photos from your computer and click **Upload**.
   - **Use Webcam Tab:** Use your device's camera (browser webcam, USB webcam, or phone camera) to capture 5-10 live snapshots directly, then click **Upload & Enroll**.
4. The system will automatically generate 128D facial embeddings and store them in the database.
5. Students can also self-enroll from their student portal (see Section 3).

**Fingerprint Enrollment:**
1. Under the **Fingerprint** column, click **Enroll**.
2. An alert will prompt you to ask the student to place their finger on the connected R307 fingerprint sensor.
3. The sensor will capture the print, assign it an internal ID, and store the reference in the database.
   *(Note: If the hardware sensor is disconnected, the system will fall back to "Mock Mode" and simulate a successful enrollment).*

> 💡 **Face Enrollment Sources**: Face images can come from **any camera source** — the teacher's laptop webcam, an external USB webcam, or even a student's phone camera (by opening the dashboard in the phone's browser). Camera 0 on the Pi is used for live attendance, but is NOT required for enrollment.

### Step 1.4: Enroll Students into a Course
Before taking attendance, students must be explicitly enrolled into the course they are taking. This can be done in two ways:

**Method A (Admin/Teacher):**
1. Navigate to the **Courses** page in the dashboard.
2. Click the **Manage Students** button next to the relevant course.
3. A modal will appear listing all students in the system. Check the boxes next to the students who should be enrolled.
4. To **un-enroll** a student, simply uncheck their box.
5. Click **Save Changes**.

**Method B (Student Self-Enrollment):**
See Section 3 for the student workflow.

---

## 2. Teacher Workflow (Daily Attendance)

Once students and courses are configured, teachers can run automated attendance for their classes.

### Step 2.1: Start a Session
1. Navigate to the **Live Attendance** page in the dashboard.
2. Select the current Course from the dropdown menu.
3. Click **Start Session**.
4. The system instantly generates a new Attendance Session and creates a **Tabular Attendance Sheet** with all enrolled students marked as **ABSENT**.
5. The session starts in **Take Attendance mode** by default.

### Step 2.2: Take Attendance Mode (Camera 0 — Entry Camera)
After starting a session, you will see two mode buttons at the top of the attendance view.

The system is in **Take Attendance** mode by default. In this mode:
- **Camera 0** (connected to CAM/DISP 0 on Raspberry Pi 5) activates and streams the live feed.
- The **Face Recognition AI** processes each frame in real-time:
  - **>= 70% confidence**: Student is automatically marked **PRESENT** (green bounding box). Their name and "Present" appears on the physical LCD display.
  - **30%–69% confidence**: A **Fingerprint Verification Needed** prompt appears on the dashboard. The physical LCD shows the fingerprint prompt. The student places their finger on the R307 sensor.
  - **< 30% confidence**: Face is labeled "Unknown" and ignored.
  - **No face detected at all**: A **"Direct Fingerprint Scan"** button is always visible in the dashboard for students who are not being detected (e.g., wearing a hijab, mask, or in poor lighting). They can scan directly without any face detection.
- The **LCD Display** shows:
  ```
  Total Attendee: XX
  <Student Name>
     >> Present
  Mode: ATTENDANCE
  ```
- The **Attendance Log** on the dashboard updates in real-time with each student's name, method (FACE/FINGERPRINT), and confidence.

### Step 2.3: Verify Head Count Mode (Camera 1 — Classroom Camera)
Once most students have arrived and been recognized, switch to **Verify Head Count** mode to ensure no proxy attendance or unrecognized students:

1. Click the **"Verify Head Count"** button at the top of the attendance view.
2. Camera 0 stops. **Camera 1** (connected to CAM/DISP 1 on Raspberry Pi 5) activates, pointing at the whole classroom.
3. The **YOLOv8 Nano AI** counts the total number of heads visible in the frame.
4. The dashboard shows a real-time comparison:
   - **Present** (from face/fingerprint): `XX`
   - **Head Count** (from Camera 1): `YY`
   - **✓ Match** or **✗ Mismatch** result
5. The **LCD Display** shows:
   ```
   Present    =  XX
   Head Count =  XX
   ✓ Match!
   Mode: HEAD COUNT
   ```
6. If there's a **Mismatch** (more heads than present), the teacher can ask any unrecognized students to scan their fingerprint.

> 💡 **Important**: The "Verify Head Count" button is automatically disabled if Camera 1 is not connected to the system.

### Step 2.4: Switching Modes Mid-Session
You can switch between **Take Attendance** and **Verify Head Count** mode at any time during a session:
- Click either mode button to switch instantly.
- **All attendance data is preserved** across mode switches — students already marked present remain present.
- The camera switches automatically (Camera 0 ↔ Camera 1).
- The LCD display updates to reflect the current mode.

### Step 2.5: Edge Cases & Fingerprint Fallback
- **Low confidence face (30–69%)**: Dashboard shows orange "Fingerprint Verification Needed" card. Teacher clicks "Scan Fingerprint" and student places finger on R307 sensor.
- **No face detection**: Teacher clicks "Direct Fingerprint Scan" button (always visible in attendance mode) OR the student presses the **physical hardware push button** connected to the Raspberry Pi. The student then scans directly.
- The LCD shows a fingerprint prompt in both cases.

### Step 2.6: Manual Override
At any point during the session, the teacher can switch to the **Sheet** tab to view the full class roster.
- Next to every student, there is an override dropdown.
- The teacher can manually change a student's status to **Present**, **Absent**, **Late**, or **Excused**.

### Step 2.7: End Session
1. Once satisfied, the teacher clicks **End Session**.
2. All cameras are turned off.
3. The LCD shows the ClassOS idle/branding screen.
4. The attendance records for that session are permanently locked into the PostgreSQL database.

### Step 2.8: Analytics & Exporting Course Reports
Teachers and Admins can export the full attendance report for any course:
1. Navigate to the **Courses** page.
2. Click the **View Report** button on any course card.
3. A modal will display a comprehensive table of all enrolled students.
4. The table displays daily attendance statuses, an overall attendance percentage (highlighted in red if <60%), and a calculated 0-10 score.
5. Click **Export CSV** to download the entire dataset for offline record-keeping.

---

## 3. Student Workflow (Self-Service)

Students have a dedicated portal where they can manage their own biometrics, courses, and view their attendance.

### Step 3.1: Logging In
1. The admin must have first created the student account.
2. The student navigates to the login page and enters their email and password (default: `student123`).
3. Upon logging in, the student is greeted by their personalized dashboard.

### Step 3.2: Self-Service Face Enrollment
Instead of relying on the admin, students can upload their own face data from any camera-equipped device:
1. Navigate to the **Face Enrollment** page.
2. The student can check their current enrollment status (Registered / Not Registered).
3. The student can choose to:
   - **Upload Files**: Select 5-10 clear front-facing images from their device.
   - **Use Webcam**: Capture images live using their **browser webcam** (laptop webcam, USB webcam, or phone camera — all work via browser `getUserMedia`).
4. Click **Upload & Enroll**. The AI engine will extract their facial embeddings securely.
5. If a student's appearance changes significantly (new glasses, different hair), they can click **Delete Data** to reset their profile and re-upload new samples.

### Step 3.3: Course Enrollment
1. Navigate to the **Available Courses** page.
2. The student will see all courses created by the teachers.
3. The student clicks the **Enroll** button on the course they are taking.
4. If already enrolled, the student can click the red **Unenroll** button to remove themselves from the course.

### Step 3.4: Tracking Attendance
1. Navigate to the **My Attendance** page.
2. The student will see a data table listing all their enrolled courses.
3. For each course, the table displays the number of classes they were marked present, the total number of classes held, and their computed attendance percentage.
4. The percentage is color-coded to easily identify if the student is falling behind the required attendance threshold.

---

## 4. Recognition Threshold Reference

| Confidence Score | Action | Method Logged | LCD / Dashboard |
|-----------------|--------|---------------|-----------------|
| **>= 70%** | Auto-mark PRESENT | `FACE` | "Student Name >> Present" |
| **30% – 69%** | Prompt fingerprint scan | `FINGERPRINT` (after scan) | Fingerprint prompt |
| **< 30%** | Unknown / ignored | — | No action |
| **No face at all** | Direct fingerprint scan available | `FINGERPRINT` | Direct scan button |

> ⚠️ **Note**: All thresholds are configurable via `.env` — `FACE_CONFIDENCE_AUTO` and `FACE_CONFIDENCE_FINGERPRINT`.

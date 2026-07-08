# ClassOS Detailed User Guide

Welcome to the ClassOS User Guide! This document provides step-by-step instructions for interacting with the ClassOS web dashboard and physical hardware, organized by user role.

---

## Table of Contents
1. [Introduction & Roles](#1-introduction--roles)
2. [Administrator Guide](#2-administrator-guide)
   - [Managing Users](#21-managing-users)
   - [Managing Students](#22-managing-students)
   - [Enrolling Biometrics](#23-enrolling-biometrics)
3. [Teacher Guide](#3-teacher-guide)
   - [Course Management](#31-course-management)
   - [Taking Live Attendance](#32-taking-live-attendance)
   - [Mode Switching: Attendance vs. Head Count](#33-mode-switching-attendance-vs-head-count)
   - [Manual Override](#34-manual-override)
   - [Analytics & Reports](#35-analytics--reports)
4. [Student Guide](#4-student-guide)
   - [Logging In](#41-logging-in)
   - [Face Self-Enrollment](#42-face-self-enrollment)
   - [Course Enrollment](#43-course-enrollment)
   - [Viewing Attendance History](#44-viewing-attendance-history)
5. [Hardware Interaction Guide](#5-hardware-interaction-guide)
   - [Reading the LCD Display](#51-reading-the-lcd-display)
   - [Using the Fingerprint Scanner](#52-using-the-fingerprint-scanner)
   - [Using the Push Button](#53-using-the-push-button)

---

## 1. Introduction & Roles

ClassOS is a fully automated attendance system. Depending on your role, you will have access to different features in the web dashboard.

* **Administrators (Admins):** Full access to the system. Can create/delete users, manage all students, and enroll biometrics using the physical hardware.
* **Teachers:** Can manage their assigned courses, run live attendance sessions, override attendance manually, and export CSV reports.
* **Students:** Can log into a self-service portal to enroll their face data, select courses, and view their personal attendance statistics.

**Accessing the Dashboard:**
1. Connect to the same network as the ClassOS system (or the Raspberry Pi's hotspot).
2. Open your web browser and navigate to the IP address provided by your IT administrator.
3. Log in with your email and password.

*(Default Admin Credentials: `admin@classos.local` / `changeme123`)*

---

## 2. Administrator Guide

As an Admin, your primary responsibility is initial system setup and roster management.

### 2.1 Managing Users
Users are the accounts that log into the system (Admins and Teachers).
1. Go to the **Users** tab.
2. Click **Add User** to create a new Admin or Teacher.
3. The system will automatically provision their underlying profile based on the selected role.

### 2.2 Managing Students
Students require explicit profiles before they can be tracked or logged in.
1. Go to the **Students** tab.
2. Click **Add Student** and input their Student ID, First Name, Last Name, and Email.
3. This creates their profile in the roster and generates their login account (default password: `student123`).

### 2.3 Enrolling Biometrics
To track a student, the AI needs their face or fingerprint data.
* **Face Enrollment:** Click **Enroll** under the Face column. You can upload 5-10 clear photos from your computer, or use the "Use Webcam" tab to take live photos. (Students can also do this themselves).
* **Fingerprint Enrollment:** Click **Enroll** under the Fingerprint column. You must be physically near the ClassOS device. The student will be prompted to place their finger on the sensor twice.

---

## 3. Teacher Guide

Teachers run the daily operations and monitor classroom attendance.

### 3.1 Course Management
1. Go to the **Courses** tab.
2. Click **Add Course** to create a new class (e.g., CS101).
3. **Enroll Students:** Click **Manage Students** on the course card. Check the boxes next to the students who are taking this class and click Save.

### 3.2 Taking Live Attendance
1. Go to the **Live Attendance** tab.
2. Select your course from the dropdown.
3. Click **Start Session**. 
4. The physical camera (Camera 0) will turn on, and a live video feed will appear in your browser.
5. As students walk in, the AI will draw bounding boxes around their faces. Green boxes indicate they are marked **Present**.

### 3.3 Mode Switching: Attendance vs. Head Count
ClassOS has two operating modes. You can switch between them at any time during a session using the buttons above the video feed.
* **Take Attendance Mode (Default):** Uses Camera 0 to recognize faces and mark students present.
* **Verify Head Count Mode:** Switches to Camera 1 (ceiling camera). The AI counts all physical heads in the room. The dashboard will show if the Head Count matches the number of students marked Present. Use this to catch proxy attendance!

### 3.4 Manual Override
If the AI misses a student, or a student arrives very late:
1. Click the **Sheet** tab next to the live video feed.
2. Find the student in the roster.
3. Change their dropdown status to Present, Absent, Late, or Excused.

### 3.5 Analytics & Reports
At the end of the semester, you can export all data.
1. End your live session.
2. Go to the **Courses** tab.
3. Click **View Report** on a course.
4. Review the overall percentages and scores.
5. Click **Export CSV** to download a spreadsheet of the entire semester's attendance records.

---

## 4. Student Guide

Students have a secure, self-service portal.

### 4.1 Logging In
1. Navigate to the ClassOS web address.
2. Enter your email and password (if you haven't set one, the default is usually `student123`).

### 4.2 Face Self-Enrollment
You can provide your facial data without needing an Admin.
1. Go to the **Face Enrollment** tab.
2. Either upload 5-10 portrait photos of yourself from your phone/computer gallery, OR use the **Use Webcam** tab to take live pictures.
3. The system will process your photos into a secure, mathematical facial vector.

### 4.3 Course Enrollment
1. Go to the **Available Courses** tab.
2. Find the classes you are currently taking and click **Enroll**.

### 4.4 Viewing Attendance History
1. Go to the **My Attendance** tab.
2. You can view your attendance rate for each course and see the specific dates you were marked Present, Absent, or Late.

---

## 5. Hardware Interaction Guide

You interact with the physical ClassOS device when you walk into the classroom.

### 5.1 Reading the LCD Display
The 20x4 LCD screen provides real-time feedback:
* **Idle:** Shows the ClassOS logo.
* **Attendance Mode:** Shows the total number of attendees, and displays your name when you are recognized by the camera.
* **Head Count Mode:** Displays the total present vs the physical head count, showing a checkmark (✓) if they match, or an X (✗) if there is a mismatch.
* **Prompt:** If it says "Fingerprint Needed!", the camera isn't sure who you are. Proceed to step 5.2.

### 5.2 Using the Fingerprint Scanner
If you are wearing a mask, or the AI is uncertain (30-69% confidence), you must use your fingerprint.
1. Wait for the LCD to prompt you, OR press the hardware push button.
2. The scanner will light up red/blue.
3. Place your enrolled finger firmly flat on the glass until the light turns off.

### 5.3 Using the Push Button
If the camera does not detect your face at all (e.g., poor lighting), you don't need to ask the teacher for help.
1. Press the momentary push button next to the fingerprint scanner.
2. The LCD will immediately update to say "Fingerprint Needed!".
3. Scan your finger. You are now marked present!

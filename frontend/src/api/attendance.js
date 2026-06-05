import client from './client';

export const startSession = async (courseId) => {
  const response = await client.post('/attendance/sessions', { course_id: courseId });
  return response.data;
};

export const endSession = async (sessionId) => {
  const response = await client.post(`/attendance/sessions/${sessionId}/end`);
  return response.data;
};

export const markAttendanceManual = async (sessionId, studentId, status) => {
  const response = await client.post(`/attendance/sessions/${sessionId}/attendance`, {
    student_id: studentId,
    status: status
  });
  return response.data;
};

export const triggerFingerprintScan = async () => {
  const response = await client.post('/fingerprint/verify');
  return response.data;
};

export const enrollFingerprint = async (studentId) => {
  const response = await client.post('/fingerprint/enroll', { student_id: studentId });
  return response.data;
};

export const getSessionRoster = async (sessionId) => {
  const response = await client.get(`/attendance/sessions/${sessionId}/roster`);
  return response.data;
};

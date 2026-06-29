import client from './client';

export const startSession = async (courseId, mode = 'attendance') => {
  const response = await client.post('/attendance/sessions', {
    course_id: courseId,
    mode: mode,
  });
  return response.data;
};

export const endSession = async (sessionId) => {
  const response = await client.post(`/attendance/sessions/${sessionId}/end`);
  return response.data;
};

export const deleteSession = async (sessionId) => {
  const response = await client.delete(`/attendance/sessions/${sessionId}`);
  return response.data;
};

export const switchSessionMode = async (sessionId, mode) => {
  const response = await client.post(`/attendance/sessions/${sessionId}/mode`, { mode });
  return response.data;
};

export const markAttendanceManual = async (sessionId, studentId, status) => {
  const response = await client.post(`/attendance/sessions/${sessionId}/attendance`, {
    student_id: studentId,
    status: status,
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

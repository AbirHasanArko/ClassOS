import client from './client';

export const getStudents = async (skip = 0, limit = 50, search = '') => {
  const response = await client.get('/students/', { params: { skip, limit, search } });
  return response.data;
};

export const createStudent = async (studentData) => {
  const response = await client.post('/students/', studentData);
  return response.data;
};

export const getStudent = async (id) => {
  const response = await client.get(`/students/${id}`);
  return response.data;
};

export const getMyAttendance = async () => {
  const response = await client.get('/students/me/attendance');
  return response.data;
};

export const selfEnrollCourse = async (courseId) => {
  const response = await client.post(`/students/me/courses/${courseId}/enroll`);
  return response.data;
};

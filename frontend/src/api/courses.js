import client from './client';

export const getCourses = async (skip = 0, limit = 50) => {
  const response = await client.get('/courses/', { params: { skip, limit } });
  return response.data;
};

export const createCourse = async (courseData) => {
  const response = await client.post('/courses/', courseData);
  return response.data;
};

export const enrollStudents = async (courseId, studentIds) => {
  const response = await client.post(`/courses/${courseId}/enroll`, { student_ids: studentIds });
  return response.data;
};

export const getCourseStudents = async (courseId) => {
  const response = await client.get(`/courses/${courseId}/students`);
  return response.data;
};

export const updateCourse = async (courseId, courseData) => {
  const response = await client.put(`/courses/${courseId}`, courseData);
  return response.data;
};

export const deleteCourse = async (courseId) => {
  const response = await client.delete(`/courses/${courseId}`);
  return response.data;
};

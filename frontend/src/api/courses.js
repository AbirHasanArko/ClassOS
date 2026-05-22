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

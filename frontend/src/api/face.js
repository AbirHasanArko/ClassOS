import client from './client';

/**
 * Get face registration status for a student.
 * @param {string} studentId - UUID of the student
 */
export const getFaceStatus = async (studentId) => {
  const response = await client.get(`/students/${studentId}/face`);
  return response.data;
};

/**
 * Upload face images to register a student's face.
 * @param {string} studentId - UUID of the student
 * @param {FileList|File[]} files - One or more image files
 */
export const uploadFaceImages = async (studentId, files) => {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }

  const response = await client.post(`/students/${studentId}/face`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

/**
 * Delete all face data for a student (reset face registration).
 * @param {string} studentId - UUID of the student
 */
export const deleteFaceData = async (studentId) => {
  const response = await client.delete(`/students/${studentId}/face`);
  return response.data;
};

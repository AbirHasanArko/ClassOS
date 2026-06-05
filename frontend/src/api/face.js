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
 * Upload face images (or webcam blobs) to register a student's face.
 * @param {string} studentId - UUID of the student
 * @param {Array<File|Blob>} files - One or more image files or webcam blobs
 */
export const uploadFaceImages = async (studentId, files) => {
  const formData = new FormData();
  files.forEach((file, i) => {
    // File objects already carry a filename; Blobs need one supplied
    const filename = file instanceof File ? file.name : `webcam_capture_${i + 1}.jpg`;
    formData.append('files', file, filename);
  });

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

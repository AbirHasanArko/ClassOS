import client from './client';

export const getDashboardStats = async () => {
  const response = await client.get('/analytics/dashboard/stats');
  return response.data;
};

export const getSessionHistory = async (skip = 0, limit = 50) => {
  const response = await client.get(`/analytics/sessions?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const downloadSessionCsv = async (sessionId) => {
  const response = await client.get(`/analytics/sessions/${sessionId}/export`, {
    responseType: 'blob', // Important for file download
  });
  
  // Create a blob URL and trigger download
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  
  // Extract filename from Content-Disposition header if possible
  let filename = 'attendance.csv';
  const disposition = response.headers['content-disposition'];
  if (disposition && disposition.indexOf('attachment') !== -1) {
    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
    const matches = filenameRegex.exec(disposition);
    if (matches != null && matches[1]) {
      filename = matches[1].replace(/['"]/g, '');
    }
  }
  
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
};

export const getCourseReport = async (courseId) => {
  const response = await client.get(`/analytics/courses/${courseId}/report`);
  return response.data;
};

export const downloadCourseReportCsv = async (courseId) => {
  const response = await client.get(`/analytics/courses/${courseId}/report/csv`, {
    responseType: 'blob',
  });
  
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  
  let filename = 'course_report.csv';
  const disposition = response.headers['content-disposition'];
  if (disposition && disposition.indexOf('attachment') !== -1) {
    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
    const matches = filenameRegex.exec(disposition);
    if (matches != null && matches[1]) {
      filename = matches[1].replace(/['"]/g, '');
    }
  }
  
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
};

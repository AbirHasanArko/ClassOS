import client from './client';

export const getUsers = async () => {
  const response = await client.get('/users/');
  return response.data;
};

export const getTeachers = async () => {
  const response = await client.get('/users/teachers');
  return response.data;
};

export const createUser = async (userData) => {
  const response = await client.post('/users/', userData);
  return response.data;
};

export const updateUser = async (userId, userData) => {
  const response = await client.put(`/users/${userId}`, userData);
  return response.data;
};

export const deleteUser = async (userId) => {
  const response = await client.delete(`/users/${userId}`);
  return response.data;
};

export const updatePassword = async (passwordData) => {
  const response = await client.put('/users/me/password', passwordData);
  return response.data;
};

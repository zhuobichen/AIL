export const API_BASE_URL = 'http://localhost:8000/api/v1';

export async function uploadTask(file: File, book: string) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('book', book);

  const res = await fetch(`${API_BASE_URL}/tasks/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error('Upload failed');
  return res.json();
}

export async function getTaskStatus(taskId: string) {
  const res = await fetch(`${API_BASE_URL}/tasks/${taskId}/status`);
  if (!res.ok) throw new Error('Failed to fetch status');
  return res.json();
}

export async function getTaskResults(taskId: string) {
  const res = await fetch(`${API_BASE_URL}/tasks/${taskId}/results`);
  if (!res.ok) throw new Error('Failed to fetch results');
  return res.json();
}
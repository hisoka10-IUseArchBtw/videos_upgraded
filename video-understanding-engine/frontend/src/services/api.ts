const BASE_URL = "https://130-210-13-32.sslip.io";

/**
 * A wrapper around the native fetch API to automatically inject JWT tokens
 * and handle standard error formats from our FastAPI backend.
 */
export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  
  // Prevent browser caching
  headers.set('Cache-Control', 'no-cache');
  headers.set('Pragma', 'no-cache');

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    cache: 'no-store',
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = "An error occurred with the API request.";
    try {
      const errorData = await response.json();
      // FastAPI usually puts the error string in `detail`
      errorMessage = typeof errorData.detail === 'string'
        ? errorData.detail
        : JSON.stringify(errorData.detail) || errorMessage;
    } catch {
      // Ignore JSON parse error if it's not JSON
    }
    throw new Error(errorMessage);
  }

  // Handle empty responses
  if (response.status === 204) return null;

  return response.json();
}

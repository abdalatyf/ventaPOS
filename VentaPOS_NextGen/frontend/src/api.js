import axios from 'axios';

const api = axios.create({
  baseURL: '/', // Because of Vite proxy, we can just use relative URLs, or specify '/api' if we only make /api calls, but leaving '/' allows generic use.
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 403) {
      if (error.response.data && error.response.data.error === 'license_expired') {
        // Trigger a global event to show the Activation Modal
        window.dispatchEvent(new CustomEvent('show-activation-modal'));
      }
    }
    return Promise.reject(error);
  }
);

export default api;

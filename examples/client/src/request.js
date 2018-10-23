import axios from 'axios';

class Request {
  constructor() {
    this.initConfig();
  }

  initConfig() {
    const baseURL = 'http://localhost:8000/';

    axios.defaults.baseURL = baseURL;
    this.setAuthHeader(localStorage.getItem('token'));

    axios.interceptors.response.use(response => ({
      ...response,
      data: response.data,
    }), error => Promise.reject(this.parseError(error)));
  }

  setAuthHeader(token) {
    if (token) axios.defaults.headers.common.Authorization = `JWT ${token}`;
  }

  setAuthToken(token) {
    localStorage.setItem('token', token);
    this.setAuthHeader(token);
  }

  clearAuthToken() {
    localStorage.removeItem('token');
    axios.defaults.headers.common.Authorization = '';
  }

  parseError(error) {
    const { response = {} } = error;

    return {
      ...error,
      response: {
        ...response,
        data: {
          ...response.data,
          _error: response.data ? response.data.non_field_errors : [],
        },
      },
    };
  }

  get(...args) {
    return axios.get(...args);
  }

  post(...args) {
    return axios.post(...args);
  }

  options(...args) {
    return axios.options(...args);
  }

  patch(...args) {
    return axios.patch(...args);
  }

  put(...args) {
    return axios.put(...args);
  }

  delete(...args) {
    return axios.delete(...args);
  }
}

export default new Request();

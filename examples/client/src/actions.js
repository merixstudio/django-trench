import request from './request';

export const fetchMe = () => request.get('djoser/me/');
export const fetchActiveMethods = () => request.get('auth/mfa/user-active-methods/');
export const fetchMFAConfig = () => request.get('auth/mfa/config');

export const updateMe = data => request.patch('djoser/me/', data);

export const request2FAregistration = data => request.post(`auth/${data.method}/activate/`, data);
export const confirm2FAregistration = data => request.post(`auth/${data.method}/activate/confirm/`, data);
export const disableFAregistration = data => request.post(`auth/${data.method}/deactivate/`, { ...data, new_primary_method: data.new_method });

export const login = data => request.post('auth/login/', data);
export const loginCode = data => request.post('auth/login/code/', data);
export const register = data => request.post('djoser/register/', data);

export const regenerateBackupCodes = data => request.post(`auth/${data.method}/codes/regenerate/`, data);
export const requestCodeSend = data => request.post('auth/code/request/', data);
export const changePrimaryMethod = data => request.post('auth/mfa/change-primary-method/', data);

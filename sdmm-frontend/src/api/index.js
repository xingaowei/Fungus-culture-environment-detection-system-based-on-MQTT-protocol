// src/api/index.js

import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  getSensorStatusSummary() {
    return apiClient.get('/dashboard/sensor-status-summary');
  },

  getActiveSensors() {
    return apiClient.get('/sensor_board/sensors');
  },
  getSensorStatus(sensorId) {
    return apiClient.get(`/sensor_board/${sensorId}/status`);
  },
  getSensorThresholds(sensorId) {
    return apiClient.get(`/sensor_board/${sensorId}/thresholds`);
  },
  updateSensorThresholds(sensorId, thresholds) {
    return apiClient.put(`/sensor_board/${sensorId}/thresholds`, { thresholds });
  },
  queryHistoricalData(sensorId, startTime, endTime) {
    return apiClient.get(`/sensor_board/${sensorId}/history`, {
      params: {
        start_time: startTime,
        end_time: endTime,
      },
    });
  },

  getSubscriptions() {
    return apiClient.get(`/subscriptions`);
  },
  createSubscription(subscription) {
    return apiClient.post(`/subscriptions`, subscription);
  },
  updateSubscription(sensorName, subscription) {
    return apiClient.put(`/subscriptions/${sensorName}`, subscription);
  },
  deleteSubscription(sensorName) {
    return apiClient.delete(`/subscriptions/${sensorName}`);
  },
  uploadSubscriptionsFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/subscriptions/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  downloadSubscriptionsFile() {
    return apiClient.get(`/subscriptions/download`);
  },

  getAlerts() {
    return apiClient.get(`/alerts`);
  },
  deleteAlert(alertId) {
    return apiClient.delete(`/alerts/${alertId}`);
  },
  acknowledgeAlert(alertId) {
    return apiClient.put(`/alerts/${alertId}/acknowledge`);
  },
  resolveAlert(alertId) {
    return apiClient.put(`/alerts/${alertId}/resolve`);
  },
  clearAllAlerts() {
    return apiClient.delete(`/alerts/clear`);
  },

  getSensor(sensorId) {
    return apiClient.get(`/sensors/${sensorId}`);
  }
}
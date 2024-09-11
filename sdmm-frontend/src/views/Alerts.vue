<!-- src/views/Alerts.vue -->

<template>
  <div class="alerts-container">
    <div class="delete-all-container">
      <button class="delete-all-button" @click="confirmDeleteAll">Delete All Alerts</button>
    </div>
    <div class="table-responsive">
      <table class="alerts-table">
        <thead>
          <tr>
            <th>Sensor Name</th>
            <th>Alert Type</th>
            <th>Message</th>
            <th>Created At</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alert in sortedAlerts" :key="alert.alert_id">
            <td>{{ sensorNames[alert.sensor_id] || 'Loading...' }}</td>
            <td>{{ alert.alert_type }}</td>
            <td>{{ alert.message }}</td>
            <td>{{ new Date(alert.created_at).toLocaleString() }}</td>
            <td>{{ alert.status }}</td>
            <td>
              <button class="view-button" @click="viewDetails(alert)">View</button>
              <button class="acknowledge-button" :disabled="alert.status !== 'new'" @click="acknowledgeAlert(alert)">
                Acknowledge
              </button>
              <button class="resolve-button" :disabled="alert.status === 'resolved'" @click="resolveAlert(alert)">
                Resolve
              </button>
              <button class="delete-button" @click="confirmDelete(alert.alert_id)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showDetails" class="modal">
      <div class="modal-content">
        <h2>Alert Details for {{ currentAlert.sensor_id }}</h2>
        <pre>{{ beautifyJson(currentAlert) }}</pre>
        <button class="close-button" @click="closeDetails">Close</button>
      </div>
    </div>

    <div v-if="showDeleteDialog" class="modal">
      <div class="modal-content delete-modal">
        <h2>Are you sure you want to delete this alert?</h2>
        <div class="dialog-buttons">
          <button @click="deleteAlert">Delete</button>
          <button @click="closeDeleteDialog">Cancel</button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteAllDialog" class="modal">
      <div class="modal-content delete-modal">
        <h2>Are you sure you want to delete all alerts?</h2>
        <div class="dialog-buttons">
          <button @click="deleteAllAlerts">Delete All</button>
          <button @click="closeDeleteAllDialog">Cancel</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
import api from '@/api';
import { js_beautify } from 'js-beautify';

export default {
  data() {
    return {
      alerts: [],
      sensorNames: {},
      showDetails: false,
      currentAlert: null,
      showDeleteDialog: false,
      showDeleteAllDialog: false,
      deleteTarget: '',
    };
  },
  computed: {
    sortedAlerts() {
      return this.alerts
        .filter(alert => !alert.is_deleted)
        .sort((a, b) => {
          const timeDiff = new Date(b.created_at) - new Date(a.created_at);
          if (timeDiff !== 0) return timeDiff;
          return a.message.localeCompare(b.message);
        });
    },
  },
  methods: {
    confirmDeleteAll() {
      this.showDeleteAllDialog = true;
    },
    async deleteAllAlerts() {
      try {
        await api.clearAllAlerts();
        this.fetchAlerts();
        this.showDeleteAllDialog = false;
      } catch (error) {
        console.error('Error deleting all alerts:', error);
      }
    },
    async fetchAlerts() {
      const response = await api.getAlerts();
      this.alerts = response.data;
      this.alerts.forEach(alert => {
        this.fetchSensorName(alert.sensor_id);
      });
    },
    async fetchSensorName(sensorId) {
      if (!this.sensorNames[sensorId]) {
        try {
          const response = await api.getSensor(sensorId);
          this.sensorNames[sensorId] = response.data.name;
        } catch (error) {
          console.error(`Error fetching sensor name for sensor_id ${sensorId}:`, error);
        }
      }
    },
    viewDetails(alert) {
      this.currentAlert = alert;
      this.showDetails = true;
    },
    closeDetails() {
      this.showDetails = false;
    },
    beautifyJson(jsonData) {
      try {
        return js_beautify(JSON.stringify(jsonData), { indent_size: 2 });
      } catch (error) {
        console.error('Error beautifying JSON:', error);
        return JSON.stringify(jsonData);
      }
    },
    async acknowledgeAlert(alert) {
      try {
        await api.acknowledgeAlert(alert.alert_id);
        this.fetchAlerts();
      } catch (error) {
        console.error('Error acknowledging alert:', error);
      }
    },
    async resolveAlert(alert) {
      try {
        await api.resolveAlert(alert.alert_id);
        this.fetchAlerts();
      } catch (error) {
        console.error('Error resolving alert:', error);
      }
    },
    confirmDelete(alertId) {
      this.deleteTarget = alertId;
      this.showDeleteDialog = true;
    },
    closeDeleteDialog() {
      this.showDeleteDialog = false;
    },
    async deleteAlert() {
      try {
        await api.deleteAlert(this.deleteTarget);
        this.fetchAlerts();
        this.closeDeleteDialog();
      } catch (error) {
        console.error('Error deleting alert:', error);
      }
    },
    closeDeleteAllDialog() {
      this.showDeleteAllDialog = false;
    },
  },
  mounted() {
    this.fetchAlerts();
  },
};
</script>

<style scoped>
.alerts-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  color: #d1d1d1;
  background-color: #121212;
  border-radius: 10px;
}

.table-responsive {
  width: 100%;
  overflow-x: auto;
}

.alerts-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
  background-color: #1f1f1f;
  border-radius: 8px;
}

.alerts-table th,
.alerts-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #333;
  text-align: left;
}

.alerts-table th {
  background-color: #292929;
  font-weight: bold;
  color: #b0b0b0;
}

.alerts-table td {
  color: #d1d1d1;
}

.alerts-table tr:hover {
  background-color: #2a2a2a;
}

button {
  background-color: #343434;
  color: #f1f1f1;
  padding: 8px 12px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.3s ease, color 0.3s ease;
}

button:disabled {
  background-color: #555555;
  cursor: not-allowed;
}

button:hover:not(:disabled) {
  background-color: #4c4c4c;
}

.delete-button {
  background-color: #ef4444;
}

.delete-button:hover:not(:disabled) {
  background-color: #dc2626;
}

.acknowledge-button {
  background-color: #f59e0b;
}

.acknowledge-button:hover:not(:disabled) {
  background-color: #d97706;
}

.resolve-button {
  background-color: #10b981;
}

.resolve-button:hover:not(:disabled) {
  background-color: #059669;
}

.view-button {
  background-color: #3b82f6;
}

.view-button:hover:not(:disabled) {
  background-color: #2563eb;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(0, 0, 0, 0.8);
}

.modal-content {
  background-color: #1e1e1e;
  padding: 20px;
  width: 90%;
  max-width: 600px;
  max-height: 80%;
  overflow-y: auto;
  border-radius: 10px;
  color: #d1d1d1;
}

pre {
  background-color: #2a2a2a;
  padding: 10px;
  white-space: pre-wrap;
  word-wrap: break-word;
  border-radius: 5px;
  color: #d1d1d1;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
}

.dialog-buttons button {
  margin-left: 10px;
}

.delete-all-container {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 10px;
}

.delete-all-button {
  background-color: #ef4444;
  color: white;
  padding: 8px 12px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.delete-all-button:hover {
  background-color: #dc2626;
}
</style>

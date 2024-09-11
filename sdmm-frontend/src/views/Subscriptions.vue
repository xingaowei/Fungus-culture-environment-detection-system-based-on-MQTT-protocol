<!-- src/views/Subscriptions.vue -->

<template>
  <div class="subscriptions-container">
    <div class="header-buttons">
      <button class="create-subscription-button" @click="openCreateSubscriptionDialog">Create Subscription</button>
      <button class="download-button" @click="downloadSubscriptionsFile">Download Subscriptions</button>
      <input type="file" ref="fileInput" @change="handleFileUpload" class="upload-input" />
      <button class="upload-button" @click="triggerFileInput">Upload Subscriptions</button>
    </div>

    <div class="table-responsive">
      <table class="subscriptions-table">
        <thead>
          <tr>
            <th>Sensor Name</th>
            <th>Broker Address</th>
            <th>Broker Port</th>
            <th>Topic</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="subscription in subscriptions" :key="subscription.sensor_name">
            <td>{{ subscription.sensor_name }}</td>
            <td>{{ subscription.broker_address }}</td>
            <td>{{ subscription.broker_port }}</td>
            <td>{{ subscription.topic }}</td>
            <td>
              <button class="view-details-button" @click="viewDetails(subscription)">View</button>
              <button class="edit-button" @click="openEditSubscriptionDialog(subscription)">Edit</button>
              <button class="delete-button" @click="confirmDelete(subscription.sensor_name)">Del</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showDetails" class="modal">
      <div class="modal-content">
        <h2>Subscription Details for {{ currentSubscription.sensor_name }}</h2>
        <pre>{{ beautifyJson(currentSubscription) }}</pre>
        <button class="close-button" @click="closeDetails">Close</button>
      </div>
    </div>

    <div v-if="showCreateDialog || showEditDialog" class="modal">
      <div class="modal-content create-modal">
        <h2>{{ showEditDialog ? 'Edit' : 'Create' }} Subscription</h2>
        <textarea v-model="subscriptionJson" class="json-input"></textarea>
        <div class="dialog-buttons">
          <button @click="showEditDialog ? updateSubscription() : createSubscription()">
            {{ showEditDialog ? 'Update' : 'Create' }}
          </button>
          <button @click="closeCreateDialog">Cancel</button>
        </div>
      </div>
    </div>

    <div v-if="showDeleteDialog" class="modal">
      <div class="modal-content delete-modal">
        <h2>Are you sure you want to delete {{ deleteTarget }}?</h2>
        <div class="dialog-buttons">
          <button @click="deleteSubscription">Delete</button>
          <button @click="closeDeleteDialog">Cancel</button>
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
      subscriptions: [],
      showDetails: false,
      currentSubscription: null,
      showCreateDialog: false,
      showEditDialog: false,
      subscriptionJson: '',
      deleteTarget: '',
      showDeleteDialog: false,
      newSubscriptionJson: `{
  "broker_address": "mqtt_server",
  "broker_port": 1883,
  "password": null,
  "sensor_name": "Combined Sensor 1",
  "sensor_types": ["Temperature", "Humidity", "CO2 Concentration"],
  "topic": "sensor/location_1",
  "username": null,
  "metadata": [
    {
      "version": "1.3.0"
    },
    {
      "brand": "SONY"
    },
    {
      "thresholds": {
        "CO2 Concentration": {
          "max": 450.0,
          "min": 300.0
        },
        "Humidity": {
          "max": 60.0,
          "min": 30.0
        },
        "Temperature": {
          "max": 29.0,
          "min": 0.0
        }
      }
    },
    {
      "gps_location": {
        "latitude": 0.675,
        "longitude": 39.6503,
        "altitude": 120.0
      }
    }
  ]
}`
    };
  },
  methods: {
    async fetchSubscriptions() {
      const response = await api.getSubscriptions();
      this.subscriptions = response.data.sort((a, b) => {
        return a.sensor_name.localeCompare(b.sensor_name);
      });
    },
    viewDetails(subscription) {
      this.currentSubscription = subscription;
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
    openCreateSubscriptionDialog() {
      this.subscriptionJson = this.newSubscriptionJson;
      this.showCreateDialog = true;
    },
    openEditSubscriptionDialog(subscription) {
      this.subscriptionJson = js_beautify(JSON.stringify(subscription), { indent_size: 2 });
      this.showEditDialog = true;
    },
    closeCreateDialog() {
      this.showCreateDialog = false;
      this.showEditDialog = false;
    },
    confirmDelete(sensorName) {
      this.deleteTarget = sensorName;
      this.showDeleteDialog = true;
    },
    closeDeleteDialog() {
      this.showDeleteDialog = false;
    },
    async createSubscription() {
      try {
        const parsedSubscription = JSON.parse(this.subscriptionJson);
        const requiredFields = ['broker_address', 'broker_port', 'sensor_name', 'sensor_types', 'topic', 'metadata'];
        for (const field of requiredFields) {
          if (!parsedSubscription[field]) {
            throw new Error(`Missing required field: ${field}`);
          }
        }
        const response = await api.createSubscription(parsedSubscription);
        this.fetchSubscriptions();
        this.closeCreateDialog();
      } catch (error) {
        if (error.response) {
          const status = error.response.status;
          const errorMessage = js_beautify(JSON.stringify(error.response.data));
          alert(`Error: ${status}\n${errorMessage}`);
        } else {
          alert("Error: " + error.message);
        }
        console.error("Error creating subscription:", error);
      }
    },
    async updateSubscription() {
      try {
        const parsedSubscription = JSON.parse(this.subscriptionJson);
        const sensorName = parsedSubscription.sensor_name;
        await api.updateSubscription(sensorName, parsedSubscription);
        this.fetchSubscriptions();
        this.closeCreateDialog();
      } catch (error) {
        alert("Error updating subscription: " + error.message);
        console.error("Error updating subscription:", error);
      }
    },
    async deleteSubscription() {
      try {
        await api.deleteSubscription(this.deleteTarget);
        this.fetchSubscriptions();
        this.closeDeleteDialog();
      } catch (error) {
        alert("Error deleting subscription: " + error.message);
        console.error("Error deleting subscription:", error);
      }
    },
    async downloadSubscriptionsFile() {
      try {
        const response = await api.downloadSubscriptionsFile();
        const blob = new Blob([response.data], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'subscriptions.yaml';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } catch (error) {
        alert("Error downloading subscriptions: " + error.message);
        console.error("Error downloading subscriptions:", error);
      }
    },
    triggerFileInput() {
      this.$refs.fileInput.click();
    },
    async handleFileUpload(event) {
      const file = event.target.files[0];
      if (!file) return;

      try {
        await api.uploadSubscriptionsFile(file);
        this.fetchSubscriptions();
      } catch (error) {
        alert("Error uploading subscriptions: " + error.message);
        console.error("Error uploading subscriptions:", error);
      }
    }
  },
  mounted() {
    this.fetchSubscriptions();
  }
};
</script>

<style scoped>
.subscriptions-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
  color: #d1d1d1;
  background-color: #121212;
  border-radius: 10px;
}

.header-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 20px;
}

.table-responsive {
  width: 100%;
  overflow-x: auto;
}

.subscriptions-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
  background-color: #1f1f1f;
  border-radius: 8px;
}

.subscriptions-table th,
.subscriptions-table td {
  padding: 12px 15px;
  border-bottom: 1px solid #333;
  text-align: left;
}

.subscriptions-table th {
  background-color: #292929;
  font-weight: bold;
  color: #b0b0b0;
}

.subscriptions-table td {
  color: #d1d1d1;
}

.subscriptions-table tr:hover {
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

button:hover {
  background-color: #4c4c4c;
}

.create-subscription-button,
.download-button,
.upload-button {
  background-color: #3b82f6;
}

.create-subscription-button:hover,
.download-button:hover,
.upload-button:hover {
  background-color: #2563eb;
}

.delete-button {
  background-color: #ef4444;
}

.delete-button:hover {
  background-color: #dc2626;
}

.edit-button {
  background-color: #10b981;
}

.edit-button:hover {
  background-color: #059669;
}

.view-details-button {
  background-color: #f59e0b;
}

.view-details-button:hover {
  background-color: #d97706;
}

.upload-button {
  background-color: #8b5cf6;
}

.upload-button:hover {
  background-color: #7c3aed;
}

.download-button {
  background-color: #60a5fa;
}

.download-button:hover {
  background-color: #3b82f6;
}

.upload-input {
  display: none;
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

.json-input {
  width: 100%;
  height: 250px;
  background-color: #2a2a2a;
  color: #d1d1d1;
  border: 1px solid #555;
  padding: 10px;
  border-radius: 5px;
  margin-bottom: 10px;
  font-family: monospace;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
}

.dialog-buttons button {
  margin-left: 10px;
  padding: 8px 12px;
  border-radius: 5px;
  border: none;
  cursor: pointer;
  font-size: 0.9rem;
}

.dialog-buttons button:first-child {
  background-color: #10b981;
  color: white;
}

.dialog-buttons button:last-child {
  background-color: #ef4444;
  color: white;
}

.dialog-buttons button:hover {
  opacity: 0.9;
}

@media (max-width: 600px) {

  .subscriptions-table th,
  .subscriptions-table td {
    padding: 8px 10px;
    font-size: 0.85rem;
  }

  button {
    font-size: 0.8rem;
    padding: 6px 10px;
  }

  .header-buttons {
    flex-direction: column;
    align-items: flex-end;
  }

  .modal-content {
    width: 100%;
    height: 90%;
  }
}
</style>

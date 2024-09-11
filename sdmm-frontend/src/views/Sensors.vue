<!-- src/views/Sensor.vue -->

<template>
  <div class="sensor-grid-container">
    <button class="refresh-button" @click="refreshPage">
      <img src="@/assets/refresh.svg" alt="Refresh" />
    </button>
    <div class="sensor-grid">
      <div v-for="sensor in sensors" :key="sensor.sensor_id" class="sensor-card">
        <div class="status-dot" :class="sensorStatuses[sensor.sensor_id]"></div>
        <div class="sensor-info">
          <h3>{{ sensor.name }}</h3>
          <p>Location: {{ sensor.location }}</p>
          <p>Last updated: {{ new Date(sensor.updated_at).toLocaleString() }}</p>
        </div>
        <div class="sensor-chart">
          <canvas :id="'chart-' + sensor.sensor_id"></canvas>
        </div>
        <div class="capsule-buttons">
          <button v-for="type in dataTypes" :key="type" @click="changeDataType(sensor.sensor_id, type)"
            :class="{ 'active': selectedData[sensor.sensor_id] === type }">
            {{ type }}
          </button>
        </div>
        <div class="modify-threshold">
          <button @click="openThresholdDialog(sensor.sensor_id)">Modify Thresholds</button>
        </div>
        <div class="query-history">
          <button @click="openHistoryDialog(sensor.sensor_id)">Query History</button>
        </div>
      </div>
    </div>

    <div v-if="showThresholdDialog" class="modal">
      <div class="modal-content">
        <h2>Modify Thresholds for {{ currentSensorId }}</h2>
        <div v-if="thresholds[currentSensorId]">
          <div v-for="(threshold, type) in thresholds[currentSensorId]" :key="type" class="input-group">
            <label>{{ type }} Min:</label>
            <input v-model="newThresholds[type].min" type="number" />
            <label>{{ type }} Max:</label>
            <input v-model="newThresholds[type].max" type="number" />
          </div>
        </div>
        <div class="dialog-buttons">
          <button @click="updateThresholds">Save</button>
          <button @click="closeThresholdDialog">Cancel</button>
        </div>
      </div>
    </div>

    <div v-if="showHistoryDialog" class="modal">
      <div class="modal-content history-modal">
        <h2>Historical Data for {{ currentSensorId }}</h2>

        <div class="date-picker">
          <label for="start-date">Start Date:</label>
          <input type="datetime-local" v-model="historyStartDate" id="start-date" />
          <label for="end-date">End Date:</label>
          <input type="datetime-local" v-model="historyEndDate" id="end-date" />
          <button @click="fetchHistoricalData">Apply</button>
        </div>
        <div class="history-chart">
          <canvas id="history-chart"></canvas>
        </div>
        <div class="dialog-buttons">
          <button @click="closeHistoryDialog">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue';
import Chart from 'chart.js/auto';
import api from '@/api';
import annotationPlugin from 'chartjs-plugin-annotation';
Chart.register(annotationPlugin);

export default {
  data() {
    return {
      sensors: [],
      sensorStatuses: {},
      thresholds: {},
      newThresholds: {},
      dataTypes: ['Temperature', 'Humidity', 'CO2 Concentration'],
      charts: {},
      selectedData: {},
      autoRefreshInterval: null,
      showThresholdDialog: false,
      currentSensorId: null,
      showHistoryDialog: false,
      historyStartDate: new Date(new Date().getTime() - 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
      historyEndDate: new Date().toISOString().slice(0, 16),
      currentSensorId: null,
      historyChart: null,
    };
  },
  methods: {
    openHistoryDialog(sensorId) {
      this.currentSensorId = sensorId;
      this.showHistoryDialog = true;
      this.fetchHistoricalData();
    },
    closeHistoryDialog() {
      this.showHistoryDialog = false;
      if (this.historyChart) {
        this.historyChart.destroy();
      }
    },
    async fetchHistoricalData() {
      const response = await api.queryHistoricalData(
        this.currentSensorId,
        new Date(this.historyStartDate).toISOString(),
        new Date(this.historyEndDate).toISOString()
      );
      const data = response.data;
      const dataMap = {
        'Temperature': data.temperature,
        'Humidity': data.humidity,
        'CO2 Concentration': data.co2,
      };
      const selectedType = this.selectedData[this.currentSensorId];
      const thresholds = this.thresholds[this.currentSensorId]
        ? this.thresholds[this.currentSensorId][selectedType]
        : null;
      if (this.historyChart) {
        this.historyChart.destroy();
      }
      const ctx = document.getElementById('history-chart').getContext('2d');
      this.historyChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: dataMap[selectedType].map(item => new Date(item.timestamp).toLocaleTimeString()),
          datasets: [{
            label: selectedType,
            data: dataMap[selectedType].map(item => item.value),
            fill: false,
            borderColor: '#4caf50',
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            annotation: {
              annotations: [
                {
                  type: 'line',
                  mode: 'horizontal',
                  scaleID: 'y',
                  value: thresholds ? thresholds.min : null,
                  borderColor: 'rgba(0, 255, 0, 0.5)',
                  borderDash: [10, 5],
                  borderWidth: 2,
                  label: {
                    content: 'Min',
                    enabled: true,
                    position: 'end',
                    backgroundColor: 'rgba(0, 255, 0, 0.5)',
                    font: { size: 10 },
                  },
                },
                {
                  type: 'line',
                  mode: 'horizontal',
                  scaleID: 'y',
                  value: thresholds ? thresholds.max : null,
                  borderColor: 'rgba(255, 0, 0, 0.5)',
                  borderDash: [10, 5],
                  borderWidth: 2,
                  label: {
                    content: 'Max',
                    enabled: true,
                    position: 'end',
                    backgroundColor: 'rgba(255, 0, 0, 0.5)',
                    font: { size: 10 },
                  },
                }
              ]
            }
          }
        }
      });
    },
    refreshPage() {
      window.location.reload();
    },
    async fetchSensors() {
      const response = await api.getActiveSensors();
      this.sensors = response.data;
      this.sensors.sort((a, b) => a.name.localeCompare(b.name));
      this.sensors.forEach(sensor => {
        this.selectedData[sensor.sensor_id] = 'Temperature';
        this.initChart(sensor.sensor_id, 'Temperature');
        this.fetchSensorStatus(sensor.sensor_id);
        this.fetchSensorThresholds(sensor.sensor_id);
      });
    },
    async fetchSensorStatus(sensorId) {
      const response = await api.getSensorStatus(sensorId);
      if (response.data && response.data.status) {
        this.sensorStatuses[sensorId] = response.data.status;
      } else {
        this.sensorStatuses[sensorId] = 'disabled';
      }
    },
    async fetchSensorThresholds(sensorId) {
      const response = await api.getSensorThresholds(sensorId);
      if (response.data && response.data.thresholds) {
        this.thresholds[sensorId] = response.data.thresholds;
        this.newThresholds = JSON.parse(JSON.stringify(this.thresholds));
      }
    },
    async fetchSensorData(sensorId, dataType) {
      const endTime = new Date().toISOString();
      const startTime = new Date(new Date().getTime() - 6 * 60 * 1000).toISOString();
      const response = await api.queryHistoricalData(sensorId, startTime, endTime);

      if (!response.data) return [];

      const dataMap = {
        'Temperature': response.data.temperature,
        'Humidity': response.data.humidity,
        'CO2 Concentration': response.data.co2,
      };
      return dataMap[dataType] || [];
    },
    async initChart(sensorId, dataType) {
      await nextTick();
      const ctx = document.getElementById(`chart-${sensorId}`);
      if (!ctx) return;
      const data = await this.fetchSensorData(sensorId, dataType);
      if (this.charts[sensorId]) {
        this.charts[sensorId].destroy();
      }
      const thresholds = this.thresholds[sensorId] ? this.thresholds[sensorId][dataType] : null;
      this.charts[sensorId] = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
          labels: data.map(item => new Date(item.timestamp).toLocaleTimeString()),
          datasets: [{
            label: dataType,
            data: data.map(item => item.value),
            fill: false,
            borderColor: '#4caf50',
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            annotation: {
              annotations: [
                {
                  type: 'line',
                  mode: 'horizontal',
                  scaleID: 'y',
                  value: thresholds ? thresholds.min : null,
                  borderColor: 'rgba(0, 255, 0, 0.5)',
                  borderDash: [10, 5],
                  borderWidth: 2,
                  label: {
                    content: 'Min',
                    enabled: true,
                    position: 'end',
                    backgroundColor: 'rgba(0, 255, 0, 0.5)',
                    font: { size: 10 },
                  },
                },
                {
                  type: 'line',
                  mode: 'horizontal',
                  scaleID: 'y',
                  value: thresholds ? thresholds.max : null,
                  borderColor: 'rgba(255, 0, 0, 0.5)',
                  borderDash: [10, 5],
                  borderWidth: 2,
                  label: {
                    content: 'Max',
                    enabled: true,
                    position: 'end',
                    backgroundColor: 'rgba(255, 0, 0, 0.5)',
                    font: { size: 10 },
                  },
                }
              ]
            }
          }
        }
      });
    },
    async refreshCharts() {
      for (const sensor of this.sensors) {
        const dataType = this.selectedData[sensor.sensor_id];
        const data = await this.fetchSensorData(sensor.sensor_id, dataType);
        if (data.length > 0) {
          this.updateChart(sensor.sensor_id, data, dataType);
        }
      }
    },
    updateChart(sensorId, data, dataType) {
      const chart = this.charts[sensorId];
      if (!chart) return;
      chart.data.labels = data.map(item => new Date(item.timestamp).toLocaleTimeString());
      chart.data.datasets[0].data = data.map(item => item.value);
      chart.data.datasets[0].label = dataType;
      const thresholds = this.thresholds[sensorId] ? this.thresholds[sensorId][dataType] : null;
      if (chart.options.plugins.annotation.annotations[0]) {
        chart.options.plugins.annotation.annotations[0].value = thresholds ? thresholds.min : null;
      }
      if (chart.options.plugins.annotation.annotations[1]) {
        chart.options.plugins.annotation.annotations[1].value = thresholds ? thresholds.max : null;
      }
      chart.update();
    },
    changeDataType(sensorId, dataType) {
      this.selectedData[sensorId] = dataType;
      this.initChart(sensorId, dataType);
    },
    openThresholdDialog(sensorId) {
      this.currentSensorId = sensorId;
      this.newThresholds = JSON.parse(JSON.stringify(this.thresholds[sensorId]));
      this.showThresholdDialog = true;
    },
    closeThresholdDialog() {
      this.showThresholdDialog = false;
    },
    async updateThresholds() {
      try {
        await api.updateSensorThresholds(this.currentSensorId, this.newThresholds);
        this.thresholds[this.currentSensorId] = JSON.parse(JSON.stringify(this.newThresholds));
        this.closeThresholdDialog();
      } catch (error) {
        console.error('Failed to update thresholds:', error);
      }
    },
    startAutoRefresh() {
      this.autoRefreshInterval = setInterval(this.refreshCharts, 5000);
    },
    stopAutoRefresh() {
      clearInterval(this.autoRefreshInterval);
    },
  },
  mounted() {
    this.fetchSensors();
    this.startAutoRefresh();
  },
  beforeUnmount() {
    this.stopAutoRefresh();
  },
};
</script>

<style scoped>
.sensor-grid-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.sensor-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(250px, 1fr));

  gap: 20px;
  justify-content: center;
}

@media (max-width: 900px) {
  .sensor-grid {
    grid-template-columns: repeat(2, minmax(200px, 1fr));
  }
}

@media (max-width: 600px) {
  .sensor-grid {
    grid-template-columns: 1fr;

  }
}

.sensor-card {
  background-color: #1a1a1a;
  border: 1px solid #e0e0e0;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  transform: scale(0.9);
  transition: transform 0.2s ease;
}

.sensor-card:hover {
  transform: scale(1.02);
}

.status-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: gray;
}

.status-dot.normal {
  background-color: #00ff00;
}

.status-dot.warning {
  background-color: #ffeb3b;
}

.status-dot.offline {
  background-color: #f44336;
}

.status-dot.disabled {
  background-color: #9e9e9e;
}

.sensor-info {
  margin-bottom: 5px;
  text-align: center;
  color: white;
}

.sensor-chart {
  position: relative;
  width: 100%;
  height: 150px;
}

canvas {
  width: 100%;
  height: 100%;
}

.capsule-buttons {
  margin-top: 5px;
  justify-content: space-evenly;
  gap: 5px;
  width: 100%;
}

.capsule-buttons button {
  padding: 3px 10px;
  border-radius: 12px;
  background-color: #33c3d9bb;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 0.75rem;
}

.capsule-buttons button.active {
  background-color: #1976d2;
}

.modify-threshold {
  margin-top: 10px;
}

.modify-threshold button {
  padding: 5px 12px;
  border-radius: 12px;
  background-color: #ffffff28;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 0.8rem;
}

.modal {
  display: flex;
  justify-content: center;
  align-items: center;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
}

.modal-content {
  background-color: #1a1a1a;
  padding: 20px;
  border-radius: 8px;
  color: white;
  width: 80%;
  max-width: 900px;
  height: auto;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.input-group {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.input-group label {
  margin-right: 10px;
}

.input-group input {
  width: 80px;
  padding: 5px;
  background-color: #333;
  border: 1px solid #555;
  color: white;
}

.dialog-buttons {
  display: flex;
  justify-content: space-between;
}

.dialog-buttons button {
  padding: 5px 10px;
  background-color: #1e88e5;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.refresh-button {
  position: absolute;
  top: 20px;
  right: 20px;
  background: none;
  border: none;
  cursor: pointer;
}

.refresh-button img {
  width: 20px;
  height: 20px;
}

.history-modal {
  width: 100%;
  height: auto;
}

.date-picker {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  align-items: center;
}

.date-picker label {
  margin-right: 10px;
}

.date-picker input {
  padding: 5px;
  margin-right: 10px;
  background-color: #333;
  border: 1px solid #555;
  color: white;
  border-radius: 5px;
}

.date-picker button {
  padding: 6px 12px;
  background-color: #1e88e5;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.history-chart {
  width: 90%;
  height: 70%;
}

.dialog-buttons {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.dialog-buttons button {
  padding: 5px 10px;
  background-color: #1e88e5;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin-left: 10px;
}

.query-history {
  margin-top: 5px;
}

.query-history button {
  padding: 5px 12px;
  border-radius: 12px;
  color: white;
  background-color: #ffffff28;
  cursor: pointer;
  font-size: 0.8rem;
  margin-top: 5px;
  margin-bottom: 5px;
}

@media (max-width: 600px) {
  .modal-content {
    width: 90%;
    padding: 15px;
  }

  .date-picker {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }

  .date-picker label,
  .date-picker input {
    width: 100%;
    margin-bottom: 10px;
  }

  .date-picker button {
    width: 100%;
    padding: 10px;
  }

  .history-chart {
    width: 100%;
    height: 300px;
    margin-bottom: 20px;
  }

  .dialog-buttons {
    flex-direction: column;
    width: 100%;
  }

  .dialog-buttons button {
    width: 100%;
    margin-left: 0;
    margin-bottom: 10px;
  }
}
</style>

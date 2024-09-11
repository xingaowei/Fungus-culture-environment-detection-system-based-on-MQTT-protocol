<template>
  <div class="grid-item">
    <div class="sensor-overview">
      <h5>Sensor Status Overview</h5>
      <canvas id="sensorPieChart"></canvas>
      <div class="controls">
        <button @click="fetchData">Refresh</button>
        <label for="auto-refresh">
          <input type="checkbox" id="auto-refresh" v-model="autoRefresh" />
          Auto-refresh every 3s
        </label>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useSensorPieChart } from '@/composables/useSensorPieChart';

export default {
  setup() {
    const autoRefresh = ref(false);
    const { fetchData, toggleAutoRefresh } = useSensorPieChart(autoRefresh);

    return {
      autoRefresh,
      fetchData,
      toggleAutoRefresh,
    };
  },
};
</script>

<style scoped>
.grid-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  padding: 20px;
}

.grid-item {
  background-color: #f4f4f400;
  border: 1px solid #eaf399c8;
  padding: 20px;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

@media (max-width: 900px) {
  .grid-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .grid-container {
    grid-template-columns: 1fr;
  }
}

.sensor-overview {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 70%;
}

.controls {
  margin-top: 10px;
}

canvas {
  max-width: 100%;
  height: auto;
}
</style>

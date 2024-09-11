// src/composables/useSensorPieChart.js

import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import Chart from 'chart.js/auto';
import api from '@/api';

export function useSensorPieChart(autoRefresh) {
    const chart = ref(null);
    const refreshInterval = ref(null);

    const fetchData = () => {
        api.getSensorStatusSummary().then((response) => {
            const data = response.data;
            updateChart([data.normal, data.warning, data.offline, data.disabled]);
        });
    };

    const updateChart = (data) => {
        if (chart.value) {
            chart.value.destroy();
        }
        const ctx = document.getElementById('sensorPieChart').getContext('2d');
        chart.value = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Normal', 'Warning', 'Offline', 'Disabled'],
                datasets: [
                    {
                        label: 'Sensor Status',
                        data: data,
                        backgroundColor: ['#4caf50', '#ff9800', '#f44336', '#9e9e9e'],
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
            },
        });
    };

    const toggleAutoRefresh = () => {
        if (autoRefresh.value) {
            refreshInterval.value = setInterval(fetchData, 3000);
        } else {
            clearInterval(refreshInterval.value);
            refreshInterval.value = null;
        }
    };

    onMounted(() => {
        fetchData();
        if (autoRefresh.value) {
            refreshInterval.value = setInterval(fetchData, 3000);
        }
    });

    onBeforeUnmount(() => {
        if (refreshInterval.value) {
            clearInterval(refreshInterval.value);
        }
        if (chart.value) {
            chart.value.destroy();
        }
    });

    watch(autoRefresh, () => {
        toggleAutoRefresh();
    });

    return {
        fetchData,
        toggleAutoRefresh,
    };
}

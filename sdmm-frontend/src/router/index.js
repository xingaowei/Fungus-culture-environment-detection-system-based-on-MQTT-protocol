// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '../views/Dashboard.vue';
import Sensors from '../views/Sensors.vue';
import Subscriptions from '../views/Subscriptions.vue';
import Alerts from '../views/Alerts.vue';

const routes = [
  { path: '/', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
  { path: '/sensors', name: 'Sensors', component: () => import('../views/Sensors.vue') },
  { path: '/subscriptions', name: 'Subscriptions', component: () => import('../views/Subscriptions.vue') },
  { path: '/alerts', name: 'Alerts', component: () => import('../views/Alerts.vue') },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;

<!-- App.vue -->

<template>
  <div>
    <nav role="navigation" aria-label="Main Navigation">
      <router-link to="/">Dashboard</router-link>
      <router-link to="/sensors">Sensors</router-link>
      <router-link to="/subscriptions">Subscriptions</router-link>
      <router-link to="/alerts">Alerts</router-link>
    </nav>
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
};
</script>

<style>
nav {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
  background-color: #282c34;
}

nav a {
  margin: 0 10px;
  color: white;
  text-decoration: none;
}

nav a.router-link-exact-active {
  font-weight: bold;
  color: #61dafb;
}

@media (max-width: 600px) {
  nav {
    flex-direction: column;
    padding: 10px;
  }

  nav a {
    margin: 5px 0;
    font-size: 1.2em;
  }
}

@media (max-width: 400px) {
  nav {
    padding: 5px;
  }

  nav a {
    font-size: 1em;
  }
}
</style>

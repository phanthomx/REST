<script setup>
// No logic needed here yet
</script>

<template>
  <div style="text-align: center; margin-top: 50px;">
    <h1>Welcome to the App</h1>
    <p>Please login or register to continue</p>
    
    <div style="margin-top: 20px;">
      <router-link to="/login" style="margin-right: 10px; padding: 10px 20px; background: #42b983; color: white; text-decoration: none; border-radius: 5px;">
        Login
      </router-link>
      
      <router-link to="/register" style="padding: 10px 20px; background: #35495e; color: white; text-decoration: none; border-radius: 5px;">
        Register
      </router-link>
    </div>
  </div>
</template>
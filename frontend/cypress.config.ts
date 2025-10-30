import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://127.0.0.1:4200',
    specPattern: 'cypress/e2e/**/*spec.{js,jsx,ts,tsx}',
    supportFile: 'cypress/support/geonatureLogin.js',
  },
  env: {
    login_url: '/login',
    products_url: '/products',
    apiEndpoint: 'http://localhost:8000/',
  },
});

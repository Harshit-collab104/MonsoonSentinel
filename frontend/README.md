# Monsoon Sentinel — Frontend Application

Production-ready React 19 single-page application (SPA) bundled with Vite 8 and Tailwind CSS v4, built for autonomous municipal flood management and response coordination.

---

## Features

- **Autonomous Agent Console**: Strands Agent dispatch console with deterministic risk reasoning.
- **Geospatial GIS Map**: Interactive Leaflet-powered GIS hydrological view showing municipal wards, water depth telemetry, and incident markers.
- **Human Approval Queue**: Supervisor review interface for municipal dispatch authorization.
- **Private Photographic Evidence**: Citizen and field crew evidence upload directly attached to DynamoDB incident records via AWS S3 presigned URLs.
- **Deterministic Verification**: Culvert post-clearance telemetry verification.

---

## Local Development

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start Vite development server:**
   ```bash
   npm run dev
   ```
   By default, local requests to `/api/v1` are proxied to `http://localhost:8000` via Vite's local dev server proxy configured in `vite.config.js`.

3. **Lint & Build:**
   ```bash
   npm run lint
   npm run build
   ```

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `VITE_API_BASE_URL` | Base URL of the deployed backend API Gateway | `https://<api-id>.execute-api.ap-south-1.amazonaws.com/Prod` |

- For local development, leave `VITE_API_BASE_URL` empty in `.env.development` to leverage the local proxy.
- For production deployments (AWS Amplify, Vercel, Netlify), set `VITE_API_BASE_URL` in the hosting provider's environment variables.

---

## AWS Amplify Hosting

The frontend is configured for deployment on **AWS Amplify Hosting**:

- **Build specification:** Defined in `amplify.yml` (and `frontend/amplify.yml`).
- **Base directory:** `frontend` (or repository root using root `amplify.yml`).
- **Output directory:** `dist`
- **SPA Rewrites:** All paths rewrite to `/index.html` (status 200).

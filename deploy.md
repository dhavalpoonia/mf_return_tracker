# Deployment Guide: MF Performance Analyzer

This guide provides step-by-step instructions to deploy the **MF Performance Analyzer** for full, stable execution.

## 1. Prepare Your Repository
Ensure your codebase is clean and pushed to a GitHub repository.

1. Create a new repository on [GitHub](https://github.com/new).
2. Initialize and push your code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/mf-compare.git
   git branch -M main
   git push -u origin main
   ```

## 2. Deploy to Streamlit Community Cloud (Recommended)
Streamlit Community Cloud is the easiest way to deploy this app for free.

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **"New app"**.
3. Select your repository (`mf-compare`), the branch (`main`), and the main file path (`app.py`).
4. Click **"Deploy!"**.

## 3. Configure Secrets (Gemini API Key)
To enable the AI Analysis without typing the API key every time:

1. In your Streamlit Cloud dashboard, find your app and click the **three dots (...)** -> **Settings**.
2. Go to the **Secrets** tab.
3. Paste the following (replace with your actual key):
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key_here"
   ```
4. Click **Save**. The app will automatically restart and detect the key.

## 4. Stability & Performance Tips
- **Caching**: The app uses `st.cache_data` for NAV history. This minimizes API calls and speeds up the UI.
- **Error Handling**: The app gracefully handles missing data from `yfinance` or `mfapi.in`.
- **API Limits**:
  - `mfapi.in`: Generally very stable with no strict limits.
  - `yfinance`: May occasionally hit rate limits on shared cloud IPs. If charts fail to load, wait a few minutes and refresh.
  - `Gemini`: Free tier has rate limits (RPM/TPM). The dual-agent approach makes 2-3 calls per analysis.

## 5. Alternative: Deploy with Docker
If you want to host it on your own server (AWS, GCP, DigitalOcean):

1. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install --no-cache-dir -r requirements.txt
   EXPOSE 8501
   HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
   ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```
2. Build and run:
   ```bash
   docker build -t mf-analyzer .
   docker run -p 8501:8501 mf-analyzer
   ```

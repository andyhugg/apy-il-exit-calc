# Crypto Risk Analyzer

## Deployment on Render.com

1. **Fork this repository** to your GitHub account.
2. **Create a new Web Service** on Render.com:
   - Connect your GitHub repository.
   - Set the runtime to `Python`.
   - Set the build command to: `pip install -r requirements.txt`.
   - Set the start command to: `streamlit run arta-kombinasi.py --server.port $PORT --server.address 0.0.0.0`.
3. **Deploy**: Render.com will build and deploy the app.
4. **Access**: Once deployed, access the app via the provided URL.

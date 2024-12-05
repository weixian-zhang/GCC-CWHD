# --- Stage 1: Build Stage ---
    FROM python:3.11-slim AS builder

    # Set working directory
    WORKDIR /app
    
    # Copy only requirements to install dependencies
    COPY requirements.txt .
    
    # Install dependencies in a temporary directory
    RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
    
    
    # --- Stage 2: Runtime Stage ---
    FROM python:3.11-slim

    ENV HealthStatusThreshold='{     "metricUsageThreshold": {         "vm": {             "cpuUsagePercentage": 80,             "memoryUsagePercentage": 80,             "diskUsagePercentage": 80         }     } }'
    ENV APPLICATIONINSIGHTS_CONNECTION_STRING=''

    # Set working directory
    WORKDIR /app
    
    # Copy dependencies from the builder stage
    COPY --from=builder /install /usr/local
    
    # Copy application code
    COPY . .
    
    # Expose the port FastAPI will run on
    EXPOSE 8000
    
    # Run FastAPI with Uvicorn
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    
# syntax=docker/dockerfile:1
FROM --platform=$TARGETPLATFORM python:3.13-slim

# Build arguments
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Labels
LABEL org.opencontainers.image.title="MistOrgLicensingComparison"
LABEL org.opencontainers.image.description="Mist Organization Licensing Comparison Tool"
LABEL org.opencontainers.image.source="https://github.com/jmorrison-juniper/MistOrgLicensingComparison"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py mist_connection.py ./
COPY templates/ templates/

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "app:app"]

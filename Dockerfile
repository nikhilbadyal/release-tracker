FROM python:slim

# Create a non-privileged user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

# Change ownership of the app directory to the non-privileged user
RUN chown -R appuser:appuser /app

# Switch to the non-privileged user
USER appuser

ENTRYPOINT ["python", "main.py"]

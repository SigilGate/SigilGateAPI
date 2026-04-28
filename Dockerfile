FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY sigilgateapp/ sigilgateapp/
RUN pip install --no-cache-dir .
USER 1000:1000
EXPOSE 8000
CMD ["sigilgateapp", "serve"]

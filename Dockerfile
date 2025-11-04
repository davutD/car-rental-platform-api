FROM python:3.13-slim

WORKDIR /app

ARG APP_PORT=5005
ENV APP_PORT=${APP_PORT}

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE ${APP_PORT}

CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${APP_PORT} app.app:create_app"]

# Production image for the nanny portal.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN addgroup --system app \
    && adduser --system --ingroup app app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
# A throwaway key is enough for collectstatic; real secrets come from the environment at runtime.
RUN SECRET_KEY=collectstatic-only python manage.py collectstatic --noinput

USER app

EXPOSE 8000

# Use a production WSGI server; never run Django's development server here.
CMD ["gunicorn", "mysite.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

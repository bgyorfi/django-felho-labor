# Használj egy stabil Python alapot
FROM python:3.10-slim

# Környezeti változók
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Port, amin a Gunicorn figyelni fog (az EXPOSE csak dokumentáció)
ENV PORT=8000
EXPOSE 8000

# Munkakönyvtár
WORKDIR /app

# Függőségek telepítése
# Először csak a requirements.txt-t másoljuk, hogy a Docker cache-t ki tudjuk használni
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Teljes alkalmazáskód másolása
COPY . /app/

# Statikus fájlok összegyűjtése (Whitenoise-hoz)
# A SECRET_KEY env var szükséges lehet, adjunk neki egy dummy defaultot a settings.py-ban
RUN python manage.py collectstatic --noinput

# Konténer indítási parancsa (Gunicorn használata productionben)
# Az OpenShift S2I is általában Gunicornot használ, Dockerfile stratégiánál nekünk kell megadni
CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "photoalbum.wsgi:application"]
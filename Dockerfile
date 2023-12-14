FROM python:3.11.0-slim-bullseye

RUN apt-get update && apt-get -y install cron
# Install python dependencies
RUN mkdir /google_sync
COPY requirements_sync.txt /google_sync
RUN pip install -r /google_sync/requirements_sync.txt
# Copy hello-cron file to the cron.d directory
COPY cron-file /etc/cron.d/
# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cron-file
# Apply cron job
RUN crontab /etc/cron.d/cron-file

# Copy application
COPY sync_sheet_to_calendar.py token.pickle sheets.googleapis.com-python.json client_secret_616621345489-h4bc2astbq7lbmdbda7eqa5cpmm64fv8.apps.googleusercontent.com.json /google_sync
# Give execution rights on the cron job
RUN chmod 0744 /google_sync/sync_sheet_to_calendar.py
# Start the cron job
CMD ["cron", "-f"]
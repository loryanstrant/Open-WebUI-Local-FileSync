#!/bin/bash
set -e

# Default values
TZ=${TZ:-UTC}
SYNC_SCHEDULE=${SYNC_SCHEDULE:-daily}
SYNC_TIME=${SYNC_TIME:-00:00}
SYNC_DAY=${SYNC_DAY:-*}

# Set timezone
echo "Setting timezone to: $TZ"
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
echo $TZ > /etc/timezone

# Parse time
IFS=':' read -r HOUR MINUTE <<< "$SYNC_TIME"
HOUR=${HOUR:-0}
MINUTE=${MINUTE:-0}

# Build cron schedule based on SYNC_SCHEDULE
case "$SYNC_SCHEDULE" in
    hourly)
        CRON_SCHEDULE="$MINUTE * * * *"
        ;;
    daily)
        CRON_SCHEDULE="$MINUTE $HOUR * * *"
        ;;
    weekly)
        # Parse day of week (0-6, 0=Sunday, or mon, tue, etc.)
        if [[ "$SYNC_DAY" =~ ^[0-6]$ ]] || [[ "$SYNC_DAY" =~ ^(mon|tue|wed|thu|fri|sat|sun)$ ]]; then
            CRON_SCHEDULE="$MINUTE $HOUR * * $SYNC_DAY"
        else
            echo "Invalid SYNC_DAY: $SYNC_DAY (must be 0-6 or mon,tue,wed,thu,fri,sat,sun)"
            echo "Defaulting to Sunday (0)"
            CRON_SCHEDULE="$MINUTE $HOUR * * 0"
        fi
        ;;
    *)
        echo "Invalid SYNC_SCHEDULE: $SYNC_SCHEDULE"
        echo "Valid options: hourly, daily, weekly"
        exit 1
        ;;
esac

echo "Configuring sync schedule: $CRON_SCHEDULE ($SYNC_SCHEDULE at $SYNC_TIME)"

# Create cron job
CRON_JOB="$CRON_SCHEDULE /usr/local/bin/python3 /app/sync.py >> /proc/1/fd/1 2>&1"
echo "$CRON_JOB" > /etc/cron.d/filesync
chmod 0644 /etc/cron.d/filesync

# Apply cron job
crontab /etc/cron.d/filesync

# Run initial sync
echo "Running initial sync..."
/usr/local/bin/python3 /app/sync.py

# Start cron in foreground
echo "Starting cron daemon..."
exec cron -f

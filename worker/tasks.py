from celery import Celery
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import redis
import json
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Celery app
app = Celery('tasks', broker=os.getenv('REDIS_URL', 'redis://redis:6379/0'))

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis client for alerts
redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

# Email config
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


@app.task
def send_alert_email(website_id, url, owner_email):
    """Send email alert about website being down"""

    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = owner_email
    msg['Subject'] = f"⚠️ ALERT: Your website {url} is DOWN!"

    body = f"""
    <html>
        <body>
            <h2>⚠️ Website Down Alert</h2>
            <p>Your website <strong>{url}</strong> is currently down.</p>
            <p>Time: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Please check your website as soon as possible.</p>
            <hr>
            <p>This is an automated message from Uptime Monitor.</p>
        </body>
    </html>
    """

    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Alert sent for {url}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def process_alerts():
    """Listen for alerts from Redis and trigger emails"""
    print("Alert worker started...")

    while True:
        try:
            # Wait for alerts
            alert_data = redis_client.blpop("alert_queue", timeout=0)
            if alert_data:
                alert = json.loads(alert_data[1])

                # Get website owner's email
                db = SessionLocal()
                result = db.execute(
                    "SELECT users.email FROM users JOIN websites ON users.id = websites.owner_id WHERE websites.id = :website_id",
                    {"website_id": alert["website_id"]}
                ).first()
                db.close()

                if result:
                    # Send email asynchronously
                    send_alert_email.delay(
                        alert["website_id"],
                        alert["url"],
                        result[0]
                    )
        except Exception as e:
            print(f"Error processing alert: {e}")
            time.sleep(1)


if __name__ == "__main__":
    process_alerts()
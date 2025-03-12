from flask import Flask, render_template, request, redirect, url_for, jsonify
from task_manager import TaskManager
import os
import threading
import logging

app = Flask(__name__)
manager = TaskManager()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scheduler():
    manager.start_scheduler()

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
scheduler_thread.start()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        task_type = request.form.get("task_type")
        interval = int(request.form.get("interval"))
        unit = request.form.get("unit")

        if task_type == "organize_files":
            directory = request.form.get("directory")
            manager.add_task(interval, unit, task_type, directory=directory)

        elif task_type == "delete_files":
            directory = request.form.get("directory")
            age_days = int(request.form.get("age_days"))
            formats = request.form.get("formats").split(",")
            manager.add_task(interval, unit, task_type, directory=directory, age_days=age_days, formats=formats)

        elif task_type == "send_email":
            recipient_file = request.files.get("recipient_file")
            recipient_emails = []

            if recipient_file:
                # Read the file and extract email addresses
                for line in recipient_file.readlines():
                    line = line.strip().decode('utf-8')
                    if "," in line:
                        # Split the line into name and email
                        _, email = line.split(",", 1)
                        recipient_emails.append(email.strip())
                    else:
                        # Assume the entire line is an email address
                        recipient_emails.append(line.strip())
            else:
                recipient_email = request.form.get("recipient_email")
                if recipient_email:
                    recipient_emails = [recipient_email.strip()]

            subject = request.form.get("subject")

            message_file = request.files.get("message_file")
            message = ""
            if message_file:
                message_bytes = message_file.read()
                if message_bytes:
                    try:
                        message = message_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        message = message_bytes.decode('latin-1', errors='replace')
            else:
                message = request.form.get("message")

            attachments = request.files.getlist("attachments")
            attachment_paths = []

            upload_dir = "uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            for attachment in attachments:
                if attachment.filename:
                    try:
                        filepath = os.path.join(upload_dir, attachment.filename)
                        attachment.save(filepath)
                        attachment_paths.append(filepath)
                    except Exception as e:
                        logger.error(f"Failed to save attachment: {e}")

            # Log the email details
            logger.info(f"Recipient Emails: {recipient_emails}")
            logger.info(f"Subject: {subject}")
            logger.info(f"Message: {message}")
            logger.info(f"Attachments: {attachment_paths}")

            # Pass recipient_emails as a list to the manager
            manager.add_task(
                interval,
                unit,
                task_type,
                recipient_email=recipient_emails,  # Pass as a list
                subject=subject,
                message=message,
                attachments=attachment_paths,
            )

        elif task_type == "get_gold_rate":
            manager.add_task(interval, unit, task_type)

        elif task_type == "convert_file":
            input_dir = request.form.get("input_dir")
            output_dir = request.form.get("output_dir")
            input_format = request.form.get("input_format")
            output_format = request.form.get("output_format")
            manager.add_task(
                interval,
                unit,
                task_type,
                input_dir=input_dir,
                output_dir=output_dir,
                input_format=input_format,
                output_format=output_format,
            )

        elif task_type == "compress_files":
            directory = request.form.get("directory")
            output_dir = request.form.get("output_dir")
            compression_format = request.form.get("compression_format")
            manager.add_task(
                interval,
                unit,
                task_type,
                directory=directory,
                output_dir=output_dir,
                compression_format=compression_format,
            )

        return redirect(url_for("index"))

    tasks = manager.load_tasks()
    return render_template("index.html", tasks=tasks)

@app.route("/remove_task/", methods=["GET"])
def remove_task():
    task_name = request.args.get("task_name")
    if task_name:
        manager.remove_task(task_name)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=False)
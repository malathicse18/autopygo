# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from task_manager import TaskManager
import os
import threading

app = Flask(__name__)
manager = TaskManager()

def start_scheduler():
    manager.start_scheduler()

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
            recipient_email = request.form.get("recipient_email")
            subject = request.form.get("subject")
            message = request.form.get("message")
            attachments = request.files.getlist("attachments")
            attachment_paths = []
            for attachment in attachments:
                if attachment.filename:
                    filepath = os.path.join("uploads", attachment.filename)
                    attachment.save(filepath)
                    attachment_paths.append(filepath)
            manager.add_task(interval, unit, task_type, recipient_email=recipient_email, subject=subject, message=message, attachments=attachment_paths)
        elif task_type == "get_gold_rate":
            manager.add_task(interval, unit, task_type)
        elif task_type == "convert_file":
            input_dir = request.form.get("input_dir")
            output_dir = request.form.get("output_dir")
            input_format = request.form.get("input_format")
            output_format = request.form.get("output_format")
            manager.add_task(interval, unit, task_type, input_dir=input_dir, output_dir=output_dir, input_format=input_format, output_format=output_format)
        elif task_type == "compress_files":
            directory = request.form.get("directory")
            output_dir = request.form.get("output_dir")
            compression_format = request.form.get("compression_format")
            manager.add_task(interval, unit, task_type, directory=directory, output_dir=output_dir, compression_format=compression_format)

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
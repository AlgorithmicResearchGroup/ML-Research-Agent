import json
import os
import sys
import numpy as np
import time
import flask
import random
from flask import request, jsonify
from agent.supervisor import Supervisor
from agent.task import TaskFamily

app = flask.Flask(__name__)

@app.route('/')
def index():
    return render_response('index.html')

#keep alive route
@app.route('/run', methods=['POST'])
def run():
    data = request.get_json()
    task_number = data['task_number']
    user_id = data['user_id']
    run_id = random.getrandbits(32)
    
    start_time = time.time()
    
    print(f"Running task number: {task_number}")

    tasks = TaskFamily.get_tasks()
    
    task_name = list(tasks.keys())[int(task_number)]
    task = list(tasks.values())[int(task_number)]
    
    
    print(f"Running task: {task['prompt']}")
    
    supervisor = Supervisor()
    output = supervisor.run(task['prompt'])
    
    end_time = time.time()
    
    print(f"Task {task['prompt']} completed in {end_time - start_time} seconds.")
    print(f"Or in minutes: {(end_time - start_time) / 60} minutes")
    print(f"Or in hours: {(end_time - start_time) / 3600} hours")
    print("FINAL OUTPUT: ", output)
    
    return jsonify({"output": output})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
from flask import Flask
import os
import time
from datetime import datetime
import subprocess

app = Flask(__name__)

@app.route('/htop')
def htop():
    # Get system username
    username = os.getlogin()
    # Get current server time in IST
    server_time = datetime.now().astimezone(timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
    # Get top command output
    top_output = subprocess.check_output(['top', '-bn', '1']).decode('utf-8')

    return f"""
    <h1>System Information</h1>
    <p><strong>Name:</strong>Chappidi Chidroopa Chaitanya</p>
    <p><strong>Username:</strong> {username}</p>
    <p><strong>Server Time (IST):</strong> {server_time}</p>
    <h2>Top Output:</h2>
    <pre>{top_output}</pre>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

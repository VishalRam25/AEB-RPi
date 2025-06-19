import RPi.GPIO as GPIO
from flask import Flask, render_template, jsonify

# Set up the Flask app
app = Flask(__name__)

# Set up the GPIO mode and pins
GPIO.setmode(GPIO.BCM)

# Define GPIO pins
pins = {
    "light1": 17,
    "light2": 27,
    "fan1": 22,
    "fan2": 23,
    "ac": 24,
    "vehicle": 25
}

# Set all pins as output
for pin in pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)  # Initially turn off

# Route to render the control page
@app.route('/')
def index():
    return render_template('index.html')

# Route to toggle device state
@app.route('/toggle/<device>')
def toggle_device(device):
    if device in pins:
        current_state = GPIO.input(pins[device])
        new_state = GPIO.HIGH if current_state == GPIO.LOW else GPIO.LOW
        GPIO.output(pins[device], new_state)
        return jsonify({"state": "on" if new_state == GPIO.HIGH else "off"})
    return jsonify({"error": "Invalid device"}), 404

# Shutdown route to cleanup GPIO
@app.route('/shutdown')
def shutdown():
    GPIO.cleanup()
    return "GPIO cleaned up!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

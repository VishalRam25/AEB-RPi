import serial
import RPi.GPIO as GPIO
import time
from collections import Counter

# TF02 Pro serial setup (replace with your actual serial port)
tf_serial = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

# Relay pins setup (BCM mode)
relay1 = 17
relay2 = 18
limit_switch = 27

# Buffer for stable distance readings
distances = [0] * 10  # Buffer size of 10
index = 0
brake_activated = False
last_read_time = 0

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(relay1, GPIO.OUT)
    GPIO.setup(relay2, GPIO.OUT)
    GPIO.setup(limit_switch, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Initialize relays as off (assuming active-low)
    GPIO.output(relay1, GPIO.HIGH)
    GPIO.output(relay2, GPIO.HIGH)

    print("System Initialized...")

def read_distance():
    while tf_serial.in_waiting > 0:
        buffer = tf_serial.read(9)
        
        if len(buffer) == 9 and buffer[0] == 0x59 and buffer[1] == 0x59:
            distance_cm = buffer[2] + (buffer[3] * 256)
            return distance_cm
    return None

def apply_brake():
    # Step 1: Apply brake (motor forward)
    GPIO.output(relay1, GPIO.LOW)
    GPIO.output(relay2, GPIO.HIGH)
    print("Motor Forward (Brake Applied)")
    time.sleep(2.5)  # Actuator presses brake

    # Step 2: Cut power and hold position
    GPIO.output(relay1, GPIO.HIGH)
    GPIO.output(relay2, GPIO.HIGH)
    print("Motor Power Off (Brake Held)")
    time.sleep(2)  # Hold brake for 2 seconds

    # Step 3: Release brake (motor reverse)
    GPIO.output(relay1, GPIO.HIGH)
    GPIO.output(relay2, GPIO.LOW)
    print("Motor Reverse (Brake Releasing)")

    # Step 4: Wait for limit switch or timeout
    start_time = time.time()
    while GPIO.input(limit_switch) == GPIO.HIGH:
        if time.time() - start_time > 3:  # Safety timeout
            print("⚠️ Timeout: Limit switch not triggered!")
            break

    # Step 5: Stop motor
    GPIO.output(relay1, GPIO.HIGH)
    GPIO.output(relay2, GPIO.HIGH)
    print("Motor Stopped (Brake Fully Released)")

def most_frequent(arr):
    """Function to get the most frequent element in a list."""
    return Counter(arr).most_common(1)[0][0]

def main():
    global index, brake_activated, last_read_time

    setup()

    try:
        while True:
            # Read distance from TF02 Pro sensor
            distance_cm = read_distance()
            if distance_cm is not None:
                # Store distance reading in the buffer
                distances[index] = distance_cm
                index = (index + 1) % 10

                # Stable distance reading logic (every 2 seconds)
                if time.time() - last_read_time > 2:
                    stable_cm = most_frequent(distances)
                    stable_m = stable_cm / 100.0  # Convert cm to meters

                    print(f"Distance between vehicles: {stable_m:.2f} m")

                    # Emergency Brake Logic
                    if stable_cm < 150 and not brake_activated:
                        print(f"⚠️ Emergency Brake Activated — Distance: {stable_m:.2f} m")
                        apply_brake()
                        brake_activated = True
                    elif stable_cm > 180 and brake_activated:
                        brake_activated = False
                        print("✅ Safe distance restored — system reset")

                    last_read_time = time.time()

            time.sleep(0.1)  # Slight delay to avoid overwhelming the serial port

    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()

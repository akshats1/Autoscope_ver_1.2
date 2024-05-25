from flask import Flask, render_template, Response,jsonify,request
import time
import io
import threading
import PIL.Image
#from camera_update_new import Camera 
#from camera_update_nn import Camera 
from camera_update_new import Camera 
#from camera_update_new_resolution import Camera # Import your Camera class
import atexit
from datetime import datetime
from motor_move import Motor
import serial
from movement import movexclock, movexanticlock, movey, moveycc,movezclock, movezanticlock
from autofocus import auto, scan

mtr=Motor()
try:
    arduino = serial.Serial('/dev/ttyUSB1', 9600)
except Exception as e:
    print(f"Error opening serial port: {e}")


app = Flask(__name__)
# adding save directory
save_dir="/home/pi/Pictures/Saved_videos/"
camera = Camera(save_dir=save_dir)
'''
*****************Motor Control Routes Start************ 
'''

@app.route("/motor1_forward")
def motor1_forward():
    steps = int(request.args.get("steps", 1000))
    mtr.forward_motor1(steps)
    return f"Motor 1 Forward {steps} steps"

@app.route("/motor1_backward")
def motor1_backward():
    steps = int(request.args.get("steps", 1000))
    mtr.backward_motor1(steps)
    return f"Motor 1 Backward {steps} steps"

@app.route("/motor2_forward")
def motor2_forward():
    steps = int(request.args.get("steps", 1000))
    mtr.forward_motor2(steps)
    return f"Motor 2 Forward {steps} steps"

@app.route("/motor2_backward")
def motor2_backward():
    steps = int(request.args.get("steps", 1000))
    mtr.backward_motor2(steps)
    return f"Motor 2 Backward {steps} steps"

@app.route("/motor3_forward")
def motor3_forward():
    steps = int(request.args.get("steps", 1000))
    mtr.forward_motor3(steps)
    return f"Motor 3 Forward {steps} steps"

@app.route("/motor3_backward")
def motor3_backward():
    steps = int(request.args.get("steps", 1000))
    mtr.backward_motor3(steps)
    return f"Motor 3 Backward {steps} steps"


############ Motor Control Routes END  ############


########### x y z coordinates Display Start########
 
 # Global variables to store the current positions
x_pos = 0
y_pos = 0
z_pos = 0

def update_positions(x=None, y=None, z=None):
    global x_pos, y_pos, z_pos
    if x is not None:
        x_pos += x
    if y is not None:
        y_pos += y
    if z is not None:
        z_pos += z


@app.route('/calibrate', methods=['POST'])
def calibrate():
    magnification = request.args.get('magnification')
    if magnification == '4x':
        distance = 200  # Example distance for 4x calibration
    elif magnification == '10x':
        distance = 350  # Example distance for 10x calibration
    elif magnification == '40x':
        distance = 395  # Example distance for 40x calibration
    else:
        return jsonify({"error": "Invalid magnification"}), 400
    
    # Perform calibration logic here
    # For example, we can move the Z axis for calibration
    movezclock(distance)
    update_positions(z=-distance)

    return jsonify({"x": x_pos, "y": y_pos, "z": z_pos})

@app.route('/initialize', methods=['POST'])
def initialize():
    global x_pos, y_pos, z_pos

    # Move X axis to 0
    if x_pos > 0:
        movexanticlock(x_pos)
    elif x_pos < 0:
        movexclock(-x_pos)
    x_pos = 0

    # Move Y axis to 0
    if y_pos > 0:
        movey(-y_pos)
    y_pos = 0

    # Move Z axis to 0
    if z_pos > 0:
        movezanticlock(z_pos)
    elif z_pos < 0:
        movezclock(-z_pos)
    z_pos = 0

    return jsonify({"x": x_pos, "y": y_pos, "z": z_pos})

@app.route('/move', methods=['POST'])
def move():
    axis = request.args.get('axis')
    direction = request.args.get('direction')
    steps = int(request.args.get('steps', 0))

    if axis == 'x':
        if direction == 'clock':
            movexclock(steps)
            update_positions(x=steps)
        elif direction == 'anticlock':
            movexanticlock(steps)
            update_positions(x=-steps)
        else:
            return jsonify({"error": "Invalid direction"}), 400
    elif axis == 'y':
        if direction == 'clock':
            movey(steps)
            update_positions(y=steps)
        elif direction == 'anticlock':
            moveycc(steps)
            update_positions(y=-steps)
        else:
            return jsonify({"error": "Invalid direction"}), 400
    elif axis == 'z':
        if direction == 'clock':
            movezclock(steps)
            update_positions(z=steps)
        elif direction == 'anticlock':
            movezanticlock(steps)
            update_positions(z=-steps)
        else:
            return jsonify({"error": "Invalid direction"}), 400
            
    else:
        return jsonify({"error": "Invalid axis"}), 400

    return jsonify({"x": x_pos, "y": y_pos, "z": z_pos})

 
 
 
########### x y z coordinates Display End##########






@app.route('/')
# 16 May 
def start_page():
    #return render_template('index.html')
    #return render_template('index.html')
    return render_template('start.html')
@app.route('/index')
def index_page():
    return render_template('index.html')
@app.route('/start')
def start_page_alias():
    return render_template('start.html')

@app.route('/gallery')
def gallery_page():
    return render_template('gallery.html')


def generate_frames():
    while True:
        frame = camera.get_frame()  # Get a frame from the camera
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.5)  # Adjust sleep time as needed

@app.route('/video_record')
def video_record():
    filename=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+'.mp4'
    # for recording the live video
    camera.start_recording(filename)
    return 'video recording started'

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture')
def capture():
    camera.capture_image()  # Capture an image
    #return 'Image captured!'
    return 'Image Captured'

@app.route('/stop_record')
def stop_capture():
    camera.stop_recording()  # Stop video recording
    return 'Video recording stopped!'
def cleanup():
    camera.close()# After Picamera stop preview close the camera

if __name__ == "__main__":
    atexit.register(cleanup)# for releasing the resources of picamera
    app.run(debug=True,use_reloader=False)


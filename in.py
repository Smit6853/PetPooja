from flask import Flask, request, jsonify 
import cv2
import numpy as np
import json
import mysql.connector
from io import BytesIO
from PIL import Image
from flask_cors import CORS 

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)  # This will allow cross-origin requests from your React frontend

# MySQL Database Connection (same as your existing code)
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Add your password if necessary
        database="smart_kitchen"
    )
    return conn

# YOLO setup
yolo_net = cv2.dnn.readNet("yolov4.weights", "yolov4.cfg")
layer_names = yolo_net.getLayerNames()
output_layers = [layer_names[i - 1] for i in yolo_net.getUnconnectedOutLayers().flatten()]

def detect_objects(image):
    height, width = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 0.00392, (416, 416), (0, 0, 0), swapRB=True, crop=False)
    yolo_net.setInput(blob)
    outputs = yolo_net.forward(output_layers)
    
    inventory = []
    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = int(np.argmax(scores))
            confidence = float(scores[class_id])

            if confidence > 0.4:  # Confidence threshold
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = center_x - w // 2
                y = center_y - h // 2

                item_name = "tomato"  # Example, map class_id to real object names
                inventory.append({"item_name": item_name, "confidence": confidence, "bbox": [x, y, w, h]})
    
    return inventory

@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        # Get the image file from the request
        file = request.files['image']
        img = Image.open(file.stream)
        img_np = np.array(img)
        
        # Convert RGB to BGR for OpenCV processing
        img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

        # Detect objects in the image
        detected_inventory = detect_objects(img_np)

        # Store inventory data into MySQL (similar to your original Python code)
        conn = get_db_connection()
        cursor = conn.cursor()
        for item in detected_inventory:
            cursor.execute("""
                INSERT INTO inventory (item_name, confidence, bbox)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE confidence = VALUES(confidence)
            """, (item['item_name'], item['confidence'], json.dumps(item['bbox'])))
        conn.commit()

        return jsonify({"detected_inventory": detected_inventory})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

import cv2
import numpy as np
import mysql.connector
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# MySQL Database Connection and Setup using XAMPP
def setup_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",   # XAMPP MySQL server host
            user="root",         # Default MySQL password for XAMPP (empty by default)
            database="smart_kitchen"
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS smart_kitchen")
        conn.database = "smart_kitchen"
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name VARCHAR(255) NOT NULL,
                confidence FLOAT,
                bbox JSON
            )
        """)
        conn.commit()
        return conn, cursor
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None, None

conn, cursor = setup_database()

# YOLO object detection setup
yolo_net = cv2.dnn.readNet("yolov4.weights", "yolov4.cfg")
layer_names = yolo_net.getLayerNames()
output_layers = [layer_names[i - 1] for i in yolo_net.getUnconnectedOutLayers().flatten()]

# Function to process image and detect food items
def detect_objects(image: np.ndarray):
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

            if confidence > 0.4:  # Lower threshold for object detection
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = center_x - w // 2
                y = center_y - h // 2

                # Assuming predefined mapping for food items
                item_name = "tomato"  # Placeholder, should map class_id to a food item
                inventory.append({"item_name": item_name, "confidence": confidence, "bbox": [x, y, w, h]})
    
    return inventory

# Function to process image file
def process_image(image_path):
    try:
        # Read the image file
        image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError("Invalid image file.")
        
        # Detect objects (inventory) in the image
        detected_inventory = detect_objects(image)

        # Store inventory data in MySQL
        for item in detected_inventory:
            cursor.execute("""
                INSERT INTO inventory (item_name, confidence, bbox)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE confidence = VALUES(confidence)
            """, (item['item_name'], item['confidence'], json.dumps(item['bbox'])))
        conn.commit()

        return {"detected_inventory": detected_inventory}

    except Exception as e:
        print(f"Error processing image: {e}")
        return {"error": str(e)}

# Close MySQL connection at the end of execution
def shutdown():
    if cursor and conn:
        cursor.close()
        conn.close()

# Route to process the uploaded image
@app.route('/process_image', methods=['POST'])
def process_image_route():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    image_file = request.files['image']
    image_path = "uploaded_image.jpg"  # Temporary path to save the uploaded image
    image_file.save(image_path)  # Save the uploaded image

    result = process_image(image_path)  # Call the existing process_image function
    return jsonify(result)  # Return the result as JSON

if __name__ == "__main__":
    app.run(debug=True)  # Start the Flask application

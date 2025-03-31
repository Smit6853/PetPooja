import React, { useState } from 'react';
import './App.css';

const App = () => {
  const [image, setImage] = useState(null);
  const [detectedInventory, setDetectedInventory] = useState([]);
  
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        setImage(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUploadImage = async () => {
    // Make sure image is selected
    if (!image) return;

    const formData = new FormData();
    formData.append("image", image); // Add image as form data

    try {
      // Send the image to the backend for processing
      const response = await fetch('http://localhost:5000/process_image', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      setDetectedInventory(data.detected_inventory || []);
    } catch (error) {
      console.error('Error processing image:', error);
    }
  };

  const drawBoundingBoxes = (ctx) => {
    detectedInventory.forEach((item) => {
      const [x, y, w, h] = item.bbox;
      ctx.beginPath();
      ctx.rect(x, y, w, h);
      ctx.lineWidth = 2;
      ctx.strokeStyle = 'red';
      ctx.stroke();
      ctx.font = "16px Arial";
      ctx.fillStyle = "red";
      ctx.fillText(item.item_name, x, y - 10);  // Label for the detected object
    });
  };

  return (
    <div className="App">
      <h1>Smart Kitchen Inventory</h1>

      <input type="file" onChange={handleImageChange} />
      <button onClick={handleUploadImage}>Upload and Process Image</button>

      {image && (
        <div style={{ position: 'relative' }}>
          <img src={image} alt="Upload" style={{ maxWidth: '100%', maxHeight: '500px' }} />
          {detectedInventory.length > 0 && (
            <canvas
              width={500} // Set appropriate width
              height={500} // Set appropriate height
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                pointerEvents: 'none',  // To ensure canvas doesn’t block image interactions
              }}
              ref={(canvas) => {
                if (canvas) {
                  const ctx = canvas.getContext('2d');
                  drawBoundingBoxes(ctx);  // Draw bounding boxes on the canvas
                }
              }}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default App;

import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import csv
import os

# Load the TFLite model
interpreter = tflite.Interpreter(model_path='model.tflite')
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Directory to save feature vectors and cropped face images
name = ''
output_dir = ''
file = f'{name}_rasp'
images_directory = f'{output_dir}/{name}'
os.makedirs(output_dir, exist_ok=True)

vectors = []

# Process images in the directory
for filename in os.listdir(images_directory):
    if filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.jpeg'):
        img_path = os.path.join(images_directory, filename)
        frame = cv2.imread(img_path)

        # Resize the image to match the model's expected input size
        input_image_resized = cv2.resize(frame, (input_details[0]['shape'][2], input_details[0]['shape'][1]))
        input_image_resized = np.expand_dims(input_image_resized, axis=0)
        input_image_resized = input_image_resized.astype(np.float32)

        # Set input tensor for the model
        interpreter.set_tensor(input_details[0]['index'], input_image_resized)

        # Run inference
        interpreter.invoke()

        # Get output tensor
        output_data = interpreter.get_tensor(output_details[0]['index'])

        # Save the extracted facial features to the list
        vectors.append(output_data.flatten())

# Save all the extracted facial features to a CSV file along with image names
output_file = os.path.join(output_dir, f'{file}.csv')
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    for vector in vectors:
        writer.writerow(vector.tolist())

print('All feature vectors are saved')
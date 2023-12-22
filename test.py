import cv2
import numpy as np
import tensorflow as tf
from arcface_tf2.modules.models import ArcFaceModel  # Đảm bảo import mô hình ArcFace đúng cách
import csv
import os

# Đường dẫn đến thư mục chứa các ảnh và nơi lưu trữ file output
name = ''  # Thay đổi thành tên thư mục chứa ảnh
output_dir = ''  # Thay đổi thành thư mục lưu trữ file CSV và kết quả
file = f'{name}_rasp'
images_directory = f'{output_dir}/{name}'
os.makedirs(output_dir, exist_ok=True)

vectors = []

# Tạo mô hình ArcFace
model = ArcFaceModel(size=YOUR_SIZE, channels=YOUR_CHANNELS, num_classes=YOUR_NUM_CLASSES,
                     name='arcface_model', margin=YOUR_MARGIN, logist_scale=YOUR_LOGIST_SCALE,
                     embd_shape=YOUR_EMBD_SHAPE, head_type='ArcHead', backbone_type='MobileNetV2',
                     w_decay=YOUR_WEIGHT_DECAY, use_pretrain=True, training=False)

# Đường dẫn đến tệp checkpoint của mô hình ArcFace
checkpoint_path = '/path/to/your/arcface_checkpoint/e_8_b_40000.ckpt'

# Load trọng số từ tệp checkpoint
checkpoint = tf.train.Checkpoint(model=model)
checkpoint.restore(checkpoint_path).expect_partial()

# Tiến hành xử lý ảnh và trích xuất đặc trưng
for filename in os.listdir(images_directory):
    if filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.jpeg'):
        img_path = os.path.join(images_directory, filename)
        frame = cv2.imread(img_path)

        # Tiền xử lý ảnh trước khi đưa vào mô hình
        resized_image = cv2.resize(frame, (100, 100))  # Resize ảnh thành kích thước 100x100

        # Chuyển đổi sang định dạng phù hợp với mô hình
        input_image_resized = resized_image.astype(np.float32)
        input_image_resized = np.expand_dims(input_image_resized, axis=0)

        # Thực hiện inference với mô hình ArcFace
        output_data = model.predict(input_image_resized)

        # Lưu các vector đặc trưng vào danh sách
        vectors.append(output_data.flatten())

# Lưu các vector đặc trưng vào file CSV cùng với tên ảnh
output_file = os.path.join(output_dir, f'{file}.csv')
with open(output_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    for vector in vectors:
        writer.writerow(vector.tolist())

print('All feature vectors are saved')
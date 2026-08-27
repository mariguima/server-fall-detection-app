# Fall Detection Model

Put the exported TensorFlow Lite model from Colab in this folder:

```text
model/fall_detection_model.tflite
```

The server does not run the Colab training script. It only runs inference with the
exported `.tflite` file.

Expected model input:

- grayscale image
- resized to `96x96`
- normalized to `[0, 1]`
- shape `[1, 96, 96, 1]`

Prediction output:

- sigmoid score near `0` means `No Fall`
- sigmoid score near `1` means `Fall`

ESP32 frame endpoint:

```http
POST /api/v1/frames
Content-Type: image/jpeg
x-api-key: <device api key>
x-device-id: <registered device id>
x-frame-sequence: <counter>
x-frame-timestamp: <epoch seconds or milliseconds>

<raw JPEG bytes>
```

The server runs inference on each frame. A Firestore event is created after
`3` consecutive frames are predicted as `Fall`. While the fall streak continues,
the server does not create duplicate events; a `No Fall` frame resets the alert.

Install one TensorFlow Lite interpreter package before running inference:

```powershell
python -m pip install tensorflow
```

If TensorFlow is too heavy for deployment, use a platform-compatible
`tflite-runtime` package instead.

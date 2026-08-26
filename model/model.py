import base64
import io
import os
from pathlib import Path

import numpy as np
from PIL import Image


MODEL_PATH = Path(__file__).with_name("fall_detection_model.tflite")
INPUT_SIZE = (96, 96)
CLASS_NAMES = ("No Fall", "Fall")
DEFAULT_THRESHOLD = float(os.getenv("FALL_MODEL_THRESHOLD", "0.5"))

_interpreter = None
_input_details = None
_output_details = None


class ModelNotConfiguredError(RuntimeError):
    pass


def _load_interpreter():
    global _interpreter, _input_details, _output_details

    if _interpreter is not None:
        return _interpreter

    if not MODEL_PATH.exists():
        raise ModelNotConfiguredError(
            f"Missing model file: {MODEL_PATH}. Export it from Colab and place it there."
        )

    try:
        from tensorflow.lite.python.interpreter import Interpreter
    except ImportError:
        try:
            from tflite_runtime.interpreter import Interpreter
        except ImportError as error:
            raise ModelNotConfiguredError(
                "Install tensorflow or tflite-runtime to run fall detection inference."
            ) from error

    _interpreter = Interpreter(model_path=str(MODEL_PATH))
    _interpreter.allocate_tensors()
    _input_details = _interpreter.get_input_details()
    _output_details = _interpreter.get_output_details()

    return _interpreter


def _image_to_input_array(image):
    image = image.convert("L")
    image = image.resize(INPUT_SIZE)
    image_array = np.asarray(image, dtype=np.float32) / 255.0
    return np.expand_dims(image_array, axis=(0, -1))


def _decode_base64_image(image_base64):
    if "," in image_base64:
        image_base64 = image_base64.split(",", 1)[1]

    return Image.open(io.BytesIO(base64.b64decode(image_base64)))


def predict_image(image, threshold=DEFAULT_THRESHOLD):
    interpreter = _load_interpreter()
    input_array = _image_to_input_array(image)

    input_detail = _input_details[0]
    input_dtype = input_detail["dtype"]

    if input_dtype == np.uint8:
        scale, zero_point = input_detail["quantization"]
        if scale > 0:
            input_array = input_array / scale + zero_point
        input_array = input_array.astype(np.uint8)
    else:
        input_array = input_array.astype(input_dtype)

    interpreter.set_tensor(input_detail["index"], input_array)
    interpreter.invoke()

    output = interpreter.get_tensor(_output_details[0]["index"])
    score = float(np.squeeze(output))
    predicted_index = int(score >= threshold)

    return {
        "label": CLASS_NAMES[predicted_index],
        "isFall": bool(predicted_index),
        "fallScore": score,
        "threshold": threshold,
    }


def predict(payload):
    if "imageBase64" in payload:
        return predict_image(_decode_base64_image(payload["imageBase64"]))

    if "imagePath" in payload:
        return predict_image(Image.open(payload["imagePath"]))

    raise ValueError("Provide imageBase64, imagePath, or multipart file field 'frame'.")

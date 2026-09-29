from flask import Flask, Response, request
from flask_cors import CORS
import cv2
import numpy as np
import mediapipe as mp
import os
import time
import math

# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "http://127.0.0.1:5500",
                "http://localhost:5500"
            ]
        }
    }
)
@app.after_request
def add_security_headers(response):

    response.headers["X-Content-Type-Options"] = "nosniff"

    response.headers["X-Frame-Options"] = "DENY"

    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(self), "
        "microphone=(), "
        "geolocation=()"
    )

    return response


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CLOTHES_DIR = os.path.join(BASE_DIR, "Clothes")

POSE_MODEL = os.path.join(
    BASE_DIR,
    "pose_landmarker_full.task"
)


# ============================================================
# CAMERA
# ============================================================

camera = None
# ============================================================
# PERFORMANCE / TRACKING CACHE
# ============================================================

cached_clothing = None
cached_clothing_filename = None

cached_landmarks = None

frame_counter = 0

# Run MediaPipe every N frames.
# This prevents the camera from freezing because
# pose detection is expensive.
POSE_INTERVAL = 3


# ============================================================
# SELECTED CLOTHING
# ============================================================

selected_clothing = {
    "filename": None,
    "type": "upper-body"
}


# ============================================================
# MEDIAPIPE POSE
# ============================================================

BaseOptions = mp.tasks.BaseOptions

PoseLandmarker = mp.tasks.vision.PoseLandmarker

PoseLandmarkerOptions = (
    mp.tasks.vision.PoseLandmarkerOptions
)

VisionRunningMode = mp.tasks.vision.RunningMode


pose_options = PoseLandmarkerOptions(

    base_options=BaseOptions(
        model_asset_path=POSE_MODEL
    ),

    running_mode=VisionRunningMode.IMAGE,

    num_poses=1,

    min_pose_detection_confidence=0.5,

    min_pose_presence_confidence=0.5,

    min_tracking_confidence=0.5
)

print("================================")
print("POSE MODEL:", POSE_MODEL)
print("EXISTS:", os.path.exists(POSE_MODEL))

if os.path.exists(POSE_MODEL):
    print("SIZE:", os.path.getsize(POSE_MODEL), "bytes")

print("================================")

pose_landmarker = PoseLandmarker.create_from_options(
    pose_options
)


# ============================================================
# START CAMERA
# ============================================================

def start_camera():

    global camera

    if camera is None:

        camera = cv2.VideoCapture(0)

    if not camera.isOpened():

        print("ERROR: Camera could not be opened")

        return False

    return True


# ============================================================
# STOP CAMERA
# ============================================================

def release_camera():

    global camera

    if camera is not None:

        if camera.isOpened():

            camera.release()

        camera = None


# ============================================================
# LOAD CLOTHING
# ============================================================

def load_clothing():

    global cached_clothing
    global cached_clothing_filename

    filename = selected_clothing["filename"]

    if not filename:
        return None

    filename = os.path.basename(filename)

    # --------------------------------------------------------
    # USE CACHE
    # --------------------------------------------------------

    if (
        cached_clothing is not None
        and
        cached_clothing_filename == filename
    ):
        return cached_clothing

    # --------------------------------------------------------
    # LOAD FILE
    # --------------------------------------------------------

    file_path = os.path.join(
        CLOTHES_DIR,
        filename
    )

    if not os.path.exists(file_path):

        print(
            "Clothing file not found:",
            file_path
        )

        return None

    clothing = cv2.imread(
        file_path,
        cv2.IMREAD_UNCHANGED
    )

    if clothing is None:

        print(
            "Could not load clothing:",
            file_path
        )

        return None

    # --------------------------------------------------------
    # ENSURE 4 CHANNELS
    # --------------------------------------------------------

    if len(clothing.shape) != 3:

        print(
            "Invalid clothing image:",
            filename
        )

        return None

    if clothing.shape[2] == 3:

        # Create alpha from non-black pixels
        bgr = clothing

        gray = cv2.cvtColor(
            bgr,
            cv2.COLOR_BGR2GRAY
        )

        alpha = np.where(
            gray > 5,
            255,
            0
        ).astype(
            np.uint8
        )

        clothing = cv2.cvtColor(
            clothing,
            cv2.COLOR_BGR2BGRA
        )

        clothing[:, :, 3] = alpha

    elif clothing.shape[2] != 4:

        print(
            "Unsupported image channels:",
            clothing.shape
        )

        return None

    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    cached_clothing = clothing
    cached_clothing_filename = filename

    print(
        "Loaded clothing:",
        filename
    )

    return cached_clothing


# ============================================================
# DISTANCE BETWEEN TWO POINTS
# ============================================================

def distance(p1, p2):

    return math.sqrt(
        (p2[0] - p1[0]) ** 2 +
        (p2[1] - p1[1]) ** 2
    )


# ============================================================
# ROTATE IMAGE
# ============================================================

def rotate_image(image, angle):

    height, width = image.shape[:2]

    center = (
        width // 2,
        height // 2
    )

    matrix = cv2.getRotationMatrix2D(
        center,
        angle,
        1.0
    )

    cos = abs(matrix[0, 0])
    sin = abs(matrix[0, 1])

    new_width = int(
        (height * sin) +
        (width * cos)
    )

    new_height = int(
        (height * cos) +
        (width * sin)
    )

    matrix[0, 2] += (
        new_width / 2
    ) - center[0]

    matrix[1, 2] += (
        new_height / 2
    ) - center[1]

    rotated = cv2.warpAffine(

        image,

        matrix,

        (new_width, new_height),

        flags=cv2.INTER_LINEAR,

        borderMode=cv2.BORDER_CONSTANT,

        borderValue=(0, 0, 0, 0)
    )

    return rotated


# ============================================================
# OVERLAY TRANSPARENT PNG
# ============================================================

def overlay_transparent(
    background,
    overlay,
    x,
    y
):
    """
    Safely overlay a transparent RGBA image
    onto a BGR camera frame.

    Handles:
    - negative x/y
    - right/bottom overflow
    - empty crops
    - mismatched dimensions
    - BGR/RGBA channel differences
    """

    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if background is None:
        return background

    if overlay is None:
        return background

    if background.size == 0:
        return background

    if overlay.size == 0:
        return background


    # --------------------------------------------------------
    # BACKGROUND MUST BE BGR
    # --------------------------------------------------------

    if len(background.shape) != 3:
        return background

    if background.shape[2] != 3:
        return background


    # --------------------------------------------------------
    # OVERLAY MUST HAVE 4 CHANNELS
    # --------------------------------------------------------

    if len(overlay.shape) != 3:
        return background

    if overlay.shape[2] == 3:

        overlay = cv2.cvtColor(
            overlay,
            cv2.COLOR_BGR2BGRA
        )

    if overlay.shape[2] != 4:
        return background


    # --------------------------------------------------------
    # ORIGINAL DIMENSIONS
    # --------------------------------------------------------

    bg_h, bg_w = background.shape[:2]

    ov_h, ov_w = overlay.shape[:2]


    if ov_h <= 0 or ov_w <= 0:
        return background


    # --------------------------------------------------------
    # CALCULATE INTERSECTION
    #
    # Instead of modifying the overlay first and hoping
    # the background crop has the same size, calculate
    # exactly which part of both images overlaps.
    # --------------------------------------------------------

    bg_x1 = max(
        0,
        x
    )

    bg_y1 = max(
        0,
        y
    )

    bg_x2 = min(
        bg_w,
        x + ov_w
    )

    bg_y2 = min(
        bg_h,
        y + ov_h
    )


    # --------------------------------------------------------
    # NOTHING IS INSIDE CAMERA FRAME
    # --------------------------------------------------------

    if bg_x1 >= bg_x2:
        return background

    if bg_y1 >= bg_y2:
        return background


    # --------------------------------------------------------
    # CORRESPONDING OVERLAY COORDINATES
    # --------------------------------------------------------

    ov_x1 = max(
        0,
        -x
    )

    ov_y1 = max(
        0,
        -y
    )

    ov_x2 = (
        ov_x1
        +
        (bg_x2 - bg_x1)
    )

    ov_y2 = (
        ov_y1
        +
        (bg_y2 - bg_y1)
    )


    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    if ov_x1 >= ov_x2:
        return background

    if ov_y1 >= ov_y2:
        return background


    # --------------------------------------------------------
    # EXTRACT EXACT SAME SIZE
    # --------------------------------------------------------

    overlay_crop = overlay[
        ov_y1:ov_y2,
        ov_x1:ov_x2
    ]

    background_crop = background[
        bg_y1:bg_y2,
        bg_x1:bg_x2
    ]


    # --------------------------------------------------------
    # EMPTY CROP CHECK
    # --------------------------------------------------------

    if overlay_crop.size == 0:
        return background

    if background_crop.size == 0:
        return background


    # --------------------------------------------------------
    # DIMENSION CHECK
    # --------------------------------------------------------

    if (
        overlay_crop.shape[0]
        !=
        background_crop.shape[0]
    ):
        return background

    if (
        overlay_crop.shape[1]
        !=
        background_crop.shape[1]
    ):
        return background


    # --------------------------------------------------------
    # CHANNEL CHECK
    # --------------------------------------------------------

    if overlay_crop.shape[2] != 4:
        return background

    if background_crop.shape[2] != 3:
        return background


    # --------------------------------------------------------
    # RGB/BGR CLOTHING
    # --------------------------------------------------------

    overlay_rgb = (
        overlay_crop[:, :, :3]
        .astype(np.float32)
    )


    # --------------------------------------------------------
    # ALPHA
    # --------------------------------------------------------

    alpha = (
        overlay_crop[:, :, 3]
        .astype(np.float32)
        /
        255.0
    )


    # Convert:

    # (height, width)

    # to:

    # (height, width, 1)

    alpha = alpha[
        :,
        :,
        np.newaxis
    ]


    # --------------------------------------------------------
    # BACKGROUND
    # --------------------------------------------------------

    background_float = (
        background_crop
        .astype(np.float32)
    )


    # --------------------------------------------------------
    # FINAL SAFETY CHECK
    # --------------------------------------------------------

    if (
        alpha.shape[0]
        !=
        overlay_rgb.shape[0]
    ):
        return background

    if (
        alpha.shape[1]
        !=
        overlay_rgb.shape[1]
    ):
        return background

    if (
        overlay_rgb.shape
        !=
        background_float.shape
    ):
        return background


    # --------------------------------------------------------
    # BLEND
    # --------------------------------------------------------

    blended = (
        overlay_rgb * alpha
        +
        background_float *
        (1.0 - alpha)
    )


    # --------------------------------------------------------
    # WRITE BACK
    # --------------------------------------------------------

    background[
        bg_y1:bg_y2,
        bg_x1:bg_x2
    ] = np.clip(
        blended,
        0,
        255
    ).astype(
        np.uint8
    )


    return background


# ============================================================
# GET LANDMARK POSITION
# ============================================================

def landmark_xy(
    landmarks,
    index,
    width,
    height
):

    landmark = landmarks[index]

    x = int(
        landmark.x * width
    )

    y = int(
        landmark.y * height
    )

    return x, y


# ============================================================
# UPPER BODY CLOTHING
# ============================================================

def apply_upper_body(frame, clothing, landmarks):

    height, width = frame.shape[:2]

    # ---------------------------------------------
    # BODY LANDMARKS
    # ---------------------------------------------

    left_shoulder = landmark_xy(
        landmarks, 11, width, height
    )

    right_shoulder = landmark_xy(
        landmarks, 12, width, height
    )

    left_hip = landmark_xy(
        landmarks, 23, width, height
    )

    right_hip = landmark_xy(
        landmarks, 24, width, height
    )

    # ---------------------------------------------
    # BODY MEASUREMENTS
    # ---------------------------------------------

    shoulder_width = distance(
        left_shoulder,
        right_shoulder
    )

    if shoulder_width < 30:
        return frame

    shoulder_center_x = int(
        (
            left_shoulder[0] +
            right_shoulder[0]
        ) / 2
    )

    shoulder_center_y = int(
        (
            left_shoulder[1] +
            right_shoulder[1]
        ) / 2
    )

    hip_center_y = int(
        (
            left_hip[1] +
            right_hip[1]
        ) / 2
    )

    torso_height = (
        hip_center_y -
        shoulder_center_y
    )

    if torso_height < 40:
        return frame

    # ---------------------------------------------
    # GARMENT SIZE
    # ---------------------------------------------

    target_width = int(
        shoulder_width * 1.20
    )

    target_height = int(
        torso_height * 1.15
    )

    if target_width <= 0 or target_height <= 0:
        return frame

    # ---------------------------------------------
    # RESIZE
    # ---------------------------------------------

    resized = cv2.resize(
        clothing,
        (
            target_width,
            target_height
        ),
        interpolation=cv2.INTER_AREA
    )

    # ---------------------------------------------
    # VERTICAL FLIP
    # Keep this because your garment needed it
    # ---------------------------------------------

    resized = cv2.flip(
        resized,
        0
    )

    # ---------------------------------------------
    # SHOULDER ANGLE
    # ---------------------------------------------

    dx = (
        right_shoulder[0] -
        left_shoulder[0]
    )

    dy = (
        right_shoulder[1] -
        left_shoulder[1]
    )

    angle = math.degrees(
        math.atan2(dy, dx)
    )

    rotated = rotate_image(
        resized,
        -angle
    )

    rotated_h, rotated_w = (
        rotated.shape[:2]
    )

    # ---------------------------------------------
    # POSITION
    # ---------------------------------------------

    x = int(
        shoulder_center_x -
        rotated_w / 2
    )

    y = int(
        shoulder_center_y -
        rotated_h * 0.12
    )

    # ---------------------------------------------
    # OVERLAY
    # ---------------------------------------------

    frame = overlay_transparent(
        frame,
        rotated,
        x,
        y
    )

    return frame

# ============================================================
# LOWER BODY CLOTHING
# ============================================================

def apply_upper_body(
    frame,
    clothing,
    landmarks
):

    height, width = frame.shape[:2]

    # --------------------------------------------------------
    # MEDIAPIPE LANDMARKS
    # --------------------------------------------------------

    # Left shoulder = 11
    # Right shoulder = 12
    # Left hip = 23
    # Right hip = 24

    left_shoulder = landmark_xy(
        landmarks,
        11,
        width,
        height
    )

    right_shoulder = landmark_xy(
        landmarks,
        12,
        width,
        height
    )

    left_hip = landmark_xy(
        landmarks,
        23,
        width,
        height
    )

    right_hip = landmark_xy(
        landmarks,
        24,
        width,
        height
    )

    # --------------------------------------------------------
    # BODY MEASUREMENTS
    # --------------------------------------------------------

    shoulder_width = distance(
        left_shoulder,
        right_shoulder
    )

    hip_width = distance(
        left_hip,
        right_hip
    )

    if shoulder_width < 20:
        return frame

    # --------------------------------------------------------
    # BODY CENTERS
    # --------------------------------------------------------

    center_x = int(
        (
            left_shoulder[0]
            +
            right_shoulder[0]
        ) / 2
    )

    shoulder_center_y = int(
        (
            left_shoulder[1]
            +
            right_shoulder[1]
        ) / 2
    )

    hip_center_y = int(
        (
            left_hip[1]
            +
            right_hip[1]
        ) / 2
    )

    # --------------------------------------------------------
    # TORSO HEIGHT
    # --------------------------------------------------------

    torso_height = (
        hip_center_y
        -
        shoulder_center_y
    )

    if torso_height < 30:
        return frame

    # --------------------------------------------------------
    # CLOTHING SIZE
    # --------------------------------------------------------

    # Slightly wider than shoulders
    target_width = int(
        shoulder_width * 1.30
    )

    # Use torso height instead of PNG aspect ratio
    target_height = int(
        torso_height * 1.35
    )

    if target_width <= 0 or target_height <= 0:
        return frame

    # --------------------------------------------------------
    # RESIZE
    # --------------------------------------------------------

    resized = cv2.resize(
        clothing,
        (
            target_width,
            target_height
        ),
        interpolation=cv2.INTER_AREA
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Flip this ONLY if your clothing PNG is upside down.
    # --------------------------------------------------------

    resized = cv2.flip(
        resized,
        0
    )

    # --------------------------------------------------------
    # SHOULDER ROTATION
    # --------------------------------------------------------

    dx = (
        right_shoulder[0]
        -
        left_shoulder[0]
    )

    dy = (
        right_shoulder[1]
        -
        left_shoulder[1]
    )

    angle = math.degrees(
        math.atan2(
            dy,
            dx
        )
    )

    # Rotate opposite direction
    # because image Y increases downward

    rotated = rotate_image(
        resized,
        -angle
    )

    rotated_h, rotated_w = (
        rotated.shape[:2]
    )

    # --------------------------------------------------------
    # POSITION
    # --------------------------------------------------------

    x = int(
        center_x
        -
        rotated_w / 2
    )

    # Put the top of the garment
    # slightly above the shoulder line

    y = int(
        shoulder_center_y
        -
        rotated_h * 0.10
    )

    # --------------------------------------------------------
    # OVERLAY
    # --------------------------------------------------------

    frame = overlay_transparent(
        frame,
        rotated,
        x,
        y
    )

    return frame

    # --------------------------------------------------------
    # HIP ROTATION
    # --------------------------------------------------------

    dx = (
        right_hip[0]
        -
        left_hip[0]
    )

    dy = (
        right_hip[1]
        -
        left_hip[1]
    )

    angle = math.degrees(
        math.atan2(
            dy,
            dx
        )
    )

    rotated = rotate_image(
        resized,
        -angle
    )

    rotated_h, rotated_w = (
        rotated.shape[:2]
    )

    x = int(
        center_x -
        rotated_w / 2
    )

    y = int(
        center_y -
        rotated_h * 0.08
    )

    frame = overlay_transparent(
        frame,
        rotated,
        x,
        y
    )

    return frame


# ============================================================
# BELT
# ============================================================

def apply_belt(
    frame,
    clothing,
    landmarks
):

    height, width = frame.shape[:2]

    left_hip = landmark_xy(
        landmarks,
        23,
        width,
        height
    )

    right_hip = landmark_xy(
        landmarks,
        24,
        width,
        height
    )

    hip_width = distance(
        left_hip,
        right_hip
    )

    if hip_width < 20:

        return frame

    center_x = int(
        (
            left_hip[0]
            +
            right_hip[0]
        ) / 2
    )

    center_y = int(
        (
            left_hip[1]
            +
            right_hip[1]
        ) / 2
    )

    original_h, original_w = (
        clothing.shape[:2]
    )

    aspect_ratio = (
        original_h /
        original_w
    )

    target_width = int(
        hip_width * 1.45
    )

    target_height = max(
        20,
        int(
            target_width *
            aspect_ratio
        )
    )

    resized = cv2.resize(
        clothing,
        (
            target_width,
            target_height
        ),
        interpolation=cv2.INTER_AREA
    )

    x = int(
        center_x -
        target_width / 2
    )

    y = int(
        center_y -
        target_height / 2
    )

    frame = overlay_transparent(
        frame,
        resized,
        x,
        y
    )

    return frame


# ============================================================
# APPLY CLOTHING
# ============================================================

def apply_clothing(
    frame,
    clothing,
    garment_type,
    landmarks
):

    if clothing is None:

        return frame

    if garment_type == "upper-body":

        return apply_upper_body(
            frame,
            clothing,
            landmarks
        )

    if garment_type == "lower-body":

        return apply_lower_body(
            frame,
            clothing,
            landmarks
        )

    if garment_type == "belt":

        return apply_belt(
            frame,
            clothing,
            landmarks
        )

    return frame


# ============================================================
# PROCESS FRAME
# ============================================================

def process_frame(frame):

    global cached_landmarks
    global frame_counter

    if frame is None:
        return frame

    if frame.size == 0:
        return frame

    try:

        frame_counter += 1

        # ====================================================
        # LOAD CLOTHING
        # ====================================================

        clothing = load_clothing()

        if clothing is None:

            return frame


        # ====================================================
        # MEDIA PIPE
        #
        # Don't run pose detection on every frame.
        # Run it every 3 frames and reuse the previous
        # landmarks between detections.
        # ====================================================

        if (
            cached_landmarks is None
            or
            frame_counter % POSE_INTERVAL == 0
        ):

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            mp_image = mp.Image(

                image_format=
                mp.ImageFormat.SRGB,

                data=rgb
            )


            result = pose_landmarker.detect(
                mp_image
            )


            if result.pose_landmarks:

                cached_landmarks = (
                    result.pose_landmarks[0]
                )

            else:

                # Person temporarily lost.
                # Keep previous landmarks for a
                # short time instead of freezing.

                return frame


        # ====================================================
        # NO LANDMARKS
        # ====================================================

        if cached_landmarks is None:

            return frame


        # ====================================================
        # APPLY CLOTHING
        # ====================================================

        output = apply_clothing(

            frame,

            clothing,

            selected_clothing["type"],

            cached_landmarks

        )


        if output is None:

            return frame


        return output


    except Exception as error:

        print(
            "PROCESS FRAME ERROR:",
            repr(error)
        )

        # VERY IMPORTANT:
        # Return the original camera frame.
        # NEVER let one bad frame kill the stream.

        return frame


# ============================================================
# GENERATE VIDEO
# ============================================================

def generate_frames():

    global camera

    if not start_camera():

        return


    while True:

        try:

            # =================================================
            # CAMERA CHECK
            # =================================================

            if camera is None:
                break

            if not camera.isOpened():
                break


            # =================================================
            # READ FRAME
            # =================================================

            success, frame = camera.read()


            if not success:

                print(
                    "Camera frame read failed."
                )

                time.sleep(
                    0.05
                )

                continue


            if frame is None:
                continue


            if frame.size == 0:
                continue


            # =================================================
            # MIRROR
            # =================================================

            frame = cv2.flip(
                frame,
                1
            )


            # =================================================
            # PROCESS
            # =================================================

            try:

                processed_frame = (
                    process_frame(frame)
                )

                if (
                    processed_frame is not None
                    and
                    processed_frame.size != 0
                ):

                    frame = processed_frame


            except Exception as error:

                print(
                    "FRAME PROCESSING ERROR:",
                    repr(error)
                )

                # IMPORTANT:
                # Keep original camera frame.
                #
                # Do NOT:
                #
                # continue
                #
                # because that would cause the
                # browser video to freeze.

                pass


            # =================================================
            # ENCODE FRAME
            # =================================================

            success, encoded = cv2.imencode(

                ".jpg",

                frame,

                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    80
                ]

            )


            if not success:

                continue


            frame_bytes = (
                encoded.tobytes()
            )


            # =================================================
            # SEND FRAME
            # =================================================

            yield (

                b"--frame\r\n"

                b"Content-Type: image/jpeg\r\n"

                b"Content-Length: "

                +
                str(
                    len(frame_bytes)
                ).encode()

                +
                b"\r\n\r\n"

                +
                frame_bytes

                +
                b"\r\n"

            )


            # Small delay prevents CPU from
            # being completely saturated.

            time.sleep(
                0.01
            )


        except GeneratorExit:

            print(
                "Video client disconnected."
            )

            break


        except Exception as error:

            print(
                "VIDEO LOOP ERROR:",
                repr(error)
            )

            # Don't kill the stream.

            time.sleep(
                0.05
            )

            continue


# ============================================================
# START CAMERA
# ============================================================

@app.route(
    "/start-camera",
    methods=["GET"]
)
def start_camera_route():

    print(
        "START CAMERA REQUEST RECEIVED"
    )

    if start_camera():

        return {
            "status":
            "camera started"
        }

    return {
        "status":
        "camera failed"
    }, 500


# ============================================================
# SELECT CLOTHING
# ============================================================

@app.route(
    "/set-clothing",
    methods=["POST"]
)
def set_clothing():

    global selected_clothing

    data = request.get_json(
        silent=True
    )

    if not data:

        return {
            "status":
            "error",
            "message":
            "No JSON data received"
        }, 400

    filename = data.get(
        "filename"
    )

    garment_type = data.get(
        "type",
        "upper-body"
    )

    if not filename:

        return {
            "status":
            "error",
            "message":
            "No clothing filename"
        }, 400

    # Only allow filename

    filename = os.path.basename(
        filename
    )

    allowed_extensions = [
        ".png",
        ".jpg",
        ".jpeg"
    ]

    extension = os.path.splitext(
        filename
    )[1].lower()

    if extension not in allowed_extensions:

        return {
            "status":
            "error",
            "message":
            "Invalid clothing file"
        }, 400

    file_path = os.path.join(
        CLOTHES_DIR,
        filename
    )

    if not os.path.exists(
        file_path
    ):

        return {
            "status":
            "error",
            "message":
            f"Clothing not found: {filename}"
        }, 404

    selected_clothing = {

        "filename":
        filename,

        "type":
        garment_type
    }

    print(
        "Selected clothing:",
        selected_clothing
    )

    return {

        "status":
        "clothing selected",

        "clothing":
        selected_clothing
    }


# ============================================================
# VIDEO
# ============================================================

@app.route("/video")
def video():

    print(
        "VIDEO REQUEST RECEIVED"
    )

    return Response(

        generate_frames(),

        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ============================================================
# STOP CAMERA
# ============================================================

@app.route(
    "/stop-camera"
)
def stop_camera():

    release_camera()

    return {

        "status":
        "camera stopped"
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "======================================"
    )
    print(
        "   MY BRAND VIRTUAL FITTING ROOM"
    )
    print(
        "======================================"
    )
    print(
        "Server:"
    )
    print(
        "http://127.0.0.1:5000"
    )
    print(
        "======================================"
    )
    print()

    app.run(

        host="127.0.0.1",

        port=5000,

        debug=True,

        threaded=True,

        use_reloader=False
    )

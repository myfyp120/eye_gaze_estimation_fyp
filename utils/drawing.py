import cv2

def draw_gaze_point(frame, gaze_x, gaze_y):
    """
    Draws a gaze indicator on the frame.
    gaze_x, gaze_y are values between 0 and 1
    """
    h, w = frame.shape[:2]
    x = int(gaze_x * w)
    y = int(gaze_y * h)

    # Outer circle
    cv2.circle(frame, (x, y), 20, (0, 255, 0), 2)
    # Inner dot
    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
    # Crosshair lines
    cv2.line(frame, (x - 30, y), (x + 30, y), (0, 255, 0), 1)
    cv2.line(frame, (x, y - 30), (x, y + 30), (0, 255, 0), 1)

    return frame
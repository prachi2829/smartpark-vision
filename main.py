from ultralytics import YOLO
import cv2
import numpy as np
import math

#intersection
def intersects(box, p1, p2):
    x1,y1,x2,y2 = box
    for t in range(40):
        x = int(p1[0] + (p2[0]-p1[0]) * t/40)
        y = int(p1[1] + (p2[1]-p1[1]) * t/40)
        if x1 <= x <= x2 and y1 <= y <= y2:
            return True
    return False


model=YOLO("models/best.pt")

frame = cv2.imread("test.jpg")
orig_frame = frame.copy()

#detection
results = model(frame)[0]

slots = []
for box in results.boxes:
    x1, y1, x2, y2 = map(int, box.xyxy[0])
    cls = int(box.cls[0])
    label = model.names[cls]
    slots.append({"bbox": (x1, y1, x2, y2), "label": label})

empty_slots = [s for s in slots if s["label"] == "empty"]

if not empty_slots:
    print("No empty slots available")
    exit()

#helper fnct
def center(b):
    return ((b[0] + b[2]) // 2, (b[1] + b[3]) // 2)

def dist(a, b):
    return ((a[0] - b[0])**2 + (a[1] - b[1])**2)**0.5

def draw_slots(img):
    for s in slots:
        x1, y1, x2, y2 = s["bbox"]
        color = (0,255,255) if s["label"]=="empty" else (0,0,255)
        cv2.rectangle(img, (x1,y1), (x2,y2), color, 2)

#interaction
car_pos = None

def mouse_click(event, x, y, flags, param):
    global car_pos
    if event == cv2.EVENT_LBUTTONDOWN:
        car_pos = (x, y)

cv2.namedWindow("Parking")
cv2.setMouseCallback("Parking", mouse_click)

#main
while True:
    display = orig_frame.copy()
    draw_slots(display)

    cv2.rectangle(display, (10,10), (350,140), (0,0,0), -1)
    cv2.putText(display, "SMART PARKING SYSTEM", (20,35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

    total = len(slots)
    empty = len(empty_slots)

    cv2.putText(display, f"Slots: {empty}/{total}", (20,65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    cv2.putText(display, "Click: Set Car | A: Animate | R: Reset",
                (20,90), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200,200,200), 1)

    status = "Idle"

    if car_pos is not None:

        #draw car
        cv2.circle(display, car_pos, 8, (255,0,0), -1)
        cv2.circle(display, car_pos, 12, (255,0,0), 2)

        #slot selection
        best = min(empty_slots, key=lambda s: dist(car_pos, center(s["bbox"])))
        tx, ty = center(best["bbox"])
        target = (tx, ty - 20)

        x1,y1,x2,y2 = best["bbox"]
        cv2.rectangle(display,(x1,y1),(x2,y2),(0,255,0),3)
        cv2.putText(display,"TARGET",(x1,y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),2)

        #distance
        distance = int(dist(car_pos, target))
        cv2.putText(display, f"Distance: {distance}", (20,115),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        #base path
        path = [
            car_pos,
            (car_pos[0], target[1]),
            target
        ]

        #obstacle check
        dx = target[0] - car_pos[0]
        direction_sign = 1 if dx > 0 else -1

        offset = 0

        while True:
            blocked = False

            for i in range(len(path)-1):
                for s in slots:
                    if s["label"] == "occupied":
                        if intersects(s["bbox"], path[i], path[i+1]):
                            blocked = True
                            break
                if blocked:
                    break

            if not blocked:
                break

            offset += 60
            new_x = car_pos[0] + direction_sign * offset

            path = [
                car_pos,
                (new_x, car_pos[1]),
                (new_x, target[1]),
                target
            ]

            if offset > 400:
                break

        #drawing path
        for i in range(len(path)-1):
            cv2.line(display, path[i], path[i+1], (255,0,255), 3)

        #direction
        dx = target[0] - car_pos[0]
        if dx > 40:
            direction = "Turn Right"
        elif dx < -40:
            direction = "Turn Left"
        else:
            direction = "Go Straight"

        cv2.putText(display, direction, (20,135),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        status = "Path Planned"

    cv2.putText(display, f"Status: {status}", (20,160),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    cv2.imshow("Parking", display)

    key = cv2.waitKey(1)

    #animation
    if key == ord('a') and car_pos is not None:
        for i in range(len(path)-1):
            start = path[i]
            end = path[i+1]

            for t in np.linspace(0,1,30):
                x = int(start[0] + (end[0]-start[0])*t)
                y = int(start[1] + (end[1]-start[1])*t)

                temp = orig_frame.copy()
                draw_slots(temp)

                cv2.rectangle(temp,(x1,y1),(x2,y2),(0,255,0),3)

                for j in range(len(path)-1):
                    cv2.line(temp, path[j], path[j+1], (255,0,255), 3)

                cv2.circle(temp, (x,y), 8, (255,0,0), -1)
                cv2.circle(temp, (x,y), 12, (255,0,0), 2)

                cv2.imshow("Parking", temp)
                cv2.waitKey(20)

    if key == ord('r'):
        car_pos = None

    if key == 27:
        break

cv2.destroyAllWindows()
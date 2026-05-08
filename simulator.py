import cv2
import numpy as np
import random
import heapq

#initial
WIDTH, HEIGHT = 900, 600
GRID_SIZE = 20

COLS = 5
SLOT_W = 100
SLOT_H = 60
GAP = 20

TOP_ROW_Y = 120
BOTTOM_ROW_Y = 420

#slot generation
slots = []
for i in range(COLS):
    x = 100 + i*(SLOT_W + GAP)

    slots.append({
        "bbox": (x, TOP_ROW_Y, x+SLOT_W, TOP_ROW_Y+SLOT_H),
        "label": "empty" if random.random() < 0.7 else "occupied"
    })

    slots.append({
        "bbox": (x, BOTTOM_ROW_Y, x+SLOT_W, BOTTOM_ROW_Y+SLOT_H),
        "label": "empty" if random.random() < 0.7 else "occupied"
    })

#grid
rows = HEIGHT // GRID_SIZE
cols = WIDTH // GRID_SIZE

def create_grid():
    grid = np.zeros((rows, cols), dtype=int)

    for s in slots:
        if s["label"] == "occupied":
            x1,y1,x2,y2 = s["bbox"]

            for y in range(y1//GRID_SIZE, y2//GRID_SIZE):
                for x in range(x1//GRID_SIZE, x2//GRID_SIZE):
                    if 0 <= y < rows and 0 <= x < cols:
                        grid[y][x] = 1
    return grid

#a* algorithm
def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def astar(grid, start, goal):
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        neighbors = [
            (current[0]+1, current[1]),
            (current[0]-1, current[1]),
            (current[0], current[1]+1),
            (current[0], current[1]-1)
        ]

        for nx, ny in neighbors:
            if 0 <= nx < cols and 0 <= ny < rows:
                if grid[ny][nx] == 1:
                    continue

                new_cost = g_score[current] + 1

                if (nx,ny) not in g_score or new_cost < g_score[(nx,ny)]:
                    g_score[(nx,ny)] = new_cost
                    priority = new_cost + heuristic((nx,ny), goal)
                    heapq.heappush(open_set, (priority, (nx,ny)))
                    came_from[(nx,ny)] = current

    return []

#helper
def center(b):
    return ((b[0]+b[2])//2, (b[1]+b[3])//2)

def dist(a,b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2)**0.5

def draw_slots(img):
    for s in slots:
        x1,y1,x2,y2 = s["bbox"]
        color = (0,255,0) if s["label"]=="empty" else (0,0,255)
        cv2.rectangle(img,(x1,y1),(x2,y2),color,2)

car_pos = None

def mouse(event,x,y,flags,param):
    global car_pos
    if event == cv2.EVENT_LBUTTONDOWN:
        car_pos = (x,y)

cv2.namedWindow("Simulator")
cv2.setMouseCallback("Simulator", mouse)

#main
while True:
    frame = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8)*50

    
    cv2.rectangle(frame, (10,10), (360,170), (0,0,0), -1)
    cv2.putText(frame, "SMART PARKING SIMULATOR", (20,35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

    total = len(slots)
    empty = len([s for s in slots if s["label"]=="empty"])

    cv2.putText(frame, f"Slots: {empty}/{total}", (20,65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    cv2.putText(frame, "Click: Place Car", (20,90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200,200,200), 1)

    cv2.putText(frame, "A: Animate | R: Reset", (20,110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200,200,200), 1)

    draw_slots(frame)

    grid = create_grid()
    empty_slots = [s for s in slots if s["label"]=="empty"]

    status = "Idle"
    path = []

    if car_pos and empty_slots:
        cv2.circle(frame, car_pos, 8, (255,0,0), -1)

        best = min(empty_slots, key=lambda s: dist(car_pos, center(s["bbox"])))
        target = center(best["bbox"])

        x1,y1,x2,y2 = best["bbox"]
        cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,255),3)
        cv2.putText(frame,"TARGET",(x1,y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,255),2)

        distance = int(dist(car_pos, target))
        cv2.putText(frame, f"Distance: {distance}", (20,135),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

        start = (car_pos[0]//GRID_SIZE, car_pos[1]//GRID_SIZE)
        goal = (target[0]//GRID_SIZE, target[1]//GRID_SIZE)

        path = astar(grid, start, goal)

        for (x,y) in path:
            px = x * GRID_SIZE + GRID_SIZE//2
            py = y * GRID_SIZE + GRID_SIZE//2
            cv2.circle(frame, (px,py), 2, (255,0,255), -1)

        status = "Path Found"

    cv2.putText(frame, f"Status: {status}", (20,155),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    cv2.imshow("Simulator", frame)

    key = cv2.waitKey(1)

    #animation
    if key == ord('a') and car_pos is not None and path:
        for (x,y) in path:
            px = x * GRID_SIZE + GRID_SIZE//2
            py = y * GRID_SIZE + GRID_SIZE//2

            temp = frame.copy()
            draw_slots(temp)

            cv2.circle(temp, (px,py), 8, (255,0,0), -1)

            cv2.imshow("Simulator", temp)
            cv2.waitKey(40)

    if key == ord('r'):
        car_pos = None

    if key == 27:
        break

cv2.destroyAllWindows()



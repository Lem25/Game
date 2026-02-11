import heapq
from constants import GRID_W, GRID_H

def astar(grid, start, goal):
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    close_set = set()
    came_from = {}
    gscore = {start: 0}
    fscore = {start: heuristic(start, goal)}
    open_heap = []
    heapq.heappush(open_heap, (fscore[start], start))
    
    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]
        close_set.add(current)
        for dx, dy in neighbors:
            neighbor = (current[0] + dx, current[1] + dy)
            nx, ny = neighbor[0], neighbor[1]
            if (0 <= nx < GRID_W and 0 <= ny < GRID_H and 
                grid[ny][nx] == 2 and neighbor not in close_set):
                tentative_g = gscore[current] + 1
                if neighbor not in gscore or tentative_g < gscore[neighbor]:
                    came_from[neighbor] = current
                    gscore[neighbor] = tentative_g
                    fscore[neighbor] = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_heap, (fscore[neighbor], neighbor))
    return []

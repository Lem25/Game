from constants import TILE


class SpatialHash:
    def __init__(self, cell_size=TILE * 2):
        self.cell_size = max(8, int(cell_size))
        self.buckets = {}

    def clear(self):
        self.buckets.clear()

    def _key(self, pos):
        return (int(pos.x // self.cell_size), int(pos.y // self.cell_size))

    def rebuild(self, entities):
        self.clear()
        for entity in entities:
            key = self._key(entity.pos)
            self.buckets.setdefault(key, []).append(entity)

    def query_radius(self, center, radius):
        min_x = int((center.x - radius) // self.cell_size)
        max_x = int((center.x + radius) // self.cell_size)
        min_y = int((center.y - radius) // self.cell_size)
        max_y = int((center.y + radius) // self.cell_size)

        results = []
        for bx in range(min_x, max_x + 1):
            for by in range(min_y, max_y + 1):
                results.extend(self.buckets.get((bx, by), []))
        return results

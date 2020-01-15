import numpy as np
import math

# 0 ~ 26 : blocks (color, shape, pattern)
# 27 : empty
# 28 ~ 30 : dummy blocks

def circle_dist(x, y):
    return math.sqrt(x*x + y*y)

def square_dist(x, y):
    return max(x, -x, y, -y)

def triangle_dist(x, y):
    return max((6 * x - 3 * y + 1) / 4, (- 6 * x - 3 * y + 1) / 4, (3 * y - 1) / 2)

class BHB_renderer(object):
    def __init__(self, size):
        self.size = size
        self.cell_w = 20
        self.cell_h = 20
        self.w = self.cell_w * self.size
        self.h = self.cell_h * (self.size + 2)

        self.block_templates = []
        for i in range(31):
            self.block_templates.append(self.block_template(i))
        self.gauge_templates = [] # 0 : small, 1 : big
        for i in range(2):
            self.gauge_templates.append(self.gauge_template(i))

    def gauge_template(self, gauge):
        canvas = np.ones([self.cell_w, self.cell_h, 3])

        center = [self.cell_w // 2, self.cell_h // 2]
        if gauge == 0:
            r = self.cell_w // 10
            for x in range(center[0] - r, center[0] + r):
                for y in range(center[1] - r, center[1] // 2 + r):
                    if circle_dist(x - center[0], y - center[1]) <= r:
                        canvas[x, y] = [0, 0, 0]
        elif gauge == 1:
            r = self.cell_w // 4
            for x in range(center[0] - r, center[0] + r):
                for y in range(center[1] - r, center[1] + r):
                    canvas[x, y] = [0, 0, 0]
        return canvas

    def block_template(self, block):
        canvas = np.zeros([self.cell_w, self.cell_h, 3])
        mw = self.cell_w // 20
        mh = self.cell_h // 20
        for x in range(0, self.cell_w):
            for y in range(mh):
                canvas[x, y] = [1, 1, 1]
                canvas[x, self.cell_h - 1 - y] = [1, 1, 1]
        for y in range(0, self.cell_h):
            for x in range(mw):
                canvas[x, y] = [1, 1, 1]
                canvas[self.cell_w - 1 - x, y] = [1, 1, 1]

        if block == 27:
            return canvas
        if block > 27:
            period = 4 if block == 28 else 3 if block == 29 else 1
            for x in range(mw * 2, self.cell_w - mw * 2 + 1):
                for y in range(mh * 2, self.cell_h - mh * 2 + 1):
                    if (y - x) % period == 0:
                        canvas[x, y] = [1, 1, 1]
            return canvas

        color_ = block // 9          # R, G, B
        shape = (block % 9) // 3    # circle, square, triangle
        pattern = block % 3         # empty, stripe, full
        
        color = [0, 0, 0]
        color[color_] = 1

        dist_func = circle_dist if shape == 0 else square_dist if shape == 1 else triangle_dist

        center = [float(self.cell_w) / 2, float(self.cell_h) / 2]
        for x in range(mw * 2, self.cell_w - mw * 2 + 1):
            for y in range(mh * 2, self.cell_h - mh * 2 + 1):
                d = dist_func((x - center[0]) / (self.cell_w / 2 - mw * 2), (y - center[1]) / (self.cell_h / 2 - mh * 2))
                if d <= 1 and ((pattern == 0 and 0.8 <= d) or
                    (pattern == 1 and (d <= 0.2 or (0.4 <= d and d <= 0.6) or 0.8 <= d)) or
                    (pattern == 2)):
                    canvas[x,y] = color
        return canvas

    def draw_cell(self, canvas, x, y, id_, is_block=True):
        bw, bh = self.cell_w, self.cell_h
        if(is_block):
            canvas[bw * x : bw * (x + 1), bh * y : bh * (y + 1)] = self.block_templates[id_]
        else:
            canvas[bw * x : bw * (x + 1), bh * y : bh * (y + 1)] = self.gauge_templates[id_]

    def render(self, state):
        canvas = np.ones([self.w, self.h, 3])
        self.draw_cell(canvas, 3, self.size + 1, state.current_block)

        for x in range(0, self.size):
            for y in range(0, self.size):
                self.draw_cell(canvas, x, y + 1, state.blocks[x][y])
        
        for x in range(0, self.size):
            if x > self.size - 1 - state.gauge:
                self.draw_cell(canvas, x, 0, 0, False)
            else:
                self.draw_cell(canvas, x, 0, 1, False)
        return canvas


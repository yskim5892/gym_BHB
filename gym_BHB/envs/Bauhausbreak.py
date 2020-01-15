import numpy as np
import random
import math
from BHB_renderer import BHB_renderer
import gym
from gym import error, spaces, utils
from gym.utils import seeding

# 0 ~ 26 : blocks (color, shape, pattern)
# 27 : empty
# 28 ~ 30 : dummy blocks

class BHB_State(object):
    def __init__(self, is_terminal, blocks, gauge, current_block, score):
        self.is_terminal = is_terminal
        self.blocks = blocks
        self.gauge = gauge
        self.current_block = current_block
        self.score = score

def check_matching(b1, b2, b3):
        color_matched = int((((b1 // 9) + (b2 // 9) + (b3 // 9)) % 3 == 0))
        shape_matched = int(((b1 // 3) + (b2 // 3) + (b3 // 3)) % 3 == 0)
        pattern_matched = int((b1 + b2 + b3) % 3 == 0)
        sum_ = color_matched + shape_matched + pattern_matched
        return sum_

class Bauhausbreak(gym.Env):
    metadata = {'render.modes' : ['human']} 
    def __init__(self):
        self.size = 8
        self.renderer = BHB_renderer(self.size)

        self.observation_space = spaces.Box(low=0, high=1, shape=(self.renderer.w, self.renderer.h, 3))
        self.action_space = spaces.Discrete(self.size)
                
    def obs(self):
        return self.renderer.render(self.state)

    def step(self, action):
        blocks = self.state.blocks.copy()
        if(blocks[action][self.size-1] != 27):
            new_state = BHB_State(True, blocks, self.state.gauge, random.randrange(0, 27), self.state.score)
            self.state = new_state
            return new_state, 0


        for y in range(0, self.size):
            if(blocks[action][y] == 27):
                blocks[action][y] = self.state.current_block
                break

        sum_rew = 0
        while(True):
            matchings, sum_grade = self.find_all_matchings(blocks)
            if(len(matchings) == 0):
                break
            rew, removed_columns = self.break_dummy_blocks(matchings, blocks)
            sum_rew += rew
            self.drop_boxes(removed_columns, blocks)
        sum_rew *= pow(1.0002, self.state.score)
        
        new_block = random.randrange(0, 27)
        gauge = self.state.gauge
        gauge += 1
        if(gauge == self.size):
            gauge = 0
            for x in range(0, self.size):
                if(blocks[x][self.size-1] != 27):
                    new_state = BHB_State(True, blocks, gauge, new_block, self.state.score + sum_rew)
                    self.state = new_state
                    return self.obs(), sum_rew, True, {}
            for x in range(0, self.size):
                for y in range(self.size - 1, 0, -1):
                    blocks[x][y] = blocks[x][y - 1]
                blocks[x][0] = 30
        new_state = BHB_State(False, blocks, gauge, new_block, self.state.score + sum_rew)
        self.state = new_state
        return self.obs(), sum_rew, False, {}

    def reset(self):
        blocks = np.full((self.size, self.size), 27)
        '''for x in range(0, self.size):
            if(x % 2 == 1):
                blocks[x][0] = 30
            else:
                blocks[x][0] = random.randrange(0, 27)

            if(x % 3 != 2):
                blocks[x][1] = random.randrange(0, 27)

            if(x  == 1 or x == 3 or x == 7):
                blocks[x][2] = random.randrange(0, 27)'''
        for x in range(0, self.size):
            if(x % 2 == 0):
                blocks[x][0] = random.randrange(0, 27)
            else:
                blocks[x][0] = 30

        self.state = BHB_State(False, blocks, 0, random.randrange(0, 27),0)
        return self.obs()

    def render(self, mode='human'):
        return self.obs()

    def close(self):
        pass

    def find_all_matchings(self, blocks):
        matchings = []
        sum_grade = 0
        for x in range(0, self.size):
            for y in range(0, self.size):
                if(blocks[x][y] >= 27):
                    continue
                if(x <= self.size - 3 and blocks[x+1][y] < 27 and blocks[x+2][y] < 27):
                    grade = check_matching(blocks[x][y], blocks[x+1][y], blocks[x+2][y])
                    if(grade != 0):
                        matchings.append(((x, y), 0, grade))
                        sum_grade += grade
                if(y <= self.size - 3 and blocks[x][y+1] < 27 and blocks[x][y+2] < 27):
                    grade = check_matching(blocks[x][y], blocks[x][y+1], blocks[x][y+2])
                    if(grade != 0):
                        matchings.append(((x, y), 1, grade))
                        sum_grade += grade
        return matchings, sum_grade

    def grade_to_rew(self, grade):
        if(grade == 1):
            return 0
        if(grade == 2):
            return 0
        if(grade == 3):
            return 300
        return 0

    def break_dummy_blocks(self, matchings, blocks):
        rew = 0
        removed_columns = dict()
        for match in matchings:
            grade = match[2]
            rew += self.grade_to_rew(grade)
            x = match[0][0]
            y = match[0][1]
            dx = int(match[1] == 0)
            dy = int(match[1] == 1)

            for i in range(0, 3):
                x_ = x + i * dx
                y_ = y + i * dy
                blocks[x_][y_] = 27
                removed_columns[x_] = 1

                for dx_, dy_ in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    x__ = x_ + dx_
                    y__ = y_ + dy_
                    if(x__ >= 0 and x__ < self.size and y__ >= 0 and y__ < self.size and blocks[x__][y__] >= 28):
                        blocks[x__][y__] = blocks[x__][y__] - grade
                        if(blocks[x__][y__] <= 27):
                            blocks[x__][y__] = 27
                            removed_columns[x__] = 1
        return rew, removed_columns

    def drop_boxes(self, removed_columns, blocks):
        for x in range(0, self.size):
            if (x in removed_columns):
                removed_boxes_num = 0
                for y in range(0, self.size):
                    if (blocks[x][y] == 27):
                        removed_boxes_num += 1
                        continue
                    elif(removed_boxes_num >= 1):
                        blocks[x][y - removed_boxes_num] = blocks[x][y]
                        blocks[x][y] = 27



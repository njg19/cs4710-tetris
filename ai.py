from tetris import BOARD_DATA, BOARD2_DATA, Shape

import math
from datetime import datetime
import numpy as np
import random

# Agent 1 - Q Learner

class Tetris_AI_1(object):

    def __init__(self, **args):
        self.q_values = {}
        self.alpha = 0.2
        self.gamma = 0.8
        self.epsilon = 0.025
        self.qCount = 0
        self.random = 0

    def getQValue(self, state):
        if state in self.q_values:
            return self.q_values[state]
        return 0.0
    
    def getReward(self, state):
        return self.calculateScore(state)
    
    def computeValueFromQValues(self, state):
        answer = -999999999
        for newState in self.getPossibleStates(state):
            q2 = self.getQValue(newState)
            answer = max(q2, answer)
        return answer
    
    def nextMove(self, gameCount):
        # Epsilon greedy
        strategies, q_strategy = self.getPossibleStrategies()
        if random.random() < 1 - self.epsilon or gameCount > 125:
            self.qCount += 1
            return q_strategy
        else:
            self.random += 1
            return random.choice(strategies)
        #return q_strategy
        
    def update(self, state, nextState, reward):
        state = self.cleanState(state)
        if state not in self.q_values:
            self.q_values[state] = 0.0
        q = self.getQValue(state) * (1 - self.alpha)
        m = self.alpha * ( reward + self.computeValueFromQValues(self.cleanState(nextState)) * self.gamma )
        self.q_values[state] = q + m

    def getPossibleStates(self, state):
        states = []
        d0Range, _ = self.getDRanges()
        for d0 in d0Range:
            minX, maxX, _, _ = BOARD_DATA.currentShape.getBoundingOffsets(d0)
            for x0 in range(-minX, BOARD_DATA.width - maxX):
                board = self.calcStep1Board(d0, x0)
                states.append(self.cleanState(board))
        return states
    
    def getPossibleStrategies(self):
        # Greedy Q Value
        strategies = []
        optimal_strategy = None
        d0Range, d1Range = self.getDRanges()
        for d0 in d0Range:
            minX, maxX, _, _ = BOARD_DATA.currentShape.getBoundingOffsets(d0)
            for x0 in range(-minX, BOARD_DATA.width - maxX):
                board = self.calcStep1Board(d0, x0)
                for d1 in d1Range:
                    minX, maxX, _, _ = BOARD_DATA.nextShape.getBoundingOffsets(d1)
                    dropDist = self.calcNextDropDist(board, d1, range(-minX, BOARD_DATA.width - maxX))
                    for x1 in range(-minX, BOARD_DATA.width - maxX):
                        # Q Score calculations here
                        r = self.calculateScore(np.copy(board), d1, x1, dropDist)
                        q = self.getQValue(self.cleanState( np.array(BOARD_DATA.getData()).reshape((BOARD_DATA.height, BOARD_DATA.width))))
                        q_prime = self.getQValue(self.cleanState(board))
                        score = q + self.alpha * (r + self.gamma * q_prime)
                        # if score > 0:
                        #     print("QLEARNED")
                        strategy = (d0, x0, score)
                        strategies.append(strategy)
                        if not optimal_strategy or optimal_strategy[2] < score:
                            optimal_strategy = strategy
        return strategies, optimal_strategy
    
    def getDRanges(self):
        if BOARD_DATA.currentShape.shape in (Shape.shapeI, Shape.shapeZ, Shape.shapeS):
            d0Range = (0, 1)
        elif BOARD_DATA.currentShape.shape == Shape.shapeO:
            d0Range = (0,)
        else:
            d0Range = (0, 1, 2, 3)

        if BOARD_DATA.nextShape.shape in (Shape.shapeI, Shape.shapeZ, Shape.shapeS):
            d1Range = (0, 1)
        elif BOARD_DATA.nextShape.shape == Shape.shapeO:
            d1Range = (0,)
        else:
            d1Range = (0, 1, 2, 3)
        return d0Range, d1Range

    def calcNextDropDist(self, data, d0, xRange):
        res = {}
        for x0 in xRange:
            if x0 not in res:
                res[x0] = BOARD_DATA.height - 1
            for x, y in BOARD_DATA.nextShape.getCoords(d0, x0, 0):
                yy = 0
                while yy + y < BOARD_DATA.height and (yy + y < 0 or data[(y + yy), x] == Shape.shapeNone):
                    yy += 1
                yy -= 1
                if yy < res[x0]:
                    res[x0] = yy
        return res

    def calcStep1Board(self, d0, x0):
        board = np.array(BOARD_DATA.getData()).reshape((BOARD_DATA.height, BOARD_DATA.width))
        self.dropDown(board, BOARD_DATA.currentShape, d0, x0)
        return board

    def dropDown(self, data, shape, direction, x0):
        dy = BOARD_DATA.height - 1
        for x, y in shape.getCoords(direction, x0, 0):
            yy = 0
            while yy + y < BOARD_DATA.height and (yy + y < 0 or data[(y + yy), x] == Shape.shapeNone):
                yy += 1
            yy -= 1
            if yy < dy:
                dy = yy
        self.dropDownByDist(data, shape, direction, x0, dy)

    def dropDownByDist(self, data, shape, direction, x0, dist):
        for x, y in shape.getCoords(direction, x0, 0):
            data[y + dist, x] = shape.shape

    def calculateScore(self, step1Board, d1, x1, dropDist):
        width = BOARD_DATA.width
        height = BOARD_DATA.height
        self.dropDownByDist(step1Board, BOARD_DATA.nextShape, d1, x1, dropDist[x1])
        fullLines, nearFullLines = 0, 0
        roofY = [0] * width
        holeCandidates = [0] * width
        holeConfirm = [0] * width
        vHoles, vBlocks = 0, 0
        for y in range(height - 1, -1, -1):
            hasHole = False
            hasBlock = False
            for x in range(width):
                if step1Board[y, x] == Shape.shapeNone:
                    hasHole = True
                    holeCandidates[x] += 1
                else:
                    hasBlock = True
                    roofY[x] = height - y
                    if holeCandidates[x] > 0:
                        holeConfirm[x] += holeCandidates[x]
                        holeCandidates[x] = 0
                    if holeConfirm[x] > 0:
                        vBlocks += 1
            if not hasBlock:
                break
            if not hasHole and hasBlock:
                fullLines += 1
        vHoles = sum([x ** .7 for x in holeConfirm])
        maxHeight = max(roofY) - fullLines
        roofDy = [roofY[i] - roofY[i+1] for i in range(len(roofY) - 1)]
        if len(roofY) <= 0:
            stdY = 0
        else:
            stdY = math.sqrt(sum([y ** 2 for y in roofY]) / len(roofY) - (sum(roofY) / len(roofY)) ** 2)
        if len(roofDy) <= 0:
            stdDY = 0
        else:
            stdDY = math.sqrt(sum([y ** 2 for y in roofDy]) / len(roofDy) - (sum(roofDy) / len(roofDy)) ** 2)
        absDy = sum([abs(x) for x in roofDy])
        maxDy = max(roofY) - min(roofY)
        score = fullLines * 1.8 - vHoles * 1.0 - vBlocks * 0.5 - maxHeight ** 1.5 * 0.02 \
            - stdY * 0.0 - stdDY * 0.01 - absDy * 0.2 - maxDy * 0.3
        return score
    
    ######################
    #       Helpers      #
    ######################
    
    def cleanState(self, board):
        # Convert all non-zero elements in the board to 1
        board[board != 0] = 1
        tuple_board = tuple(map(tuple, board))
        return tuple_board
    
# Agent 2
    
class Tetris_AI_2(object):

    def __init__(self, **args):
        self.q_values = {}
        self.alpha = 0.1
        self.gamma = 0.1

    def getQValue(self, state):
        if state in self.q_values:
            return self.q_values[state]
        return 0.0
    
    def getReward(self, strategy, board, d1, x1, dropDist):
        if strategy == 1: # patient
            return self.calculateScore(board, d1, x1, dropDist)
        return self.calculateScore2(board, d1, x1, dropDist) # agressive
    
    def nextMove2(self):
        if BOARD2_DATA.currentShape == Shape.shapeNone:
            return None

        strategy = None
        if BOARD2_DATA.currentShape.shape in (Shape.shapeI, Shape.shapeZ, Shape.shapeS):
            d0Range = (0, 1)
        elif BOARD2_DATA.currentShape.shape == Shape.shapeO:
            d0Range = (0,)
        else:
            d0Range = (0, 1, 2, 3)

        if BOARD2_DATA.nextShape.shape in (Shape.shapeI, Shape.shapeZ, Shape.shapeS):
            d1Range = (0, 1)
        elif BOARD2_DATA.nextShape.shape == Shape.shapeO:
            d1Range = (0,)
        else:
            d1Range = (0, 1, 2, 3)

        for d0 in d0Range:
            minX, maxX, _, _ = BOARD2_DATA.currentShape.getBoundingOffsets(d0)
            for x0 in range(-minX, BOARD2_DATA.width - maxX):
                board = self.calcStep1Board2(d0, x0)
                for d1 in d1Range:
                    minX, maxX, _, _ = BOARD2_DATA.nextShape.getBoundingOffsets(d1)
                    dropDist = self.calcNextDropDist2(board, d1, range(-minX, BOARD2_DATA.width - maxX))
                    for x1 in range(-minX, BOARD2_DATA.width - maxX):
                        score = self.calculateScore2(np.copy(board), d1, x1, dropDist)
                        if not strategy or strategy[2] < score:
                            strategy = (d0, x0, score)
        return strategy
    
    def calcNextDropDist2(self, data, d0, xRange):
        res = {}
        for x0 in xRange:
            if x0 not in res:
                res[x0] = BOARD2_DATA.height - 1
            for x, y in BOARD2_DATA.nextShape.getCoords(d0, x0, 0):
                yy = 0
                while yy + y < BOARD2_DATA.height and (yy + y < 0 or data[(y + yy), x] == Shape.shapeNone):
                    yy += 1
                yy -= 1
                if yy < res[x0]:
                    res[x0] = yy
        return res
    
    def calcStep1Board2(self, d0, x0):
        board = np.array(BOARD2_DATA.getData()).reshape((BOARD2_DATA.height, BOARD2_DATA.width))
        self.dropDown2(board, BOARD2_DATA.currentShape, d0, x0)
        return board

    def dropDown2(self, data, shape, direction, x0):
        dy = BOARD2_DATA.height - 1
        for x, y in shape.getCoords(direction, x0, 0):
            yy = 0
            while yy + y < BOARD2_DATA.height and (yy + y < 0 or data[(y + yy), x] == Shape.shapeNone):
                yy += 1
            yy -= 1
            if yy < dy:
                dy = yy
        self.dropDownByDist(data, shape, direction, x0, dy)

    def dropDownByDist(self, data, shape, direction, x0, dist):
        for x, y in shape.getCoords(direction, x0, 0):
            data[y + dist, x] = shape.shape
    
    def calculateScore2(self, step1Board, d1, x1, dropDist):
        # print("calculateScore")
        t1 = datetime.now()
        width = BOARD2_DATA.width
        height = BOARD2_DATA.height

        self.dropDownByDist(step1Board, BOARD2_DATA.nextShape, d1, x1, dropDist[x1])
        # print(datetime.now() - t1)

        # Term 1: lines to be removed
        fullLines, nearFullLines = 0, 0
        roofY = [0] * width
        holeCandidates = [0] * width
        holeConfirm = [0] * width
        vHoles, vBlocks = 0, 0
        for y in range(height - 1, -1, -1):
            hasHole = False
            hasBlock = False
            for x in range(width):
                if step1Board[y, x] == Shape.shapeNone:
                    hasHole = True
                    holeCandidates[x] += 1
                else:
                    hasBlock = True
                    roofY[x] = height - y
                    if holeCandidates[x] > 0:
                        holeConfirm[x] += holeCandidates[x]
                        holeCandidates[x] = 0
                    if holeConfirm[x] > 0:
                        vBlocks += 1
            if not hasBlock:
                break
            if not hasHole and hasBlock:
                fullLines += 1
        vHoles = sum([x ** .7 for x in holeConfirm])
        maxHeight = max(roofY) - fullLines
        # print(datetime.now() - t1)

        roofDy = [roofY[i] - roofY[i+1] for i in range(len(roofY) - 1)]

        if len(roofY) <= 0:
            stdY = 0
        else:
            stdY = math.sqrt(sum([y ** 2 for y in roofY]) / len(roofY) - (sum(roofY) / len(roofY)) ** 2)
        if len(roofDy) <= 0:
            stdDY = 0
        else:
            stdDY = math.sqrt(sum([y ** 2 for y in roofDy]) / len(roofDy) - (sum(roofDy) / len(roofDy)) ** 2)

        absDy = sum([abs(x) for x in roofDy])
        maxDy = max(roofY) - min(roofY)
        # print(datetime.now() - t1)

        score = fullLines * 1.8 - vHoles * 1.0 - vBlocks * 0.5 - maxHeight ** 1.5 * 0.02 \
            - stdY * 0.0 - stdDY * 0.01 - absDy * 0.2 - maxDy * 0.3
        # print(score, fullLines, vHoles, vBlocks, maxHeight, stdY, stdDY, absDy, roofY, d0, x0, d1, x1)
        return score

Agent1 = Tetris_AI_1()
Agent2 = Tetris_AI_2()


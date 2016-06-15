#!/usr/bin/env python
#coding:utf-8

from random import randint
from BaseAI import BaseAI
import time
import math
import Grid

class PlayerAI(BaseAI):
    def __init__(self):
        #self.minSearchTime = 1
        self.directionVectors = (UP_VEC, DOWN_VEC, LEFT_VEC, RIGHT_VEC) = ((-1, 0), (1, 0), (0, -1), (0, 1))
        self.moveMap = ["UP", "DOWN", "LEFT", "RIGHT"]

    def getAvailableGridCells(self, grid):
        cells = []
        for i in range(grid.size):
            for j in range(grid.size):
                if grid.map[i][j] == 0:
                    cells.append((i, j))
        return cells

    def cellOccupied(self, grid, position):
        return self.withinBounds(grid, position) and grid.map[position[0]][position[1]] > 0

    def cellAvailable(self, grid, position):
        return not self.cellOccupied(grid, position)
        
    def withinBounds(self, grid, position):
        return position[0] >= 0 and position[0] < grid.size and position[1] >= 0 and position[1] < grid.size

    def getMove(self, grid):
        return self.iterativeDeepening(grid)

    def iterativeDeepening(self, grid):
        # not really iterative now, the depth is hard code now.
        # return self.search(4, -10000, 10000, 0, 0, grid, True)
        best_move = None
        emptyCells = len(self.getAvailableGridCells(grid))
        if emptyCells <= 4:
            depth = 4
        else:
            depth = 3
        for i in range(depth):
            result = self.search(i, -10000, 10000, grid, True)
            if result["move"] == None:
                break
            else:
                best_move = result["move"]
        if best_move == None:
            #print "The move is " + self.moveMap[best_move]
            raise Exception("No move is provided!")
        return best_move

    def smoothness(self, grid):
        smoothness = 0
        for x in range(grid.size):
            for y in range(grid.size):
                if grid.map[x][y] != 0:
                    value = math.log(grid.map[x][y]) / math.log(2)
                    for index in [1, 3]:
                        directionVec = self.directionVectors[index]
                        targetCell = self.findFarthestPosition(grid, (x, y), directionVec)["next"]
                        if self.cellOccupied(grid, targetCell):
                            target = grid.map[targetCell[0]][targetCell[1]]
                            targetValue = math.log(target) / math.log(2)
                            smoothness -= abs(value - targetValue)
        return smoothness

    def findFarthestPosition(self, grid, position, directionVec):
        if not self.withinBounds(grid, position):
            raise Exception("the position is not valid for the board")
        cell = position
        while True:
            previous = cell
            cell = (previous[0] + directionVec[0], previous[1] + directionVec[1])
            if not self.withinBounds(grid, cell) or not self.cellAvailable(grid, cell):
                return {
                "farthest": previous, "next": cell
                }

    def islands(self, grid):
        that = self
        def dfs(board, markMap, pos, value):
            if that.cellOccupied(board, pos) and board.map[pos[0]][pos[1]] == value and markMap[pos[0]][pos[1]] == False:
                markMap[pos[0]][pos[1]] = True
                for index in [0, 1, 2, 3]:
                    directionVec = self.directionVectors[index]
                    dfs(board, markMap, (pos[0] + directionVec[0], pos[1] + directionVec[1]), value)

        markMap = []
        for x in range(grid.size):
            markMap.append([])
            for y in range(grid.size):
                markMap[x].append(False)
        islandsNum = 0
        for x in range(grid.size):
            for y in range(grid.size):
                if grid.map[x][y] > 0 and not markMap[x][y]:
                    islandsNum = islandsNum + 1
                    dfs(grid, markMap, (x, y), grid.map[x][y])
        return islandsNum

    def search(self, depth, alpha, beta, grid, isPlayer):

        bestScore = None
        bestMove = None
        result = None
        if isPlayer:
            bestScore = alpha
            for direction in range(4): # up down left right
                newGrid = grid.clone()
                if newGrid.move(direction):
                    if not newGrid.canMove():
                        print "cannot move!"
                        return {"move": direction, "score": self.eval(newGrid)}

                    if depth == 0:
                        score_candidate = self.eval(newGrid)
                        if score_candidate > bestScore:
                            bestScore = score_candidate
                            bestMove = direction
                        #return {"move": direction, "score": self.eval(newGrid)}
                        continue

                    result = self.search(depth - 1, bestScore, beta, newGrid, False)

                    if result["score"] > bestScore:
                        bestScore = result["score"]
                        bestMove = direction
                    if bestScore > beta:
                        return {
                            "move": bestMove, "score": beta
                        }
        else:
            bestScore = beta
            candidates = []
            cells = self.getAvailableGridCells(grid)
            scores = {2: [], 4: []}
            for key, value in scores.iteritems():
                for idx, position in enumerate(cells):
                    scores[key].append(None)
                    grid.insertTile(position, key)
                    # evaluate the score
                    scores[key][idx] = self.islands(grid) - self.smoothness(grid)
                    grid.insertTile(position, 0)
            # now just pick out the most annoying moves
            maxScore = max([max(scores[2]), max(scores[4])])
            for key, value in scores.iteritems():
                for idx, score in enumerate(value):
                    if maxScore == score:
                        candidates.append({"position": cells[idx], "tileValue": key})
            # search on each candidate
            for candidate in candidates:
                position = candidate["position"]
                value = candidate["tileValue"]
                newGrid = grid.clone()
                newGrid.insertTile(position, value)
                result = self.search(depth, alpha, bestScore, newGrid, True)
                if result["score"] < bestScore:
                    bestScore = result["score"]
                if bestScore < alpha:
                    #return {"move": None, "score": alpha}
                    return {"move": None, "score": bestScore}
        return {"move": bestMove, "score": bestScore}

    def eval(self, grid):
        emptyCells = self.getAvailableGridCells(grid)
        emptyCellsNum = len(emptyCells)
        smoothWeight = 0.1
        mono2Weight = 1.0
        emptyWeight = 2.7
        maxWeight = 1.0
        return self.smoothness(grid) * smoothWeight + self.monotonicity2(grid) * mono2Weight + math.log(emptyCellsNum) * emptyWeight + self.gridMaxValue(grid) * maxWeight

    def gridMaxValue(self, grid):
        maxValue = 0
        for x in range(grid.size):
            for y in range(grid.size):
                if self.cellOccupied(grid, (x, y)):
                    value = grid.map[x][y]
                    if value > maxValue:
                        maxValue = value
        return math.log(maxValue) / math.log(2)

    def monotonicity2(self, grid):
        # measures how monotonic the grid is. This means the values of the tiles are strictly increasing or decreasing in both the left/right and up/down directions

        # scores for all four directions
        totals = [0, 0, 0, 0]

        # up/down direction
        for col in range(grid.size):
            curRow = 0
            nextRow = curRow + 1
            while nextRow < 4:
                while nextRow < 4 and not self.cellOccupied(grid, (nextRow, col)):
                    nextRow = nextRow + 1
                if nextRow >= 4:
                    nextRow = nextRow - 1
                currentValue = 0
                if self.cellOccupied(grid, (curRow, col)):
                    currentValue = math.log(grid.map[curRow][col]) / math.log(2)
                nextValue = 0
                if self.cellOccupied(grid, (nextRow, col)):
                    currentValue = math.log(grid.map[nextRow][col]) / math.log(2)
                if currentValue > nextValue:
                    totals[0] += nextValue - currentValue
                elif nextValue > currentValue:
                    totals[1] += currentValue - nextValue
                curRow = nextRow
                nextRow = nextRow + 1

        # left/right direction
        for row in range(grid.size):
            curCol = 0
            nextCol = curCol + 1
            while nextCol < 4:
                while nextCol < 4 and not self.cellOccupied(grid, (row, nextCol)):
                    nextCol = nextCol + 1
                if nextCol >= 4:
                    nextCol = nextCol - 1
                currentValue = 0
                if self.cellOccupied(grid, (row, curCol)):
                    currentValue = math.log(grid.map[row][curCol]) / math.log(2)
                nextValue = 0
                if self.cellOccupied(grid, (row, nextCol)):
                    currentValue = math.log(grid.map[row][nextCol]) / math.log(2)
                if currentValue > nextValue:
                    totals[2] += nextValue - currentValue
                elif nextValue > currentValue:
                    totals[3] += currentValue - nextValue
                curCol = nextCol
                nextCol = nextCol + 1
        return max([totals[0], totals[1]]) + max([totals[2], totals[3]])

def main():
    test_grid = Grid.Grid()
    test_grid.map = [[2, 8, 16, 2], [4, 64, 32, 4], [8, 32, 128, 1024], [2, 8, 4, 4]]
    player = PlayerAI()
    print player.getMove(test_grid)

if __name__ == '__main__':
	main()
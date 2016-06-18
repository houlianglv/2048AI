#!/usr/bin/env python
# coding:utf-8

from BaseAI import BaseAI
import Grid
import time

infinity = 1.0e400


class PlayerAI(BaseAI):
    def __init__(self, t_limit):
        self.directionVectors = ((-1, 0), (1, 0), (0, -1), (0, 1))  # UP DOWN LEFT RIGHT
        self.gradients = [[[0.135759, 0.121925, 0.102812, 0.099937],
                           [0.09997992, 0.0888405, 0.076711, 0.0724143],
                           [0.060654, 0.0562579, 0.037116, 0.0161889],
                           [0.0125498, 0.00992495, 0.00575871, 0.00335193]],
                          [[0.0125498, 0.060654, 0.09997992, 0.135759],
                           [0.00992495, 0.0562579, 0.0888405, 0.121925],
                           [0.00575871, 0.037116, 0.076711, 0.102812],
                           [0.00335193, 0.0161889, 0.0724143, 0.099937]],
                          [[0.00335193, 0.00575871, 0.00992495, 0.0125498],
                           [0.0161889, 0.037116, 0.0562579, 0.060654],
                           [0.0724143, 0.076711, 0.0888405, 0.09997992],
                           [0.099937, 0.102812, 0.121925, 0.135759]],
                          [[0.099937, 0.0724143, 0.0161889, 0.00335193],
                           [0.102812, 0.076711, 0.037116, 0.00575871],
                           [0.121925, 0.0888405, 0.0562579, 0.00992495],
                           [0.135759, 0.09997992, 0.060654, 0.0125498]]]
        self.time_limit = None
        self.t_limit = t_limit

    @staticmethod
    def get_available_grid_cells(grid):
        cells = []
        for i in range(grid.size):
            for j in range(grid.size):
                if grid.map[i][j] == 0:
                    cells.append((i, j))
        return cells

    @staticmethod
    def cell_occupied(grid, position):
        return PlayerAI.within_bounds(grid, position) and grid.map[position[0]][position[1]] > 0

    @staticmethod
    def cell_available(grid, position):
        return not PlayerAI.cell_occupied(grid, position)

    @staticmethod
    def within_bounds(grid, position):
        return 0 <= position[0] < grid.size and 0 <= position[1] < grid.size

    def getMove(self, grid):
        # iterative_deepening with time limitation
        self.time_limit = time.time() + self.t_limit
        best_move = -1
        # depth = 4
        depth = 1
        while time.time() < self.time_limit:
            move_score = self.search(grid, -infinity, infinity, depth, True)
            if move_score.direction is -1:
                break
            best_move = move_score.direction
            depth += 1

        if best_move is -1:
            raise Exception("No move is provided!")
        return best_move

    def search(self, grid, alpha, beta, depth, player):
        # check the depth
        if time.time() >= self.time_limit:
            return MoveScore(-1, None)
        if depth is 0:
            return MoveScore(-1, self.eval(grid))
        if player:
            return self.max_value(grid, alpha, beta, depth)
        else:
            return self.min_value(grid, alpha, beta, depth)

    def max_value(self, grid, alpha, beta, depth):
        v = -infinity
        move = -1
        blocked_directions = 0
        for direction in range(4):
            new_grid = grid.clone()
            if new_grid.move(direction):
                if depth is 0:
                    score = self.eval(grid)
                    if score > v:
                        v = score
                        move = direction
                    continue
                # min_value returns a instance of MoveScore
                move_score = self.search(new_grid, alpha, beta, depth - 1, False)
                # check if the time limit is reached
                if move_score.score is None:
                    return move_score
                if move_score.score > v:
                    v = move_score.score
                    move = direction
                if v >= beta:
                    return MoveScore(direction, v, cutoff=True)
                if v > alpha:
                    alpha = v
            else:
                # when you cannot move:
                blocked_directions += 1
        if blocked_directions is 4:
            return MoveScore(-1, self.eval(grid))
        else:
            return MoveScore(move, v)

    def min_value(self, grid, alpha, beta, depth):
        v = infinity
        cells = self.get_available_grid_cells(grid)
        children = []
        for cell in cells:
            new_grid = grid.clone()
            new_grid.insertTile(cell, 2)
            children.append(new_grid)
        for cell in cells:
            new_grid = grid.clone()
            new_grid.insertTile(cell, 4)
            children.append(new_grid)

        # search on each candidate
        for child in children:
            move_score = self.search(child, alpha, beta, depth - 1, True)
            # check if time limit is reached
            if move_score.score is None:
                return move_score
            if move_score.score < v:
                v = move_score.score
            if v <= alpha:
                return MoveScore(-1, v, True)
            beta = min(beta, v)

        return MoveScore(-1, v)

    def eval(self, grid):
        max_score = None
        for weight_matrix in self.gradients:
            score = 0.0
            for x in range(4):
                for y in range(4):
                    score += grid.map[x][y] * weight_matrix[x][y]
            if score > max_score:
                max_score = score
        return max_score


class MoveScore:
    def __init__(self, direction, score, cutoff=False):
        self.direction = direction
        self.score = score
        self.cutoff = cutoff


def main():
    test_grid = Grid.Grid()
    test_grid.map = [[2, 8, 16, 2], [4, 64, 32, 4], [8, 32, 128, 1024], [2, 8, 4, 4]]
    player = PlayerAI()
    print player.getMove(test_grid)


if __name__ == '__main__':
    main()

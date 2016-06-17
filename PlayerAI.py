#!/usr/bin/env python
# coding:utf-8

from BaseAI import BaseAI
import Grid
import time
import math

infinity = 1.0e400


class PlayerAI(BaseAI):
    def __init__(self):
        self.directionVectors = ((-1, 0), (1, 0), (0, -1), (0, 1))  # UP DOWN LEFT RIGHT
        self.time_limit = None
        self.current_max_tile = None
        self.threshold = 256
        self.snakes = [[[15, 14, 13, 12],
                       [8, 9, 10, 11],
                       [7, 6, 5, 4],
                       [0, 1, 2, 3]],

                       [[15, 8, 7, 0],
                        [14, 9, 6, 1],
                        [13, 10, 5, 2],
                        [12, 11, 4, 3]],

                       [[12, 13, 14, 15],
                       [11, 10, 9, 8],
                       [4, 5, 6, 7],
                       [3, 2, 1, 0]],

                       [[0, 7, 8, 15],
                       [1, 6, 9, 14],
                       [2, 5, 10, 13],
                       [3, 4, 11, 12]],

                       [[3, 4, 11, 12],
                       [2, 5, 10, 13],
                       [1, 6, 9, 14],
                       [0, 7, 8, 15]],

                       [[3, 2, 1, 0],
                        [4, 5, 6, 7],
                        [11, 10, 9, 8],
                        [12, 13, 14, 15]],

                       [[0, 1, 2, 3],
                       [7, 6, 5, 4],
                       [8, 9, 10, 11],
                       [15, 14, 13, 12]],

                       [[12, 11, 4, 3],
                       [13, 10, 5, 2],
                       [14, 9, 6, 1],
                       [15, 8, 7, 0]]]

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
        best_move = -1
        # iterative_deepening with time limitation
        self.time_limit = time.time() + 0.98

        depth = 4
        while time.time() < self.time_limit:
            move_score = self.search(grid, -infinity, infinity, depth, True)
            if move_score.direction is -1:
                break
            best_move = move_score.direction
            depth += 1

        if best_move is -1:
            raise Exception("No move is provided!")
        return best_move

    def update_max_tile(self, grid):
        if self.current_max_tile >= self.threshold:
            return
        else:
            for x in [0, 1, 2, 3]:
                for y in [0, 1, 2, 3]:
                    if grid.map[x][y] >= self.threshold:
                        self.current_max_tile = grid.map[x][y]
                        return

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
        scores = {2: [], 4: []}
        for key, value in scores.iteritems():
            for idx, position in enumerate(cells):
                scores[key].append(None)
                grid.insertTile(position, key)
                # evaluate the score
                scores[key][idx] = self.eval(grid)
                grid.insertTile(position, 0)
        # now just pick out the most annoying moves
        candidates = []
        min_score = min([min(scores[2]), min(scores[4])])
        for key, value in scores.iteritems():
            for idx, score in enumerate(value):
                if min_score == score:
                    candidates.append({"position": cells[idx], "tileValue": key})
        # search on each candidate
        for candidate in candidates:
            position = candidate["position"]
            value = candidate["tileValue"]
            new_grid = grid.clone()
            new_grid.insertTile(position, value)
            move_score = self.search(new_grid, alpha, beta, depth - 1, True)
            # check if time limit is reached
            if move_score.score is None:
                return move_score
            if move_score.score < v:
                v = move_score.score
            if v <= alpha:
                return MoveScore(-1, v, True)
            beta = min([beta, v])
        return MoveScore(-1, v)

    def eval(self, grid):
        # return self.weight_score(grid)
        return self.snake_weight_score(grid)

    def weight_score(self, grid):
        max_score = None
        for weight_matrix in self.gradients:
            score = 0.0
            for x in range(4):
                for y in range(4):
                    score += grid.map[x][y] * weight_matrix[x][y]
            if score > max_score:
                max_score = score
        return max_score

    def snake_weight_score(self, grid):
        max_score = None
        for snake in self.snakes:
            score = 0
            for x in range(4):
                for y in range(4):
                    # use left shift
                    score += grid.map[x][y] << snake[x][y]
            if score > max_score:
                max_score = score
        return max_score

    def one_move_direction(self, grid):
        best = -1
        best_score = None
        for direction in range(4):
            new_grid = grid.clone()
            new_grid.move(direction)
            score = self.eval(new_grid)
            if score > best_score:
                best_score = score
                best = direction
        return best


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

#!/usr/bin/env python
# coding:utf-8

from BaseAI import BaseAI
import Grid
import time

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

    def update_max_tile(self, grid):
        if self.current_max_tile >= self.threshold:
            return
        else:
            for x in [0, 1, 2, 3]:
                for y in [0, 1, 2, 3]:
                    if grid.map[x][y] >= self.threshold:
                        self.current_max_tile = grid.map[x][y]
                        return

    def getMove(self, grid):
        best_move = -1
        # iterative_deepening with time limitation
        self.time_limit = time.time() + 0.98

        depth = 4
        while time.time() < self.time_limit:
            move_score = self.alpha_beta(grid, depth, -infinity, infinity, True)
            if move_score.direction is -1:
                break
            best_move = move_score.direction
            depth += 1

        if best_move is -1:
            raise Exception("No move is provided!")
        return best_move

    def alpha_beta(self, grid, depth, alpha, beta, player):
        if time.time() >= self.time_limit:
            return MoveScore(-1, None)
        if player:
            children = []
            for i in range(4):
                new_grid = grid.clone()
                if new_grid.move(i):
                    children.append((i, new_grid))
            if len(children) is 0:
                # when player cannot move
                return MoveScore(-1, self.eval(grid))
            new_alpha = alpha
            best_move = -1
            for child in children:
                direction = child[0]
                child_grid = child[1]
                if depth is 0:
                    # if the depth is 0, evaluate the current board
                    move_score = MoveScore(-1, self.eval(grid))
                else:
                    move_score = self.alpha_beta(child_grid, depth - 1, new_alpha, beta, False)
                if move_score.score is None:
                    # when reach the time limitation
                    return move_score
                if move_score.score > new_alpha:
                    new_alpha = move_score.score
                    best_move = direction
                if new_alpha >= beta:
                    break
            return MoveScore(best_move, new_alpha)
        else:
            empty_cells = self.get_available_grid_cells(grid)
            new_beta = beta
            for cell in empty_cells:
                # insert 2
                grid.insertTile(cell, 2)
                if depth is 0:
                    # when depth is 0, eval the current board
                    new_beta = self.eval(grid)
                else:
                    new_beta = min(new_beta, self.alpha_beta(grid, depth - 1, alpha, new_beta, True).score)
                grid.insertTile(cell, 0)
                if new_beta <= alpha:
                    return MoveScore(-1, new_beta)
            for cell in empty_cells:
                # insert 4
                grid.insertTile(cell, 4)
                if depth is 0:
                    # when depth is 0, eval the current board
                    new_beta = self.eval(grid)
                else:
                    new_beta = min(new_beta, self.alpha_beta(grid, depth - 1, alpha, new_beta, True).score)
                grid.insertTile(cell, 0)
                if new_beta <= alpha:
                    return MoveScore(-1, new_beta)
            return MoveScore(-1, new_beta)

    def eval(self, grid):
        return self.snake_weight_score(grid)

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

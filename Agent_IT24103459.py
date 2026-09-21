import random
from collections import deque
import heapq
import math


class SimpleReflexAgent:
    """
    Practicals 1: reacts purely to the current percept via condition-action
    rules. Has NO memory of past percepts or actions.
    """
    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        wall_ahead = percept.get('wall_ahead', False)
        food_here = percept.get('food_here', False)

        # Condition-action rules, evaluated purely from the current percept
        if food_here:
            return 'Stay'
        if wall_ahead:
            # turn to a different direction rather than walking into the wall
            return random.choice(['Left', 'Right', 'Down', 'Up'])
        return random.choice(self.actions_pool)


class ModelBasedAgent:
    """
    Practical 2: keeps an internal model of the world (here, its last
    action) so it can react differently to a repeated percept and avoid
    getting stuck oscillating against the same wall.
    """
    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']
        self.last_action = None   # internal state / memory

    def sense_and_act(self, percept: dict) -> str:
        wall_ahead = percept.get('wall_ahead', False)
        food_here = percept.get('food_here', False)

        if food_here:
            action = 'Stay'
        elif wall_ahead:
            # use memory: don't repeat the action that just failed
            alternatives = [a for a in self.actions_pool if a != self.last_action]
            action = random.choice(alternatives)
        else:
            action = random.choice(self.actions_pool)

        self.last_action = action
        return action


class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""
    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        # If standing directly on food, or just wander / move towards coordinates
        pos = percept['agent_pos']
        # Simple heuristic or fallback random sweep
        return random.choice(self.actions_pool)


class SearchAgent:
    """
    Goal-based / planning agent.
    Practical 03: BFS, DFS, UCS (uninformed search)
    Practical 04: A* (informed search, with Manhattan / Euclidean heuristics)
    """

    def __init__(self):
        self.plan = []
        self.active_algo = 'BFS'   # 'BFS', 'DFS', 'UCS', or 'AStar'
        self.last_nodes_expanded = 0   # set by each *_search call for instrumentation

    # ------------------------------------------------------------------
    # Shared helper: valid orthogonal neighbours of a cell
    # ------------------------------------------------------------------
    def _neighbors(self, pos, walls, grid_size):
        x, y = pos
        # Cartesian convention: Up increases y, Down decreases y (matches the
        # grid diagrams in the practical sheets, where row 0 is the bottom row)
        moves = [('Up', 0, 1), ('Down', 0, -1), ('Left', -1, 0), ('Right', 1, 0)]
        for action, dx, dy in moves:
            nx, ny = x + dx, y + dy
            if 0 <= nx < grid_size[0] and 0 <= ny < grid_size[1] and (nx, ny) not in walls:
                yield action, (nx, ny)

    # ------------------------------------------------------------------
    # Practical 04 — Heuristic functions
    # ------------------------------------------------------------------
    def manhattan_distance(self, pos, goal):
        x1, y1 = pos
        x2, y2 = goal
        return abs(x1 - x2) + abs(y1 - y2)

    def euclidean_distance(self, pos, goal):
        x1, y1 = pos
        x2, y2 = goal
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    # ------------------------------------------------------------------
    # Practical 03 — BFS: FIFO queue, shallowest node first
    # ------------------------------------------------------------------
    def bfs_search(self, start_pos, goal_pos, walls, grid_size):
        frontier = deque([(start_pos, [])])   # (current_pos, path_taken)
        reached = {start_pos}
        nodes_expanded = 0

        while frontier:
            current_pos, path_taken = frontier.popleft()
            nodes_expanded += 1

            if current_pos == goal_pos:
                self.last_nodes_expanded = nodes_expanded
                return path_taken

            for action, neighbor in self._neighbors(current_pos, walls, grid_size):
                if neighbor not in reached:
                    reached.add(neighbor)
                    frontier.append((neighbor, path_taken + [action]))

        self.last_nodes_expanded = nodes_expanded
        return []

    # ------------------------------------------------------------------
    # Practical 03 — DFS: LIFO stack, deepest node first
    # ------------------------------------------------------------------
    def dfs_search(self, start_pos, goal_pos, walls, grid_size):
        frontier = [(start_pos, [])]          # stack: (current_pos, path_taken)
        reached = {start_pos}
        nodes_expanded = 0

        while frontier:
            current_pos, path_taken = frontier.pop()
            nodes_expanded += 1

            if current_pos == goal_pos:
                self.last_nodes_expanded = nodes_expanded
                return path_taken

            for action, neighbor in self._neighbors(current_pos, walls, grid_size):
                if neighbor not in reached:
                    reached.add(neighbor)
                    frontier.append((neighbor, path_taken + [action]))

        self.last_nodes_expanded = nodes_expanded
        return []

    # ------------------------------------------------------------------
    # Practical 03 — UCS: priority queue ordered by path cost g(n)
    # ------------------------------------------------------------------
    def ucs_search(self, start_pos, goal_pos, walls, grid_size):
        frontier = []                          # (g_cost, current_pos, path_taken)
        heapq.heappush(frontier, (0, start_pos, []))
        reached = set()
        nodes_expanded = 0

        while frontier:
            g_cost, current_pos, path_taken = heapq.heappop(frontier)

            if current_pos == goal_pos:
                self.last_nodes_expanded = nodes_expanded
                return path_taken

            if current_pos in reached:
                continue
            reached.add(current_pos)
            nodes_expanded += 1

            for action, neighbor in self._neighbors(current_pos, walls, grid_size):
                if neighbor not in reached:
                    g_new = g_cost + 1
                    heapq.heappush(frontier, (g_new, neighbor, path_taken + [action]))

        self.last_nodes_expanded = nodes_expanded
        return []

    # ------------------------------------------------------------------
    # Practical 04 — A*: priority queue ordered by f(n) = g(n) + h(n)
    # ------------------------------------------------------------------
    def astar_search(self, start_pos, goal_pos, walls, grid_size,
                      heuristic_type='manhattan'):
        heuristic_fn = (self.manhattan_distance if heuristic_type == 'manhattan'
                         else self.euclidean_distance)

        frontier = []          # (f_cost, g_cost, current_pos, path_taken)
        reached_states = set()
        nodes_expanded = 0

        h0 = heuristic_fn(start_pos, goal_pos)
        heapq.heappush(frontier, (h0, 0, start_pos, []))

        while frontier:
            f_cost, g_cost, current_pos, path_taken = heapq.heappop(frontier)

            if current_pos == goal_pos:
                self.last_nodes_expanded = nodes_expanded
                return path_taken

            if current_pos in reached_states:
                continue
            reached_states.add(current_pos)
            nodes_expanded += 1

            for action, neighbor in self._neighbors(current_pos, walls, grid_size):
                if neighbor not in reached_states:
                    g_new = g_cost + 1
                    h_new = heuristic_fn(neighbor, goal_pos)
                    f_new = g_new + h_new
                    heapq.heappush(frontier, (f_new, g_new, neighbor, path_taken + [action]))

        self.last_nodes_expanded = nodes_expanded
        return []

    # ------------------------------------------------------------------
    # Decision loop — shared by BFS / DFS / UCS / A*
    # ------------------------------------------------------------------
    def sense_and_act(self, percept: dict) -> str:
        if not self.plan:
            all_food = [tuple(f) for f in percept['all_food']]
            walls = {tuple(w) for w in percept['walls']}
            grid_size = percept['grid_size']
            current_pos = tuple(percept['agent_pos'])  # positions must be hashable

            if not all_food:
                return None  # nothing left to do

            # closest food by Manhattan distance, used as the search target
            goal_pos = min(
                all_food,
                key=lambda f: abs(f[0] - current_pos[0]) + abs(f[1] - current_pos[1])
            )

            if self.active_algo == 'BFS':
                self.plan = self.bfs_search(current_pos, goal_pos, walls, grid_size)
            elif self.active_algo == 'DFS':
                self.plan = self.dfs_search(current_pos, goal_pos, walls, grid_size)
            elif self.active_algo == 'UCS':
                self.plan = self.ucs_search(current_pos, goal_pos, walls, grid_size)
            elif self.active_algo == 'AStar':
                self.plan = self.astar_search(current_pos, goal_pos, walls, grid_size,
                                               heuristic_type='manhattan')

        if not self.plan:
            return None

        return self.plan.pop(0)

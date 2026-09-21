# se3062_visual_grid_game.py
import random
import tkinter as tk

DIRECTION_ORDER = ['Up', 'Left', 'Down', 'Right']   # counter-clockwise order
DELTA = {'Up': (0, 1), 'Down': (0, -1), 'Left': (-1, 0), 'Right': (1, 0)}


class VisualGridHuntGame:
    """Heading-based Pacman-style grid environment (Partially Observable)."""

    def __init__(self, width=10, height=10, num_food=10, num_opponents=2,
                 custom_walls=None, start_pos=(0, 0), start_facing='Up'):
        self.width = width
        self.height = height
        self.agent_pos = list(start_pos)
        self.facing = start_facing

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos_tuple = (fx, fy)
            if pos_tuple != tuple(self.agent_pos) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            if (tuple(op_pos) != tuple(self.agent_pos) and tuple(op_pos) not in self.walls
                    and tuple(op_pos) not in self.food_positions):
                self.opponents.append(op_pos)

        # Carried over from Lab 01 (toxic hazard)
        self.toxic_traps = set()
        num_traps = max(1, num_food // 3)
        while len(self.toxic_traps) < num_traps:
            tx = random.randint(0, self.width - 1)
            ty = random.randint(0, self.height - 1)
            trap_pos = (tx, ty)
            if (trap_pos != tuple(self.agent_pos) and trap_pos not in self.walls
                    and trap_pos not in self.food_positions and trap_pos not in self.toxic_traps):
                self.toxic_traps.add(trap_pos)

        self.score = 0
        self.steps = 0
        self.collision = False

    # ------------------------------------------------------------------
    # Step 1.1: local, heading-relative percept — NO global coordinates
    # ------------------------------------------------------------------
    def _cell_ahead(self):
        dx, dy = DELTA[self.facing]
        return (self.agent_pos[0] + dx, self.agent_pos[1] + dy)

    def get_percept(self) -> dict:
        ahead = self._cell_ahead()
        in_bounds = 0 <= ahead[0] < self.width and 0 <= ahead[1] < self.height
        wall_ahead = (not in_bounds) or (ahead in self.walls)

        return {
            'wall_ahead': wall_ahead,
            'food_here': tuple(self.agent_pos) in self.food_positions,
            'smells_toxin': tuple(self.agent_pos) in self.toxic_traps,
            'collision': self.collision,
            'score': self.score,
            'remaining_food': len(self.food_positions),
            # NOTE: intentionally no 'agent_pos', 'walls', or 'all_food' keys —
            # the agent is only allowed to perceive its immediate surroundings.
        }

    # ------------------------------------------------------------------
    # Step 1.1 / 1.2 / 1.3: heading-relative action execution
    # ------------------------------------------------------------------
    def execute_action(self, action: str):
        self.steps += 1

        if action == 'turn_left':
            idx = DIRECTION_ORDER.index(self.facing)
            self.facing = DIRECTION_ORDER[(idx + 1) % 4]
        elif action == 'turn_right':
            idx = DIRECTION_ORDER.index(self.facing)
            self.facing = DIRECTION_ORDER[(idx - 1) % 4]
        elif action == 'move_forward':
            ahead = self._cell_ahead()
            in_bounds = 0 <= ahead[0] < self.width and 0 <= ahead[1] < self.height
            if not in_bounds or ahead in self.walls:
                self.score -= 5   # bumped into a wall / the boundary
            else:
                self.agent_pos = list(ahead)
                if tuple(self.agent_pos) in self.toxic_traps:
                    self.score -= 15
        elif action == 'suck':
            pos = tuple(self.agent_pos)
            if pos in self.food_positions:
                self.food_positions.remove(pos)
                self.score += 20
        # any other/None action: no-op (agent stays put, facing unchanged)

        for op in self.opponents:
            move = random.choice(['Up', 'Down', 'Left', 'Right', 'Stay'])
            if move == 'Up' and op[1] < self.height - 1:
                op[1] += 1
            elif move == 'Down' and op[1] > 0:
                op[1] -= 1
            elif move == 'Left' and op[0] > 0:
                op[0] -= 1
            elif move == 'Right' and op[0] < self.width - 1:
                op[0] += 1
            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 60 or self.collision


class GridGameGUI:
    """Tkinter wrapper — same visuals as Lab 01, plus a heading indicator on the agent."""

    def __init__(self, root, width=10, height=10, num_food=12, num_opponents=2, walls=None, agent=None):
        self.root = root
        self.root.title("SE3062 - Partially Observable Grid Hunt")

        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food,
                                      num_opponents=num_opponents, custom_walls=walls)

        if agent is None:
            from se3062_agent import ModelBasedAgent
            agent = ModelBasedAgent()
        self.agent = agent

        max_canvas_dim = 600
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))
        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()
        self.label = tk.Label(root, text="Score: 0 | Steps: 0", font=("Arial", 14))
        self.label.pack(pady=10)
        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop, font=("Arial", 12),
                             bg="#000066", fg="white")
        self.btn.pack(pady=5)
        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")
        for x in range(self.env.width):
            for y in range(self.env.height):
                x1, y1 = x * self.cell_size, (self.env.height - 1 - y) * self.cell_size
                x2, y2 = x1 + self.cell_size, y1 + self.cell_size
                color = "#f1f5f9" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5,
                                    fill="#f59e0b", outline="#d97706")

        for tx, ty in self.env.toxic_traps:
            offset = self.cell_size * 0.2
            x1 = tx * self.cell_size + offset
            y1 = (self.env.height - 1 - ty) * self.cell_size + offset
            x2, y2 = x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6
            mx = (x1 + x2) / 2
            self.canvas.create_polygon(mx, y1, x2, (y1 + y2) / 2, mx, y2, x1, (y1 + y2) / 2,
                                       fill="#7c3aed", outline="#5b21b6")

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7,
                                fill="#000066", outline="#1e3a8a")
        # small heading tick so you can see which way the agent is facing
        cx, cy = ax * self.cell_size + self.cell_size / 2, (self.env.height - 1 - ay) * self.cell_size + self.cell_size / 2
        dx, dy = DELTA[self.env.facing]
        self.canvas.create_line(cx, cy, cx + dx * self.cell_size * 0.4, cy - dy * self.cell_size * 0.4,
                                fill="#22c55e", width=3)

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)
                self.env.execute_action(action)
                self.draw_grid()
                self.label.config(text=f"Score: {self.env.score} | Steps: {self.env.steps} | Action: {action}")
                self.root.after(250, step)
            else:
                end_text = (f"Collision! Game Over! Final Score: {self.env.score}" if self.env.collision
                           else f"Finished! Final Score: {self.env.score}")
                self.label.config(text=end_text)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
    from se3062_agent import ModelBasedAgent
    root = tk.Tk()
    app = GridGameGUI(root, width=8, height=8, num_food=6, num_opponents=0, agent=ModelBasedAgent())
    root.mainloop()

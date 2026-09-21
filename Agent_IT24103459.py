# se3062_agent.py

class SimpleReflexAgent:
    """
    Step 1.2: strict IF-THEN condition-action rules only.
    No __init__ state, no memory of past percepts or actions — this is what
    makes it fail (see Practical 02 write-up, Q3).
    """

    def sense_and_act(self, percept: dict) -> str:
        # Condition-action rules:
        if percept.get('food_here'):
            return 'suck'
        if percept.get('wall_ahead'):
            return 'turn_left'
        return 'move_forward'


class ModelBasedAgent:
    """
    Step 1.3: keeps an internal state (Transition Model) so it can recognize
    when it's spinning in place — i.e. hitting a wall over and over without
    ever moving — and break the cycle by reversing its turn direction instead
    of blindly repeating 'turn_left' forever.
    """

    def __init__(self):
        self.last_action = None
        self.consecutive_turns = 0   # how many turns in a row with no movement

    def sense_and_act(self, percept: dict) -> str:
        wall_ahead = percept.get('wall_ahead', False)
        food_here = percept.get('food_here', False)

        # --- Update internal state first (Transition & Sensor Model) ---
        if self.last_action == 'move_forward' or self.last_action == 'suck':
            self.consecutive_turns = 0  # we just made progress, reset memory

        # --- Then select an action using memory-aware rules ---
        if food_here:
            action = 'suck'
        elif wall_ahead:
            self.consecutive_turns += 1
            # IF wall_ahead AND we've already been turning the same way for a
            # while (i.e. left_is_visited in the lecture's example), switch
            # rotation direction to escape a spin-in-place cycle.
            action = 'turn_right' if self.consecutive_turns >= 3 else 'turn_left'
        else:
            action = 'move_forward'

        self.last_action = action
        return action

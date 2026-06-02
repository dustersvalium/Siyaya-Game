from __future__ import annotations

import csv
import json
import os
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from age_of_wheels import GameState, MAP_FILE, MapStorage, TARGET_POINTS


Action = Tuple
METRICS_DIR = Path(__file__).resolve().parent / "training_metrics"
TRAINING_CSV = METRICS_DIR / "training_progress.csv"
EVAL_CSV = METRICS_DIR / "evaluation_history.csv"
TRAINING_JSONL = METRICS_DIR / "training_progress.jsonl"
EVAL_JSONL = METRICS_DIR / "evaluation_history.jsonl"


def ensure_metrics_dir() -> None:
    METRICS_DIR.mkdir(exist_ok=True)


def append_csv_row(path: Path, fieldnames: Sequence[str], row: Dict) -> None:
    ensure_metrics_dir()
    file_exists = path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({key: row.get(key) for key in fieldnames})


def append_jsonl_row(path: Path, row: Dict) -> None:
    ensure_metrics_dir()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


class SiyayaTrainingEnv:
    """Wraps the game logic in a training-friendly interface."""

    def __init__(self, map_path: str | None = None, max_turns: int = 250, max_decisions: int = 400):
        if map_path is None:
            map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MAP_FILE)
        self.storage = MapStorage(map_path)
        self.map_data = self.storage.load()
        self.max_turns = max_turns
        self.max_decisions = max_decisions
        self.node_names = [node["name"] for node in self.map_data["nodes"]]
        self.node_to_index = {name: index for index, name in enumerate(self.node_names)}
        self.game = None
        self.decision_count = 0
        self.state_repeat_counts = defaultdict(int)

    def reset(self) -> List[float]:
        """Resets game for new match"""
        self.game = GameState(self.map_data)
        self.decision_count = 0
        self.state_repeat_counts = defaultdict(int)
        return self.get_feature_vector()

    def get_legal_actions(self) -> List[Action]:
        """dictates what the agent can do and returns decisions for each valid action"""
        game = self.game
        if game.winner:
            return []

        if game.pending_owner_fee:
            return [
                ("owner_fee", True),
                ("owner_fee", False),
            ]

        if game.pending_police:
            return [
                ("police", "bribe"),
                ("police", "refuse"),
            ]

        if game.phase == "move":
            return [("move", destination) for destination in game.accessible_moves()]

        if game.phase == "invest":
            actions = [
                ("invest", option["source"], option["destination"])
                for option in game.all_investments()
            ]
            actions.append(("skip_investment",))
            return actions

        return []

    def distance_to_johannesburg(self, start_name: str) -> int:
        """Calculates how far a position is from Joburg"""
        distances = self.game.bfs_distances(start_name)
        return distances.get("Johannesburg", len(self.node_names))

    def count_owned_routes(self, player_name: str) -> int:
        """Counts how many routes/arcs a player owns if invested in"""
        return sum(1 for edge in self.game.edges.values() if edge["owner"] == player_name)

    def count_unclaimed_adjacent(self, player_name: str) -> int:
        position = self._get_player(player_name)["position"]
        return sum(1 for neighbor in self.game.adjacency[position] if neighbor not in self.game.claimed_nodes)

    def count_unclaimed_within_two_steps(self, player_name: str) -> int:
        position = self._get_player(player_name)["position"]
        distances = self.game.bfs_distances(position)
        return sum(
            1
            for node_name, distance in distances.items()
            if 1 <= distance <= 2 and node_name not in self.game.claimed_nodes
        )

    def count_toll_moves(self, player_name: str) -> int:
        player = self._get_player(player_name)
        return sum(
            1
            for neighbor in self.game.adjacency[player["position"]]
            if self.game.toll_cost(player["position"], neighbor) > 0
        )

    def count_police_moves(self, player_name: str) -> int:
        player = self._get_player(player_name)
        return sum(
            1
            for neighbor in self.game.adjacency[player["position"]]
            if self.game.get_edge(player["position"], neighbor)["type"] == "police"
        )

    def get_feature_vector(self) -> List[float]:
        """Small first feature vector for early experiments."""
        game = self.game
        player = game.current_player
        opponent = game.opponent
        legal_actions = self.get_legal_actions()
        player_distance = self.distance_to_johannesburg(player["position"])
        opponent_distance = self.distance_to_johannesburg(opponent["position"])
        cash_advantage = float(player["points"] - opponent["points"])
        distance_advantage = float(opponent_distance - player_distance)
        can_win_if_reach_johannesburg = 1.0 if player["points"] >= TARGET_POINTS else 0.0
        travel_history = player.get("travel_history", set())
        recent_revisit_count = float(max(0, player.get("turns_taken", 0) + 1 - len(travel_history)))

        phase_move = 1.0 if game.phase == "move" else 0.0
        phase_invest = 1.0 if game.phase == "invest" else 0.0
        pending_police = 1.0 if game.pending_police else 0.0
        pending_owner_fee = 1.0 if game.pending_owner_fee else 0.0

        vector = [
            float(player["points"]),
            float(opponent["points"]),
            cash_advantage,
            float(player_distance),
            float(opponent_distance),
            distance_advantage,
            float(len(game.accessible_moves())),
            float(len(game.all_investments()) if game.phase == "invest" else 0),
            float(self.count_owned_routes(player["name"])),
            float(self.count_owned_routes(opponent["name"])),
            float(self.count_unclaimed_adjacent(player["name"])),
            float(self.count_unclaimed_within_two_steps(player["name"])),
            float(self.count_toll_moves(player["name"])),
            float(self.count_police_moves(player["name"])),
            phase_move,
            phase_invest,
            pending_police,
            pending_owner_fee,
            float(player["skip_turn"]),
            float(opponent["skip_turn"]),
            float(max(0, TARGET_POINTS - player["points"])),
            can_win_if_reach_johannesburg,
            recent_revisit_count,
            float(self.node_to_index[player["position"]]),
            float(self.node_to_index[opponent["position"]]),
            float(len(legal_actions)),
        ]
        return vector

    def step(self, action: Action) -> Tuple[List[float], float, bool, Dict]:
        """Applies one decision and returns (obs, reward, done, info)."""
        if not action:
            raise ValueError("Action cannot be empty.")

        game = self.game
        actor_name = game.current_player["name"]
        opponent_name = game.opponent["name"]
        actor_before = self._player_snapshot(actor_name)
        opponent_before = self._player_snapshot(opponent_name)
        claimed_before = len(game.claimed_nodes)
        turn_before = game.turn_number
        legal_resolution = False
        route_start = None
        route_end = None
        route_toll = 0
        route_edge_type = None

        action_type = action[0]
        if action_type == "move":
            route_start = game.current_player["position"]
            route_end = action[1]
            route_toll = game.toll_cost(route_start, route_end)
            route_edge_type = game.get_edge(route_start, route_end)["type"]
            ok, message = game.begin_move(action[1])
        elif action_type == "owner_fee":
            if game.pending_owner_fee:
                route_start = game.pending_owner_fee["from"]
                route_end = game.pending_owner_fee["to"]
                route_toll = game.toll_cost(route_start, route_end)
                route_edge_type = game.get_edge(route_start, route_end)["type"]
            ok, message = game.resolve_owner_fee(action[1])
            if action[1] is False and message.startswith("You declined to pay"):
                legal_resolution = True
        elif action_type == "police":
            if game.pending_police:
                route_start = game.pending_police["from"]
                route_end = game.pending_police["to"]
                route_toll = game.toll_cost(route_start, route_end)
                route_edge_type = game.get_edge(route_start, route_end)["type"]
            ok, message = game.resolve_police(action[1])
        elif action_type == "invest":
            ok, message = game.invest(action[1], action[2])
            if ok:
                game.end_turn()
        elif action_type == "skip_investment":
            ok, message = game.skip_investment()
        else:
            raise ValueError(f"Unknown action type: {action_type}")

        self.decision_count += 1
        actor_after = self._player_snapshot(actor_name)
        opponent_after = self._player_snapshot(opponent_name)
        state_key = self._loop_state_key(actor_name)
        self.state_repeat_counts[state_key] += 1

        forced_terminal = False
        forced_terminal_reason = None
        if self.decision_count >= self.max_decisions:
            forced_terminal = True
            forced_terminal_reason = "max_decisions"
        elif self.state_repeat_counts[state_key] >= 12:
            forced_terminal = True
            forced_terminal_reason = "state_loop"
        elif not self.get_legal_actions() and not game.winner:
            forced_terminal = True
            forced_terminal_reason = "no_legal_actions"

        reward = self._calculate_reward(
            actor_name=actor_name,
            actor_before=actor_before,
            actor_after=actor_after,
            opponent_before=opponent_before,
            opponent_after=opponent_after,
            claimed_before=claimed_before,
            turn_before=turn_before,
            action=action,
            action_succeeded=ok,
            legal_resolution=legal_resolution,
            forced_terminal_reason=forced_terminal_reason,
        )

        done = bool(game.winner) or game.turn_number > self.max_turns or forced_terminal
        if game.turn_number > self.max_turns and not game.winner:
            reward -= 20.0
        if forced_terminal_reason == "max_decisions":
            reward -= 25.0
        elif forced_terminal_reason == "state_loop":
            reward -= 30.0
        elif forced_terminal_reason == "no_legal_actions":
            reward -= 15.0

        info = {
            "message": message,
            "winner": game.winner,
            "turn_number": game.turn_number,
            "phase": game.phase,
            "actor": actor_name,
            "action": action,
            "action_succeeded": ok,
            "forced_terminal_reason": forced_terminal_reason,
            "route_start": route_start,
            "route_end": route_end,
            "route_toll": route_toll,
            "route_edge_type": route_edge_type,
            "legal_resolution": legal_resolution,
        }
        return self.get_feature_vector(), reward, done, info

    def _calculate_reward(
        self,
        actor_name: str,
        actor_before: Dict,
        actor_after: Dict,
        opponent_before: Dict,
        opponent_after: Dict,
        claimed_before: int,
        turn_before: int,
        action: Action,
        action_succeeded: bool,
        legal_resolution: bool,
        forced_terminal_reason: str | None,
    ) -> float:
        game = self.game
        reward = -0.75

        if legal_resolution:
            reward -= 0.1
        elif not action_succeeded:
            return reward - 2.0

        actor_points_delta = actor_after["points"] - actor_before["points"]
        opponent_points_delta = opponent_after["points"] - opponent_before["points"]
        points_needed_before = max(0, TARGET_POINTS - actor_before["points"])
        points_needed_after = max(0, TARGET_POINTS - actor_after["points"])
        actor_distance_before = self.distance_to_johannesburg(actor_before["position"])
        actor_distance_after = self.distance_to_johannesburg(actor_after["position"])
        opponent_distance_before = self.distance_to_johannesburg(opponent_before["position"])
        opponent_distance_after = self.distance_to_johannesburg(opponent_after["position"])
        reward += actor_points_delta * 0.6
        reward -= max(0, -actor_points_delta) * 0.15
        reward += (points_needed_before - points_needed_after) * 0.35

        if opponent_points_delta < 0:
            reward += min(4.0, abs(opponent_points_delta) * 0.1)

        claimed_delta = len(game.claimed_nodes) - claimed_before
        if claimed_delta > 0:
            reward += 10.0

        if actor_distance_after < actor_distance_before:
            reward += 4.0
        elif actor_distance_after > actor_distance_before:
            reward -= 2.0

        advantage_before = (
            (actor_before["points"] - opponent_before["points"])
            + (opponent_distance_before - actor_distance_before) * 6.0
        )
        advantage_after = (
            (actor_after["points"] - opponent_after["points"])
            + (opponent_distance_after - actor_distance_after) * 6.0
        )
        reward += max(-8.0, min(8.0, (advantage_after - advantage_before) * 0.15))

        if actor_before["points"] < TARGET_POINTS <= actor_after["points"]:
            reward += 15.0

        if action[0] == "invest":
            destination_value = game.nodes[action[2]]["pts"]
            reward += 6.0 + destination_value * 0.3
        if action[0] == "skip_investment":
            reward -= 1.0
        if action[0] == "police" and action[1] == "refuse":
            reward -= 4.5
        if action[0] == "police" and action[1] == "bribe":
            reward -= 2.5
        if action[0] == "move" and actor_after["position"] == "Johannesburg":
            if actor_after["points"] >= TARGET_POINTS:
                reward += 30.0
            else:
                reward -= 12.0
        if action[0] == "move" and actor_after["travel_history_size"] == actor_before["travel_history_size"]:
            reward -= 2.5

        if game.winner == actor_name:
            reward += 130.0
        elif game.winner and game.winner != actor_name:
            reward -= 110.0

        if forced_terminal_reason == "state_loop":
            reward -= 10.0
        elif forced_terminal_reason == "no_legal_actions":
            reward -= 8.0

        if game.turn_number > turn_before:
            reward -= 0.4

        return reward

    def _player_snapshot(self, player_name: str) -> Dict:
        player = self._get_player(player_name)
        return {
            "name": player["name"],
            "position": player["position"],
            "points": player["points"],
            "skip_turn": player["skip_turn"],
            "turns_taken": player.get("turns_taken", 0),
            "travel_history_size": len(player.get("travel_history", set())),
        }

    def _get_player(self, player_name: str) -> Dict:
        for player in self.game.players:
            if player["name"] == player_name:
                return player
        raise ValueError(f"Unknown player: {player_name}")

    def _loop_state_key(self, player_name: str) -> Tuple:
        player = self._get_player(player_name)
        pending_owner = None
        if self.game.pending_owner_fee:
            pending_owner = (
                self.game.pending_owner_fee["from"],
                self.game.pending_owner_fee["to"],
                self.game.pending_owner_fee["owner"],
            )
        pending_police = None
        if self.game.pending_police:
            pending_police = (
                self.game.pending_police["from"],
                self.game.pending_police["to"],
            )
        return (
            player["name"],
            player["position"],
            self.game.phase,
            pending_owner,
            pending_police,
            player["skip_turn"],
        )


class RandomAgent:
    """Baseline agent that picks any legal action at random."""

    def choose_action(self, observation: Sequence[float], legal_actions: Sequence[Action], env=None) -> Action:
        del observation, env
        return random.choice(list(legal_actions))


class HeuristicAgent:
    """Simple handcrafted baseline used to test whether the learned agent beats obvious strategies."""

    def choose_action(self, observation: Sequence[float], legal_actions: Sequence[Action], env=None) -> Action:
        del observation
        if not legal_actions:
            raise ValueError("HeuristicAgent received no legal actions.")

        best_score = None
        best_actions = []
        current_player = env.game.current_player
        current_position = current_player["position"]
        current_distance = env.distance_to_johannesburg(current_position)
        opponent = env.game.opponent

        def score_destination(destination: str, extra_cost: float = 0.0, police_penalty: float = 0.0) -> float:
            destination_distance = env.distance_to_johannesburg(destination)
            destination_value = env.game.nodes[destination]["pts"]
            points_after_move = current_player["points"]
            if destination not in env.game.claimed_nodes:
                points_after_move += destination_value

            score = (current_distance - destination_distance) * 14.0
            if destination not in env.game.claimed_nodes:
                needed_points = max(0, TARGET_POINTS - current_player["points"])
                score += min(destination_value, needed_points) * 2.2
                score += destination_value * 0.9
            else:
                score -= 6.0

            if points_after_move >= TARGET_POINTS:
                score += max(0, 10 - destination_distance) * 7.0

            if destination == "Johannesburg":
                if points_after_move >= TARGET_POINTS:
                    score += 320.0
                else:
                    score -= 45.0

            score -= extra_cost * 1.4
            score -= police_penalty
            return score

        def score_investment(source: str, destination: str) -> float:
            destination_value = env.game.nodes[destination]["pts"]
            source_distance = env.distance_to_johannesburg(source)
            opponent_distance_to_source = env.distance_to_johannesburg(opponent["position"])
            pressure_bonus = 10.0 if opponent_distance_to_source <= source_distance + 1 else 0.0
            return destination_value * 1.8 + max(0, 8 - source_distance) * 3.0 + pressure_bonus

        for action in legal_actions:
            score = 0.0
            if action[0] == "move":
                destination = action[1]
                toll_cost = env.game.toll_cost(current_position, destination)
                edge_type = env.game.get_edge(current_position, destination)["type"]
                police_penalty = 12.0 if edge_type == "police" else 0.0
                score = score_destination(destination, extra_cost=toll_cost, police_penalty=police_penalty)
            elif action[0] == "invest":
                source, destination = action[1], action[2]
                score = score_investment(source, destination)
            elif action == ("owner_fee", True):
                pending = env.game.pending_owner_fee
                score = score_destination(
                    pending["to"],
                    extra_cost=15 + env.game.toll_cost(pending["from"], pending["to"]),
                    police_penalty=12.0 if env.game.get_edge(pending["from"], pending["to"])["type"] == "police" else 0.0,
                )
            elif action == ("owner_fee", False):
                pending = env.game.pending_owner_fee
                route_score = score_destination(
                    pending["to"],
                    extra_cost=15 + env.game.toll_cost(pending["from"], pending["to"]),
                    police_penalty=12.0 if env.game.get_edge(pending["from"], pending["to"])["type"] == "police" else 0.0,
                )
                score = -2.0 if route_score > 12.0 else 8.0
            elif action == ("police", "bribe"):
                pending = env.game.pending_police
                score = score_destination(pending["to"], extra_cost=15.0, police_penalty=0.0)
            elif action == ("police", "refuse"):
                pending = env.game.pending_police
                route_score = score_destination(pending["to"], extra_cost=0.0, police_penalty=18.0)
                score = route_score - 12.0
            elif action == ("skip_investment",):
                score = -4.0

            if best_score is None or score > best_score:
                best_score = score
                best_actions = [action]
            elif score == best_score:
                best_actions.append(action)

        return sorted(best_actions, key=str)[0]


class QAgent:
    """Very small tabular Q-learning agent for a first training experiment."""

    def __init__(
        self,
        alpha: float = 0.15,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.05,
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.q_table = defaultdict(float)

    def state_key(self, observation: Sequence[float]) -> Tuple:
        """Discretises the observation so Q-learning has a manageable state key."""

        def bucket_points(value: float) -> int:
            shifted = value + 200 if value < 0 else value
            return int(min(20, max(0, shifted // 20)))

        def bucket_distance(value: float) -> int:
            return int(min(10, value))

        def bucket_count(value: float) -> int:
            return int(min(8, value))

        return (
            bucket_points(observation[0]),
            bucket_points(observation[1]),
            bucket_points(observation[2]),
            bucket_distance(observation[3]),
            bucket_distance(observation[4]),
            bucket_distance(observation[5]),
            bucket_count(observation[6]),
            bucket_count(observation[7]),
            bucket_count(observation[8]),
            bucket_count(observation[9]),
            bucket_count(observation[10]),
            bucket_count(observation[11]),
            int(observation[12]),
            int(observation[13]),
            int(observation[14]),
            int(observation[15]),
            int(observation[16]),
            bucket_points(observation[17]),
            int(observation[18]),
            bucket_count(observation[19]),
        )

    def choose_action(self, observation: Sequence[float], legal_actions: Sequence[Action]) -> Action:
        if not legal_actions:
            raise ValueError("choose_action received no legal actions.")

        state = self.state_key(observation)
        if random.random() < self.epsilon:
            return random.choice(list(legal_actions))

        scored_actions = [(self.q_table[(state, action)], action) for action in legal_actions]
        best_score = max(score for score, _ in scored_actions)
        best_actions = [action for score, action in scored_actions if score == best_score]
        return random.choice(best_actions)

    def learn(
        self,
        observation: Sequence[float],
        action: Action,
        reward: float,
        next_observation: Sequence[float],
        next_legal_actions: Sequence[Action],
        done: bool,
    ) -> None:
        state = self.state_key(observation)
        next_state = self.state_key(next_observation)
        current_q = self.q_table[(state, action)]

        if done or not next_legal_actions:
            target = reward
        else:
            next_best = max(self.q_table[(next_state, next_action)] for next_action in next_legal_actions)
            target = reward + self.gamma * next_best

        self.q_table[(state, action)] = current_q + self.alpha * (target - current_q)

    def decay_epsilon(self) -> None:
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


def choose_controller_action(controller, observation, legal_actions, env):
    try:
        return controller.choose_action(observation, legal_actions, env)
    except TypeError:
        return controller.choose_action(observation, legal_actions)


def play_one_game(
    env: SiyayaTrainingEnv,
    agent_one,
    agent_two,
    verbose: bool = False,
    starting_player_index: int = 0,
) -> Dict:
    observation = env.reset()
    env.game.current_player_index = starting_player_index
    env.game.log(f"Evaluation start: {env.game.current_player['name']} moves first.")
    observation = env.get_feature_vector()
    done = False
    total_rewards = {
        "Player 1": 0.0,
        "Player 2": 0.0,
    }
    event_counts = {
        "investments": 0,
        "toll_routes_taken": 0,
        "police_bribes": 0,
        "police_refusals": 0,
        "owner_fee_paid": 0,
        "owner_fee_declined": 0,
    }
    reached_johannesburg = {
        "Player 1": False,
        "Player 2": False,
    }
    forced_terminal_reason = None

    while not done:
        current_name = env.game.current_player["name"]
        agent = agent_one if current_name == "Player 1" else agent_two
        legal_actions = env.get_legal_actions()
        if not legal_actions:
            break

        action = choose_controller_action(agent, observation, legal_actions, env)
        observation, reward, done, info = env.step(action)
        total_rewards[current_name] += reward
        forced_terminal_reason = info.get("forced_terminal_reason") or forced_terminal_reason

        if info["action_succeeded"] and info.get("route_toll", 0) > 0:
            event_counts["toll_routes_taken"] += 1
        if action[0] == "invest" and info["action_succeeded"]:
            event_counts["investments"] += 1
        if action == ("police", "bribe") and info["action_succeeded"]:
            event_counts["police_bribes"] += 1
        if action == ("police", "refuse") and info["action_succeeded"]:
            event_counts["police_refusals"] += 1
        if action == ("owner_fee", True) and info["action_succeeded"]:
            event_counts["owner_fee_paid"] += 1
        if action == ("owner_fee", False) and info.get("legal_resolution"):
            event_counts["owner_fee_declined"] += 1

        for player in env.game.players:
            if player["position"] == "Johannesburg":
                reached_johannesburg[player["name"]] = True

        if verbose:
            print(
                f"{info['actor']} | turn {info['turn_number']} | phase {info['phase']} | "
                f"action={info['action']} | reward={reward:.2f} | {info['message']}"
            )

    return {
        "winner": env.game.winner,
        "turns": env.game.turn_number,
        "decision_count": env.decision_count,
        "scores": {player["name"]: player["points"] for player in env.game.players},
        "rewards": total_rewards,
        "event_counts": event_counts,
        "reached_johannesburg": reached_johannesburg,
        "forced_terminal_reason": forced_terminal_reason,
        "starting_player": env.game.players[starting_player_index]["name"],
    }


def run_random_baseline(
    game_count: int = 10,
    verbose_first_game: bool = True,
    max_turns: int = 80,
) -> None:
    env = SiyayaTrainingEnv(max_turns=max_turns)
    red_agent = RandomAgent()
    blue_agent = RandomAgent()

    wins = {
        "Player 1": 0,
        "Player 2": 0,
        "draw": 0,
    }
    total_turns = 0

    for game_index in range(1, game_count + 1):
        result = play_one_game(
            env,
            red_agent,
            blue_agent,
            verbose=verbose_first_game and game_index == 1,
            starting_player_index=(game_index - 1) % 2,
        )
        winner = result["winner"] if result["winner"] else "draw"
        wins[winner] += 1
        total_turns += result["turns"]
        print(
            f"Game {game_index:02d} | winner={winner} | turns={result['turns']} | "
            f"scores={result['scores']} | rewards={result['rewards']}"
        )

    print("\nSummary")
    print(f"Player 1 wins: {wins['Player 1']}")
    print(f"Player 2 wins: {wins['Player 2']}")
    print(f"Draws/unfinished: {wins['draw']}")
    print(f"Average turns: {total_turns / game_count:.2f}")


def train_q_agent(
    episode_count: int = 100,
    report_every: int = 10,
    evaluation_games: int = 1,
    max_turns: int = 80,
    evaluation_max_turns: int = 80,
) -> QAgent:
    """Trains a first Q-learning agent by letting it control both sides."""

    ensure_metrics_dir()
    env = SiyayaTrainingEnv(max_turns=max_turns)
    agent = QAgent()

    for episode in range(1, episode_count + 1):
        observation = env.reset()
        done = False
        episode_reward = 0.0

        while not done:
            legal_actions = env.get_legal_actions()
            if not legal_actions:
                break

            action = agent.choose_action(observation, legal_actions)
            next_observation, reward, done, _info = env.step(action)
            next_legal_actions = env.get_legal_actions()
            agent.learn(observation, action, reward, next_observation, next_legal_actions, done)

            observation = next_observation
            episode_reward += reward

        agent.decay_epsilon()
        training_row = {
            "episode": episode,
            "epsilon": round(agent.epsilon, 6),
            "episode_reward": round(episode_reward, 4),
            "q_table_size": len(agent.q_table),
            "max_turns": max_turns,
            "max_decisions": env.max_decisions,
        }
        append_csv_row(
            TRAINING_CSV,
            ["episode", "epsilon", "episode_reward", "q_table_size", "max_turns", "max_decisions"],
            training_row,
        )
        append_jsonl_row(TRAINING_JSONL, training_row)

        if episode % report_every == 0:
            print(
                f"Episode {episode:04d} finished | epsilon={agent.epsilon:.3f} | "
                f"last_episode_reward={episode_reward:.2f} | running evaluation..."
            )
            eval_summary = evaluate_agent(agent, evaluation_games, max_turns=evaluation_max_turns)
            random_eval = eval_summary["vs_random"]
            heuristic_eval = eval_summary["vs_heuristic"]
            self_eval = eval_summary["self_play"]
            eval_row = {
                "episode": episode,
                "epsilon": round(agent.epsilon, 6),
                "random_agent_wins": random_eval["agent_wins"],
                "random_opponent_wins": random_eval["opponent_wins"],
                "random_draws": random_eval["draw"],
                "random_avg_turns": random_eval["avg_turns"],
                "random_avg_agent_balance": random_eval["avg_agent_balance"],
                "heur_agent_wins": heuristic_eval["agent_wins"],
                "heur_opponent_wins": heuristic_eval["opponent_wins"],
                "heur_draws": heuristic_eval["draw"],
                "heur_avg_turns": heuristic_eval["avg_turns"],
                "heur_avg_agent_balance": heuristic_eval["avg_agent_balance"],
                "self_agent_wins": self_eval["agent_wins"],
                "self_opponent_wins": self_eval["opponent_wins"],
                "self_draws": self_eval["draw"],
                "self_avg_turns": self_eval["avg_turns"],
            }
            append_csv_row(
                EVAL_CSV,
                [
                    "episode", "epsilon",
                    "random_agent_wins", "random_opponent_wins", "random_draws", "random_avg_turns", "random_avg_agent_balance",
                    "heur_agent_wins", "heur_opponent_wins", "heur_draws", "heur_avg_turns", "heur_avg_agent_balance",
                    "self_agent_wins", "self_opponent_wins", "self_draws", "self_avg_turns",
                ],
                eval_row,
            )
            append_jsonl_row(EVAL_JSONL, eval_row)
            print(
                f"Episode {episode:04d} evaluation | "
                f"random(agent/opponent/draw)={random_eval['agent_wins']}/{random_eval['opponent_wins']}/{random_eval['draw']} | "
                f"heuristic(agent/opponent/draw)={heuristic_eval['agent_wins']}/{heuristic_eval['opponent_wins']}/{heuristic_eval['draw']} | "
                f"self(agent/opponent/draw)={self_eval['agent_wins']}/{self_eval['opponent_wins']}/{self_eval['draw']}"
            )

    return agent


def _aggregate_matchup(agent, opponent, game_count: int, max_turns: int, label: str) -> Dict:
    env = SiyayaTrainingEnv(max_turns=max_turns)
    wins = {
        "agent_wins": 0,
        "opponent_wins": 0,
        "draw": 0,
        "agent_wins_as_first": 0,
        "agent_wins_as_second": 0,
    }
    total_turns = 0
    total_decisions = 0
    agent_balance_total = 0.0
    opponent_balance_total = 0.0
    agent_reward_total = 0.0
    opponent_reward_total = 0.0
    total_events = {
        "investments": 0,
        "toll_routes_taken": 0,
        "police_bribes": 0,
        "police_refusals": 0,
        "owner_fee_paid": 0,
        "owner_fee_declined": 0,
    }
    johannesburg_reaches = {
        "agent": 0,
        "opponent": 0,
    }
    forced_terminal_counts = defaultdict(int)

    for game_index in range(game_count):
        starting_player_index = game_index % 2
        agent_as_player_one = game_index % 2 == 0
        player_one_controller = agent if agent_as_player_one else opponent
        player_two_controller = opponent if agent_as_player_one else agent
        result = play_one_game(
            env,
            player_one_controller,
            player_two_controller,
            verbose=False,
            starting_player_index=starting_player_index,
        )

        winner = result["winner"]
        agent_player_name = "Player 1" if agent_as_player_one else "Player 2"
        opponent_player_name = "Player 2" if agent_as_player_one else "Player 1"
        agent_started_first = starting_player_index == (0 if agent_as_player_one else 1)

        if winner is None:
            wins["draw"] += 1
        elif winner == agent_player_name:
            wins["agent_wins"] += 1
            if agent_started_first:
                wins["agent_wins_as_first"] += 1
            else:
                wins["agent_wins_as_second"] += 1
        else:
            wins["opponent_wins"] += 1

        total_turns += result["turns"]
        total_decisions += result["decision_count"]
        agent_balance_total += result["scores"][agent_player_name]
        opponent_balance_total += result["scores"][opponent_player_name]
        agent_reward_total += result["rewards"][agent_player_name]
        opponent_reward_total += result["rewards"][opponent_player_name]
        for key, value in result["event_counts"].items():
            total_events[key] += value
        johannesburg_reaches["agent"] += int(result["reached_johannesburg"][agent_player_name])
        johannesburg_reaches["opponent"] += int(result["reached_johannesburg"][opponent_player_name])
        if result["forced_terminal_reason"]:
            forced_terminal_counts[result["forced_terminal_reason"]] += 1

    return {
        "matchup": label,
        "game_count": game_count,
        **wins,
        "avg_turns": round(total_turns / game_count, 2),
        "avg_decisions": round(total_decisions / game_count, 2),
        "avg_agent_balance": round(agent_balance_total / game_count, 2),
        "avg_opponent_balance": round(opponent_balance_total / game_count, 2),
        "avg_agent_reward": round(agent_reward_total / game_count, 2),
        "avg_opponent_reward": round(opponent_reward_total / game_count, 2),
        "avg_investments": round(total_events["investments"] / game_count, 2),
        "avg_toll_routes": round(total_events["toll_routes_taken"] / game_count, 2),
        "avg_police_bribes": round(total_events["police_bribes"] / game_count, 2),
        "avg_police_refusals": round(total_events["police_refusals"] / game_count, 2),
        "avg_owner_fee_paid": round(total_events["owner_fee_paid"] / game_count, 2),
        "avg_owner_fee_declined": round(total_events["owner_fee_declined"] / game_count, 2),
        "agent_johannesburg_reaches": johannesburg_reaches["agent"],
        "opponent_johannesburg_reaches": johannesburg_reaches["opponent"],
        "forced_terminal_counts": dict(forced_terminal_counts),
    }


def evaluate_agent(agent: QAgent, game_count: int = 10, max_turns: int = 80) -> Dict:
    """Evaluates the learned agent fairly across start positions and opponent types."""

    saved_epsilon = agent.epsilon
    agent.epsilon = 0.0

    random_opponent = RandomAgent()
    heuristic_opponent = HeuristicAgent()

    random_summary = _aggregate_matchup(agent, random_opponent, game_count, max_turns, "vs_random")
    heuristic_summary = _aggregate_matchup(agent, heuristic_opponent, game_count, max_turns, "vs_heuristic")
    self_play_summary = _aggregate_matchup(agent, agent, game_count, max_turns, "self_play")

    agent.epsilon = saved_epsilon
    return {
        "vs_random": random_summary,
        "vs_heuristic": heuristic_summary,
        "self_play": self_play_summary,
    }


def print_evaluation_summary(summary: Dict) -> None:
    for label in ("vs_random", "vs_heuristic", "self_play"):
        matchup = summary[label]
        print(
            f"{label}: "
            f"agent_wins={matchup['agent_wins']} | "
            f"opponent_wins={matchup['opponent_wins']} | "
            f"draws={matchup['draw']} | "
            f"agent_as_first={matchup['agent_wins_as_first']} | "
            f"agent_as_second={matchup['agent_wins_as_second']} | "
            f"avg_turns={matchup['avg_turns']} | "
            f"avg_agent_balance={matchup['avg_agent_balance']}"
        )


def print_first_steps_tutorial() -> None:
    print("First training steps for Siyaya")
    print("1. Run this file and make sure random-vs-random games finish.")
    print("2. Read get_legal_actions() and understand every action type.")
    print("3. Read get_feature_vector() and decide what extra information you need.")
    print("4. Read _calculate_reward() and adjust the reward shaping carefully.")
    print("5. Then read QAgent, train_q_agent(), and evaluate_agent().\n")


def main() -> None:
    print_first_steps_tutorial()
    print("=== Random baseline ===")
    run_random_baseline(game_count=2, verbose_first_game=False, max_turns=80)

    print("\n=== Q-learning demo ===")
    print("This is a short demo run. Increase episode_count later once you are comfortable.")
    agent = train_q_agent(
        episode_count=1000,
        report_every=100,
        evaluation_games=3,
        max_turns=60,
        evaluation_max_turns=60,
    )

    print("\n=== Final evaluation ===")
    summary = evaluate_agent(agent, game_count=10, max_turns=80)
    print_evaluation_summary(summary)


if __name__ == "__main__":
    main()

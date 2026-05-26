"""Starter training scaffold for Siyaya.

This file is intentionally beginner-friendly. It gives you:

1. A small training environment around GameState
2. A legal-action function
3. A first feature vector
4. A reward calculation
5. A random baseline agent
6. A simulation loop you can run from the terminal

Run:
    python3 train_agent.py

This does NOT train a smart agent yet. It is the step before training.
Its job is to prove that the game can be played automatically without Tkinter.
"""

from __future__ import annotations

import os
import random
from typing import Dict, List, Sequence, Tuple

from age_of_wheels import GameState, MAP_FILE, MapStorage, TARGET_POINTS


Action = Tuple


class SiyayaTrainingEnv:
    """Wraps the game logic in a training-friendly interface."""

    def __init__(self, map_path: str | None = None, max_turns: int = 250):
        if map_path is None:
            map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MAP_FILE)
        self.storage = MapStorage(map_path)
        self.map_data = self.storage.load()
        self.max_turns = max_turns
        self.node_names = [node["name"] for node in self.map_data["nodes"]]
        self.node_to_index = {name: index for index, name in enumerate(self.node_names)}
        self.game = None
        self.decision_count = 0

    def reset(self) -> List[float]:
        self.game = GameState(self.map_data)
        self.decision_count = 0
        return self.get_feature_vector()

    def get_legal_actions(self) -> List[Action]:
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
        distances = self.game.bfs_distances(start_name)
        return distances.get("Johannesburg", len(self.node_names))

    def count_owned_routes(self, player_name: str) -> int:
        return sum(1 for edge in self.game.edges.values() if edge["owner"] == player_name)

    def count_unclaimed_adjacent(self, player_name: str) -> int:
        position = self._get_player(player_name)["position"]
        return sum(1 for neighbor in self.game.adjacency[position] if neighbor not in self.game.claimed_nodes)

    def get_feature_vector(self) -> List[float]:
        """Small first feature vector for early experiments."""
        game = self.game
        player = game.current_player
        opponent = game.opponent
        legal_actions = self.get_legal_actions()

        phase_move = 1.0 if game.phase == "move" else 0.0
        phase_invest = 1.0 if game.phase == "invest" else 0.0
        pending_police = 1.0 if game.pending_police else 0.0
        pending_owner_fee = 1.0 if game.pending_owner_fee else 0.0

        vector = [
            float(player["points"]),
            float(opponent["points"]),
            float(self.distance_to_johannesburg(player["position"])),
            float(self.distance_to_johannesburg(opponent["position"])),
            float(len(game.accessible_moves())),
            float(len(game.all_investments()) if game.phase == "invest" else 0),
            float(self.count_owned_routes(player["name"])),
            float(self.count_owned_routes(opponent["name"])),
            float(self.count_unclaimed_adjacent(player["name"])),
            phase_move,
            phase_invest,
            pending_police,
            pending_owner_fee,
            float(player["skip_turn"]),
            float(opponent["skip_turn"]),
            float(max(0, TARGET_POINTS - player["points"])),
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

        action_type = action[0]
        if action_type == "move":
            ok, message = game.begin_move(action[1])
        elif action_type == "owner_fee":
            ok, message = game.resolve_owner_fee(action[1])
        elif action_type == "police":
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
        )

        done = bool(game.winner) or game.turn_number > self.max_turns
        if game.turn_number > self.max_turns and not game.winner:
            reward -= 20.0

        info = {
            "message": message,
            "winner": game.winner,
            "turn_number": game.turn_number,
            "phase": game.phase,
            "actor": actor_name,
            "action": action,
            "action_succeeded": ok,
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
    ) -> float:
        game = self.game
        reward = -0.5

        if not action_succeeded:
            return reward - 2.0

        actor_points_delta = actor_after["points"] - actor_before["points"]
        opponent_points_delta = opponent_after["points"] - opponent_before["points"]
        reward += actor_points_delta * 0.6
        reward -= max(0, -actor_points_delta) * 0.15

        if opponent_points_delta < 0:
            reward += min(4.0, abs(opponent_points_delta) * 0.1)

        claimed_delta = len(game.claimed_nodes) - claimed_before
        if claimed_delta > 0:
            reward += 8.0

        distance_before = self.distance_to_johannesburg(actor_before["position"])
        distance_after = self.distance_to_johannesburg(actor_after["position"])
        if distance_after < distance_before:
            reward += 3.0
        elif distance_after > distance_before:
            reward -= 1.0

        if action[0] == "invest":
            reward += 4.0
        if action[0] == "skip_investment":
            reward -= 0.5
        if action[0] == "police" and action[1] == "refuse":
            reward -= 3.0
        if action[0] == "police" and action[1] == "bribe":
            reward -= 1.5

        if game.winner == actor_name:
            reward += 100.0
        elif game.winner and game.winner != actor_name:
            reward -= 100.0

        if game.turn_number > turn_before:
            reward -= 0.2

        return reward

    def _player_snapshot(self, player_name: str) -> Dict:
        player = self._get_player(player_name)
        return {
            "name": player["name"],
            "position": player["position"],
            "points": player["points"],
            "skip_turn": player["skip_turn"],
        }

    def _get_player(self, player_name: str) -> Dict:
        for player in self.game.players:
            if player["name"] == player_name:
                return player
        raise ValueError(f"Unknown player: {player_name}")


class RandomAgent:
    """Baseline agent that picks any legal action at random."""

    def choose_action(self, observation: Sequence[float], legal_actions: Sequence[Action]) -> Action:
        del observation
        return random.choice(list(legal_actions))


def play_one_game(env: SiyayaTrainingEnv, agent_one, agent_two, verbose: bool = False) -> Dict:
    observation = env.reset()
    done = False
    total_rewards = {
        "Player 1": 0.0,
        "Player 2": 0.0,
    }

    while not done:
        current_name = env.game.current_player["name"]
        agent = agent_one if current_name == "Player 1" else agent_two
        legal_actions = env.get_legal_actions()
        if not legal_actions:
            break

        action = agent.choose_action(observation, legal_actions)
        observation, reward, done, info = env.step(action)
        total_rewards[current_name] += reward

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
    }


def run_random_baseline(game_count: int = 10, verbose_first_game: bool = True) -> None:
    env = SiyayaTrainingEnv()
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


def print_first_steps_tutorial() -> None:
    print("First training steps for Siyaya")
    print("1. Run this file and make sure random-vs-random games finish.")
    print("2. Read get_legal_actions() and understand every action type.")
    print("3. Read get_feature_vector() and decide what extra information you need.")
    print("4. Read _calculate_reward() and adjust the reward shaping carefully.")
    print("5. Replace RandomAgent with a learning agent only after steps 1-4 work.\n")


def main() -> None:
    print_first_steps_tutorial()
    run_random_baseline(game_count=5, verbose_first_game=True)


if __name__ == "__main__":
    main()

import json
import math
import os
import random
import tkinter as tk
from collections import deque
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

MAP_FILE = "map_data.json"
TARGET_POINTS = 200
START_POINTS = 120
CANVAS_WIDTH = 1400
CANVAS_HEIGHT = 1000

DEFAULT_MAP = {
    "nodes": [
        {"name": "Cape Town", "province": "Western Cape", "pts": 29, "type": "city", "x": 110, "y": 570},
        {"name": "Stellenbosch", "province": "Western Cape", "pts": 13, "type": "town", "x": 180, "y": 545},
        {"name": "Paarl", "province": "Western Cape", "pts": 10, "type": "town", "x": 210, "y": 515},
        {"name": "Worcester", "province": "Western Cape", "pts": 5, "type": "town", "x": 285, "y": 490},
        {"name": "George", "province": "Western Cape", "pts": 7, "type": "town", "x": 260, "y": 615},
        {"name": "Kimberley", "province": "Northern Cape", "pts": 20, "type": "city", "x": 390, "y": 360},
        {"name": "Upington", "province": "Northern Cape", "pts": 8, "type": "town", "x": 225, "y": 320},
        {"name": "Springbok", "province": "Northern Cape", "pts": 5, "type": "town", "x": 120, "y": 250},
        {"name": "De Aar", "province": "Northern Cape", "pts": 3, "type": "town", "x": 355, "y": 445},
        {"name": "Postmasburg", "province": "Northern Cape", "pts": 7, "type": "town", "x": 330, "y": 300},
        {"name": "Bloemfontein", "province": "Free State", "pts": 25, "type": "city", "x": 520, "y": 405},
        {"name": "Welkom", "province": "Free State", "pts": 10, "type": "town", "x": 515, "y": 335},
        {"name": "Sasolburg", "province": "Free State", "pts": 7, "type": "town", "x": 580, "y": 290},
        {"name": "Kroonstad", "province": "Free State", "pts": 5, "type": "town", "x": 565, "y": 345},
        {"name": "Phuthaditjhaba", "province": "Free State", "pts": 9, "type": "town", "x": 630, "y": 375},
        {"name": "Rustenburg", "province": "North West", "pts": 23, "type": "city", "x": 560, "y": 205},
        {"name": "Klerksdorp", "province": "North West", "pts": 14, "type": "town", "x": 475, "y": 250},
        {"name": "Mahikeng", "province": "North West", "pts": 9, "type": "town", "x": 430, "y": 180},
        {"name": "Brits", "province": "North West", "pts": 6, "type": "town", "x": 610, "y": 180},
        {"name": "Potchefstroom", "province": "North West", "pts": 11, "type": "town", "x": 520, "y": 255},
        {"name": "Johannesburg", "province": "Gauteng", "pts": 27, "type": "city", "x": 705, "y": 240},
        {"name": "Soweto", "province": "Gauteng", "pts": 11, "type": "town", "x": 675, "y": 275},
        {"name": "Benoni", "province": "Gauteng", "pts": 8, "type": "town", "x": 760, "y": 235},
        {"name": "Germiston", "province": "Gauteng", "pts": 14, "type": "town", "x": 735, "y": 265},
        {"name": "Kempton Park", "province": "Gauteng", "pts": 9, "type": "town", "x": 760, "y": 205},
        {"name": "Polokwane", "province": "Limpopo", "pts": 22, "type": "city", "x": 720, "y": 90},
        {"name": "Tzaneen", "province": "Limpopo", "pts": 10, "type": "town", "x": 790, "y": 85},
        {"name": "Bela-Bela", "province": "Limpopo", "pts": 6, "type": "town", "x": 675, "y": 145},
        {"name": "Mokopane", "province": "Limpopo", "pts": 9, "type": "town", "x": 745, "y": 135},
        {"name": "Louis Trichardt", "province": "Limpopo", "pts": 5, "type": "town", "x": 760, "y": 40},
        {"name": "Mbombela", "province": "Mpumalanga", "pts": 21, "type": "city", "x": 860, "y": 220},
        {"name": "Witbank/eMalahleni", "province": "Mpumalanga", "pts": 12, "type": "town", "x": 800, "y": 200},
        {"name": "Middelburg", "province": "Mpumalanga", "pts": 8, "type": "town", "x": 835, "y": 180},
        {"name": "Secunda", "province": "Mpumalanga", "pts": 11, "type": "town", "x": 790, "y": 265},
        {"name": "White River", "province": "Mpumalanga", "pts": 4, "type": "town", "x": 900, "y": 200},
        {"name": "Durban", "province": "KwaZulu-Natal", "pts": 26, "type": "city", "x": 820, "y": 405},
        {"name": "Pietermaritzburg", "province": "KwaZulu-Natal", "pts": 12, "type": "town", "x": 760, "y": 360},
        {"name": "Richards Bay", "province": "KwaZulu-Natal", "pts": 9, "type": "town", "x": 860, "y": 330},
        {"name": "Ladysmith", "province": "KwaZulu-Natal", "pts": 6, "type": "town", "x": 720, "y": 320},
        {"name": "Newcastle", "province": "KwaZulu-Natal", "pts": 11, "type": "town", "x": 765, "y": 270},
        {"name": "Gqeberha (Port Elizabeth)", "province": "Eastern Cape", "pts": 24, "type": "city", "x": 665, "y": 555},
        {"name": "East London", "province": "Eastern Cape", "pts": 15, "type": "town", "x": 720, "y": 505},
        {"name": "Mthatha", "province": "Eastern Cape", "pts": 8, "type": "town", "x": 755, "y": 455},
        {"name": "Grahamstown", "province": "Eastern Cape", "pts": 4, "type": "town", "x": 640, "y": 585},
        {"name": "Queenstown", "province": "Eastern Cape", "pts": 7, "type": "town", "x": 650, "y": 470}
    ],
    "edges": [
        {"from": "Cape Town", "to": "Stellenbosch", "type": "normal", "owner": None},
        {"from": "Cape Town", "to": "Paarl", "type": "normal", "owner": None},
        {"from": "Stellenbosch", "to": "Paarl", "type": "normal", "owner": None},
        {"from": "Paarl", "to": "Worcester", "type": "normal", "owner": None},
        {"from": "Worcester", "to": "George", "type": "normal", "owner": None},
        {"from": "Worcester", "to": "De Aar", "type": "normal", "owner": None},
        {"from": "Worcester", "to": "Kimberley", "type": "toll_border", "owner": None},
        {"from": "George", "to": "Gqeberha (Port Elizabeth)", "type": "police", "owner": None},
        {"from": "Kimberley", "to": "Upington", "type": "normal", "owner": None},
        {"from": "Upington", "to": "Springbok", "type": "normal", "owner": None},
        {"from": "Kimberley", "to": "Postmasburg", "type": "normal", "owner": None},
        {"from": "Kimberley", "to": "De Aar", "type": "normal", "owner": None},
        {"from": "Kimberley", "to": "Bloemfontein", "type": "toll_border", "owner": None},
        {"from": "Postmasburg", "to": "Mahikeng", "type": "normal", "owner": None},
        {"from": "De Aar", "to": "Bloemfontein", "type": "normal", "owner": None},
        {"from": "Bloemfontein", "to": "Welkom", "type": "normal", "owner": None},
        {"from": "Welkom", "to": "Kroonstad", "type": "normal", "owner": None},
        {"from": "Kroonstad", "to": "Sasolburg", "type": "normal", "owner": None},
        {"from": "Bloemfontein", "to": "Phuthaditjhaba", "type": "police", "owner": None},
        {"from": "Phuthaditjhaba", "to": "Ladysmith", "type": "normal", "owner": None},
        {"from": "Bloemfontein", "to": "Queenstown", "type": "toll_border", "owner": None},
        {"from": "Queenstown", "to": "East London", "type": "normal", "owner": None},
        {"from": "Queenstown", "to": "Mthatha", "type": "normal", "owner": None},
        {"from": "Gqeberha (Port Elizabeth)", "to": "Grahamstown", "type": "normal", "owner": None},
        {"from": "Grahamstown", "to": "East London", "type": "normal", "owner": None},
        {"from": "East London", "to": "Mthatha", "type": "normal", "owner": None},
        {"from": "Gqeberha (Port Elizabeth)", "to": "Queenstown", "type": "normal", "owner": None},
        {"from": "Mthatha", "to": "Durban", "type": "toll_border", "owner": None},
        {"from": "Durban", "to": "Pietermaritzburg", "type": "normal", "owner": None},
        {"from": "Pietermaritzburg", "to": "Ladysmith", "type": "normal", "owner": None},
        {"from": "Ladysmith", "to": "Newcastle", "type": "police", "owner": None},
        {"from": "Durban", "to": "Richards Bay", "type": "normal", "owner": None},
        {"from": "Richards Bay", "to": "Newcastle", "type": "normal", "owner": None},
        {"from": "Newcastle", "to": "Secunda", "type": "toll_border", "owner": None},
        {"from": "Secunda", "to": "Witbank/eMalahleni", "type": "normal", "owner": None},
        {"from": "Witbank/eMalahleni", "to": "Middelburg", "type": "normal", "owner": None},
        {"from": "Middelburg", "to": "Mbombela", "type": "normal", "owner": None},
        {"from": "Mbombela", "to": "White River", "type": "police", "owner": None},
        {"from": "Witbank/eMalahleni", "to": "Johannesburg", "type": "normal", "owner": None},
        {"from": "Secunda", "to": "Johannesburg", "type": "toll_border", "owner": None},
        {"from": "Sasolburg", "to": "Johannesburg", "type": "normal", "owner": None},
        {"from": "Johannesburg", "to": "Germiston", "type": "normal", "owner": None},
        {"from": "Johannesburg", "to": "Soweto", "type": "normal", "owner": None},
        {"from": "Johannesburg", "to": "Benoni", "type": "normal", "owner": None},
        {"from": "Johannesburg", "to": "Kempton Park", "type": "normal", "owner": None},
        {"from": "Germiston", "to": "Benoni", "type": "normal", "owner": None},
        {"from": "Germiston", "to": "Kempton Park", "type": "normal", "owner": None},
        {"from": "Benoni", "to": "Kempton Park", "type": "normal", "owner": None},
        {"from": "Johannesburg", "to": "Brits", "type": "toll_border", "owner": None},
        {"from": "Brits", "to": "Rustenburg", "type": "normal", "owner": None},
        {"from": "Rustenburg", "to": "Mahikeng", "type": "normal", "owner": None},
        {"from": "Rustenburg", "to": "Klerksdorp", "type": "normal", "owner": None},
        {"from": "Klerksdorp", "to": "Potchefstroom", "type": "normal", "owner": None},
        {"from": "Potchefstroom", "to": "Johannesburg", "type": "normal", "owner": None},
        {"from": "Klerksdorp", "to": "Welkom", "type": "normal", "owner": None},
        {"from": "Brits", "to": "Bela-Bela", "type": "police", "owner": None},
        {"from": "Bela-Bela", "to": "Polokwane", "type": "normal", "owner": None},
        {"from": "Polokwane", "to": "Mokopane", "type": "normal", "owner": None},
        {"from": "Polokwane", "to": "Tzaneen", "type": "normal", "owner": None},
        {"from": "Polokwane", "to": "Louis Trichardt", "type": "normal", "owner": None},
        {"from": "Mokopane", "to": "Bela-Bela", "type": "normal", "owner": None},
        {"from": "Mokopane", "to": "Witbank/eMalahleni", "type": "normal", "owner": None},
        {"from": "Tzaneen", "to": "Mbombela", "type": "normal", "owner": None},
        {"from": "Polokwane", "to": "Mbombela", "type": "toll_border", "owner": None}
    ],
    "province_borders": {
        "Western Cape": ["Worcester", "Kimberley"],
        "Northern Cape": ["Kimberley", "Bloemfontein"],
        "Free State": ["Bloemfontein", "Queenstown"],
        "Eastern Cape": ["Mthatha", "Durban"],
        "KwaZulu-Natal": ["Newcastle", "Secunda"],
        "Gauteng": ["Johannesburg", "Brits"],
        "North West": ["Johannesburg", "Brits"],
        "Limpopo": ["Polokwane", "Mbombela"],
        "Mpumalanga": ["Secunda", "Johannesburg"]
    },
    "province_labels": {
        "Western Cape": {"x": 180, "y": 660},
        "Northern Cape": {"x": 250, "y": 220},
        "Free State": {"x": 520, "y": 455},
        "North West": {"x": 490, "y": 135},
        "Gauteng": {"x": 715, "y": 315},
        "Limpopo": {"x": 740, "y": 15},
        "Mpumalanga": {"x": 880, "y": 145},
        "KwaZulu-Natal": {"x": 875, "y": 455},
        "Eastern Cape": {"x": 680, "y": 640}
    }
}

PROVINCE_TEXT_COLORS = {
    "Western Cape": "#53b7ff",
    "Northern Cape": "#f5b971",
    "Free State": "#ffd166",
    "North West": "#f497b6",
    "Gauteng": "#81d4fa",
    "Limpopo": "#ffb677",
    "Mpumalanga": "#9cc7ff",
    "KwaZulu-Natal": "#ff8f8f",
    "Eastern Cape": "#84d9a5"
}

LABEL_DIRECTIONS = {
    "Western Cape": (0, -26),
    "Northern Cape": (-8, -26),
    "Free State": (0, 26),
    "North West": (-20, -18),
    "Gauteng": (26, -10),
    "Limpopo": (0, -26),
    "Mpumalanga": (26, 0),
    "KwaZulu-Natal": (24, 8),
    "Eastern Cape": (0, 28),
}


def deep_copy(value):
    return json.loads(json.dumps(value))


def edge_key(left, right):
    return "||".join(sorted((left, right)))


def stabilize_map_layout(map_data):
    """Deterministically spreads nodes to reduce overlap on every startup."""
    data = deep_copy(map_data)
    nodes = data.get("nodes", [])
    if not nodes:
        return data

    province_centers = {}
    for node in nodes:
        province = node["province"]
        province_centers.setdefault(province, [0.0, 0.0, 0])
        province_centers[province][0] += node["x"]
        province_centers[province][1] += node["y"]
        province_centers[province][2] += 1

    for province, values in province_centers.items():
        province_centers[province] = (values[0] / values[2], values[1] / values[2])

    for _ in range(35):
        for left_index in range(len(nodes)):
            left = nodes[left_index]
            for right_index in range(left_index + 1, len(nodes)):
                right = nodes[right_index]
                dx = right["x"] - left["x"]
                dy = right["y"] - left["y"]
                distance = math.hypot(dx, dy) or 0.01
                minimum = 70 if left["type"] == "city" or right["type"] == "city" else 54
                if distance >= minimum:
                    continue
                push = (minimum - distance) / 2.0
                ux = dx / distance
                uy = dy / distance
                left["x"] -= ux * push
                left["y"] -= uy * push
                right["x"] += ux * push
                right["y"] += uy * push

        for node in nodes:
            center_x, center_y = province_centers[node["province"]]
            node["x"] += (center_x - node["x"]) * 0.03
            node["y"] += (center_y - node["y"]) * 0.03
            node["x"] = int(max(85, min(CANVAS_WIDTH - 85, node["x"])))
            node["y"] = int(max(80, min(CANVAS_HEIGHT - 120, node["y"])))

    labels = {}
    for province, center in province_centers.items():
        members = [node for node in nodes if node["province"] == province]
        min_x = min(node["x"] for node in members)
        max_x = max(node["x"] for node in members)
        max_y = max(node["y"] for node in members)
        labels[province] = {
            "x": int((min_x + max_x) / 2),
            "y": int(max_y + 48),
        }
    data["province_labels"] = labels
    return data


def format_money(amount):
    prefix = "-" if amount < 0 else ""
    return f"{prefix}R{abs(int(amount))}"


def display_node_label(name):
    replacements = {
        "Gqeberha (Port Elizabeth)": "Gqeberha\n(Port Elizabeth)",
        "Witbank/eMalahleni": "Witbank /\neMalahleni",
        "Louis Trichardt": "Louis\nTrichardt",
        "Kempton Park": "Kempton\nPark",
        "East London": "East\nLondon",
        "Richards Bay": "Richards\nBay",
        "White River": "White\nRiver",
        "Pietermaritzburg": "Pietermaritz-\nburg",
        "Phuthaditjhaba": "Phuthadit-\njhaba",
    }
    return replacements.get(name, name)


class MapStorage:
    def __init__(self, path):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            self.save(DEFAULT_MAP)
        with open(self.path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        data.setdefault("province_borders", {})
        data.setdefault("province_labels", {})
        return data

    def save(self, data):
        payload = deep_copy(data)
        for edge in payload["edges"]:
            edge["owner"] = None
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)


class GameState:
    def __init__(self, map_data):
        self.load_map(map_data)

    def load_map(self, map_data):
        self.map_data = deep_copy(map_data)
        self.nodes = {node["name"]: node for node in self.map_data["nodes"]}
        self.adjacency = {name: [] for name in self.nodes}
        self.edges = {}
        for edge in self.map_data["edges"]:
            key = edge_key(edge["from"], edge["to"])
            if key in self.edges:
                continue
            edge["owner"] = None
            self.edges[key] = edge
            self.adjacency[edge["from"]].append(edge["to"])
            self.adjacency[edge["to"]].append(edge["from"])
        for neighbors in self.adjacency.values():
            neighbors.sort()
        self.new_match()

    def new_match(self):
        vehicles = ["Taxi", "Bus"]
        random.shuffle(vehicles)
        self.players = [
            {
                "name": "Player 1",
                "color": "#ff5d73",
                "vehicle": vehicles[0],
                "position": "Cape Town",
                "points": START_POINTS,
                "skip_turn": 0
            },
            {
                "name": "Player 2",
                "color": "#57a0ff",
                "vehicle": vehicles[1],
                "position": "Cape Town",
                "points": START_POINTS,
                "skip_turn": 0
            }
        ]
        for edge in self.edges.values():
            edge["owner"] = None
        self.claimed_nodes = {"Cape Town"}
        self.current_player_index = 0
        self.turn_number = 1
        self.phase = "move"
        self.turn_invested = False
        self.winner = None
        self.pending_police = None
        self.pending_owner_fee = None
        self.last_transaction = "Opening balance: R120"
        self.last_transaction_node = "Cape Town"
        self.last_transaction_color = "#22c55e"
        self.transaction_version = 1
        self.log_messages = [
            "Cape Town is already claimed at the start of the game.",
            f"{self.current_player['name']} begins the race with R{START_POINTS} cash."
        ]

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    @property
    def opponent(self):
        return self.players[1 - self.current_player_index]

    def log(self, message):
        self.log_messages.append(f"Turn {self.turn_number}: {message}")

    def record_transaction(self, text, node_name=None, color="#e5e7eb"):
        self.last_transaction = text
        self.last_transaction_node = node_name
        self.last_transaction_color = color
        self.transaction_version += 1

    def get_edge(self, left, right):
        return self.edges[edge_key(left, right)]

    def toll_cost(self, from_name, to_name):
        origin = self.nodes[from_name]
        destination = self.nodes[to_name]
        border = self.map_data.get("province_borders", {}).get(origin["province"])
        if border and edge_key(*border) == edge_key(from_name, to_name) and origin["province"] != destination["province"]:
            return math.ceil(destination["pts"] / 2)
        return 0

    def bfs_distances(self, start_name):
        distances = {start_name: 0}
        queue = deque([start_name])
        while queue:
            current = queue.popleft()
            for neighbor in self.adjacency[current]:
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
        return distances

    def accessible_moves(self):
        if self.phase != "move" or self.winner or self.pending_police:
            return []
        player = self.current_player
        moves = []
        for neighbor in self.adjacency[player["position"]]:
            edge = self.get_edge(player["position"], neighbor)
            toll = self.toll_cost(player["position"], neighbor)
            owner_fee = 15 if edge["owner"] and edge["owner"] != player["name"] else 0
            if player["points"] < toll + owner_fee:
                continue
            moves.append(neighbor)
        return moves

    def invest_sources(self):
        if self.phase != "invest" or self.turn_invested or self.winner or self.pending_police:
            return {}
        distances = self.bfs_distances(self.current_player["position"])
        sources = {}
        for start, distance in distances.items():
            if distance != 2:
                continue
            options = []
            for neighbor in sorted(self.adjacency[start]):
                edge = self.get_edge(start, neighbor)
                if edge["owner"]:
                    continue
                cost = self.nodes[neighbor]["pts"]
                if self.current_player["points"] >= cost:
                    options.append({"source": start, "destination": neighbor, "cost": cost})
            if options:
                sources[start] = options
        return sources

    def all_investments(self):
        options = []
        for source, source_options in self.invest_sources().items():
            for option in source_options:
                options.append(option)
        options.sort(key=lambda item: (item["source"], item["destination"]))
        return options

    def begin_move(self, destination):
        if destination not in self.accessible_moves():
            return False, "That node is not reachable right now."
        edge = self.get_edge(self.current_player["position"], destination)
        if edge["owner"] and edge["owner"] != self.current_player["name"]:
            self.pending_owner_fee = {
                "from": self.current_player["position"],
                "to": destination,
                "owner": edge["owner"],
            }
            return True, f"{edge['owner']} owns this road. Pay R15 to use it?"
        if edge["type"] == "police":
            self.pending_police = {
                "from": self.current_player["position"],
                "to": destination
            }
            return True, "Police encounter triggered."
        self.finalize_move(destination, police_note=None)
        return True, f"{self.current_player['name']} moved to {destination}."

    def resolve_owner_fee(self, pay_fee):
        if not self.pending_owner_fee:
            return False, "No owned-road decision is pending."
        if not pay_fee:
            blocked_by = self.pending_owner_fee["owner"]
            destination = self.pending_owner_fee["to"]
            self.pending_owner_fee = None
            return False, f"You declined to pay {blocked_by} for access to {destination}."

        player = self.current_player
        destination = self.pending_owner_fee["to"]
        owner_name = self.pending_owner_fee["owner"]
        total_required = self.toll_cost(self.pending_owner_fee["from"], destination) + 15
        if player["points"] < total_required:
            self.pending_owner_fee = None
            return False, "Not enough cash for the owner fee and toll."

        player["points"] -= 15
        for candidate in self.players:
            if candidate["name"] == owner_name:
                candidate["points"] += 15
                break
        self.log(f"{player['name']} paid R15 to {owner_name} to use the road.")
        self.record_transaction(f"-R15 Access Fee", destination, "#fb7185")
        current_from = self.pending_owner_fee["from"]
        self.pending_owner_fee = None
        edge = self.get_edge(current_from, destination)
        if edge["type"] == "police":
            self.pending_police = {"from": current_from, "to": destination}
            return True, "Owner fee paid. Police encounter triggered."
        self.finalize_move(destination, police_note=None)
        return True, "Owner fee paid."

    def resolve_police(self, choice):
        if not self.pending_police:
            return False, "No police decision is pending."
        if choice not in {"bribe", "refuse"}:
            return False, "Unknown police choice."
        destination = self.pending_police["to"]
        if choice == "bribe":
            total = self.toll_cost(self.pending_police["from"], destination) + 15
            if self.current_player["points"] < total:
                return False, "Not enough cash for the toll and the bribe."
            self.current_player["points"] -= 15
            self.log(f"{self.current_player['name']} bribed the police for R15.")
            self.record_transaction("-R15 Police Bribe", destination, "#ef4444")
            note = "Bribed the police and kept going."
        else:
            if self.current_player["points"] < self.toll_cost(self.pending_police["from"], destination):
                return False, "Not enough cash for the border toll on that route."
            self.current_player["skip_turn"] += 1
            self.log(f"{self.current_player['name']} refused the bribe and will miss the next turn.")
            note = "Refused the police demand and accepted the delay."
        self.finalize_move(destination, police_note=note)
        return True, "Police decision resolved."

    def finalize_move(self, destination, police_note=None):
        player = self.current_player
        toll = self.toll_cost(player["position"], destination)
        if toll:
            player["points"] -= toll
            self.log(f"{player['name']} paid a toll of R{toll} on the way to {destination}.")
            self.record_transaction(f"-R{toll} Toll Fee", destination, "#f59e0b")
        player["position"] = destination
        move_message = f"{player['name']} moved to {destination}."
        if police_note:
            move_message += f" {police_note}"
        self.log(move_message)
        if destination not in self.claimed_nodes:
            self.claimed_nodes.add(destination)
            reward = self.nodes[destination]["pts"]
            player["points"] += reward
            self.log(f"{player['name']} earned R{reward} from {destination}.")
            self.record_transaction(f"+R{reward} Travel Income", destination, "#22c55e")
        self.pending_police = None
        if player["position"] == "Johannesburg" and player["points"] >= TARGET_POINTS:
            self.winner = player["name"]
            self.log(f"{player['name']} reached Johannesburg with R{player['points']} and wins.")
            self.phase = "done"
        else:
            self.phase = "invest"

    def invest(self, source, destination):
        if self.phase != "invest":
            return False, "Investments are only available after moving."
        if self.turn_invested:
            return False, "You already invested this turn."
        for option in self.all_investments():
            if option["source"] == source and option["destination"] == destination:
                self.current_player["points"] -= option["cost"]
                self.get_edge(source, destination)["owner"] = self.current_player["name"]
                self.turn_invested = True
                self.record_transaction(f"-R{option['cost']} Route Investment", destination, "#a78bfa")
                self.log(
                    f"{self.current_player['name']} invested in {source} -> {destination} for R{option['cost']}."
                )
                return True, "Investment completed."
        return False, "That route is not available for investment."

    def can_end_turn(self):
        return self.phase == "invest" and not self.pending_police and not self.winner

    def end_turn(self):
        if not self.can_end_turn():
            return False, "Finish moving before ending the turn."
        self.current_player_index = 1 - self.current_player_index
        self.turn_number += 1
        self.phase = "move"
        self.turn_invested = False
        while self.players[self.current_player_index]["skip_turn"] > 0:
            skipped = self.players[self.current_player_index]
            skipped["skip_turn"] -= 1
            self.log(f"{skipped['name']} lost this turn after refusing a police stop.")
            self.current_player_index = 1 - self.current_player_index
            self.turn_number += 1
        self.log(f"It is now {self.current_player['name']}'s turn.")
        return True, "Turn ended."

    def skip_investment(self):
        if self.phase != "invest":
            return False, "You can only skip during the investment phase."
        self.log(f"{self.current_player['name']} skipped investment.")
        return self.end_turn()


class AgeOfWheelsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Siyaya!")
        self.root.geometry("1360x860")
        self.root.minsize(1280, 800)
        self.storage = MapStorage(os.path.join(os.path.dirname(os.path.abspath(__file__)), MAP_FILE))
        self.map_data = stabilize_map_layout(self.storage.load())
        self.game = GameState(self.map_data)

        self.editor_mode = False
        self.editor_collapsed = True
        self.edge_type_var = tk.StringVar(value="normal")
        self.editor_status_var = tk.StringVar(value="Editor off")
        self.turn_var = tk.StringVar()
        self.phase_var = tk.StringVar()
        self.cash_event_var = tk.StringVar()
        self.invest_hint_var = tk.StringVar()
        self.hovered_node = None
        self.tooltip_after_id = None
        self.tooltip_window = None
        self.police_window = None
        self.owner_fee_window = None
        self.dragging_node = None
        self.drag_moved = False
        self.selected_nodes = []
        self.selected_invest_source = None
        self.editor_forms = []
        self.canvas_items = {"nodes": {}, "labels": {}, "edges": {}, "markers": {}}
        self.glow_on = False
        self.glow_after_id = None
        self.last_log_count = 0
        self.last_transaction_seen = 0
        self.floating_cash = None

        self._configure_theme()
        self._build_ui()
        self._bind_events()
        self.refresh_everything()
        self.animate_glow()

    def _configure_theme(self):
        self.root.configure(bg="#0b1220")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background="#0b1220", foreground="#edf2f7", fieldbackground="#111a2b")
        style.configure("Sidebar.TFrame", background="#111827")
        style.configure("Card.TFrame", background="#182235")
        style.configure("CardTitle.TLabel", background="#182235", foreground="#f8fafc", font=("Segoe UI", 12, "bold"))
        style.configure("Muted.TLabel", background="#111827", foreground="#94a3b8", font=("Segoe UI", 10))
        style.configure("Body.TLabel", background="#111827", foreground="#e5e7eb", font=("Segoe UI", 10))
        style.configure("Accent.TButton", background="#2563eb", foreground="white", padding=8, font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[("active", "#3b82f6")])
        style.configure("Ghost.TButton", background="#1f2937", foreground="#e5e7eb", padding=8, font=("Segoe UI", 10))
        style.map("Ghost.TButton", background=[("active", "#334155")])
        style.configure("Chip.TButton", background="#162235", foreground="#dbeafe", padding=6, font=("Segoe UI", 9, "bold"))
        style.map("Chip.TButton", background=[("active", "#21334d")])
        style.configure("Dark.Horizontal.TProgressbar", troughcolor="#0f172a", bordercolor="#0f172a",
                        background="#38bdf8", lightcolor="#38bdf8", darkcolor="#38bdf8")
        style.configure("Editor.TCombobox", fieldbackground="#0f172a", background="#0f172a", foreground="#e5e7eb")

    def _build_ui(self):
        main = ttk.Frame(self.root, style="Sidebar.TFrame")
        main.pack(fill="both", expand=True)

        self.paned = tk.PanedWindow(main, orient="horizontal", bg="#0b1220", sashwidth=8, showhandle=False)
        self.paned.pack(fill="both", expand=True)

        map_holder = tk.Frame(self.paned, bg="#07111f")
        self.paned.add(map_holder, stretch="always")

        self.canvas = tk.Canvas(
            map_holder,
            width=980,
            height=820,
            bg="#07111f",
            highlightthickness=0,
            scrollregion=(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.x_scroll = ttk.Scrollbar(map_holder, orient="horizontal", command=self.canvas.xview)
        self.x_scroll.grid(row=1, column=0, sticky="ew")
        self.y_scroll = ttk.Scrollbar(map_holder, orient="vertical", command=self.canvas.yview)
        self.y_scroll.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(xscrollcommand=self.x_scroll.set, yscrollcommand=self.y_scroll.set)
        map_holder.rowconfigure(0, weight=1)
        map_holder.columnconfigure(0, weight=1)

        sidebar = ttk.Frame(self.paned, style="Sidebar.TFrame", padding=(16, 16))
        self.paned.add(sidebar, minsize=360)

        title = tk.Label(
            sidebar,
            text="Siyaya! Age of Wheels",
            bg="#111827",
            fg="#f8fafc",
            font=("Segoe UI", 22, "bold")
        )
        title.pack(anchor="w")
        subtitle = ttk.Label(
            sidebar,
            text="South Africa hotseat strategy race",
            style="Muted.TLabel"
        )
        subtitle.pack(anchor="w", pady=(0, 12))

        summary = ttk.Frame(sidebar, style="Card.TFrame", padding=14)
        summary.pack(fill="x", pady=(0, 12))
        ttk.Label(summary, textvariable=self.turn_var, style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(summary, textvariable=self.phase_var, style="Body.TLabel", wraplength=300).pack(anchor="w", pady=(8, 0))

        

        self.player_cards = []
        for _ in range(2):
            card = tk.Frame(
                sidebar,
                bg="#182235",
                highlightthickness=2,
                highlightbackground="#182235",
                highlightcolor="#182235"
            )
            card.pack(fill="x", pady=(0, 10))
            inner = tk.Frame(card, bg="#182235", padx=14, pady=14)
            inner.pack(fill="both", expand=True)
            title_label = tk.Label(inner, bg="#182235", fg="#f8fafc", font=("Segoe UI", 12, "bold"), anchor="w")
            title_label.pack(anchor="w")
            info_label = tk.Label(inner, bg="#182235", fg="#e5e7eb", font=("Segoe UI", 10), justify="left", anchor="w")
            info_label.pack(anchor="w", pady=(6, 4))
            bar = ttk.Progressbar(inner, style="Dark.Horizontal.TProgressbar", maximum=TARGET_POINTS, mode="determinate")
            bar.pack(fill="x")
            self.player_cards.append((card, inner, title_label, info_label, bar))

        actions = ttk.Frame(sidebar, style="Sidebar.TFrame")
        actions.pack(fill="x", pady=(6, 12))
        ttk.Button(actions, text="New Match", style="Ghost.TButton", command=self.new_match).pack(fill="x")

        self.turn_action_card = ttk.Frame(sidebar, style="Card.TFrame", padding=14)
        self.turn_action_card.pack(fill="x", pady=(0, 12))
        ttk.Label(self.turn_action_card, text="Route Shop", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(self.turn_action_card, textvariable=self.invest_hint_var, style="Body.TLabel", wraplength=300).pack(anchor="w", pady=(8, 10))
        self.invest_source_row = tk.Frame(self.turn_action_card, bg="#182235")
        self.invest_source_row.pack(fill="x")
        self.invest_option_grid = tk.Frame(self.turn_action_card, bg="#182235")
        self.invest_option_grid.pack(fill="x", pady=(8, 0))
        self.invest_skip_row = tk.Frame(self.turn_action_card, bg="#182235")
        self.invest_skip_row.pack(fill="x", pady=(8, 0))

        editor_panel = ttk.Frame(sidebar, style="Card.TFrame", padding=14)
        editor_panel.pack(fill="x", pady=(0, 12))
        editor_header = ttk.Frame(editor_panel, style="Card.TFrame")
        editor_header.pack(fill="x")
        ttk.Label(editor_header, text="Editor", style="CardTitle.TLabel").pack(side="left")
        self.editor_collapse_btn = ttk.Button(
            editor_header,
            text="Show",
            style="Ghost.TButton",
            command=self.toggle_editor_pane
        )
        self.editor_collapse_btn.pack(side="right")
        self.editor_body = ttk.Frame(editor_panel, style="Card.TFrame")
        ttk.Label(self.editor_body, textvariable=self.editor_status_var, style="Body.TLabel", wraplength=300).pack(anchor="w", pady=(6, 8))
        editor_buttons = ttk.Frame(self.editor_body, style="Card.TFrame")
        editor_buttons.pack(fill="x")

        ttk.Button(editor_buttons, text="Toggle Editor (E)", style="Ghost.TButton", command=self.toggle_editor).pack(fill="x", pady=(0, 6))
        ttk.Button(editor_buttons, text="Add Node", style="Ghost.TButton", command=self.open_add_node_form).pack(fill="x", pady=(0, 6))
        ttk.Button(editor_buttons, text="Save Map", style="Ghost.TButton", command=self.save_map).pack(fill="x", pady=(0, 6))
        ttk.Label(self.editor_body, text="New edge type", style="Body.TLabel").pack(anchor="w", pady=(6, 4))
        self.edge_type_combo = ttk.Combobox(
            self.editor_body,
            textvariable=self.edge_type_var,
            values=("normal", "police", "toll_border"),
            state="readonly",
            style="Editor.TCombobox"
        )
        self.edge_type_combo.pack(fill="x", pady=(0, 6))
        ttk.Button(self.editor_body, text="Apply Selected Edge", style="Ghost.TButton", command=self.apply_selected_edge).pack(fill="x", pady=(0, 6))
        ttk.Button(self.editor_body, text="Remove Selected Edge", style="Ghost.TButton", command=self.remove_selected_edge).pack(fill="x")

        instructions = ttk.Frame(sidebar, style="Card.TFrame", padding=14)
        instructions.pack(fill="x", pady=(0, 12))
        ttk.Label(instructions, text="Quick Guide", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(
            instructions,
            text=(
                "Move: click a glowing neighboring stop.\n"
                "Route Shop: quick-buy a road after moving, or skip.\n"
                "Editor: optional map tweaking only."
            ),
            style="Body.TLabel",
            justify="left",
            wraplength=300
        ).pack(anchor="w", pady=(6, 0))

        log_frame = ttk.Frame(sidebar, style="Card.TFrame", padding=14)
        log_frame.pack(fill="both", expand=True)
        ttk.Label(log_frame, text="Game Log", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        self.log_widget = ScrolledText(
            log_frame,
            height=16,
            wrap="word",
            bg="#020617",
            fg="#e2e8f0",
            insertbackground="#e2e8f0",
            relief="flat",
            font=("Consolas", 10)
        )
        self.log_widget.pack(fill="both", expand=True)
        self.log_widget.configure(state="disabled")

        self.tooltip_label = tk.Label(
            self.canvas,
            bg="#111827",
            fg="#f8fafc",
            bd=0,
            padx=8,
            pady=4,
            font=("Segoe UI", 9),
            relief="solid"
        )
        self.tooltip_label.place_forget()
        self.toggle_editor_pane(force_collapsed=True)

    def _bind_events(self):
        self.root.bind("<e>", lambda _event: self.toggle_editor())
        self.root.bind("<E>", lambda _event: self.toggle_editor())
        self.canvas.bind("<ButtonPress-1>", self.on_left_press)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Motion>", self.on_canvas_motion)
        self.canvas.bind("<Leave>", lambda _event: self.hide_tooltip())

    def world_coords(self, event):
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def hit_node(self, x, y):
        for node in reversed(self.map_data["nodes"]):
            radius = 18 if node["type"] == "city" else 12
            if (x - node["x"]) ** 2 + (y - node["y"]) ** 2 <= radius ** 2:
                return node
        return None

    def hit_edge(self, x, y):
        nodes_by_name = {node["name"]: node for node in self.map_data["nodes"]}
        for edge in self.map_data["edges"]:
            start = nodes_by_name.get(edge["from"])
            end = nodes_by_name.get(edge["to"])
            if not start or not end:
                continue
            distance = self.point_to_segment_distance(x, y, start["x"], start["y"], end["x"], end["y"])
            if distance <= 6:
                return edge
        return None

    @staticmethod
    def point_to_segment_distance(px, py, ax, ay, bx, by):
        dx = bx - ax
        dy = by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = ((px - ax) * dx + (py - ay) * dy) / float(dx * dx + dy * dy)
        t = max(0.0, min(1.0, t))
        nearest_x = ax + t * dx
        nearest_y = ay + t * dy
        return math.hypot(px - nearest_x, py - nearest_y)

    def on_left_press(self, event):
        x, y = self.world_coords(event)
        node = self.hit_node(x, y)
        self.dragging_node = node if self.editor_mode else None
        self.drag_moved = False
        if self.editor_mode and node:
            self.select_editor_node(node["name"])

    def on_left_drag(self, event):
        if not self.editor_mode or not self.dragging_node:
            return
        x, y = self.world_coords(event)
        self.drag_moved = True
        self.dragging_node["x"] = int(x)
        self.dragging_node["y"] = int(y)
        if self.dragging_node["province"] not in self.map_data["province_labels"]:
            self.map_data["province_labels"][self.dragging_node["province"]] = {"x": int(x), "y": int(y + 40)}
        self.redraw_map()

    def on_left_release(self, event):
        x, y = self.world_coords(event)
        node = self.hit_node(x, y)
        if self.editor_mode:
            if self.dragging_node and self.drag_moved:
                self.editor_status_var.set(f"Moved {self.dragging_node['name']} to ({self.dragging_node['x']}, {self.dragging_node['y']}).")
            self.dragging_node = None
            self.drag_moved = False
            return

        if self.police_window is not None or self.owner_fee_window is not None or self.game.winner:
            return

        if node is None:
            return
        if self.game.phase == "move":
            ok, message = self.game.begin_move(node["name"])
            if not ok:
                self.log(message)
            else:
                if self.game.pending_owner_fee:
                    self.open_owner_fee_modal()
                elif self.game.pending_police:
                    self.open_police_modal()
                else:
                    self.after_action_refresh()
        elif self.game.phase == "invest":
            investable = self.game.invest_sources()
            if node["name"] in investable:
                self.selected_invest_source = node["name"]
                self.invest_hint_var.set(f"Invest from {node['name']} or skip this turn.")
                self.refresh_everything()

    def on_right_click(self, event):
        if not self.editor_mode:
            return
        x, y = self.world_coords(event)
        node = self.hit_node(x, y)
        if node:
            self.open_node_editor(node)
            return
        edge = self.hit_edge(x, y)
        if edge:
            self.open_edge_menu(edge, event.x_root, event.y_root)

    def on_canvas_motion(self, event):
        x, y = self.world_coords(event)
        node = self.hit_node(x, y)
        if node:
            self.show_tooltip(event.x + 14, event.y + 18, f"{node['name']}\n{node['province']} · R{node['pts']}")
        else:
            self.hide_tooltip()

    def show_tooltip(self, x, y, text):
        self.tooltip_label.configure(text=text)
        self.tooltip_label.place(x=x, y=y)

    def hide_tooltip(self):
        self.tooltip_label.place_forget()

    def select_editor_node(self, name):
        if name in self.selected_nodes:
            return
        self.selected_nodes.append(name)
        self.selected_nodes = self.selected_nodes[-2:]
        if len(self.selected_nodes) == 1:
            self.editor_status_var.set(f"Selected node {self.selected_nodes[0]}. Choose another node or drag it.")
        else:
            self.editor_status_var.set(
                f"Selected edge pair: {self.selected_nodes[0]} -> {self.selected_nodes[1]}."
            )
        self.redraw_map()

    def open_node_editor(self, node):
        window = tk.Toplevel(self.root)
        window.title(f"Edit Node - {node['name']}")
        window.configure(bg="#111827")
        window.transient(self.root)
        form = {}
        fields = [("Name", "name"), ("Province", "province"), ("Cash Value", "pts"), ("Type", "type")]
        for row, (label_text, key) in enumerate(fields):
            tk.Label(window, text=label_text, bg="#111827", fg="#e5e7eb", font=("Segoe UI", 10)).grid(
                row=row, column=0, sticky="w", padx=12, pady=8
            )
            entry = ttk.Entry(window)
            entry.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
            entry.insert(0, str(node[key]))
            form[key] = entry
        window.columnconfigure(1, weight=1)

        def save_changes():
            old_name = node["name"]
            new_name = form["name"].get().strip()
            province = form["province"].get().strip()
            node_type = form["type"].get().strip().lower()
            try:
                pts = int(form["pts"].get().strip())
            except ValueError:
                messagebox.showerror("Invalid cash value", "Cash value must be an integer.", parent=window)
                return
            if not new_name or not province or node_type not in {"city", "town"}:
                messagebox.showerror("Missing data", "Provide a name, province, and type of city or town.", parent=window)
                return
            if new_name != old_name and new_name in {item["name"] for item in self.map_data["nodes"]}:
                messagebox.showerror("Duplicate name", "Node names must remain unique.", parent=window)
                return
            node["name"] = new_name
            node["province"] = province
            node["pts"] = pts
            node["type"] = node_type
            for edge in self.map_data["edges"]:
                if edge["from"] == old_name:
                    edge["from"] = new_name
                if edge["to"] == old_name:
                    edge["to"] = new_name
            for province_name, border in list(self.map_data.get("province_borders", {}).items()):
                if border[0] == old_name:
                    border[0] = new_name
                if border[1] == old_name:
                    border[1] = new_name
                if province_name == old_name:
                    self.map_data["province_borders"][new_name] = self.map_data["province_borders"].pop(province_name)
            self.reload_map_from_editor()
            self.editor_status_var.set(f"Updated node {new_name}.")
            window.destroy()

        ttk.Button(window, text="Save Node", style="Accent.TButton", command=save_changes).grid(
            row=len(fields), column=0, columnspan=2, sticky="ew", padx=12, pady=12
        )

    def open_edge_menu(self, edge, x_root, y_root):
        menu = tk.Menu(self.root, tearoff=0, bg="#0f172a", fg="#e5e7eb", activebackground="#1d4ed8", activeforeground="white")
        for edge_type in ("normal", "police", "toll_border"):
            menu.add_command(label=f"Set {edge_type}", command=lambda kind=edge_type: self.update_edge_type(edge, kind))
        menu.add_separator()
        menu.add_command(label="Delete edge", command=lambda: self.delete_edge(edge))
        menu.tk_popup(x_root, y_root)

    def update_edge_type(self, edge, kind):
        edge["type"] = kind
        self.editor_status_var.set(f"Updated edge {edge['from']} -> {edge['to']} to {kind}.")
        self.reload_map_from_editor()

    def delete_edge(self, edge):
        self.map_data["edges"] = [item for item in self.map_data["edges"] if item is not edge]
        self.editor_status_var.set(f"Removed edge {edge['from']} -> {edge['to']}.")
        self.reload_map_from_editor()

    def open_add_node_form(self):
        if not self.editor_mode:
            self.toggle_editor()
        window = tk.Toplevel(self.root)
        window.title("Add Node")
        window.configure(bg="#111827")
        window.transient(self.root)
        defaults = {
            "name": "",
            "province": "",
            "pts": "5",
            "type": "town",
            "x": "950",
            "y": "650"
        }
        entries = {}
        for row, (label, key) in enumerate(
            [("Name", "name"), ("Province", "province"), ("Cash Value", "pts"), ("Type", "type"), ("X", "x"), ("Y", "y")]
        ):
            tk.Label(window, text=label, bg="#111827", fg="#e5e7eb", font=("Segoe UI", 10)).grid(
                row=row, column=0, sticky="w", padx=12, pady=8
            )
            entry = ttk.Entry(window)
            entry.grid(row=row, column=1, sticky="ew", padx=12, pady=8)
            entry.insert(0, defaults[key])
            entries[key] = entry
        window.columnconfigure(1, weight=1)

        def add_node():
            try:
                pts = int(entries["pts"].get().strip())
                x = int(entries["x"].get().strip())
                y = int(entries["y"].get().strip())
            except ValueError:
                messagebox.showerror("Invalid values", "Cash value, x and y must be integers.", parent=window)
                return
            name = entries["name"].get().strip()
            province = entries["province"].get().strip()
            node_type = entries["type"].get().strip().lower()
            if not name or not province or node_type not in {"city", "town"}:
                messagebox.showerror("Missing data", "Provide a name, province, and type of city or town.", parent=window)
                return
            if name in {node["name"] for node in self.map_data["nodes"]}:
                messagebox.showerror("Duplicate node", "That node name already exists.", parent=window)
                return
            self.map_data["nodes"].append(
                {"name": name, "province": province, "pts": pts, "type": node_type, "x": x, "y": y}
            )
            self.map_data.setdefault("province_labels", {}).setdefault(province, {"x": x, "y": y + 40})
            self.reload_map_from_editor()
            self.editor_status_var.set(f"Added node {name}.")
            window.destroy()

        ttk.Button(window, text="Create Node", style="Accent.TButton", command=add_node).grid(
            row=6, column=0, columnspan=2, sticky="ew", padx=12, pady=12
        )

    def apply_selected_edge(self):
        if len(self.selected_nodes) != 2:
            self.editor_status_var.set("Select two nodes first.")
            return
        left, right = self.selected_nodes
        key = edge_key(left, right)
        for edge in self.map_data["edges"]:
            if edge_key(edge["from"], edge["to"]) == key:
                edge["type"] = self.edge_type_var.get()
                self.editor_status_var.set(f"Updated edge {left} -> {right} to {self.edge_type_var.get()}.")
                self.reload_map_from_editor()
                return
        self.map_data["edges"].append({"from": left, "to": right, "type": self.edge_type_var.get(), "owner": None})
        self.editor_status_var.set(f"Added {self.edge_type_var.get()} edge between {left} and {right}.")
        self.reload_map_from_editor()

    def remove_selected_edge(self):
        if len(self.selected_nodes) != 2:
            self.editor_status_var.set("Select two nodes first.")
            return
        left, right = self.selected_nodes
        key = edge_key(left, right)
        original_count = len(self.map_data["edges"])
        self.map_data["edges"] = [edge for edge in self.map_data["edges"] if edge_key(edge["from"], edge["to"]) != key]
        if len(self.map_data["edges"]) == original_count:
            self.editor_status_var.set("No edge existed between those nodes.")
        else:
            self.editor_status_var.set(f"Removed edge between {left} and {right}.")
            self.reload_map_from_editor()

    def reload_map_from_editor(self):
        self.map_data = stabilize_map_layout(self.map_data)
        self.game.load_map(self.map_data)
        self.selected_nodes = [name for name in self.selected_nodes if name in self.game.nodes]
        self.refresh_everything()

    def save_map(self):
        self.map_data = stabilize_map_layout(self.map_data)
        self.storage.save(self.map_data)
        self.editor_status_var.set("Saved map_data.json.")
        self.log("Map changes saved to map_data.json.")

    def toggle_editor_pane(self, force_collapsed=None):
        if force_collapsed is None:
            self.editor_collapsed = not self.editor_collapsed
        else:
            self.editor_collapsed = force_collapsed
        if self.editor_collapsed:
            self.editor_body.pack_forget()
            self.editor_collapse_btn.configure(text="Show")
        else:
            self.editor_body.pack(fill="x", pady=(6, 0))
            self.editor_collapse_btn.configure(text="Hide")



    def toggle_editor(self):
        self.editor_mode = not self.editor_mode
        if self.editor_mode:
            self.editor_status_var.set("Editor on. Drag nodes, left-click two nodes for an edge, right-click nodes or edges to edit.")
        else:
            self.selected_nodes.clear()
            self.editor_status_var.set("Editor off")
        self.redraw_map()

    def open_police_modal(self):
        if self.police_window is not None or not self.game.pending_police:
            return
        pending = self.game.pending_police
        window = tk.Toplevel(self.root)
        window.title("Police Encounter")
        window.configure(bg="#111827")
        window.transient(self.root)
        window.grab_set()
        self.police_window = window
        tk.Label(
            window,
            text=f"Police on {pending['from']} -> {pending['to']}",
            bg="#111827",
            fg="#f8fafc",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=18, pady=(16, 6))
        tk.Label(
            window,
            text="Bribe for R15 or refuse and lose your next turn.",
            bg="#111827",
            fg="#e5e7eb",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=18, pady=(0, 14))
        button_row = tk.Frame(window, bg="#111827")
        button_row.pack(fill="x", padx=18, pady=(0, 18))
        ttk.Button(button_row, text="Bribe (R15)", style="Accent.TButton",
                   command=lambda: self.finish_police("bribe")).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(button_row, text="Refuse", style="Ghost.TButton",
                   command=lambda: self.finish_police("refuse")).pack(side="left", fill="x", expand=True)
        window.protocol("WM_DELETE_WINDOW", lambda: None)

    def open_owner_fee_modal(self):
        if self.owner_fee_window is not None or not self.game.pending_owner_fee:
            return
        pending = self.game.pending_owner_fee
        window = tk.Toplevel(self.root)
        window.title("Owned Road")
        window.configure(bg="#111827")
        window.transient(self.root)
        window.grab_set()
        self.owner_fee_window = window
        tk.Label(
            window,
            text=f"{pending['owner']} owns {pending['from']} -> {pending['to']}",
            bg="#111827",
            fg="#f8fafc",
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=18, pady=(16, 6))
        tk.Label(
            window,
            text="Pay R15 to the owner to use this route, or cancel and choose another road.",
            bg="#111827",
            fg="#e5e7eb",
            font=("Segoe UI", 10),
            wraplength=320,
            justify="left"
        ).pack(anchor="w", padx=18, pady=(0, 14))
        button_row = tk.Frame(window, bg="#111827")
        button_row.pack(fill="x", padx=18, pady=(0, 18))
        ttk.Button(
            button_row, text="Pay R15", style="Accent.TButton", command=lambda: self.finish_owner_fee(True)
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(
            button_row, text="Cancel", style="Ghost.TButton", command=lambda: self.finish_owner_fee(False)
        ).pack(side="left", fill="x", expand=True)
        window.protocol("WM_DELETE_WINDOW", lambda: None)

    def finish_owner_fee(self, pay_fee):
        ok, message = self.game.resolve_owner_fee(pay_fee)
        if self.owner_fee_window:
            self.owner_fee_window.grab_release()
            self.owner_fee_window.destroy()
            self.owner_fee_window = None
        if not ok:
            self.log(message)
            self.refresh_everything()
            return
        if self.game.pending_police:
            self.refresh_everything()
            self.open_police_modal()
        else:
            self.after_action_refresh()

    def finish_police(self, choice):
        ok, message = self.game.resolve_police(choice)
        if not ok:
            messagebox.showwarning("Police", message, parent=self.police_window)
            return
        if self.police_window:
            self.police_window.grab_release()
            self.police_window.destroy()
            self.police_window = None
        self.after_action_refresh()

    def confirm_investment(self, option):
        ok, message = self.game.invest(option["source"], option["destination"])
        if not ok:
            self.log(message)
            self.refresh_everything()
            return
        self.selected_invest_source = None
        self.game.end_turn()
        self.refresh_everything()

    def skip_investment(self):
        self.selected_invest_source = None
        ok, message = self.game.skip_investment()
        if not ok:
            self.log(message)
        self.refresh_everything()

    def new_match(self):
        self.game.new_match()
        self.selected_invest_source = None
        self.log("Started a new match.")
        self.refresh_everything()

    def after_action_refresh(self):
        self.refresh_everything()
        if self.game.winner:
            wants_rematch = messagebox.askyesno(
                "Winner",
                f"{self.game.winner} wins!\n\nStart a rematch?",
                parent=self.root
            )
            if wants_rematch:
                self.new_match()
            return
        if self.game.phase == "invest" and not self.game.all_investments():
            self.game.skip_investment()
            self.refresh_everything()

    def log(self, message):
        self.game.log(message) if not message.startswith("Turn ") else None
        self.refresh_log()

    def update_cash_feedback(self):
        self.cash_event_var.set(self.game.last_transaction)
        if self.game.transaction_version != self.last_transaction_seen:
            self.last_transaction_seen = self.game.transaction_version
            anchor = self.game.last_transaction_node
            if anchor and anchor in self.game.nodes:
                node = self.game.nodes[anchor]
                self.floating_cash = {
                    "text": self.game.last_transaction,
                    "x": node["x"],
                    "y": node["y"] - 26,
                    "color": self.game.last_transaction_color,
                    "ttl": 12,
                }

    def draw_shadowed_text(self, x, y, text, fill, font, anchor="center", justify="center", shadow="#020617"):
        self.canvas.create_text(
            x + 1, y + 1,
            text=text,
            fill=shadow,
            font=font,
            anchor=anchor,
            justify=justify
        )
        return self.canvas.create_text(
            x, y,
            text=text,
            fill=fill,
            font=font,
            anchor=anchor,
            justify=justify
        )

    def draw_info_panel(self, x1, y1, x2, y2, title, body_lines):
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#08111f",
            outline="#1e293b",
            width=2
        )
        self.draw_shadowed_text(
            x1 + 14, y1 + 14,
            title,
            fill="#f8fafc",
            font=("Segoe UI", 11, "bold"),
            anchor="nw",
            justify="left"
        )
        self.draw_shadowed_text(
            x1 + 14, y1 + 36,
            "\n".join(body_lines),
            fill="#dbeafe",
            font=("Segoe UI", 9),
            anchor="nw",
            justify="left"
        )

    def refresh_turn_actions(self):
        for child in self.invest_source_row.winfo_children():
            child.destroy()
        for child in self.invest_option_grid.winfo_children():
            child.destroy()
        for child in self.invest_skip_row.winfo_children():
            child.destroy()

        if self.game.phase == "move":
            self.invest_hint_var.set("Move on the map first. After landing, quick-buy road options appear here.")
            return

        if self.game.phase == "done":
            self.invest_hint_var.set("Match complete. Start a new match to play again.")
            return

        grouped = self.game.invest_sources()
        if not grouped:
            self.invest_hint_var.set("No investments available this turn. The game will skip ahead.")
            return

        sources = sorted(grouped.keys())
        if self.selected_invest_source not in grouped:
            self.selected_invest_source = sources[0]

        self.invest_hint_var.set(
            f"Pick a source two stops ahead, then tap a destination to buy that road."
        )

        for source in sources:
            style = "Accent.TButton" if source == self.selected_invest_source else "Chip.TButton"
            ttk.Button(
                self.invest_source_row,
                text=f"From {source}",
                style=style,
                command=lambda current=source: self.select_invest_source(current)
            ).pack(side="left", padx=(0, 6), pady=(0, 6))

        selected_options = grouped[self.selected_invest_source]
        for index, option in enumerate(selected_options):
            row = index // 2
            column = index % 2
            ttk.Button(
                self.invest_option_grid,
                text=f"Buy to {option['destination']}\nR{option['cost']}",
                style="Accent.TButton",
                command=lambda current=option: self.confirm_investment(current)
            ).grid(row=row, column=column, sticky="ew", padx=4, pady=4)
        self.invest_option_grid.columnconfigure(0, weight=1)
        self.invest_option_grid.columnconfigure(1, weight=1)

        ttk.Button(
            self.invest_skip_row,
            text="Skip This Buy",
            style="Ghost.TButton",
            command=self.skip_investment
        ).pack(fill="x")

    def select_invest_source(self, source_name):
        self.selected_invest_source = source_name
        self.refresh_turn_actions()

    def refresh_log(self):
        if len(self.game.log_messages) == self.last_log_count:
            return
        self.log_widget.configure(state="normal")
        self.log_widget.delete("1.0", "end")
        self.log_widget.insert("end", "\n".join(self.game.log_messages))
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")
        self.last_log_count = len(self.game.log_messages)
        self.log_widget.update_idletasks()

    def refresh_everything(self):
        self.turn_var.set(
            f"Turn {self.game.turn_number} · {self.game.current_player['name']} · {self.game.current_player['vehicle']}"
        )
        if self.game.phase == "move":
            phase_text = "Move phase: click a reachable neighboring stop."
        elif self.game.phase == "invest":
            phase_text = "Route Shop phase: buy a road from the sidebar or skip."
        else:
            phase_text = "Game over."
        self.phase_var.set(phase_text)
        self.update_cash_feedback()

        for idx, (card, inner, title_label, info_label, bar) in enumerate(self.player_cards):
            player = self.game.players[idx]
            is_active = idx == self.game.current_player_index and self.game.winner is None
            bg = "#24344d" if is_active and self.glow_on else "#182235"
            border = player["color"] if is_active else "#182235"
            card.configure(bg=bg, highlightbackground=border, highlightcolor=border)
            inner.configure(bg=bg)
            title_label.configure(bg=bg)
            info_label.configure(bg=bg)
            title_label.configure(text=f"{player['name']} · {player['vehicle']}")
            info_label.configure(
                text=(
                    f"Location: {player['position']}\n"
                    f"Balance: R{player['points']} / R{TARGET_POINTS}\n"
                    f"Skip next turn: {player['skip_turn']}"
                )
            )
            bar.configure(value=min(player["points"], TARGET_POINTS))
        self.refresh_turn_actions()
        self.redraw_map()
        self.refresh_log()
        self.root.update_idletasks()

    def redraw_map(self):
        self.canvas.delete("all")
        invest_sources = self.game.invest_sources()
        move_targets = set(self.game.accessible_moves())
        nodes_by_name = {node["name"]: node for node in self.map_data["nodes"]}

        for edge in self.map_data["edges"]:
            start = nodes_by_name.get(edge["from"])
            end = nodes_by_name.get(edge["to"])
            if not start or not end:
                continue
            owner = self.game.get_edge(edge["from"], edge["to"]).get("owner")
            color = "#64748b"
            width = 2
            dash = None
            if owner == "Player 1":
                color = "#ff5d73"
                width = 4
            elif owner == "Player 2":
                color = "#57a0ff"
                width = 4
            elif edge["type"] == "police":
                color = "#ef4444"
                dash = (7, 4)
                width = 3
            elif edge["type"] == "toll_border":
                color = "#f59e0b"
                dash = (10, 6)
                width = 3
            self.canvas.create_line(start["x"], start["y"], end["x"], end["y"], fill=color, width=width, dash=dash)

        for province, position in self.map_data.get("province_labels", {}).items():
            self.draw_shadowed_text(
                position["x"], position["y"],
                province,
                fill=PROVINCE_TEXT_COLORS.get(province, "#8ea1b8"),
                font=("Segoe UI", 14, "bold")
            )

        for node in self.map_data["nodes"]:
            name = node["name"]
            radius = 19 if node["type"] == "city" else 13
            fill = "#111827"
            outline = "#cbd5e1"
            width = 2
            if name == self.game.current_player["position"]:
                fill = "#1d4ed8"
                outline = "#93c5fd"
                width = 3
            elif name in move_targets and self.game.phase == "move":
                fill = "#132f4c"
                outline = "#22d3ee"
                width = 3
            elif name in invest_sources and self.game.phase == "invest":
                fill = "#291f08"
                outline = "#facc15" if self.glow_on else "#f59e0b"
                width = 5 if self.glow_on else 3
            elif name in self.game.claimed_nodes:
                fill = "#172033"
                outline = "#64748b"
            if self.editor_mode and name in self.selected_nodes:
                outline = "#f97316"
                width = 4
            self.canvas.create_oval(
                node["x"] - radius, node["y"] - radius, node["x"] + radius, node["y"] + radius,
                fill=fill, outline=outline, width=width
            )
            label_fill = "#f8fafc" if node["type"] == "city" else "#dbeafe"
            dx, dy = LABEL_DIRECTIONS.get(node["province"], (0, -24))
            self.draw_shadowed_text(
                node["x"] + dx, node["y"] + dy,
                f"{display_node_label(name)}\nR{node['pts']}",
                fill=label_fill,
                justify="center",
                font=("Segoe UI", 8, "bold" if node["type"] == "city" else "normal")
            )

        offsets = [(-10, -10), (10, 10)]
        for index, player in enumerate(self.game.players):
            node = nodes_by_name[player["position"]]
            dx, dy = offsets[index]
            active = index == self.game.current_player_index and self.game.winner is None
            marker_radius = 8 if active and self.glow_on else 6
            outline = "#fde68a" if active else "#f8fafc"
            outline_width = 4 if active else 2
            self.canvas.create_oval(
                node["x"] + dx - marker_radius, node["y"] + dy - marker_radius,
                node["x"] + dx + marker_radius, node["y"] + dy + marker_radius,
                fill=player["color"], outline=outline, width=outline_width
            )

        if self.floating_cash and self.floating_cash["ttl"] > 0:
            offset = 14 - self.floating_cash["ttl"]
            self.draw_shadowed_text(
                self.floating_cash["x"],
                self.floating_cash["y"] - offset,
                self.floating_cash["text"],
                fill=self.floating_cash["color"],
                font=("Segoe UI", 11, "bold")
            )

        hud_lines = [
            f"{self.game.current_player['name']} balance: R{self.game.current_player['points']}",
            f"Target: R{TARGET_POINTS} at Johannesburg",
            f"Latest: {self.game.last_transaction}",
        ]
        self.draw_info_panel(CANVAS_WIDTH - 290, 20, CANVAS_WIDTH - 20, 102, "Cash Tracker", hud_lines)

        legend_x = 24
        legend_y = 20
        self.canvas.create_rectangle(
            legend_x - 12, legend_y - 10, legend_x + 308, legend_y + 92,
            fill="#08111f",
            outline="#1e293b",
            width=2
        )
        self.draw_shadowed_text(
            legend_x, legend_y,
            "How to Read the Map",
            fill="#e2e8f0",
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        )

        self.canvas.create_oval(
            legend_x, legend_y + 18, legend_x + 18, legend_y + 36,
            fill="#132f4c", outline="#22d3ee", width=3
        )
        self.draw_shadowed_text(
            legend_x + 28, legend_y + 27,
            "Blue glow = move now",
            fill="#cbd5e1",
            font=("Segoe UI", 9),
            anchor="w"
        )

        self.canvas.create_oval(
            legend_x + 130, legend_y + 18, legend_x + 148, legend_y + 36,
            fill="#291f08", outline="#facc15", width=4
        )
        self.draw_shadowed_text(
            legend_x + 158, legend_y + 27,
            "Gold glow = buy road",
            fill="#cbd5e1",
            font=("Segoe UI", 9),
            anchor="w"
        )

        self.canvas.create_line(
            legend_x, legend_y + 54, legend_x + 22, legend_y + 54,
            fill="#ef4444", width=3, dash=(7, 4)
        )
        self.draw_shadowed_text(
            legend_x + 28, legend_y + 54,
            "Red dash = police",
            fill="#cbd5e1",
            font=("Segoe UI", 9),
            anchor="w"
        )

        self.canvas.create_line(
            legend_x + 130, legend_y + 54, legend_x + 152, legend_y + 54,
            fill="#f59e0b", width=3, dash=(10, 6)
        )
        self.draw_shadowed_text(
            legend_x + 158, legend_y + 54,
            "Amber dash = toll",
            fill="#cbd5e1",
            font=("Segoe UI", 9),
            anchor="w"
        )

        self.canvas.create_oval(
            legend_x, legend_y + 71, legend_x + 14, legend_y + 85,
            fill="#57a0ff", outline="#fde68a", width=3
        )
        self.draw_shadowed_text(
            legend_x + 28, legend_y + 78,
            "Gold ring = your turn",
            fill="#cbd5e1",
            font=("Segoe UI", 9),
            anchor="w"
        )

    def animate_glow(self):
        self.glow_on = not self.glow_on
        if self.floating_cash and self.floating_cash["ttl"] > 0:
            self.floating_cash["ttl"] -= 1
        self.refresh_everything()
        self.glow_after_id = self.root.after(450, self.animate_glow)


def main():
    root = tk.Tk()
    app = AgeOfWheelsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

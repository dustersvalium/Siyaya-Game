from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from age_of_wheels import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    MAP_FILE,
    PROVINCE_TEXT_COLORS,
    GameState,
    MapStorage,
    TARGET_POINTS,
    display_node_label,
    stabilize_map_layout,
)


BACKGROUND = (8, 13, 25)
MAP_BG = (7, 17, 31)
PANEL_BG = (17, 24, 39)
CARD_BG = (24, 34, 53)
TEXT = (238, 242, 255)
MUTED = (154, 166, 190)
BORDER = (54, 65, 90)
CYAN = (34, 211, 238)
GOLD = (250, 204, 21)
AMBER = (245, 158, 11)
RED = (239, 68, 68)
BLUE = (87, 160, 255)
PINK = (255, 93, 115)
GREEN = (34, 197, 94)
OVERLAY = (4, 9, 18, 190)


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: Callable[[], None]
    fill: Tuple[int, int, int]
    text_color: Tuple[int, int, int] = TEXT


class SiyayaPygameApp:
    def __init__(self) -> None:
        print("Launching Siyaya Pygame window...", flush=True)
        pygame.init()
        pygame.display.set_caption("Siyaya! - Pygame Edition")
        self.screen = pygame.display.set_mode((1280, 820), pygame.RESIZABLE)
        print(f"Pygame display initialized at {self.screen.get_size()}.", flush=True)
        self.clock = pygame.time.Clock()
        self.running = True

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage = MapStorage(os.path.join(self.base_dir, MAP_FILE))
        self.map_data = stabilize_map_layout(self.storage.load())
        self.game = GameState(self.map_data)

        self.font_title = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self.font_heading = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 15)
        self.font_small = pygame.font.SysFont("Segoe UI", 12)
        self.font_tiny = pygame.font.SysFont("Segoe UI", 11)

        self.selected_invest_source: Optional[str] = None
        self.hover_node: Optional[str] = None
        self.buttons: List[Button] = []
        self.last_size = self.screen.get_size()

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            if self.screen.get_size() != self.last_size:
                self.last_size = self.screen.get_size()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.VIDEORESIZE:
            width = max(1024, event.w)
            height = max(680, event.h)
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_n:
                self.start_new_match()
            return

        if event.type == pygame.MOUSEMOTION:
            self.hover_node = self.node_at_point(event.pos)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.handle_left_click(event.pos)

    def start_new_match(self) -> None:
        self.game.new_match()
        self.selected_invest_source = None

    def layout(self) -> Tuple[pygame.Rect, pygame.Rect]:
        width, height = self.screen.get_size()
        panel_width = max(280, min(340, int(width * 0.27)))
        map_rect = pygame.Rect(0, 0, width - panel_width, height)
        panel_rect = pygame.Rect(width - panel_width, 0, panel_width, height)
        return map_rect, panel_rect

    def map_transform(self, map_rect: pygame.Rect) -> Tuple[float, float, float]:
        nodes = self.map_data["nodes"]
        min_x = min(node["x"] for node in nodes)
        max_x = max(node["x"] for node in nodes)
        min_y = min(node["y"] for node in nodes)
        max_y = max(node["y"] for node in nodes)
        world_w = max_x - min_x
        world_h = max_y - min_y
        padding = 42
        scale = min(
            (map_rect.width - padding * 2) / max(1, world_w),
            (map_rect.height - padding * 2) / max(1, world_h),
        )
        offset_x = map_rect.x + (map_rect.width - world_w * scale) / 2 - min_x * scale
        offset_y = map_rect.y + (map_rect.height - world_h * scale) / 2 - min_y * scale
        return scale, offset_x, offset_y

    def world_to_screen(self, x: float, y: float, map_rect: pygame.Rect) -> Tuple[int, int]:
        scale, offset_x, offset_y = self.map_transform(map_rect)
        return int(x * scale + offset_x), int(y * scale + offset_y)

    def node_radius(self, node: Dict, map_rect: pygame.Rect) -> int:
        scale, _, _ = self.map_transform(map_rect)
        base = 18 if node["type"] == "city" else 12
        return max(10, int(base * scale * 0.55))

    def node_at_point(self, point: Tuple[int, int]) -> Optional[str]:
        map_rect, _panel_rect = self.layout()
        if not map_rect.collidepoint(point):
            return None
        for node in reversed(self.map_data["nodes"]):
            sx, sy = self.world_to_screen(node["x"], node["y"], map_rect)
            radius = self.node_radius(node, map_rect)
            dx = point[0] - sx
            dy = point[1] - sy
            if dx * dx + dy * dy <= radius * radius:
                return node["name"]
        return None

    def handle_left_click(self, position: Tuple[int, int]) -> None:
        for button in self.buttons:
            if button.rect.collidepoint(position):
                button.action()
                return

        if self.game.winner:
            return

        node_name = self.node_at_point(position)
        if node_name is None:
            return

        if self.game.pending_owner_fee or self.game.pending_police:
            return

        if self.game.phase == "move":
            ok, _message = self.game.begin_move(node_name)
            if ok and not self.game.pending_owner_fee and not self.game.pending_police:
                self.after_action_refresh()
            return

        if self.game.phase == "invest":
            grouped = self.game.invest_sources()
            if node_name in grouped:
                self.selected_invest_source = node_name
                return

            if self.selected_invest_source and self.selected_invest_source in grouped:
                for option in grouped[self.selected_invest_source]:
                    if option["destination"] == node_name:
                        ok, _message = self.game.invest(option["source"], option["destination"])
                        if ok:
                            self.selected_invest_source = None
                            self.game.end_turn()
                            self.after_action_refresh()
                        return

    def after_action_refresh(self) -> None:
        if self.game.winner:
            self.selected_invest_source = None
            return
        if self.game.phase == "invest" and not self.game.all_investments():
            if not self.game.can_offer_investment():
                reason = f"{self.game.current_player['name']} can only buy roads every second personal turn."
            else:
                reason = (
                    f"{self.game.current_player['name']} has no eligible Route Shop buys from untraveled source nodes."
                )
            self.game.skip_investment(reason=reason)
        if self.game.phase != "invest":
            self.selected_invest_source = None
        else:
            grouped = self.game.invest_sources()
            if self.selected_invest_source not in grouped:
                self.selected_invest_source = next(iter(grouped), None)

    def resolve_owner_fee(self, pay_fee: bool) -> None:
        ok, _message = self.game.resolve_owner_fee(pay_fee)
        if ok and not self.game.pending_police:
            self.after_action_refresh()

    def resolve_police(self, choice: str) -> None:
        ok, _message = self.game.resolve_police(choice)
        if ok:
            self.after_action_refresh()

    def skip_investment(self) -> None:
        self.selected_invest_source = None
        self.game.skip_investment()
        self.after_action_refresh()

    def draw(self) -> None:
        self.screen.fill(BACKGROUND)
        map_rect, panel_rect = self.layout()
        pygame.draw.rect(self.screen, MAP_BG, map_rect)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, BORDER, (panel_rect.x, 0), (panel_rect.x, panel_rect.bottom), 2)
        self.buttons = []

        self.draw_map(map_rect)
        self.draw_panel(panel_rect)

        if self.game.pending_owner_fee:
            self.draw_owner_fee_modal()
        elif self.game.pending_police:
            self.draw_police_modal()
        elif self.game.winner:
            self.draw_winner_modal()

    def draw_map(self, map_rect: pygame.Rect) -> None:
        nodes_by_name = {node["name"]: node for node in self.map_data["nodes"]}
        accessible = set(self.game.accessible_moves())
        invest_sources = self.game.invest_sources()
        invest_destinations = set()
        if self.selected_invest_source and self.selected_invest_source in invest_sources:
            invest_destinations = {item["destination"] for item in invest_sources[self.selected_invest_source]}

        for edge in self.map_data["edges"]:
            start = nodes_by_name[edge["from"]]
            end = nodes_by_name[edge["to"]]
            p1 = self.world_to_screen(start["x"], start["y"], map_rect)
            p2 = self.world_to_screen(end["x"], end["y"], map_rect)
            owner = self.game.get_edge(edge["from"], edge["to"]).get("owner")
            color = (100, 116, 139)
            width = 2
            if owner == "Player 1":
                color = PINK
                width = 4
            elif owner == "Player 2":
                color = BLUE
                width = 4
            elif edge["type"] == "police":
                color = RED
                width = 3
            elif edge["type"] == "toll_border":
                color = AMBER
                width = 3
            pygame.draw.line(self.screen, color, p1, p2, width)
            if edge["type"] in {"police", "toll_border"}:
                self.draw_route_markers(p1, p2, edge["type"])

        for province, position in self.map_data.get("province_labels", {}).items():
            sx, sy = self.world_to_screen(position["x"], position["y"], map_rect)
            text = self.font_heading.render(province, True, PROVINCE_TEXT_COLORS.get(province, MUTED))
            self.screen.blit(text, text.get_rect(center=(sx, sy)))

        for node in self.map_data["nodes"]:
            name = node["name"]
            sx, sy = self.world_to_screen(node["x"], node["y"], map_rect)
            radius = self.node_radius(node, map_rect)
            fill = (17, 24, 39)
            outline = (203, 213, 225)
            width = 2

            if name == self.game.current_player["position"]:
                fill = (29, 78, 216)
                outline = (147, 197, 253)
                width = 3
            elif self.game.phase == "move" and name in accessible:
                fill = (19, 47, 76)
                outline = CYAN
                width = 3
            elif self.game.phase == "invest" and name in invest_sources:
                fill = (41, 31, 8)
                outline = GOLD
                width = 4
            elif self.game.phase == "invest" and name in invest_destinations:
                fill = (44, 32, 12)
                outline = AMBER
                width = 4
            elif name in self.game.claimed_nodes:
                fill = (23, 32, 51)
                outline = (100, 116, 139)

            pygame.draw.circle(self.screen, fill, (sx, sy), radius)
            pygame.draw.circle(self.screen, outline, (sx, sy), radius, width)

            self.draw_node_label(node, sx, sy)

        offsets = [(-10, -10), (10, 10)]
        for index, player in enumerate(self.game.players):
            node = nodes_by_name[player["position"]]
            sx, sy = self.world_to_screen(node["x"], node["y"], map_rect)
            ox, oy = offsets[index]
            marker_color = PINK if player["name"] == "Player 1" else BLUE
            pygame.draw.circle(self.screen, marker_color, (sx + ox, sy + oy), 7)
            pygame.draw.circle(self.screen, (253, 230, 138), (sx + ox, sy + oy), 7, 2)

        self.draw_investment_labels(map_rect, invest_sources)
        if self.hover_node:
            self.draw_tooltip(map_rect, self.hover_node)

    def draw_route_markers(self, start: Tuple[int, int], end: Tuple[int, int], edge_type: str) -> None:
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = max(1, int((dx * dx + dy * dy) ** 0.5))
        steps = max(2, length // 28)
        color = RED if edge_type == "police" else AMBER
        for index in range(1, steps):
            t = index / steps
            x = int(start[0] + dx * t)
            y = int(start[1] + dy * t)
            pygame.draw.circle(self.screen, color, (x, y), 2)

    def draw_node_label(self, node: Dict, sx: int, sy: int) -> None:
        label = f"{display_node_label(node['name'])} | R{node['pts']}"
        surface = self.font_tiny.render(label.replace("\n", " "), True, TEXT if node["type"] == "city" else (219, 234, 254))
        rect = surface.get_rect(center=(sx, sy - 24))
        bg = pygame.Rect(rect.x - 5, rect.y - 2, rect.width + 10, rect.height + 4)
        pygame.draw.rect(self.screen, (6, 10, 18), bg, border_radius=8)
        self.screen.blit(surface, rect)

    def draw_investment_labels(self, map_rect: pygame.Rect, grouped: Dict[str, List[Dict]]) -> None:
        if self.game.phase != "invest" or not grouped:
            return
        if self.selected_invest_source not in grouped:
            return
        source = self.selected_invest_source
        nodes_by_name = {node["name"]: node for node in self.map_data["nodes"]}
        start = nodes_by_name[source]
        start_point = self.world_to_screen(start["x"], start["y"], map_rect)
        for option in grouped[source]:
            destination = nodes_by_name[option["destination"]]
            end_point = self.world_to_screen(destination["x"], destination["y"], map_rect)
            pygame.draw.line(self.screen, GOLD, start_point, end_point, 5)
            mid_x = (start_point[0] + end_point[0]) // 2
            mid_y = (start_point[1] + end_point[1]) // 2
            label = self.font_small.render(f"R{option['cost']}", True, TEXT)
            box = label.get_rect(center=(mid_x, mid_y))
            box.inflate_ip(16, 8)
            pygame.draw.rect(self.screen, (74, 46, 0), box, border_radius=10)
            pygame.draw.rect(self.screen, GOLD, box, 2, border_radius=10)
            self.screen.blit(label, label.get_rect(center=box.center))

    def draw_panel(self, panel_rect: pygame.Rect) -> None:
        x = panel_rect.x + 18
        y = 18
        width = panel_rect.width - 36

        title = self.font_title.render("Siyaya!", True, TEXT)
        self.screen.blit(title, (x, y))
        y += 38

        y = self.draw_card(
            pygame.Rect(x, y, width, 98),
            "Turn Summary",
            [
                f"Turn {self.game.turn_number} | {self.game.current_player['name']} | {self.game.current_player['vehicle']}",
                self.phase_text(),
                self.hint_text(),
            ],
        )
        y += 12

        for player in self.game.players:
            active = player["name"] == self.game.current_player["name"] and not self.game.winner
            y = self.draw_player_card(pygame.Rect(x, y, width, 86), player, active)
            y += 10

        y = self.draw_card(
            pygame.Rect(x, y, width, 76),
            "Latest Transaction",
            [self.game.last_transaction],
        )
        y += 12

        new_match_rect = pygame.Rect(x, y, width, 42)
        self.add_button(new_match_rect, "New Match", self.start_new_match, fill=(37, 99, 235))
        y += 54

        if self.game.phase == "invest":
            y = self.draw_card(
                pygame.Rect(x, y, width, 125),
                "Investment",
                [
                    "1. Click a glowing source node.",
                    "2. Click a highlighted destination to buy that road.",
                    "3. Use Skip if you do not want to invest.",
                ],
            )
            y += 12
            skip_rect = pygame.Rect(x, y, width, 42)
            self.add_button(skip_rect, "Skip Investment", self.skip_investment, fill=(31, 41, 55))
            y += 54
        elif self.game.pending_owner_fee:
            y = self.draw_card(
                pygame.Rect(x, y, width, 88),
                "Owned Road",
                ["Choose whether to pay the access fee for the selected route."],
            )
            y += 12
        elif self.game.pending_police:
            y = self.draw_card(
                pygame.Rect(x, y, width, 88),
                "Police Stop",
                ["Choose whether to bribe the police or accept losing the next turn."],
            )
            y += 12

        y = self.draw_legend(pygame.Rect(x, y, width, 122))
        y += 12

        footer = self.font_tiny.render("N = new match | ESC = quit", True, MUTED)
        self.screen.blit(footer, (x, panel_rect.bottom - 22))

    def draw_card(self, rect: pygame.Rect, heading: str, lines: List[str]) -> int:
        pygame.draw.rect(self.screen, CARD_BG, rect, border_radius=16)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=16)
        heading_surface = self.font_heading.render(heading, True, TEXT)
        self.screen.blit(heading_surface, (rect.x + 14, rect.y + 12))
        y = rect.y + 40
        for line in lines:
            color = MUTED if line == lines[-1] and len(lines) > 1 else TEXT
            body = self.font_body.render(line, True, color)
            self.screen.blit(body, (rect.x + 14, y))
            y += 22
        return rect.bottom

    def draw_player_card(self, rect: pygame.Rect, player: Dict, active: bool) -> int:
        fill = (36, 52, 77) if active else CARD_BG
        accent = PINK if player["name"] == "Player 1" else BLUE
        pygame.draw.rect(self.screen, fill, rect, border_radius=16)
        pygame.draw.rect(self.screen, accent if active else BORDER, rect, 2 if active else 1, border_radius=16)
        title = self.font_heading.render(f"{player['name']} | {player['vehicle']}", True, TEXT)
        body = self.font_body.render(
            f"{player['position']} | R{player['points']} | skip {player['skip_turn']}",
            True,
            TEXT,
        )
        progress = max(0.0, min(1.0, player["points"] / TARGET_POINTS))
        self.screen.blit(title, (rect.x + 14, rect.y + 12))
        self.screen.blit(body, (rect.x + 14, rect.y + 42))
        bar_rect = pygame.Rect(rect.x + 14, rect.bottom - 18, rect.width - 28, 8)
        pygame.draw.rect(self.screen, (15, 23, 42), bar_rect, border_radius=4)
        fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.width * progress), bar_rect.height)
        pygame.draw.rect(self.screen, accent, fill_rect, border_radius=4)
        return rect.bottom

    def draw_legend(self, rect: pygame.Rect) -> int:
        pygame.draw.rect(self.screen, CARD_BG, rect, border_radius=16)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=16)
        heading = self.font_heading.render("Legend", True, TEXT)
        self.screen.blit(heading, (rect.x + 14, rect.y + 12))

        row_y = rect.y + 44
        self.draw_legend_node(rect.x + 24, row_y + 6, (19, 47, 76), CYAN, 3)
        self.screen.blit(self.font_body.render("Blue glow = valid move", True, TEXT), (rect.x + 44, row_y))

        row_y += 28
        pygame.draw.line(self.screen, AMBER, (rect.x + 16, row_y + 8), (rect.x + 34, row_y + 8), 3)
        for dot_x in range(rect.x + 18, rect.x + 33, 6):
            pygame.draw.circle(self.screen, AMBER, (dot_x, row_y + 8), 2)
        self.screen.blit(self.font_body.render("Amber road = toll route", True, TEXT), (rect.x + 44, row_y))

        row_y += 28
        pygame.draw.line(self.screen, RED, (rect.x + 16, row_y + 8), (rect.x + 34, row_y + 8), 3)
        for dot_x in range(rect.x + 18, rect.x + 33, 6):
            pygame.draw.circle(self.screen, RED, (dot_x, row_y + 8), 2)
        self.screen.blit(self.font_body.render("Red road = police route", True, TEXT), (rect.x + 44, row_y))

        return rect.bottom

    def draw_legend_node(
        self,
        x: int,
        y: int,
        fill: Tuple[int, int, int],
        outline: Tuple[int, int, int],
        width: int,
    ) -> None:
        pygame.draw.circle(self.screen, fill, (x, y), 10)
        pygame.draw.circle(self.screen, outline, (x, y), 10, width)

    def add_button(self, rect: pygame.Rect, label: str, action: Callable[[], None], fill: Tuple[int, int, int]) -> None:
        self.buttons.append(Button(rect, label, action, fill))
        pygame.draw.rect(self.screen, fill, rect, border_radius=12)
        pygame.draw.rect(self.screen, BORDER, rect, 1, border_radius=12)
        text = self.font_body.render(label, True, TEXT)
        self.screen.blit(text, text.get_rect(center=rect.center))

    def phase_text(self) -> str:
        if self.game.phase == "move":
            return "Move phase"
        if self.game.phase == "invest":
            return "Investment phase"
        return "Game complete"

    def hint_text(self) -> str:
        if self.game.pending_owner_fee:
            return "Resolve the owner fee prompt."
        if self.game.pending_police:
            return "Resolve the police decision."
        if self.game.phase == "move":
            return "Click a glowing neighboring node to move."
        if self.game.phase == "invest":
            if self.game.all_investments():
                return "Click a source node, then click a highlighted destination."
            if not self.game.can_offer_investment():
                return "No buys this turn: investment is available every second personal turn."
            return "No eligible investment routes from untraveled source nodes."
        if self.game.winner:
            return f"{self.game.winner} wins. Start a new match to play again."
        return ""

    def draw_owner_fee_modal(self) -> None:
        pending = self.game.pending_owner_fee
        message = [
            f"{pending['owner']} owns {pending['from']} -> {pending['to']}.",
            "Pay R15 to use this road, or cancel and choose another route.",
        ]
        rect = self.draw_modal("Owned Road", message)
        button_y = rect.bottom - 62
        gap = 14
        width = (rect.width - 56 - gap) // 2
        pay_rect = pygame.Rect(rect.x + 20, button_y, width, 42)
        cancel_rect = pygame.Rect(pay_rect.right + gap, button_y, width, 42)
        self.add_button(pay_rect, "Pay R15", lambda: self.resolve_owner_fee(True), fill=(37, 99, 235))
        self.add_button(cancel_rect, "Cancel", lambda: self.resolve_owner_fee(False), fill=(31, 41, 55))

    def draw_police_modal(self) -> None:
        message = [
            "Police encountered on this route.",
            "Bribe for R15 or refuse and lose your next turn.",
        ]
        rect = self.draw_modal("Police Stop", message)
        button_y = rect.bottom - 62
        gap = 14
        width = (rect.width - 56 - gap) // 2
        bribe_rect = pygame.Rect(rect.x + 20, button_y, width, 42)
        refuse_rect = pygame.Rect(bribe_rect.right + gap, button_y, width, 42)
        self.add_button(bribe_rect, "Bribe R15", lambda: self.resolve_police("bribe"), fill=(37, 99, 235))
        self.add_button(refuse_rect, "Refuse", lambda: self.resolve_police("refuse"), fill=(31, 41, 55))

    def draw_winner_modal(self) -> None:
        rect = self.draw_modal("Winner", [f"{self.game.winner} wins the match.", "Start a new match to play again."])
        new_rect = pygame.Rect(rect.x + 40, rect.bottom - 62, rect.width - 80, 42)
        self.add_button(new_rect, "New Match", self.start_new_match, fill=(37, 99, 235))

    def draw_modal(self, title: str, lines: List[str]) -> pygame.Rect:
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill(OVERLAY)
        self.screen.blit(overlay, (0, 0))
        width = min(520, self.screen.get_width() - 80)
        height = 210
        rect = pygame.Rect(0, 0, width, height)
        rect.center = self.screen.get_rect().center
        pygame.draw.rect(self.screen, PANEL_BG, rect, border_radius=18)
        pygame.draw.rect(self.screen, BORDER, rect, 2, border_radius=18)
        title_surface = self.font_title.render(title, True, TEXT)
        self.screen.blit(title_surface, (rect.x + 20, rect.y + 18))
        y = rect.y + 68
        for line in lines:
            body = self.font_body.render(line, True, TEXT)
            self.screen.blit(body, (rect.x + 20, y))
            y += 24
        return rect

    def draw_tooltip(self, map_rect: pygame.Rect, node_name: str) -> None:
        node = next(node for node in self.map_data["nodes"] if node["name"] == node_name)
        sx, sy = self.world_to_screen(node["x"], node["y"], map_rect)
        label = f"{node['name']} | {node['province']} | R{node['pts']}"
        surface = self.font_small.render(label, True, TEXT)
        rect = surface.get_rect()
        rect.x = min(map_rect.right - rect.width - 16, sx + 16)
        rect.y = max(map_rect.top + 16, sy - 34)
        bg = pygame.Rect(rect.x - 8, rect.y - 6, rect.width + 16, rect.height + 12)
        pygame.draw.rect(self.screen, (11, 18, 32), bg, border_radius=10)
        pygame.draw.rect(self.screen, BORDER, bg, 1, border_radius=10)
        self.screen.blit(surface, rect)


def main() -> None:
    try:
        app = SiyayaPygameApp()
        app.run()
    except Exception as error:
        print(f"Failed to start Pygame UI: {error}", flush=True)
        raise


if __name__ == "__main__":
    sys.exit(main())

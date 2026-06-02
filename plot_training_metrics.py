from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


BASE_DIR = Path(__file__).resolve().parent
METRICS_DIR = BASE_DIR / "training_metrics"
CHARTS_DIR = METRICS_DIR / "charts"
TRAINING_CSV = METRICS_DIR / "training_progress.csv"
EVAL_CSV = METRICS_DIR / "evaluation_history.csv"


def load_csv_rows(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def to_float(row: dict, key: str, default: float = 0.0) -> float:
    value = row.get(key, "")
    if value in ("", None):
        return default
    try:
        return float(value)
    except ValueError:
        return default


def svg_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def make_line_chart(
    title: str,
    x_label: str,
    y_label: str,
    series: Sequence[Tuple[str, Sequence[Tuple[float, float]], str]],
    output_path: Path,
    width: int = 980,
    height: int = 520,
) -> None:
    margin_left = 78
    margin_right = 24
    margin_top = 62
    margin_bottom = 72
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    all_points = [point for _name, points, _color in series for point in points]
    if not all_points:
        return

    min_x = min(point[0] for point in all_points)
    max_x = max(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_y = max(point[1] for point in all_points)

    if min_x == max_x:
        max_x += 1.0
    if min_y == max_y:
        padding = 1.0 if min_y == 0 else abs(min_y) * 0.1
        min_y -= padding
        max_y += padding
    else:
        padding = (max_y - min_y) * 0.08
        min_y -= padding
        max_y += padding

    def x_to_px(x: float) -> float:
        return margin_left + ((x - min_x) / (max_x - min_x)) * plot_width

    def y_to_px(y: float) -> float:
        return margin_top + (1.0 - ((y - min_y) / (max_y - min_y))) * plot_height

    horizontal_ticks = 5
    vertical_ticks = 5
    svg_lines: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0c1220"/>',
        f'<text x="{margin_left}" y="30" fill="#f5f7fb" font-size="24" font-family="Helvetica, Arial, sans-serif" font-weight="700">{svg_escape(title)}</text>',
    ]

    for tick in range(horizontal_ticks + 1):
        y_value = min_y + ((max_y - min_y) * tick / horizontal_ticks)
        y = y_to_px(y_value)
        svg_lines.append(
            f'<line x1="{margin_left}" y1="{y:.2f}" x2="{width - margin_right}" y2="{y:.2f}" stroke="#24324a" stroke-width="1"/>'
        )
        svg_lines.append(
            f'<text x="{margin_left - 12}" y="{y + 4:.2f}" fill="#c7d4ea" font-size="12" text-anchor="end" font-family="Helvetica, Arial, sans-serif">{y_value:.1f}</text>'
        )

    for tick in range(vertical_ticks + 1):
        x_value = min_x + ((max_x - min_x) * tick / vertical_ticks)
        x = x_to_px(x_value)
        svg_lines.append(
            f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{height - margin_bottom}" stroke="#24324a" stroke-width="1"/>'
        )
        svg_lines.append(
            f'<text x="{x:.2f}" y="{height - margin_bottom + 24}" fill="#c7d4ea" font-size="12" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{x_value:.0f}</text>'
        )

    svg_lines.append(
        f'<line x1="{margin_left}" y1="{height - margin_bottom}" x2="{width - margin_right}" y2="{height - margin_bottom}" stroke="#8aa4c8" stroke-width="2"/>'
    )
    svg_lines.append(
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{height - margin_bottom}" stroke="#8aa4c8" stroke-width="2"/>'
    )

    legend_x = width - margin_right - 220
    legend_y = 24
    for index, (name, points, color) in enumerate(series):
        if not points:
            continue
        line_y = legend_y + index * 24
        svg_lines.append(
            f'<line x1="{legend_x}" y1="{line_y}" x2="{legend_x + 24}" y2="{line_y}" stroke="{color}" stroke-width="4" stroke-linecap="round"/>'
        )
        svg_lines.append(
            f'<text x="{legend_x + 32}" y="{line_y + 4}" fill="#f5f7fb" font-size="13" font-family="Helvetica, Arial, sans-serif">{svg_escape(name)}</text>'
        )

    for name, points, color in series:
        if not points:
            continue
        point_string = " ".join(f"{x_to_px(x):.2f},{y_to_px(y):.2f}" for x, y in points)
        svg_lines.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" points="{point_string}"/>'
        )
        for x, y in points:
            px = x_to_px(x)
            py = y_to_px(y)
            svg_lines.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="3.5" fill="{color}"/>')

    svg_lines.append(
        f'<text x="{margin_left + plot_width / 2:.2f}" y="{height - 18}" fill="#d7e3f5" font-size="14" text-anchor="middle" font-family="Helvetica, Arial, sans-serif">{svg_escape(x_label)}</text>'
    )
    svg_lines.append(
        f'<text x="22" y="{margin_top + plot_height / 2:.2f}" fill="#d7e3f5" font-size="14" text-anchor="middle" transform="rotate(-90 22 {margin_top + plot_height / 2:.2f})" font-family="Helvetica, Arial, sans-serif">{svg_escape(y_label)}</text>'
    )
    svg_lines.append("</svg>")

    output_path.write_text("\n".join(svg_lines), encoding="utf-8")


def write_dashboard(chart_files: Iterable[Tuple[str, str]], output_path: Path) -> None:
    cards = []
    for title, filename in chart_files:
        cards.append(
            f"""
            <section class="card">
              <h2>{svg_escape(title)}</h2>
              <img src="{svg_escape(filename)}" alt="{svg_escape(title)}" />
            </section>
            """
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Siyaya Training Dashboard</title>
  <style>
    body {{
      margin: 0;
      font-family: Helvetica, Arial, sans-serif;
      background: #08101b;
      color: #f2f6fc;
    }}
    header {{
      padding: 28px 32px 8px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 32px;
    }}
    p {{
      margin: 0;
      color: #c3d2e8;
    }}
    main {{
      padding: 24px 24px 40px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
      gap: 20px;
    }}
    .card {{
      background: #101a2b;
      border: 1px solid #1f2d46;
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
    }}
    .card h2 {{
      margin: 0 0 12px;
      font-size: 18px;
    }}
    .card img {{
      width: 100%;
      height: auto;
      border-radius: 12px;
      display: block;
      background: #0c1220;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Siyaya Training Dashboard</h1>
    <p>Charts generated from training_progress.csv and evaluation_history.csv</p>
  </header>
  <main>
    {''.join(cards)}
  </main>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def build_charts() -> List[Tuple[str, str]]:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    training_rows = load_csv_rows(TRAINING_CSV)
    eval_rows = load_csv_rows(EVAL_CSV)
    if not training_rows and not eval_rows:
        raise FileNotFoundError("No training CSV data found in training_metrics.")

    chart_files: List[Tuple[str, str]] = []

    if training_rows:
        reward_points = [(to_float(row, "episode"), to_float(row, "episode_reward")) for row in training_rows]
        epsilon_points = [(to_float(row, "episode"), to_float(row, "epsilon")) for row in training_rows]
        q_size_points = [(to_float(row, "episode"), to_float(row, "q_table_size")) for row in training_rows]

        make_line_chart(
            "Episode Reward Over Time",
            "Episode",
            "Episode Reward",
            [("Episode reward", reward_points, "#5fc8ff")],
            CHARTS_DIR / "episode_reward.svg",
        )
        chart_files.append(("Episode Reward Over Time", "episode_reward.svg"))

        make_line_chart(
            "Exploration Decay (Epsilon)",
            "Episode",
            "Epsilon",
            [("Epsilon", epsilon_points, "#ffd166")],
            CHARTS_DIR / "epsilon_decay.svg",
        )
        chart_files.append(("Exploration Decay (Epsilon)", "epsilon_decay.svg"))

        make_line_chart(
            "Q-Table Growth",
            "Episode",
            "Q-Table Entries",
            [("Q-table size", q_size_points, "#8ce99a")],
            CHARTS_DIR / "q_table_size.svg",
        )
        chart_files.append(("Q-Table Growth", "q_table_size.svg"))

    if eval_rows:
        episode_points = [to_float(row, "episode") for row in eval_rows]
        random_wins = list(zip(episode_points, [to_float(row, "random_agent_wins") for row in eval_rows]))
        random_draws = list(zip(episode_points, [to_float(row, "random_draws") for row in eval_rows]))
        heur_wins = list(zip(episode_points, [to_float(row, "heur_agent_wins") for row in eval_rows]))
        heur_draws = list(zip(episode_points, [to_float(row, "heur_draws") for row in eval_rows]))
        self_wins = list(zip(episode_points, [to_float(row, "self_agent_wins") for row in eval_rows]))
        random_balance = list(zip(episode_points, [to_float(row, "random_avg_agent_balance") for row in eval_rows]))
        heur_balance = list(zip(episode_points, [to_float(row, "heur_avg_agent_balance") for row in eval_rows]))

        make_line_chart(
            "Evaluation Wins by Opponent Type",
            "Episode",
            "Wins Per Evaluation Checkpoint",
            [
                ("Vs random wins", random_wins, "#4cc9f0"),
                ("Vs heuristic wins", heur_wins, "#f72585"),
                ("Self-play wins", self_wins, "#90be6d"),
            ],
            CHARTS_DIR / "evaluation_wins.svg",
        )
        chart_files.append(("Evaluation Wins by Opponent Type", "evaluation_wins.svg"))

        make_line_chart(
            "Evaluation Draws by Opponent Type",
            "Episode",
            "Draws Per Evaluation Checkpoint",
            [
                ("Vs random draws", random_draws, "#4cc9f0"),
                ("Vs heuristic draws", heur_draws, "#f72585"),
            ],
            CHARTS_DIR / "evaluation_draws.svg",
        )
        chart_files.append(("Evaluation Draws by Opponent Type", "evaluation_draws.svg"))

        make_line_chart(
            "Random vs Heuristic Comparison",
            "Episode",
            "Agent Balance",
            [
                ("Vs random avg balance", random_balance, "#4cc9f0"),
                ("Vs heuristic avg balance", heur_balance, "#f72585"),
            ],
            CHARTS_DIR / "random_vs_heuristic_comparison.svg",
        )
        chart_files.append(("Random vs Heuristic Comparison", "random_vs_heuristic_comparison.svg"))

    write_dashboard(chart_files, CHARTS_DIR / "index.html")
    return chart_files


def main() -> None:
    chart_files = build_charts()
    print("Generated charts:")
    for title, filename in chart_files:
        print(f"- {title}: {CHARTS_DIR / filename}")
    print(f"\nDashboard: {CHARTS_DIR / 'index.html'}")


if __name__ == "__main__":
    main()

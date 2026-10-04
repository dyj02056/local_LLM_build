"""Colab 학습 로그(Step / Training Loss 표)를 README용 Loss 그래프로 그린다.

사용법:
    python scripts/plot_loss.py loss_table/loss_table.txt --out docs/loss_curve.png
필요 패키지: pip install -e ".[plot]"
"""

import argparse
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SURFACE, INK, INK_2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
RAW, SMOOTH = "#86b6ef", "#2a78d6"  # 같은 파랑 계열: 원본은 연하게, 이동평균은 진하게


def read_log(path: str) -> tuple[list[int], list[float]]:
    """'숫자 숫자' 꼴의 줄만 읽는다 (헤더·잡문구는 무시)."""
    steps, losses = [], []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*(\d+)\s+([0-9.]+(?:e-?\d+)?)\s*$", line)
        if m:
            steps.append(int(m.group(1)))
            losses.append(float(m.group(2)))
    if not steps:
        raise SystemExit(f"{path} 에서 Step/Loss 숫자를 찾지 못했습니다.")
    return steps, losses


def moving_avg(xs: list[float], k: int) -> list[float]:
    return [sum(xs[max(0, i - k + 1): i + 1]) / len(xs[max(0, i - k + 1): i + 1]) for i in range(len(xs))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--out", default="docs/loss_curve.png")
    ap.add_argument("--window", type=int, default=10, help="이동평균 구간 (로그 줄 수)")
    args = ap.parse_args()

    steps, losses = read_log(args.log)
    smooth = moving_avg(losses, args.window)

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    ax.plot(steps, losses, color=RAW, linewidth=1.2)
    ax.plot(steps, smooth, color=SMOOTH, linewidth=2)

    # 직접 라벨 (범례 대신 선 끝에)
    ax.annotate("per-step loss", (steps[-1], losses[-1]), xytext=(6, 10), textcoords="offset points",
                color=INK_2, fontsize=9, va="center")
    ax.annotate(f"moving avg ({args.window * (steps[1] - steps[0])} steps): {smooth[-1]:.3f}",
                (steps[-1], smooth[-1]), xytext=(6, -8), textcoords="offset points", color=INK, fontsize=9,
                va="center")
    # 시작 값
    ax.plot([steps[0]], [losses[0]], "o", color=SMOOTH, markersize=5)
    ax.annotate(f"{losses[0]:.3f}", (steps[0], losses[0]), xytext=(8, 0), textcoords="offset points",
                color=INK, fontsize=9, va="center")

    ax.set_title("QLoRA fine-tuning loss — Qwen2.5-Coder-3B on Spider (1 epoch)",
                 color=INK, fontsize=11, loc="left", pad=12)
    ax.set_xlabel("training step", color=INK_2, fontsize=9)
    ax.set_ylabel("training loss", color=INK_2, fontsize=9)
    ax.set_ylim(0, max(losses) * 1.1)
    ax.set_xlim(0, steps[-1] * 1.3)  # 오른쪽 라벨 자리
    ax.set_xticks([t for t in ax.get_xticks() if 0 <= t <= steps[-1]])
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.8)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#d4d3cd")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, facecolor=SURFACE)
    print(f"steps {steps[0]}~{steps[-1]} ({len(steps)}개), loss {losses[0]:.3f} -> {losses[-1]:.3f}, "
          f"min {min(losses):.3f}, 마지막 {args.window}개 평균 {smooth[-1]:.3f}")
    print(f"그래프 -> {out}")


if __name__ == "__main__":
    main()

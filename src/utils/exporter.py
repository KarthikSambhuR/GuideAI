"""Session tutorial guide recorder and Markdown exporter."""

import json
import time
from pathlib import Path


class GuideExporter:
    """Serializes completed multi-step tutorial sessions into Markdown and JSON files."""

    def __init__(self, export_dir: str | Path = "exports") -> None:
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_session(self, question: str, steps_history: list[dict], final_answer: str = "") -> Path:
        """Export a completed guide session to a Markdown document.

        Returns
        -------
        Path
            Path to the generated Markdown export file.
        """
        timestamp = int(time.time())
        filename = f"guide_{timestamp}.md"
        filepath = self.export_dir / filename

        lines = [
            f"# GuideAI Step-by-Step Tutorial: {question}\n",
            f"*Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}*\n",
            "## Completed Steps\n",
        ]

        if not steps_history:
            lines.append("1. Answer provided: " + (final_answer or "No steps recorded."))
        else:
            for idx, step in enumerate(steps_history, start=1):
                label = step.get("label") or f"target at ({step.get('x')}, {step.get('y')})"
                lines.append(f"{idx}. Click **{label}**")

        if final_answer:
            lines.append(f"\n## Guidance Summary\n{final_answer}\n")

        filepath.write_text("\n".join(lines), encoding="utf-8")
        print(f"GuideAI exporter: session exported to {filepath}")
        return filepath

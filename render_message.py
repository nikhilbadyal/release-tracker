# render_message.py

from typing import Literal

from watcher.base import ReleaseInfo

RenderFormat = Literal["markdown", "html", "text"]


def render_message(repo_id: str, release: ReleaseInfo, render_format: RenderFormat = "text") -> str:
    if render_format == "markdown":
        lines = [
            f"🚀 **New Release** for `{repo_id}`: `{release.tag}`",
            "**Assets:**",
        ] + [f"- [{a.name}]({a.download_url})" for a in release.assets]
        return "\n".join(lines)

    if render_format == "html":
        lines = [
            f"<p>🚀 <strong>New Release</strong> for <code>{repo_id}</code>: <code>{release.tag}</code></p>",
            "<p><strong>Assets:</strong></p><ul>",
        ] + [f"<li><a href='{a.download_url}'>{a.name}</a></li>" for a in release.assets]
        lines.append("</ul>")
        return "\n".join(lines)

    if render_format == "text":
        lines = [
            f"New Release for {repo_id}: {release.tag}",
            "Assets:",
        ] + [f"- {a.name}: {a.download_url}" for a in release.assets]
        return "\n".join(lines)

    msg = f"Unsupported format: {render_format}"
    raise ValueError(msg)

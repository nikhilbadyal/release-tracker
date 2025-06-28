# render_message.py

from typing import Literal

from watcher.base import ReleaseInfo

RenderFormat = Literal["markdown", "html", "text"]


def render_message(repo_id: str, release: ReleaseInfo, render_format: RenderFormat = "text") -> str:
    footer_md: str = "\n\n---\nPowered by [release-tracker](https://github.com/nikhilbadyal/release-tracker)"
    footer_html: str = (
        "<hr><p>Powered by <a href='https://github.com/nikhilbadyal/release-tracker'>release-tracker</a></p>"
    )
    footer_text: str = "\n\n---\nPowered by: https://github.com/nikhilbadyal/release-tracker"

    if render_format == "markdown":
        # Check if ReleaseInfo has a source URL
        if hasattr(release, "source_url") and release.source_url:
            repo_display = f"[{repo_id}]({release.source_url})"
        else:
            repo_display = f"`{repo_id}`"

        lines = [
            f"🚀 **New Release** for {repo_display}: `{release.tag}`",
            "**Assets:**",
        ] + [f"- [{a.name}]({a.download_url})" for a in release.assets]
        lines.append(footer_md)
        return "\n".join(lines)

    if render_format == "html":
        # Check if ReleaseInfo has a source URL
        if hasattr(release, "source_url") and release.source_url:
            repo_display = f"<a href='{release.source_url}'>{repo_id}</a>"
        else:
            repo_display = f"<code>{repo_id}</code>"

        lines = [
            f"<p>🚀 <strong>New Release</strong> for {repo_display}: <code>{release.tag}</code></p>",
            "<p><strong>Assets:</strong></p><ul>",
        ] + [f"<li><a href='{a.download_url}'>{a.name}</a></li>" for a in release.assets]
        lines.append("</ul>")
        lines.append(footer_html)
        return "\n".join(lines)

    if render_format == "text":
        # Check if ReleaseInfo has a source URL
        if hasattr(release, "source_url") and release.source_url:
            repo_display = f"{repo_id} ({release.source_url})"
        else:
            repo_display = repo_id

        lines = [
            f"New Release for {repo_display}: {release.tag}",
            "Assets:",
        ] + [f"- {a.name}: {a.download_url}" for a in release.assets]
        lines.append(footer_text)
        return "\n".join(lines)

    msg = f"Unsupported format: {render_format}"
    raise ValueError(msg)

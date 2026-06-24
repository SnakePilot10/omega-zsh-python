from pathlib import Path

from omega_zsh.core.apply import apply_config, build_config_context, render_config
from omega_zsh.core.context import SystemContext
from omega_zsh.core.state import AppState


def test_build_config_context_keeps_binary_tools_out_of_omz_plugins(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    context = SystemContext(home=home, env={})
    state = AppState(
        selected_plugins=["zsh-autosuggestions", "zoxide", "eza"],
        selected_header="none",
    )

    data = build_config_context(context, state)

    assert "zsh-autosuggestions" in data["plugins"]
    assert "zoxide" not in data["plugins"]
    assert "eza" not in data["plugins"]
    assert data["active_tools"] == ["zoxide", "eza"]
    assert "theme" not in data
    assert "omega_dir" not in data


def test_render_config_is_pure_and_does_not_write_zshrc(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    context = SystemContext(home=home, env={})
    state = AppState(selected_plugins=["git"], selected_header="none")

    content = render_config(context, state)

    assert "export ZSH" in content
    assert "plugins=(git )" in content
    assert not context.zshrc_path.exists()


def test_apply_config_orchestrates_theme_links_and_zshrc_write(tmp_path, monkeypatch):
    home = tmp_path / "home"
    omz = home / ".oh-my-zsh"
    (omz / "custom" / "themes").mkdir(parents=True)
    (omz / "oh-my-zsh.sh").write_text("# omz\n", encoding="utf-8")
    assets = tmp_path / "assets"
    templates = assets / "templates"
    themes = assets / "themes"
    templates.mkdir(parents=True)
    themes.mkdir()
    (themes / "omega-test.zsh-theme").write_text("PROMPT=test\n", encoding="utf-8")
    repo_templates = Path(__file__).parent.parent / "omega_zsh" / "assets" / "templates"
    (templates / ".zshrc.j2").write_text((repo_templates / ".zshrc.j2").read_text(encoding="utf-8"), encoding="utf-8")
    context = SystemContext(home=home, env={"ZSH": str(omz)})
    context.assets_dir = assets
    state = AppState(selected_plugins=["git"], selected_header="none")
    monkeypatch.setattr("omega_zsh.core.shell.which", lambda command: None)

    result = apply_config(context, state)

    assert result.ok
    assert context.zshrc_path.exists()
    assert (omz / "custom" / "themes" / "omega-test.zsh-theme").is_symlink()

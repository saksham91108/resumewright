# generator.py
from jinja2 import Environment, FileSystemLoader
import shutil
import os

AVAILABLE_TEMPLATES = {
    "1": {"name": "Template 1 — Ledger", "folder": "template1"},
    "2": {"name": "Template 2 — Terminal", "folder": "template2"},
    "3": {"name": "Template 3 — Signal", "folder": "template3"},
    "4": {"name": "Template 4 — Dynamic", "folder": "template4"},
}

def choose_template():
    """Ask the user to pick a template interactively."""
    print("\nChoose a portfolio template:")
    for key, tmpl in AVAILABLE_TEMPLATES.items():
        print(f"  {key}. {tmpl['name']}")

    choice = input("Enter choice (1-4): ").strip()
    while choice not in AVAILABLE_TEMPLATES:
        choice = input("Invalid choice. Enter 1, 2, 3, or 4: ").strip()

    return AVAILABLE_TEMPLATES[choice]["folder"]

def render_portfolio(data, template_folder, output_dir="output"):
    """Render the portfolio HTML using the chosen template."""
    os.makedirs(output_dir, exist_ok=True)

    template_dir = os.path.join("templates", template_folder)
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("portfolio_template.html")

    html_output = template.render(**data)

    output_path = os.path.join(output_dir, "portfolio.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_output)

    css_source = os.path.join(template_dir, "style.css")
    if os.path.exists(css_source):
        shutil.copy(css_source, os.path.join(output_dir, "style.css"))

    return output_path
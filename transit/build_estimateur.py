#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère `estimateur-embed.html` (MINIFIÉ, sans commentaires) à coller dans un
bloc « Embed / HTML » de Webstudio, à partir de :

  • estimateur.template.html  → la structure (HTML + CSS + JS), avec des
    marqueurs {{...}} là où vont les données ;
  • estimateur-data.json      → les DONNÉES (projets, prix de base, niveaux de
    complexité, options de l'étape 3, lien du bouton final, marge…).

Workflow :
  1. Éditez estimateur-data.json (c'est le seul fichier à modifier au quotidien).
  2. Lancez :  python3 build_estimateur.py
  3. Collez le contenu de estimateur-embed.html dans Webstudio.

La minification retire les commentaires et l'indentation pour tenir sous la
limite de caractères de Webstudio. Le CSS et le JS sont minifiés séparément du
balisage pour ne pas casser le script.
"""
import json
import os
import re
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "estimateur.template.html")
DATA = os.path.join(HERE, "estimateur-data.json")
OUTPUT = os.path.join(HERE, "estimateur-embed.html")


# --------------------------------------------------------------------------
#  Helpers de données
# --------------------------------------------------------------------------
def fr_money(n):
    """5000 -> '5 000 €' (espace comme séparateur de milliers)."""
    return format(int(round(n)), ",").replace(",", " ") + " €"


def esc(s):
    """Échappe le texte destiné au HTML (&, <, >, \")."""
    return _html.escape(str(s), quote=True)


def info_icon(text):
    """Petit « i » avec infobulle au survol — uniquement si `text` non vide."""
    if not text:
        return ""
    return (
        '<span class="est-info" tabindex="0">i'
        '<span class="est-tip">{}</span></span>'.format(esc(text))
    )


def build_cards(projects):
    """Construit les boutons de l'étape 1 (un par projet)."""
    out = []
    for p in projects:
        label = p.get("priceLabel") or ("À partir de " + fr_money(p["base"]))
        out.append(
            '<button type="button" class="est-card" '
            'data-base="{base}" data-project="{pid}">'
            '<span class="est-card-head">'
            '<span class="est-card-name">{title}</span>{info}</span>'
            '<span class="est-card-desc">{desc}</span>'
            '<span class="est-card-meta">{label}</span>'
            "</button>".format(
                base=int(p["base"]),
                pid=esc(p["id"]),
                title=esc(p["title"]),
                info=info_icon(p.get("info")),
                desc=esc(p["desc"]),
                label=esc(label),
            )
        )
    return "".join(out)


def build_config(projects):
    """Construit l'objet CONFIG (JS) = JSON compact indexé par data-project."""
    cfg = {}
    for p in projects:
        cfg[p["id"]] = {
            "complexity": p.get("complexity", []),
            "features": p.get("features", []),
        }
    # JSON compact : valide tel quel comme littéral objet JavaScript.
    return json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))


# --------------------------------------------------------------------------
#  Minification
# --------------------------------------------------------------------------
def minify_css(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)        # commentaires
    css = re.sub(r"\s+", " ", css)                          # runs d'espaces
    css = re.sub(r"\s*([{}:;,>])\s*", r"\1", css)           # autour des symboles
    css = css.replace(";}", "}")                            # ; superflu
    return css.strip()


def minify_js(js):
    # Retire les commentaires /* ... */ (aucun n'apparaît dans une chaîne ici).
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
    lines = []
    for line in js.split("\n"):
        # Commentaires // ... (le code n'utilise jamais « // » dans une chaîne).
        i = line.find("//")
        if i != -1:
            line = line[:i]
        line = line.strip()
        if line:
            lines.append(line)
    # On garde les sauts de ligne entre instructions (sûr vis-à-vis de l'ASI).
    return "\n".join(lines)


def minify_markup(markup):
    markup = re.sub(r"<!--.*?-->", "", markup, flags=re.S)  # commentaires HTML
    markup = re.sub(r">\s+<", "><", markup)                 # espaces entre balises
    markup = re.sub(r"\s+", " ", markup)                    # runs d'espaces
    return markup.strip()


# --------------------------------------------------------------------------
#  Build
# --------------------------------------------------------------------------
def main():
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    with open(TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()

    projects = data["projects"]
    cta = data.get("cta", {})

    # 1) Injection des données dans les marqueurs.
    tpl = tpl.replace("{{RANGE}}", json.dumps(data.get("range", 0.12)))
    tpl = tpl.replace("{{CONFIG}}", build_config(projects))
    tpl = tpl.replace("{{PROJECT_CARDS}}", build_cards(projects))
    tpl = tpl.replace("{{CTA_LABEL}}", esc(cta.get("label", "Nous contacter")))
    tpl = tpl.replace(
        "{{CTA_ACTION}}",
        esc(cta.get("action", "https://redirect-methode.jcalenge.workers.dev/")),
    )
    tpl = tpl.replace(
        "{{CTA_EMAIL_PLACEHOLDER}}",
        esc(cta.get("emailPlaceholder", "Votre email")),
    )

    # 2) On isole <style> et <script> pour les minifier à part (sinon le
    #    minifieur de balisage casserait le CSS/JS).
    m_style = re.search(r"<style>(.*?)</style>", tpl, re.S)
    m_script = re.search(r"<script>(.*?)</script>", tpl, re.S)
    css_min = minify_css(m_style.group(1))
    js_min = minify_js(m_script.group(1))

    tpl = re.sub(r"<style>.*?</style>", "@@STYLE@@", tpl, count=1, flags=re.S)
    tpl = re.sub(r"<script>.*?</script>", "@@SCRIPT@@", tpl, count=1, flags=re.S)

    # 3) Minification du balisage, puis réinjection du CSS/JS minifiés.
    out = minify_markup(tpl)
    out = out.replace("@@STYLE@@", "<style>" + css_min + "</style>")
    out = out.replace("@@SCRIPT@@", "<script>" + js_min + "</script>")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(out)

    print("✓ {} généré ({:,} caractères)".format(
        os.path.basename(OUTPUT), len(out)).replace(",", " "))


if __name__ == "__main__":
    main()

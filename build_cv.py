"""
CV build pipeline.

Reads:
  - cv_data.json    -> content (source of truth, edit this to update your CV)
  - config.json     -> style/layout (edit this to restyle without touching content)

Writes:
  - <output_filename from config>  (single-column, ATS-friendly PDF)

Usage:
    python build_cv.py [--data cv_data.json] [--config config.json] [--out out.pdf]
"""

import argparse
import json
from pathlib import Path

from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether,
)

PAGE_SIZES = {"A4": A4, "LETTER": LETTER}





# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

with open('input/secrets.json', encoding = "utf-8") as secretsFile:
    secrets = json.load(secretsFile)
    EMAIL = secrets['mail']
    PHONE = secrets['phone']
    LOCATION = secrets['location']


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_date_range(start: str, end: str, currently_working: bool) -> str:
    """Dates are already stored as MM/YYYY in cv_data.json."""
    end_label = "Present" if currently_working or not end else end
    return f"{start} - {end_label}"


# --------------------------------------------------------------------------
# Style building (derived entirely from config.json — no hardcoded values)
# --------------------------------------------------------------------------

def build_styles(cfg: dict) -> dict:
    fonts = cfg["fonts"]
    colors = cfg["colors"]
    spacing = cfg["spacing"]

    leading_factor = spacing["line_leading"]
    primary = HexColor(colors["primary_text"])
    secondary = HexColor(colors["secondary_text"])
    accent = HexColor(colors["accent"])

    def size(key):
        return fonts["sizes"][key]

    styles = {
        "name": ParagraphStyle(
            "name", fontName=fonts["family_bold"], fontSize=size("name"),
            leading=size("name") * leading_factor, textColor=primary,
            spaceAfter=1, alignment=TA_LEFT,
        ),
        "title": ParagraphStyle(
            "title", fontName=fonts["family"], fontSize=size("professional_title"),
            leading=size("professional_title") * leading_factor, textColor=accent,
            spaceAfter=3, alignment=TA_LEFT,
        ),
        "contact": ParagraphStyle(
            "contact", fontName=fonts["family"], fontSize=size("small"),
            leading=size("small") * leading_factor, textColor=secondary,
            spaceAfter=spacing["section_gap"],
        ),
        "section_heading": ParagraphStyle(
            "section_heading", fontName=fonts["family_bold"], fontSize=size("section_heading"),
            leading=size("section_heading") * leading_factor, textColor=accent,
            spaceBefore=spacing["section_gap"], spaceAfter=2, alignment=TA_LEFT,
        ),
        "job_title": ParagraphStyle(
            "job_title", fontName=fonts["family_bold"], fontSize=size("job_title"),
            leading=size("job_title") * leading_factor, textColor=primary,
        ),
        "job_meta": ParagraphStyle(
            "job_meta", fontName=fonts["family_italic"], fontSize=size("small"),
            leading=size("small") * leading_factor, textColor=secondary,
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "body", fontName=fonts["family"], fontSize=size("body"),
            leading=size("body") * leading_factor, textColor=primary,
            spaceAfter=1,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName=fonts["family"], fontSize=size("body"),
            leading=size("body") * leading_factor, textColor=primary,
            leftIndent=10, spaceAfter=1,
        ),
        "profile": ParagraphStyle(
            "profile", fontName=fonts["family"], fontSize=size("body"),
            leading=size("body") * leading_factor, textColor=primary,
            spaceAfter=spacing["section_gap"],
        ),
    }
    return styles


# --------------------------------------------------------------------------
# Section builders — each returns a list of flowables.
# Plain text only, single column, standard headings -> parses cleanly
# for both human readers and automated/ATS text extraction.
# --------------------------------------------------------------------------

def section_heading(text: str, cfg: dict, styles: dict):
    flow = [Paragraph(text, styles["section_heading"])]
    flow.append(HRFlowable(
        width="100%", thickness=cfg["spacing"]["rule_thickness_pt"],
        color=HexColor(cfg["colors"]["rule"]), spaceAfter=4, spaceBefore=0,
    ))
    return flow


def build_header(data: dict, cfg: dict, styles: dict):
    basics = data["basics"]
    basics['email'] = EMAIL
    basics['phone'] = PHONE
    basics['location'] = LOCATION

    flow = [
        Paragraph(basics["name"], styles["name"]),
        Paragraph(basics["professionalTitle"], styles["title"]),
        Paragraph(
            f'{basics["email"]}  |  {basics["phone"]}  |  {basics["location"]}',
            styles["contact"],
        ),
        Paragraph(basics["professionalProfile"], styles["profile"]),
    ]
    return flow


def build_experience(data: dict, cfg: dict, styles: dict):
    bullet_char = cfg["layout"]["bullet_char"]
    flow = section_heading(cfg["section_titles"]["experience"], cfg, styles)

    for job in data["experience"]:
        block = []
        date_range = format_date_range(
            job["startDate"], job["endDate"], job.get("currentlyWorking", False)
        )
        header_line = f'{job["position"]} — {job["company"]}'
        meta_line = f'{job["city"]}, {job["country"]}  |  {date_range}'

        block.append(Paragraph(header_line, styles["job_title"]))
        block.append(Paragraph(meta_line, styles["job_meta"]))

        if job.get("description"):
            block.append(Paragraph(job["description"], styles["body"]))

        for achievement in job.get("achievements", []):
            if achievement:
                block.append(Paragraph(f"{bullet_char} {achievement}", styles["bullet"]))

        if job.get("technologies"):
            tech_line = "Technologies: " + ", ".join(job["technologies"])
            block.append(Paragraph(tech_line, styles["job_meta"]))

        block.append(Spacer(1, cfg["spacing"]["item_gap"]))
        # Keep each job block from splitting awkwardly across a page break.
        flow.append(KeepTogether(block))

    return flow


def build_education(data: dict, cfg: dict, styles: dict):
    flow = section_heading(cfg["section_titles"]["education"], cfg, styles)
    for edu in data["education"]:
        line1 = f'{edu["degree"]}'
        line2 = f'{edu["institution"]} — {edu["city"]}, {edu["country"]}'
        flow.append(Paragraph(line1, styles["job_title"]))
        flow.append(Paragraph(line2, styles["job_meta"]))
    return flow


def build_skills(data: dict, cfg: dict, styles: dict):
    flow = section_heading(cfg["section_titles"]["skills"], cfg, styles)
    skills = data.get("skills") or data.get("Skills") or []
    flow.append(Paragraph(", ".join(skills), styles["body"]))
    return flow


def build_languages(data: dict, cfg: dict, styles: dict):
    flow = section_heading(cfg["section_titles"]["languages"], cfg, styles)
    langs = data.get("languages", {})
    line = ", ".join(f"{lang} ({level})" for lang, level in langs.items())
    flow.append(Paragraph(line, styles["body"]))
    return flow


SECTION_BUILDERS = {
    "basics": build_header,
    "experience": build_experience,
    "education": build_education,
    "skills": build_skills,
    "languages": build_languages,
}


# --------------------------------------------------------------------------
# Document assembly
# --------------------------------------------------------------------------

def substitute_metadata(cfg: dict, data: dict) -> dict:
    basics = data["basics"]
    raw = cfg["metadata"]
    return {
        "title": raw["title"].format(**basics),
        "author": raw["author"].format(**basics),
        "subject": raw["subject"].format(**basics),
        "keywords": ", ".join(raw.get("keywords", [])),
    }


def build_pdf(data: dict, cfg: dict, output_path: Path):
    page_size = PAGE_SIZES.get(cfg["page"]["size"].upper(), A4)
    m = cfg["page"]["margins_cm"]
    meta = substitute_metadata(cfg, data)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=page_size,
        topMargin=m["top"] * cm,
        bottomMargin=m["bottom"] * cm,
        leftMargin=m["left"] * cm,
        rightMargin=m["right"] * cm,
        title=meta["title"],
        author=meta["author"],
        subject=meta["subject"],
        # ReportLab has no direct 'keywords' kwarg on SimpleDocTemplate;
        # set it on the canvas via afterInit hook below instead.
    )

    styles = build_styles(cfg)

    story = []
    for section_name in cfg["sections_order"]:
        builder = SECTION_BUILDERS.get(section_name)
        if builder:
            story.extend(builder(data, cfg, styles))

    def _set_keywords(canvas, _doc):
        canvas.setTitle(meta["title"])
        canvas.setAuthor(meta["author"])
        canvas.setSubject(meta["subject"])
        canvas.setKeywords(meta["keywords"])

    doc.build(story, onFirstPage=_set_keywords, onLaterPages=_set_keywords)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():

    
    while True: 

        try:
            lang = int(input("""Language : 
            1: En
            2: Fr
            """))
        
            match lang:
                case 1:
                    default_file = "input/cv_data_en.json"
                    sufix_pdf = "_en"
                    break
                case 2:
                    default_file = "input/cv_data_fr.json"
                    sufix_pdf = "_fr"
                    break
                case _:
                    print("Non valid")
        except :
            print("Error, try again.")

    
    parser = argparse.ArgumentParser(description="Build a CV PDF from JSON data + config.")
    parser.add_argument("--data", default=default_file)
    parser.add_argument("--config", default="input/config.json")
    parser.add_argument("--out", default=None, help="Overrides output_filename in config.json")
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    data = load_json(base_dir / args.data)
    cfg = load_json(base_dir / args.config)

    output_name = args.out or cfg.get("output_filename", "cv.pdf")
    output_name = output_name.replace(".",f"{sufix_pdf}.")

    output_path = base_dir / "output" / output_name
    build_pdf(data, cfg, output_path)
    print(f"CV generated: {output_path}")


if __name__ == "__main__":
    main()



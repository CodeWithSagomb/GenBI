"""Generate RuwaGenBI_Kera_MLRoundtable.pptx using Kera's official
"ML Research Presentation Template" branding (colors, fonts, logo assets
extracted from ../../ML Research Presentation Template.pdf at the
GenerativeBI project root) and structure (Problem & Motivation / Approach &
Methodology / Results & Evaluation / Conclusions & Future Work / Questions
& Discussion).

Usage : python3 build_pptx_kera.py
Requires assets/kera_logo_full.png and assets/kera_icon.png (already
extracted and committed alongside this script).

Note on fonts: Montserrat and Calibri are set by name to match the Kera
brand exactly. Calibri ships with Microsoft Office. Montserrat does not
ship with Office by default, if it is not installed on the presenting
machine, PowerPoint will substitute a fallback font, install Montserrat
(Google Fonts, free) beforehand for full visual fidelity.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Exact colors extracted from the Kera template's vector shapes.
INDIGO = RGBColor(0x32, 0x31, 0xB1)        # section titles, title bg
LOGO_BLUE = RGBColor(0x2C, 0x59, 0xFA)     # kera icon/wordmark blue
MINT = RGBColor(0x86, 0xEA, 0xE9)          # decorative circle
NAVY = RGBColor(0x23, 0x08, 0x71)          # decorative circle
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)
GREY = RGBColor(0x88, 0x88, 0x88)

HEADING_FONT = "Montserrat"
BODY_FONT = "Calibri"
ITALIC_FONT = "Arial"

LOGO_ICON = "assets/kera_icon.png"
LOGO_FULL = "assets/kera_logo_full.png"

PRESENTER = "Christ Sagombaye"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]

slide_num = 0  # running counter for the bottom-right page number


def add_slide():
    return prs.slides.add_slide(BLANK)


def add_textbox(slide, left, top, width, height, anchor=None):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    if anchor:
        tf.vertical_anchor = anchor
    return tf


def run(paragraph, text, size, color, bold=False, italic=False, font=BODY_FONT):
    r = paragraph.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.color.rgb = color
    r.font.bold = bold
    r.font.italic = italic
    r.font.name = font
    return r


def header(slide, eyebrow_text):
    """Small icon + italic indigo running header, top-left (persists per section)."""
    slide.shapes.add_picture(LOGO_ICON, Inches(0.55), Inches(0.42), height=Inches(0.42))
    tf = add_textbox(slide, 1.05, 0.42, 8, 0.5)
    run(tf.paragraphs[0], eyebrow_text, 15, INDIGO, italic=True, font=ITALIC_FONT)


def big_title(slide, text, top=1.55, size=44):
    tf = add_textbox(slide, 0.55, top, 12.2, 1.7)
    run(tf.paragraphs[0], text, size, INDIGO, bold=True, font=HEADING_FONT)
    return tf


def bullets(slide, items, top=3.2, size=20):
    tf = add_textbox(slide, 0.6, top, 11.8, 3.6)
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(14)
        run(p, "●  " + item, size, BLACK, font=BODY_FONT)


def page_number(slide, dark=False):
    global slide_num
    slide_num += 1
    tf = add_textbox(slide, 12.55, 7.05, 0.7, 0.35)
    tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
    run(tf.paragraphs[0], str(slide_num), 12, GREY if not dark else RGBColor(0xCF, 0xCE, 0xE8), bold=True, font=BODY_FONT)


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def box(slide, shape_type, left, top, width, height, fill, text="", text_color=BLACK,
         text_size=14, border=None, bold=True):
    sh = slide.shapes.add_shape(shape_type, Inches(left), Inches(top), Inches(width), Inches(height))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if border is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = border
        sh.line.width = Pt(1.25)
    sh.shadow.inherit = False
    if text:
        tf = sh.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.08); tf.margin_right = Inches(0.08)
        tf.margin_top = Inches(0.04); tf.margin_bottom = Inches(0.04)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for i, line in enumerate(text.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.CENTER
            run(p, line, text_size, text_color, bold=bold, font=BODY_FONT)
    return sh


def arrow_down(slide, cx, top, height=0.22, width=0.34, fill=INDIGO):
    slide.shapes.add_shape(
        MSO_SHAPE.DOWN_ARROW, Inches(cx - width / 2), Inches(top), Inches(width), Inches(height)
    ).fill.solid()
    sh = slide.shapes[-1]
    sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def arrow_up(slide, cx, top, height=0.22, width=0.34, fill=INDIGO):
    sh = slide.shapes.add_shape(
        MSO_SHAPE.UP_ARROW, Inches(cx - width / 2), Inches(top), Inches(width), Inches(height)
    )
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def arrow_right(slide, left, cy, width=0.34, height=0.22, fill=INDIGO, flip=False):
    shape_kind = MSO_SHAPE.LEFT_ARROW if flip else MSO_SHAPE.RIGHT_ARROW
    sh = slide.shapes.add_shape(shape_kind, Inches(left), Inches(cy - height / 2), Inches(width), Inches(height))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def diagram_slide(eyebrow_text, title_text, title_size=32, title_top=1.0):
    s = add_slide()
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = WHITE
    header(s, eyebrow_text)
    big_title(s, title_text, top=title_top, size=title_size)
    return s


def small_label(slide, cx, top, text, width=3.2, size=11, color=GREY):
    tf = add_textbox(slide, cx - width / 2, top, width, 0.3)
    tf.paragraphs[0].alignment = PP_ALIGN.CENTER
    run(tf.paragraphs[0], text, size, color, italic=True, font=ITALIC_FONT)


def architecture_diagram_slide():
    s = add_slide()
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = WHITE
    header(s, "Approach & Methodology")
    big_title(s, "End-to-End Architecture, At a Glance", top=1.0, size=32)

    cx = 6.6  # horizontal center of the whole diagram

    # user
    box(s, MSO_SHAPE.OVAL, cx - 1.3, 1.85, 2.6, 0.55, WHITE, "Pharmacist",
        text_color=INDIGO, border=INDIGO, text_size=14)
    arrow_down(s, cx, 2.42)
    small_label(s, cx + 1.9, 2.40, "asks in plain language")

    # frontend
    box(s, MSO_SHAPE.ROUNDED_RECTANGLE, cx - 4.15, 2.72, 8.3, 0.62, WHITE,
        "React Frontend  :  Dashboard  ·  Chat  ·  Profile",
        text_color=INDIGO, border=INDIGO, text_size=15)
    arrow_down(s, cx, 3.36)
    small_label(s, cx + 1.7, 3.34, "REST + streaming (SSE)")

    # backend, the core
    box(s, MSO_SHAPE.ROUNDED_RECTANGLE, cx - 4.15, 3.66, 8.3, 0.72, INDIGO,
        "Backend  —  9-step pipeline orchestration",
        text_color=WHITE, text_size=16)

    # fan-out bus bar
    bus_y = 4.40
    box(s, MSO_SHAPE.RECTANGLE, cx - 4.15, bus_y, 8.3, 0.05, INDIGO)

    col_w = 3.55
    gap = 0.35
    total = col_w * 3 + gap * 2
    start_x = cx - total / 2
    centers = [start_x + col_w / 2, start_x + col_w + gap + col_w / 2, start_x + 2 * (col_w + gap) + col_w / 2]

    for c in centers:
        arrow_down(s, c, bus_y + 0.05, height=0.20, width=0.30)

    box_top = bus_y + 0.27
    box_h = 0.85
    box(s, MSO_SHAPE.HEXAGON, centers[0] - col_w / 2, box_top, col_w, box_h, LOGO_BLUE,
        "Ollama (local LLM)\nqwen2.5-coder:7b", text_color=WHITE, text_size=13)
    box(s, MSO_SHAPE.CLOUD, centers[1] - col_w / 2, box_top - 0.08, col_w, box_h + 0.16, MINT,
        "ChromaDB (RAG)\none collection per pharmacy", text_color=NAVY, text_size=13)
    box(s, MSO_SHAPE.CAN, centers[2] - col_w / 2, box_top, col_w, box_h, NAVY,
        "PostgreSQL\nrow-level security (RLS)", text_color=WHITE, text_size=13)

    # dbt feeding postgres
    dbt_y = box_top + box_h + 0.14
    arrow_down(s, centers[2], box_top + box_h - 0.05, height=0.18, width=0.28, fill=NAVY)
    box(s, MSO_SHAPE.ROUNDED_RECTANGLE, centers[2] - col_w / 2, dbt_y, col_w, 0.42, WHITE,
        "dbt: raw → staging → marts", text_color=INDIGO, border=INDIGO, text_size=11, bold=False)

    small_label(s, cx, dbt_y + 0.55, "Ollama and Postgres run entirely on the local machine, no external network call", width=10.5, size=12, color=GREY)

    page_number(s)
    set_notes(s, (
        "Use this as the visual anchor for the whole Approach & Methodology section.\n"
        "Point out the fan-out from the backend: one orchestrator, three local services.\n"
        "Repeat: Ollama and Postgres are both local, nothing shown here calls out to the internet.\n"
        "The 9 pipeline steps that follow all happen inside the FastAPI box."
    ))
    return s


def footnote(slide, text, top=6.85):
    """Small grey citation line, bottom-left, clear of the page number (bottom-right)."""
    tf = add_textbox(slide, 0.6, top, 10.8, 0.35)
    run(tf.paragraphs[0], text, 10.5, GREY, italic=True, font=ITALIC_FONT)


def content_slide(eyebrow_text, title_text, bullet_items, notes_text, title_size=44,
                   bullets_top=3.2, bullets_size=20, footnote_text=None):
    s = add_slide()
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = WHITE
    header(s, eyebrow_text)
    big_title(s, title_text, size=title_size)
    bullets(s, bullet_items, top=bullets_top, size=bullets_size)
    if footnote_text:
        footnote(s, footnote_text)
    page_number(s)
    set_notes(s, notes_text)
    return s


# 0. TITLE ------------------------------------------------------------------
s = add_slide()
s.background.fill.solid()
s.background.fill.fore_color.rgb = INDIGO

# decorative circles, mirroring the template's composition (mint behind, navy in front)
mint = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.6), Inches(-1.6), Inches(6.6), Inches(6.6))
mint.fill.solid(); mint.fill.fore_color.rgb = MINT; mint.line.fill.background(); mint.shadow.inherit = False
navy = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(9.9), Inches(3.55), Inches(2.9), Inches(2.9))
navy.fill.solid(); navy.fill.fore_color.rgb = NAVY; navy.line.fill.background(); navy.shadow.inherit = False

# white circle + logo, top right
white_circle = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.55), Inches(-1.3), Inches(3.2), Inches(3.2))
white_circle.fill.solid(); white_circle.fill.fore_color.rgb = WHITE; white_circle.line.fill.background(); white_circle.shadow.inherit = False
s.shapes.add_picture(LOGO_FULL, Inches(10.95), Inches(0.35), height=Inches(0.6))

tf = add_textbox(s, 0.9, 2.5, 9.5, 0.5)
run(tf.paragraphs[0], "APPLIED AI / DATA PRODUCT", 15, WHITE, bold=True, font=BODY_FONT)
tf = add_textbox(s, 0.85, 2.95, 10.5, 1.9)
run(tf.paragraphs[0], "RuwaGenBI", 52, WHITE, bold=True, font=HEADING_FONT)
tf = add_textbox(s, 0.9, 4.15, 9.8, 1.0)
run(tf.paragraphs[0], "Generative BI for pharmacies: from natural language to reliable SQL, fully on-device", 22, WHITE, font=BODY_FONT)
tf = add_textbox(s, 0.9, 5.35, 6, 0.5)
run(tf.paragraphs[0], PRESENTER, 22, WHITE, bold=True, font=HEADING_FONT)

# navy circle text block: Topic type / ML Roundtable / Date
tf = add_textbox(s, 10.15, 4.15, 2.6, 1.9, anchor=MSO_ANCHOR.MIDDLE)
tf.paragraphs[0].alignment = PP_ALIGN.CENTER
run(tf.paragraphs[0], "ML Roundtable", 15, WHITE, font=BODY_FONT)
p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
run(p2, "[Date]", 14, RGBColor(0xC9, 0xC7, 0xEE), font=BODY_FONT)

# 1-2. PROBLEM & MOTIVATION --------------------------------------------------
content_slide(
    "Problem & Motivation",
    "Problem & Motivation",
    [
        "Classic BI locks in the question before the need is even known: business need, then an "
        "analyst writes SQL, then a dashboard gets published, then the user consults it.",
        "Any unanticipated question triggers a brand new cycle: a ticket, a developer, a deployment.",
        "Proof point in this very project: the React Dashboard runs 6 pre-written SQL queries. "
        "That's classic BI, just with a modern interface.",
    ],
    "1:00\n"
    "Walk through the cycle: business need, analyst, dashboard, consult.\n"
    "Stress: any unanticipated question means a full development cycle.\n"
    "Concrete proof point from this very project: the Dashboard page is exactly that pattern."
)

content_slide(
    "Problem & Motivation",
    "The Proposition: Generate SQL On the Fly",
    [
        "An LLM translates any natural-language question into SQL at the moment it's asked.",
        "Coverage is no longer “what we had time to build,” it's “everything the data can answer.”",
        "The real risk: an LLM can hallucinate incorrect SQL. The rest of this talk is how trust is "
        "built around that unpredictability.",
    ],
    "1:00\n"
    "State the core proposition plainly.\n"
    "Name the risk (hallucination) immediately, it defuses the question the audience is already forming.\n"
    "Explicitly frame the rest of the talk as the answer to that risk."
)


def business_value_slide():
    s = diagram_slide("Problem & Motivation", "Why This Matters to the Pharmacy Team", title_size=32)

    cards = [
        (INDIGO, "Get answers in seconds",
         "Ask a question and get an answer right away. No ticket, no developer, no waiting."),
        (LOGO_BLUE, "Ask anything, not just the usual",
         "A fixed dashboard only answers a few set questions. Here, you can ask anything about "
         "your data."),
        (MINT, "Catch problems early",
         "The system warns you about low stock or products about to expire, while there is "
         "still time to act."),
        (NAVY, "Safe for every pharmacy",
         "Each pharmacy only sees its own numbers. This stays true even as more pharmacies "
         "join the network."),
    ]

    col_w, gap_x = 5.55, 0.5
    row_h, gap_y = 1.55, 0.3
    accent_h = 0.1
    start_x = 6.6 - (col_w * 2 + gap_x) / 2
    start_y = 2.05

    for i, (color, title, desc) in enumerate(cards):
        col, row = i % 2, i // 2
        left = start_x + col * (col_w + gap_x)
        top = start_y + row * (row_h + gap_y + accent_h)
        box(s, MSO_SHAPE.RECTANGLE, left, top, col_w, accent_h, color)
        card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top + accent_h),
                                   Inches(col_w), Inches(row_h))
        card.fill.solid(); card.fill.fore_color.rgb = WHITE
        card.line.color.rgb = color; card.line.width = Pt(1.5)
        card.shadow.inherit = False
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.22); tf.margin_right = Inches(0.22)
        tf.margin_top = Inches(0.16); tf.margin_bottom = Inches(0.16)
        p = tf.paragraphs[0]
        run(p, title, 16, INDIGO, bold=True, font=HEADING_FONT)
        p2 = tf.add_paragraph()
        p2.space_before = Pt(6)
        run(p2, desc, 13, BLACK, font=BODY_FONT)

    bottom = start_y + 2 * (row_h + gap_y + accent_h) + 0.1
    tf = add_textbox(s, 0.9, bottom, 11.5, 0.5)
    run(tf.paragraphs[0], "The big change: you don't need a developer to ask a new question. "
        "You just ask it.", 15, INDIGO, bold=True, italic=True, font=HEADING_FONT)

    page_number(s)
    set_notes(s, (
        "1:00\n"
        "This slide answers the template's own “why is this important” prompt directly, before "
        "diving into architecture.\n"
        "Go through the 4 cards briskly, they are meant to land quickly, not be read word for word.\n"
        "Close on the italic line: the shift is from “needs a developer” to “just ask.” That's the "
        "business takeaway to leave them with before the technical deep dive starts."
    ))
    return s


business_value_slide()

# 3. APPROACH & METHODOLOGY (section header) ---------------------------------
content_slide(
    "Approach & Methodology",
    "Approach & Methodology",
    [
        "Frontend: React 18 + Vite. Dashboard (fixed SQL), Chat (LLM), Profile. Bilingual FR/EN.",
        "Backend: FastAPI + Python 3.11. Orchestrates a 9-step pipeline. Zero hardcoded business logic.",
        "Local LLM: Ollama runs natively on macOS with qwen2.5-coder:7b, never inside a Docker "
        "container. No data ever leaves the machine.",
    ],
    "1:00\n"
    "Three layers, one sentence each.\n"
    "Stress Ollama running natively, never in Docker, zero external network call.\n"
    "This is the foundation for the “zero data leakage” argument used later."
)

architecture_diagram_slide()

def data_layer_slide():
    s = diagram_slide("Approach & Methodology", "Data Layer: raw, staging, marts")

    cx = 6.6
    col_w = 3.3
    gap = 0.5
    total = col_w * 3 + gap * 2
    start_x = cx - total / 2
    centers = [start_x + col_w / 2, start_x + col_w + gap + col_w / 2, start_x + 2 * (col_w + gap) + col_w / 2]
    row_top = 2.35
    row_h = 0.95

    box(s, MSO_SHAPE.ROUNDED_RECTANGLE, centers[0] - col_w / 2, row_top, col_w, row_h, WHITE,
        "raw\ningested, never edited", text_color=INDIGO, border=INDIGO, text_size=14)
    arrow_right(s, centers[0] + col_w / 2 + 0.06, row_top + row_h / 2, width=0.34)
    box(s, MSO_SHAPE.ROUNDED_RECTANGLE, centers[1] - col_w / 2, row_top, col_w, row_h, WHITE,
        "staging\ncleaned views", text_color=INDIGO, border=INDIGO, text_size=14)
    arrow_right(s, centers[1] + col_w / 2 + 0.06, row_top + row_h / 2, width=0.34)
    box(s, MSO_SHAPE.ROUNDED_RECTANGLE, centers[2] - col_w / 2, row_top, col_w, row_h, INDIGO,
        "marts\n9 tables the LLM queries", text_color=WHITE, text_size=14)

    arrow_down(s, centers[2], row_top + row_h + 0.06, height=0.20, width=0.30, fill=NAVY)
    box(s, MSO_SHAPE.ROUNDED_RECTANGLE, centers[2] - col_w / 2, row_top + row_h + 0.34, col_w, 0.5,
        NAVY, "row-level security (RLS)\napplied on every rebuild", text_color=WHITE, text_size=12)

    small_label(s, cx, row_top + row_h + 1.05,
                "19 dbt models total: 10 in staging, 9 in marts", width=8, size=13, color=GREY)

    tf = add_textbox(s, 0.9, row_top + row_h + 1.5, 11.5, 1.0)
    run(tf.paragraphs[0], "Even if the generated SQL forgets a filter, cross-pharmacy leakage stays "
        "structurally impossible.", 16, BLACK, font=BODY_FONT)

    page_number(s)
    set_notes(s, (
        "1:00\n"
        "raw, staging, marts: one sentence each, do not linger.\n"
        "Key point: isolation is a Postgres policy (RLS), not a WHERE clause written in Python.\n"
        "Repeat the guarantee: even if the LLM forgets a filter, cross-pharmacy access is impossible."
    ))
    return s


data_layer_slide()

def pipeline_steps_slide():
    s = diagram_slide("Approach & Methodology", "The Pipeline: 9 Steps, ~800ms End-to-End", title_size=34)

    steps = [
        "1. Retrieve\nsimilar examples", "2. Filter\nrelevant schema", "3. Generate\nSQL",
        "4. Validate\nread-only", "5. Execute\n+ auto-repair", "6. Check\ncoherence",
        "7. Format\nfor humans", "8. Generate\ninsight", "9. Pick\nchart type",
    ]
    colors = [MINT, MINT, LOGO_BLUE, INDIGO, INDIGO, INDIGO, MINT, LOGO_BLUE, MINT]
    text_colors = [NAVY, NAVY, WHITE, WHITE, WHITE, WHITE, NAVY, WHITE, NAVY]

    cx = 6.6
    col_w = 3.55
    gap = 0.35
    total = col_w * 3 + gap * 2
    start_x = cx - total / 2
    col_centers = [start_x + col_w / 2, start_x + col_w + gap + col_w / 2, start_x + 2 * (col_w + gap) + col_w / 2]

    box_h = 0.78
    row_gap = 0.42
    row_tops = [2.15, 2.15 + box_h + row_gap, 2.15 + 2 * (box_h + row_gap)]

    order = [
        (0, 0), (0, 1), (0, 2),   # row 1, left to right: steps 1,2,3
        (1, 2), (1, 1), (1, 0),   # row 2, right to left: steps 4,5,6
        (2, 0), (2, 1), (2, 2),   # row 3, left to right: steps 7,8,9
    ]
    for i, (row, col) in enumerate(order):
        left = col_centers[col] - col_w / 2
        top = row_tops[row]
        box(s, MSO_SHAPE.ROUNDED_RECTANGLE, left, top, col_w, box_h, colors[i],
            steps[i], text_color=text_colors[i], text_size=13)

    # arrows within row 1 (left to right)
    arrow_right(s, col_centers[0] + col_w / 2 + 0.06, row_tops[0] + box_h / 2, width=0.24)
    arrow_right(s, col_centers[1] + col_w / 2 + 0.06, row_tops[0] + box_h / 2, width=0.24)
    # wrap down, right side
    arrow_down(s, col_centers[2], row_tops[0] + box_h + 0.05, height=0.18, width=0.28)
    # arrows within row 2 (right to left)
    arrow_right(s, col_centers[1] + col_w / 2 - 0.30, row_tops[1] + box_h / 2, width=0.24, flip=True)
    arrow_right(s, col_centers[0] + col_w / 2 - 0.30, row_tops[1] + box_h / 2, width=0.24, flip=True)
    # wrap down, left side
    arrow_down(s, col_centers[0], row_tops[1] + box_h + 0.05, height=0.18, width=0.28)
    # arrows within row 3 (left to right)
    arrow_right(s, col_centers[0] + col_w / 2 + 0.06, row_tops[2] + box_h / 2, width=0.24)
    arrow_right(s, col_centers[1] + col_w / 2 + 0.06, row_tops[2] + box_h / 2, width=0.24)

    small_label(s, cx, row_tops[2] + box_h + 0.25,
                "Steps 3 and 8 call the local LLM (Ollama). Every other step is plain, deterministic code.",
                width=10.5, size=13, color=GREY)

    page_number(s)
    set_notes(s, (
        "1:00\n"
        "Overview only, do not detail every step here, the next slides zoom in.\n"
        "Give the headline number: about 800ms end-to-end on a reference question.\n"
        "Point out visually: only 2 of the 9 boxes touch the LLM, the rest is deterministic code."
    ))
    return s


pipeline_steps_slide()

content_slide(
    "Approach & Methodology",
    "Reducing Context Intelligently, No LLM Involved",
    [
        "Example retrieval: one ChromaDB collection per pharmacy, retrieves the 3 closest "
        "question/SQL examples by meaning.",
        "Schema filtering: a score blending a little lexical overlap and mostly semantic "
        "similarity, computed per table.",
        "Keeps the 15 most relevant tables out of 19, with 3 always included for safety.",
    ],
    "1:30\n"
    "Two distinct mechanisms, stress the difference: past examples vs. relevant tables.\n"
    "Repeat: zero LLM call in schema filtering, fast and deterministic.\n"
    "Key number: schema shrunk from 13,200 to 2,600 characters, a measured quality gain.\n"
    "Both cited papers are on the References slide if anyone asks for the source.",
    footnote_text="Hybrid scoring approach adapted from Tang et al., AP-SQL, EITCE 2025 (arXiv:2506.03598) "
                  "and Nahid et al., Bidirectional Schema Linking, EACL 2026 Findings (arXiv:2510.14296)",
)

content_slide(
    "Approach & Methodology",
    "Deterministic Generation, Structural Validation",
    [
        "SQL is generated at zero temperature, to stay as deterministic as possible.",
        "The most critical reminders are placed right before the question itself, the model reads "
        "them last and follows them best.",
        "Validation is a real parser, not a keyword blocklist: checks for a single statement, and "
        "that it's read-only.",
        "This isn't where real security lives, that comes from read-only database rights and "
        "row-level isolation.",
    ],
    "1:30\n"
    "Zero temperature: explain why, same question should always produce the same SQL.\n"
    "If asked: critical reminders sit right before the question, high-recency position.\n"
    "State explicitly: this validation is not the real security boundary, that comes next."
)

def mars_sql_slide():
    s = diagram_slide("Approach & Methodology", "MARS-SQL: Automated Repair via Execution Feedback",
                       title_size=32)

    cx = 6.6
    col_w = 2.65
    gap = 0.3
    total = col_w * 4 + gap * 3
    start_x = cx - total / 2
    centers = [start_x + col_w / 2 + i * (col_w + gap) for i in range(4)]
    row_top = 2.3
    box_h = 0.85

    labels = ["SQL\nfails", "Exact error\nsent to LLM", "SQL gets\ncorrected", "Retry\nexecution"]
    colors = [NAVY, LOGO_BLUE, LOGO_BLUE, INDIGO]
    for i, (c, label, fill) in enumerate(zip(centers, labels, colors)):
        box(s, MSO_SHAPE.ROUNDED_RECTANGLE, c - col_w / 2, row_top, col_w, box_h, fill,
            label, text_color=WHITE, text_size=14)
        if i < 3:
            arrow_right(s, c + col_w / 2 + 0.04, row_top + box_h / 2, width=0.22)

    # loop-back path, offset to the right of box 4's center, back to box 1
    tick_top = row_top + box_h + 0.02
    tick_h = 0.33
    bar_y = tick_top + tick_h
    loop_x = centers[3] + 0.55
    box(s, MSO_SHAPE.RECTANGLE, centers[0], bar_y, loop_x - centers[0], 0.05, GREY)
    box(s, MSO_SHAPE.RECTANGLE, loop_x - 0.025, tick_top, 0.05, tick_h, GREY)
    arrow_up(s, centers[0], tick_top, height=tick_h, width=0.28, fill=GREY)
    small_label(s, (centers[0] + loop_x) / 2, bar_y + 0.12,
                "loops back, up to 2 repairs, 3 attempts total", width=7, size=12)

    # outcome, straight down from box 4's own center, reaching all the way to the outcome card
    exit_y = bar_y + 0.55
    arrow_down(s, centers[3] - 0.55, tick_top, height=exit_y - tick_top - 0.04, width=0.26, fill=MINT)
    outcome_w = col_w * 2 + gap
    box(s, MSO_SHAPE.ROUNDED_RECTANGLE, centers[3] - outcome_w + col_w / 2, exit_y, outcome_w, 0.6,
        WHITE, "Succeeds  →  result returned\nStill fails after 3 tries  →  clear error shown to user",
        text_color=INDIGO, border=INDIGO, text_size=12, bold=False)

    footnote(s, "Multi-agent, execution-feedback idea adapted from Yang et al., MARS-SQL, "
                "arXiv:2511.01008 (2025)")
    page_number(s)
    set_notes(s, (
        "1:30, KEY MOMENT, take your time here\n"
        "Walk the cycle slowly: fails, exact error goes back to the LLM, it corrects, retries.\n"
        "Stress the difference with a blind retry: the model sees why, not just that it should retry.\n"
        "Anticipate the likely question: what if all 3 attempts fail? Point at the right-hand box: a "
        "clear error is returned to the user, never silence or a made-up result.\n"
        "If asked about the paper's venue: it is an arXiv preprint, cite it as such, do not say ICLR "
        "2025, that claim was checked and is not supported by the paper's own listing."
    ))
    return s


mars_sql_slide()

content_slide(
    "Approach & Methodology",
    "Semantic Validation: Coherence, Not Just Syntax",
    [
        "An empty result is suspicious, unless the question is about existence.",
        "A question expecting a single value but returning more than 3 ungrouped rows is suspicious.",
        "A “top N” query returning far more than N rows is suspicious too.",
        "Deliberately conservative: prefers letting a borderline case through over needless "
        "re-generation.",
    ],
    "1:00\n"
    "Distinguish clearly from the previous slide: here the SQL runs without error, different question.\n"
    "Go through the 3 rules quickly, do not over-explain each one.\n"
    "Stress: most text-to-SQL systems do not have this layer at all."
)

content_slide(
    "Approach & Methodology",
    "Reliable Steps Built Around an Unreliable Model",
    [
        "Formatting: months, days, true/false values. Simple conversions, no LLM dependency.",
        "Insight: a sentence generated at low temperature, then automatically corrected so amount "
        "formatting is always right.",
        "Every step adds a reliable safeguard around a model that isn't always reliable. The "
        "architecture assumes the LLM will make mistakes, and is built around that.",
    ],
    "1:00\n"
    "Formatting step: pure conversions, zero LLM dependency, move quickly.\n"
    "Insight: low temperature plus deterministic correction after the fact on amount formatting.\n"
    "Key message, try to say it close to verbatim: the architecture assumes the LLM will make "
    "mistakes, and organizes around that."
)

def chart_decision_slide():
    s = diagram_slide("Approach & Methodology", "The Chart Picks Itself", title_size=36)

    rows = [
        ("Time trend in the question", "Line chart", LOGO_BLUE),
        ("A “LIMIT” in the SQL (top-N)", "Bar chart", INDIGO),
        ("Ranking / comparison wording", "Bar chart", INDIGO),
        ("Composition / breakdown wording", "Pie chart", MINT),
        ("None of the above", "Bar chart (default)", INDIGO),
    ]
    left_x, left_w = 1.15, 7.1
    right_x, right_w = 8.75, 3.55
    row_h, row_gap = 0.62, 0.14
    top0 = 2.05

    for i, (cond, outcome, color) in enumerate(rows):
        top = top0 + i * (row_h + row_gap)
        box(s, MSO_SHAPE.OVAL, 0.55, top, 0.5, row_h, WHITE, str(i + 1),
            text_color=INDIGO, border=INDIGO, text_size=15)
        box(s, MSO_SHAPE.ROUNDED_RECTANGLE, left_x, top, left_w, row_h, WHITE, cond,
            text_color=BLACK, border=GREY, text_size=15, bold=False)
        arrow_right(s, left_x + left_w + 0.06, top + row_h / 2, width=0.28, height=0.2)
        text_color = NAVY if color == MINT else WHITE
        box(s, MSO_SHAPE.ROUNDED_RECTANGLE, right_x, top, right_w, row_h, color, outcome,
            text_color=text_color, text_size=15)

    small_label(s, 6.6, top0 + 5 * (row_h + row_gap) + 0.05,
                "Checked top to bottom, first match wins. Entirely Python and regex, zero LLM.",
                width=10.5, size=13, color=GREY)

    page_number(s)
    set_notes(s, (
        "0:45\n"
        "Go through the cascade quickly, one sentence per rule, follow the numbers top to bottom.\n"
        "Repeat: this logic is entirely Python and regex, zero LLM here either.\n"
        "Mention the frontend refines the choice further (single line vs. combo chart)."
    ))
    return s


chart_decision_slide()

content_slide(
    "Approach & Methodology",
    "Zero Redeployment to Adjust LLM Behavior",
    [
        "All business rules, the ones covering charts, semantic validation, and prompt reminders, "
        "live in four readable configuration files.",
        "A single admin endpoint call reloads them live, with nothing restarted.",
        "Adjusting a rule means editing a text file, never touching Python code.",
    ],
    "1:00\n"
    "Business rules live in configuration, not code, stress this choice.\n"
    "Hot reload, no redeployment: a good example of the project's agility.\n"
    "If a technical audience is curious: every rule is a readable file, not hidden code."
)

def security_layers_slide():
    s = diagram_slide("Approach & Methodology", "Three Independent Security Layers", title_size=34)

    cards = [
        (INDIGO, "Read-only role", "The pipeline's database account only has read rights, and "
                                   "cannot bypass isolation even if it tried."),
        (LOGO_BLUE, "Database-enforced isolation", "Each pharmacy only ever sees its own rows."),
        (NAVY, "A real parser", "A single statement, never anything but a read."),
    ]
    col_w, gap = 3.7, 0.5
    total = col_w * 3 + gap * 2
    start_x = 6.6 - total / 2
    accent_top, accent_h = 2.15, 0.14
    body_top, body_h = accent_top + accent_h, 2.9

    for i, (color, title, desc) in enumerate(cards):
        left = start_x + i * (col_w + gap)
        box(s, MSO_SHAPE.RECTANGLE, left, accent_top, col_w, accent_h, color)
        card = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(body_top),
                                   Inches(col_w), Inches(body_h))
        card.fill.solid(); card.fill.fore_color.rgb = WHITE
        card.line.color.rgb = color; card.line.width = Pt(1.5)
        card.shadow.inherit = False
        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.22); tf.margin_right = Inches(0.22)
        tf.margin_top = Inches(0.28); tf.margin_bottom = Inches(0.2)
        p = tf.paragraphs[0]
        run(p, title, 17, INDIGO, bold=True, font=HEADING_FONT)
        p2 = tf.add_paragraph()
        p2.space_before = Pt(10)
        run(p2, desc, 14, BLACK, font=BODY_FONT)

    tf = add_textbox(s, 0.9, body_top + body_h + 0.25, 11.5, 0.5)
    run(tf.paragraphs[0], "None of these three layers depends on the LLM behaving correctly.",
        16, INDIGO, bold=True, font=BODY_FONT)

    page_number(s)
    set_notes(s, (
        "1:00\n"
        "Recap the 3 layers, one sentence each, do not repeat what was already said in detail.\n"
        "Repeat the most important point: none of these 3 layers depends on the LLM being reliable.\n"
        "Best answer if someone asks what happens if the model gets it completely wrong."
    ))
    return s


security_layers_slide()

# 4. RESULTS & EVALUATION -----------------------------------------------------
content_slide(
    "Results & Evaluation",
    "Results & Evaluation",
    [
        "50 business questions across 7 categories, a test suite replayed on every change.",
        "Against a model twice the size: same score, but twice as slow. Documented rollback, "
        "backed by real numbers.",
        "The chosen model (7 billion parameters) offers the best quality/speed balance, measured, "
        "not assumed.",
    ],
    "1:00\n"
    "Golden set of 50 questions, reproducible on every change, mention briefly.\n"
    "The point to really land here: an argued rejection of a bigger model, with precise numbers.\n"
    "It shows engineering discipline, not just “we picked the biggest model available.”"
)

content_slide(
    "Results & Evaluation",
    "Live Walkthrough",
    [
        "A real question asked in the Chat, walking through the generated SQL, the chart, and the "
        "resulting sentence together.",
        "Safety net planned: a screenshot or a short backup video in case Ollama is slow that day.",
    ],
    "2:00 to 3:00, SWITCH TO THE LIVE APPLICATION\n"
    "Ask a simple question first, to show the normal path (SQL, chart, insight).\n"
    "If time allows: ask a slightly ambiguous question to trigger MARS-SQL live.\n"
    "Backup plan ready: screenshot or short video if Ollama is slow that day."
)

# 5. CONCLUSIONS & FUTURE WORK -------------------------------------------------
content_slide(
    "Conclusions & Future Work",
    "Conclusions & Future Work",
    [
        "Key takeaway: classic BI trades flexibility for reliability. A raw LLM does the opposite. "
        "This system keeps natural-language flexibility while layering deterministic safeguards "
        "at every stage.",
        "Honest limitation: Ollama processes one generation at a time, no real multi-user "
        "parallelism yet. This remains a lab MVP, not a production deployment, by design.",
        "Future directions: enable Ollama's parallelism, cache frequent questions, move to an "
        "inference server with batching.",
    ],
    "1:00, SECOND MOMENT WHERE A TECHNICAL AUDIENCE DIGS IN, leave room\n"
    "Own it fully: Ollama is single-threaded, no real parallelism today.\n"
    "Context to repeat: lab MVP, not production, this is an assumed choice.\n"
    "If the scaling question comes back: give the 3 listed directions, without committing to a "
    "timeline.\n"
    "Close by reading the key takeaway close to verbatim, then open the floor."
)

# 5b. REFERENCES ----------------------------------------------------------------
content_slide(
    "Conclusions & Future Work",
    "References",
    [
        "Yang, Zhang, He, Zhou, Fung. “MARS-SQL: A Multi-Agent Reinforcement Learning Framework "
        "for Text-to-SQL.” arXiv:2511.01008 (2025). Underlies the execution-feedback repair loop.",
        "Tang, Ma, Wu. “AP-SQL: A Resource-Efficient Architecture for Text-to-SQL Translation in "
        "Constrained Environments.” EITCE 2025, arXiv:2506.03598. Underlies the schema-filtering "
        "score.",
        "Nahid, Rafiei, Zhang, Zhang. “Rethinking Schema Linking: A Context-Aware Bidirectional "
        "Retrieval Approach for Text-to-SQL.” EACL 2026 (Findings), arXiv:2510.14296. Underlies the "
        "schema-filtering score.",
    ],
    "Only papers whose actual idea is used in a slide are listed here, verified directly against "
    "each paper's arXiv listing before this talk, not just copied from internal notes.\n"
    "If asked why no venue is given for MARS-SQL: it is currently an arXiv preprint only, no "
    "conference or journal acceptance is listed on arXiv as of this talk.",
    bullets_size=16,
    bullets_top=2.6,
)

# 6. QUESTIONS & DISCUSSION -----------------------------------------------------
content_slide(
    "Questions & Discussion",
    "Questions & Discussion",
    ["Open floor for questions"],
    "Open floor. Keep MARS-SQL and the scalability limits close in mind, they are the two most "
    "likely topics.",
    bullets_top=3.6,
)

# 7. THANK YOU -----------------------------------------------------------------
s = add_slide()
s.background.fill.solid()
s.background.fill.fore_color.rgb = WHITE
s.shapes.add_picture(LOGO_ICON, Inches(0.55), Inches(0.42), height=Inches(0.42))
tf = add_textbox(s, 0.9, 3.3, 11, 1.5, anchor=MSO_ANCHOR.MIDDLE)
run(tf.paragraphs[0], "Thank you for your attention", 46, INDIGO, bold=True, font=HEADING_FONT)
set_notes(s, "Thank the audience, invite follow-up questions offline if time ran out.")

prs.save("RuwaGenBI_Kera_MLRoundtable.pptx")
print("OK:", len(prs.slides.__iter__.__self__._sldIdLst), "slides generated")

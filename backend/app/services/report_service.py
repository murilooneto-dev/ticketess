from datetime import date, datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.config import settings
from app.models.report import Report, ReportType
from app.services.report_data import ProjectPeriodData, collect_period_data
from app.services.report_glossary import (
    describe_project_period_summary_plain,
    describe_ticket_opened_technical,
    describe_ticket_resolved_technical,
)

BRAND_NAVY = colors.HexColor("#0b1530")
BRAND_BLUE = colors.HexColor("#1554c9")
BRAND_BLUE_LIGHT = colors.HexColor("#5aa9ff")
BRAND_GRAY = colors.HexColor("#64748b")
BRAND_BORDER = colors.HexColor("#cbd5e1")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2 * cm
HEADER_HEIGHT = 2.6 * cm
FOOTER_HEIGHT = 1.2 * cm

LOGO_PATH = Path(__file__).resolve().parents[3] / "frontend" / "public" / "logo.png"
LOGO_ASPECT_RATIO = 1536 / 1024

_BASE_STYLES = getSampleStyleSheet()
STYLES = {
    "ReportTitle": ParagraphStyle(
        "ReportTitle", parent=_BASE_STYLES["Title"], textColor=BRAND_NAVY, spaceAfter=4,
    ),
    "Meta": ParagraphStyle("Meta", parent=_BASE_STYLES["Normal"], textColor=BRAND_GRAY, fontSize=9),
    "ProjectHeading": ParagraphStyle(
        "ProjectHeading",
        parent=_BASE_STYLES["Heading2"],
        textColor=colors.white,
        backColor=BRAND_BLUE,
        borderPadding=(6, 8, 6, 8),
        spaceBefore=10,
        spaceAfter=8,
    ),
    "SectionHeading": ParagraphStyle(
        "SectionHeading", parent=_BASE_STYLES["Heading3"], textColor=BRAND_NAVY, spaceBefore=6, spaceAfter=4,
    ),
    "Body": ParagraphStyle("Body", parent=_BASE_STYLES["BodyText"], leading=14, spaceAfter=2),
    "Empty": ParagraphStyle("Empty", parent=_BASE_STYLES["Normal"], textColor=BRAND_GRAY),
}


def _report_dir(report_type: ReportType) -> Path:
    subdir = "technical" if report_type == ReportType.TECHNICAL else "management"
    directory = settings.reports_dir / subdir
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _report_filename(start: date, end: date) -> str:
    return f"{start.isoformat()}_{end.isoformat()}.pdf"


def _bullet(text: str):
    return Paragraph(f"• {text}", STYLES["Body"])


def _draw_header_footer(report_title: str, start: date, end: date):
    period_label = f"{start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}"

    def _draw(canvas, doc):
        canvas.saveState()

        # cabeçalho com a marca — fundo branco-gelo, logo em destaque
        header_top = PAGE_HEIGHT
        canvas.setFillColor(colors.white)
        canvas.rect(0, header_top - HEADER_HEIGHT, PAGE_WIDTH, HEADER_HEIGHT, stroke=0, fill=1)
        canvas.setStrokeColor(BRAND_BLUE)
        canvas.setLineWidth(2)
        canvas.line(0, header_top - HEADER_HEIGHT, PAGE_WIDTH, header_top - HEADER_HEIGHT)

        if LOGO_PATH.is_file():
            logo_height = HEADER_HEIGHT - 0.7 * cm
            logo_width = logo_height * LOGO_ASPECT_RATIO
            canvas.drawImage(
                str(LOGO_PATH),
                MARGIN,
                header_top - HEADER_HEIGHT + 0.35 * cm,
                width=logo_width,
                height=logo_height,
                mask="auto",
                preserveAspectRatio=True,
            )
        else:
            canvas.setFont("Helvetica-Bold", 18)
            canvas.setFillColor(BRAND_NAVY)
            canvas.drawString(MARGIN, header_top - HEADER_HEIGHT + 1.2 * cm, "TickeTess")

        text_y = header_top - HEADER_HEIGHT + 1.35 * cm
        canvas.setFont("Helvetica-Bold", 12)
        canvas.setFillColor(BRAND_NAVY)
        canvas.drawRightString(PAGE_WIDTH - MARGIN, text_y, report_title)
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(BRAND_GRAY)
        canvas.drawRightString(PAGE_WIDTH - MARGIN, text_y - 0.5 * cm, f"Período: {period_label}")

        # rodapé
        canvas.setStrokeColor(BRAND_BORDER)
        canvas.line(MARGIN, FOOTER_HEIGHT, PAGE_WIDTH - MARGIN, FOOTER_HEIGHT)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(BRAND_GRAY)
        generated_at = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
        canvas.drawString(MARGIN, FOOTER_HEIGHT - 0.5 * cm, f"TickeTess — gerado em {generated_at}")
        canvas.drawRightString(PAGE_WIDTH - MARGIN, FOOTER_HEIGHT - 0.5 * cm, f"Página {doc.page}")

        canvas.restoreState()

    return _draw


def _build_pdf(path: Path, report_title: str, start: date, end: date, sections: list[ProjectPeriodData], technical: bool) -> None:
    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        topMargin=HEADER_HEIGHT + 0.6 * cm,
        bottomMargin=FOOTER_HEIGHT + 0.4 * cm,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        title=report_title,
        author="TickeTess",
    )
    frame = Frame(
        MARGIN,
        FOOTER_HEIGHT + 0.4 * cm,
        PAGE_WIDTH - 2 * MARGIN,
        PAGE_HEIGHT - doc.topMargin - (FOOTER_HEIGHT + 0.4 * cm),
        id="content",
    )
    doc.addPageTemplates(
        [PageTemplate(id="branded", frames=[frame], onPage=_draw_header_footer(report_title, start, end))]
    )

    story: list = []

    if not sections:
        story.append(Paragraph("Nenhuma atividade registrada no período.", STYLES["Empty"]))

    for data in sections:
        story.append(Paragraph(f"{data.project.name} — {data.project.status.value}", STYLES["ProjectHeading"]))

        if not technical:
            total = (
                len(data.tickets_opened)
                + len(data.tickets_resolved)
                + len(data.commits)
                + len(data.pull_requests)
                + len(data.updates)
            )
            story.append(
                Paragraph(
                    describe_project_period_summary_plain(data.project.name, total, start, end),
                    STYLES["Body"],
                )
            )
            story.append(Spacer(1, 0.4 * cm))
            continue

        if data.tickets_opened:
            story.append(Paragraph("Solicitações abertas no período", STYLES["SectionHeading"]))
            for ticket in data.tickets_opened:
                story.append(_bullet(describe_ticket_opened_technical(ticket)))
            story.append(Spacer(1, 0.25 * cm))

        if data.tickets_resolved:
            story.append(Paragraph("Solicitações concluídas ou canceladas no período", STYLES["SectionHeading"]))
            for ticket in data.tickets_resolved:
                story.append(_bullet(describe_ticket_resolved_technical(ticket)))
            story.append(Spacer(1, 0.25 * cm))

        if data.commits:
            story.append(Paragraph("Alterações no código", STYLES["SectionHeading"]))
            for commit in data.commits:
                message = commit.message.splitlines()[0] if commit.message else ""
                story.append(_bullet(f"{commit.sha[:7]} — {message} ({commit.author_name or '—'})"))
            story.append(Spacer(1, 0.25 * cm))

        if data.pull_requests:
            story.append(Paragraph("Pull requests", STYLES["SectionHeading"]))
            for pr in data.pull_requests:
                story.append(_bullet(f"#{pr.number} {pr.title} — {pr.state}"))
            story.append(Spacer(1, 0.25 * cm))

        if data.updates:
            story.append(Paragraph("Andamentos registrados", STYLES["SectionHeading"]))
            for update in data.updates:
                story.append(_bullet(update.message))
            story.append(Spacer(1, 0.25 * cm))

        story.append(Spacer(1, 0.4 * cm))

    doc.build(story)


def _upsert_report(db: DbSession, report_type: ReportType, start: date, end: date, file_path: Path) -> Report:
    existing = db.execute(
        select(Report).where(
            Report.type == report_type, Report.period_start == start, Report.period_end == end
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.file_path = str(file_path)
        existing.created_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(existing)
        return existing

    report = Report(
        type=report_type,
        period_start=start,
        period_end=end,
        file_path=str(file_path),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def generate_reports(db: DbSession, start: date, end: date) -> tuple[Report, Report]:
    period_data = collect_period_data(db, start, end)

    technical_path = _report_dir(ReportType.TECHNICAL) / _report_filename(start, end)
    _build_pdf(technical_path, "Relatório Técnico", start, end, period_data, technical=True)

    management_path = _report_dir(ReportType.MANAGEMENT) / _report_filename(start, end)
    _build_pdf(management_path, "Relatório de Acompanhamento", start, end, period_data, technical=False)

    technical_report = _upsert_report(db, ReportType.TECHNICAL, start, end, technical_path)
    management_report = _upsert_report(db, ReportType.MANAGEMENT, start, end, management_path)
    return technical_report, management_report


def list_reports(db: DbSession) -> list[Report]:
    query = select(Report).order_by(Report.period_start.desc())
    return list(db.execute(query).scalars())


def get_report(db: DbSession, report_id: int) -> Report | None:
    return db.get(Report, report_id)

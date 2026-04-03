import io
from datetime import date
from decimal import Decimal, InvalidOperation

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


st.set_page_config(page_title="PNC Travel Forms", page_icon="🧾", layout="centered")

PRIMARY = colors.HexColor("#4E73A8")
BAND = colors.HexColor("#E9F0F8")
LABEL_BG = colors.HexColor("#F8FAFC")
GRID = colors.HexColor("#C8CDD4")
TEXT = colors.HexColor("#1F1F1F")
MUTED = colors.HexColor("#666666")


styles = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "TitleCustom",
    parent=styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=15,
    leading=18,
    textColor=TEXT,
    alignment=TA_LEFT,
    spaceAfter=4,
)
SUBTITLE = ParagraphStyle(
    "SubtitleCustom",
    parent=styles["Normal"],
    fontName="Helvetica-Oblique",
    fontSize=8.5,
    leading=10,
    textColor=MUTED,
    alignment=TA_LEFT,
    spaceAfter=4,
)
CELL = ParagraphStyle(
    "CellCustom",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=8.8,
    leading=10.2,
    textColor=TEXT,
    alignment=TA_LEFT,
)
CELL_BOLD = ParagraphStyle(
    "CellBoldCustom",
    parent=CELL,
    fontName="Helvetica-Bold",
)
CELL_SMALL = ParagraphStyle(
    "CellSmallCustom",
    parent=CELL,
    fontSize=8.0,
    leading=9.0,
    textColor=MUTED,
)
HEADER = ParagraphStyle(
    "HeaderCustom",
    parent=CELL_BOLD,
    fontSize=8.6,
    textColor=colors.white,
    alignment=TA_CENTER,
)
SECTION = ParagraphStyle(
    "SectionCustom",
    parent=CELL_BOLD,
    fontSize=9.0,
    textColor=TEXT,
)
RIGHT = ParagraphStyle(
    "RightCustom",
    parent=CELL,
    alignment=TA_RIGHT,
)


def p(text: str | None, style=CELL):
    safe = (text or "").replace("\n", "<br/>")
    return Paragraph(safe, style)


def money(value: str | float | int | Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    cleaned = str(value).replace(",", "").strip()
    if not cleaned:
        return Decimal("0")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def peso_text(amount: Decimal) -> str:
    return f"PHP {amount:,.2f}"


def yn(flag: bool) -> str:
    return "YES" if flag else "NO"


def section_row(title: str):
    row = [p(title, SECTION), "", ""]
    return row


PDF_COLS = [48 * mm, 93 * mm, 44 * mm]


def add_table(pdf_story, title: str, subtitle: str, right_text: str, rows: list[list]):
    pdf_story.append(p(title, TITLE))
    if subtitle:
        pdf_story.append(p(subtitle, SUBTITLE))

    top = Table(
        [[p("Philippine Nanogoku Corporation", CELL_SMALL), p(right_text, ParagraphStyle("TopRight", parent=CELL_SMALL, alignment=TA_RIGHT))]],
        colWidths=[120 * mm, 65 * mm],
    )
    top.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, GRID),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, GRID),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    pdf_story.append(top)
    pdf_story.append(Spacer(1, 4))

    data = [[p("Item", HEADER), p("Details / Entry", HEADER), p("Notes", HEADER)]] + rows
    table = Table(data, colWidths=PDF_COLS, repeatRows=1)

    style_cmds = [
        ("BOX", (0, 0), (-1, -1), 0.6, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, GRID),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]

    for idx, row in enumerate(data[1:], start=1):
        if isinstance(row[0], Paragraph) and row[0].style.name == SECTION.name:
            style_cmds.extend(
                [
                    ("SPAN", (0, idx), (2, idx)),
                    ("BACKGROUND", (0, idx), (2, idx), BAND),
                    ("BOX", (0, idx), (2, idx), 0.8, colors.HexColor("#7A8CA5")),
                ]
            )
        else:
            style_cmds.append(("BACKGROUND", (0, idx), (0, idx), LABEL_BG))

    table.setStyle(TableStyle(style_cmds))
    pdf_story.append(table)


def build_authorization_pdf(data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=8 * mm,
        title="Travel Authorization & Cash Advance Request",
    )

    rows = [
        section_row("1. EMPLOYEE / TRIP INFORMATION"),
        [p("Employee Name", CELL_BOLD), p(data["employee_name"]), p("")],
        [p("Department / Position", CELL_BOLD), p(f"{data['department']} / {data['position']}"), p("")],
        [p("Date of Request", CELL_BOLD), p(data["request_date"]), p("Submit before travel date")],
        [p("Destination", CELL_BOLD), p(data["destination"]), p("Indicate city / province")],
        [
            p("Travel Period", CELL_BOLD),
            p(f"Departure: {data['departure_date']}    Return: {data['return_date']}    No. of Nights: {data['nights']}"),
            p(""),
        ],
        [p("Purpose of Travel", CELL_BOLD), p(data["purpose"]), p("State business purpose clearly", CELL_SMALL)],
        section_row("2. ESTIMATED TRAVEL COST / CASH ADVANCE REQUEST"),
        [p("Travel Allowance (TA)", CELL_BOLD), p(peso_text(data["ta_amount"])), p("Based on company policy", CELL_SMALL)],
        [p("Transportation", CELL_BOLD), p(peso_text(data["transport_amount"])), p("Airfare / bus / fuel / fares", CELL_SMALL)],
        [p("Accommodation", CELL_BOLD), p(peso_text(data["accommodation_amount"])), p("If company-paid, indicate N/A", CELL_SMALL)],
        [p("Other Estimated Cost", CELL_BOLD), p(peso_text(data["other_amount"])), p("Meals / tolls / incidentals if allowed", CELL_SMALL)],
        [p("TOTAL ESTIMATED COST", CELL_BOLD), p(peso_text(data["total_estimated"]), CELL_BOLD), p("")],
        [p("Cash Advance Requested", CELL_BOLD), p(peso_text(data["cash_advance_requested"]), CELL_BOLD), p("Fill if advance is needed", CELL_SMALL)],
        section_row("3. ADMIN / POLICY CHECK"),
        [p("Overnight Travel?", CELL_BOLD), p(yn(data["overnight_travel"])), p("TA usually applies to overnight travel", CELL_SMALL)],
        [
            p("Provided by Company / Hotel", CELL_BOLD),
            p(
                "Transportation: " + yn(data["company_transport"]) +
                "    Accommodation: " + yn(data["company_accommodation"]) +
                "    Meals: " + yn(data["company_meals"])
            ),
            p("Check if already covered", CELL_SMALL),
        ],
        [p("Special Instructions", CELL_BOLD), p(data["special_instructions"] or "-"), p("")],
    ]

    story = []
    add_table(
        story,
        "TRAVEL AUTHORIZATION & CASH ADVANCE REQUEST",
        "For official business travel approval and estimated travel cash advance request.",
        "Form No: PNC-HR-TA-2025",
        rows,
    )
    story.append(Spacer(1, 5))

    sig_data = [
        [p("Approval Line", HEADER), p("Signature / Printed Name", HEADER), p("Date", HEADER)],
        [p("Requested by\n(Employee)", CELL), p("\n\n"), p("\n")],
        [p("Checked by\n(Admin / HR)", CELL), p("\n\n"), p("\n")],
        [p("Approved by\n(Department Head)", CELL), p("\n\n"), p("\n")],
    ]
    sig = Table(sig_data, colWidths=[56 * mm, 92 * mm, 37 * mm])
    sig.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, GRID),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, GRID),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6B7280")),
                ("BACKGROUND", (0, 1), (0, -1), LABEL_BG),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 1), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
            ]
        )
    )
    story.append(p("4. APPROVAL", CELL_BOLD))
    story.append(sig)
    story.append(Spacer(1, 3))
    story.append(p("Note: Original receipts and this approved form may be required for post-travel liquidation.", CELL_SMALL))

    doc.build(story)
    return buffer.getvalue()


def build_liquidation_pdf(data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=8 * mm,
        title="Travel Expense Liquidation & Trip Report",
    )

    settlement_text = (
        f"Amount Due to Employee: {peso_text(data['amount_due_employee'])}"
        if data["amount_due_employee"] > 0
        else f"Amount to be Returned by Employee: {peso_text(data['amount_to_return'])}"
    )

    attachments = []
    if data["attach_receipts"]:
        attachments.append("Original Receipts / ORs")
    if data["attach_approved_form"]:
        attachments.append("Approved Travel Form")
    if data["attach_other_support"]:
        attachments.append("Other Supporting Documents")
    attachment_text = ", ".join(attachments) if attachments else "None indicated"

    rows = [
        section_row("1. GENERAL INFORMATION"),
        [p("Employee Name", CELL_BOLD), p(data["employee_name"]), p("")],
        [p("Department / Position", CELL_BOLD), p(f"{data['department']} / {data['position']}"), p("")],
        [p("Travel Completion Date", CELL_BOLD), p(data["travel_completion_date"]), p("")],
        [p("Destination / Area Covered", CELL_BOLD), p(data["destination"]), p("")],
        [p("Trip Summary / Accomplishment", CELL_BOLD), p(data["trip_summary"]), p("Briefly state the result of the trip", CELL_SMALL)],
        section_row("2. TRAVEL ALLOWANCE / ADVANCE SETTLEMENT"),
        [p("No. of Nights", CELL_BOLD), p(f"{data['nights']} Night(s)"), p("")],
        [p("Approved / Applicable TA", CELL_BOLD), p(peso_text(data["approved_ta"])), p("Based on approved rate", CELL_SMALL)],
        [p("Less: Meals / Benefits Provided", CELL_BOLD), p(peso_text(data["less_meals"])), p("Deduct if company / hotel provided meals", CELL_SMALL)],
        [p("(A) Net TA Due", CELL_BOLD), p(peso_text(data["net_ta_due"]), CELL_BOLD), p("")],
        section_row("3. ACTUAL REIMBURSABLE EXPENSES"),
        [p("Transportation", CELL_BOLD), p(peso_text(data["transportation"])), p("Attach OR if applicable", CELL_SMALL)],
        [p("Accommodation", CELL_BOLD), p(peso_text(data["accommodation"])), p("Attach OR / hotel bill", CELL_SMALL)],
        [p("Other Approved Expense", CELL_BOLD), p(peso_text(data["other_expense"])), p("Tolls / fares / fuel / misc.", CELL_SMALL)],
        [p("(B) Subtotal Reimbursable", CELL_BOLD), p(peso_text(data["subtotal_reimbursable"]), CELL_BOLD), p("")],
        section_row("4. FINAL SETTLEMENT"),
        [p("Cash Advance Received", CELL_BOLD), p(peso_text(data["cash_advance_received"])), p("")],
        [p("TOTAL CLAIM (A + B)", CELL_BOLD), p(peso_text(data["total_claim"]), CELL_BOLD), p("")],
        [p("Settlement Result", CELL_BOLD), p(settlement_text), p("Calculated from Total Claim less Cash Advance", CELL_SMALL)],
        [p("Attachments Submitted", CELL_BOLD), p(attachment_text), p("Check all attached documents", CELL_SMALL)],
    ]

    story = []
    add_table(
        story,
        "TRAVEL EXPENSE LIQUIDATION & TRIP REPORT",
        "For post-travel accomplishment reporting and settlement of travel expenses / cash advance.",
        f"Ref. Approved Travel Form No: {data['reference_form_no']}",
        rows,
    )
    story.append(Spacer(1, 5))

    sig_data = [
        [p("Line", HEADER), p("Signature / Printed Name / Date", HEADER), p("Purpose", HEADER)],
        [p("Prepared by\n(Employee)", CELL), p("\n\n"), p("I certify this report and expenses are true and correct", CELL_SMALL)],
        [p("Checked by\n(Department Head)", CELL), p("\n\n"), p("Reviewed and verified", CELL_SMALL)],
        [p("Reviewed by\n(Accounting / Finance)", CELL), p("\n\n"), p("Final liquidation review", CELL_SMALL)],
    ]
    sig = Table(sig_data, colWidths=[56 * mm, 88 * mm, 41 * mm])
    sig.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.6, GRID),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, GRID),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6B7280")),
                ("BACKGROUND", (0, 1), (0, -1), LABEL_BG),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 1), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 10),
            ]
        )
    )
    story.append(p("5. SIGNATURES / VERIFICATION", CELL_BOLD))
    story.append(sig)
    story.append(Spacer(1, 3))
    story.append(p("Note: Any excess cash advance should be returned promptly upon liquidation, subject to company policy.", CELL_SMALL))

    doc.build(story)
    return buffer.getvalue()


def validate_authorization(data: dict) -> list[str]:
    errors = []
    required_text = {
        "Employee Name": data["employee_name"],
        "Department": data["department"],
        "Position": data["position"],
        "Destination": data["destination"],
        "Purpose of Travel": data["purpose"],
    }
    for label, value in required_text.items():
        if not str(value).strip():
            errors.append(f"{label} is required.")

    if data["return_date"] < data["departure_date"]:
        errors.append("Return date cannot be earlier than departure date.")

    if data["nights"] < 0:
        errors.append("No. of Nights cannot be negative.")

    if data["cash_advance_requested"] > data["total_estimated"]:
        errors.append("Cash Advance Requested cannot be greater than Total Estimated Cost.")

    return errors


def validate_liquidation(data: dict) -> list[str]:
    errors = []
    required_text = {
        "Reference Form No": data["reference_form_no"],
        "Employee Name": data["employee_name"],
        "Department": data["department"],
        "Position": data["position"],
        "Destination / Area Covered": data["destination"],
        "Trip Summary / Accomplishment": data["trip_summary"],
    }
    for label, value in required_text.items():
        if not str(value).strip():
            errors.append(f"{label} is required.")

    if data["nights"] < 0:
        errors.append("No. of Nights cannot be negative.")

    if data["cash_advance_received"] < 0:
        errors.append("Cash Advance Received cannot be negative.")

    return errors


st.title("PNC Travel Forms")
st.caption("Stage 1: Streamlit input -> A4 PDF output with required-field validation.")

with st.expander("How this stage works", expanded=False):
    st.write(
        "Fill in the form, click the PDF button, and the app will validate required items first. "
        "If anything important is missing, the app shows errors instead of generating the PDF."
    )


tab1, tab2 = st.tabs([
    "Travel Authorization & Cash Advance Request",
    "Travel Expense Liquidation & Trip Report",
])

with tab1:
    st.subheader("Pre-Travel Request")

    with st.form("authorization_form"):
        c1, c2 = st.columns(2)
        employee_name = c1.text_input("Employee Name *")
        department = c1.text_input("Department *")
        position = c2.text_input("Position *")
        request_date = c2.date_input("Date of Request", value=date.today())

        destination = st.text_input("Destination *")
        c3, c4, c5 = st.columns(3)
        departure_date = c3.date_input("Departure Date")
        return_date = c4.date_input("Return Date")
        nights = c5.number_input("No. of Nights", min_value=0, step=1, value=0)

        purpose = st.text_area("Purpose of Travel *", height=100)

        st.markdown("**Estimated Travel Cost**")
        d1, d2 = st.columns(2)
        ta_amount = d1.number_input("Travel Allowance (TA)", min_value=0.0, step=100.0, value=0.0)
        transport_amount = d2.number_input("Transportation", min_value=0.0, step=100.0, value=0.0)
        accommodation_amount = d1.number_input("Accommodation", min_value=0.0, step=100.0, value=0.0)
        other_amount = d2.number_input("Other Estimated Cost", min_value=0.0, step=100.0, value=0.0)
        cash_advance_requested = d1.number_input("Cash Advance Requested", min_value=0.0, step=100.0, value=0.0)

        st.markdown("**Policy Check**")
        overnight_travel = st.checkbox("Overnight Travel?")
        e1, e2, e3 = st.columns(3)
        company_transport = e1.checkbox("Transportation provided by company / hotel")
        company_accommodation = e2.checkbox("Accommodation provided by company / hotel")
        company_meals = e3.checkbox("Meals provided by company / hotel")
        special_instructions = st.text_area("Special Instructions", height=70)

        submitted_auth = st.form_submit_button("Generate Authorization PDF")

    total_estimated = money(ta_amount) + money(transport_amount) + money(accommodation_amount) + money(other_amount)
    st.info(f"Total Estimated Cost: {peso_text(total_estimated)}")

    if submitted_auth:
        auth_data = {
            "employee_name": employee_name,
            "department": department,
            "position": position,
            "request_date": request_date.strftime("%Y-%m-%d"),
            "destination": destination,
            "departure_date": departure_date.strftime("%Y-%m-%d"),
            "return_date": return_date.strftime("%Y-%m-%d"),
            "nights": int(nights),
            "purpose": purpose,
            "ta_amount": money(ta_amount),
            "transport_amount": money(transport_amount),
            "accommodation_amount": money(accommodation_amount),
            "other_amount": money(other_amount),
            "total_estimated": total_estimated,
            "cash_advance_requested": money(cash_advance_requested),
            "overnight_travel": overnight_travel,
            "company_transport": company_transport,
            "company_accommodation": company_accommodation,
            "company_meals": company_meals,
            "special_instructions": special_instructions,
        }
        errors = validate_authorization(auth_data)
        if errors:
            for err in errors:
                st.error(err)
        else:
            pdf_bytes = build_authorization_pdf(auth_data)
            st.success("PDF generated successfully.")
            st.download_button(
                "Download Authorization PDF",
                data=pdf_bytes,
                file_name="travel_authorization_request.pdf",
                mime="application/pdf",
            )

with tab2:
    st.subheader("Post-Travel Liquidation & Report")

    with st.form("liquidation_form"):
        a1, a2 = st.columns(2)
        reference_form_no = a1.text_input("Reference Approved Travel Form No. *")
        travel_completion_date = a2.date_input("Travel Completion Date", value=date.today())

        b1, b2 = st.columns(2)
        employee_name2 = b1.text_input("Employee Name *")
        department2 = b1.text_input("Department *")
        position2 = b2.text_input("Position *")
        destination2 = b2.text_input("Destination / Area Covered *")

        c1, c2 = st.columns(2)
        nights2 = c1.number_input("No. of Nights", min_value=0, step=1, value=0, key="nights2")
        approved_ta = c2.number_input("Approved / Applicable TA", min_value=0.0, step=100.0, value=0.0)
        less_meals = c1.number_input("Less: Meals / Benefits Provided", min_value=0.0, step=100.0, value=0.0)
        cash_advance_received = c2.number_input("Cash Advance Received", min_value=0.0, step=100.0, value=0.0)

        trip_summary = st.text_area("Trip Summary / Accomplishment *", height=100)

        st.markdown("**Actual Reimbursable Expenses**")
        d1, d2, d3 = st.columns(3)
        transportation = d1.number_input("Transportation", min_value=0.0, step=100.0, value=0.0)
        accommodation = d2.number_input("Accommodation", min_value=0.0, step=100.0, value=0.0)
        other_expense = d3.number_input("Other Approved Expense", min_value=0.0, step=100.0, value=0.0)

        st.markdown("**Attachments Submitted**")
        e1, e2, e3 = st.columns(3)
        attach_receipts = e1.checkbox("Original Receipts / ORs")
        attach_approved_form = e2.checkbox("Approved Travel Form")
        attach_other_support = e3.checkbox("Other Supporting Documents")

        submitted_liq = st.form_submit_button("Generate Liquidation PDF")

    net_ta_due = money(approved_ta) - money(less_meals)
    subtotal_reimbursable = money(transportation) + money(accommodation) + money(other_expense)
    total_claim = net_ta_due + subtotal_reimbursable
    difference = total_claim - money(cash_advance_received)
    amount_due_employee = difference if difference > 0 else Decimal("0")
    amount_to_return = abs(difference) if difference < 0 else Decimal("0")

    x1, x2, x3 = st.columns(3)
    x1.metric("Net TA Due", peso_text(net_ta_due))
    x2.metric("Subtotal Reimbursable", peso_text(subtotal_reimbursable))
    x3.metric("Total Claim", peso_text(total_claim))

    if amount_due_employee > 0:
        st.info(f"Settlement Result: Amount Due to Employee = {peso_text(amount_due_employee)}")
    else:
        st.info(f"Settlement Result: Amount to be Returned by Employee = {peso_text(amount_to_return)}")

    if submitted_liq:
        liq_data = {
            "reference_form_no": reference_form_no,
            "employee_name": employee_name2,
            "department": department2,
            "position": position2,
            "travel_completion_date": travel_completion_date.strftime("%Y-%m-%d"),
            "destination": destination2,
            "trip_summary": trip_summary,
            "nights": int(nights2),
            "approved_ta": money(approved_ta),
            "less_meals": money(less_meals),
            "net_ta_due": net_ta_due,
            "transportation": money(transportation),
            "accommodation": money(accommodation),
            "other_expense": money(other_expense),
            "subtotal_reimbursable": subtotal_reimbursable,
            "cash_advance_received": money(cash_advance_received),
            "total_claim": total_claim,
            "amount_due_employee": amount_due_employee,
            "amount_to_return": amount_to_return,
            "attach_receipts": attach_receipts,
            "attach_approved_form": attach_approved_form,
            "attach_other_support": attach_other_support,
        }
        errors = validate_liquidation(liq_data)
        if errors:
            for err in errors:
                st.error(err)
        else:
            pdf_bytes = build_liquidation_pdf(liq_data)
            st.success("PDF generated successfully.")
            st.download_button(
                "Download Liquidation PDF",
                data=pdf_bytes,
                file_name="travel_liquidation_report.pdf",
                mime="application/pdf",
            )

st.divider()
st.caption("Stage 2 can add email routing and approver action flow after this PDF version is finalized.")

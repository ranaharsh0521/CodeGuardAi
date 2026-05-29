import tempfile
import os
from app.schemas.analysis import ScanDetails


class ReportGenerator:
    def generate_pdf(self, scan_details: ScanDetails) -> str:
        """Generate a simple text-based PDF report without heavy dependencies."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            return self._generate_with_reportlab(scan_details)
        except ImportError:
            return self._generate_text_report(scan_details)

    def _generate_with_reportlab(self, scan_details: ScanDetails) -> str:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet

        fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("CodeGuard AI Scan Report", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Scan ID: {scan_details.scan_id}", styles["Normal"]))
        story.append(Paragraph(f"Status: {scan_details.status}", styles["Normal"]))
        story.append(Paragraph(f"Risk Score: {scan_details.risk_score}", styles["Normal"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Findings:", styles["Heading2"]))
        if scan_details.findings:
            data = [["Severity", "Tool", "Message", "File", "Line"]]
            for f in scan_details.findings:
                data.append([
                    f.severity.upper(), f.tool,
                    f.message[:60] + "..." if len(f.message) > 60 else f.message,
                    os.path.basename(f.file_path), str(f.line_number),
                ])
            table = Table(data, colWidths=[60, 60, 200, 120, 40])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No findings.", styles["Normal"]))
        doc.build(story)
        return pdf_path

    def _generate_text_report(self, scan_details: ScanDetails) -> str:
        """Fallback: plain-text report saved as .txt"""
        fd, txt_path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(f"CodeGuard AI Scan Report\n")
            f.write(f"========================\n")
            f.write(f"Scan ID   : {scan_details.scan_id}\n")
            f.write(f"Status    : {scan_details.status}\n")
            f.write(f"Risk Score: {scan_details.risk_score}\n\n")
            f.write(f"Findings ({len(scan_details.findings)}):\n")
            for finding in scan_details.findings:
                f.write(f"  [{finding.severity.upper()}] {finding.tool} - {finding.message} "
                        f"({finding.file_path}:{finding.line_number})\n")
        return txt_path

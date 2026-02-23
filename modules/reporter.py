import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER

class NarrativeReporter:
    @staticmethod
    def get_summary(results, inputs):
        sr = results['success_rate'] * 100
        if results['status'] == "GREEN":
            return f"🛡️ **Status: SECURE ({sr:.1f}%)**\nYour plan is highly resilient. Maintain current strategy."
        elif results['status'] == "YELLOW":
            return f"⚠️ **Status: CAUTION ({sr:.1f}%)**\nPlan is fragile. Consider delaying SS or increasing savings."
        return f"🚨 **Status: CRITICAL ({sr:.1f}%)**\nHigh depletion risk. Immediate adjustments required."

class ReportGenerator:
    @staticmethod
    def create_pdf(inputs, success_rate):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=LETTER)
        p.drawString(100, 750, f"Aegis Strategy Report - Success: {success_rate*100:.1f}%")
        p.save()
        buffer.seek(0)
        return buffer
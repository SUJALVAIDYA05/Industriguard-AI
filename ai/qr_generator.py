import qrcode
import json
import os
from PIL import Image, ImageDraw, ImageFont

class QRGenerator:
    def __init__(
        self,
        employees_file="employee_data/employees.json",
        output_dir="employee_data/qr_cards"
    ):
        self.employees_file = employees_file
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def load_employees(self):
        with open(self.employees_file, "r") as f:
            data = json.load(f)
        return data["employees"]

    def generate_qr(self, employee_id):
        """
        Generates a QR code image for an employee ID.
        The QR code encodes the employee ID string directly.
        Example: scanning returns "EMP-001"
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4
        )
        qr.add_data(employee_id)
        qr.make(fit=True)

        qr_image = qr.make_image(
            fill_color="black",
            back_color="white"
        ).convert("RGB")

        return qr_image

    def create_id_card(self, employee):
        """
        Creates a full printable ID card with:
        - Employee name and details
        - QR code
        - IndustriGuard branding
        """
        # Card dimensions (in pixels at 96dpi)
        card_width  = 400
        card_height = 550

        # Create blank white card
        card = Image.new("RGB", (card_width, card_height), color=(255, 255, 255))
        draw = ImageDraw.Draw(card)

        # ── Header banner ─────────────────────────────────────────
        draw.rectangle([(0, 0), (card_width, 80)], fill=(20, 60, 120))
        draw.text(
            (card_width // 2, 25),
            "IndustriGuard AI",
            fill=(255, 255, 255),
            anchor="mm"
        )
        draw.text(
            (card_width // 2, 55),
            "Employee Safety ID",
            fill=(180, 200, 255),
            anchor="mm"
        )

        # ── Employee info ─────────────────────────────────────────
        draw.text(
            (card_width // 2, 110),
            employee["id"],
            fill=(20, 60, 120),
            anchor="mm"
        )
        draw.text(
            (card_width // 2, 145),
            employee["name"],
            fill=(30, 30, 30),
            anchor="mm"
        )
        draw.text(
            (card_width // 2, 175),
            f'{employee["role"]}',
            fill=(80, 80, 80),
            anchor="mm"
        )
        draw.text(
            (card_width // 2, 200),
            f'Dept: {employee["department"]}',
            fill=(80, 80, 80),
            anchor="mm"
        )

        # ── Divider line ──────────────────────────────────────────
        draw.line([(30, 220), (370, 220)], fill=(200, 200, 200), width=1)

        # ── QR Code ───────────────────────────────────────────────
        qr_image = self.generate_qr(employee["id"])
        qr_image = qr_image.resize((220, 220))
        qr_x = (card_width - 220) // 2
        card.paste(qr_image, (qr_x, 235))

        # ── Footer ────────────────────────────────────────────────
        draw.rectangle(
            [(0, card_height - 50), (card_width, card_height)],
            fill=(240, 240, 240)
        )
        draw.text(
            (card_width // 2, card_height - 25),
            "Scan QR code before entering work area",
            fill=(120, 120, 120),
            anchor="mm"
        )

        return card

    def generate_all(self):
        """Generates ID cards for all employees in JSON file"""
        employees = self.load_employees()

        print(f"\n[QRGenerator] Generating ID cards for {len(employees)} employees...\n")

        for emp in employees:
            card = self.create_id_card(emp)
            filename = f'{emp["id"]}_{emp["name"].replace(" ", "_")}.png'
            filepath = os.path.join(self.output_dir, filename)
            card.save(filepath)
            print(f"  ✓ Generated: {filename}")

        print(f"\n[QRGenerator] All cards saved to → {self.output_dir}/\n")


# ── Run directly to generate all cards ────────────────────────────
if __name__ == "__main__":
    generator = QRGenerator(
        employees_file="../employee_data/employees.json",
        output_dir="../employee_data/qr_cards"
    )
    generator.generate_all()
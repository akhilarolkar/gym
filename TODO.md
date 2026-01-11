# TODO: Create Invoice-like PDFs for Members

## Completed Tasks
- [x] Added ReportLab to requirements.txt for PDF generation
- [x] Added ReportLab imports to views.py
- [x] Created generate_invoice_pdf view function with:
  - Member information section
  - Membership details section
  - Charges calculation with pricing per membership type
  - Professional PDF layout with tables and styling
- [x] Added URL pattern for PDF generation
- [x] Installed dependencies (in progress)

## Remaining Tasks
- [ ] Test the PDF generation functionality
- [ ] Add a "Generate Invoice" button to the member list template
- [ ] Verify PDF downloads correctly
- [ ] Test with different membership types and durations

## Notes
- Membership pricing: strength ($50/month), cardio ($40/month), crossfit ($60/month)
- PDF includes invoice number, date, member details, membership info, and calculated charges
- Uses professional styling with tables and proper formatting

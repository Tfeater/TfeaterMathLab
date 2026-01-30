# PDF Export (`pdf_export.py`, `pdf_generator_reportlab.py`)

The PDF export pipeline turns solved calculations into portable,
professional‑looking PDF documents.

## `pdf_export.py`

Defines three main views:

- `ExportPDFView` – exports a specific `Calculation` by ID.
- `ExportCurrentPDFView` – exports the most recent calculation for the
  current user (or anonymous session).
- `export_history_pdf` – exports a group of calculations, defaulting to
  the latest 10 if no explicit IDs are given.

These views:

- Retrieve the relevant `Calculation` instances with proper access control.
- Use `generate_pdf_from_calculation_model` or inline ReportLab code
  to render pages.
- Return `HttpResponse` objects with `Content-Type: application/pdf` and
  appropriate `Content-Disposition` headers for download.

## `pdf_generator_reportlab.py`

Encapsulates the layout logic for single‑calculation PDFs:

- Renders:
  - Operation type and metadata.
  - Original input expression.
  - Result in a highlighted box.
  - Optional steps, explanation text, and any other annotations.
- Uses ReportLab primitives (paragraphs, spacers, styles) for a clean,
  print‑friendly design.

## Error handling and guarantees

- If PDF generation dependencies are missing, views return a 500 status
  with a clear message instead of crashing.
- If the requested calculation does not exist or is not owned by the
  user, a 404 is returned.
- PDFs are generated only for successful calculations; error states do
  not produce misleading documents.


from xhtml2pdf import pisa


def generate_report_pdf(source_html, output_filename):
    result_file = open(output_filename, "w+b")
    pisa_status = pisa.CreatePDF(
        source_html,
        dest=result_file,
        encoding="utf-8",
    )
    result_file.close()
    return pisa_status.err


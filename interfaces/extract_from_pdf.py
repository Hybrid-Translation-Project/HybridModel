import library


def pdf_to_text(pdf_path: str) -> str:
    text = ""
    with library.pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def save_txt(text: str, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


# UI'nin çağıracağı tek fonksiyon
def extract_pdf_to_txt(input_path: str, output_txt_path: str) -> None:
    text = pdf_to_text(input_path)
    save_txt(text, output_txt_path)


if __name__ == "__main__":
    # Manuel test (isteğe bağlı)
    sample_in = r"samples\sample.pdf"
    sample_out = r"outputs\outputPdf.txt"
    extract_pdf_to_txt(sample_in, sample_out)
    print(f"OK: {sample_out}")

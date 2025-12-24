import library


def docx_to_text(docx_path: str) -> str:
    doc = library.Document(docx_path)
    return "\n".join(p.text for p in doc.paragraphs)


def save_txt(text: str, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


# UI'nin çağıracağı tek fonksiyon
def extract_docx_to_txt(input_path: str, output_txt_path: str) -> None:
    text = docx_to_text(input_path)
    save_txt(text, output_txt_path)


if __name__ == "__main__":
    # Manuel test (isteğe bağlı): bu blok sadece dosya direkt çalıştırılırsa çalışır.
    sample_in = r"samples\demo.docx"
    sample_out = r"outputs\outputDoc.txt"
    extract_docx_to_txt(sample_in, sample_out)
    print(f"OK: {sample_out}")

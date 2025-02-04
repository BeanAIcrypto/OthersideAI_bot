import zipfile
import rarfile
import py7zr
import tarfile
import os
import PyPDF2
from docx import Document
from odf.opendocument import load
from odf.text import P
import pandas as pd
from pptx import Presentation
import logging
from bs4 import BeautifulSoup
import email
import mimetypes


logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text


def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def extract_text_from_odt(file_path):
    doc = load(file_path)
    texts = [element for element in doc.getElementsByType(P)]
    return "\n".join([text.firstChild.data for text in texts if text.firstChild is not None])


def extract_text_from_excel(file_path):
    df = pd.read_excel(file_path)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    df = df.dropna(how='all').dropna(axis=1, how='all')
    markdown_table = df.to_markdown(index=False)
    return markdown_table


def extract_text_from_presentation(file_path):
    presentation = Presentation(file_path)
    text = []
    for slide in presentation.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text.append(shape.text)
    return "\n".join(text)


def extract_text_from_zip(file_path):
    extracted_text = []
    with zipfile.ZipFile(file_path, 'r') as archive:
        for file in archive.namelist():
            mime_type = mimetypes.guess_type(file)[0]

            if mime_type in text_extraction_from_a_document:
                with archive.open(file) as f:
                    text_extraction_function = text_extraction_from_a_document[mime_type]
                    extracted_text.append(text_extraction_function(f))
            else:
                logger.error(f"ZIP архив содержит неподдерживаемый формат: {file} (MIME-тип: {mime_type})")
                continue
    return "\n".join(extracted_text)


def extract_text_from_rar(file_path):
    extracted_text = []
    with rarfile.RarFile(file_path, 'r') as archive:
        for file in archive.infolist():
            mime_type = mimetypes.guess_type(file.filename)[0]
            if mime_type in text_extraction_from_a_document:
                extracted_text.append(text_extraction_from_a_document[mime_type](archive.open(file.filename)))
            else:
                logger.error(f"RAR архив содержит неподдерживаемый формат: {file.filename} (MIME-тип: {mime_type})")
                continue
    return "\n".join(extracted_text)


def extract_text_from_7z(file_path):
    extracted_text = []
    with py7zr.SevenZipFile(file_path, mode='r') as archive:
        archive.extractall(path="tmp")
        for root, dirs, files in os.walk("tmp"):
            for file in files:
                mime_type = mimetypes.guess_type(file)[0]

                if mime_type in text_extraction_from_a_document:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        text_extraction_function = text_extraction_from_a_document[mime_type]
                        extracted_text.append(text_extraction_function(f))
                else:
                    logger.error(f"7Z архив содержит неподдерживаемый формат: {file} (MIME-тип: {mime_type})")
                    continue
    return "\n".join(extracted_text)


def extract_text_from_tar(file_path):
    extracted_text = []
    with tarfile.open(file_path, 'r') as archive:
        for member in archive.getmembers():
            if member.isfile():
                mime_type = mimetypes.guess_type(member.name)[0]

                if mime_type in text_extraction_from_a_document:
                    with archive.extractfile(member) as f:
                        text_extraction_function = text_extraction_from_a_document[mime_type]
                        extracted_text.append(text_extraction_function(f))
                else:
                    logger.error(f"TAR архив содержит неподдерживаемый формат: {member.name} (MIME-тип: {mime_type})")
                    continue
    return "\n".join(extracted_text)


def extract_text_from_mhtml(file_path):
    try:
        with open(file_path, 'rb') as file:
            msg = email.message_from_binary_file(file)
            extracted_text = []

            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type in ['text/plain', 'text/html']:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset()
                        if charset:
                            text = payload.decode(charset, errors='ignore')
                        else:
                            text = payload.decode('utf-8', errors='ignore')
                        if content_type == 'text/html':
                            soup = BeautifulSoup(text, 'html.parser')
                            text = soup.get_text(separator='\n')

                        extracted_text.append(text.strip())
            if extracted_text:
                return '\n'.join(extracted_text)
            else:
                logger.error(f"Не удалось извлечь текст из MHTML файла: {file_path}")
                return ""
    except Exception as e:
        logger.error(f"Ошибка при обработке MHTML файла: {e}")
        return ""

def extract_text_from_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


text_extraction_from_a_document = {
    'application/pdf': extract_text_from_pdf,
    'text/plain': extract_text_from_txt,
    'application/msword': extract_text_from_docx,
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': extract_text_from_docx,
    'application/vnd.oasis.opendocument.text': extract_text_from_odt,
    'application/vnd.ms-excel': extract_text_from_excel,
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': extract_text_from_excel,
    'application/vnd.oasis.opendocument.spreadsheet': extract_text_from_excel,
    'application/vnd.ms-powerpoint': extract_text_from_presentation,
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': extract_text_from_presentation,
    'application/vnd.oasis.opendocument.presentation': extract_text_from_presentation,
    'application/zip': extract_text_from_zip,
    'application/x-rar-compressed': extract_text_from_rar,
    'application/x-7z-compressed': extract_text_from_7z,
    'application/x-tar': extract_text_from_tar,
    'application/gzip': extract_text_from_tar,
    'application/x-bzip2': extract_text_from_tar,
    'text/markdown': extract_text_from_markdown,
    'application/x-mimearchive': extract_text_from_mhtml,
    'text/html': extract_text_from_mhtml,

}
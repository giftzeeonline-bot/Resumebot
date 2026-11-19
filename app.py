from pathlib import Path
import re
import shutil

import pymupdf as fitz
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

from synthetic_resumes import create_resume_archive


DATASET_HANDLE = "hadikp/resume-data-pdf"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_DATASET_DIR = Path("data/resume-data-pdf")


def get_pdf_signature(directory: str) -> tuple[tuple[str, int, int], ...]:
    root = Path(directory).expanduser()
    if not root.is_dir():
        raise ValueError(f"Dataset folder does not exist: {root}")

    pdfs = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf"),
        key=str,
    )
    if not pdfs:
        raise ValueError(f"No PDF resumes found in {root}")
    return tuple((str(path), path.stat().st_mtime_ns, path.stat().st_size) for path in pdfs)


@st.cache_data(show_spinner=False)
def load_resumes(
    file_signature: tuple[tuple[str, int, int], ...]
) -> tuple[list[dict[str, str]], int]:
    resumes = []
    unreadable_count = 0
    for path_string, _, _ in file_signature:
        path = Path(path_string)
        try:
            with fitz.open(path) as document:
                page_text = []
                for page in document:
                    text = page.get_text().strip()
                    if len(text) < 30:
                        if not shutil.which("tesseract"):
                            raise ValueError(
                                "Scanned PDFs need Tesseract OCR. Install Tesseract and "
                                "its English language data, then try again."
                            )
                        try:
                            text = page.get_text(
                                textpage=page.get_textpage_ocr(language="eng", dpi=150)
                            ).strip()
                        except RuntimeError as error:
                            raise ValueError(
                                "Tesseract OCR failed. Check that the English language "
                                "data is installed, then try again."
                            ) from error
                    page_text.append(text)

            text = "\n".join(page_text).strip()
            if text:
                resumes.append(
                    {
                        "filename": path.name,
                        "category": path.parent.name,
                        "path": str(path),
                        "text": text,
                    }
                )
            else:
                unreadable_count += 1
        except fitz.FileDataError:
            unreadable_count += 1

    return resumes, unreadable_count


def split_into_chunks(text: str, words_per_chunk: int = 100) -> list[str]:
    words = re.findall(r"\S+", text)
    if not words:
        return []
    step = max(1, words_per_chunk - 20)
    return [" ".join(words[start : start + words_per_chunk]) for start in range(0, len(words), step)]


@st.cache_resource(show_spinner="Loading the local AI model...")
def load_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def rank_resumes(
    job_description: str, resumes: list[dict[str, str]], model: SentenceTransformer
) -> list[dict[str, str | float]]:
    chunks = []
    owners = []
    for index, resume in enumerate(resumes):
        for chunk in split_into_chunks(resume["text"]):
            chunks.append(chunk)
            owners.append(index)

    if not chunks:
        return []

    query_embedding = model.encode(
        job_description, convert_to_numpy=True, normalize_embeddings=True
    )
    chunk_embeddings = model.encode(
        chunks,
        batch_size=32,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    chunk_scores = chunk_embeddings @ query_embedding

    best_scores = np.full(len(resumes), -1.0)
    best_chunks = [""] * len(resumes)
    for chunk, owner, score in zip(chunks, owners, chunk_scores):
        if score > best_scores[owner]:
            best_scores[owner] = float(score)
            best_chunks[owner] = chunk

    ranked = []
    for index, resume in enumerate(resumes):
        ranked.append(
            {
                **resume,
                "score": float(best_scores[index]),
                "excerpt": best_chunks[index],
            }
        )
    return sorted(ranked, key=lambda resume: resume["score"], reverse=True)[:10]


st.set_page_config(page_title="Resume Search", page_icon="📄", layout="wide")
st.title("AI Resume Search")
st.write(
    "Find the ten resumes most relevant to a job description. Matching runs locally; "
    "resume contents are not sent to an external AI service."
)
st.info(
    "Use the ranking as a review aid, not as an automated hiring decision. "
    "Scores are relevance estimates, not probabilities."
)

if "dataset_directory" not in st.session_state:
    st.session_state.dataset_directory = str(DEFAULT_DATASET_DIR)

with st.sidebar:
    st.header("Resume dataset")
    dataset_directory = st.text_input(
        "Folder containing PDF resumes",
        key="dataset_directory",
        help="The app searches this folder and its subfolders.",
    )

    if st.button("Download dataset from Kaggle", use_container_width=True):
        import kagglehub

        with st.spinner("Downloading the Kaggle dataset (about 2.14 GB)..."):
            downloaded_directory = kagglehub.dataset_download(DATASET_HANDLE)
        st.session_state.dataset_directory = downloaded_directory
        st.success(f"Dataset downloaded to {downloaded_directory}")
        st.rerun()

    st.caption(
        "Downloading requires Kaggle API credentials and acceptance of the dataset terms. "
        "You can also download it from Kaggle and enter its folder above."
    )

with st.expander("Create fictional test resumes"):
    st.write(
        "Generate 100 synthetic, clearly labeled resumes as two-page PDFs in a ZIP. "
        "They are useful for testing search and are not real candidate records."
    )
    if st.button("Generate 100 sample resumes"):
        with st.spinner("Creating 100 fictional resume PDFs..."):
            st.session_state.sample_resume_archive = create_resume_archive()
    if "sample_resume_archive" in st.session_state:
        st.download_button(
            "Download 100 resumes (ZIP)",
            data=st.session_state.sample_resume_archive,
            file_name="synthetic_resumes.zip",
            mime="application/zip",
        )

job_description = st.text_area(
    "Job description",
    height=220,
    placeholder="Paste the role, responsibilities, required skills, and experience...",
)

if st.button("Find top 10 resumes", type="primary", disabled=not job_description.strip()):
    try:
        file_signature = get_pdf_signature(dataset_directory)
        with st.spinner("Reading resumes (scanned PDFs may require OCR)..."):
            resumes, unreadable_count = load_resumes(file_signature)
    except ValueError as error:
        st.error(str(error))
    else:
        if unreadable_count:
            st.warning(
                f"{unreadable_count} PDF(s) were empty or unreadable and were not ranked."
            )
        if not resumes:
            st.error(
                "No resume text could be extracted. Install Tesseract OCR and make sure "
                "the English language data is available, then try again."
            )
        else:
            with st.spinner("Comparing the job description with resumes..."):
                model = load_model()
                results = rank_resumes(job_description, resumes, model)

            if not results:
                st.error("No readable resume text was available to rank.")
            else:
                st.subheader("Top 10 matches")
                st.caption(
                    f"Ranked {len(resumes)} readable resumes. "
                    "The first use downloads the local embedding model."
                )
                for rank, resume in enumerate(results, start=1):
                    with st.expander(
                        f"{rank}. {resume['filename']} · {resume['category']} · "
                        f"Similarity {resume['score']:.3f}"
                    ):
                        st.write(resume["excerpt"])
                        with open(resume["path"], "rb") as pdf_file:
                            st.download_button(
                                "Download resume",
                                data=pdf_file.read(),
                                file_name=resume["filename"],
                                mime="application/pdf",
                                key=f"download-{rank}-{resume['path']}",
                            )

# AI Resume Search

A local Streamlit app that ranks PDF resumes against a job description using
sentence embeddings from `all-MiniLM-L6-v2`. It returns up to ten matches,
shows the best-matching text excerpt, and lets you download each resume.
Resume contents stay on your machine; the embedding model is downloaded
separately the first time you search.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For scanned PDFs, install Tesseract OCR and its English language data. For
example, on Debian/Ubuntu:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

## Get the dataset

In the app, select **Download dataset from Kaggle**. This dataset is about
2.14 GB and requires Kaggle API credentials and acceptance of its terms. Set
up credentials using Kaggle's documented API authentication, then restart the
app. Alternatively, download
[Resume Dataset PDF on Kaggle](https://www.kaggle.com/datasets/hadikp/resume-data-pdf)
yourself and enter the extracted folder in the app's sidebar.

## Usage and limitations

Paste a job description and select **Find top 10 resumes**. The app searches
PDFs in the selected folder and its subfolders. Scanned pages are OCR-processed
locally. OCR requires Tesseract; the first model load requires an internet
connection.

Relevance scores are approximate similarity estimates, not probabilities or
recommendations to hire. Use them only to assist human review, and assess
candidates based on job-related criteria.

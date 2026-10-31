# Proyek Analisis Data: E-Commerce Public Dataset
- **Nama:** Indah Putri Lestari
- **Email:** indahptr401@gmail.com
- **ID Dicoding:** indah_putri_lestari

## Struktur Folder
```
submission
├── dashboard
│   ├── dashboard.py
│   ├── main_data.csv
│   └── state_geo.csv
├── data
│   └── (9 file CSV dataset Olist)
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment - Anaconda
```
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run Streamlit App
Jalankan dari folder utama proyek (yang berisi `requirements.txt`):
```
streamlit run dashboard/dashboard.py
```

## Dashboard Online
[https://[nama-app-kamu].streamlit.app](https://submissionkelasbelajarfundamentalindah-mh3cqeqf56zvioxzswivwl.streamlit.app/)

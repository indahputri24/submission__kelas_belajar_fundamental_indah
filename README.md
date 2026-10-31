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
├── data/
│   ├── customers_dataset.csv
│   ├── geolocation_dataset.csv
│   ├── order_items_dataset.csv
│   ├── order_payments_dataset.csv
│   ├── order_reviews_dataset.csv
│   ├── orders_dataset.csv
│   ├── product_category_name_translation.csv
│   ├── products_dataset.csv
│   └── sellers_dataset.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment - Anaconda
```
conda create --name main-ds python=3.11
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```
cd submission
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run Streamlit App
```
streamlit run dashboard/dashboard.py
```

## Dashboard Online
https://submissionkelasbelajarfundamentalindah-mh3cqeqf56zvioxzswivwl.streamlit.app/



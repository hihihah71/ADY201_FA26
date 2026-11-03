# 01 — Cài đặt và cấu trúc project

## Yêu cầu

- Python 3.11 trở lên.
- PowerShell trên Windows cho các lệnh trong tài liệu.
- OSM PBF và Overture GeoParquet theo đúng đường dẫn chuẩn.

## Cài đặt editable

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

`pip install -e .` tạo lệnh `ady201` và cho phép thay đổi code trong `src/` mà không phải cài lại sau mỗi lần sửa.

## Kiểm tra

```powershell
ady201 --version
ady201 --help
python -c "from ady201.evaluation import SuitabilityModel; print('ok')"
```

## Cấu trúc package

```text
src/ady201/
├── __init__.py          # phiên bản package
├── __main__.py          # python -m ady201
├── main.py              # CLI
├── overture.py          # tải Places Việt Nam
├── poi.py               # POI feature Overture
├── grid_cell.py         # grid vuông 200 m
├── network.py           # road feature OSM
├── feature_process.py   # ghép và fill missing
├── regions.py           # pipeline một region
├── evaluation.py        # suitability model
├── database.py          # DuckDB phụ trợ
├── osm_input.py         # kiểm tra OSM, chưa hoàn thiện
└── analys.py            # helper cũ, không thuộc luồng chính
```

## Entry points

Hai cách gọi CLI tương đương:

```powershell
ady201 --help
python -m ady201 --help
```

Giao diện là entry point riêng:

```powershell
streamlit run app.py
```

## Dependency chính

- `pyrosm`: đọc OSM PBF.
- `geopandas`, `shapely`, `pyproj`: xử lý không gian.
- `scipy`: KD-tree cho radius và nearest.
- `duckdb`, `pyarrow`: tải/lưu/query Parquet.
- `streamlit`, `pydeck`: giao diện và bản đồ.

## File tự sinh

`.venv/`, `__pycache__/`, `*.egg-info/`, `data/raw/`, `data/processed/` và database cục bộ đã được `.gitignore` loại khỏi Git.

## Kiểm tra sau thay đổi

```powershell
python -m compileall -q src app.py
ady201 --help
```

Khi sửa giao diện:

```powershell
streamlit run app.py --server.headless true
```

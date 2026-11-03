# 08 — Chiều dài và mật độ đường quanh cell

## Nguồn

Mạng đường lấy từ `data/raw/osm/vietnam-261014.osm.pbf` với:

```python
network_type="walking"
```

## Bán kính

Pipeline tính hai bộ feature:

- 500 m.
- 1000 m.

## Luồng tính

1. Tạo buffer quanh geometry cell.
2. Clip buffer theo boundary tỉnh/thành.
3. Overlay đường với từng buffer.
4. Tính chiều dài mỗi đoạn giao bằng CRS mét.
5. Cộng chiều dài theo `cell_id`.
6. Chia cho diện tích buffer thực sau clip.

## Công thức

```text
road_length_km = tổng chiều dài road intersection / 1000

road_density_km_per_km2 = road_length_km / buffer_area_km2
```

## Cột output

```text
road_length_500m_km
road_density_500m_km_per_km2
road_length_1000m_km
road_density_1000m_km_per_km2
```

## Kiểm tra

```python
columns = [
    "road_length_500m_km",
    "road_density_500m_km_per_km2",
    "road_length_1000m_km",
    "road_density_1000m_km_per_km2",
]

assert road_features["cell_id"].is_unique
assert road_features[columns].ge(0).all().all()
```

## Lưu ý hiệu năng

Đây thường là bước chạy lâu nhất vì `gpd.overlay()` phải cắt nhiều đoạn đường với nhiều buffer. CLI chưa có progress bar cho bước này.

`network.py` hiện đọc mạng đường từ reader OSM toàn quốc trong `get_road_features()`. Cần thận trọng khi mở rộng batch nhiều tỉnh vì thời gian và bộ nhớ có thể lớn.

## Lưu ý boundary

Buffer sát biên bị clip, vì vậy diện tích mẫu số nhỏ hơn hình tròn đầy đủ. Đây là chủ ý để mật độ chỉ phản ánh phần nằm trong vùng nghiên cứu.

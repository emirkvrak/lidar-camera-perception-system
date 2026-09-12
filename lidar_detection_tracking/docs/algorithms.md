# LiDAR İşleme Katkılarım

Bu klasördeki örnekler, kurumsal projeye ait gerçek veri dosyasını veya özel
uygulama kodunu içermez. Amaç, LiDAR noktaları üzerinde geliştirdiğim işleme
adımlarını bağımsız ve tekrar çalıştırılabilir biçimde anlatmaktır.

## 1. Filtreleme ve ön işleme

- Yükseklik filtresiyle zemin ve geçersiz yükseklikteki noktalar elenir.
- İleri mesafe filtresiyle analiz menzili sınırlandırılır.
- Şerit/yol filtresiyle yalnızca çalışma alanındaki noktalar tutulur.
- `SHRINK` değeriyle şerit kenarlarından gelen noktalar azaltılır.
- Ağırlıklı voxel filtresinde aynı voxel içindeki noktalar birleştirilir.
- Photon count değeri, voxel merkezinin ağırlığını belirler.
- Boş veri güvenli biçimde işlenir.

## 2. Nesne tespiti

DBSCAN ile komşu noktalar kümelenir. Gürültü etiketi `-1` olan noktalar
ayrılır. Her geçerli küme için merkez, standart sapma, 2D/3D sınırlar ve
takip sisteminin kullanacağı `[forward, lateral]` ölçümü üretilir.

## 3. Nesne takibi

Her nesne için durum vektörü şu yapıdadır:

```text
[forward, lateral, forward_velocity, lateral_velocity]
```

Kalman filtresi bir sonraki konumu tahmin eder. Hungarian Algorithm, tahmin
edilen takipleri yeni tespitlerle mesafe maliyeti üzerinden eşleştirir.
Hız ölçümü low-pass filtreyle yumuşatılır; kayıp takipler belirlenen kayıp
sayısına göre korunur veya silinir.

## Çalıştırma

Gerçek kurumsal `lidar_detection_tracking.py` ve `shared_data/lidar.data`
yerine sentetik veri kullanan demo çalıştırılabilir:

```powershell
python -m examples.synthetic_pipeline_demo
```

Bu demo, gerçek verinin veya kurumsal uygulamanın paylaşılmasını gerektirmez.

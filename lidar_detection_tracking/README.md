# LiDAR Nesne Tespiti ve Takibi — Açık Algoritmalar

Bu klasör, LiDAR noktaları üzerinde geliştirdiğim filtreleme, nesne tespiti
ve çoklu nesne takip algoritmalarını kurumsal uygulama kodundan bağımsız olarak
göstermek için hazırlanmıştır.

## Katkılarım

- Yükseklik, ileri mesafe ve şerit/yol alanı filtreleri
- Şerit kenarı daraltma (`SHRINK`)
- Photon count ağırlıklı voxel filtreleme
- DBSCAN tabanlı nokta kümelendirme
- Gürültü ayıklama ve minimum küme kontrolü
- Nesne merkezi, standart sapma ve bounding box çıkarımı
- Kalman filtreli konum tahmini
- Hız hesabı, low-pass yumuşatma ve hız değişimi sınırlandırma
- Hungarian Algorithm ile track–detection eşleştirme
- Track oluşturma, doğrulama, kayıp track yönetimi ve ID yönetimi

## Klasör yapısı

- `public_algorithms/preprocessing.py`: filtreleme ve voxel işlemleri
- `public_algorithms/detection.py`: DBSCAN ve nesne bilgisi çıkarımı
- `public_algorithms/tracking.py`: Kalman ve çoklu nesne takip akışı
- `examples/synthetic_pipeline_demo.py`: örnek veriyle çalışan demo
- `docs/algorithms.md`: algoritmaların teknik açıklaması

Orijinal `lidar_detection_tracking.py` dosyası kurumsal/özel uygulama kodu
içerdiği için GitHub paylaşımının dışında tutulur. Bu klasördeki örnekler,
aynı teknik katkıları özel veri veya uygulama bağımlılığı olmadan sunar.

## Çalıştırma

```powershell
python -m pip install -r requirements.txt
python -m examples.synthetic_pipeline_demo
```

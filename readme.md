# 🚘 LiDAR & Kamera Sensör Füzyonu ve Çoklu Nesne Takip Sistemi

Bu proje, otonom araç algı sistemlerinin (Perception Stack) temel bileşenlerini simüle eden; gerçek zamanlı **LiDAR nokta bulutu işleme**, **yoğunluk tabanlı kümeleme**, **çoklu nesne takibi** ve **kamera–LiDAR sensör füzyonu** gerçekleştiren modüler ve ölçeklenebilir bir yazılım mimarisidir.

Sistem, 3D uzaydaki nesneleri tespit eder, takip eder, hızlarını tahmin eder ve LiDAR verisini kalibre edilmiş kamera görüntüsü üzerine projekte eder.

---

# 🎯 Sistem Yetkinlikleri

- Gerçek zamanlı LiDAR veri işleme
- DBSCAN ile nesne kümeleme
- Kalman Filter tabanlı hareket tahmini
- Hungarian Algorithm ile veri ilişkilendirme
- Track yaşam döngüsü yönetimi
- 3D → 2D projeksiyon (sensör füzyonu)
- Gürültü filtreleme ve performans optimizasyonu
- Pygame tabanlı analiz ve görselleştirme arayüzü

---

# 📸 Ekran Görüntüleri

![Resim 1](/image/Resim(1).png)

---

![Resim 2](/image/Resim(2).png)

---

![Resim 3](/image/Resim(3).png)

---

![Resim 4](/image/Resim(4).png)

---

![Resim 5](/image/Resim(5).png)

---

![Resim 6](/image/Resim(6).png)

---

![Resim 7](/image/Resim(7).png)

---

![Resim 8](/image/Resim(8).png)

---


# 🧠 Sistem Mimarisi ve Algoritmalar

## 1️⃣ Ham Veri İşleme

- Binary LiDAR veri okuma
- Polar → Kartezyen (XYZ) dönüşüm
- Gerçek zamanlı veri akışı yönetimi

---

## 2️⃣ Ön İşleme (Preprocessing)

### 🔹 Voxel Grid Filter
- Nokta bulutu yoğunluğunu azaltır
- Hesaplama maliyetini düşürür
- Gürültüyü filtreler

### 🔹 ROI (Region of Interest)
- Yol ve kritik alanları sınırlar
- Gereksiz veri işlenmesini engeller
- Performansı artırır

---

## 3️⃣ Kümeleme (Clustering)

### 🔹 DBSCAN (Density-Based Spatial Clustering)

- Yoğunluk tabanlı nesne ayrıştırma
- Gürültü noktalarının otomatik elenmesi
- Araç / yaya / engel ayrımı için temel segmentasyon

---

## 4️⃣ Çoklu Nesne Takibi (Multi-Object Tracking)

### 🔹 Kalman Filter
- Hareket modeli tabanlı tahmin
- Ölçüm gürültüsünün azaltılması
- Hız ve konum kestirimi

### 🔹 Hungarian Algorithm
- Veri ilişkilendirme (Data Association)
- Algılanan kümelerin mevcut track’lerle eşleştirilmesi

### 🔹 Track Lifecycle Management
- Birth (Yeni track oluşturma)
- Tracking (Aktif takip)
- Death (Zaman aşımı ile silinme)

---

## 5️⃣ Sensör Füzyonu

- LiDAR + endüstriyel kamera entegrasyonu
- 3D Dünya Koordinatları → 2D Piksel Koordinatları dönüşümü
- Intrinsic & Extrinsic kalibrasyon desteği
- Homojen dönüşüm matrisi kullanımı
- Projeksiyon doğrulama mekanizması

---

# 🏗 Mimari Tasarım

Proje iki farklı mimari yaklaşımı desteklemektedir:

## 🔹 Monolitik Prototip

- `lidar.py`
- Hızlı algoritma testleri
- Ar-Ge ve prototipleme amacıyla geliştirilmiştir

## 🔹 Clean Architecture Tabanlı Yapı (`src/`)

- `domain/` → Veri modelleri ve temel varlıklar  
- `core/` → İş mantığı ve projeksiyon algoritmaları  
- `infrastructure/` → Sensör sürücüleri ve dış bağımlılıklar  
- `fsm/` → Finite State Machine yönetimi  
- `app/` → Sistem orkestrasyonu  
- `ui/` → Pygame tabanlı görselleştirme  

Bu yapı sayesinde:

- Test edilebilirlik artar
- Bağımlılıklar minimize edilir
- Sistem ölçeklenebilir hale gelir
- Endüstriyel seviyede sürdürülebilirlik sağlanır

---

# 🚀 Sonuç

Bu proje;

- Algoritma geliştirme,
- Gerçek zamanlı veri işleme,
- Sensör füzyonu,
- Nesne takibi,
- Yazılım mimarisi tasarımı

alanlarında uçtan uca bir otonom sürüş algı sistemi simülasyonu sunmaktadır.

Hem akademik hem de endüstriyel uygulamalar için güçlü bir temel oluşturur.

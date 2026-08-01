1 @startuml
    2 title 4.2.2.1 Sequence Diagram - Dashboard Pemantauan Siklon
    3
    4 skinparam sequenceMessageAlign center
    5 autonumber
    6
    7 actor Pengguna
    8 participant DashboardPage
    9 participant Utils
   10 participant FoliumMap
   11
   12 Pengguna -> DashboardPage : Membuka Halaman Dashboard
   13 activate DashboardPage
   14
   15 DashboardPage -> Utils : load_prediction_data()
   16 activate Utils
   17 Utils --> DashboardPage : Data Prediksi (DataFrame)
   18 deactivate Utils
   19
   20 DashboardPage -> Utils : load_test_data()
   21 activate Utils
   22 Utils --> DashboardPage : Data Observasi (DataFrame)
   23 deactivate Utils
   24
   25 Pengguna -> DashboardPage : Menggeser Slider Radius (km)
   26 DashboardPage -> Utils : haversine_km(kordinat_padang)
   27 activate Utils
   28 Utils --> DashboardPage : Jarak ke Padang (km)
   29 deactivate Utils
   30
   31 DashboardPage -> DashboardPage : Filter SID berdasarkan Radius
   32
   33 Pengguna -> DashboardPage : Memilih ID Siklon (Searchbox/Dropdown)
   34 DashboardPage -> DashboardPage : Merge Data Aktual & Prediksi
   35
   36 DashboardPage -> FoliumMap : render_map(merged_data)
   37 activate FoliumMap
   38 FoliumMap --> DashboardPage : Visualisasi Jalur (Aktual & Prediksi)
   39 deactivate FoliumMap
   40
   41 DashboardPage -> DashboardPage : Hitung Metrik Akurasi (RMSE & MAE)
   42 DashboardPage --> Pengguna : Menampilkan Dashboard (Metrik, Peta, & Tabel)
   43
   44 deactivate DashboardPage
   45
   46 footer
   47     Dokumentasi Sistem - Dashboard Monitoring
   48 end footer
   49 @enduml

  2. Sequence Diagram - Halaman Prediksi

    1 @startuml
    2 title 4.2.2.2 Sequence Diagram - Prediksi Lintasan Siklon (LSTM)
    3
    4 skinparam sequenceMessageAlign center
    5 autonumber
    6
    7 actor Pengguna
    8 participant PredictionPage
    9 participant InferenceService
   10 participant "Model LSTM (.keras)" as Model
   11 participant AnalyticsService
   12 participant MapVisualizer
   13 participant PDFService
   14
   15 Pengguna -> PredictionPage : Membuka Halaman Prediksi
   16 activate PredictionPage
   17
   18 PredictionPage -> InferenceService : load_resources()
   19 activate InferenceService
   20 InferenceService -> Model : load_model()
   21 InferenceService --> PredictionPage : Model & Scaler Siap
   22 deactivate InferenceService
   23
   24 alt Input Koordinat via Peta
   25     Pengguna -> MapVisualizer : Klik Lokasi pada Peta
   26     activate MapVisualizer
   27     MapVisualizer --> PredictionPage : last_clicked (Lat, Lon)
   28     deactivate MapVisualizer
   29     PredictionPage -> PredictionPage : Auto-fill Form Koordinat
   30 else Input Manual via Form
   31     Pengguna -> PredictionPage : Input (Lat, Lon, Wind, Pressure)
   32 end
   33
   34 Pengguna -> PredictionPage : Simpan 8 Titik Observasi
   35 Pengguna -> PredictionPage : Set Konfigurasi (Tanggal & Horizon Jam)
   36
   37 Pengguna -> PredictionPage : Klik Tombol "Prediksi LSTM"
   38 activate PredictionPage
   39
   40 PredictionPage -> InferenceService : run_recursive_inference(df_obs, steps)
   41 activate InferenceService
   42 loop Tiap Langkah (Step)
   43     InferenceService -> InferenceService : Feature Engineering (Delta, Speed, Bearing)
   44     InferenceService -> Model : model.predict(X_input)
   45     Model --> InferenceService : Hasil Prediksi (Lat, Lon)
   46     InferenceService -> InferenceService : Update Window (Slide Data)
   47 end
   48 InferenceService --> PredictionPage : List Koordinat Prediksi
   49 deactivate InferenceService
   50
   51 PredictionPage -> AnalyticsService : calculate_analytics(results)
   52 activate AnalyticsService
   53 AnalyticsService -> AnalyticsService : Hitung Kategori (WMO/NOAA)
   54 AnalyticsService -> AnalyticsService : Hitung Jarak Terdekat ke Pesisir Sumbar
   55 AnalyticsService --> PredictionPage : Hasil Analisis & Kategori Risiko
   56 deactivate AnalyticsService
   57
   58 PredictionPage -> MapVisualizer : draw_trajectory(history, prediction)
   59 activate MapVisualizer
   60 MapVisualizer --> PredictionPage : Peta AntPath (Garis Merah Putus-putus)
   61 deactivate MapVisualizer
   62
   63 PredictionPage --> Pengguna : Tampilkan Hasil Prediksi & Analisis Lengkap
   64
   65 opt Cetak Laporan PDF
   66     Pengguna -> PredictionPage : Klik Tombol "Cetak Laporan PDF"
   67     PredictionPage -> PDFService : generate_report(data_lengkap)
   68     activate PDFService
   69     PDFService --> Pengguna : File PDF Laporan Terunduh
   70     deactivate PDFService
   71 end
   72
   73 deactivate PredictionPage
   74
   75 footer
   76     Dokumentasi Sistem - Proses Prediksi & Analytics
   77 end footer
   78 @enduml

  3. Sequence Diagram - Halaman Evaluasi

    1 @startuml
    2 title 4.2.2.3 Sequence Diagram - Evaluasi Akurasi Per Kasus
    3
    4 skinparam sequenceMessageAlign center
    5 autonumber
    6
    7 actor Pengguna
    8 participant EvaluationPage
    9 participant Utils
   10
   11 Pengguna -> EvaluationPage : Membuka Halaman Evaluasi
   12 activate EvaluationPage
   13
   14 EvaluationPage -> Utils : load_prediction_data()
   15 activate Utils
   16 Utils --> EvaluationPage : Seluruh Data Prediksi
   17 deactivate Utils
   18
   19 Pengguna -> EvaluationPage : Cari/Pilih ID Siklon (SID)
   20 EvaluationPage -> EvaluationPage : Filter Data Berdasarkan SID
   21
   22 EvaluationPage -> EvaluationPage : Hitung Metrik (MAE, RMSE, Min/Max Error)
   23 EvaluationPage -> EvaluationPage : Klasifikasi Predikat Akurasi
   24
   25 EvaluationPage -> EvaluationPage : Generate Grafik Garis (Deviasi Jarak)
   26 EvaluationPage -> EvaluationPage : Generate Grafik Batang (Distribusi Error)
   27 EvaluationPage -> EvaluationPage : Generate Grafik Dekomposisi (Lat vs Lon)
   28
   29 EvaluationPage --> Pengguna : Menampilkan Statistik & Grafik Analisis
   30
   31 opt Unduh Data CSV
   32     Pengguna -> EvaluationPage : Klik Tombol "Unduh CSV"
   33     EvaluationPage --> Pengguna : File eval_sid.csv
   34 end
   35
   36 deactivate EvaluationPage
   37
   38 footer
   39     Dokumentasi Sistem - Evaluasi & Statistik
   40 end footer
   41 @enduml

  4. Sequence Diagram - Halaman Data Siklon

    1 @startuml
    2 title 4.2.2.4 Sequence Diagram - Inventaris Data Observasi
    3
    4 skinparam sequenceMessageAlign center
    5 autonumber
    6
    7 actor Pengguna
    8 participant DataPage
    9 participant Utils
   10
   11 Pengguna -> DataPage : Membuka Halaman Data Siklon
   12 activate DataPage
   13
   14 DataPage -> Utils : load_observasi_data()
   15 activate Utils
   16 Utils --> DataPage : Dataset Observasi IBTrACS
   17 deactivate Utils
   18
   19 Pengguna -> DataPage : Pilih ID Siklon (SID)
   20 DataPage -> DataPage : Filter Baris Berdasarkan SID
   21
   22 DataPage -> DataPage : Mapping Status Data (Badge: Asli/Perbaikan)
   23 DataPage --> Pengguna : Tampilkan Tabel Detail Observasi & Status Imputasi
   24
   25 deactivate DataPage
   26
   27 footer
   28     Dokumentasi Sistem - Manajemen Data Observasi
   29 end footer
   30 @enduml

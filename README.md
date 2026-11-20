# Azərbaycan Sığorta Bazarının Təhlili

> 29 sığorta şirkətinin məlumatlarından trendlərə, müqayisələrə və ödənişlərin təxmininə.

Bu layihə 2016–2026-cı illər üzrə sığorta şirkətlərinin haqlarını və ödənişlərini Python ilə təhlil edir. Məqsəd illik dəyişiklikləri izləmək, şirkətləri müqayisə etmək və məlum sığorta haqları əsasında ödənişləri təxmin edən interaktiv tətbiq hazırlamaqdır.

## Məlumatların Xülasəsi

- **Birləşdirmədən sonra:** 3 204 şirkət–dövr qeydi.
- **Təmizləmədən sonra:** 3 186 qeyd.
- **Şirkət sayı:** 29.
- **Əhatə dövrü:** yanvar 2016 – sentyabr 2026.
- **İlkin sütun sayı:** 6.

### Əsas Göstəricilər

**Şirkət və dövr:** `company`, `year`, `month`, `date`.

**Maliyyə məlumatları:** `premiums` — sığorta haqları, `claims` — sığorta ödənişləri.

**Çatışmayan məlumatlar:** sığorta haqqı olmayan 18 qeyd təhlildən çıxarılıb. Sıfır məbləğlər ilkin məlumatlarda saxlanılıb.

**Ölçü vahidi:** CSV-lərdə məbləğlər **min AZN** ilədir; məsələn, `100` = 100 000 AZN. Maliyyə qrafikləri və aşağıdakı illik/şirkət cədvəlləri **milyon AZN** ilə göstərilir.

**Hesabat prinsipi:** məbləğlər yanvardan hesabat ayınadək yığılır. Tam illik nəticə üçün dekabr istifadə edilir; aylıq yığılan məbləğlər toplanmır.

Məlumatlar “Sığorta şirkətləri üzrə sığorta haqları və sığorta ödənişləri” cədvəlindən hazırlanıb. Dəqiq mənbə URL-si repozitoriyada hələ göstərilməyib.

## Python ilə İlkin Məlumat Təhlili

**Məlumatların yüklənməsi:** iki CSV `pandas` vasitəsilə birləşdirilib.

**Təkrarlanan dövrlər:** eyni şirkət, il və ay üçün daha yeni fayldakı mövcud məbləğə üstünlük verilib.

**İlkin yoxlamalar:** çatışmayan dəyərlər, sıfırlar və təsviri statistika yoxlanılıb.

**Kənar dəyərlər:** IQR üsulu ilə müəyyən edilib. Böyük şirkətlərdə yüksək məbləğlər normal ola bildiyi üçün avtomatik silinməyib.

**Yeni dəyişənlər:** `premium_category` və `log_claims` yaradılıb. Model üçün kateqoriyalar ədədi sütunlara çevrilib.

## Sığorta Göstəricilərinin Təhlili

### İllik Sığorta Haqları və Ödənişləri

Dekabr hesabatlarında olan şirkət məbləğlərinin cəmi müqayisə edilib.

| İl | Sığorta haqları, milyon AZN | Sığorta ödənişləri, milyon AZN |
| --- | ---: | ---: |
| 2016 | 486.07 | 237.25 |
| 2017 | 556.87 | 257.11 |
| 2018 | 727.95 | 240.33 |
| 2019 | 681.18 | 301.54 |
| 2020 | 728.63 | 465.15 |
| 2021 | 843.90 | 458.73 |
| 2022 | 970.82 | 433.20 |
| 2023 | 1,222.54 | 587.32 |
| 2024 | 1,353.19 | 752.71 |
| 2025 | 1,504.71 | 920.40 |

2026-cı il natamam olduğu üçün bu cədvələ daxil edilməyib. Bunlar təmizlənmiş məlumatlarda olan şirkətlərin cəmidir; dərc edilmiş rəsmi bazar yekunu kimi təqdim edilmir.

### Ödənişlər üzrə İlk 5 Şirkət

Son hesabat dövrü — **yanvar–sentyabr 2026**.

| Şirkət | Sığorta ödənişləri, milyon AZN |
| --- | ---: |
| Paşa Həyat Sığorta | 548.53 |
| Paşa Sığorta | 130.90 |
| Atəşgah Həyat | 87.75 |
| Atəşgah | 32.00 |
| Qala Sığorta | 18.00 |

### Aylar və İllər üzrə Əhatə

Qrafiklər hər ay və il üzrə qeyd sayını göstərir. Qeyd sayı maliyyə fəaliyyəti və ya gəlir demək deyil. Son illərdə əhatə və natamam dövrlər müqayisəyə təsir edir.

## Maşın Öyrənməsi ilə Ödənişlərin Təxmini

Şirkət, il, ay, sığorta haqqı və haqqın kateqoriyası əsasında `log_claims` təxmin edilir. Nəticə ilkin pul ölçüsünə qaytarılır.

Üç model sıfırlar daxil edilən və yalnız müsbət məbləğlərlə təlim variantlarında yoxlanılıb. Altı variant üçün eyni validasiya tarixləri istifadə edilib. Son tarixlər ayrıca test üçün saxlanılıb.

### Validasiya Müqayisəsi

| Model | Təlim məlumatları | R² | MAE, min AZN |
| --- | --- | ---: | ---: |
| Təsadüfi meşə | Yalnız müsbət | 0.8548 | 5 198.97 |
| Təsadüfi meşə | Sıfırlar daxil | 0.8246 | 5 538.29 |
| Qradient gücləndirmə | Yalnız müsbət | 0.8083 | 5 117.36 |
| Qradient gücləndirmə | Sıfırlar daxil | 0.7986 | 5 160.97 |
| Xətti reqressiya | Yalnız müsbət | -9.3430 | 17 885.97 |
| Xətti reqressiya | Sıfırlar daxil | -448.6556 | 80 972.18 |

Seçim meyarı ən yüksək validasiya **R²** göstəricisidir. Buna görə yalnız müsbət məbləğlərlə öyrədilən **Random Forest** seçilib; ən aşağı MAE başqa modeldə ola bilər.

### Seçilmiş Modelin Test Nəticələri

Test dəstində sıfır qeydlər də saxlanılıb.

| Göstərici | Nəticə |
| --- | ---: |
| R² | 0.7393 |
| MAE | 10 046.13 min AZN |
| RMSE | 38 294.72 min AZN |

MAE orta mütləq xətanı, RMSE isə böyük səhvlərə daha çox çəki verən xətanı göstərir. Daha aşağı daha yaxşıdır. Bu nəticələr fərdi şirkət üzrə yüksək dəqiqlik vəd etmir.

## Streamlit Tətbiqi

Azərbaycan dilində tətbiqdə şirkət, il, ay və sığorta haqqı daxil edilir. Tətbiq aşağıdakıları göstərir:

- Təxmin edilən sığorta ödənişləri.
- Mövcud olduqda seçilmiş dövrün faktiki ödənişləri.
- Eyni ay üzrə şirkət və bütün şirkətlərin tarixi ortalamaları.
- Şirkətin illər üzrə həmin ayın tarixçəsi.
- Sıfır və qeyri-adi sığorta haqqı üçün xəbərdarlıqlar.

Faktiki ödəniş CSV-dən götürülür və girişdəki sığorta haqqını dəyişəndə dəyişmir. Faktiki nəticə ilə düzgün müqayisə üçün həmin dövrün faktiki sığorta haqqını daxil etmək lazımdır.

## Nəticələr və Tövsiyələr

- **İllik müqayisə:** yığılan aylıq məbləğlər əvəzinə dekabr göstəricilərindən istifadə edin.
- **Sıfır qeydlər:** səbəbi təsdiqlənmədən ilkin məlumatdan silməyin; təlim strategiyasını validasiya ilə yoxlayın.
- **Model nəticələri:** orta xəta ilə yanaşı şirkət üzrə faktiki nəticələri də qiymətləndirin.
- **Tarixi ortalamalar:** sıfır dövrlər, şirkət miqyası və illər üzrə dəyişikliklərin ortalamaya təsirini nəzərə alın.

Bu layihə tədris və portfolio məqsədlidir. Model məlum sığorta haqqı əsasında dövrün ödənişini təxmin edir; gələcək üçün müstəqil proqnoz və ya fərdi tibbi xərc kalkulyatoru deyil. Tarixi hesabat düzəlişləri qiymətləndirməni məhdudlaşdıra bilər. Biznes qərarları üçün əlavə yoxlama tələb olunur.

## İstifadə Olunan Texnologiyalar

Python · pandas · NumPy · Matplotlib · Seaborn · scikit-learn · Streamlit · joblib

## Layihənin İşə Salınması

Layihə Python 3.13 ilə yoxlanılıb. Terminalı layihə qovluğunda açın:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Windows-da aktivləşdirmə əmri:

```powershell
.venv\Scripts\Activate.ps1
```

Modelləri yenidən öyrətmək üçün `notebooks/project.ipynb` hüceyrələrini sıra ilə işlədin. CSV faylları `data/`, model faylları isə `models/` qovluğunda saxlanılır. Notebook-u layihənin kökündən və ya `notebooks/` qovluğundan işə salmaq olar.

| Fayl | Təyinat |
| --- | --- |
| `notebooks/project.ipynb` | Təmizləmə, təhlil və model müqayisəsi |
| `app.py` | İnteraktiv tətbiq |
| `data/insurance_2016_2025.csv`, `data/insurance_2016_2026.csv` | Təmizlənmiş məlumatlar |
| `models/insurance_model.pkl` | Seçilmiş model |
| `models/model_features.pkl` | Modelin giriş sütunları |
| `models/model_name.pkl` | Seçilmiş modelin adı |
| `models/model_info.pkl` | Təlim strategiyası və əhatəsi |
| `requirements.txt` | Python asılılıqları |

`.venv/`, `__pycache__/` və `.DS_Store` GitHub-a daxil edilməməlidir. Canlı tətbiq yayımlandıqda onun ünvanını repozitoriyanın **About → Website** bölməsinə əlavə edin. Məlumatları paylaşmazdan əvvəl mənbənin istifadə şərtlərini yoxlayın.

## Qovluq Strukturu

```text
.
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── insurance_2016_2025.csv
│   └── insurance_2016_2026.csv
├── models/
│   ├── insurance_model.pkl
│   ├── model_features.pkl
│   ├── model_name.pkl
│   └── model_info.pkl
└── notebooks/
    └── project.ipynb
```

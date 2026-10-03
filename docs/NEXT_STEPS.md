# Next steps (checklist)

## 0. Sabse pehle (1–2 min, ek baar)
- [ ] `python ml/train.py` — model ko apne computer ke scikit-learn version ke mutabiq dobara train karta hai.
      Iske baad dashboard ka "ML model CHECK / NEEDS CHECK" hat jata hai aur `pytest` ka version-wala test pass hota hai.
      (Zip mein model kisi aur scikit-learn version se bana hota hai, isliye yeh step zaroori hai.)

## A. Pehli baar chalana (15–20 min)
- [ ] 1. Zip extract karo, terminal project folder mein kholo.
- [ ] 2. `pip install -r backend/requirements.txt`
- [ ] 3. (Optional) `.env.example` ko copy karke `.env` banao, aur **ek** key daalo: `GEMINI_API_KEY=...`
- [ ] 4. `uvicorn backend.main:app --port 8000`
- [ ] 5. Browser: `http://localhost:8000/`
- [ ] 6. **Status panel padho** (Overview ke upar "DATA QUALITY & SYSTEM STATUS"):
  - Weather = **OK** → real Open-Meteo chal raha hai. **DEMO** → internet/Open-Meteo reach nahi ho raha.
  - Recommendations = **OK** → Gemini ne likha. **CHECK** → Gemini fail hua (key/model/quota), terminal ka message dekho.
- [ ] 7. Backend band karke dekho: red banner aana chahiye; dobara start karo: khud reconnect.
- [ ] 8. `pip install -r backend/requirements-dev.txt` phir `pytest tests/ -v` → 68 pass (step 0 ke baad).
- [ ] 8b. Browser mein `Ctrl + F5` (hard refresh) agar purana dashboard cache mein ho.

## B. Presentation se pehle (zaroori)
- [ ] 9. `data/zones.py` ke 11 zones ke numbers (built-up, NDVI, road, water) apni local knowledge se check/theek karo.
        Badalne ke baad: `python ml/generate_dataset.py` aur `python ml/train.py`.
- [ ] 10. Presentation mein yeh kaho: "Synthetic data par pipeline demo; weather real; zone values estimates."
         **"88% accuracy" mat kaho.** (Model Performance page par noise ceiling likha hai.)
- [ ] 11. Screenshots lo jisme badges (DEMO / ESTIMATE / SYNTHETIC DATA) dikhein: yeh honesty ka saboot hai.
- [ ] 12. `docs/MODEL_CARD.md` aur `docs/CHANGELOG.md` ek baar parh lo.

## C. Agar Gemini/Open-Meteo kaam na kare
- Recommendations hamesha RULE-BASED → terminal mein `[recommendations] gemini call failed: <ErrorType>` dekho.
  `HTTPError` = key/model galat ya quota; `Timeout/ConnectionError` = internet.
  Model naam badalna ho: `.env` mein `GEMINI_MODEL=<naya-naam>`.
- Weather DEMO → internet/firewall check karo. Dashboard phir bhi chalta hai (simulation), bas DEMO likha rahega.
- Model warning "trained with scikit-learn X" → `python ml/train.py` dobara chalao.
- Charts (trend/donut) khaali hon → ab dashboard par "CHART LIBRARY NOT LOADED" likha aayega; `frontend/vendor/` folder poora hona chahiye (Ctrl+F5 bhi karo).

## D. Aage ke upgrades (optional)
- [ ] 13. Real satellite data (Sentinel-2/Landsat via Google Earth Engine) → zone values asli banengi.
- [ ] 14. Real ward boundaries (GeoJSON) → map par polygons.
- [ ] 15. Real data par model dobara train karo, tab hi accuracy report karo.
- [ ] 16. Docker test: `docker build -t heatshield-ai .` (maine nahi chalaya).

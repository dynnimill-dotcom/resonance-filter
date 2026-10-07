# ==================== ВКЛАДКА 3 ====================
with tab3:
    st.markdown("### 🎯 Очаги напряжения")
    st.markdown("""
    <div style="background: white; border-radius: 15px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
        <p style="color: #636e72; margin: 0;">
        Эта вкладка находит <b>горячие точки</b> — адреса, откуда идёт массовый поток жалоб. 
        Очаг формируется по адресу. Добродел и Инцидент объединяются в один кластер. 
        Показываются все адреса, где <b>2 и более жалоб</b>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown('<div class="upload-card"><h3>📄 Файл №1 (Добродел)</h3><p>Excel (.xlsx, .xls) или CSV (.csv)</p></div>', unsafe_allow_html=True)
        hotspot_file1 = st.file_uploader("", type=["xlsx", "xls", "csv"], label_visibility="collapsed", key="hotspot_dobrodel")
    with col2:
        st.markdown('<div class="upload-card"><h3>📄 Файл №2 (Инцидент)</h3><p>Excel (.xlsx, .xls) или CSV (.csv)</p></div>', unsafe_allow_html=True)
        hotspot_file2 = st.file_uploader("", type=["xlsx", "xls", "csv"], label_visibility="collapsed", key="hotspot_incident")

    hotspot_clicked = st.button("🎯 Найти очаги напряжения", type="primary", use_container_width=True, key="btn_hotspot")

    if hotspot_clicked:
        if not hotspot_file1 or not hotspot_file2:
            st.error("⚠️ Загрузите оба файла!")
        else:
            with st.spinner("🔄 Ищем очаги..."):
                try:
                    df1 = load_dobrodel(hotspot_file1)
                    df2 = load_incident(hotspot_file2)

                    # Загружаем полные данные (включая почту для Добродела)
                    df1_full = read_file(hotspot_file1)
                    df2_full = read_file(hotspot_file2)

                    # ==================== СБОР ДАННЫХ ====================
                    hotspots = defaultdict(lambda: {
                        "omсу": "",
                        "address": "",
                        "count": 0,
                        "best_description": "",
                        "best_score": -1,
                        "dobrodel_count": 0,
                        "incident_count": 0,
                        "dobrodel_numbers": [],
                        "incident_numbers": [],
                        "emails": defaultdict(int)
                    })

                    # ==================== ОБРАБОТКА ДОБРОДЕЛА ====================
                    for idx, row in df1_full.iterrows():
                        address = get_address_dobrodel(row)
                        if not address:
                            continue

                        norm_addr = normalize_address(address)
                        key = norm_addr

                        описание = str(row.get("Описание", "")) if pd.notna(row.get("Описание")) else ""
                        score = calculate_tension(описание)
                        номер = str(row.get("Номер в источнике", "")).strip()
                        почта = str(row.get("Почта заявителя", "")).strip() if pd.notna(row.get("Почта заявителя")) else ""

                        hotspots[key]["omсу"] = row.get("ОМСУ", "")
                        hotspots[key]["address"] = address
                        hotspots[key]["count"] += 1
                        hotspots[key]["dobrodel_count"] += 1
                        if номер:
                            hotspots[key]["dobrodel_numbers"].append(номер)

                        if почта and почта.lower() not in ["nan", "none", ""]:
                            hotspots[key]["emails"][почта] += 1

                        if score > hotspots[key]["best_score"]:
                            hotspots[key]["best_score"] = score
                            hotspots[key]["best_description"] = описание

                    # ==================== ОБРАБОТКА ИНЦИДЕНТА ====================
                    for idx, row in df2_full.iterrows():
                        address = get_address_incident(row)
                        if not address:
                            continue

                        norm_addr = normalize_address(address)
                        key = norm_addr  # объединяем с Доброделом по нормализованному адресу

                        контент = str(row.get("Контент", "")) if pd.notna(row.get("Контент")) else ""
                        score = calculate_tension(контент)
                        номер = str(row.get("Номер инцидента", "")).strip()

                        # Если очаг уже существует — дополняем ОМСУ
                        if not hotspots[key]["omсу"]:
                            hotspots[key]["omсу"] = row.get("Локация", "")
                        if not hotspots[key]["address"]:
                            hotspots[key]["address"] = address

                        hotspots[key]["count"] += 1
                        hotspots[key]["incident_count"] += 1
                        if номер:
                            hotspots[key]["incident_numbers"].append(номер)

                        if score > hotspots[key]["best_score"]:
                            hotspots[key]["best_score"] = score
                            hotspots[key]["best_description"] = контент

                    # ==================== ФИЛЬТР И СОРТИРОВКА ====================
                    filtered = {k: v for k, v in hotspots.items() if v["count"] >= 2}
                    sorted_hotspots = sorted(filtered.items(), key=lambda x: x["count"], reverse=True)

                    # ==================== ФОРМИРОВАНИЕ ВЫВОДА ====================
                    text_output = ""
                    if not sorted_hotspots:
                        st.warning("⚠️ Очагов напряжения не найдено.")
                    else:
                        text_output += "🎯 ОЧАГИ НАПРЯЖЕНИЯ\n"
                        text_output += "=" * 70 + "\n\n"

                        for i, (key, data) in enumerate(sorted_hotspots, 1):
                            text_output += f"{i}. {data['omсу']} - {data['count']} жалоб - {data['address']}\n"

                            # Все номера жалоб
                            all_numbers = []
                            if data["dobrodel_numbers"]:
                                all_numbers.extend(data["dobrodel_numbers"])
                            if data["incident_numbers"]:
                                all_numbers.extend(data["incident_numbers"])
                            if all_numbers:
                                text_output += f"   📞 Номера жалоб: {', '.join(all_numbers)}\n"

                            # Почты заявителей (только Добродел)
                            if data["emails"]:
                                sorted_emails = sorted(data["emails"].items(), key=lambda x: x[1], reverse=True)
                                for email, count in sorted_emails:
                                    text_output += f"   📧 {email} - {count} жалоб\n"
                            else:
                                text_output += f"   📧 Почта заявителя: Не указана\n"

                            # Самое резонансное
                            text_output += f"   📝 Самое резонансное: {data['best_description'][:300]}\n"

                            # Источники
                            text_output += f"   📊 Источники: Добродел ({data['dobrodel_count']}), Инцидент ({data['incident_count']})\n"

                            text_output += "-" * 70 + "\n\n"

                        # ==================== ВЫВОД В ИНТЕРФЕЙС ====================
                        st.markdown('<div class="result-box">', unsafe_allow_html=True)
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
                            <span style="font-size: 2rem;">🎯</span>
                            <h3 style="margin: 0; color: #2d3436;">Найдено <span style="color: #e74c3c;">{len(sorted_hotspots)}</span> очагов напряжения</h3>
                            <span style="margin-left: auto; background: #dfe6e9; padding: 0.3rem 1rem; border-radius: 50px; font-size: 0.85rem; color: #636e72;">🔽 от самых горячих</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.text_area("", text_output, height=500, label_visibility="collapsed")
                        st.download_button("📥 Скачать как .txt", data=text_output, file_name="очаги_напряжения.txt", mime="text/plain")
                        st.markdown('</div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Ошибка: {e}")
                    import traceback
                    st.text(traceback.format_exc())

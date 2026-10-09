import streamlit as st
import os
from datetime import date, timedelta
from ai.llm_client import LLMClient
from documents.word_generator import WordGenerator
from documents.ppt_generator import PPTGenerator
from documents.pdf_converter import PDFConverter
from audio.tts_generator import TTSGenerator
from utils.helpers import generate_filename, format_currency
from config.settings import settings

def init_session_state():
    if "itinerary" not in st.session_state:
        st.session_state.itinerary = None
    if "generated" not in st.session_state:
        st.session_state.generated = False
    if "audio_files" not in st.session_state:
        st.session_state.audio_files = []
    if "flight_results" not in st.session_state:
        st.session_state.flight_results = []
    if "return_flight_results" not in st.session_state:
        st.session_state.return_flight_results = []
    if "selected_flight" not in st.session_state:
        st.session_state.selected_flight = None
    if "selected_return_flight" not in st.session_state:
        st.session_state.selected_return_flight = None
    if "accommodation_results" not in st.session_state:
        st.session_state.accommodation_results = []
    if "selected_accommodations" not in st.session_state:
        st.session_state.selected_accommodations = {}
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_display" not in st.session_state:
        st.session_state.chat_display = []

def main():
    st.set_page_config(
        page_title="TripAI - 智能旅行攻略",
        page_icon="🎒",
        layout="wide"
    )
    
    init_session_state()
    
    st.title("🎒 TripAI - 智能旅行攻略一键生成")
    st.subheader("输入您的旅行偏好，AI为您生成专属攻略")
    
    with st.sidebar:
        st.header("🚀 旅行参数设置")
        
        origin = st.text_input("🏙️ 出发城市", value="上海")
        destination = st.text_input("📍 目的地", value="北京")
        
        departure_date = st.date_input("📅 出发日期", value=date.today() + timedelta(days=7))
        days = st.slider("📅 旅行天数", min_value=1, max_value=7, value=3)
        return_date = departure_date + timedelta(days=days - 1)
        st.info(f"📅 返程日期：{return_date.strftime('%Y-%m-%d')}")
        
        travel_group_options = ["情侣出游", "家庭亲子", "朋友结伴", "独自旅行", "商务出差"]
        travel_group = st.selectbox("👥 出行人群", travel_group_options, index=0)
        
        traveler_count = st.slider("🧍 游玩人数", min_value=1, max_value=10, value=2)
        
        transport_options = ["飞机", "高铁", "普通火车", "自驾", "长途汽车"]
        transport = st.selectbox("🚄 往返交通方式", transport_options, index=0)
        
        provider_options = [("DeepSeek", "deepseek"), ("豆包", "doubao"), ("OpenAI", "openai")]
        provider = st.selectbox("🤖 AI服务商", options=[p[0] for p in provider_options], index=0)
        provider_key = dict(provider_options)[provider]
        
        st.markdown("---")
        budget = st.slider("💰 总预算（元，含通勤）", min_value=1000, max_value=50000, value=5000, step=100)
        
        voice_type = st.radio("🗣️ 语音类型", ["女声", "男声"], index=0)
        voice_key = "female" if voice_type == "女声" else "male"
    
    if transport in ["飞机", "高铁"] and not st.session_state.generated:
        flight_label = "航班" if transport == "飞机" else "车次"
        st.header(f"✈️ {flight_label}搜索与选择")
        
        col_search_go, col_search_ret = st.columns(2)
        
        with col_search_go:
            st.subheader(f"🛫 去程：{origin} → {destination}")
            st.caption(f"📅 {departure_date.strftime('%Y-%m-%d')}")
            if st.button(f"🔍 搜索去程{flight_label}", key="search_go", use_container_width=True):
                with st.spinner(f"正在搜索去程{flight_label}..."):
                    try:
                        llm_search = LLMClient(provider=provider_key)
                        flights = llm_search.search_flights(
                            origin=origin,
                            destination=destination,
                            departure_date=departure_date.strftime("%Y-%m-%d"),
                            transport=transport,
                            traveler_count=traveler_count,
                            is_return=False
                        )
                        st.session_state.flight_results = flights
                    except Exception as e:
                        st.error(f"搜索失败: {str(e)}")
            
            if st.session_state.flight_results:
                go_flights = st.session_state.flight_results
                for i, f in enumerate(go_flights):
                    with st.expander(
                        f"**{f['flight_no']}** | {f['departure_time']}→{f['arrival_time']} | ¥{f['price_per_person']}/人",
                        expanded=False
                    ):
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.write(f"**{flight_label}号**")
                            st.write(f.get('flight_no', ''))
                            st.write(f"**{'航空公司' if transport == '飞机' else '运营方'}**")
                            st.write(f.get('airline_or_operator', ''))
                        with c2:
                            st.write(f"**出发**")
                            st.write(f"{f.get('departure_time', '')}")
                            st.write(f.get('departure_airport_or_station', ''))
                            st.write(f"**抵达**")
                            st.write(f"{f.get('arrival_time', '')}")
                            st.write(f.get('arrival_airport_or_station', ''))
                        with c3:
                            st.write(f"**耗时**")
                            st.write(f.get('duration', ''))
                            st.write(f"**{'机型' if transport == '飞机' else '车型'}**")
                            st.write(f.get('aircraft_or_train_type', ''))
                            st.write(f"**准点率**")
                            st.write(f.get('on_time_rate', ''))
                        with c4:
                            st.write(f"**{'舱位' if transport == '飞机' else '座席'}**")
                            st.write(f.get('seat_type', ''))
                            st.write(f"**单人票价**")
                            st.write(f"¥{f.get('price_per_person', 0)}")
                            st.write(f"**{traveler_count}人总价**")
                            st.write(f"¥{f.get('price_total', 0)}")
                            st.write(f"**行李**")
                            st.write(f.get('luggage_info', ''))
                        
                        if st.button(f"✅ 选择此{flight_label}", key=f"go_{i}", use_container_width=True):
                            st.session_state.selected_flight = f
                            st.rerun()
                
                if st.session_state.selected_flight:
                    sf = st.session_state.selected_flight
                    st.success(
                        f"✅ 已选去程：{sf['flight_no']} | "
                        f"{sf['departure_time']}→{sf['arrival_time']} | "
                        f"¥{sf.get('price_total', sf['price_per_person'] * traveler_count)}"
                    )
        
        with col_search_ret:
            st.subheader(f"🛬 返程：{destination} → {origin}")
            st.caption(f"📅 {return_date.strftime('%Y-%m-%d')}")
            if st.button(f"🔍 搜索返程{flight_label}", key="search_ret", use_container_width=True):
                with st.spinner(f"正在搜索返程{flight_label}..."):
                    try:
                        llm_search = LLMClient(provider=provider_key)
                        ret_flights = llm_search.search_flights(
                            origin=origin,
                            destination=destination,
                            departure_date=return_date.strftime("%Y-%m-%d"),
                            transport=transport,
                            traveler_count=traveler_count,
                            is_return=True
                        )
                        st.session_state.return_flight_results = ret_flights
                    except Exception as e:
                        st.error(f"搜索失败: {str(e)}")
            
            if st.session_state.return_flight_results:
                ret_flights = st.session_state.return_flight_results
                for i, f in enumerate(ret_flights):
                    with st.expander(
                        f"**{f['flight_no']}** | {f['departure_time']}→{f['arrival_time']} | ¥{f['price_per_person']}/人",
                        expanded=False
                    ):
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.write(f"**{flight_label}号**")
                            st.write(f.get('flight_no', ''))
                            st.write(f"**{'航空公司' if transport == '飞机' else '运营方'}**")
                            st.write(f.get('airline_or_operator', ''))
                        with c2:
                            st.write(f"**出发**")
                            st.write(f"{f.get('departure_time', '')}")
                            st.write(f.get('departure_airport_or_station', ''))
                            st.write(f"**抵达**")
                            st.write(f"{f.get('arrival_time', '')}")
                            st.write(f.get('arrival_airport_or_station', ''))
                        with c3:
                            st.write(f"**耗时**")
                            st.write(f.get('duration', ''))
                            st.write(f"**{'机型' if transport == '飞机' else '车型'}**")
                            st.write(f.get('aircraft_or_train_type', ''))
                            st.write(f"**准点率**")
                            st.write(f.get('on_time_rate', ''))
                        with c4:
                            st.write(f"**{'舱位' if transport == '飞机' else '座席'}**")
                            st.write(f.get('seat_type', ''))
                            st.write(f"**单人票价**")
                            st.write(f"¥{f.get('price_per_person', 0)}")
                            st.write(f"**{traveler_count}人总价**")
                            st.write(f"¥{f.get('price_total', 0)}")
                            st.write(f"**行李**")
                            st.write(f.get('luggage_info', ''))
                        
                        if st.button(f"✅ 选择此{flight_label}", key=f"ret_{i}", use_container_width=True):
                            st.session_state.selected_return_flight = f
                            st.rerun()
                
                if st.session_state.selected_return_flight:
                    srf = st.session_state.selected_return_flight
                    st.success(
                        f"✅ 已选返程：{srf['flight_no']} | "
                        f"{srf['departure_time']}→{srf['arrival_time']} | "
                        f"¥{srf.get('price_total', srf['price_per_person'] * traveler_count)}"
                    )
        
        st.markdown("---")
    elif transport not in ["飞机", "高铁"]:
        st.session_state.flight_results = []
        st.session_state.return_flight_results = []
        st.session_state.selected_flight = None
        st.session_state.selected_return_flight = None
    
    if not st.session_state.generated:
        st.header("🏨 住宿搜索与选择")
        st.caption(f"搜索{destination}的住宿，并为每天选择入住酒店（可选，不选则由AI自动推荐）")
        
        col_acc_search, col_acc_filter = st.columns([3, 2])
        with col_acc_filter:
            acc_budget = st.slider("每晚预算上限（元）", min_value=0, max_value=2000, value=0, step=50, key="acc_budget_slider", help="0表示不限预算")
            acc_area = st.text_input("偏好区域/商圈", placeholder="如：故宫附近、三里屯等", key="acc_area_input")
        with col_acc_search:
            if st.button("🔍 搜索住宿", key="search_acc", use_container_width=True):
                with st.spinner(f"正在搜索{destination}住宿..."):
                    try:
                        llm_search = LLMClient(provider=provider_key)
                        accommodations = llm_search.search_accommodations(
                            destination=destination,
                            travel_group=travel_group,
                            traveler_count=traveler_count,
                            budget_per_night=acc_budget,
                            preferred_area=acc_area
                        )
                        st.session_state.accommodation_results = accommodations
                    except Exception as e:
                        st.error(f"搜索失败: {str(e)}")
        
        if st.session_state.accommodation_results:
            acc_results = st.session_state.accommodation_results
            for i, acc in enumerate(acc_results):
                nearby = acc.get('nearby_attractions', [])
                nearby_str = '、'.join(nearby) if nearby else '暂无'
                with st.expander(
                    f"**{acc.get('hotel', '')}** | {acc.get('type', '')} | ¥{acc.get('price_per_night', 0)}/晚 | {acc.get('rating', '')}",
                    expanded=False
                ):
                    ca1, ca2, ca3 = st.columns(3)
                    with ca1:
                        st.write(f"**酒店名称**")
                        st.write(acc.get('hotel', ''))
                        st.write(f"**类型**")
                        st.write(acc.get('type', ''))
                        st.write(f"**评分**")
                        st.write(acc.get('rating', ''))
                    with ca2:
                        st.write(f"**区域**")
                        st.write(acc.get('location', ''))
                        st.write(f"**每晚价格**")
                        st.write(f"¥{acc.get('price_per_night', 0)}")
                        st.write(f"**适合人群**")
                        st.write(acc.get('suitable_for', ''))
                    with ca3:
                        st.write(f"**附近景点**")
                        st.write(nearby_str)
                        st.write(f"**交通便利**")
                        st.write(acc.get('transport_convenience', ''))
                        st.write(f"**设施**")
                        st.write(acc.get('amenities', ''))
                    
                    st.write(f"**简介**：{acc.get('description', '')}")
                    
                    day_options = list(range(1, days + 1))
                    selected_day = st.selectbox(
                        "分配到第几天",
                        options=["不分配"] + [f"第{d}天" for d in day_options],
                        key=f"acc_day_{i}",
                        index=0
                    )
                    if st.button(f"✅ 选择此住宿", key=f"acc_{i}", use_container_width=True):
                        if selected_day != "不分配":
                            day_num = int(selected_day.replace("第", "").replace("天", ""))
                            st.session_state.selected_accommodations[day_num] = acc
                            st.rerun()
                        else:
                            st.warning("请先选择要分配到哪一天")
            
            if st.session_state.selected_accommodations:
                st.subheader("📋 已选住宿")
                for day_num in sorted(st.session_state.selected_accommodations.keys()):
                    sa = st.session_state.selected_accommodations[day_num]
                    col_sa_info, col_sa_del = st.columns([9, 1])
                    with col_sa_info:
                        st.success(
                            f"✅ 第{day_num}天：{sa.get('hotel', '')} | "
                            f"{sa.get('location', '')} | "
                            f"¥{sa.get('price_per_night', 0)}/晚"
                        )
                    with col_sa_del:
                        if st.button("🗑️", key=f"del_acc_{day_num}", help=f"取消第{day_num}天住宿选择"):
                            del st.session_state.selected_accommodations[day_num]
                            st.rerun()
        
        st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("✨ 生成攻略", use_container_width=True):
            if not destination.strip():
                st.error("请输入目的地")
                return
            
            with st.spinner("🎯 AI正在为您生成旅行攻略..."):
                try:
                    llm_client = LLMClient(provider=provider_key)
                    itinerary = llm_client.generate_itinerary(
                        origin=origin,
                        destination=destination,
                        days=days,
                        travel_group=travel_group,
                        traveler_count=traveler_count,
                        transport=transport,
                        budget=budget,
                        departure_date=departure_date.strftime("%Y-%m-%d"),
                        return_date=return_date.strftime("%Y-%m-%d"),
                        selected_flight=st.session_state.selected_flight,
                        selected_return_flight=st.session_state.selected_return_flight,
                        selected_accommodations=st.session_state.selected_accommodations if st.session_state.selected_accommodations else None
                    )
                    
                    st.session_state.itinerary = itinerary
                    st.session_state.generated = True
                    st.success("🎉 攻略生成成功！")
                    
                except Exception as e:
                    st.error(f"生成失败: {str(e)}")
    
    with col2:
        if st.session_state.generated and st.session_state.itinerary:
            if st.button("📄 导出Word", use_container_width=True):
                with st.spinner("正在生成Word文档..."):
                    try:
                        filename = generate_filename(f"{destination}_攻略")
                        output_path = os.path.join(settings.OUTPUT_DIR, f"{filename}.docx")
                        
                        word_gen = WordGenerator()
                        word_gen.generate_document(st.session_state.itinerary, output_path)
                        
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="📥 下载Word",
                                data=f,
                                file_name=f"{filename}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True
                            )
                        
                        st.success("Word文档生成成功！")
                    except Exception as e:
                        st.error(f"生成Word失败: {str(e)}")
    
    with col3:
        if st.session_state.generated and st.session_state.itinerary:
            if st.button("📊 导出PPT", use_container_width=True):
                with st.spinner("正在生成PPT..."):
                    try:
                        filename = generate_filename(f"{destination}_攻略")
                        output_path = os.path.join(settings.OUTPUT_DIR, f"{filename}.pptx")
                        
                        ppt_gen = PPTGenerator()
                        ppt_gen.generate_document(st.session_state.itinerary, output_path)
                        
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="📥 下载PPT",
                                data=f,
                                file_name=f"{filename}.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                use_container_width=True
                            )
                        
                        st.success("PPT生成成功！")
                    except Exception as e:
                        st.error(f"生成PPT失败: {str(e)}")
    
    if st.session_state.generated and st.session_state.itinerary:
        if st.button("📑 导出PDF", use_container_width=True):
            with st.spinner("正在生成PDF..."):
                try:
                    filename = generate_filename(f"{destination}_攻略")
                    output_path = os.path.join(settings.OUTPUT_DIR, f"{filename}.pdf")
                    
                    pdf_gen = PDFConverter()
                    pdf_gen.generate_document(st.session_state.itinerary, output_path)
                    
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="📥 下载PDF",
                            data=f,
                            file_name=f"{filename}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    
                    st.success("PDF生成成功！")
                except Exception as e:
                    st.error(f"生成PDF失败: {str(e)}")
    
    if st.session_state.generated and st.session_state.itinerary:
        st.header("🎧 生成语音导览")
        if st.button(f"🎙️ 生成{voice_type}语音导览", use_container_width=True):
            with st.spinner("正在生成语音导览..."):
                try:
                    tts_gen = TTSGenerator(voice_type=voice_key)
                    audio_files = tts_gen.generate_attraction_audio(
                        st.session_state.itinerary,
                        voice_type=voice_key
                    )
                    st.session_state.audio_files = audio_files
                    st.success("语音导览生成成功！")
                except Exception as e:
                    st.error(f"生成语音失败: {str(e)}")
        
        if st.session_state.audio_files:
            st.subheader("🎵 语音导览列表")
            for audio in st.session_state.audio_files:
                with st.expander(f"第{audio['day']}天 {audio['period']} - {audio['attraction']}"):
                    try:
                        with open(audio['path'], "rb") as f:
                            audio_data = f.read()
                            st.audio(audio_data, format="audio/mp3")
                            
                            st.download_button(
                                label=f"⬇️ 下载 {audio['attraction']} 导览",
                                data=audio_data,
                                file_name=os.path.basename(audio['path']),
                                mime="audio/mp3"
                            )
                    except Exception as e:
                        st.warning(f"无法播放: {str(e)}")
    
    if st.session_state.generated and st.session_state.itinerary:
        st.header("📋 攻略预览")
        
        itinerary = st.session_state.itinerary
        
        st.subheader(f"📍 {itinerary.get('origin', origin)} → {itinerary['destination']} - {itinerary['days']}天行程")
        st.write(f"**出行人群**: {itinerary['travel_group']}")
        st.write(f"**游玩人数**: {itinerary.get('traveler_count', traveler_count)}人")
        st.write(f"**往返交通**: {itinerary.get('transport', transport)}")
        
        if itinerary.get('departure_date') or itinerary.get('return_date'):
            st.write(f"**出行日期**: {itinerary.get('departure_date', '')} ~ {itinerary.get('return_date', '')}")
        
        sf = itinerary.get('selected_flight')
        if sf and sf is not None:
            flight_label = "航班" if itinerary.get('transport') == "飞机" else "车次"
            with st.expander(f"🛫 去程{flight_label}：{sf.get('flight_no', '')}", expanded=True):
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                with col_f1:
                    st.write(f"**{flight_label}号**: {sf.get('flight_no', '')}")
                    st.write(f"**{'航空公司' if itinerary.get('transport') == '飞机' else '运营方'}**: {sf.get('airline_or_operator', '')}")
                with col_f2:
                    st.write(f"**出发**: {sf.get('departure_time', '')} {sf.get('departure_airport_or_station', '')}")
                    st.write(f"**抵达**: {sf.get('arrival_time', '')} {sf.get('arrival_airport_or_station', '')}")
                with col_f3:
                    st.write(f"**耗时**: {sf.get('duration', '')}")
                    st.write(f"**{'机型' if itinerary.get('transport') == '飞机' else '车型'}**: {sf.get('aircraft_or_train_type', '')}")
                    st.write(f"**准点率**: {sf.get('on_time_rate', '')}")
                with col_f4:
                    st.write(f"**{'舱位' if itinerary.get('transport') == '飞机' else '座席'}**: {sf.get('seat_type', '')}")
                    st.write(f"**单人票价**: ¥{sf.get('price_per_person', 0)}")
                    st.write(f"**{itinerary.get('traveler_count', traveler_count)}人总价**: ¥{sf.get('price_total', 0)}")
                    st.write(f"**行李**: {sf.get('luggage_info', '')}")
        
        srf = itinerary.get('selected_return_flight')
        if srf and srf is not None:
            flight_label = "航班" if itinerary.get('transport') == "飞机" else "车次"
            with st.expander(f"🛬 返程{flight_label}：{srf.get('flight_no', '')}", expanded=True):
                col_f1, col_f2, col_f3, col_f4 = st.columns(4)
                with col_f1:
                    st.write(f"**{flight_label}号**: {srf.get('flight_no', '')}")
                    st.write(f"**{'航空公司' if itinerary.get('transport') == '飞机' else '运营方'}**: {srf.get('airline_or_operator', '')}")
                with col_f2:
                    st.write(f"**出发**: {srf.get('departure_time', '')} {srf.get('departure_airport_or_station', '')}")
                    st.write(f"**抵达**: {srf.get('arrival_time', '')} {srf.get('arrival_airport_or_station', '')}")
                with col_f3:
                    st.write(f"**耗时**: {srf.get('duration', '')}")
                    st.write(f"**{'机型' if itinerary.get('transport') == '飞机' else '车型'}**: {srf.get('aircraft_or_train_type', '')}")
                    st.write(f"**准点率**: {srf.get('on_time_rate', '')}")
                with col_f4:
                    st.write(f"**{'舱位' if itinerary.get('transport') == '飞机' else '座席'}**: {srf.get('seat_type', '')}")
                    st.write(f"**单人票价**: ¥{srf.get('price_per_person', 0)}")
                    st.write(f"**{itinerary.get('traveler_count', traveler_count)}人总价**: ¥{srf.get('price_total', 0)}")
                    st.write(f"**行李**: {srf.get('luggage_info', '')}")
        
        col_budget1, col_budget2, col_budget3 = st.columns(3)
        with col_budget1:
            st.metric("💰 总预算", format_currency(itinerary['total_budget']))
        with col_budget2:
            st.metric("🚄 通勤费用", format_currency(itinerary.get('transport_cost', 0)))
        with col_budget3:
            st.metric("🎒 当地花费", format_currency(itinerary['total_budget'] - itinerary.get('transport_cost', 0)))
        
        st.write(f"**行程概述**: {itinerary['summary']}")
        
        st.subheader("📅 每日行程")
        for day in itinerary['daily_itinerary']:
            with st.expander(f"第{day['day']}天 - {day['title']}"):
                col_morning, col_afternoon = st.columns(2)
                
                with col_morning:
                    st.markdown("### 🌅 上午")
                    st.write(f"**景点**: {day['morning']['attraction']}")
                    st.write(f"**介绍**: {day['morning']['description']}")
                    st.write(f"**时长**: {day['morning']['duration']}")
                    st.write(f"**门票**: {format_currency(day['morning']['ticket_price'])}")
                    
                    st.markdown("### 🍛 午餐")
                    st.write(f"**餐厅**: {day['lunch']['restaurant']}")
                    st.write(f"**推荐**: {day['lunch']['dish']}")
                
                with col_afternoon:
                    st.markdown("### 🌤️ 下午")
                    st.write(f"**景点**: {day['afternoon']['attraction']}")
                    st.write(f"**介绍**: {day['afternoon']['description']}")
                    st.write(f"**时长**: {day['afternoon']['duration']}")
                    st.write(f"**门票**: {format_currency(day['afternoon']['ticket_price'])}")
                    
                    st.markdown("### 🍽️ 晚餐")
                    st.write(f"**餐厅**: {day['dinner']['restaurant']}")
                    st.write(f"**推荐**: {day['dinner']['dish']}")
                
                st.markdown("### 🏨 住宿")
                acc = day['accommodation']
                day_num = day['day']
                if day_num in st.session_state.get('selected_accommodations', {}):
                    st.caption("🎯 您自选的住宿")
                st.write(f"**酒店**: {acc.get('hotel', '')}")
                st.write(f"**位置**: {acc.get('location', '')}")
                if acc.get('price_per_night'):
                    st.write(f"**每晚价格**: {format_currency(acc['price_per_night'])}")
                if acc.get('nearby_attractions'):
                    st.write(f"**附近景点**: {', '.join(acc['nearby_attractions'])}")
                if acc.get('selection_reason'):
                    st.write(f"**选择理由**: {acc['selection_reason']}")
                
                commutes = day.get('commutes', [])
                if commutes:
                    st.markdown("### 🚇 景点间通勤")
                    commute_data = [["出发", "到达", "方式", "耗时", "费用/人", "路线详情"]]
                    total_commute_cost = 0
                    for c in commutes:
                        cost = c.get('cost_per_person', 0)
                        total_commute_cost += cost
                        commute_data.append([
                            c.get('from', ''),
                            c.get('to', ''),
                            c.get('method', ''),
                            c.get('duration', ''),
                            format_currency(cost),
                            c.get('detail', '')
                        ])
                    st.table(commute_data)
                    st.caption(f"当日通勤费用合计：{format_currency(total_commute_cost)}/人")
                
                st.markdown("### 📊 当日预算")
                st.write(f"{format_currency(day['daily_budget'])}")
        
        st.subheader("🍜 美食推荐")
        food_cols = st.columns(3)
        for i, food in enumerate(itinerary['food_recommendations']):
            with food_cols[i % 3]:
                st.write(f"**{food['name']}**")
                st.write(f"{food['description'][:30]}...")
                st.write(f"💰 {format_currency(food['price'])}")
        
        st.subheader("⚠️ 注意事项")
        for tip in itinerary['tips']:
            st.write(f"• {tip}")
        
        st.subheader("🎒 出行清单")
        for item in itinerary['packing_list']:
            st.write(f"• {item}")
        
        st.markdown("---")
        st.header("💬 AI 对话 — 提出修改要求")
        st.caption("告诉 AI 你想怎么调整攻略，例如：\"第2天换成去长城\"、\"预算太紧，减少住宿开支\"、\"增加更多美食推荐\"")
        
        chat_container = st.container(height=320)
        with chat_container:
            if not st.session_state.chat_display:
                st.info("👋 你可以提出任何修改要求，AI 会据此调整攻略。")
            for msg in st.session_state.chat_display:
                if msg["role"] == "user":
                    st.chat_message("user").write(msg["content"])
                else:
                    st.chat_message("assistant").write(msg["content"])
        
        col_chat_input, col_chat_send, col_chat_clear = st.columns([8, 1, 1])
        with col_chat_input:
            user_input = st.text_input(
                "修改要求",
                placeholder="输入你的修改要求...",
                label_visibility="collapsed",
                key="chat_input_field"
            )
        with col_chat_send:
            send_clicked = st.button("发送", use_container_width=True, key="chat_send_btn")
        with col_chat_clear:
            clear_clicked = st.button("清空", use_container_width=True, key="chat_clear_btn")
        
        if clear_clicked:
            st.session_state.chat_history = []
            st.session_state.chat_display = []
            st.rerun()
        
        if send_clicked and user_input.strip():
            st.session_state.chat_display.append({"role": "user", "content": user_input.strip()})
            st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
            
            with st.spinner("🤔 AI 正在修改攻略..."):
                try:
                    llm_client = LLMClient(provider=provider_key)
                    refined = llm_client.refine_itinerary(
                        itinerary=st.session_state.itinerary,
                        chat_history=st.session_state.chat_history[:-1],
                        user_request=user_input.strip()
                    )
                    st.session_state.itinerary = refined
                    
                    change_summary_parts = []
                    if refined.get('summary'):
                        change_summary_parts.append(f"✅ 攻略已更新！概述：{refined['summary'][:60]}...")
                    else:
                        change_summary_parts.append("✅ 攻略已更新！")
                    
                    ai_reply = change_summary_parts[0]
                    st.session_state.chat_display.append({"role": "assistant", "content": ai_reply})
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
                    
                    st.rerun()
                except Exception as e:
                    error_msg = f"❌ 修改失败：{str(e)}"
                    st.session_state.chat_display.append({"role": "assistant", "content": error_msg})
                    st.rerun()

if __name__ == "__main__":
    main()
import json
import requests
from typing import Dict, Any, List
from config.settings import settings

class LLMClient:
    def __init__(self, provider: str = "deepseek"):
        self.provider = provider
        self.api_key = self._get_api_key()
        self.api_base = self._get_api_base()
        self.model = self._get_model()
    
    def _get_api_key(self) -> str:
        if self.provider == "deepseek":
            return settings.DEEPSEEK_API_KEY
        elif self.provider == "doubao":
            return settings.DOUBAN_API_KEY
        else:
            return settings.OPENAI_API_KEY
    
    def _get_api_base(self) -> str:
        if self.provider == "deepseek":
            return settings.DEEPSEEK_API_BASE
        elif self.provider == "doubao":
            return settings.DOUBAN_API_BASE
        else:
            return settings.OPENAI_API_BASE
    
    def _get_model(self) -> str:
        if self.provider == "deepseek":
            return settings.DEEPSEEK_MODEL
        elif self.provider == "doubao":
            return settings.DOUBAN_MODEL
        else:
            return settings.OPENAI_MODEL
    
    def search_flights(self, origin: str, destination: str, departure_date: str, transport: str, traveler_count: int, is_return: bool = False) -> List[Dict[str, Any]]:
        transport_label = "航班" if transport == "飞机" else "车次"
        direction = "返程" if is_return else "去程"
        from_city = destination if is_return else origin
        to_city = origin if is_return else destination
        prompt = f"""
你是专业旅行顾问，请根据以下信息推荐{direction}{transport_label}：

出发城市：{from_city}
目的城市：{to_city}
出发日期：{departure_date}
交通方式：{transport}
人数：{traveler_count}人

请推荐6-8个从{from_city}到{to_city}的{transport_label}，输出JSON数组格式：
[
    {{
        "flight_no": "{transport_label}号",
        "departure_time": "出发时间 HH:MM",
        "arrival_time": "抵达时间 HH:MM",
        "duration": "耗时",
        "price_per_person": 单人票价（元）,
        "price_total": {traveler_count}人总价（元）,
        "airline_or_operator": "航空公司或铁路局",
        "seat_type": "舱位/座席等级",
        "departure_airport_or_station": "出发机场/车站",
        "arrival_airport_or_station": "抵达机场/车站",
        "aircraft_or_train_type": "机型/车型",
        "on_time_rate": "准点率（如95%）",
        "luggage_info": "行李额/携带说明"
    }}
]

要求：
1. 输出必须是有效的JSON数组。
2. 时间必须符合{transport}的实际情况，包含早中晚不同时段。
3. 票价需参考{from_city}到{to_city}的{transport}真实市场价。
4. {transport_label}号格式要真实（如CA1234、G102等）。
5. 按出发时间从早到晚排列。
6. 机场/车站名称要真实（如上海虹桥站、首都机场T3等）。
7. 机型/车型要真实（如Boeing 737-800、复兴号CR400AF等）。
"""
        try:
            if self.provider == "deepseek":
                content = self._call_deepseek_raw(prompt)
            elif self.provider == "doubao":
                content = self._call_doubao_raw(prompt)
            else:
                content = self._call_openai_raw(prompt)
            return self._parse_json_array(content)
        except Exception as e:
            raise Exception(f"搜索{transport_label}失败: {str(e)}")

    def search_accommodations(self, destination: str, travel_group: str, traveler_count: int, budget_per_night: float = 0, preferred_area: str = "") -> List[Dict[str, Any]]:
        budget_hint = f"\n每晚预算上限：约¥{budget_per_night:.0f}" if budget_per_night > 0 else ""
        area_hint = f"\n偏好区域/商圈：{preferred_area}" if preferred_area else ""
        prompt = f"""
你是专业旅行顾问，请根据以下信息推荐{destination}的住宿选项：

目的地：{destination}
出行人群：{travel_group}
人数：{traveler_count}人{budget_hint}{area_hint}

请推荐8-10个{destination}的住宿选项，涵盖不同区域和价位，输出JSON数组格式：
[
    {{
        "hotel": "酒店/民宿名称",
        "type": "住宿类型（如：经济型酒店、商务酒店、精品民宿、度假酒店、青年旅舍等）",
        "location": "所在区域/商圈",
        "price_per_night": 每晚价格（元）,
        "rating": "评分（如4.5/5）",
        "nearby_attractions": ["附近景点1", "附近景点2"],
        "transport_convenience": "交通便利性说明（如：地铁X号线XX站步行5分钟）",
        "description": "简要介绍（30字以内）",
        "suitable_for": "适合人群（如：情侣、家庭、商务等）",
        "amenities": "主要设施（如：WiFi、早餐、停车场、健身房等）"
    }}
]

要求：
1. 输出必须是有效的JSON数组。
2. 推荐应覆盖{destination}主要旅游区域，方便游览不同景点。
3. 价格需参考{destination}真实住宿市场价，包含经济型到中高档不同价位。
4. nearby_attractions需列出该住宿附近真实可到达的景点（2-4个）。
5. 按每晚价格从低到高排列。
6. 住宿类型要多样化，包含酒店和民宿等。
7. 酒店名称和区域要真实可信。
"""
        try:
            if self.provider == "deepseek":
                content = self._call_deepseek_raw(prompt)
            elif self.provider == "doubao":
                content = self._call_doubao_raw(prompt)
            else:
                content = self._call_openai_raw(prompt)
            return self._parse_json_array(content)
        except Exception as e:
            raise Exception(f"搜索住宿失败: {str(e)}")

    def _call_deepseek_raw(self, prompt: str) -> str:
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _call_doubao_raw(self, prompt: str) -> str:
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "thinking": {"type": "disabled"}}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _call_openai_raw(self, prompt: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content

    def _parse_json_array(self, content: str) -> List[Dict[str, Any]]:
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        start_idx = content.find("[")
        end_idx = content.rfind("]") + 1
        if start_idx == -1 or end_idx == 0:
            raise ValueError("无法找到JSON数组内容")
        json_str = content[start_idx:end_idx]
        return json.loads(json_str)

    def _build_prompt(self, origin: str, destination: str, days: int, travel_group: str, traveler_count: int, transport: str, budget: float, departure_date: str = "", return_date: str = "", selected_flight: Dict[str, Any] = None, selected_return_flight: Dict[str, Any] = None, selected_accommodations: Dict[int, Dict[str, Any]] = None) -> str:
        flight_info = ""
        arrival_constraint = ""
        if selected_flight:
            flight_info += f"""
已选去程{('航班' if transport == '飞机' else '车次')}：
- {('航班' if transport == '飞机' else '车次')}号：{selected_flight.get('flight_no', '')}
- 出发：{selected_flight.get('departure_time', '')} {selected_flight.get('departure_airport_or_station', '')}
- 抵达：{selected_flight.get('arrival_time', '')} {selected_flight.get('arrival_airport_or_station', '')}
- 耗时：{selected_flight.get('duration', '')}
- 单人票价：¥{selected_flight.get('price_per_person', 0)}
- {traveler_count}人总价：¥{selected_flight.get('price_total', 0)}
- {'航空公司' if transport == '飞机' else '运营方'}：{selected_flight.get('airline_or_operator', '')}
- {'舱位' if transport == '飞机' else '座席'}：{selected_flight.get('seat_type', '')}
"""
            arrival_constraint = f"""
重要：用户将于第1天 {selected_flight.get('arrival_time', '')} 抵达{destination}，请根据抵达时间合理安排第1天行程：
- 如果抵达时间在上午（12:00前），第1天可以安排下午景点+晚餐。
- 如果抵达时间在下午（12:00-17:00），第1天只安排傍晚/晚间活动和晚餐。
- 如果抵达时间在晚间（17:00后），第1天仅安排入住和晚餐/夜宵。
- 第1天的morning字段请改为"抵达"场景描述（如"抵达{destination}，前往酒店办理入住"）。
"""
        if selected_return_flight:
            flight_info += f"""
已选返程{('航班' if transport == '飞机' else '车次')}：
- {('航班' if transport == '飞机' else '车次')}号：{selected_return_flight.get('flight_no', '')}
- 出发：{selected_return_flight.get('departure_time', '')} {selected_return_flight.get('departure_airport_or_station', '')}
- 抵达：{selected_return_flight.get('arrival_time', '')} {selected_return_flight.get('arrival_airport_or_station', '')}
- 耗时：{selected_return_flight.get('duration', '')}
- 单人票价：¥{selected_return_flight.get('price_per_person', 0)}
- {traveler_count}人总价：¥{selected_return_flight.get('price_total', 0)}
- {'航空公司' if transport == '飞机' else '运营方'}：{selected_return_flight.get('airline_or_operator', '')}
- {'舱位' if transport == '飞机' else '座席'}：{selected_return_flight.get('seat_type', '')}
"""
            arrival_constraint += f"""
重要：用户将于最后1天 {selected_return_flight.get('departure_time', '')} 从{destination}出发返程，请根据出发时间合理安排最后1天行程：
- 如果出发时间在上午（12:00前），最后1天仅安排早餐和前往机场/车站。
- 如果出发时间在下午（12:00-17:00），最后1天可以安排上午景点+午餐，然后前往机场/车站。
- 如果出发时间在晚间（17:00后），最后1天可以安排上午+下午景点，傍晚前往机场/车站。
"""

        date_info = ""
        if departure_date:
            date_info += f"\n出发日期：{departure_date}"
        if return_date:
            date_info += f"\n返程日期：{return_date}"

        accommodation_info = ""
        accommodation_constraint = ""
        if selected_accommodations:
            accommodation_info = "\n用户已自选住宿：\n"
            for day_num, acc in selected_accommodations.items():
                accommodation_info += f"- 第{day_num}天：{acc.get('hotel', '')}（{acc.get('location', '')}，¥{acc.get('price_per_night', 0)}/晚，类型：{acc.get('type', '')}）\n"
            accommodation_constraint = """
重要：用户已为部分或全部天数自选了住宿，请在对应天的accommodation字段中严格使用用户选择的酒店，不要替换。
将用户选择的酒店信息填入accommodation字段，nearby_attractions和selection_reason根据该酒店实际位置合理填写。
"""

        return f"""
你是专业旅行规划师，请根据以下信息生成详细旅行攻略：

出发城市：{origin}
目的地：{destination}{date_info}
旅行天数：{days}天
出行人群：{travel_group}
游玩人数：{traveler_count}人
往返交通方式：{transport}
总预算：¥{budget}（已包含往返交通费用，请将通勤费用计入预算分配）
{flight_info}{accommodation_info}
{arrival_constraint}{accommodation_constraint}
请输出JSON格式攻略：
{{
    "origin": "出发城市名称",
    "destination": "目的地名称",
    "departure_date": "出发日期",
    "return_date": "返程日期",
    "days": 天数,
    "travel_group": "出行人群",
    "traveler_count": 游玩人数,
    "transport": "往返交通方式",
    "transport_cost": 往返交通总费用（元，往返合计）,
    "selected_flight": {{"flight_no":"去程航次号","departure_time":"出发时间","arrival_time":"抵达时间","duration":"耗时","price_per_person":0,"price_total":0,"airline_or_operator":"运营方","seat_type":"舱位/座席","departure_airport_or_station":"出发机场/车站","arrival_airport_or_station":"抵达机场/车站"}},
    "selected_return_flight": {{"flight_no":"返程航次号","departure_time":"出发时间","arrival_time":"抵达时间","duration":"耗时","price_per_person":0,"price_total":0,"airline_or_operator":"运营方","seat_type":"舱位/座席","departure_airport_or_station":"出发机场/车站","arrival_airport_or_station":"抵达机场/车站"}},
    "total_budget": 总预算,
    "summary": "行程概述",
    "daily_itinerary": [
        {{
            "day": 天数,
            "title": "当天主题",
            "morning": {{"attraction": "景点","description":"介绍","duration":"时长","ticket_price":0,"tips":"贴士"}},
            "lunch": {{"restaurant":"餐厅","dish":"菜品","price_per_person":0,"description":"介绍"}},
            "afternoon": {{"attraction": "景点","description":"介绍","duration":"时长","ticket_price":0,"tips":"贴士"}},
            "dinner": {{"restaurant":"餐厅","dish":"菜品","price_per_person":0,"description":"介绍"}},
            "accommodation": {{
                "hotel": "酒店名称",
                "price_per_night": 每晚价格,
                "location": "酒店所在区域/商圈",
                "description": "酒店简介",
                "nearby_attractions": ["该酒店附近方便到达的景点1","景点2"],
                "selection_reason": "选择该酒店的合理性说明（如：位于XX和XX之间，步行可达XX景区，方便当天和次日行程）"
            }},
            "commutes": [
                {{
                    "from": "出发地点（如：酒店、上午景点名、午餐餐厅名等）",
                    "to": "到达地点（如：上午景点名、午餐餐厅名、下午景点名等）",
                    "method": "通勤方式（如：步行、地铁、公交、出租车、骑行等）",
                    "duration": "预计耗时（如：15分钟、约30分钟）",
                    "cost_per_person": 单人费用（元）,
                    "detail": "通勤详情（如：乘坐地铁2号线XX站→XX站，或步行沿XX路约800米等）"
                }}
            ],
            "daily_budget": 当天预算
        }}
    ],
    "food_recommendations": [{{"name":"美食","description":"介绍","price":0,"location":"地点"}}],
    "shopping_recommendations": [{{"name":"地点","description":"介绍","specialty":"特色"}}],
    "tips": ["注意事项"],
    "packing_list": ["物品"]
}}

要求：
1. 输出必须是有效的JSON格式，内容详细实用。
2. transport_cost 字段必须估算 {traveler_count} 人从{origin}到{destination}往返{transport}的大致总费用，并从总预算中扣除这部分。
3. daily_budget 合计（加上transport_cost）应等于 total_budget。
4. 给出的景点门票、餐饮、住宿等价格需根据 {traveler_count} 人合理估算。
5. selected_flight 字段填入用户已选的航次信息（如未选则填null）。
6. **住宿安排必须合理**：每天选择的酒店应靠近当天和/或次日要参观的景点，避免不必要的长途通勤。在accommodation.selection_reason中说明选择理由，在accommodation.nearby_attractions中列出酒店附近方便到达的景点。
7. **通勤信息必须详细**：每天的commutes数组必须包含当天所有活动之间的通勤路线，按时间顺序排列，至少包括：
   - 酒店→上午景点（或抵达后→酒店/上午景点）
   - 上午景点→午餐餐厅
   - 午餐餐厅→下午景点
   - 下午景点→晚餐餐厅
   - 晚餐餐厅→酒店
   每段通勤需给出具体的交通方式（地铁/公交/出租车/步行/骑行等）、预计耗时、单人费用和路线详情。
8. 通勤费用应计入daily_budget中，确保预算完整。
"""
    
    def generate_itinerary(self, origin: str, destination: str, days: int, travel_group: str, traveler_count: int, transport: str, budget: float, departure_date: str = "", return_date: str = "", selected_flight: Dict[str, Any] = None, selected_return_flight: Dict[str, Any] = None, selected_accommodations: Dict[int, Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = self._build_prompt(origin, destination, days, travel_group, traveler_count, transport, budget, departure_date, return_date, selected_flight, selected_return_flight, selected_accommodations)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.provider == "deepseek":
                    return self._call_deepseek(prompt)
                elif self.provider == "doubao":
                    return self._call_doubao(prompt)
                else:
                    return self._call_openai(prompt)
            except ValueError as e:
                if "JSON解析失败" in str(e) and attempt < max_retries - 1:
                    prompt = prompt + "\n\n【重要提醒】上次生成的JSON格式有误，请务必输出严格合法的JSON，不要遗漏逗号，不要有多余逗号，字符串中的引号必须转义。"
                    continue
                raise Exception(f"生成攻略失败: {str(e)}")
            except Exception as e:
                raise Exception(f"生成攻略失败: {str(e)}")
        raise Exception("生成攻略失败: 多次重试后JSON仍无法解析")
    
    def refine_itinerary(self, itinerary: Dict[str, Any], chat_history: List[Dict[str, str]], user_request: str) -> Dict[str, Any]:
        current_json = json.dumps(itinerary, ensure_ascii=False, indent=2)
        system_prompt = f"""你是专业旅行规划师。用户已有一份旅行攻略，现在提出了修改要求。

当前攻略JSON如下：
{current_json}

请根据用户的修改要求，调整攻略并输出完整的JSON格式攻略（结构与原攻略完全一致）。
要求：
1. 输出必须是有效的JSON格式，保持原有结构不变。
2. 只修改用户要求的部分，其余保持不变。
3. 确保修改后的预算仍然合理。
4. 每天的commutes数组必须包含当天所有活动之间的通勤路线（酒店→上午景点→午餐→下午景点→晚餐→酒店），每段通勤需给出方式、耗时、费用和路线详情。
5. 每天的accommodation必须包含nearby_attractions（附近景点）和selection_reason（选择理由），确保住宿安排合理。
6. 不要输出任何解释文字，只输出JSON。"""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in chat_history:
            messages.append(msg)
        messages.append({"role": "user", "content": user_request})

        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self.provider == "deepseek":
                    return self._call_deepseek_with_messages(messages)
                elif self.provider == "doubao":
                    return self._call_doubao_with_messages(messages)
                else:
                    return self._call_openai_with_messages(messages)
            except ValueError as e:
                if "JSON解析失败" in str(e) and attempt < max_retries - 1:
                    messages.append({"role": "assistant", "content": "[上次输出JSON格式有误]"})
                    messages.append({"role": "user", "content": "上次生成的JSON格式有误，请务必输出严格合法的JSON，不要遗漏逗号，不要有多余逗号，字符串中的引号必须转义。请重新输出完整的攻略JSON。"})
                    continue
                raise Exception(f"修改攻略失败: {str(e)}")
            except Exception as e:
                raise Exception(f"修改攻略失败: {str(e)}")
        raise Exception("修改攻略失败: 多次重试后JSON仍无法解析")

    def _call_deepseek_with_messages(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"model": self.model, "messages": messages, "temperature": 0.7}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return self._parse_json(content)

    def _call_doubao_with_messages(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"model": self.model, "messages": messages, "temperature": 0.7, "thinking": {"type": "disabled"}}
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return self._parse_json(content)

    def _call_openai_with_messages(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        content = response.choices[0].message.content
        return self._parse_json(content)

    def _call_deepseek(self, prompt: str) -> Dict[str, Any]:
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return self._parse_json(content)
    
    def _call_doubao(self, prompt: str) -> Dict[str, Any]:
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        data = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "thinking": {"type": "disabled"}}
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return self._parse_json(content)
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.api_base)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        content = response.choices[0].message.content
        return self._parse_json(content)
    
    def _parse_json(self, content: str) -> Dict[str, Any]:
        content = content.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        start_idx = content.find("{")
        end_idx = content.rfind("}") + 1
        
        if start_idx == -1:
            raise ValueError("无法找到JSON内容")
        
        if end_idx == 0:
            json_str = self._close_brackets(content[start_idx:])
        else:
            json_str = content[start_idx:end_idx]
        
        for repair_fn in [lambda s: s, self._fix_json, self._repair_json_aggressive]:
            try:
                repaired = repair_fn(json_str)
                return json.loads(repaired)
            except (json.JSONDecodeError, Exception):
                continue
        
        raise ValueError(f"JSON解析失败（所有修复策略均无效）\n原始内容片段: {content[:500]}")

    def _repair_json_aggressive(self, s: str) -> str:
        s = self._fix_json(s)
        for _ in range(80):
            try:
                json.loads(s)
                return s
            except json.JSONDecodeError as e:
                pos = e.pos
                msg = e.msg
                if pos >= len(s):
                    s = self._close_brackets(s)
                    continue

                fixed = False

                if msg == "Expecting ',' delimiter":
                    ch = s[pos] if pos < len(s) else ''
                    before = s[:pos].rstrip()
                    if before and before[-1] in ('"', ']', '}', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'l', 'e'):
                        s = s[:pos] + ',' + s[pos:]
                        fixed = True
                    else:
                        for j in range(pos - 1, max(pos - 200, -1), -1):
                            if s[j] == '"':
                                quote_check = s[:j]
                                if quote_check.count('"') % 2 == 1:
                                    s = s[:j] + '\\"' + s[j + 1:]
                                    fixed = True
                                    break
                        if not fixed:
                            s = s[:pos] + ',' + s[pos:]
                            fixed = True

                elif msg == "Expecting property name enclosed in double quotes":
                    if pos < len(s) and s[pos] == '}':
                        for j in range(pos - 1, max(pos - 50, -1), -1):
                            if s[j] == ',':
                                s = s[:j] + s[j + 1:]
                                fixed = True
                                break
                    elif pos < len(s) and s[pos] == ']':
                        for j in range(pos - 1, max(pos - 50, -1), -1):
                            if s[j] == ',':
                                s = s[:j] + s[j + 1:]
                                fixed = True
                                break
                    if not fixed:
                        for j in range(pos - 1, max(pos - 200, -1), -1):
                            if s[j] == '"':
                                s = s[:j] + '\\"' + s[j + 1:]
                                fixed = True
                                break

                elif msg == "Expecting value":
                    if pos < len(s) and s[pos] in ('}', ']'):
                        for j in range(pos - 1, max(pos - 50, -1), -1):
                            if s[j] == ',':
                                s = s[:j] + s[j + 1:]
                                fixed = True
                                break
                    elif pos < len(s) and s[pos] == '"':
                        for j in range(pos - 1, max(pos - 200, -1), -1):
                            if s[j] == '"':
                                s = s[:j] + '\\"' + s[j + 1:]
                                fixed = True
                                break

                elif "Unterminated string" in msg:
                    s = s[:pos] + '"' + s[pos:]
                    fixed = True

                elif "Extra data" in msg:
                    s = self._close_brackets(s[:pos])
                    fixed = True

                elif "Invalid \\escape" in msg:
                    for j in range(pos - 1, max(pos - 10, -1), -1):
                        if s[j] == '\\':
                            s = s[:j] + s[j + 1:]
                            fixed = True
                            break

                if not fixed:
                    s = self._close_brackets(s)
                    try:
                        json.loads(s)
                        return s
                    except json.JSONDecodeError:
                        break

        s = self._close_brackets(s)
        return s

    def _close_brackets(self, s: str) -> str:
        s = s.rstrip()
        open_braces = s.count('{') - s.count('}')
        open_brackets = s.count('[') - s.count(']')
        if open_brackets > 0:
            s += ']' * open_brackets
        if open_braces > 0:
            s += '}' * open_braces
        return s

    def _fix_json(self, s: str) -> str:
        import re

        s = re.sub(r',\s*([}\]])', r'\1', s)

        def add_missing_comma(match):
            return match.group(1) + ',' + match.group(2)

        s = re.sub(r'(["\d\]\}])\s*\n(\s*["\{\[])', add_missing_comma, s)

        s = re.sub(r'(\})\s*\n(\s*\{)', r'\1,\n\2', s)
        s = re.sub(r'(\])\s*\n(\s*\[)', r'\1,\n\2', s)
        s = re.sub(r'(\])\s*\n(\s*\{)', r'\1,\n\2', s)
        s = re.sub(r'(\})\s*\n(\s*\[)', r'\1,\n\2', s)

        s = re.sub(r'(\d)\s*\n(\s*")', r'\1,\n\2', s)
        s = re.sub(r'(")\s*\n(\s*\d)', r'\1,\n\2', s)
        s = re.sub(r'(")\s*\n(\s*")', r'\1,\n\2', s)
        s = re.sub(r'(\d)\s*\n(\s*\d)', r'\1,\n\2', s)
        s = re.sub(r'(true|false|null)\s*\n(\s*")', r'\1,\n\2', s)
        s = re.sub(r'(true|false|null)\s*\n(\s*\d)', r'\1,\n\2', s)
        s = re.sub(r'(true|false|null)\s*\n(\s*\{)', r'\1,\n\2', s)
        s = re.sub(r'(true|false|null)\s*\n(\s*\[)', r'\1,\n\2', s)
        s = re.sub(r'(")\s*\n(\s*(?:true|false|null))', r'\1,\n\2', s)
        s = re.sub(r'(\d)\s*\n(\s*(?:true|false|null))', r'\1,\n\2', s)

        s = re.sub(r'(\d)\s+(\d)', r'\1,\2', s)
        s = re.sub(r'(\d)\s+(")', r'\1,\2', s)
        s = re.sub(r'(")\s+(\d)', r'\1,\2', s)
        s = re.sub(r'(")\s+(")', r'\1,\2', s)
        s = re.sub(r'(\])\s+(\d)', r'\1,\2', s)
        s = re.sub(r'(\])\s+(")', r'\1,\2', s)
        s = re.sub(r'(\])\s+(\{)', r'\1,\2', s)
        s = re.sub(r'(\])\s+(\[)', r'\1,\2', s)
        s = re.sub(r'(\})\s+(\{)', r'\1,\2', s)
        s = re.sub(r'(\})\s+(\[)', r'\1,\2', s)
        s = re.sub(r'(\})\s+(")', r'\1,\2', s)
        s = re.sub(r'(\})\s+(\d)', r'\1,\2', s)

        s = re.sub(r'\\(?!["\\/bfnrtu])', '', s)

        s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', s)

        return s
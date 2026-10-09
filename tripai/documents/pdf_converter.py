from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from typing import Dict, Any, List
import os
from utils.helpers import format_currency

class PDFConverter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='TitleStyle',
            fontSize=24,
            bold=True,
            alignment=1,
            textColor=colors.darkblue,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='Heading1',
            fontSize=18,
            bold=True,
            textColor=colors.darkblue,
            spaceBefore=15,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='Heading2',
            fontSize=14,
            bold=True,
            textColor=colors.blue,
            spaceBefore=10,
            spaceAfter=5
        ))
    
    def _generate_cover(self, itinerary: Dict[str, Any]) -> List:
        elements = []
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph("智能旅行攻略", self.styles['TitleStyle']))
        route_text = f"{itinerary.get('origin', '')} → {itinerary['destination']}"
        elements.append(Paragraph(route_text, self.styles['Heading1']))
        elements.append(Spacer(1, 0.5*inch))
        
        info_data = [
            ["旅行天数", f"{itinerary['days']}天"],
            ["出行人群", itinerary['travel_group']],
            ["游玩人数", f"{itinerary.get('traveler_count', 1)}人"],
            ["往返交通", itinerary.get('transport', '')],
            ["通勤费用", format_currency(itinerary.get('transport_cost', 0))],
            ["总预算（含通勤）", format_currency(itinerary['total_budget'])]
        ]
        
        if itinerary.get('departure_date'):
            info_data.append(["出行日期", f"{itinerary.get('departure_date', '')} ~ {itinerary.get('return_date', '')}"])
        
        sf = itinerary.get('selected_flight')
        srf = itinerary.get('selected_return_flight')
        if sf and sf is not None:
            transport = itinerary.get('transport', '')
            flight_label = "航班" if transport == "飞机" else "车次"
            info_data.append([
                f"去程{flight_label}",
                f"{sf.get('flight_no', '')} | {sf.get('departure_time', '')}→{sf.get('arrival_time', '')} | {sf.get('duration', '')}"
            ])
        if srf and srf is not None:
            transport = itinerary.get('transport', '')
            flight_label = "航班" if transport == "飞机" else "车次"
            info_data.append([
                f"返程{flight_label}",
                f"{srf.get('flight_no', '')} | {srf.get('departure_time', '')}→{srf.get('arrival_time', '')} | {srf.get('duration', '')}"
            ])
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 2*inch))
        return elements
    
    def _generate_summary(self, itinerary: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("行程概述", self.styles['Heading1']))
        elements.append(Paragraph(itinerary['summary'], self.styles['Normal']))
        
        local_cost = itinerary['total_budget'] - itinerary.get('transport_cost', 0)
        stats_data = [
            ["出发地", itinerary.get('origin', '')],
            ["目的地", itinerary['destination']],
            ["总天数", f"{itinerary['days']}天{itinerary['days']-1}晚"],
            ["游玩人数", f"{itinerary.get('traveler_count', 1)}人 · {itinerary['travel_group']}"],
            ["往返交通", f"{itinerary.get('transport', '')} · 通勤 {format_currency(itinerary.get('transport_cost', 0))}"],
            ["预算分配", f"通勤 {format_currency(itinerary.get('transport_cost', 0))} + 当地 {format_currency(local_cost)} = {format_currency(itinerary['total_budget'])}"]
        ]
        
        if itinerary.get('departure_date'):
            stats_data.append(["出行日期", f"{itinerary.get('departure_date', '')} ~ {itinerary.get('return_date', '')}"])
        
        sf = itinerary.get('selected_flight')
        srf = itinerary.get('selected_return_flight')
        if sf and sf is not None:
            transport = itinerary.get('transport', '')
            flight_label = "航班" if transport == "飞机" else "车次"
            stats_data.append([
                f"去程{flight_label}",
                f"{sf.get('flight_no', '')} {sf.get('departure_time', '')}→{sf.get('arrival_time', '')} 抵达后安排首日行程"
            ])
        if srf and srf is not None:
            transport = itinerary.get('transport', '')
            flight_label = "航班" if transport == "飞机" else "车次"
            stats_data.append([
                f"返程{flight_label}",
                f"{srf.get('flight_no', '')} {srf.get('departure_time', '')}→{srf.get('arrival_time', '')} 出发前安排末尾天行程"
            ])
        
        stats_table = Table(stats_data, colWidths=[2*inch, 4*inch])
        
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(stats_table)
        return elements
    
    def _generate_daily_itinerary(self, itinerary: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("每日行程", self.styles['Heading1']))
        
        for day in itinerary['daily_itinerary']:
            elements.append(Paragraph(f"第{day['day']}天 - {day['title']}", self.styles['Heading2']))
            
            elements.append(Paragraph(f"上午：{day['morning']['attraction']}", self.styles['Normal']))
            elements.append(Paragraph(f"介绍：{day['morning']['description']}", self.styles['Normal']))
            elements.append(Paragraph(f"时长：{day['morning']['duration']} | 门票：{format_currency(day['morning']['ticket_price'])}", self.styles['Normal']))
            
            elements.append(Paragraph(f"午餐：{day['lunch']['restaurant']} | 推荐：{day['lunch']['dish']}", self.styles['Normal']))
            
            elements.append(Paragraph(f"下午：{day['afternoon']['attraction']}", self.styles['Normal']))
            elements.append(Paragraph(f"介绍：{day['afternoon']['description']}", self.styles['Normal']))
            
            elements.append(Paragraph(f"晚餐：{day['dinner']['restaurant']} | 推荐：{day['dinner']['dish']}", self.styles['Normal']))
            
            acc = day['accommodation']
            elements.append(Paragraph(f"住宿：{acc.get('hotel', '')} | 位置：{acc.get('location', '')}", self.styles['Normal']))
            if acc.get('price_per_night'):
                elements.append(Paragraph(f"每晚价格：{format_currency(acc['price_per_night'])}", self.styles['Normal']))
            if acc.get('nearby_attractions'):
                elements.append(Paragraph(f"附近景点：{', '.join(acc['nearby_attractions'])}", self.styles['Normal']))
            if acc.get('selection_reason'):
                elements.append(Paragraph(f"选择理由：{acc['selection_reason']}", self.styles['Normal']))
            
            commutes = day.get('commutes', [])
            if commutes:
                elements.append(Paragraph("景点间通勤", self.styles['Heading2']))
                commute_data = [["出发", "到达", "方式", "耗时", "费用/人", "路线详情"]]
                for c in commutes:
                    commute_data.append([
                        c.get('from', ''),
                        c.get('to', ''),
                        c.get('method', ''),
                        c.get('duration', ''),
                        format_currency(c.get('cost_per_person', 0)),
                        c.get('detail', '')
                    ])
                commute_table = Table(commute_data, colWidths=[1*inch, 1*inch, 0.7*inch, 0.7*inch, 0.7*inch, 2*inch])
                commute_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 8)
                ]))
                elements.append(commute_table)
            
            elements.append(Paragraph(f"当日预算：{format_currency(day['daily_budget'])}", self.styles['Normal']))
            elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _generate_food(self, itinerary: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("美食推荐", self.styles['Heading1']))
        
        food_data = [["美食名称", "介绍", "价格", "推荐地点"]]
        for food in itinerary['food_recommendations']:
            food_data.append([
                food['name'],
                food['description'][:30] + "...",
                format_currency(food['price']),
                food['location']
            ])
        
        food_table = Table(food_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1.5*inch])
        food_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(food_table)
        return elements
    
    def _generate_budget(self, itinerary: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("预算明细", self.styles['Heading1']))
        
        budget_data = [["项目", "金额"]]
        budget_data.append([
            f"往返交通（{itinerary.get('transport', '')}，{itinerary.get('traveler_count', 1)}人）",
            format_currency(itinerary.get('transport_cost', 0))
        ])
        for day in itinerary['daily_itinerary']:
            budget_data.append([f"第{day['day']}天", format_currency(day['daily_budget'])])
        budget_data.append(["总计", format_currency(itinerary['total_budget'])])
        
        budget_table = Table(budget_data, colWidths=[2*inch, 4*inch])
        budget_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(budget_table)
        return elements
    
    def _generate_tips(self, itinerary: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("注意事项", self.styles['Heading1']))
        
        for i, tip in enumerate(itinerary['tips'], 1):
            elements.append(Paragraph(f"{i}. {tip}", self.styles['Normal']))
        
        return elements
    
    def _generate_packing(self, itinerary: Dict[str, Any]) -> List:
        elements = []
        elements.append(Paragraph("出行清单", self.styles['Heading1']))
        
        for item in itinerary['packing_list']:
            elements.append(Paragraph(f"• {item}", self.styles['Normal']))
        
        return elements
    
    def generate_document(self, itinerary: Dict[str, Any], output_path: str):
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=inch,
            bottomMargin=inch
        )
        
        elements = []
        elements.extend(self._generate_cover(itinerary))
        elements.append(Paragraph("<pagebreak/>", self.styles['Normal']))
        
        elements.extend(self._generate_summary(itinerary))
        elements.extend(self._generate_daily_itinerary(itinerary))
        elements.extend(self._generate_food(itinerary))
        elements.extend(self._generate_budget(itinerary))
        elements.extend(self._generate_tips(itinerary))
        elements.extend(self._generate_packing(itinerary))
        
        doc.build(elements)
        return output_path
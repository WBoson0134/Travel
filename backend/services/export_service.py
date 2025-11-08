from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from icalendar import Calendar, Event
from datetime import datetime, timedelta, time
import io

class ExportService:
    """导出服务：PDF和ICS格式导出"""
    
    def export_to_pdf(self, trip_data):
        """导出为PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        # 标题
        story.append(Paragraph(f"{trip_data['city']} {trip_data['days']}日游行程", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # 行程信息
        info_text = f"""
        <b>出行节奏：</b>{trip_data.get('pace', 'N/A')}<br/>
        <b>交通方式：</b>{trip_data.get('transport_mode', 'N/A')}<br/>
        <b>优先级：</b>{trip_data.get('priority', 'N/A')}<br/>
        """
        story.append(Paragraph(info_text, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # 每日行程
        for day_plan in trip_data.get('days_plans', []):
            story.append(Paragraph(
                f"第 {day_plan['day_number']} 天",
                heading_style
            ))
            
            if day_plan.get('description'):
                story.append(Paragraph(day_plan['description'], styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
            
            # 活动表格
            activity_data = [['时间', '活动', '地址', '类型']]
            for activity in day_plan.get('activities', []):
                time_str = f"{activity.get('start_time', '')} - {activity.get('end_time', '')}"
                activity_data.append([
                    time_str,
                    activity.get('name', ''),
                    activity.get('address', ''),
                    activity.get('type', '')
                ])
            
            if len(activity_data) > 1:
                table = Table(activity_data, colWidths=[1.5*inch, 2*inch, 2*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
                ]))
                story.append(table)
            
            story.append(Spacer(1, 0.3*inch))
            story.append(PageBreak())
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def export_to_ics(self, trip_data, start_date=None):
        """导出为ICS日历文件"""
        cal = Calendar()
        cal.add('prodid', '-//Travel Planner//Travel Plan//CN')
        cal.add('version', '2.0')
        
        if not start_date:
            start_date = datetime.now().date()
        
        current_date = start_date
        
        for day_plan in trip_data.get('days_plans', []):
            for activity in day_plan.get('activities', []):
                event = Event()
                event.add('summary', activity.get('name', '活动'))
                event.add('description', activity.get('description', ''))
                
                # 解析时间
                start_time_str = activity.get('start_time', '09:00')
                end_time_str = activity.get('end_time', '12:00')
                
                try:
                    start_hour, start_min = map(int, start_time_str.split(':'))
                    end_hour, end_min = map(int, end_time_str.split(':'))
                    
                    start_datetime = datetime.combine(current_date, time(hour=start_hour, minute=start_min))
                    end_datetime = datetime.combine(current_date, time(hour=end_hour, minute=end_min))
                    
                    event.add('dtstart', start_datetime)
                    event.add('dtend', end_datetime)
                    
                    if activity.get('address'):
                        event.add('location', activity['address'])
                    
                    cal.add_component(event)
                except Exception as e:
                    print(f"处理活动时间失败: {e}")
            
            current_date += timedelta(days=1)
        
        return cal.to_ical()


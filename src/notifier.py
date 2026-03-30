"""
通知模块
支持微信推送
"""

import json
import requests
from pathlib import Path
from datetime import datetime

class Notifier:
    def __init__(self, config: dict = None):
        self.config = config or {}
    
    def send_wechat(self, message: str) -> bool:
        """发送微信通知（通过 QClaw）"""
        # 这里集成 OpenClaw 的微信推送
        # 暂时保存到文件
        notification_file = Path("data/notifications.json")
        notification_file.parent.mkdir(exist_ok=True)
        
        notification = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "status": "pending"
        }
        
        notifications = []
        if notification_file.exists():
            with open(notification_file, 'r', encoding='utf-8') as f:
                notifications = json.load(f)
        
        notifications.append(notification)
        
        with open(notification_file, 'w', encoding='utf-8') as f:
            json.dump(notifications, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 通知已保存到 {notification_file}")
        return True
    
    def format_opportunity(self, opp: dict) -> str:
        """格式化套利机会为微信消息"""
        msg = f"""🎯 套利机会发现！

📦 {opp['name']}

💰 价格对比:
├─ AmiAmi: ¥{opp['amiami_price']:,} (原价 ¥{opp['amiami_original_price']:,})
├─ 折扣: {opp['discount']}%
├─ 成色: {opp['condition']}
└─ Mercari 预期: ¥{opp['mercari_adjusted_price']:,}

📊 利润分析:
├─ 净利润: ¥{opp['net_profit']:,}
└─ 利润率: {opp['profit_rate']:.1f}%

🔗 购买链接:
{opp['amiami_url']}
"""
        return msg
    
    def send_opportunities(self, opportunities: list):
        """发送所有套利机会"""
        if not opportunities:
            print("没有套利机会需要通知")
            return
        
        # 合并消息
        if len(opportunities) == 1:
            message = self.format_opportunity(opportunities[0])
        else:
            message = f"🎯 发现 {len(opportunities)} 个套利机会！\n\n"
            for i, opp in enumerate(opportunities[:5], 1):  # 最多显示5个
                message += f"{i}. {opp['name']}\n"
                message += f"   利润: ¥{opp['net_profit']:,} ({opp['profit_rate']:.0f}%)\n"
                message += f"   {opp['amiami_url']}\n\n"
            
            if len(opportunities) > 5:
                message += f"... 还有 {len(opportunities) - 5} 个机会"
        
        self.send_wechat(message)

# feishu_client.py - 飞书 API 封装
# 负责与飞书多维表格 API 交互

import os
from dotenv import load_dotenv

# Step 2.1: 加载环境变量
load_dotenv()

APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")
APP_TOKEN = os.getenv("FEISHU_APP_TOKEN")
TABLE_ID = os.getenv("FEISHU_TABLE_ID")

# 初始化飞书客户端
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *

client = lark.Client.builder() \
    .app_id(APP_ID) \
    .app_secret(APP_SECRET) \
    .log_level(lark.LogLevel.WARNING) \
    .build()


def create_record(fields: dict) -> str:
    """
    Step 2.2: 创建表格记录
    在飞书多维表格中插入新记录
    返回新记录的 record_id，失败返回空字符串
    """
    try:
        request = CreateAppTableRecordRequest.builder() \
            .app_token(APP_TOKEN) \
            .table_id(TABLE_ID) \
            .request_body(AppTableRecord.builder()
                .fields(fields)
                .build()) \
            .build()
        
        response = client.bitable.v1.app_table_record.create(request)
        
        if response.success():
            record_id = response.data.record.record_id
            print(f"[飞书] 创建记录成功: {record_id}")
            return record_id
        else:
            print(f"[飞书] 创建记录失败: {response.code} - {response.msg}")
            return ""
    except Exception as e:
        print(f"[飞书] 创建记录异常: {e}")
        return ""


def find_record(position_id: str) -> str:
    """
    Step 2.3: 查询记录
    根据 positionId 查询飞书表格中的记录
    返回 record_id，未找到返回 None
    """
    try:
        # 使用搜索 API 查询
        request = SearchAppTableRecordRequest.builder() \
            .app_token(APP_TOKEN) \
            .table_id(TABLE_ID) \
            .request_body(SearchAppTableRecordRequestBody.builder()
                .filter(FilterInfo.builder()
                    .conjunction("and")
                    .conditions([Condition.builder()
                        .field_name("positionId")
                        .operator("is")
                        .value([position_id])
                        .build()])
                    .build())
                .build()) \
            .build()
        
        response = client.bitable.v1.app_table_record.search(request)
        
        if response.success():
            items = response.data.items
            if items and len(items) > 0:
                return items[0].record_id
        return None
    except Exception as e:
        print(f"[飞书] 查询记录异常: {e}")
        raise e # 抛出异常，中断流程，防止主程序误判为"不存在"而创建重复记录


def update_record(record_id: str, fields: dict) -> bool:
    """
    Step 2.4: 更新表格记录
    更新飞书多维表格中的现有记录
    返回布尔值表示成功或失败
    """
    try:
        request = UpdateAppTableRecordRequest.builder() \
            .app_token(APP_TOKEN) \
            .table_id(TABLE_ID) \
            .record_id(record_id) \
            .request_body(AppTableRecord.builder()
                .fields(fields)
                .build()) \
            .build()
        
        response = client.bitable.v1.app_table_record.update(request)
        
        if response.success():
            print(f"[飞书] 更新记录成功: {record_id}")
            return True
        else:
            print(f"[飞书] 更新记录失败: {response.code} - {response.msg}")
            return False
    except Exception as e:
        print(f"[飞书] 更新记录异常: {e}")
        return False


def get_all_records() -> dict:
    """
    Step 2.5: 批量获取所有记录
    遍历整个表格，构建 positionId -> CacheData 的映射
    用于程序启动时快速建立缓存，避免 N+1 次 API 查询
    """
    print("[飞书] 正在全量同步表格数据以建立缓存...")
    cache_map = {}
    page_token = ""
    has_more = True
    
    try:
        while has_more:
            request = ListAppTableRecordRequest.builder() \
                .app_token(APP_TOKEN) \
                .table_id(TABLE_ID) \
                .page_size(100) \
                .page_token(page_token) \
                .build()
            
            response = client.bitable.v1.app_table_record.list(request)
            
            if response.success():
                items = response.data.items or []
                for item in items:
                    fields = item.fields
                    pid = fields.get("positionId")
                    if pid:
                        # 提取构建缓存所需的数据
                        cache_map[pid] = {
                            "record_id": item.record_id,
                            "entry_price": float(fields.get("入场价", 0)),
                            "leverage": int(fields.get("杠杆", 0))
                        }
                
                has_more = response.data.has_more
                page_token = response.data.page_token
                print(f"[飞书] 已加载 {len(cache_map)} 条记录...")
            else:
                print(f"[飞书] 列表获取失败: {response.code} - {response.msg}")
                break
                
        print(f"[飞书] 缓存建立完成，共 {len(cache_map)} 条记录")
        return cache_map
    except Exception as e:
        print(f"[飞书] 批量获取异常: {e}")
        return {}




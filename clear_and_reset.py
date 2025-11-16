#!/usr/bin/env python3
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print('清空数据库中...')

# Delete all
batch_size = 1000
deleted_total = 0

while True:
    records = supabase.table('cards').select('id').limit(batch_size).execute()
    if not records.data:
        break
    
    for r in records.data:
        try:
            supabase.table('cards').delete().eq('id', r['id']).execute()
            deleted_total += 1
        except:
            pass
    
    if len(records.data) < batch_size:
        break
    
    print(f'已删除 {deleted_total} 条...')

count = supabase.table('cards').select('*', count='exact').execute().count
print(f'\n✅ 清空完成')
print(f'📊 剩余记录: {count}')
print(f'🗑️  共删除: {deleted_total}')
print(f'\n⚠️  ID 序列需要手动重置:')
print(f'    在 Supabase SQL Editor 执行:')
print(f'    TRUNCATE TABLE cards RESTART IDENTITY CASCADE;')

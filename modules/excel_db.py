from openpyxl import Workbook
import pandas as pd
import os
import time
import logging
logger = logging.getLogger(__name__)
def init():
    # file_handler = logging.FileHandler('app.log')
    # file_handler.setLevel(logging.WARNING)
    # file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    # logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
    logger.addHandler(stream_handler)

def createindex_row(df, key, vkeys, dttype='hash', start=0, end=-1, processdiv=999):
    '''
    创建索引
    批次读取(pandas版本未支持)
    例: key='商品单号', vkeys=['退商品金额（元）', '售后状态']
    '''
    logger.warning(f'----开始建立索引,{key}:{vkeys}----')

    result = dict()
    chunksize = 1000

    totalCount = 0
    divCount = 0

    # for _, row in df.iterrows():
    #     result[row[key]] = tuple(row[vk] for vk in vkeys)

    for index in df.index:
        if index < start: continue
        if end != -1 and index >= end: break
        row = df.loc[index]
        
        try:
            if dttype == 'hash':
                result[str(row[key])] = {vk: str(row[vk]) for vk in vkeys}
            elif dttype == 'list':
                result[str(row[key])] = list(str(row[vk]) for vk in vkeys)
            elif dttype == 'tuple':
                result[str(row[key])] = tuple(str(row[vk]) for vk in vkeys)
        except Exception as e:
            raise type(e) (f'{e}\n\n行号:{index}\n{row}')

        totalCount += 1
        divCount += 1
        if divCount > processdiv:
            divCount = 0
            logger.warning(f'已处理{totalCount}条')

    logger.warning(f'{totalCount}条处理完毕')
    logger.warning(f'----索引建立完成----')
    return result

class HashableWrapper:
    def __init__(self, obj):
        self.obj = obj

    def __hash__(self):
        return id(self.obj)

    def __eq__(self, other):
        return self.obj is other.obj

    def __repr__(self):
        return repr(self.obj)
    
def createindex_class(df, chandlers:dict, start=0, end=-1, processdiv=999):
    '''
    创建类索引
    批次读取(pandas版本未支持)
    例: chandlers = {
        '耙耙柑': lambda row: row['选购商品'] == '耙耙柑', 
    }
    '''
    logger.warning(f'----开始建立类索引,{list(chandlers.keys())}----')

    result = dict()
    chunksize = 1000
    totalCount = 0
    divCount = 0

    result = {cname: set() for cname in chandlers}
    for index in df.index:
        if index < start: continue
        if end != -1 and index >= end: break
        row = df.loc[index]

        try:
            for cname, call in chandlers.items():
                if callable(call):
                    condition = call
                    resulthandler = HashableWrapper
                elif isinstance(call, (list, tuple)):
                    if not call: raise Exception(f'处理器列表为空,请检查')
                    if not callable(call[0]): raise Exception(f'条件处理器不可调用,{call[0]}')
                    condition = call[0]
                    if len(call) >= 2: 
                        resulthandler = call[1]
                        if not callable(call[1]): raise Exception(f'行结果处理器不可调用,{call[1]}')
                    else:
                        resulthandler = HashableWrapper
                elif isinstance(call, dict):
                    if not call: raise Exception(f'处理器字典为空,请检查')
                    condition = call.get('condition', None)
                    if not callable(condition): raise Exception(f'条件处理器不可调用,{condition}')
                    resulthandler = call.get('resulthandler', HashableWrapper)
                    if not callable(resulthandler): raise Exception(f'行结果处理器不可调用,{resulthandler}')

                if condition(cname, row): result[cname].add(resulthandler(row))
        except Exception as e:
            raise type(e) (f'{e}\n\n行号:{index}\n{row}')
   
        totalCount += 1
        divCount += 1
        if divCount > processdiv:
            divCount = 0
            logger.warning(f'已处理{totalCount}条')

    logger.warning(f'{totalCount}条处理完毕')
    logger.warning(f'----类索引建立完成----')
    return result

def generate_abstractinfo(df, output, vhandlers, return_df=True, start=0, end=-1, processdiv=999):
    '''
    抽象信息
    批次读取(pandas版本未支持)
    例: vhandlers = [
        ('商品单号', lambda row: row['商品单号']), 
        ('退款金额', lambda row: row['退款金额']), 
        ('退款状态', lambda row: row['退款状态'])
    ]
    '''
    keys = [key for key, _ in vhandlers]
    handlers = [handler for _, handler in vhandlers]
    logger.warning(f'----开始抽象,{keys}----')
    chunksize = 1000

    write_only = not return_df
    workbook_new = Workbook(write_only=write_only)
    df_new = list()
    if write_only: 
        sheet_new = workbook_new.create_sheet() 
    else: 
        sheet_new = workbook_new.active
    
    if return_df: df_new.append(keys)
    sheet_new.append(keys)
    totalCount = 0
    divCount = 0
    # for _, row in df.iterrows():
    #     # 处理每一行数据
    #     row_new = list()
    #     for handler in handlers: row_new.append(handler(row))
    #     sheet_new.append(row_new)

    for index in df.index:
        if index < start: continue
        if end != -1 and index >= end: break
        row = df.loc[index]

        # 处理每一行数据
        try:
            row_new = list()
            for handler in handlers: row_new.append(handler(row))
            sheet_new.append(row_new)
            if return_df: df_new.append(row_new)
        except Exception as e:
            raise type(e) (f'{e}\n\n行号:{index}\n{row}')

        totalCount += 1
        divCount += 1
        if divCount > processdiv:
            divCount = 0
            logger.warning(f'已处理{totalCount}条')

    logger.warning(f'{totalCount}条处理完毕')
    os.makedirs(os.path.dirname(output), exist_ok=True)
    workbook_new.save(output)
    logger.warning(f'----抽象完成,输出到{output}----')
    df_new = pd.DataFrame(df_new[1:], columns=df_new[0])
    return df_new

init()